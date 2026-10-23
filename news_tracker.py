#!/usr/bin/env python3
"""Account Intelligence news tracker.

Collects news for the accounts in config.COMPANIES across the geographies in
config.COUNTRIES using Google News RSS (and optionally Bing News RSS) - no API
keys required. Results are de-duplicated, categorised by topic (multilingual
keyword taxonomy), scored for sentiment/priority, flagged as NEW versus
previous runs, and exported to Excel, CSV and an HTML digest.

Usage examples
--------------
    python news_tracker.py                          # last 7 days, all companies/countries
    python news_tracker.py --days 30                # last 30 days
    python news_tracker.py --deep                   # extra topic-targeted queries (more coverage, slower)
    python news_tracker.py --companies Airbus BASF  # subset of companies (partial, case-insensitive)
    python news_tracker.py --countries France Germany Global
    python news_tracker.py --no-bing                # Google News only
    python news_tracker.py --all-languages          # include local-language news (default is English only)
"""
from __future__ import annotations

import argparse
import html
import logging
import re
import sqlite3
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

import feedparser
import pandas as pd
import requests

import config

log = logging.getLogger("news_tracker")

ENGLISH_ONLY = True  # set from CLI (--all-languages disables)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
GOOGLE_RSS = "https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"
BING_RSS = "https://www.bing.com/news/search?q={q}&format=rss&cc={cc}&setlang={lang}"


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Article:
    company: str
    title: str
    link: str
    source: str
    published: datetime | None
    snippet: str
    countries: set[str] = field(default_factory=set)
    engines: set[str] = field(default_factory=set)
    queries: set[str] = field(default_factory=set)
    categories: list[str] = field(default_factory=list)
    sentiment: str = "Neutral"
    priority: str = "Normal"
    is_new: bool = True

    @property
    def key(self) -> str:
        return f"{self.company}|{normalise(self.title)}"


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", text or ""))).strip()


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def split_title_source(title: str, source: str) -> tuple[str, str]:
    """Google News titles look like 'Headline - Publisher'."""
    if source and title.endswith(f" - {source}"):
        title = title[: -len(source) - 3]
    elif " - " in title and not source:
        head, _, tail = title.rpartition(" - ")
        title, source = head, tail
    return title.strip(), source.strip()


def _term_regex(terms: list[str]) -> re.Pattern:
    parts = [r"(?<![a-z0-9])" + re.escape(normalise(t)) + r"(?![a-z0-9])" for t in terms]
    return re.compile("|".join(parts))


_COMPANY_MATCH = {
    name: (
        _term_regex(cfg["match"]),
        _term_regex(cfg["exclude"]) if cfg.get("exclude") else None,
    )
    for name, cfg in config.COMPANIES.items()
}


def is_relevant(company: str, text: str) -> bool:
    inc, exc = _COMPANY_MATCH[company]
    norm = normalise(text)
    if not inc.search(norm):
        return False
    return not (exc and exc.search(norm) and not re.search(r"contitech|aumovio|continental ag", norm))


_STOP = {
    "en": "the and of to in for on with at by from is are was were has have will its their after as that this new over "
          "into amid says said about up out more than against how why what who may could would".split(),
    "foreign": (
        "le la les des du une et est pour dans sur avec pas qui sont ses leur aux au par plus ce cette "  # fr
        "der das und ist für mit von auf den dem ein eine nicht sich auch zu im bei nach wird werden über aus "  # de
        "el los las del por para con una que se su como más pero sus al "  # es
        "het een van voor met niet naar zijn bij ook maar wordt worden over dat deze"  # nl
    ).split(),
}
_EN_RE = re.compile(r"(?<![a-z])(?:" + "|".join(_STOP["en"]) + r")(?![a-z])")
_FOREIGN_RE = re.compile(r"(?<![a-z])(?:" + "|".join(_STOP["foreign"]) + r")(?![a-z])")


def is_english(text: str) -> bool:
    """Cheap stop-word language check; ambiguous (no stop words) headlines are kept."""
    lowered = unicodedata.normalize("NFKD", text.lower())
    lowered = "".join(c for c in lowered if not unicodedata.combining(c))
    return len(_EN_RE.findall(lowered)) >= len(_FOREIGN_RE.findall(lowered))


def _kw_regex(kws: list[str]) -> re.Pattern:
    # prefix match on the left boundary so "layoff" also hits "layoffs", "sustainab" hits "sustainability"
    return re.compile("|".join(r"(?<![a-z0-9])" + re.escape(normalise(k)) for k in kws if normalise(k)))


_CAT_RE = {c: _kw_regex(v["kw"]) for c, v in config.CATEGORIES.items()}
_POS_RE = _kw_regex(config.POSITIVE)
_NEG_RE = _kw_regex(config.NEGATIVE)


