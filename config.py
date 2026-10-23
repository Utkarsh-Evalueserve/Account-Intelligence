"""Configuration for the Account Intelligence news tracker.

Edit this file to add/remove companies, aliases, geographies or topic keywords.
"""

# --------------------------------------------------------------------------
# Companies: display name -> search aliases (quoted phrases in the query) and
# `match` terms (a headline/snippet must contain one to be kept; removes noise
# such as articles about the generic word "continental").
# --------------------------------------------------------------------------
COMPANIES = {
    "Groupe Invivo": {
        "aliases": ["Groupe Invivo", "Invivo Group", "InVivo Agrosolutions", "Invivo Retail", "Soufflet"],
        "match": ["invivo", "in vivo group", "soufflet"],
    },
    "Auchan Retail": {
        "aliases": ["Auchan Retail", "Auchan", "Auchan Holding"],
        "match": ["auchan"],
    },
    "Intermarché": {
        "aliases": ["Intermarché", "Groupement Les Mousquetaires", "Les Mousquetaires", "Netto Intermarché"],
        "match": ["intermarché", "intermarche", "mousquetaires"],
    },
    "Groupe Clarins": {
        "aliases": ["Groupe Clarins", "Clarins", "Clarins Group"],
        "match": ["clarins"],
    },
    "Groupe Rocher & Yves Rocher": {
        "aliases": ["Groupe Rocher", "Yves Rocher", "Rocher Group", "Petit Bateau Rocher", "Dr Pierre Ricaud"],
        "match": ["groupe rocher", "yves rocher", "rocher group", "bruno rocher", "ricaud"],
    },
    "Renault S.A.": {
        "aliases": ["Renault Group", "Renault", "Ampere Renault", "Dacia Renault", "Alpine Renault"],
        "match": ["renault"],
    },
    "Airbus SE": {
        "aliases": ["Airbus", "Airbus SE", "Airbus Defence and Space", "Airbus Helicopters"],
        "match": ["airbus"],
    },
    "BASF SE": {
        "aliases": ["BASF", "BASF SE"],
        "match": ["basf"],
    },
    "ZF Friedrichshafen AG": {
        "aliases": ["ZF Friedrichshafen", "ZF Group", "ZF Lifetec", "ZF Aftermarket", "ZF Wabco"],
        "match": ["zf friedrichshafen", "zf group", "zf lifetec", "zf aftermarket", "zf wabco", "zf-gruppe", "zf"],
    },
    "Continental AG": {
        "aliases": ["Continental AG", "ContiTech", "Continental tires", "Continental Reifen", "Continental Automotive Aumovio"],
        "match": ["continental ag", "contitech", "continental tire", "continental reifen", "continental automotive",
                  "aumovio", "continental pneu", "continental neumáticos", "continental banden", "continental"],
        "exclude": ["continental europe", "continental breakfast", "continental airlines", "continental divide",
                    "continental shelf", "continental drift", "continental u.s.", "continental us", "continental cup",
                    "continental resources", "continental league", "continental philosophy", "continental army",
                    "europe continental", "intercontinental"],
    },
}

# --------------------------------------------------------------------------
# Geographies. gl/hl/ceid are Google News edition parameters; `bing_cc` is the
# Bing market code. "Global" = English-language, no country restriction.
# --------------------------------------------------------------------------
COUNTRIES = {
    "France":         {"gl": "FR", "hl": "fr",    "ceid": "FR:fr",    "bing_cc": "fr-FR", "lang": "fr"},
    "United Kingdom": {"gl": "GB", "hl": "en-GB", "ceid": "GB:en",    "bing_cc": "en-GB", "lang": "en"},
    "Netherlands":    {"gl": "NL", "hl": "nl",    "ceid": "NL:nl",    "bing_cc": "nl-NL", "lang": "nl"},
    "Belgium":        {"gl": "BE", "hl": "fr",    "ceid": "BE:fr",    "bing_cc": "fr-BE", "lang": "fr"},
    "Luxembourg":     {"gl": "LU", "hl": "fr",    "ceid": "LU:fr",    "bing_cc": "fr-FR", "lang": "fr"},
    "Germany":        {"gl": "DE", "hl": "de",    "ceid": "DE:de",    "bing_cc": "de-DE", "lang": "de"},
    "Austria":        {"gl": "AT", "hl": "de",    "ceid": "AT:de",    "bing_cc": "de-AT", "lang": "de"},
    "Switzerland":    {"gl": "CH", "hl": "de",    "ceid": "CH:de",    "bing_cc": "de-CH", "lang": "de"},
    "Spain":          {"gl": "ES", "hl": "es",    "ceid": "ES:es",    "bing_cc": "es-ES", "lang": "es"},
    "United States":  {"gl": "US", "hl": "en-US", "ceid": "US:en",    "bing_cc": "en-US", "lang": "en"},
    "Global":         {"gl": "US", "hl": "en",    "ceid": "US:en",    "bing_cc": "en-WW", "lang": "en"},
}

