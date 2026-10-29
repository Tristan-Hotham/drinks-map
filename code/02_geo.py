"""World outlines, regions and city labels, reused from the sister project food-map (read only).

food-map built them from Natural Earth (admin-0 1:50m, admin-1 1:10m, public domain) and GeoNames city names
(CC BY 4.0); see https://github.com/Tristan-Hotham/food-map, code/02_geo.py. Copied here:
- data/world.json, data/countries_geo.json, data/cities.json (unchanged)
- work/regions_full.json: the food-map regions (states, provinces, merged regions of Spain, Italy, France, Portugal and
  England), used for point-in-polygon and, for countries with regional detail, written to data/regions.json later.
"""
import shutil
from common import *

for f in ["world.json", "countries_geo.json", "cities.json"]:
    shutil.copy(f"{FOOD}/data/{f}", f"{DATA}/{f}")
shutil.copy(f"{FOOD}/data/regions.json", f"{WORK}/regions_full.json")
w = jload(f"{DATA}/world.json")
r = jload(f"{WORK}/regions_full.json")
print(len(w["features"]), "countries;", len(r["features"]), "regions")
