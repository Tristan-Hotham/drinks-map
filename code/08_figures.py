"""Static figures: header.png (1200 x 630), blog figures (release/blog/b_*.png, 1520 px wide) and paper figures
(release/paper/f_*.png). Maps are drawn from coordinates and Natural Earth outlines, no web tiles."""
from collections import Counter, defaultdict
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from shapely.geometry import shape
from figstyle import *
import matplotlib.ticker

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
O = jload(f"{WORK}/osm.json"); G = jload(f"{WORK}/gi.json")
CN = SITE["cname"]
REL = os.path.join(ROOT, "release"); os.makedirs(f"{REL}/blog", exist_ok=True); os.makedirs(f"{REL}/paper", exist_ok=True)
GC = {"wine": "#8E1F45", "beer": "#D99A00", "spirits": "#2E4A7D", "cider": "#84B135"}  # distilleries in navy here: copper is lost between claret and amber in a dot map
GN = {"wine": "Winery", "beer": "Brewery", "spirits": "Distillery", "cider": "Cider maker"}
FAMC = {f[0]: f[2] for f in SITE["fams"]}; FAMN = {f[0]: f[1] for f in SITE["fams"]}


def legend(fig, items, y, ncol=3, x=.03, fs=11, marker=False):
    if marker:
        h = [Line2D([], [], marker="o", ls="", ms=7, mfc=c, mec="none", label=l) for l, c in items]
    else:
        h = [Patch(fc=c, ec="none", label=l) for l, c in items]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(x, y), ncol=ncol, frameon=False, fontsize=fs, handlelength=1.2,
               handleheight=1.0, columnspacing=1.4, labelspacing=.5)


def osm_points(ax, s=1.2, alpha=.55, order=("wine", "beer", "spirits")):
    for g in order:
        pts = np.array([[o[0], o[1]] for o in O if o[2] == g])
        x, y = tr.transform(pts[:, 0], pts[:, 1])
        ax.scatter(x, y, s=s, c=GC[g], alpha=alpha, lw=0, zorder=3)


# ---------- header (1200 x 630) ----------
fig = plt.figure(figsize=(6, 3.15), facecolor=BG)
ax = fig.add_axes([.33, .02, .69, .96]); world(ax, lambda i: "#E6DDCB", lw=.2, extent=(-12.0e6, 15.6e6, -5.6e6, 8.3e6))
osm_points(ax, s=.35, alpha=.6)
fig.text(.04, .86, "What does the", fontproperties=DISP, fontsize=21, color=FG, va="top")
fig.text(.04, .73, "world drink?", fontproperties=DISP, fontsize=21, color=HOT, va="top")
fig.text(.04, .54, f"{R['producers']['osm_n']:,} wineries, breweries and\ndistilleries, {R['gi']['n']:,} protected names\nand the national drink of\n{R['national']['n_drink']} countries.",
         fontproperties=SERP, fontsize=8.6, color=FG, va="top", linespacing=1.45)
for i, g in enumerate(["wine", "beer", "spirits"]):
    fig.add_artist(Line2D([.046 + i * .1], [.188], marker="o", ms=3.4, mfc=GC[g], mec="none", ls="", transform=fig.transFigure))
    fig.text(.058 + i * .1, .2, GN[g].lower(), fontsize=5.6, color=GC[g], va="top")
fig.text(.04, .08, "maps.tristanhotham.com/drinks-map", fontsize=5.8, color=MUT)
save(fig, os.path.join(ROOT, "header.png"))

# ---------- national drink map ----------
natk = lambda iso: KIND[kindkey(SITE["c"][iso]["nk"])][1] if iso in SITE["c"] and SITE["c"][iso].get("nk") else None
used = {kindkey(c.get("nk")) for c in SITE["c"].values() if c.get("nk")}
cnt = Counter(kindkey(c.get("nk")) for c in SITE["c"].values() if c.get("nk"))
for out in (f"{REL}/blog/b_national_map.png", f"{REL}/paper/f_national_map.png"):
    fig = plt.figure(figsize=(7.6, 5.1), facecolor=BG)
    ax = fig.add_axes([0, .24, 1, .76]); world(ax, natk)
    legend(fig, [(f"{KIND[k][0]} ({cnt[k]})", KIND[k][1]) for k in KORDER if k in used], .24, ncol=3, fs=9.4)
    save(fig, out)