def classify(article: Article) -> None:
    text = normalise(f"{article.title} {article.snippet}")
    title = normalise(article.title)
    scored = []
    for order, (cat, rx) in enumerate(_CAT_RE.items()):
        hits_title = len(rx.findall(title))
        hits_all = len(rx.findall(text))
        if hits_all:
            scored.append((-(hits_title * 3 + hits_all), order, cat))
    scored.sort()
    article.categories = [c for _, _, c in scored] or [config.GENERAL_CATEGORY]

    pos, neg = len(_POS_RE.findall(text)), len(_NEG_RE.findall(text))
    article.sentiment = "Positive" if pos > neg else "Negative" if neg > pos else "Neutral"
    article.priority = (
        "High"
        if (set(article.categories) & config.HIGH_PRIORITY) and (article.sentiment == "Negative" or len(article.categories) > 1
                                                                 or article.categories[0] in config.HIGH_PRIORITY)
        else "Normal"
    )


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Job:
    engine: str  # google | bing
    company: str
    country: str
    query: str  # human-readable label
    url: str


def company_query(company: str) -> str:
    aliases = config.COMPANIES[company]["aliases"]
    return "(" + " OR ".join(f'"{a}"' for a in aliases) + ")"


def build_jobs(companies, countries, days, deep, use_bing, english_only=True) -> list[Job]:
    jobs: list[Job] = []
    for company in companies:
        base = company_query(company)
        for country in countries:
            c = dict(config.COUNTRIES[country])
            if english_only:  # English-language edition of each country's news
                c.update(hl="en", ceid=f"{c['gl']}:en", lang="en", bing_cc=c["gl"] if country != "Global" else "WW")
            variants = [("all news", base)]
            if deep:
                variants.append(("topics (EN)", f"{base} AND ({_deep_en()})"))
                local = "" if english_only else config.LOCAL_DEEP_TERMS.get(c["lang"], "")
                if local:
                    variants.append((f"topics ({c['lang'].upper()})", f"{base} AND ({local})"))
            for label, q in variants:
                g_q = quote_plus(f"{q} when:{days}d")
                jobs.append(Job("google", company, country, label,
                                GOOGLE_RSS.format(q=g_q, hl=c["hl"], gl=c["gl"], ceid=c["ceid"])))
                if use_bing:
                    jobs.append(Job("bing", company, country, label,
                                    BING_RSS.format(q=quote_plus(q), cc=c["bing_cc"], lang=c["lang"])))
    return jobs


def _deep_en() -> str:
    return " OR ".join(f"({v['deep'][0]})" for v in config.CATEGORIES.values())


def fetch(session: requests.Session, job: Job, retries: int = 3, pause: float = 0.4) -> list[Article]:
    for attempt in range(1, retries + 1):
        try:
            time.sleep(pause)
            resp = session.get(job.url, timeout=25)
            if resp.status_code in (429, 503):
                time.sleep(2 ** attempt * 2)
                continue
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            return list(parse_entries(feed, job, ENGLISH_ONLY))
        except requests.RequestException as exc:
            log.debug("fetch error (%s/%s try %d): %s", job.company, job.country, attempt, exc)
            time.sleep(2 ** attempt)
    log.warning("giving up: %s | %s | %s | %s", job.engine, job.company, job.country, job.query)
    return []


def parse_entries(feed, job: Job, english_only: bool = True):
    for e in feed.entries:
        raw_title = strip_html(e.get("title", ""))
        source = ""
        src = e.get("source")
        if src:
            source = src.get("title", "") if isinstance(src, dict) else str(src)
        title, source = split_title_source(raw_title, source)
        snippet = strip_html(e.get("summary", ""))
        if job.engine == "google":
            # Google's summary is just the title + publisher again
            snippet = "" if normalise(snippet).startswith(normalise(title)[:40]) else snippet
        link = e.get("link", "")
        if job.engine == "bing":
            qs = parse_qs(urlparse(link).query)
            link = qs.get("url", [link])[0]
            source = source or e.get("news_source", "")
        published = None
        if e.get("published_parsed"):
            published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
        if not title or not link:
            continue
        if not is_relevant(job.company, f"{title} {snippet}"):
            continue
        if english_only and not is_english(f"{title} {snippet}"):
            continue
        art = Article(job.company, title, link, source, published, snippet)
        art.countries.add(job.country)
        art.engines.add(job.engine)
        art.queries.add(job.query)
        yield art


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
def collect(jobs: list[Job], workers: int, cutoff: datetime) -> dict[str, Article]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en,fr;q=0.8,de;q=0.6"})
    merged: dict[str, Article] = {}
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, session, j): j for j in jobs}
        for fut in as_completed(futures):
            done += 1
            if done % 25 == 0 or done == len(jobs):
                print(f"\r  fetched {done}/{len(jobs)} feeds  |  {len(merged)} unique articles", end="", flush=True)
            for art in fut.result():
                if art.published and art.published < cutoff:
                    continue
                existing = merged.get(art.key)
                if existing is None:
                    merged[art.key] = art
                else:
                    existing.countries |= art.countries
                    existing.engines |= art.engines
                    existing.queries |= art.queries
                    if not existing.snippet and art.snippet:
                        existing.snippet = art.snippet
    print()
    return merged


