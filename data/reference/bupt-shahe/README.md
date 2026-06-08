# BUPT Shahe Reference Campus Map Data

Use this directory for manually supplied campus navigation source files.

## Directory Contract

```text
data/reference/bupt-shahe/
  raw_wgs84/       original JSON/GeoJSON source layers in WGS84
  topology/        original road graph topology files
  processed/       cleaned/intermediate files generated from the source data
```

Recommended filenames:

```text
raw_wgs84/campus_layers_wgs84.geojson
raw_wgs84/campus_pois_wgs84.json
topology/campus_topology_wgs84.json
topology/campus_topology_wgs84.geojson
```

## Coordinate Contract

- Source files must use WGS84 longitude/latitude.
- Coordinate order must be `[lng, lat]`.
- Do not store GCJ-02 coordinates here.
- Frontend AMap rendering converts backend WGS84 data to GCJ-02 at display time.

## Data Role

These files are reference input for campus-internal navigation:

- roads and walkable paths
- route graph nodes and edges
- building polygons or building points
- facilities and service POIs
- optional entrances/gates used to connect buildings/facilities to roads

They are not the nationwide attraction/school recommendation dataset.

## Commit Rule

Commit these reference files when they are reasonably small and allowed to be shared for the course project. If a file is too large or contains sensitive data, keep it outside the repo and document its path in a local note that is not committed.

## Import Rule

Do not read from this directory directly in API handlers. Add a script/service that validates, cleans, and imports the files into `map_nodes`, `map_edges`, `buildings`, `facilities`, and related tables.