# --------------------------------------------------------------------------
# Topic taxonomy (multilingual keywords, matched case-insensitively against
# title + snippet). Listed in priority order: the first match is the "primary"
# category. `deep_terms` are used by --deep mode to run extra targeted queries
# (English is always used; local-language terms are added per country).
# --------------------------------------------------------------------------
CATEGORIES = {
    "M&A / Investments": {
        "kw": ["acquisition", "acquire", "acquires", "merger", "takeover", "divest", "stake", "joint venture",
               "buyout", "spin-off", "spin off", "investment", "invests", "investit", "rachat", "acquiert", "cession",
               "fusion", "übernahme", "übernimmt", "beteiligung", "verkauf", "fusión", "adquisición", "overname",
               "participation", "capex", "new plant", "new factory", "usine", "werk", "fábrica", "fabriek"],
        "deep": ["acquisition OR merger OR divestment OR stake OR \"joint venture\""],
    },
    "Financial Results": {
        "kw": ["results", "earnings", "revenue", "profit", "sales", "guidance", "outlook", "ebit", "ebitda",
               "quarter", "q1", "q2", "q3", "q4", "dividend", "forecast", "turnover", "résultats", "chiffre d'affaires",
               "bénéfice", "perte", "ergebnis", "umsatz", "gewinn", "verlust", "prognose", "quartal", "resultados",
               "ventas", "beneficio", "pérdidas", "omzet", "winst", "kwartaal", "credit rating", "rating", "bond",
               "debt", "share price", "stock", "action", "aktie", "shares"],
        "deep": ["results OR earnings OR revenue OR profit OR guidance OR dividend"],
    },
    "Leadership & Governance": {
        "kw": ["ceo", "cfo", "chairman", "appoints", "appointed", "nominated", "resigns", "steps down", "board",
               "executive", "succession", "management", "nomination", "nomme", "directeur", "pdg", "président",
               "démission", "vorstand", "aufsichtsrat", "ernennt", "rücktritt", "geschäftsführer", "nombra",
               "dimite", "consejero", "bestuur", "benoemt", "director general", "chief"],
        "deep": ["CEO OR CFO OR chairman OR appoints OR \"board of directors\" OR succession"],
    },
    "Workforce & Labour": {
        "kw": ["layoff", "layoffs", "job cuts", "jobs", "redundan", "strike", "union", "hiring", "restructuring",
               "workforce", "employees", "plan social", "licenciement", "suppression de postes", "grève", "syndicat",
               "emploi", "stellenabbau", "entlassung", "streik", "gewerkschaft", "betriebsrat", "arbeitsplätze",
               "despidos", "huelga", "sindicato", "ere", "ontslag", "staking", "vakbond", "banen", "recrute"],
        "deep": ["layoffs OR \"job cuts\" OR strike OR union OR restructuring OR hiring"],
    },
    "Legal, Regulatory & Compliance": {
        "kw": ["lawsuit", "sued", "court", "fine", "fined", "antitrust", "competition authority", "investigation",
               "probe", "regulator", "regulation", "sanction", "tariff", "customs", "settlement", "litigation",
               "tribunal", "amende", "enquête", "justice", "condamn", "procès", "autorité de la concurrence", "dgccrf",
               "klage", "bußgeld", "kartell", "ermittlung", "gericht", "urteil", "strafe", "demanda", "multa",
               "tribunal", "investigación", "rechtbank", "boete", "onderzoek", "recall", "rappel", "rückruf", "tax",
               "fiscal", "steuer"],
        "deep": ["lawsuit OR fine OR antitrust OR investigation OR regulator OR sanctions OR tariffs"],
    },
    "ESG & Sustainability": {
        "kw": ["sustainab", "esg", "carbon", "co2", "emission", "net zero", "net-zero", "climate", "decarbon",
               "renewable", "recycl", "biodiversity", "csr", "rse", "green", "circular", "durable", "développement durable",
               "nachhaltig", "klima", "umwelt", "emissionen", "sostenib", "emisiones", "duurzaam", "milieu",
               "pollution", "water", "deforestation", "animal welfare", "bio", "organic", "packaging"],
        "deep": ["sustainability OR ESG OR CO2 OR \"net zero\" OR decarbonisation OR recycling"],
    },
    "Partnerships & Contracts": {
        "kw": ["partnership", "partners", "alliance", "agreement", "contract", "order", "orders", "deal", "supplier",
               "collaboration", "signs", "wins", "awarded", "tender", "mou", "memorandum", "partenariat", "accord",
               "contrat", "commande", "fournisseur", "alliance", "partnerschaft", "vereinbarung", "auftrag",
               "kooperation", "zusammenarbeit", "lieferant", "acuerdo", "contrato", "pedido", "samenwerking",
               "overeenkomst", "bestelling", "deliveries", "livraison", "lieferung"],
        "deep": ["partnership OR agreement OR contract OR order OR alliance OR collaboration"],
    },
    "Product & Innovation": {
        "kw": ["launch", "launches", "unveil", "unveils", "new model", "innovation", "r&d", "patent", "prototype",
               "electric", "ev ", "battery", "hydrogen", "autonomous", "software", "ai ", "artificial intelligence",
               "digital", "technology", "lance", "dévoile", "nouveau", "innovation", "voiture électrique",
               "vorstellt", "neue", "entwickl", "forschung", "elektro", "lanza", "presenta", "nuevo", "lanceert",
               "onthult", "nieuw", "a350", "a320", "a220", "sdv", "adas", "sustainable aviation fuel", "saf",
               "product", "produit", "produkt", "producto", "range", "gamme"],
        "deep": ["launch OR unveils OR innovation OR \"new model\" OR technology OR AI OR electric"],
    },
    "Operations & Supply Chain": {
        "kw": ["supply chain", "production", "output", "shortage", "delay", "delays", "plant", "factory", "closure",
               "logistics", "capacity", "shutdown", "disruption", "chip", "semiconductor", "raw material", "energy",
               "gas price", "approvisionnement", "pénurie", "retard", "fermeture", "site", "lieferkette",
               "produktion", "engpass", "verzögerung", "schließung", "standort", "cadena de suministro",
               "producción", "escasez", "retraso", "cierre", "toeleveringsketen", "productie", "tekort", "sluiting",
               "stores", "magasins", "supermarket", "supermarché", "filiale", "subsidiary", "expansion", "opening",
               "ouverture"],
        "deep": ["production OR \"supply chain\" OR shortage OR delays OR closure OR plant"],
    },
    "Cyber, Data & IT": {
        "kw": ["cyber", "hack", "hacked", "ransomware", "data breach", "breach", "leak", "phishing", "data protection",
               "gdpr", "rgpd", "dsgvo", "cyberattaque", "piratage", "fuite de données", "cyberangriff", "datenleck",
               "ciberataque", "datalek", "cloud", "erp"],
        "deep": ["cyberattack OR ransomware OR \"data breach\" OR hack OR GDPR"],
    },
    "Market & Competition": {
        "kw": ["market share", "competitor", "rival", "price war", "pricing", "prices", "demand", "analyst",
               "downgrade", "upgrade", "target price", "ranking", "parts de marché", "concurrent", "prix",
               "marktanteil", "wettbewerb", "preise", "nachfrage", "cuota de mercado", "competencia", "precios",
               "marktaandeel", "concurrentie", "prijzen", "inflation", "consumer", "consommateur", "verbraucher",
               "consumidor", "consument"],
        "deep": ["\"market share\" OR competitor OR analyst OR \"price target\" OR demand"],
    },
    "Risk & Incidents": {
        "kw": ["accident", "crash", "fire", "explosion", "injur", "death", "defect", "safety", "scandal", "boycott",
               "controversy", "criticism", "complaint", "incident", "accident", "incendie", "mort", "défaut", "scandale",
               "boycott", "polémique", "unfall", "brand", "explosion", "mängel", "skandal", "kritik", "accidente",
               "incendio", "defecto", "escándalo", "ongeval", "brand", "schandaal", "recall"],
        "deep": ["accident OR fire OR explosion OR scandal OR boycott OR defect OR safety"],
    },
}

