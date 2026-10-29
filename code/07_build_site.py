"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (site.json, world.json, cities) is embedded; data/points.json, data/osm.json and
data/regions.json are loaded by the page. Facts stated in words are checked here. The full-screen map snippet
(/home/claude/hist/_brief/fullscreen_snippet.html, copied to code/fullscreen_snippet.html) is pasted before </body>."""
import json, re, shutil
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
N = jload(f"{WORK}/national.json")
G = jload(f"{WORK}/gi.json")
D = jload(f"{WORK}/drinks.json")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{v:.1f}"
    raise ValueError(f)


# facts stated in words
fk = R["national"]["first_kind"]
order = sorted([k for k in fk if k not in ("tea", "coffee", "soft", "unclassified")], key=lambda k: -fk[k])
assert order[:4] == ["brandy", "spirit", "beer", "cocktail"], order
fsp = R["national"]["first_spirits"]
assert fsp > fk["beer"] > fk["cocktail"] > fk["trad"] and fk["brandy"] == max(fk[k] for k in fk if k in ("whisky", "gin", "rum", "agave", "vodka", "brandy", "anise", "asian", "liqueur", "spirit"))
assert [c["iso"] for c in R["gi"]["top_wine"][:4]] == ["ITA", "FRA", "ESP", "GRC"]
assert R["gi"]["wine_top_regions"][0]["iso"] == "FRA"
assert R["producers"]["osm_topreg_wine"][0]["name"] == "Rhineland-Palatinate"
assert [c["iso"] for c in R["drinks"]["top_beer"][:3]] == ["USA", "NLD", "BEL"]
assert [c["iso"] for c in R["producers"]["osm_top_beer"][:4]] == ["USA", "FRA", "GBR", "DEU"]
assert R["producers"]["osm_topreg_beer"][0]["name"] == "Bavaria"
assert R["producers"]["osm_topreg_spirits"][0]["name"] == "Scotland"
assert R["grapes"]["top"][0]["iso"] == "ITA"
assert [x["n"] for x in R["national"]["most_named"][:2]] == ["rum", "coffee"]
for name in ("České pivo", "Bayerisches Bier", "Kölsch", "Münchener Bier"):
    assert any(g["cat"] == "beer" and name in g["name"] for g in G), name
for w in ("grozdova", "pálinka", "grappa"):
    assert any(w in g["name"].lower() for g in G if g["cat"] == "spirits"), w
for w in ("Normand", "Bretagne", "Asturias", "Sagardoa", "Herefordshire", "Gloucestershire", "Worcestershire"):
    assert any(w in g["name"] for g in G if g["fam"] == "cider"), w
liq = {i: [d["n"].lower() for d in e["liquors"]] for i, e in N.items()}
assert "baijiu" in liq["CHN"] and "soju" in liq["KOR"] and "shōchū" in liq["JPN"] and {"tequila", "mezcal", "pulque"} <= set(liq["MEX"])
assert "pisco" in liq["PER"] and "pisco" in liq["CHL"] and "rakija" in liq["SRB"] and "arak" in liq["LBN"] and "rum" in liq["JAM"]
nd = {i: [d["n"].lower() for d in e["drinks"]] for i, e in N.items()}
assert nd["ARG"][0] == "mate" and nd["IND"][0] == "lassi" and nd["BRA"][0] == "caipirinha" and all(nd[i][0].startswith("kava") for i in ("PNG", "WSM", "VUT", "TON"))
for nm, iso in (("kvass", None), ("pulque", "MEX"), ("chicha", None), ("tej", "ETH"), ("boza", None), ("kumis", None), ("palm wine", None), ("huangjiu", "CHN"), ("sake", "JPN")):
    assert any(d["n"].lower() == nm and d["kind"] == "type" and (iso is None or d["iso"] == iso) for d in D), nm
assert not any(d["n"].lower() == "mead" for d in D)
assert R["records"]["by_continent"][0]["name"] == "Europe" and R["records"]["by_continent"][1]["name"] == "North America"
assert R["producers"]["sake_top"][0]["iso"] == "JPN"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3)), tpl)
    assert "{{" not in html
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    snip = os.path.join(ROOT, "code", "fullscreen_snippet.html")
    if os.path.exists("/home/claude/hist/_brief/fullscreen_snippet.html"):
        shutil.copy("/home/claude/hist/_brief/fullscreen_snippet.html", snip)
    html = html.replace("/*FULLSCREEN*/", open(snip, encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
