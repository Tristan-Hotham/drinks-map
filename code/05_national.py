"""National drinks and national liquors from English Wikipedia.

- 'List of national drinks' (article title 'National drink'): each line '*'''{{flag|Country}}:''' text' gives the
  drinks suggested for that country, alcoholic or not. 'List of national liquors': lines '* {{IOC code}}: text'.
- Every link in a line is resolved to its Wikidata item (through the Wikipedia API, redirects followed). A link is
  a drink if Wikidata puts it under 'drink' (Q40050) or 'alcoholic beverage' (Q154), or it is one of the drink types
  in this study. The first such link is the country's 'first-listed' drink.
- Kind of drink: tea, coffee, a mixed drink (cocktail), one of the alcoholic families in families.py, or another
  non-alcoholic drink. The lists are what Wikipedia's editors have written, with sources of mixed quality; they are
  not official and some countries have several suggestions.
Outputs: data/national_drinks.csv, work/national.json
"""
import csv
from collections import Counter
from common import *
from families import family, KEY

P = jload(f"{WORK}/parsed.json")
CL = {r["q"]: r for r in P["classes"]}
NL = {r["q"]: r for r in P["natlinks"]}
LINKS = P["wikipedia"]["links"]
geo = jload(f"{DATA}/countries_geo.json")
name2iso = {norm(v["name"]): k for k, v in geo.items()}
ALIAS = {"united states": "USA", "united kingdom": "GBR", "czech republic": "CZE", "czechia": "CZE", "ivory coast": "CIV",
         "democratic republic of the congo": "COD", "republic of the congo": "COG", "the gambia": "GMB", "gambia": "GMB",
         "the bahamas": "BHS", "bahamas": "BHS", "east timor": "TLS", "timor leste": "TLS", "eswatini": "SWZ",
         "north macedonia": "MKD", "russia": "RUS", "south korea": "KOR", "north korea": "PRK", "laos": "LAO",
         "vietnam": "VNM", "syria": "SYR", "iran": "IRN", "bolivia": "BOL", "venezuela": "VEN", "tanzania": "TZA",
         "moldova": "MDA", "brunei": "BRN", "cape verde": "CPV", "micronesia": "FSM", "federated states of micronesia": "FSM",
         "palestine": "PSE", "state of palestine": "PSE", "taiwan": "TWN", "vatican city": "VAT", "bosnia and herzegovina": "BIH",
         "sao tome and principe": "STP", "saint kitts and nevis": "KNA", "saint lucia": "LCA", "saint vincent and the grenadines": "VCT",
         "trinidad and tobago": "TTO", "antigua and barbuda": "ATG", "united arab emirates": "ARE", "dominican republic": "DOM",
         "central african republic": "CAF", "equatorial guinea": "GNQ", "papua new guinea": "PNG", "solomon islands": "SLB",
         "hong kong": "HKG", "macau": "MAC", "puerto rico": "PRI", "kosovo": "XKX", "turkey": "TUR", "turkiye": "TUR",
         "myanmar": "MMR", "burma": "MMR", "china": "CHN", "people s republic of china": "CHN", "netherlands": "NLD",
         "the netherlands": "NLD", "philippines": "PHL", "the philippines": "PHL", "curacao": "CUW", "england": "GBR",
         "scotland": "GBR", "wales": "GBR", "northern ireland": "GBR", "faroe islands": "FRO", "greenland": "GRL"}
IOC = {"GER": "DEU", "NED": "NLD", "SUI": "CHE", "BUL": "BGR", "CRO": "HRV", "ESA": "SLV", "GUA": "GTM", "POR": "PRT",
       "GRE": "GRC", "DEN": "DNK", "SLO": "SVN", "LAT": "LVA", "MGL": "MNG", "PHI": "PHL", "INA": "IDN", "MAS": "MYS",
       "VIE": "VNM", "RSA": "ZAF", "CHI": "CHL", "URU": "URY", "PAR": "PRY", "CRC": "CRI", "HON": "HND", "NCA": "NIC",
       "HAI": "HTI", "BAR": "BRB", "TRI": "TTO", "ANT": "ATG", "IRI": "IRN", "KSA": "SAU", "UAE": "ARE", "LIB": "LBN",
       "ALG": "DZA", "MAD": "MDG", "ZIM": "ZWE", "ZAM": "ZMB", "TAN": "TZA", "NGR": "NGA", "ANG": "AGO", "SRI": "LKA",
       "NEP": "NPL", "BAN": "BGD", "MYA": "MMR", "CAM": "KHM", "TPE": "TWN", "KOS": "XKX", "MON": "MCO", "SKN": "KNA",
       "VIN": "VCT", "LCA": "LCA", "GRN": "GRD", "BIZ": "BLZ", "PUR": "PRI", "ARU": "ABW", "AHO": "CUW", "FIJ": "FJI",
       "SAM": "WSM", "TGA": "TON", "VAN": "VUT", "SOL": "SLB", "MRI": "MUS", "SEY": "SYC", "BOT": "BWA", "LES": "LSO",
       "SWZ": "SWZ", "GAM": "GMB", "GBS": "GNB", "GEQ": "GNQ", "CGO": "COG", "COD": "COD", "CHA": "TCD", "NIG": "NER",
       "BUR": "BFA", "TOG": "TGO", "BEN": "BEN", "MTN": "MRT", "LBA": "LBY", "SUD": "SDN", "OMA": "OMN", "KUW": "KWT",
       "BRU": "BRN", "ISV": "VIR", "IVB": "VGB", "CAY": "CYM", "BER": "BMU", "GBR": "GBR", "UK": "GBR", "USA": "USA"}


