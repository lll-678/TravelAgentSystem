# Map Data Design

## Source

Backend road topology and building polygons are imported from OpenStreetMap through OSMnx/Overpass when network access is available. Required tests use a deterministic OSM-shaped fixture.

Facility density can be enriched from AMap Web Service Place Around POIs. This is a POI import path only; it does not replace backend route topology.

## Stored Layers

- Roads: `map_nodes`, `map_edges`.
- Buildings: `buildings` polygons.
- Facilities: `facilities` points and `facility_categories`.

## Coordinate Contract

All API coordinates are WGS84 `[lng, lat]` arrays. AMap Web Service POIs arrive as GCJ-02 and are converted to WGS84 before storage. Frontend overlays convert WGS84 back to GCJ-02 before rendering on the AMap basemap.

## Frontend Rendering

`AMapView.vue` renders:

- Marker overlays for facilities.
- Polygon overlays for buildings.
- Polyline overlays for roads and routes.

Old overlays are cleared before redraw to avoid duplicate markers and stale routes.

## Import Modes

- Fixture import: offline and test-safe.
- OSMnx import: manual/network-enabled path.
- AMap POI import: manual/network-enabled facility enrichment path using `AMAP_WEB_API_KEY`.
- If Nominatim place lookup fails, importer falls back to configured center point and radius.
