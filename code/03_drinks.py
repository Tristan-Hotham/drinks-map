"""Named drinks (types, styles and brands) and producers from Wikidata; producers from OpenStreetMap.

Named drinks
- Every Wikidata class below 'alcoholic beverage' (Q154) and every item that is an instance of one, plus rum, kvass,
  kumis and tuba, which Wikidata does not connect to Q154. Classes are 'types and styles' (tequila, Kolsch, Rioja);
  instances are 'brands and products' (a named beer, whisky or wine).
- Family: first match of the item's ancestors against the anchors in families.py. Mixed drinks (cocktails),
  alcopops and words that are not drinks of a place are left out.
- Country, in order: country of origin (P495); country (P17); the country of its location (P131, P276, P1071);
  the country of its manufacturer (P176); the country of its point. Historical states are mapped to today's country
  through their own country statement or their coordinates.
- Point, in order: its own coordinates (P625); its location's coordinates (if the location is not a whole country);
  its manufacturer's coordinates or headquarters (P159). Items with only a country are counted but not drawn.
Producers
- Wikidata items that are wineries, breweries, distilleries, sake breweries or cider mills (and subclasses), with
  coordinates (own, or of their location or headquarters).
- OpenStreetMap features tagged craft=winery, brewery, distillery or cider (Overpass, 29 October 2026), with their
  country from the point.
Outputs: data/drinks.csv, data/producers.csv, work/drinks.json, work/producers.json, work/osm.json
"""
import csv, urllib.parse
from collections import Counter, defaultdict
from common import *
from families import FAMS, KEY, GROUP, family
from geo import country_at, region_at

P = jload(f"{WORK}/parsed.json")
PL = P["places"]
CL = {r["q"]: r for r in P["classes"]}
WORLD_ISO = set(jload(f"{DATA}/countries_geo.json"))
FIX = {"SDS": "SSD", "KOS": "XKX"}

# ancestors in the class tree
par = {q: set(r.get("par", [])) for q, r in CL.items()}
anc_cache = {}


def ancestors(q):
    if q in anc_cache:
        return anc_cache[q]
    seen, stack = set(), [q]
    while stack:
        x = stack.pop()
        for p in par.get(x, ()):
            if p not in seen:
                seen.add(p); stack.append(p)
    anc_cache[q] = seen
    return seen


def iso_of_q(q, depth=0):
    """ISO3 of a Wikidata country (or historical state, or any place with a country)."""
    p = PL.get(q)
    if not p:
        return None
    if p["iso3"]:
        i = FIX.get(p["iso3"], p["iso3"])
        return i if i in WORLD_ISO else None
    if depth < 2:
        for k in p["p17"]:
            if k != q:
                i = iso_of_q(k, depth + 1)
                if i:
                    return i
    if p["c"]:
        return country_at(*p["c"])
    return None


def is_country(q):
    p = PL.get(q)
    return bool(p and (p["iso3"] or "Q6256" in p["cls"] or "Q3024240" in p["cls"] or "Q3624078" in p["cls"]))


def wtitle(w):
    return urllib.parse.unquote(w).replace("_", " ") if w else ""


def place_drink(r):
    """returns iso, iso_source, (lon, lat), point_source, place label"""
    iso, isrc = None, ""
    for f, src in (("origin", "origin"), ("p17", "country")):
        for q in r.get(f, []):
            iso = iso_of_q(q)
            if iso:
                isrc = src; break
        if iso:
            break
    pt, psrc, plab = None, "", ""
    if r["c"]:
        pt, psrc = r["c"], "own"
    if not pt:
        for q in r.get("locs", []):
            p = PL.get(q)
            if p and p["c"] and not is_country(q):
                pt, psrc, plab = p["c"], "location", p["l"]; break
    if not pt:
        for q in r.get("manu", []):
            p = PL.get(q)
            if p and (p["c"] or p["hq"]):
                pt, psrc, plab = p["c"] or p["hq"], "manufacturer", p["l"]; break
    if not iso:
        for q in r.get("locs", []):
            iso = iso_of_q(q)
            if iso:
                isrc = "location"; break
    if not iso:
        for q in r.get("manu", []):
            iso = iso_of_q(q)
            if iso:
                isrc = "manufacturer"; break
    if not iso and pt:
        iso = country_at(*pt); isrc = "point" if iso else ""
    if pt and iso and country_at(*pt, tol=1.0) not in (iso, None) and psrc != "own":
        # a manufacturer's head office abroad (a brand owned by a multinational) is not where the drink is from
        pt, psrc, plab = None, "", ""
    return iso, isrc, pt, psrc, plab


