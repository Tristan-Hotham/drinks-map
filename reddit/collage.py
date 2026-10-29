"""r/dataisbeautiful collage for drinks-map: 2400 x 3000 px. Numbers from data/results.json and the page data."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json"); O = jload(f"{WORK}/osm.json")
GEO = jload(f"{DATA}/countries_geo.json")
BG = "#EEF1EA"   # pale bottle glass
LANDC = "#DCDDD2"
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(.045, .968, "What does the world drink?", fontproperties=DISP, fontsize=56, color=FG, va="top")
fig.text(.045, .905, f"The first drink listed for each country in Wikipedia's list of national drinks ({R['national']['n_drink']} countries),\ncoloured by kind, with protected names and every winery, brewery and distillery below.",
         fontproperties=SERP, fontsize=16, color=FG, va="top", linespacing=1.4)

# hero map
nk = lambda iso: KIND[kindkey(SITE["c"][iso]["nk"])][1] if iso in SITE["c"] and SITE["c"][iso].get("nk") else None
ax = fig.add_axes([0, .43, 1, .43])
world(ax, nk, lw=.4, extent=(-12.3e6, 15.6e6, -5.9e6, 8.4e6), ec=BG)
for iso, ps in SHAPES:
    if not nk(iso):
        for p in ps:
            ax.add_patch(MPoly(p, closed=True, fc=LANDC, ec=BG, lw=.4))
LAB = {"USA": (-100, 41), "CAN": (-104, 60), "MEX": (-118, 13), "BRA": (-48, -8), "ARG": (-82, -40), "PER": (-100, -10), "COL": (-100, 3),
       "GBR": (-28, 60), "FRA": (-27, 47), "PRT": (-29, 37.5), "DEU": (-8, 63), "GRC": (16, 29), "GEO": (52, 47), "TUR": (31, 35.5),
       "RUS": (95, 63), "EGY": (10, 25), "SAU": (45, 21), "IND": (77, 18), "CHN": (101, 33), "JPN": (152, 40), "KOR": (138, 29), "PHL": (136, 13),
       "AUS": (133, -25), "ETH": (56, 6), "KEN": (50, -9), "NGA": (-14, 3), "ZAF": (24, -30), "MAR": (-26, 29), "PNG": (156, -14)}
INSIDE = {"USA", "BRA", "RUS", "SAU", "IND", "CHN", "AUS", "ZAF"}
for iso, (lx, ly) in LAB.items():
    nd = SITE["c"][iso]["nd"][0][0].replace("Moroccan mint tea", "Mint tea").replace("Green Tea", "Green tea")
    g = GEO[iso]; x0, y0 = tr.transform(g["lon"], g["lat"]); x1, y1 = tr.transform(lx, ly)
    if iso in INSIDE:
        ax.text(x1, y1, nd, fontsize=10.5, color=FG, ha="center", va="center", family=MONO,
                bbox=dict(boxstyle="round,pad=.2", fc=BG, ec="none", alpha=.85), zorder=6)
    else:
        ax.annotate(nd, xy=(x0, y0), xytext=(x1, y1), fontsize=10.5, color=FG, ha="center", va="center", family=MONO,
                    arrowprops=dict(arrowstyle="-", color=FG, lw=.7, shrinkA=3, shrinkB=0), zorder=6,
                    bbox=dict(boxstyle="round,pad=.2", fc=BG, ec="none", alpha=.85))
        ax.plot([x0], [y0], "o", ms=2.6, color=FG, zorder=7)
from collections import Counter
cnt = Counter(kindkey(c.get("nk")) for c in SITE["c"].values() if c.get("nk"))
LEGP = SERP.copy(); LEGP.set_size(13.5)
h = [Patch(fc=KIND[k][1], ec="none", label=f"{KIND[k][0]} {cnt[k]}") for k in KORDER if cnt[k]]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(.04, .432), ncol=4, frameon=False, prop=LEGP,
           handlelength=1.1, columnspacing=1.5, labelspacing=.5)

# big numbers
nums = [(f"{R['national']['first_nonalc_pct']:.0f}%", "#2F6B4F", f"of countries list a drink\nwithout alcohol first:\ntea {R['national']['first_tea']}, coffee {R['national']['first_coffee']}"),
        (f"{R['gi']['n']:,}", "#8E1F45", f"protected drink names in\nthe EU register; wine:\nItaly {R['gi']['top_wine'][0]['n']}, France {R['gi']['top_wine'][1]['n']}"),
        (f"{R['drinks']['beer_top3_pct']:.0f}%", "#C08A00", f"of {R['drinks']['by_group']['beer']:,} named beers\nin Wikidata are from the\nUS, Netherlands, Belgium"),
        (f"{R['records']['africa_pct']:.1f}%", "#5B4D63", f"of all {R['records']['n']:,} records\nare African: a map of\nwho keeps records")]
for i, (big, col, small) in enumerate(nums):
    x = .045 + i * .235
    fig.text(x, .352, big, fontproperties=DISP, fontsize=46, color=col, va="top")
    fig.text(x, .294, small, family=MONO, fontsize=11.5, color=FG, va="top", linespacing=1.45)

# small multiples: producers
og = Counter(o[2] for o in O)
SM = [("wine", "Wineries", "#8E1F45"), ("beer", "Breweries", "#C08A00"), ("spirits", "Distilleries", "#2E4A7D")]
ext = (-12.3e6, 15.6e6, -5.2e6, 7.9e6)
for i, (g, lab, col) in enumerate(SM):
    a = fig.add_axes([.02 + i * .325, .07, .315, .13])
    world(a, lambda iso: LANDC, lw=.2, extent=ext, ec=BG)
    pts = np.array([[o[0], o[1]] for o in O if o[2] == g]); x, y = tr.transform(pts[:, 0], pts[:, 1])
    a.scatter(x, y, s=.9, c=col, lw=0, alpha=.7, rasterized=True)
    a.set_title(f"{lab} in OpenStreetMap  {og[g]:,}", family=MONO, fontsize=12.5, color=FG, pad=3, loc="left")
fig.text(.045, .022, "Sources: English Wikipedia, 'List of national drinks' (CC BY-SA 4.0); EU eAmbrosia register (© European Union, CC BY 4.0);\n"
         "OpenStreetMap contributors (ODbL); Wikidata (CC0) via QLever; Natural Earth. Lists are informal; counts are records, not consumption.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/drinks-map", family=MONO, fontsize=9.5, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "what_the_world_drinks.png")
fig.savefig(out, facecolor=BG, dpi=200)
print("ok", out)
