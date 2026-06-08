# Stage 13 Campus Data Density Upgrade

## Diagnosis

For campus navigation, the previous deterministic seed was enough for algorithm demos but not dense enough for a convincing campus guide:

- `map_nodes`: 80
- `map_edges`: 220
- `buildings`: 20
- `facilities`: 50
- `restaurants`: 5
- `foods`: 30

This supports smoke tests, but sparse points make route planning, nearby search, and map browsing feel like a demo rather than a campus-scale system.

## Strategy

Use a two-step data strategy:

1. Offline deterministic enrichment first.
   - Increase road graph density.
   - Add more buildings, facilities, restaurants, and foods.
   - Use campus-like semantic names.
   - Keep tests network-free.
2. Optional AMap POI enrichment later.
   - Add a Web Service key only if needed.
   - Import POIs into our own database.
   - Keep backend route algorithms under our control.

This keeps the project demo stable without depending on live network POI calls during grading. AMap is used for the frontend basemap and rendering alignment; backend graph calculations remain database-driven and deterministic.

## Target Seed Scale

- `map_nodes`: at least 180
- `map_edges`: at least 450
- `buildings`: at least 60
- `facilities`: at least 120
- `restaurants`: at least 12
- `foods`: at least 72

## Coordinate Drift Fix

AMap renders GCJ-02 coordinates while OSM-style backend data is stored as WGS84. `AMapView` now converts road paths, route paths, building polygons, markers, and the default center from WGS84 to GCJ-02 before rendering. Backend route algorithms continue to use WGS84.

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
