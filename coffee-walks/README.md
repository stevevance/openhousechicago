# Open House Coffee Walks

Walking routes from the sites new to Open House Chicago 2026 to the nearest coffee shop on Soren Spicknall's South Side Coffee Shops map. The page has one overview map (MapLibre GL JS) and a small map for each site.

It is a static page. Serve the folder from any web server (GitHub Pages works); opening `index.html` straight from disk won't work, because the page loads its data with `fetch`.

## Files

| File | What it holds |
|---|---|
| `index.html` | The page, its styles and its scripts |
| `data/cards.json` | One record per site: the site, its nearest coffee shop, the walking route, distance and time, plus the streets, parks, water and cemeteries clipped to that site's small map |
| `data/walks.json` | Sites, coffee shops, walking routes and the Chicago city limits for the overview map (GeoJSON) |

The overview map's basemap is [OpenFreeMap](https://openfreemap.org) vector tiles, which need no API key. The small maps draw their own streets, parks, water and cemeteries from `data/cards.json`.

## Method

- **Sites**: Open House Chicago's "New Sites for 2026" list. Nine of OHC's map pins were about a block from the street address, so those sites were re-geocoded from their addresses.
- **Coffee shops**: [South Side Coffee Shops](https://www.google.com/maps/d/viewer?mid=18b9uhyH_1C6SRk4byD2WnPSrN5UW6BJH) by Soren Spicknall, which covers Chicago south of Roosevelt Road, plus Unison Coffee (148 S. California Ave.), which soft-opened in April 2026 and isn't on that map yet.
- **Which sites**: those within 1.5 miles, in a straight line, of a coffee shop.
- **Routes**: Conveyal R5 (via r5py), walking on an August 2026 OpenStreetMap extract at 3.5 mph. Each site was routed to its three closest shops, and the quickest walk was kept.

## Credits and licenses

- Routes and cemetery outlines: © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright)
- Overview basemap: OpenFreeMap, © OpenMapTiles, data © OpenStreetMap contributors
- Street centerlines, park boundaries, hydrography and city limits: City of Chicago and Chicago Park District open data
- Coffee icon: [Font Awesome Free](https://fontawesome.com/license/free) "mug-hot", CC BY 4.0
- Map library: [MapLibre GL JS](https://maplibre.org/) 5.6.0, BSD-3-Clause
