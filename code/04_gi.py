"""Geographical indications for drinks (EU eAmbrosia register) and wine regions and appellations (Wikidata).

eAmbrosia
- Drink GIs: product type 'Wine' or 'Spirit drink', or a 'Food' GI whose customs code is 2203 (beer), 2204 (wine),
  2205 (aromatised wine), 2206 (cider, perry and other fermented drinks) or 2208 (spirits).
- Kept: registered, published and applied for; left out: cancelled and rejected (counted).
- Place: (1) the Wikidata item that carries the GI's eAmbrosia ID (P9854), its coordinates or its location's; or
  (2) a Wikidata item with coordinates whose label in a language of the GI's country (or English) equals the
  protected name (or the name without a bracketed part or a generic prefix such as 'Vin de pays'), in the same
  country: the best match is a wine region or appellation, then the item with the most sitelinks (so a region or
  well-known town beats a namesake hamlet). Unplaced GIs are counted by country only.
- Spirit and cider GIs get a family from words in their name (whisky, gin, rum, brandy, grappa, ouzo, liqueur...).
Wikidata wine regions and appellations: items that are wine regions, AOC, DOC, DOCG, DO, DOCa, IGT, vin de pays,
American Viticultural Areas, appellations or New Zealand GIs, with coordinates (own or of their location).
Outputs: data/gi_drinks.csv, data/wine_regions.csv, work/gi.json, work/wineregions.json
"""
import csv, urllib.parse
from collections import Counter
from common import *
from geo import country_at, region_at

P = jload(f"{WORK}/parsed.json")
PL = P["places"]
A2 = {v["a2"]: k for k, v in jload(f"{DATA}/countries_geo.json").items() if v.get("a2")}
A2.update({"GB": "GBR", "FR": "FRA", "NO": "NOR", "XI": "GBR", "EL": "GRC", "UK": "GBR"})


def cat(r):
    cn = " ".join(r["cn"])
    if r["pt"] == "Wine":
        return "aromatised" if cn.startswith("2205") else "wine"
    if r["pt"] == "Spirit drink":
        return "spirits"
    for code, c in (("2203", "beer"), ("2204", "wine"), ("2205", "aromatised"), ("2206", "fermented"), ("2208", "spirits")):
        if re.search(r"(^|\s)" + code, cn):
            return c
    return None


SPW = [("whisky", r"whisk"), ("asian", r"wu liang|moutai|jian nan chun|gao lu|ban dao jing"), ("rice", r"shaoxing|nuo mi"),
       ("gin", r"\bgin\b|genever|jenever|geneva|genièvre|wacholder|borovi|steinh[aä]ger|p[eè]ket"),
       ("liqueur", r"liqueur|lik[oö]r|liquore|licor|ratafia|cr[eè]me de|amaro|bitter|nocino|limoncello|mirto|kr[uú]pnik|nalewk|kräuter|vermut|cherry|ginjinha|pachar[aá]n|patxaran|k[uü]mmel|g[eé]n[eé]p|cassis|trauktin|bärenfang|irish cream|blutwurz|b[aä]rwurz|pelinkov|tentoura|koum kouat|punsch|herbero|aperitivo|palo de|cantueso|hierbas|herbes|j[aä]g[ae]rtee|h[uü]ttentee|maraschino|kitro|poncha|ronmiel|pommeau|devynerios"),
       ("rum", r"\brum\b|\brhum|inländerrum|ron de|cacha|^cuba$"), ("agave", r"tequila|mezcal"), ("vodka", r"vodka|w[oó]dka|vodca|\bvodk"),
       ("anise", r"ouzo|tsipouro|anis|an[ií]s|pastis|rak[iı]\b|mastic|absinth|chinch[oó]n"),
       ("brandy", r"brand|cognac|armagnac|grappa|rakij|rakia|rakya|ракия|p[aá]linka|p[aă]linc|calvados|eau[- ]de[- ]vie|obstler|schnaps|slivovic|sliwovitz|śliwowica|sljivovic|šljivovica|pisco|tresterbrand|bagaceira|orujo|aguardente|aguardiente|marc |marc$|trester|kirsch|zwetschg|weinbrand|vinars|zivania|tsikoudia|williams|poire|mirabelle|framboise|himbeergeist|quetsch|horinc|fine bordeaux|fine de bourgogne|loza|sadjevec|aprikot|distillato|marille|gravensteiner|golden delicious|medronho|pregler|travarica|fruit|komovica|lozovača|horilka|horinca|t[uu]ica|țuică|pálenka|destilado|brinjevec|kornbrand|korn\b")]
