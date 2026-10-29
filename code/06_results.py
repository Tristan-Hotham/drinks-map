"""Every number used in the page, paper, blog and collage (data/results.json), and the page data.

Page data: data/site.json (embedded in index.html), data/points.json (named drinks, Wikidata producers, GIs and wine
regions with a point), data/osm.json (OpenStreetMap producers, loaded when zoomed in), data/regions.json (the
food-map regions of countries with at least one placed record).
"""
import csv
from collections import Counter, defaultdict
from common import *
from families import FAMS, KEY, GROUP, GROUPS, SPIRITS
from geo import REGNAME, CNAME

P = jload(f"{WORK}/parsed.json")
D = jload(f"{WORK}/drinks.json")
PR = jload(f"{WORK}/producers.json")
O = jload(f"{WORK}/osm.json")
G = jload(f"{WORK}/gi.json")
WR = jload(f"{WORK}/wineregions.json")
N = jload(f"{WORK}/national.json")
GEO = jload(f"{DATA}/countries_geo.json")
PL = P["places"]
GK = [g[0] for g in GROUPS]
FK = [f[0] for f in FAMS]
pct = lambda a, b: round(100 * a / b, 1) if b else 0


def gfam(f):
    return GROUP.get(f, f)


def iso_of_q(q, depth=0):
    p = PL.get(q)
    if not p:
        return None
    if p["iso3"]:
        return p["iso3"] if p["iso3"] in GEO else None
    if depth < 2:
        for k in p["p17"]:
            if k != q:
                i = iso_of_q(k, depth + 1)
                if i:
                    return i
    return None


R = {"retrieved": "29 October 2026", "meta": {"doi": DOI, "retrieved": "29 October 2026", "page": PAGE, "repo": REPO, "blog": BLOG}}

# ---- named drinks
grp = Counter(d["grp"] for d in D)
fam = Counter(d["fam"] for d in D)
kinds = Counter(d["kind"] for d in D)
R["drinks"] = {"n": len(D), "n_types": kinds["type"], "n_products": kinds["product"], "n_point": sum(1 for d in D if d["lat"] is not None),
               "n_countries": len({d["iso"] for d in D}), "by_group": {g: grp[g] for g in GK}, "by_family": {f: fam[f] for f in FK},
               "point_from": dict(Counter(d["psrc"] or "none" for d in D))}
for g in GK:
    c = Counter(d["iso"] for d in D if d["grp"] == g)
    tot = sum(c.values())
    R["drinks"][f"top_{g}"] = [{"iso": i, "name": CNAME.get(i, i), "n": n, "pct": pct(n, tot)} for i, n in c.most_common(8)]
bc = Counter(d["iso"] for d in D if d["grp"] == "beer")
R["drinks"]["beer_top3_pct"] = pct(sum(n for _, n in bc.most_common(3)), grp["beer"])
wc = Counter(d["iso"] for d in D if d["grp"] == "wine")
R["drinks"]["wine_fra_ita_pct"] = pct(wc["FRA"] + wc["ITA"], grp["wine"])
mc = Counter(d["manu"] for d in D if d["grp"] == "beer" and d["manu"])
R["drinks"]["beer_top_makers"] = [{"name": dash(m), "n": n} for m, n in mc.most_common(5)]
R["drinks"]["beer_products_pct"] = pct(sum(1 for d in D if d["grp"] == "beer" and d["kind"] == "product"), grp["beer"])
sp = Counter(d["iso"] for d in D if d["grp"] == "spirits")
R["drinks"]["n_spirits_countries"] = len(sp)
types = [d for d in D if d["kind"] == "type"]
tc = Counter(d["iso"] for d in types)
R["drinks"]["types_top"] = [{"iso": i, "name": CNAME.get(i, i), "n": n} for i, n in tc.most_common(10)]
R["drinks"]["types_countries"] = len(tc)
R["drinks"]["types_by_group"] = {g: sum(1 for d in types if d["grp"] == g) for g in GK}

# ---- producers
pg = Counter(p["grp"] for p in PR)
og = Counter(o[2] for o in O)
R["producers"] = {"wikidata_n": len(PR), "wikidata_point": sum(1 for p in PR if p["lat"] is not None),
                  "wikidata_by_group": {g: pg[g] for g in GK if pg[g]}, "osm_n": len(O), "osm_by_group": {g: og[g] for g in GK if og[g]},
                  "osm_countries": len({o[3] for o in O if o[3]}), "osm_no_country": sum(1 for o in O if not o[3])}
