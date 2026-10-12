"""Build ../saturday.html from page.src.html, the R5 legs and an OpenStreetMap extract.

Run route.R first (it writes build/legs.geojson), then, from this folder:
    python3 build.py

Needs GDAL's ogr2ogr (with the OSM driver) and geopandas. The OSM extract comes from
OSM_PBF, or the Chicago Cityscape cache by default.

Everything the map draws is built into the page: streets, parks, cemeteries and water
clipped to BBOX, the land polygon from the city limits, the routes, notable graves at
Oak Woods, and the two label fonts. The page needs no tile server, so the same body also
works as a claude.ai artifact (build/artifact.html).
"""
import base64
import json
import os
import subprocess
import urllib.request

import geopandas as gpd
from shapely.geometry import box, shape
from shapely.ops import polygonize, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
PBF = os.environ.get("OSM_PBF", "/Users/stevevance/Sites/Chicago Cityscape/cli/beach_access/data/cache/chicago.osm.pbf")
WALKS = os.path.join(HERE, "..", "coffee-walks", "data", "walks.json")
OUT = os.path.join(HERE, "..", "saturday.html")
MAPLIBRE_CSS = "https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/5.6.0/maplibre-gl.css"

# West, south, east, north: Kedzie to the lake, 87th St. to Addison
BBOX = [-87.712, 41.735, -87.52, 41.950]
# Oak Woods Cemetery, for graves and its internal lanes
OAK_WOODS = [-87.6075, 41.7655, -87.5945, 41.7735]