CIW = r"cid|sidra|sagardo|apfelwein|apfelmost|poir|perry|most\b|viez|pomm"


def spfam(name):
    n = name.lower()
    for k, rx in SPW:
        if re.search(rx, n):
            return k
    return "spirit"


GEOCLS = {"Q2140699", "Q1565828", "Q654824", "Q2305591", "Q3139487", "Q95556874", "Q1410822", "Q2140793", "Q166247", "Q2858704",
          "Q20723149", "Q117085231"}
geo_items = {r["q"] for r in P["geo"]}
SETTLE = {"Q515", "Q3957", "Q532", "Q484170", "Q747074", "Q2039348", "Q262166", "Q1549591", "Q15284", "Q5119", "Q1637706",
          "Q3184121", "Q123705", "Q16110", "Q2177636", "Q1906268", "Q36784", "Q10864048", "Q82794", "Q1620908", "Q15978299",
          "Q50337", "Q2072997", "Q1115575", "Q956214", "Q106658", "Q6465", "Q36784", "Q22865", "Q192287", "Q3191695", "Q23442"}

# eAmbrosia id -> Wikidata item with coordinates
byeam = {}
for r in P["eam"] + P["inst"] + P["classes"] + P["geo"]:
    for e in r.get("eam", []) or []:
        pt = r["c"]
        if not pt:
            for q in r.get("locs", []):
                p = PL.get(q)
                if p and p["c"] and not p["iso3"]:
                    pt = p["c"]; break
        if e not in byeam or (pt and not byeam[e][1]):
            byeam[e] = (r["q"], pt, r["l"], urllib.parse.unquote(r.get("w") or "").replace("_", " "))
gm = {}
for m in P["gimatch"]:
    gm.setdefault((m["name"], m["iso2"]), []).append(m)


def best_match(names, iso2):
    cands = []
    for n in names:
        for v in {n, re.sub(r"\s*\(.*?\)\s*", " ", n).strip(),
                  re.sub(r"^(Vino de la Tierra|Vino de Pago|Vinho Regional|Vin de pays|Vin de Pays|Pays d'|Pays de|Landwein|Côtes de|Coteaux de|Coteaux du|Côtes du)\s*", "", n).strip()}:
            cands += gm.get((v, iso2), [])
    if not cands:
        return None

    def score(m):
        cl = set(m["cls"])
        return (1 if (m["q"] in geo_items or cl & GEOCLS) else 0, m["sl"])
    return max(cands, key=score)