GENERAL_CATEGORY = "General / Other"

# Categories considered high-priority for account teams (highlighted in outputs).
HIGH_PRIORITY = {
    "M&A / Investments", "Financial Results", "Leadership & Governance",
    "Workforce & Labour", "Legal, Regulatory & Compliance", "Cyber, Data & IT", "Risk & Incidents",
}

# Words used by the lightweight multilingual sentiment heuristic.
POSITIVE = [
    "growth", "record", "wins", "win", "profit rises", "beats", "upgrade", "expands", "success", "boost", "surge",
    "strong", "rebound", "croissance", "hausse", "succès", "record", "gagne", "wachstum", "rekord", "steigt", "erfolg",
    "crecimiento", "récord", "éxito", "groei", "stijgt", "succes",
]
NEGATIVE = [
    "loss", "falls", "drop", "plunge", "cuts", "layoff", "job cuts", "strike", "fine", "lawsuit", "probe", "recall",
    "crisis", "warning", "downgrade", "decline", "slump", "scandal", "cyberattack", "closure", "baisse", "perte",
    "chute", "crise", "grève", "amende", "rappel", "verlust", "einbruch", "krise", "streik", "stellenabbau",
    "rückruf", "pérdida", "caída", "crisis", "huelga", "multa", "daling", "verlies", "crisis", "ontslag", "boete",
]

# Extra query language terms used in --deep mode, per language (generic "news" nudge).
LOCAL_DEEP_TERMS = {
    "fr": "résultats OR acquisition OR nomination OR grève OR enquête OR innovation OR partenariat OR usine",
    "de": "Ergebnis OR Übernahme OR Vorstand OR Streik OR Stellenabbau OR Innovation OR Partnerschaft OR Werk",
    "es": "resultados OR adquisición OR nombramiento OR huelga OR investigación OR innovación OR alianza OR fábrica",
    "nl": "resultaten OR overname OR benoeming OR staking OR onderzoek OR innovatie OR partnerschap OR fabriek",
    "en": "",
}
