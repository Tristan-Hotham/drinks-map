"""Point-in-polygon helpers on the reused Natural Earth countries and food-map regions."""
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

_W = jload(f"{DATA}/world.json")["features"]
_WG = [shape(f["geometry"]) for f in _W]
_WI = [f["properties"]["iso"] for f in _W]
_WT = STRtree(_WG)
_R = jload(f"{WORK}/regions_full.json")["features"]
_RG = [shape(f["geometry"]).buffer(0) for f in _R]
_RK = [f["properties"]["k"] for f in _R]
_RT = STRtree(_RG)


def country_at(lon, lat, tol=0.6):
    p = Point(lon, lat)
    for i in _WT.query(p):
        if _WG[i].contains(p):
            return _WI[i]
    i = _WT.nearest(p)
    return _WI[i] if _WG[i].distance(p) <= tol else None


def region_at(lon, lat, iso=None, tol=0.25):
    p = Point(lon, lat)
    for i in _RT.query(p):
        if _RG[i].contains(p) and (iso is None or _RK[i].startswith(iso + ":")):
            return _RK[i]
    i = _RT.nearest(p)
    if _RG[i].distance(p) <= tol and (iso is None or _RK[i].startswith(iso + ":")):
        return _RK[i]
    return None


REGNAME = {f["properties"]["k"]: f["properties"]["n"] for f in _R}
CNAME = {k: v["name"] for k, v in jload(f"{DATA}/countries_geo.json").items()}
