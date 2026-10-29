"""README.md and LICENSE, numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
d, p, g, n, rc = R["drinks"], R["producers"], R["gi"], R["national"], R["records"]
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) / 1e6:.1f} MB"
readme = f"""# What does the world drink?

A world map of where drinks come from: wine, beer, cider and perry, spirits, sake and other rice drinks, traditional drinks, brands and producers, protected names and national drinks. Built from Wikidata, the EU register of geographical indications (eAmbrosia), OpenStreetMap and English Wikipedia: {rc['n']:,} records in {rc['n_countries']} countries.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
Sister study: https://maps.tristanhotham.com/food-map/

## Headline results

- National drinks: of {n['n_drink']} countries in Wikipedia's list, {n['first_nonalc']} ({n['first_nonalc_pct']:.0f}%) name a drink without alcohol first (tea {n['first_tea']}, coffee {n['first_coffee']}); spirits of every kind come first in {n['first_spirits']}. The most named drinks across the national drink and national liquor lists are rum ({n['most_named'][0]['count']} countries) and coffee ({n['most_named'][1]['count']}).
- Protected names: the EU register holds {g['n']:,} drink GIs from {g['n_countries']} countries ({g['by_cat']['wine']:,} wines, {g['by_cat']['spirits']} spirits, {g['by_cat']['beer']} beers). Italy has {g['top_wine'][0]['n']} wine names and France {g['top_wine'][1]['n']}; {g['placed']} ({g['placed_pct']:.0f}%) could be placed on the map.
- Producers: OpenStreetMap has {p['osm_by_group']['wine']:,} wineries, {p['osm_by_group']['beer']:,} breweries and {p['osm_by_group']['spirits']:,} distilleries. The busiest regions are {p['osm_topreg_wine'][0]['name']} for wineries ({p['osm_topreg_wine'][0]['n']:,}), {p['osm_topreg_beer'][0]['name']} for breweries ({p['osm_topreg_beer'][0]['n']}) and {p['osm_topreg_spirits'][0]['name']} for distilleries ({p['osm_topreg_spirits'][0]['n']}).
- Wikidata names {d['n']:,} drinks with a country ({d['n_types']:,} types and styles, {d['n_products']:,} brands and products). {d['beer_top3_pct']:.0f}% of its {d['by_group']['beer']:,} beers come from the United States, the Netherlands and Belgium, and {d['wine_fra_ita_pct']:.0f}% of its {d['by_group']['wine']:,} wines from France and Italy.
- Spirits, sake and traditional drinks are thinly recorded: {d['by_group']['spirits']} named spirits, {d['by_group']['rice']} rice drinks and {d['by_group']['trad']} traditional drinks with a country; {p['sake_wikidata']} sake breweries.
- Coverage: Europe holds {rc['europe_pct']:.1f}% of all records and Africa {rc['africa_pct']:.1f}%. The map shows where open data about drinks is rich and where it is silent, not what people drink.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; page data embedded, `data/points.json`, `data/osm.json` and `data/regions.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/drinks.csv` | {d['n']:,} named drinks from Wikidata: family, kind (type or product), country and where it came from, point and where it came from, place, maker, region ({size('drinks.csv')}). |
| `data/producers.csv` | {p['wikidata_n']:,} Wikidata producers and {p['osm_n']:,} OpenStreetMap producers with group, country, region and point ({size('producers.csv')}; ODbL for the OpenStreetMap rows). |
| `data/gi_drinks.csv` | {g['n']:,} drink GIs from the EU register: type, category, family, country, status, year, point and how it was placed. |
| `data/wine_regions.csv` | {R['wine_regions']['n']} Wikidata wine regions and appellations with a point. |
| `data/national_drinks.csv` | National drinks and national liquors by country, in list order, with Wikipedia title, Wikidata item and kind. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json`, `data/points.json`, `data/osm.json`, `data/regions.json`, `data/world.json`, `data/countries_geo.json`, `data/cities.json` | Page data; world, region and city geometry reused from the food map. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Named drinks: every Wikidata class below 'alcoholic beverage' and its instances, alcohol brands, and rum, kvass, kumis and tuba (not linked to 'alcoholic beverage' in Wikidata). Family from the class tree (code/families.py); cocktails and mixed drinks left out. Country from country of origin, else country, location or maker; point from own coordinates, else location, else maker (not if the maker is abroad).
- Protected names: wine, spirit, aromatised wine, beer and cider entries of the eAmbrosia register (cancelled and rejected names left out). Placed through Wikidata's eAmbrosia ID or by matching the name to a Wikidata place in the same country (approximate). Spirit families from words in the names.
- Producers: Wikidata wineries, breweries, distilleries, sake breweries and cider mills; OpenStreetMap craft=winery, brewery, distillery and cider.
- National drinks: country lines of Wikipedia's 'List of national drinks' and 'List of national liquors', links classified through Wikidata.
- Regions: Natural Earth states and provinces, merged into regions for Spain, Italy, France, Portugal and England (as in the food map).
- Caveats: records, not consumption; very uneven coverage by country and family; approximate name matching for some protected names; informal national drink lists.

## How to rerun

Needs Python 3 with shapely, pyproj, matplotlib, fontTools and Pillow, xelatex and pdftotext. Raw inputs were fetched in a browser on {R['retrieved']} and are read in place from `{RAW}/` (set in `code/common.py`): `drinks_wd_eam_part2.json.gz` (Wikidata query results and the eAmbrosia register), `drinks_wd_wp_part1.json.gz` (Wikipedia wikitext and link resolution), `drinks_osm_part3.json.gz` (OpenStreetMap producers, Wikidata classes of national drinks, rum and kvass supplement), `drinks_gi_match_part4.json.gz` (Wikidata places matching protected names), `drinks_brands_part5.json.gz` (alcohol brands and labels). World and region geometry are copied from the food map (`/home/claude/hist/food-map/data/`). Intermediate files go to `/dev/shm/drinks/work` (set `DRINKTMP` to change).

```
python3 code/02_geo.py         # world, regions and city labels from the food map
python3 code/01_parse.py       # parse the browser bundles
python3 code/03_drinks.py      # named drinks, producers
python3 code/04_gi.py          # protected names, wine regions
python3 code/05_national.py    # national drinks and liquors
python3 code/06_results.py     # results.json and page data
python3 code/07_build_site.py  # index.html
python3 code/08_figures.py     # header, blog and paper figures
python3 code/09_paper.py       # paper PDF
python3 code/11_readme.py      # README and LICENSE
python3 code/10_release.py     # blog post, Zenodo files
python3 reddit/collage.py      # collage
```

## Sources and licences

- Wikidata, via QLever (https://qlever.cs.uni-freiburg.de/wikidata). CC0.
- EU geographical indications register eAmbrosia (https://ec.europa.eu/agriculture/eambrosia/), public API. © European Union, reused under the Commission's reuse policy (CC BY 4.0). Protected names are geographical indications; they are used only to show where each comes from.
- OpenStreetMap contributors (https://www.openstreetmap.org/copyright), via the Overpass API. ODbL 1.0.
- English Wikipedia: 'List of national drinks' and 'List of national liquors'. CC BY-SA 4.0.
- Natural Earth countries and states and provinces (public domain) and GeoNames city names (CC BY 4.0), as prepared for https://maps.tristanhotham.com/food-map/.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) What does the world drink? Wine, beer, cider, spirits, sake and national drinks in Wikidata, Wikipedia, the EU register of geographical indications and OpenStreetMap. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--"):
    assert bad not in readme.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = open("/home/claude/hist/food-map/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/ and the page scripts. The text of the
page, the figures and the derived data files in data/ are released under
CC BY-SA 4.0, because they summarise material from English Wikipedia
(CC BY-SA 4.0). The producer table (data/producers.csv) and the page file
data/osm.json contain OpenStreetMap data and are made available under the Open
Database Licence 1.0 (c) OpenStreetMap contributors. Wikidata is CC0. Data from
the EU eAmbrosia register are (c) European Union, reused under CC BY 4.0.
Country and province outlines are Natural Earth (public domain); city names
are GeoNames (CC BY 4.0).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README", len(readme.split()), "words")
