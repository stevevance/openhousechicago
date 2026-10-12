# Saturday South Side ride

Source for [`../saturday.html`](../saturday.html), a bike route for Open House Chicago on Saturday, Oct. 17, 2026: Pressbox (Dearborn Station) to the Kam Liu Building, the Forum, the 1 p.m. tour at Narrow Bridge Arts Club and Oak Woods Cemetery, with optional stops at Rockefeller Chapel and the Stony Island Arts Bank.

The page is one self-contained HTML file. Streets, parks, routes, graves and label fonts are built into it, so it needs no tile server and the same body also works as a claude.ai artifact.

## Files

| File | What it does |
|---|---|
| `page.src.html` | The page: styles, stop list, schedule and the MapLibre map. `/*__ML_CSS__*/` and `/*__DATA__*/` are filled in by `build.py` |
| `route.R` | Routes every leg with Conveyal R5 (r5r) and writes `build/legs.geojson` |
| `build.py` | Extracts the basemap and Oak Woods graves from OpenStreetMap, adds the legs and fonts, and writes `../saturday.html` and `build/artifact.html` |
| `fonts/` | Noto Sans Regular and Italic glyphs (0–255) for street and grave labels, from OpenFreeMap |

`build/` holds the R5 network and intermediate files and is not committed.

## Rebuild

```sh
cd saturday
Rscript route.R      # about a minute; builds the R5 network on first run
python3 build.py
```

Both scripts read the OpenStreetMap extract from `OSM_PBF`, or the Chicago Cityscape cache (`cli/beach_access/data/cache/chicago.osm.pbf`) by default. `route.R` expects Java 21 from Homebrew (`openjdk@21`). `build.py` needs `ogr2ogr` with the OSM driver and geopandas, and reads the city limits from `../coffee-walks/data/walks.json`.

## Making changes

- **Stops, times and notes** are the `STOPS` array in `page.src.html`. Each stop's `leg` is the index of the ride that follows it.
- **Adding or moving a stop**: add its coordinates to `P` and the pair to `LEGS` in `route.R`, rerun both scripts, then update `STOPS`, `VIA` and the `LEG` style table in `page.src.html`.
- **Map extent**: `BBOX` in `build.py`. The page is about 4 MB at Addison-to-87th, Kedzie-to-the-lake.
- **Grave notes** are `GRAVES` in `page.src.html`; their locations come from OSM nodes tagged `memorial=grave`.

## Method

- **Routing**: R5 bicycle mode, level of traffic stress capped at 2, 14 km/h (8.7 mph). LTS comes from OSM tags.
- **Hours and descriptions**: openhousechicago.org site pages, October 2026.
- **Basemap**: OpenStreetMap streets, parks, cemeteries and water; land from the City of Chicago city limits.

## Credits

- Map data: © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright)
- City limits: City of Chicago open data
- Map library: [MapLibre GL JS](https://maplibre.org/) 5.6.0, BSD-3-Clause
- Fonts: Noto Sans, SIL Open Font License, glyphs from [OpenFreeMap](https://openfreemap.org)
