# What does the world drink?

A world map of where drinks come from: wine, beer, cider and perry, spirits, sake and other rice drinks, traditional drinks, brands and producers, protected names and national drinks. Built from Wikidata, the EU register of geographical indications (eAmbrosia), OpenStreetMap and English Wikipedia: 67,755 records in 186 countries.

Interactive page: https://maps.tristanhotham.com/drinks-map/
Paper: https://doi.org/10.5281/zenodo.23764739
Blog post: https://blog.tristanhotham.com/2026/10/29/drinks-map/
Sister study: https://maps.tristanhotham.com/food-map/

## Headline results

- National drinks: of 201 countries in Wikipedia's list, 90 (45%) name a drink without alcohol first (tea 19, coffee 16); spirits of every kind come first in 47. The most named drinks across the national drink and national liquor lists are rum (17 countries) and coffee (13).
- Protected names: the EU register holds 1,985 drink GIs from 40 countries (1,665 wines, 273 spirits, 25 beers). Italy has 522 wine names and France 442; 996 (50%) could be placed on the map.
- Producers: OpenStreetMap has 17,682 wineries, 11,649 breweries and 3,062 distilleries. The busiest regions are Rhineland-Palatinate for wineries (1,980), Bavaria for breweries (387) and Scotland for distilleries (177).
- Wikidata names 27,322 drinks with a country (1,476 types and styles, 25,846 brands and products). 78% of its 20,381 beers come from the United States, the Netherlands and Belgium, and 94% of its 6,174 wines from France and Italy.
- Spirits, sake and traditional drinks are thinly recorded: 594 named spirits, 21 rice drinks and 30 traditional drinks with a country; 88 sake breweries.
- Coverage: Europe holds 64.7% of all records and Africa 0.7%. The map shows where open data about drinks is rich and where it is silent, not what people drink.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; page data embedded, `data/points.json`, `data/osm.json` and `data/regions.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/drinks.csv` | 27,322 named drinks from Wikidata: family, kind (type or product), country and where it came from, point and where it came from, place, maker, region (4.5 MB). |
| `data/producers.csv` | 6,044 Wikidata producers and 32,425 OpenStreetMap producers with group, country, region and point (3.0 MB; ODbL for the OpenStreetMap rows). |
| `data/gi_drinks.csv` | 1,985 drink GIs from the EU register: type, category, family, country, status, year, point and how it was placed. |
| `data/wine_regions.csv` | 471 Wikidata wine regions and appellations with a point. |
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

Needs Python 3 with shapely, pyproj, matplotlib, fontTools and Pillow, xelatex and pdftotext. Raw inputs were fetched in a browser on 29 October 2026 and are read in place from `/home/claude/hist/_data18/drinks-map/` (set in `code/common.py`): `drinks_wd_eam_part2.json.gz` (Wikidata query results and the eAmbrosia register), `drinks_wd_wp_part1.json.gz` (Wikipedia wikitext and link resolution), `drinks_osm_part3.json.gz` (OpenStreetMap producers, Wikidata classes of national drinks, rum and kvass supplement), `drinks_gi_match_part4.json.gz` (Wikidata places matching protected names), `drinks_brands_part5.json.gz` (alcohol brands and labels). World and region geometry are copied from the food map (`/home/claude/hist/food-map/data/`). Intermediate files go to `/dev/shm/drinks/work` (set `DRINKTMP` to change).

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

Hotham, T. (2026) What does the world drink? Wine, beer, cider, spirits, sake and national drinks in Wikidata, Wikipedia, the EU register of geographical indications and OpenStreetMap. Zenodo. https://doi.org/10.5281/zenodo.23764739

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
