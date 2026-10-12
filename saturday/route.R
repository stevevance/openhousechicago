# Bike routes for the Saturday ride, from Conveyal R5 via r5r.
# Writes build/legs.geojson: one row per leg, in the order the page expects (see LEGS below).
#
# Run from this folder:  Rscript route.R
# OSM extract: set OSM_PBF, or it uses the Chicago Cityscape cache.

Sys.setenv(JAVA_HOME = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home")
options(java.parameters = "-Xmx12G")
suppressMessages({ library(r5r); library(sf) })

pbf <- Sys.getenv("OSM_PBF", "/Users/stevevance/Sites/Chicago Cityscape/cli/beach_access/data/cache/chicago.osm.pbf")
net_dir <- file.path("build", "r5net")
dir.create(net_dir, recursive = TRUE, showWarnings = FALSE)
link <- file.path(net_dir, "chicago.osm.pbf")
if (!file.exists(link)) file.symlink(normalizePath(pbf), link)
r5 <- build_network(net_dir, verbose = FALSE)

# Stop coordinates. Kam Liu and Oak Woods use the re-geocoded points from coffee-walks;
# Oak Woods is its main gate at 67th and Greenwood.
P <- list(
  pressbox     = c(41.87188, -87.62913),    # Dearborn Station, 47 W. Polk St.
  kamliu       = c(41.85448, -87.6358),
  forum        = c(41.816793, -87.61855),
  narrowbridge = c(41.7849533, -87.6125401),
  rockefeller  = c(41.788241, -87.596827),
  oakwoods     = c(41.7729, -87.59914),
  artsbank     = c(41.7716748, -87.5868885)
)

# Leg index → page meaning: 0–2 morning; 3–4 chapel detour; 5–6 Arts Bank detour;
# 7 shortcut skipping the chapel; 8 ride home from Oak Woods
LEGS <- list(
  c("pressbox", "kamliu"), c("kamliu", "forum"), c("forum", "narrowbridge"),
  c("narrowbridge", "rockefeller"), c("rockefeller", "oakwoods"),
  c("oakwoods", "artsbank"), c("artsbank", "pressbox"),
  c("narrowbridge", "oakwoods"), c("oakwoods", "pressbox")
)

pt <- function(ids, suffix = "") data.frame(
  id = paste0(ids, suffix),
  lat = sapply(ids, function(i) P[[i]][1]),
  lon = sapply(ids, function(i) P[[i]][2]))
o <- pt(sapply(LEGS, `[`, 1))
d <- pt(sapply(LEGS, `[`, 2), paste0("_", seq_along(LEGS)))  # unique ids keep the legs in order

# LTS 2 keeps the route on low-stress streets and paths; 14 km/h is about 8.7 mph
it <- detailed_itineraries(r5, origins = o, destinations = d, mode = "BICYCLE", max_lts = 2,
  bike_speed = 14, departure_datetime = as.POSIXct("2026-10-17 10:00:00"),
  shortest_path = TRUE, all_to_all = FALSE)

it$leg <- as.integer(sub(".*_", "", it$to_id)) - 1L
it <- it[order(it$leg), c("leg", "from_id", "to_id", "total_duration", "total_distance")]
print(st_drop_geometry(it))
st_write(it, file.path("build", "legs.geojson"), delete_dsn = TRUE, quiet = TRUE)
