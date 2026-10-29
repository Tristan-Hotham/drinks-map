"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex."""
import re, shutil, subprocess
from collections import Counter
from common import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_What_Does_the_World_Drink"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    return tex(str(v))


d, p, g = R["drinks"], R["producers"], R["gi"]
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sources, what was kept and licences.}\\label{tab:sources}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.3cm}>{\\raggedright\\arraybackslash}p{6.6cm}r>{\\raggedright\\arraybackslash}p{2.4cm}}\\toprule Source & Kept & Records & Licence\\\\\\midrule\n"
      f"Wikidata & Named drinks with a country (types, styles, brands, products) & {d['n']:,} & CC0\\\\\n"
      f"Wikidata & Wineries, breweries, distilleries, sake breweries, cider mills & {p['wikidata_n']:,} & CC0\\\\\n"
      f"EU eAmbrosia & Protected names of wines, spirits, beers, ciders & {g['n']:,} & CC BY 4.0\\\\\n"
      f"OpenStreetMap & Wineries, breweries, distilleries, cider makers & {p['osm_n']:,} & ODbL 1.0\\\\\n"
      f"English Wikipedia & Countries with a national drink / national liquor & {R['national']['n_drink']} / {R['national']['n_liquor']} & CC BY-SA 4.0\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
GRP = [("wine", "Wine"), ("beer", "Beer"), ("cider", "Cider and perry"), ("spirits", "Spirits"), ("rice", "Sake and rice"), ("trad", "Traditional")]
G = jload(f"{WORK}/gi.json")
OC = Counter(o[2] for o in jload(f"{WORK}/osm.json") if o[3])  # OpenStreetMap producers that fall in a country
spir = {"whisky", "gin", "rum", "agave", "vodka", "brandy", "anise", "asian", "liqueur", "spirit"}
gig = Counter(("spirits" if x["fam"] in spir else x["fam"]) for x in G)
rows = ""; tot = [0] * 5
for k, n in GRP:
    v = [d["by_group"].get(k, 0), p["wikidata_by_group"].get(k, 0), OC.get(k, 0), gig.get(k, 0)]
    v.append(sum(v)); tot = [a + b for a, b in zip(tot, v)]
    rows += f"{n} & " + " & ".join(f"{x:,}" for x in v) + "\\\\\n"
assert tot[4] == R["records"]["n"], (tot, R["records"]["n"])
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Records by drink group and source.}\\label{tab:groups}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{lrrrrr}\\toprule Group & Named drinks & Wikidata producers & OSM producers & Protected names & All\\\\\\midrule\n" + rows +
      "\\midrule All & " + " & ".join(f"{x:,}" for x in tot) + "\\\\\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for t in R["records"]["top"][:10]:
    r = SITE["c"][t["iso"]]["r"]
    rows += f"{tex(t['name'].replace('United States of America', 'United States'))} & {t['n']:,} & " + " & ".join(f"{r.get(k, 0):,}" for k, _ in GRP) + "\\\\\n"
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{The ten countries with most records, by drink group.}\\label{tab:top}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Country & All & Wine & Beer & Cider & Spirits & Rice & Trad.\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_SOURCES}}", TS).replace("{{TABLE_GROUPS}}", TG).replace("{{TABLE_TOP}}", TT)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
txt = subprocess.run(["pdftotext", os.path.join(ROOT, "release", NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words; dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