ROAD_CLASS = {
    "motorway": "major", "trunk": "major", "primary": "major", "secondary": "major",
    "tertiary": "mid",
    "residential": "minor", "unclassified": "minor", "living_street": "minor",
    "cycleway": "path", "footway": "path", "path": "path", "pedestrian": "path",
}
ROAD_CLASS.update({k + "_link": v for k, v in list(ROAD_CLASS.items())})

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://stevevance.github.io/openhousechicago/saturday.html">
<meta property="og:title" content="OHC Saturday South Side Ride">
<meta property="og:description" content="{desc}">
<style>html,body{{margin:0}}body{{-webkit-text-size-adjust:100%}}[hidden]{{display:none!important}}img{{max-width:100%}}</style>
"""
DESC = ("A Saturday Open House Chicago 2026 bike route from the South Loop to Chinatown, Bronzeville, "
        "Woodlawn and Oak Woods Cemetery, routed on low-stress streets.")


def ogr(out, layer, bbox, where, fields):
    path = os.path.join(BUILD, out)
    if os.path.exists(path):
        os.remove(path)
    subprocess.run(["ogr2ogr", "-q", "-f", "GeoJSON", path, PBF, layer,
                    "-spat", *map(str, bbox), "-where", where, "-select", fields], check=True)
    return gpd.read_file(path)


def round_coords(c):
    return [round_coords(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]


def to_fc(gdf, types):
    gdf = gdf.explode(index_parts=False)
    gdf = gdf[gdf.geometry.geom_type.isin(types)]
    fc = json.loads(gdf.to_json(drop_id=True))
    for f in fc["features"]:
        f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"])
    return fc


def build_data():
    clip = box(*BBOX)

    st = ogr("streets.geojson", "lines", BBOX, "highway is not null", "name,highway")
    st["c"] = st.highway.map(ROAD_CLASS)
    st = st[st.c.notna() & ((st.c != "path") | st.name.notna())]  # paths only when named (trails)
    st["geometry"] = st.geometry.clip(clip).simplify(0.00003)
    streets = to_fc(st[["name", "c", "geometry"]], ["LineString"])

    pl = ogr("polys.geojson", "multipolygons", BBOX,
             "leisure='park' or landuse='cemetery' or natural='water'", "name,leisure,landuse,natural")
    pl["kind"] = pl.apply(lambda r: "cemetery" if r.landuse == "cemetery" else "water" if r.natural == "water" else "park", axis=1)
    pl = pl.to_crs(26916)
    pl = pl[(pl.area > 8000) & ~((pl.kind == "water") & (pl.area > 5e7))].to_crs(4326)  # drop slivers and Lake Michigan
    pl["geometry"] = pl.geometry.clip(clip).simplify(0.00008)
    polys = to_fc(pl[["name", "kind", "geometry"]], ["Polygon"])

    # Land is the city limits polygon; everything outside it shows as lake
    walks = json.load(open(WALKS))
    land = unary_union(list(polygonize(unary_union(shape(walks["city"]["boundary"]["geometry"])))))
    city = to_fc(gpd.GeoDataFrame(geometry=[land.intersection(clip.buffer(0.02)).simplify(0.0001)], crs=4326), ["Polygon"])

    # Oak Woods: lanes inside the cemetery and graves OSM tags as memorial=grave
    ow = ogr("oakwoods_polys.geojson", "multipolygons", OAK_WOODS, "landuse='cemetery'", "name")
    cem = ow[ow.name == "Oakwoods Cemetery"].geometry.iloc[0]
    lanes = ogr("oakwoods_lanes.geojson", "lines", OAK_WOODS,
                "highway in ('service','footway','path','track','unclassified')", "highway")
    lanes = lanes[lanes.intersects(cem)]
    lanes["geometry"] = lanes.geometry.intersection(cem).simplify(0.00002)
    lanes = lanes.explode(index_parts=False)
    for g in lanes[lanes.geometry.geom_type == "LineString"].geometry:
        streets["features"].append({"type": "Feature", "properties": {"name": None, "c": "cem"},
                                    "geometry": {"type": "LineString", "coordinates": round_coords(list(g.coords))}})
    pts = ogr("oakwoods_points.geojson", "points", OAK_WOODS, "name is not null", "name,other_tags")
    graves = [{"name": r["name"], "lon": round(r.geometry.x, 6), "lat": round(r.geometry.y, 6)}
              for _, r in pts.iterrows() if '"memorial"=>"grave"' in str(r.other_tags)]

    legs_gdf = gpd.read_file(os.path.join(BUILD, "legs.geojson")).sort_values("leg")
    legs = [{"from": r.from_id, "to": r.to_id.rsplit("_", 1)[0],
             "mi": round(r.total_distance / 1609.34, 1), "min": round(r.total_duration),
             "coords": [[round(y, 5), round(x, 5)] for x, y in r.geometry.coords]}
            for _, r in legs_gdf.iterrows()]

    glyphs = {f: base64.b64encode(open(os.path.join(HERE, "fonts", f, "0-255.pbf"), "rb").read()).decode()
              for f in ["noto-regular", "noto-italic"]}

    print(f"{len(streets['features'])} streets, {len(polys['features'])} polygons, {len(graves)} graves, {len(legs)} legs")
    return {"streets": streets, "polys": polys, "city": city, "legs": legs, "graves": graves,
            "glyphs": glyphs, "bounds": BBOX}


def main():
    os.makedirs(BUILD, exist_ok=True)
    css_path = os.path.join(BUILD, "maplibre.css")
    if not os.path.exists(css_path):
        urllib.request.urlretrieve(MAPLIBRE_CSS, css_path)

    data = json.dumps(build_data(), separators=(",", ":")).replace("</", "<\\/")
    src = open(os.path.join(HERE, "page.src.html")).read()
    body = src.replace("/*__ML_CSS__*/", open(css_path).read()).replace("/*__DATA__*/", data)
    open(os.path.join(BUILD, "artifact.html"), "w").write(body)

    i = body.index('<div class="wrap">')
    page = HEAD.format(desc=DESC) + body[:i] + "</head>\n<body>\n" + body[i:] + "\n</body>\n</html>\n"
    open(OUT, "w").write(page)
    print(f"wrote {os.path.relpath(OUT, HERE)} ({len(page) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
