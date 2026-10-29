"""Blog post and meta (release/blog), Zenodo files and meta (release/zenodo).
Zenodo copies of files that also live elsewhere in the repo are hard links, so they take no extra disk."""
import re, shutil, zipfile, json as _json
from common import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
REL = os.path.join(ROOT, "release")
NAME = "Hotham_What_Does_the_World_Drink"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    raise ValueError(f)


# facts stated in words in the blog (alt text included); the page build checks the rest
import importlib.util
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "07_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
tb = [round(c["pct"]) for c in R["drinks"]["top_beer"][:6]]; ob = [round(c["pct"]) for c in R["producers"]["osm_top_beer"][:6]]
assert tb[:3] == [41, 27, 10] and all(2 <= x <= 3 for x in tb[3:]) and [c["iso"] for c in R["drinks"]["top_beer"][3:6]] == ["SWE", "DEU", "GBR"]
assert ob == [32, 10, 8, 8, 5, 4] and [c["iso"] for c in R["producers"]["osm_top_beer"][4:6]] == ["CAN", "ESP"]
sf = R["gi"]["spirit_families"]
assert (sf["brandy"], sf["liqueur"], sf["gin"], sf["rum"], sf["anise"], sf["vodka"], sf["agave"]) == (143, 59, 16, 14, 14, 8, 1)
bc = {c["name"]: c for c in R["records"]["by_continent"]}
assert (bc["Europe"]["n"], bc["Europe"]["pct"], bc["North America"]["n"], bc["North America"]["pct"], bc["Africa"]["n"], bc["Africa"]["pct"]) == (43812, 64.7, 18566, 27.4, 504, 0.7)
assert all(1500 <= bc[k]["n"] <= 1700 for k in ("Asia", "South America", "Oceania"))
assert [t["k"] for t in R["gi"]["wine_top_regions"][:5]] == ["FRA:Bourgogne-Franche-Comté", "FRA:Occitanie", "FRA:Nouvelle-Aquitaine", "ITA:Veneto", "ITA:Piemonte"]
nk = {i: c.get("nk") for i, c in SITE["c"].items()}
assert nk["CHN"] == "tea" and nk["USA"] == "coffee" and nk["ETH"] == "coffee" and nk["RUS"] == "trad" and nk["IND"] == "soft" and nk["AUS"] == "soft"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):  # blog figures not used in the post
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
assert "\u2014" not in vis and "\u2013" not in vis and "--" not in vis
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "What does the world drink? Wine, beer, spirits, sake and national drinks on one map",
        "slug": "drinks-map",
        "excerpt": f"{R['gi']['n']:,} protected drink names, {R['producers']['osm_n']:,} wineries, breweries and distilleries and the national drink of {R['national']['n_drink']} countries, mapped from open data. The national drink is often tea, and the map says as much about who keeps the records as about who drinks.",
        "seo_description": "A world map of where drinks come from: wine, beer, cider, spirits, sake, protected names, producers and national drinks, from open data.",
        "tags": ["drinks", "wine", "beer", "spirits", "national drinks", "maps", "data visualisation", "Wikidata"],
        "header_alt": f"Title card reading 'What does the world drink?' in black and claret on cream, beside a world map dotted with every winery (claret), brewery (amber) and distillery (navy) in OpenStreetMap, dense across Europe, the United States and southern Australia. Text: {R['producers']['osm_n']:,} wineries, breweries and distilleries, {R['gi']['n']:,} protected names and the national drink of {R['national']['n_drink']} countries."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)


def link(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    os.link(src, dst)


link(f"{REL}/{NAME}.pdf", f"{Z}/{NAME}.pdf")
for f in ("gi_drinks.csv", "national_drinks.csv", "wine_regions.csv", "results.json"):
    link(f"{DATA}/{f}", f"{Z}/{f}")
zp = f"{Z}/drinks-map_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"drinks-map/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"drinks-map/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\emph{", "").replace("}", "").replace("\\&", "&")
zmeta = {"title": "What Does the World Drink? Wine, Beer, Cider, Spirits, Sake and National Drinks in Wikidata, Wikipedia, the EU Register of Geographical Indications and OpenStreetMap",
         "description_html": f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/drinks-map/. Data and code: https://github.com/Tristan-Hotham/drinks-map. Blog post: to follow.</p>",
         "keywords": ["drinks", "wine", "beer", "spirits", "sake", "geographical indications", "national drinks", "Wikidata", "OpenStreetMap", "maps"],
         "licence": "cc-by-sa-4.0",
         "related": [{"identifier": "https://github.com/Tristan-Hotham/drinks-map", "relation": "issupplementedby", "resource_type": "software"},
                     {"identifier": "https://maps.tristanhotham.com/drinks-map/", "relation": "issupplementedby", "resource_type": "other"},
                     {"identifier": "https://www.wikidata.org/", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://www.openstreetmap.org/", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://en.wikipedia.org/wiki/List_of_national_drinks", "relation": "isderivedfrom", "resource_type": "other"},
                     {"identifier": "https://en.wikipedia.org/wiki/List_of_national_liquors", "relation": "isderivedfrom", "resource_type": "other"},
                     {"identifier": "https://www.naturalearthdata.com/", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://www.geonames.org/", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://doi.org/10.5281/zenodo.23761260", "relation": "isderivedfrom", "resource_type": "dataset"}]}
jsave(zmeta, f"{Z}/meta.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
print("blog words", words, "; zenodo files", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
