# Stage 3 Map Data API

## Scope

This stage connects the public map browsing API to the seeded database. It does not implement real OSMnx import yet.

## Delivered

- Added `API_DATABASE_URL` so local API reads from the dev/demo database.
- `GET /api/v1/map/stats` now returns DB-backed counts.
- `GET /api/v1/map/geojson` now returns seeded roads, buildings, facilities, categories, statistics, and GeoJSON.
- Added layer endpoints:
  - `GET /api/v1/map/nodes`
  - `GET /api/v1/map/edges`
  - `GET /api/v1/map/buildings`
  - `GET /api/v1/map/facilities`
- Docker backend now points `API_DATABASE_URL` at PostgreSQL.
- Added service and API tests for the map data contract.

## API Contract

Coordinates are longitude/latitude arrays.

```text
center: [lng, lat]
roads[].path: [lng, lat][]
buildings[].polygon: [lng, lat][]
facilities[]: lng + lat fields
geojson.features[].geometry.coordinates: GeoJSON longitude/latitude order
```

Current demo source:

```text
source = database-local-map-layers
```

## Validation

Run from repository root:

```bash
bash scripts/reset_dev_db.sh
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

Manual API smoke test:

```bash
bash scripts/reset_dev_db.sh
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
curl http://127.0.0.1:8000/api/v1/map/stats
```

Expected scale:

```text
nodes: 180
roads: 641
buildings: 60
facilities: 120
categories: 10
```

## Current Follow-up Status

- Real OSMnx / Overpass import was added in Stage 7, with fixture fallback and admin import/status APIs.
- Routes and nearby facility distance were moved onto `map_nodes` / `map_edges` graph services in Stages 4 and 5.
- Stage 13 increased the deterministic 北京邮电大学沙河校区 fallback demo scale to 180 nodes, 641 edges, 60 buildings, and 120 facilities.
- Stage 19 added an AMap Web Service POI import path for real facility enrichment.
- Stage 13 also fixed AMap display drift by converting backend WGS84 coordinates to GCJ-02 in the frontend map component.

## Next Stage

The remaining map-data work is optional enrichment, not a blocker for the core demo:

- import more authoritative POI/building data if an AMap Web Service key is available
- add an admin screen for inspecting and editing individual map objects
- add browser-level visual regression checks for the AMap page when a valid key is configured