def to_iso(s):
    s = s.strip()
    if re.fullmatch(r"[A-Z]{2,3}", s):
        i = IOC.get(s, s)
        return i if i in geo else None
    n = norm(s)
    return ALIAS.get(n) or name2iso.get(n)


par = {q: set(r.get("par", [])) for q, r in CL.items()}


def ancestors(qs):
    seen, stack = set(), list(qs)
    while stack:
        x = stack.pop()
        for p in par.get(x, ()):
            if p not in seen:
                seen.add(p); stack.append(p)
    return seen | set(qs)


def kind_of(q):
    n = NL.get(q)
    if not n:
        return None
    anc = set(n["anc"])
    base = set(n["p31"]) | set(n["p279"]) | {q}
    fam = family(ancestors(base), q)
    if "Q134768" in anc or "Q134768" in base:
        return "cocktail"
    if q in CL or "Q154" in anc:
        return fam if fam and fam != "other" else "alcohol"
    if "Q6097" in anc or q == "Q6097":
        return "tea"
    if "Q8486" in anc or q == "Q8486":
        return "coffee"
    if "Q40050" in anc:
        return "soft"
    return None


def parse(text, src):
    out = []
    for ln in text.split("\n"):
        m = re.match(r"^\*+\s*'*\s*\{\{\s*(?:[Ff]lag(?:country|icon)?\s*\|\s*)?([^}|]+)[^}]*\}\}\s*'*\s*:?\s*'*\s*:?(.*)$", ln)
        if not m:
            continue
        iso = to_iso(m.group(1))
        if not iso:
            continue
        body = re.sub(r"<ref[^>]*/>", "", re.sub(r"<ref.*?(</ref>|$)", "", m.group(2), flags=re.S))
        body = re.sub(r"\{\{[^{}]*\}\}", "", body)
        drinks = []
        for lm in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]", body):
            t = lm.group(1).strip()
            res = LINKS.get(t) or LINKS.get(t[:1].upper() + t[1:])
            q = res[1] if res else None
            k = kind_of(q) if q else None
            if k:
                disp = re.sub(r"\s*\(.*?\)$", "", (lm.group(2) or t)).strip()
                if q not in [d["q"] for d in drinks]:
                    drinks.append({"q": q, "n": disp[:1].upper() + disp[1:], "w": res[0], "k": k})
        text_plain = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", body)
        text_plain = re.sub(r"'{2,}", "", text_plain).strip()
        if not drinks:  # no classified link: take the first named drink from the text, classified by a few words
            first = re.split(r"[,.;(]| and | is ", re.sub(r"^\(US\):\s*", "", text_plain))[0].strip()
            if first and len(first) <= 40 and not re.match(r"(?i)there|technically|most |kabisa", first):
                fl = first.lower()
                k = ("tea" if re.search(r"\btea\b|lahpet", fl) else "coffee" if "coffee" in fl else "trad" if "sorghum" in fl
                     else "beer" if "beer" in fl and "ginger" not in fl else "soft" if re.search(r"kava|sakau|juice|lemonade|ginger beer|alouda", fl)
                     else "unclassified")
                drinks.append({"q": "", "n": first, "w": "", "k": k})
        out.append({"iso": iso, "src": src, "drinks": drinks, "text": text_plain[:600]})
    return out


nat = parse(P["wikipedia"]["National drink"]["text"], "national drink")
liq = parse(P["wikipedia"]["List of national liquors"]["text"], "national liquor")
for r in liq:  # everything in the liquors list is a spirit
    for d in r["drinks"]:
        if d["k"] in ("unclassified", "soft", "tea", "coffee", "alcohol"):
            d["k"] = "spirit"
by = {}
for r in nat + liq:
    e = by.setdefault(r["iso"], {"drinks": [], "liquors": [], "text": [], "ltext": []})
    if r["src"] == "national drink":
        e["drinks"] += [d for d in r["drinks"] if d["q"] not in [x["q"] for x in e["drinks"]]]
        e["text"].append(r["text"])
    else:
        e["liquors"] += [d for d in r["drinks"] if d["q"] not in [x["q"] for x in e["liquors"]]]
        e["ltext"].append(r["text"])
for iso, e in by.items():
    e["first"] = e["drinks"][0]["k"] if e["drinks"] else None
    alc = [d for d in e["drinks"] if d["k"] not in ("tea", "coffee", "soft")]
    e["first_alc"] = alc[0]["k"] if alc else (e["liquors"][0]["k"] if e["liquors"] else None)
print(len(by), "countries;", sum(1 for e in by.values() if e["drinks"]), "with a national drink;",
      sum(1 for e in by.values() if e["liquors"]), "with a national liquor")
print(Counter(e["first"] for e in by.values()).most_common())
print(Counter(e["first_alc"] for e in by.values()).most_common())
jsave(by, f"{WORK}/national.json")
with open(f"{DATA}/national_drinks.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["country_iso3", "list", "order", "drink", "wikipedia_title", "wikidata", "kind"])
    for iso in sorted(by):
        for lst, key in (("national drink", "drinks"), ("national liquor", "liquors")):
            for i, d in enumerate(by[iso][key], 1):
                w.writerow([iso, lst, i, dash(d["n"]), dash(d["w"]), d["q"], d["k"]])
