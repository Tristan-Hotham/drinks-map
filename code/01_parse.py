"""Parse the browser bundles into tidy tables in the work folder (in memory, /dev/shm).

Inputs (read in place from RAW, see common.py):
- drinks_wd_eam_part2.json.gz: Wikidata via QLever (drink classes, drink items, wine regions and appellations,
  items with an eAmbrosia ID, wineries/breweries/distilleries/sake breweries/cider mills, grape varieties, and the
  places they refer to) plus the EU eAmbrosia register of geographical indications.
- drinks_wd_wp_part1.json.gz: English Wikipedia wikitext of 'List of national drinks' and 'List of national
  liquors' with every link resolved to its Wikidata item (its Wikidata tables are superseded by part 2).
- drinks_osm_part3.json.gz (if present): OpenStreetMap craft=winery/brewery/distillery/cider points via Overpass,
  and the Wikidata classes of the drinks named in the national lists.
"""
from common import *

p2 = jload(f"{RAW}/drinks_wd_eam_part2.json.gz")
p1 = jload(f"{RAW}/drinks_wd_wp_part1.json.gz")
T = {k: tsv(v) for k, v in p2["q"].items()}
O3 = f"{RAW}/drinks_osm_part3.json.gz"
p3 = jload(O3) if os.path.exists(O3) else None
if p3:  # rum, kvass, kumis and tuba have no route to 'alcoholic beverage' in Wikidata's class tree: added separately
    S = {k: tsv(v) for k, v in p3["supplement"]["q"].items()}
    for k in ["classes", "inst"]:
        have = {r["i"] for r in T[k]}
        T[k] += [r for r in S[k] if r["i"] not in have]
    have = {r["x"] for r in T["places"]}
    T["places"] += [r for r in S["places"] if r["x"] not in have]
O5 = f"{RAW}/drinks_brands_part5.json.gz"
p5 = jload(O5) if os.path.exists(O5) else None
ANYLAB = {}
if p5:  # brands: items that are alcohol brands, or brands whose product (P1056) is a drink; any-language labels
    B = tsv(p5["q"]["brands"])
    have = {r["i"] for r in T["inst"]}
    for r in B:
        r["brand"] = "1"
    bidx = {r["i"]: r for r in B}
    for r in T["inst"]:
        if r["i"] in bidx:
            r["prod"] = bidx[r["i"]].get("prod", ""); r["brand"] = "1"
            for f in ["manu", "locs"]:
                r[f] = "|".join(sorted(set(split(r.get(f, "")) + split(bidx[r["i"]].get(f, "")))))
    T["inst"] += [r for r in B if r["i"] not in have]
    have = {r["x"] for r in T["places"]}
    for t in p5["q"]["places"]:
        T["places"] += [r for r in tsv(t) if r["x"] not in have]
    ANYLAB = {r["i"]: r["lab"] for r in tsv(p5["q"]["labels"])}


def qid(v):
    return v.rsplit("/", 1)[-1] if v else ""


def qids(v):
    return [qid(x) for x in split(v)]


def coord(v):
    m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", v or "")
    if not m:
        return None
    lon, lat = float(m.group(1)), float(m.group(2))
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return None
    return [round(lon, 4), round(lat, 4)]


def label(r):
    return r.get("lab") or r.get("labm") or ANYLAB.get(r.get("i", ""), "")


def wiki(r):
    e = r.get("enwiki") or ""
    return e.replace("https://en.wikipedia.org/wiki/", "") if e else ""


out = {}
for k in ["classes", "inst", "geo", "eam", "prod", "grapes"]:
    rows = []
    for r in T[k]:
        d = {"q": r["i"], "l": label(r), "sl": int(r.get("sitelinks") or 0), "w": wiki(r), "c": coord(r.get("coord"))}
        if r.get("brand"):
            d["brand"] = 1
        for f in ["par", "cls", "origin", "p17", "manu", "locs", "type", "colour", "prod"]:
            if f in r:
                d[f] = qids(r[f])
        for f in ["desc", "inception", "dissolved"]:
            if r.get(f):
                d[f] = r[f][:10] if f != "desc" else r[f]
        if r.get("eam"):
            d["eam"] = split(r["eam"])
        rows.append(d)
    out[k] = rows
    print(k, len(rows))

places = {}
for r in T["places"]:
    if not r["x"].startswith("Q"):
        continue
    places[r["x"]] = {"l": label(r), "c": coord(r.get("coord")), "hq": coord(r.get("hq")), "p17": qids(r.get("p17")),
                      "iso3": r.get("iso3") or "", "cls": qids(r.get("cls")), "par": qids(r.get("par"))}
out["places"] = places
print("places", len(places))

eam = p2["eambrosia"]
out["eambrosia"] = {"rows": eam["rows"], "retrieved": eam["retrieved"], "total_reported": eam["total_elements_reported"]}
print("eAmbrosia", len(eam["rows"]))

wp = p1["wikipedia"]["pages"]
out["wikipedia"] = {"National drink": wp["National drink"], "List of national liquors": wp["List of national liquors"], "links": wp["_links"]}

if p3:
    out["osm"] = p3.get("osm", {})
    out["natlinks"] = [{"q": r["i"], "l": r.get("lab", ""), "p31": qids(r.get("p31")), "p279": qids(r.get("p279")),
                        "origin": qids(r.get("origin")), "anc": qids(r.get("anc"))} for r in tsv(p3["natlinks"]["tsv"])]
    print("osm", {k: len(v) for k, v in out["osm"].get("data", {}).items()}, "natlinks", len(out["natlinks"]))

O4 = f"{RAW}/drinks_gi_match_part4.json.gz"
if os.path.exists(O4):
    gm = []
    for t in jload(O4)["tsv"]:
        for r in tsv(t):
            c = coord(r.get("co"))
            if c:
                gm.append({"name": r["name"], "iso2": r["iso"], "q": qid(r["x"]), "c": c, "sl": int(r.get("sl") or 0), "cls": qids(r.get("cls"))})
    out["gimatch"] = gm
    print("GI name matches", len(gm))

jsave(out, f"{WORK}/parsed.json")
print("saved", os.path.getsize(f"{WORK}/parsed.json") // 1024, "KB")