def mark_new(articles: list[Article], db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS seen (key TEXT PRIMARY KEY, first_seen TEXT)")
    known = {r[0] for r in con.execute("SELECT key FROM seen")}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    first_run = not known
    for a in articles:
        a.is_new = a.key not in known
    con.executemany("INSERT OR IGNORE INTO seen VALUES (?, ?)", [(a.key, now) for a in articles])
    con.commit()
    con.close()
    if first_run:
        log.info("first run: every article is flagged NEW; subsequent runs will flag only unseen ones")


def to_frame(articles: list[Article]) -> pd.DataFrame:
    rows = []
    for a in articles:
        rows.append({
            "New": "NEW" if a.is_new else "",
            "Priority": a.priority,
            "Company": a.company,
            "Published (UTC)": a.published.replace(tzinfo=None) if a.published else pd.NaT,
            "Headline": a.title,
            "Source": a.source,
            "Primary Category": a.categories[0],
            "All Categories": "; ".join(a.categories),
            "Sentiment": a.sentiment,
            "Countries": "; ".join(sorted(a.countries)),
            "Engines": "; ".join(sorted(a.engines)),
            "Snippet": a.snippet[:500],
            "Link": a.link,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["_p"] = df["Priority"].map({"High": 0, "Normal": 1})
    df = df.sort_values(["Published (UTC)", "_p"], ascending=[False, True]).drop(columns="_p")
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def write_excel(df: pd.DataFrame, path: Path, explode_countries: pd.DataFrame) -> None:
    with pd.ExcelWriter(path, engine="openpyxl", datetime_format="yyyy-mm-dd hh:mm") as xw:
        df.to_excel(xw, sheet_name="All News", index=False)
        df[df["New"] == "NEW"].to_excel(xw, sheet_name="New Since Last Run", index=False)
        df[df["Priority"] == "High"].to_excel(xw, sheet_name="High Priority", index=False)
        pd.crosstab(df["Company"], df["Primary Category"], margins=True, margins_name="Total").to_excel(xw, sheet_name="Company x Category")
        pd.crosstab(explode_countries["Company"], explode_countries["Country"], margins=True, margins_name="Total").to_excel(xw, sheet_name="Company x Country")
        pd.crosstab(df["Company"], df["Sentiment"], margins=True, margins_name="Total").to_excel(xw, sheet_name="Sentiment")
        for company, sub in df.groupby("Company"):
            sub.to_excel(xw, sheet_name=re.sub(r"[\\/*?:\[\]&]", "", company)[:31], index=False)
        _format(xw)


def _format(xw: pd.ExcelWriter) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    widths = {"Headline": 90, "Snippet": 60, "Link": 40, "All Categories": 40, "Countries": 30, "Company": 26,
              "Source": 24, "Published (UTC)": 18, "Primary Category": 28}
    for ws in xw.book.worksheets:
        ws.freeze_panes = "A2"
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F3864")
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            ws.column_dimensions[get_column_letter(cell.column)].width = widths.get(str(cell.value), 14)
        if ws.max_row > 1 and ws.max_column > 8:
            ws.auto_filter.ref = ws.dimensions
            headers = {c.value: c.column for c in ws[1]}
            link_col = headers.get("Link")
            for row in range(2, ws.max_row + 1):
                if link_col:
                    c = ws.cell(row, link_col)
                    c.hyperlink = c.value
                    c.font = Font(color="0563C1", underline="single")
                if ws.cell(row, headers["Priority"]).value == "High":
                    ws.cell(row, headers["Priority"]).fill = PatternFill("solid", fgColor="F8CBAD")
                if ws.cell(row, headers["New"]).value == "NEW":
                    ws.cell(row, headers["New"]).fill = PatternFill("solid", fgColor="C6EFCE")
        if ws.title in ("Company x Category", "Company x Country", "Sentiment"):
            ws.column_dimensions["A"].width = 30


def write_html(df: pd.DataFrame, path: Path, args, generated: datetime) -> None:
    esc = html.escape
    parts = [f"""<!doctype html><html><head><meta charset="utf-8"><title>Account Intelligence Digest</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:2rem auto;max-width:1000px;color:#222}}
h1{{color:#1F3864}}h2{{border-bottom:2px solid #1F3864;padding-bottom:4px;margin-top:2rem}}
.a{{margin:.6rem 0;padding:.4rem .6rem;border-left:4px solid #bbb}}.a.High{{border-color:#c0392b}}
.m{{font-size:.8rem;color:#666}}.t{{display:inline-block;font-size:.7rem;background:#e8eef8;border-radius:3px;padding:1px 6px;margin-right:4px}}
.n{{background:#27ae60;color:#fff}}.Negative{{color:#c0392b}}.Positive{{color:#27ae60}}a{{color:#0b5ed7;text-decoration:none}}</style></head><body>
<h1>Account Intelligence Digest</h1>
<p class="m">Generated {generated:%Y-%m-%d %H:%M} UTC &middot; window: last {args.days} days &middot; {len(df)} articles &middot; {int((df['New']=='NEW').sum())} new</p>"""]
    for company, sub in df.groupby("Company", sort=False):
        parts.append(f"<h2>{esc(company)} <span class='m'>({len(sub)})</span></h2>")
        for cat, grp in sub.groupby("Primary Category"):
            parts.append(f"<h4>{esc(cat)}</h4>")
            for _, r in grp.head(args.html_max).iterrows():
                pub = r["Published (UTC)"].strftime("%Y-%m-%d") if pd.notna(r["Published (UTC)"]) else ""
                new = "<span class='t n'>NEW</span>" if r["New"] else ""
                parts.append(
                    f"<div class='a {r['Priority']}'>{new}<a href='{esc(r['Link'])}' target='_blank'>{esc(r['Headline'])}</a>"
                    f"<div class='m'>{esc(r['Source'])} &middot; {pub} &middot; {esc(r['Countries'])} &middot; "
                    f"<span class='{r['Sentiment']}'>{r['Sentiment']}</span></div></div>")
    parts.append("</body></html>")
    path.write_text("\n".join(parts), encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def pick(options: list[str], wanted: list[str] | None, label: str) -> list[str]:
    if not wanted:
        return list(options)
    chosen = []
    for w in wanted:
        hit = [o for o in options if w.lower() in o.lower()]
        if not hit:
            sys.exit(f"Unknown {label} '{w}'. Options: {', '.join(options)}")
        chosen += [h for h in hit if h not in chosen]
    return chosen


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=7, help="look-back window in days (default 7)")
    ap.add_argument("--companies", nargs="*", help="subset of companies (partial names ok)")
    ap.add_argument("--countries", nargs="*", help="subset of countries (partial names ok)")
    ap.add_argument("--deep", action="store_true", help="add topic-targeted queries (EN + local language)")
    ap.add_argument("--no-bing", action="store_true", help="skip Bing News (Google News only)")
    ap.add_argument("--all-languages", action="store_true", help="include non-English news (default: English only)")
    ap.add_argument("--workers", type=int, default=6, help="parallel fetch threads (default 6)")
    ap.add_argument("--output-dir", default="output", help="where to write results (default ./output)")
    ap.add_argument("--html-max", type=int, default=15, help="max articles per category per company in HTML")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")

    global ENGLISH_ONLY
    ENGLISH_ONLY = not args.all_languages
    companies = pick(list(config.COMPANIES), args.companies, "company")
    countries = pick(list(config.COUNTRIES), args.countries, "country")
    jobs = build_jobs(companies, countries, args.days, args.deep, not args.no_bing, ENGLISH_ONLY)
    now = datetime.now(timezone.utc)
    print(f"Tracking {len(companies)} companies x {len(countries)} geographies "
          f"-> {len(jobs)} feed requests (last {args.days} days)")

    merged = collect(jobs, args.workers, now - timedelta(days=args.days))
    articles = list(merged.values())
    if not articles:
        sys.exit("No articles found - check your internet connection/proxy (use -v for details).")
    for a in articles:
        classify(a)
    out = Path(args.output_dir)
    mark_new(articles, out / "seen_articles.db")
    df = to_frame(articles)
    country_rows = pd.DataFrame([{"Company": a.company, "Country": c} for a in articles for c in a.countries])

    stamp = now.strftime("%Y%m%d_%H%M")
    out.mkdir(parents=True, exist_ok=True)
    xlsx, csv, htm = out / f"news_{stamp}.xlsx", out / f"news_{stamp}.csv", out / f"digest_{stamp}.html"
    write_excel(df, xlsx, country_rows)
    df.to_csv(csv, index=False, encoding="utf-8-sig")
    write_html(df, htm, args, now)

    print(f"\n{len(df)} unique articles ({int((df['New'] == 'NEW').sum())} new, "
          f"{int((df['Priority'] == 'High').sum())} high priority)\n")
    print(df.groupby("Company").size().sort_values(ascending=False).to_string())
    print(f"\nExcel : {xlsx}\nCSV   : {csv}\nHTML  : {htm}")


if __name__ == "__main__":
    main()