drinks, skipped = [], Counter()
seen = set()
for kind, rows in (("type", P["classes"]), ("product", P["inst"])):
    for r in rows:
        q = r["q"]
        if q in seen or q == "Q154":
            continue
        seen.add(q)
        if kind == "type":
            anc = ancestors(q) | {q}
        else:
            anc = set(r.get("cls", [])) | set(r.get("prod", []))
            for c in list(anc):
                anc |= ancestors(c)
        fam = family(anc, q)
        if fam is None:
            skipped["mixed drink or not a drink of a place"] += 1; continue
        if fam == "other":
            skipped["no family"] += 1; continue
        name = r["l"]
        if not name:
            skipped["no English or multilingual label"] += 1; continue
        iso, isrc, pt, psrc, plab = place_drink(r)
        if not iso:
            skipped["no country"] += 1; continue
        manu = [PL[m]["l"] for m in r.get("manu", []) if m in PL and PL[m]["l"]][:2]
        reg = region_at(*pt, iso=iso) if pt else None
        drinks.append({"q": q, "n": name, "kind": kind, "fam": fam, "grp": GROUP[fam], "iso": iso, "isrc": isrc,
                       "lon": pt[0] if pt else None, "lat": pt[1] if pt else None, "psrc": psrc, "place": plab,
                       "reg": reg or "", "manu": "; ".join(manu), "sl": r["sl"], "w": wtitle(r["w"]),
                       "desc": r.get("desc", ""), "year": (r.get("inception") or "")[:4]})
print(len(drinks), "named drinks;", dict(skipped))
print(Counter(d["fam"] for d in drinks).most_common())
print("with point", sum(1 for d in drinks if d["lat"] is not None), Counter(d["psrc"] for d in drinks))

# producers
PTYPE = [("Q29850536", "rice"), ("Q5119518", "cider"), ("Q131734", "beer"), ("Q156362", "wine"), ("Q1251750", "spirits")]
prods = []
for r in P["prod"]:
    grp = next((g for t, g in PTYPE if t in r["type"]), None)
    pt = r["c"]
    if not pt:
        for q in r.get("locs", []):
            p = PL.get(q)
            if p and p["c"] and not is_country(q):
                pt = p["c"]; break
    iso = None
    for q in r.get("p17", []):
        iso = iso_of_q(q)
        if iso:
            break
    if pt and not iso:
        iso = country_at(*pt)
    if not iso or not r["l"]:
        continue
    prods.append({"q": r["q"], "n": r["l"], "grp": grp, "iso": iso, "lon": pt[0] if pt else None, "lat": pt[1] if pt else None,
                  "reg": (region_at(*pt, iso=iso) or "") if pt else "", "year": (r.get("inception") or "")[:4],
                  "closed": (r.get("dissolved") or "")[:4], "sl": r["sl"], "w": wtitle(r["w"]), "desc": r.get("desc", "")})
print(len(prods), "Wikidata producers;", Counter(p["grp"] for p in prods), "with point", sum(1 for p in prods if p["lat"] is not None))

# OpenStreetMap
osm = []
OG = {"winery": "wine", "brewery": "beer", "distillery": "spirits", "cider": "cider"}
for craft, rows in P["osm"]["data"].items():
    for lon, lat, name, cc, wd, prod, brand in rows:
        if lon is None or lat is None:
            continue
        iso = country_at(lon, lat, tol=0.3)
        osm.append([round(lon, 4), round(lat, 4), OG[craft], iso or "", (name or "")[:60], region_at(lon, lat, iso=iso, tol=0.1) or "" if iso else ""])
print(len(osm), "OSM producers;", Counter(o[2] for o in osm), "no country", sum(1 for o in osm if not o[3]))

jsave(drinks, f"{WORK}/drinks.json")
jsave(prods, f"{WORK}/producers.json")
jsave(osm, f"{WORK}/osm.json")
with open(f"{DATA}/drinks.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["wikidata", "name", "kind", "family", "family_label", "group", "country_iso3", "country_from", "lat", "lon", "point_from",
                "place", "region", "manufacturer", "sitelinks", "enwiki", "description", "inception_year"])
    for d in sorted(drinks, key=lambda d: (d["iso"], d["fam"], -d["sl"])):
        w.writerow([d["q"], dash(d["n"]), d["kind"], d["fam"], KEY[d["fam"]][1], d["grp"], d["iso"], d["isrc"], d["lat"], d["lon"], d["psrc"],
                    dash(d["place"]), d["reg"], dash(d["manu"]), d["sl"], dash(d["w"]), dash(d["desc"]), d["year"]])
with open(f"{DATA}/producers.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["source", "id", "name", "group", "country_iso3", "region", "lat", "lon", "founded", "closed", "sitelinks", "enwiki"])
    for p in sorted(prods, key=lambda p: (p["iso"], p["grp"] or "", p["n"])):
        w.writerow(["wikidata", p["q"], dash(p["n"]), p["grp"], p["iso"], p["reg"], p["lat"], p["lon"], p["year"], p["closed"], p["sl"], dash(p["w"])])
    for o in osm:
        w.writerow(["openstreetmap", "", dash(o[4]), o[2], o[3], o[5], o[1], o[0], "", "", "", ""])
