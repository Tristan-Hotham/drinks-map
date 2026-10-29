"""House style for static figures: fonts (static instances cut from the variable Fraunces and Source Serif 4 fonts
installed in ~/.fonts, written to memory), colours, and Natural Earth outlines in the Equal Earth projection."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(SHM, "fonts")
os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    instancer.instantiateVariableFont(TTFont("/root/.fonts/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf"), {"wght": 900, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf")
    for w, n in ((400, "Regular"), (600, "Semibold")):
        instancer.instantiateVariableFont(TTFont("/root/.fonts/SourceSerif4%5Bopsz,wght%5D.ttf"), {"wght": w, "opsz": 12}).save(f"{FD}/SourceSerif4-{n}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
SERP = fm.FontProperties(fname=f"{FD}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FD}/SourceSerif4-Semibold.ttf")
fm.fontManager.addfont("/root/.fonts/IBMPlexMono-Regular.ttf")
fm.fontManager.addfont("/root/.fonts/IBMPlexMono-Medium.ttf")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 13, "axes.edgecolor": "#6C6470", "axes.labelcolor": "#221C26",
                     "xtick.color": "#6C6470", "ytick.color": "#6C6470"})
BG, FG, MUT, LAND, RULE, HOT = "#F8F4EC", "#221C26", "#6C6470", "#ECE5D7", "#E2D9C8", "#8E1F45"
KIND = {"tea": ("Tea", "#2F6B4F"), "coffee": ("Coffee", "#3E2A1F"), "soft": ("Other non-alcoholic", "#8FBCDD"),
        "cocktail": ("Cocktail or mixed drink", "#F28E6B"), "wine": ("Wine", "#8E1F45"), "beer": ("Beer", "#E0A106"),
        "cider": ("Cider and perry", "#84B135"), "spirits": ("Spirit", "#B8452A"), "rice": ("Sake and rice drinks", "#3E5FB8"),
        "trad": ("Traditional drink", "#1E8C88"), "alcohol": ("Other alcoholic", "#7D6E86"), "unclassified": ("Named, not classified", "#BDB6AA")}
KORDER = ["tea", "coffee", "soft", "cocktail", "wine", "beer", "cider", "spirits", "rice", "trad", "alcohol", "unclassified"]
SPIR = ["whisky", "gin", "rum", "agave", "vodka", "brandy", "anise", "asian", "liqueur", "spirit"]
kindkey = lambda k: None if k is None else ("spirits" if k in SPIR else k)
tr = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    ps = []
    for ring in rings(f["geometry"]):
        x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), ring[:, 1])
        ps.append(np.column_stack([x, y]))
    SHAPES.append((f["properties"]["iso"], ps))
WORLD_EXT = (-12.5e6, 15.6e6, -6.2e6, 8.4e6)


def world(ax, colour_of, lw=.35, extent=WORLD_EXT, ec="#FFFFFF"):
    for iso, ps in SHAPES:
        c = colour_of(iso)
        for p in ps:
            ax.add_patch(MPoly(p, closed=True, fc=c or LAND, ec=ec, lw=lw))
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3]); ax.set_aspect("equal"); ax.axis("off")


def mix(a, b, t):
    A = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; B = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(A, B))


BINS = [1, 3, 10, 30, 100, 300, 1000]


def ramp(n, colour):
    if not n:
        return None
    k = max(i for i, b in enumerate(BINS) if n >= b)
    return mix("#EFE6D6", colour, .14 + .70 * k / (len(BINS) - 1))


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
