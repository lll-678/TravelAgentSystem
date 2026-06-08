# Stage 13 Campus Data Density Upgrade

## Diagnosis

For campus navigation, the deterministic seed is only an offline fallback for stable demos and tests. It is not enough, and should not be described as enough, for a convincing real campus guide:

- `map_nodes`: 80
- `map_edges`: 220
- `buildings`: 20
- `facilities`: 50
- `restaurants`: 5
- `foods`: 30

This supports smoke tests, but sparse points make route planning, nearby search, and map browsing feel like a demo rather than a campus-scale system.

## Strategy

Use a two-step data strategy with a clear data-source boundary:

1. Offline deterministic fallback.
   - Increase road graph density.
   - Add more buildings, facilities, restaurants, and foods.
   - Use campus-like semantic names.
   - Keep tests network-free.
   - Treat this as demo/fallback data only, not as real campus coverage.
2. Real POI enrichment.
   - Import AMap Web Service Place Around POIs into our own database.
   - Convert AMap GCJ-02 POIs back to WGS84 for backend storage.
   - De-duplicate keyword hits and bind each POI to the nearest local graph node.
   - Keep backend route algorithms under our control.

This keeps the project demo stable without depending on live network POI calls during grading, while still offering a real-data import path for campus POI density. AMap is used for the frontend basemap and optional POI enrichment; backend graph calculations remain database-driven.

## Offline Fallback Seed Scale

- `map_nodes`: at least 180
- `map_edges`: at least 450
- `buildings`: at least 60
- `facilities`: at least 120
- `restaurants`: at least 12
- `foods`: at least 72

## Coordinate Drift Fix

AMap renders GCJ-02 coordinates while OSM-style backend data is stored as WGS84. `AMapView` now converts road paths, route paths, building polygons, markers, and the default center from WGS84 to GCJ-02 before rendering. Backend route algorithms continue to use WGS84.

## Real Data Import

Use a backend Web Service key only for real POI import:

```bash
AMAP_WEB_API_KEY=... PYTHONPATH=backend python backend/scripts/import_amap_pois.py --radius 1800 --max-pages 3 --request-interval 0.5
```

Use `--reset-facilities` to replace fallback facility points while preserving existing road nodes and edges:

```bash
AMAP_WEB_API_KEY=... PYTHONPATH=backend python backend/scripts/import_amap_pois.py --radius 1800 --max-pages 5 --request-interval 0.5 --reset-facilities
```

Admin API equivalent:

```bash
ADMIN_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/users/login \
  -H 'Content-Type: application/json' \
  -d '{"username_or_email":"admin01","password":"admin123456"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -X POST http://127.0.0.1:8000/api/v1/admin/map/import \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"source":"amap_poi","dist":1800,"max_pages":3,"request_interval":0.5,"reset_existing":false}'
```

## Acceptance

Run:

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected:

- route planning still returns valid paths
- nearby facilities still return Top-K route paths
- food recommendation still returns ranked results
- admin stats show upgraded data scale
- AMap POI import can add real facility rows when `AMAP_WEB_API_KEY` and network are available