gis, dropped = [], Counter()
for r in P["eambrosia"]["rows"]:
    c = cat(r)
    if not c:
        continue
    if r["st"] in ("CANCELLED", "REJECTED") or r.get("rm"):
        dropped[r["st"] or "removed"] += 1; continue
    cc = [x.upper() for x in r["c"] or []]
    isos = [A2.get(x) for x in cc if A2.get(x)]
    if not isos:
        dropped["no country"] += 1; continue
    names = [n for n in r["names"] if n]
    name = names[0]
    fam = {"wine": "wine", "aromatised": "wine", "beer": "beer", "spirits": spfam(" ".join(names))}.get(c)
    if c == "fermented":
        nm = " ".join(names).lower()
        fam = "wine" if re.search(r"gl[uü]hwein|bermet", nm) else "trad" if re.search(r"podpiwek|şalgam|salgam|mei gui", nm) else "cider"
    pt, how, wq, wl = None, "", "", ""
    if r["id"] in byeam and byeam[r["id"]][1]:
        wq, pt, wl, _ = byeam[r["id"]]; how = "Wikidata eAmbrosia ID"
    elif len(cc) == 1:
        m = best_match(names, cc[0])
        if m:
            wq, pt, how = m["q"], m["c"], "name match"
    if pt and country_at(*pt, tol=1.0) not in isos:
        pt, how = None, ""
    reg = region_at(*pt, iso=isos[0]) if pt else None
    year = (r.get("rd") or r.get("pd") or r.get("ad") or "")[-4:]
    gis.append({"id": r["id"], "file": r["file"], "type": r["t"], "cat": c, "fam": fam, "name": dash(" / ".join(names)), "iso": isos[0],
                "isos": isos, "status": r["st"], "third": bool(r["third"]), "year": year, "lon": pt[0] if pt else None,
                "lat": pt[1] if pt else None, "how": how, "wq": wq, "reg": reg or ""})
print(len(gis), "drink GIs;", dict(dropped))
print(Counter(g["cat"] for g in gis), Counter(g["status"] for g in gis))
print("placed", sum(1 for g in gis if g["lat"] is not None), Counter(g["how"] for g in gis))
print(Counter(g["fam"] for g in gis if g["cat"] == "spirits").most_common())
print(Counter(g["iso"] for g in gis).most_common(15))

# Wikidata wine regions and appellations
LAB = {"Q2140699": "wine region", "Q1565828": "AOC", "Q654824": "DOC", "Q2305591": "DOCG", "Q3139487": "DO", "Q95556874": "DOCa",
       "Q1410822": "IGT", "Q2140793": "vin de pays", "Q166247": "American Viticultural Area", "Q2858704": "appellation",
       "Q20723149": "AOP (Switzerland)", "Q117085231": "geographical indication (New Zealand)"}
wr = []
for r in P["geo"]:
    pt = r["c"]
    if not pt:
        for q in r.get("locs", []):
            p = PL.get(q)
            if p and p["c"] and not p["iso3"]:
                pt = p["c"]; break
    if not pt or not r["l"]:
        continue
    iso = country_at(*pt)
    if not iso:
        continue
    kind = next((LAB[c] for c in r.get("cls", []) if c in LAB), "wine region")
    wr.append({"q": r["q"], "n": r["l"], "kind": kind, "iso": iso, "lon": pt[0], "lat": pt[1], "reg": region_at(*pt, iso=iso) or "",
               "sl": r["sl"], "w": urllib.parse.unquote(r["w"]).replace("_", " ") if r["w"] else "", "desc": r.get("desc", "")})
print(len(wr), "Wikidata wine regions/appellations with a point;", Counter(w["iso"] for w in wr).most_common(10))

jsave(gis, f"{WORK}/gi.json")
jsave(wr, f"{WORK}/wineregions.json")
with open(f"{DATA}/gi_drinks.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["eambrosia_id", "file_number", "gi_type", "category", "family", "protected_names", "country_iso3", "all_countries", "status",
                "third_country", "year", "lat", "lon", "placed_by", "wikidata_place", "region"])
    for g in sorted(gis, key=lambda g: (g["iso"], g["cat"], g["name"])):
        w.writerow([g["id"], g["file"], g["type"], g["cat"], g["fam"], g["name"], g["iso"], "|".join(g["isos"]), g["status"], g["third"],
                    g["year"], g["lat"], g["lon"], g["how"], g["wq"], g["reg"]])
with open(f"{DATA}/wine_regions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["wikidata", "name", "kind", "country_iso3", "region", "lat", "lon", "sitelinks", "enwiki", "description"])
    for x in sorted(wr, key=lambda x: (x["iso"], x["n"])):
        w.writerow([x["q"], dash(x["n"]), x["kind"], x["iso"], x["reg"], x["lat"], x["lon"], x["sl"], dash(x["w"]), dash(x["desc"])])
