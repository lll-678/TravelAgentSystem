# AMap Map Rendering Plan

## Goal

Frontend map rendering uses AMap JS API. Backend route topology, route planning, and road-distance calculations still use local graph data imported from OSMnx/OpenStreetMap or the deterministic fallback graph. AMap Web Service can enrich local facility POIs, but it is not the routing source.

## Dependencies

- Frontend package: `@amap/amap-jsapi-loader`
- Frontend environment variable: `VITE_AMAP_KEY`
- Backend POI import environment variable: `AMAP_WEB_API_KEY`
- Key source: `.env.local`; never hard-code keys in source files.

## Frontend Files

```text
frontend/src/utils/amap.ts
frontend/src/components/AMapView.vue
frontend/src/pages/MapGuidePage.vue
frontend/src/pages/RoutePlannerPage.vue
frontend/src/pages/NearbyFacilitiesPage.vue
```

## AMapView Contract

Props:

```text
facilities: facility points
buildings: building polygons
roadPaths: road polyline paths for guide display
routePath: route coordinate path
```

Rendering rules:

- Default center is `[116.28333, 40.15608]` for 北京邮电大学沙河校区.
- Facilities render as AMap `Marker`.
- Building areas render as AMap `Polygon`.
- Roads render as neutral AMap `Polyline`.
- Routes render as AMap `Polyline`.
- Clicking a facility marker opens an info window.
- After rendering a route, call map fit-view behavior.
- Clear old overlays before redrawing to avoid duplicate markers, polygons, or polylines.

## Page Contracts

`MapGuidePage.vue`:

- Calls `GET /api/v1/map/geojson`.
- Reads roads, buildings, and facilities.
- Converts backend GeoJSON to AMap coordinate arrays.
- Supports facility category filtering.
- Reads local DB rows. Those rows may come from deterministic fallback seed, OSMnx import, or AMap POI enrichment.

`RoutePlannerPage.vue`:

- Calls `POST /api/v1/routes/plan`.
- Reads route `path` or `path_geojson`.
- Uses `AMapView` to draw the route polyline.
- Shows total distance, estimated duration, and route steps.
- Uses backend Dijkstra over local `map_nodes` and `map_edges`.

`NearbyFacilitiesPage.vue`:

- Calls `GET /api/v1/facilities/nearby`.
- Draws nearby facilities as markers.
- Clicking a facility can route to the planner or draw the route directly.
- Uses category filtering plus Dijkstra graph distance ranking.

## Coordinate Rules

- Backend GeoJSON follows longitude/latitude order.
- AMap overlays require `[longitude, latitude]`.
- Route path arrays should be normalized to `[lng, lat][]` before passing to `AMapView`.
- Backend stores WGS84. Frontend converts WGS84 overlays to GCJ-02 for AMap rendering.
- AMap Web Service POIs arrive as GCJ-02 and are converted back to WGS84 before storage.

## Backend Boundary

- Do not use AMap routing as the backend route source.
- Use OSMnx/OSM graph data for shortest path, route distance, route time, and nearby-facility road-distance sorting.
- AMap JS API is the frontend rendering layer.
- AMap Web Service is an optional real POI enrichment source for local facility rows.
