# Account Intelligence – News Tracker

Tracks news for 10 accounts (Groupe Invivo, Auchan Retail, Intermarché, Groupe Clarins, Groupe Rocher & Yves Rocher,
Renault S.A., Airbus SE, BASF SE, ZF Friedrichshafen AG, Continental AG) across France, UK, Netherlands, Belgium,
Luxembourg, Germany, Austria, Switzerland, Spain, US and Global. No API keys needed (Google News + Bing News RSS).

## Run in VS Code
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python news_tracker.py                      # last 7 days, everything
python news_tracker.py --days 30 --deep     # wider window + topic-targeted queries (more coverage, slower)
python news_tracker.py --companies Airbus BASF --countries France Germany Global
python news_tracker.py --no-bing            # Google News only
python news_tracker.py --all-languages      # include local-language news (default is English only)
```

## Output (`./output`)
- `news_<timestamp>.xlsx` – sheets: All News, New Since Last Run, High Priority, Company x Category,
  Company x Country, Sentiment, plus one sheet per company
- `news_<timestamp>.csv` and `digest_<timestamp>.html` (readable digest grouped by company / topic)
- `seen_articles.db` – remembers past articles so later runs flag only **NEW** items (schedule daily with
  Task Scheduler / cron)

## What it does
- Returns **English-language news only** by default (English editions per country + a language filter; use `--all-languages` to disable). Queries every company x geography, using aliases and
  subsidiaries (e.g. ContiTech, Yves Rocher, Soufflet).
- Drops irrelevant hits (e.g. "continental breakfast") via per-company match/exclude rules.
- De-duplicates across countries/engines and merges the countries where a story appeared.
- Tags 11 topics (M&A, financials, leadership, workforce, legal/regulatory, ESG, partnerships, product/innovation,
  operations/supply chain, cyber, market, risk/incidents) with multilingual keywords, plus sentiment and a
  High-priority flag.

## Customise
Everything lives in `config.py`: add companies/aliases, countries, topic keywords and priority categories.

## Notes
Google News RSS returns up to ~100 items per query; use `--deep` and shorter `--days` for high-volume names
(Renault, Airbus). Headlines/snippets only – the tool links to publishers rather than copying article text.
Use responsibly and respect each source's terms.