for g in ["wine", "beer", "spirits"]:
    c = Counter(o[3] for o in O if o[2] == g and o[3])
    R["producers"][f"osm_top_{g}"] = [{"iso": i, "name": CNAME.get(i, i), "n": n, "pct": pct(n, og[g])} for i, n in c.most_common(8)]
    rc = Counter(o[5] for o in O if o[2] == g and o[5])
    R["producers"][f"osm_topreg_{g}"] = [{"k": k, "name": REGNAME.get(k, k), "iso": k.split(":")[0], "n": n} for k, n in rc.most_common(8)]
R["producers"]["sake_wikidata"] = pg["rice"]
R["producers"]["sake_top"] = [{"iso": i, "n": n} for i, n in Counter(p["iso"] for p in PR if p["grp"] == "rice").most_common(3)]

# ---- geographical indications
gc = Counter(g["cat"] for g in G)
R["gi"] = {"n": len(G), "by_cat": dict(gc), "n_registered": sum(1 for g in G if g["status"] == "REGISTERED"),
           "n_pending": sum(1 for g in G if g["status"] != "REGISTERED"), "n_third": sum(1 for g in G if g["third"]),
           "third_countries": sorted({g["iso"] for g in G if g["third"]}), "n_countries": len({g["iso"] for g in G}),
           "placed": sum(1 for g in G if g["lat"] is not None), "placed_by": dict(Counter(g["how"] or "not placed" for g in G)),
           "spirit_families": dict(Counter(g["fam"] for g in G if g["cat"] == "spirits")), "total_register": len(P["eambrosia"]["rows"]),
           "total_reported": P["eambrosia"]["total_reported"],
           "cancelled_rejected": sum(1 for r in P["eambrosia"]["rows"] if r["st"] in ("CANCELLED", "REJECTED"))}
R["gi"]["placed_pct"] = pct(R["gi"]["placed"], R["gi"]["n"])
for c in ["wine", "spirits"]:
    cc = Counter(g["iso"] for g in G if g["cat"] == c)
    R["gi"][f"top_{c}"] = [{"iso": i, "name": CNAME.get(i, i), "n": n} for i, n in cc.most_common(8)]