# ---------- every winery, brewery and distillery in OpenStreetMap ----------
og = Counter(o[2] for o in O)
for out in (f"{REL}/blog/b_producers_map.png", f"{REL}/paper/f_producers_map.png"):
    fig = plt.figure(figsize=(7.6, 4.6), facecolor=BG)
    ax = fig.add_axes([0, .12, 1, .88]); world(ax, lambda i: "#E4DBC9", lw=.25)
    osm_points(ax, s=1.0, alpha=.6)
    legend(fig, [(f"{GN[g]} ({og[g]:,})", GC[g]) for g in ("wine", "beer", "spirits")], .12, ncol=3, fs=10.5, marker=True)
    save(fig, out)

# ---------- Europe: protected wine names by region ----------
regs = jload(f"{WORK}/regions_full.json")
wreg = Counter(g["reg"] for g in G if g["cat"] in ("wine", "aromatised") and g["reg"])
ext = (-10.5, 31, 34.5, 56.5); k = np.cos(np.radians(46))
WR_RAMP = ["#F3E3E6", "#E6BFC9", "#D394A6", "#BB6680", "#A23A5C", "#7C1838"]; WB = [1, 3, 6, 12, 25, 50]
wcol = lambda n: None if not n else WR_RAMP[max(i for i, b in enumerate(WB) if n >= b)]
for out in (f"{REL}/blog/b_europe_wine.png", f"{REL}/paper/f_europe_wine.png"):
    fig = plt.figure(figsize=(7.6, 6.3), facecolor=BG)
    ax = fig.add_axes([0, .12, 1, .88])
    for f in W["features"]:
        for ring in rings(f["geometry"]):
            ax.add_patch(MPoly(np.column_stack([ring[:, 0] * k, ring[:, 1]]), closed=True, fc=LAND, ec="#FFFFFF", lw=.5))
    for f in regs["features"]:
        n = wreg.get(f["properties"]["k"], 0)
        if not n:
            continue
        for ring in rings(f["geometry"]):
            ax.add_patch(MPoly(np.column_stack([ring[:, 0] * k, ring[:, 1]]), closed=True, fc=wcol(n), ec="#FFFFFF", lw=.5))
    for f in W["features"]:  # country borders on top
        for ring in rings(f["geometry"]):
            ax.add_patch(MPoly(np.column_stack([ring[:, 0] * k, ring[:, 1]]), closed=True, fc="none", ec="#8A7F72", lw=.45))
    pts = np.array([[g["lon"], g["lat"]] for g in G if g["cat"] in ("wine", "aromatised") and g["lat"] is not None])
    ax.scatter(pts[:, 0] * k, pts[:, 1], s=3.2, c=FG, alpha=.55, lw=0, zorder=4)
    LAB = {"FRA:Bourgogne-Franche-Comté": (9.0, 53.6), "FRA:Occitanie": (-10.2, 45.2), "FRA:Nouvelle-Aquitaine": (-10.2, 48.4),
           "ITA:Veneto": (16.5, 49.6), "ITA:Piemonte": (11.0, 40.4), "ITA:Tuscany": (6.5, 38.2), "GRC:GRC-2865": (26, 39)}
    for t in R["gi"]["wine_top_regions"][:5]:
        f = next(x for x in regs["features"] if x["properties"]["k"] == t["k"])
        rp = shape(f["geometry"]).representative_point()
        tx, ty = LAB.get(t["k"], (rp.x + 3, rp.y + 2))
        ax.annotate(f"{t['name']}\n{t['n']} names", xy=(rp.x * k, rp.y), xytext=(tx * k, ty), fontsize=9, color=FG, ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=FG, lw=.7, shrinkA=2, shrinkB=0), zorder=6,
                    bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=.9))
    ax.set_xlim(ext[0] * k, ext[1] * k); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")
    legend(fig, [(f"{b}{'+' if i == len(WB) - 1 else ' to ' + str(WB[i + 1] - 1)}", WR_RAMP[i]) for i, b in enumerate(WB)] + [("placed name", FG)], .115, ncol=4, fs=9.6)
    save(fig, out)