wreg = Counter(g["reg"] for g in G if g["cat"] in ("wine", "aromatised") and g["reg"])
R["gi"]["wine_top_regions"] = [{"k": k, "name": REGNAME.get(k, k), "iso": k.split(":")[0], "n": n} for k, n in wreg.most_common(10)]
yrs = Counter(int(g["year"]) // 10 * 10 for g in G if g["year"].isdigit())
R["gi"]["by_decade"] = {str(k): yrs[k] for k in sorted(yrs)}
R["gi"]["beer_names"] = sorted(g["name"] for g in G if g["cat"] == "beer")
R["gi"]["cider_n"] = sum(1 for g in G if g["fam"] == "cider")
R["gi"]["cider_by_country"] = dict(Counter(g["iso"] for g in G if g["fam"] == "cider"))
R["wine_regions"] = {"n": len(WR), "by_kind": dict(Counter(w["kind"] for w in WR)), "top": [{"iso": i, "n": n} for i, n in Counter(w["iso"] for w in WR).most_common(6)]}

# ---- grapes
gr = []
for r in P["grapes"]:
    isos = {iso_of_q(q) for q in r.get("origin", [])} - {None}
    if isos and r["l"]:
        gr.append({"q": r["q"], "n": r["l"], "isos": sorted(isos), "sl": r["sl"]})
grc = Counter(i for g in gr for i in g["isos"])
R["grapes"] = {"n_all": len(P["grapes"]), "n_origin": len(gr), "n_countries": len(grc),
               "top": [{"iso": i, "name": CNAME.get(i, i), "n": n} for i, n in grc.most_common(10)]}

# ---- national drinks
fk = Counter(e["first"] for e in N.values() if e["drinks"])
R["national"] = {"n_countries": len(N), "n_drink": sum(1 for e in N.values() if e["drinks"]), "n_liquor": sum(1 for e in N.values() if e["liquors"]),
                 "first_kind": dict(fk), "first_alc_kind": dict(Counter(e["first_alc"] for e in N.values() if e["first_alc"]))}
nonalc = sum(n for k, n in fk.items() if k in ("tea", "coffee", "soft"))
R["national"]["first_nonalc"] = nonalc
R["national"]["first_nonalc_pct"] = pct(nonalc, R["national"]["n_drink"])
R["national"]["first_spirits"] = sum(n for k, n in fk.items() if k in SPIRITS)
R["national"]["first_tea"] = fk["tea"]; R["national"]["first_coffee"] = fk["coffee"]
lq = Counter(d["k"] for e in N.values() for d in e["liquors"][:1])
R["national"]["liquor_first_kind"] = dict(lq)
named = Counter(d["n"].lower() for e in N.values() for d in e["drinks"] + e["liquors"])
R["national"]["most_named"] = [{"n": k, "count": v} for k, v in named.most_common(8)]

# ---- headline per-country records (all sources)
rec = defaultdict(Counter)
for d in D:
    rec[d["iso"]][d["grp"]] += 1
for p in PR:
    if p["grp"]:
        rec[p["iso"]][p["grp"]] += 1
for o in O:
    if o[3]:
        rec[o[3]][o[2]] += 1
for g in G:
    rec[g["iso"]][gfam(g["fam"])] += 1
R["records"] = {"n": sum(sum(c.values()) for c in rec.values()), "n_countries": len(rec),
                "top": [{"iso": i, "name": CNAME.get(i, i), "n": sum(c.values())} for i, c in sorted(rec.items(), key=lambda x: -sum(x[1].values()))[:10]]}
R["records"]["europe_pct"] = pct(sum(sum(c.values()) for i, c in rec.items() if GEO.get(i, {}).get("continent") == "Europe"), R["records"]["n"])
cont = Counter()
for i, c in rec.items():
    cont[GEO.get(i, {}).get("continent") or "Other"] += sum(c.values())
R["records"]["by_continent"] = [{"name": k, "n": v, "pct": pct(v, R["records"]["n"])} for k, v in cont.most_common()]
R["records"]["africa"] = sum(sum(c.values()) for i, c in rec.items() if GEO.get(i, {}).get("continent") == "Africa")
R["records"]["africa_pct"] = pct(R["records"]["africa"], R["records"]["n"])

# a few anchored examples for the text (looked up, not typed)
def find(name, iso):
    for d in D:
        if d["n"].lower() == name.lower() and d["iso"] == iso:
            return {"n": d["n"], "iso": iso, "fam": d["fam"], "sl": d["sl"]}
    return None
R["examples"] = {k: find(*v) for k, v in {"tequila": ("tequila", "MEX"), "baijiu": ("baijiu", "CHN"), "soju": ("soju", "KOR"),
                                          "sake": ("sake", "JPN"), "pisco": ("pisco", "PER"), "kolsch": ("Kölsch", "DEU"),
                                          "cognac": ("cognac", "FRA"), "scotch": ("Scotch whisky", "GBR")}.items()}

R["cards"] = {"mex_liquors": len(N["MEX"]["liquors"]), "bgr_spirits": sum(1 for g in G if g["iso"] == "BGR" and g["cat"] == "spirits"),
              "bgr_grozdova": sum(1 for g in G if g["iso"] == "BGR" and "grozdova" in g["name"].lower()),
              "beer_cze_deu": sum(1 for g in G if g["cat"] == "beer" and g["iso"] in ("CZE", "DEU"))}

# ---- page data
fi = {f: i for i, f in enumerate(FK)}
gi_ = {g: i for i, g in enumerate(GK)}
pts = {"cols": {"drinks": ["lon", "lat", "fam", "name", "sitelinks", "kind", "iso", "wiki", "qid", "place", "maker", "year", "region"],
                "prod": ["lon", "lat", "group", "name", "sitelinks", "iso", "wiki", "qid", "founded", "closed", "region"],
                "gi": ["lon", "lat", "fam", "name", "gi_type", "iso", "category", "placed_by", "eambrosia_id", "year", "region"],
                "wr": ["lon", "lat", "name", "kind", "iso", "sitelinks", "wiki", "region"]}, "drinks": [], "prod": [], "gi": [], "wr": []}
for d in sorted(D, key=lambda d: -d["sl"]):
    if d["lat"] is None:
        continue
    pts["drinks"].append([d["lon"], d["lat"], fi[d["fam"]], dash(d["n"]), d["sl"], 1 if d["kind"] == "type" else 0, d["iso"], dash(d["w"]), d["q"],
                          dash(d["place"]), dash(d["manu"][:60]), d["year"], d["reg"]])
for p in sorted(PR, key=lambda p: -p["sl"]):
    if p["lat"] is None or not p["grp"]:
        continue
    pts["prod"].append([p["lon"], p["lat"], gi_[p["grp"]], dash(p["n"]), p["sl"], p["iso"], dash(p["w"]), p["q"], p["year"], p["closed"], p["reg"]])
for g in G:
    if g["lat"] is None:
        continue
    pts["gi"].append([g["lon"], g["lat"], fi.get(g["fam"], fi["spirit"]), g["name"], g["type"], g["iso"], g["cat"], g["how"], g["id"], g["year"], g["reg"]])
for w in WR:
    pts["wr"].append([w["lon"], w["lat"], dash(w["n"]), w["kind"], w["iso"], w["sl"], dash(w["w"]), w["reg"]])
jsave(pts, f"{DATA}/points.json")
jsave({"cols": ["lon", "lat", "group", "iso", "name", "region"], "groups": GK, "rows": [[o[0], o[1], gi_[o[2]], o[3], dash(o[4]), o[5]] for o in O]}, f"{DATA}/osm.json")

# per country summary for the panel
site = {"fams": [[f[0], f[1], f[2]] for f in FAMS], "groups": [list(g) for g in GROUPS], "cname": {k: v["name"] for k, v in GEO.items()}, "c": {}}
byc = defaultdict(lambda: defaultdict(list))
for d in D:
    byc[d["iso"]][d["fam"]].append(d)
gis_by = defaultdict(list)
for g in G:
    gis_by[g["iso"]].append(g)
grapes_by = defaultdict(list)
for g in gr:
    for i in g["isos"]:
        grapes_by[i].append(g)
osm_by = defaultdict(Counter)
for o in O:
    if o[3]:
        osm_by[o[3]][o[2]] += 1
prod_by = defaultdict(Counter)
for p in PR:
    if p["grp"]:
        prod_by[p["iso"]][p["grp"]] += 1
for iso in set(rec) | set(N):
    e = {"r": {g: rec[iso][g] for g in GK if rec[iso][g]},  # all records by group
         "d": {f: len(byc[iso][f]) for f in FK if byc[iso][f]},  # named drinks by family
         "t": {}, "gi": {}, "o": dict(osm_by[iso]), "p": dict(prod_by[iso])}
    for f in FK:
        L = sorted(byc[iso][f], key=lambda d: (-(d["kind"] == "type"), -d["sl"]))[:8]
        if L:
            e["t"][f] = [[dash(d["n"]), d["sl"], 1 if d["kind"] == "type" else 0, dash(d["w"]), d["q"]] for d in L]
    gl = gis_by.get(iso, [])
    for f in sorted({x["fam"] for x in gl}):
        L = [x for x in gl if x["fam"] == f]
        e["gi"][f] = [len(L)] + [x["name"].split(" / ")[0] for x in L[:6]]
    if grapes_by.get(iso):
        L = sorted(grapes_by[iso], key=lambda g: -g["sl"])
        e["gr"] = [len(L)] + [dash(g["n"]) for g in L[:8]]
    if iso in N:
        n = N[iso]
        e["nd"] = [[dash(d["n"]), d["k"], dash(d["w"])] for d in n["drinks"][:8]]
        e["nl"] = [[dash(d["n"]), d["k"], dash(d["w"])] for d in n["liquors"][:6]]
        e["nk"] = n["first"]; e["na"] = n["first_alc"]
    site["c"][iso] = e
# region counts by group (records with a region: drinks, producers, OSM, GIs, wine regions)
rg = defaultdict(Counter)
for d in D:
    if d["reg"]:
        rg[d["reg"]][d["grp"]] += 1
for p in PR:
    if p["reg"] and p["grp"]:
        rg[p["reg"]][p["grp"]] += 1
for o in O:
    if o[5]:
        rg[o[5]][o[2]] += 1
for g in G:
    if g["reg"]:
        rg[g["reg"]][gfam(g["fam"])] += 1
site["reg"] = {k: dict(v) for k, v in rg.items()}
site["rn"] = {k: REGNAME.get(k, k) for k in rg}
site["cpos"] = {k: [v["lon"], v["lat"], v.get("pop") or 0] for k, v in GEO.items()}
regc = {k.split(":")[0] for k in rg}
full = jload(f"{WORK}/regions_full.json")
jsave({"type": "FeatureCollection", "features": [f for f in full["features"] if f["properties"]["i"] in regc]}, f"{DATA}/regions.json")
R["regions"] = {"n_regions": len(rg), "n_countries": len(regc)}
site["rc"] = {i: 1 for i in sorted(regc)}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: v for k, v in R.items() if k in ("drinks", "producers", "gi", "national", "records", "grapes", "wine_regions", "regions")}, ensure_ascii=False)[:6000])
for f in ["site.json", "points.json", "osm.json", "regions.json"]:
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