# ---------- bar charts ----------
def bars(out, rows, xlabel=None, fmt=lambda v: f"{v:,}", h=None, left=.3, colour=None, log=False, xf=1.15):
    h = h or (.42 * len(rows) + .7)
    fig = plt.figure(figsize=(7.6, h), facecolor=BG)
    ax = fig.add_axes([left, .7 / h * .8, .62 - (left - .3), 1 - 1.0 / h])
    ax.set_facecolor(BG)
    y = np.arange(len(rows))[::-1]
    vals = [r[1] for r in rows]
    ax.barh(y, vals, color=[r[2] if len(r) > 2 else colour for r in rows], height=.68)
    if log:
        ax.set_xscale("log")
    for yi, r in zip(y, rows):
        ax.text(r[1] * (1.08 if log else 1) + (0 if log else max(vals) * .015), yi, fmt(r[1]), va="center", fontsize=11, color=FG)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=11.5)
    for s in ("top", "right", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="x", labelsize=9.5); ax.tick_params(axis="y", length=0)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color=MUT)
    if not log:
        ax.set_xlim(0, max(vals) * xf)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f'{v:,.0f}'))
    else:
        ax.set_xlim(.8, max(vals) * 4)
    save(fig, out)


for d in ("blog/b", "paper/f"):
    # two maps of beer: named beers vs mapped breweries
    fig = plt.figure(figsize=(7.6, 3.7), facecolor=BG)
    for j, (rows, title, col) in enumerate([(R["drinks"]["top_beer"][:6], f"Named beers in Wikidata ({R['drinks']['by_group']['beer']:,})", "#E0A106"),
                                            (R["producers"]["osm_top_beer"][:6], f"Breweries in OpenStreetMap ({R['producers']['osm_by_group']['beer']:,})", "#8A6A12")]):
        ax = fig.add_axes([.2 + j * .5, .1, .27, .74]); ax.set_facecolor(BG)
        y = np.arange(6)[::-1]
        ax.barh(y, [r["pct"] for r in rows], color=col, height=.68)
        for yi, r in zip(y, rows):
            ax.text(r["pct"] + 1.2, yi, f"{r['pct']:.0f}%", va="center", fontsize=10.5)
        ax.set_yticks(y); ax.set_yticklabels([r["name"].replace("United States of America", "United States").replace("United Kingdom", "UK") for r in rows], fontsize=10.5)
        ax.set_xlim(0, 52); ax.set_xticks([])
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        fig.text(.03 + j * .5, .93, title, fontproperties=SERB, fontsize=11.5, color=FG)
    save(fig, f"{REL}/{d}_beer_two_maps.png")
    sf = R["gi"]["spirit_families"]
    bars(f"{REL}/{d}_spirit_names.png", [(FAMN[f], sf[f], FAMC[f]) for f in sorted(sf, key=lambda f: -sf[f])], left=.36)
    nk = Counter()
    for kk, n in R["national"]["first_kind"].items():
        nk[kindkey(kk)] += n
    bars(f"{REL}/{d}_national_kinds.png", [(KIND[kk][0], n, KIND[kk][1]) for kk, n in nk.most_common()], left=.36)
    bars(f"{REL}/{d}_coverage.png", [(c["name"].replace("Seven seas (open ocean)", "Ocean islands"), c["n"], "#5B4D63") for c in R["records"]["by_continent"] if c["n"] > 50],
         fmt=lambda v: f"{v:,} ({100 * v / R['records']['n']:.1f}%)", left=.3, xf=1.5)
    bars(f"{REL}/{d}_wine_names.png", [(c["name"], c["n"], "#8E1F45") for c in R["gi"]["top_wine"]], left=.3)
# paper only: named drinks by family (log scale)
fam = R["drinks"]["by_family"]
bars(f"{REL}/paper/f_families.png", [(FAMN[f], fam[f], FAMC[f]) for f in sorted(fam, key=lambda f: -fam[f])], left=.36, log=True,
     xlabel="named drinks in Wikidata with a country (log scale)")
print(sorted(os.listdir(f"{REL}/blog")), sorted(os.listdir(f"{REL}/paper")))
