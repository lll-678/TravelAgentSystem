# Stage 35 Multi-Scene Scenic Navigation

## Scope

Add a second internal-navigation scene for a mature scenic area while keeping the current BUPT Shahe campus navigation stable.

Selected scenic area:

```text
scene_key: summer_palace
display_name: 北京颐和园
center: [116.2755, 39.9996]
```

Why Summer Palace:

- mature large scenic area
- many internal walkways and sightseeing nodes
- more suitable than a small park for multi-point route planning
- OSM/AMap data is likely richer than many smaller scenic spots

## Scene Keys

```text
bupt_shahe       北京邮电大学沙河校区
summer_palace    北京颐和园
```

Default scene remains `bupt_shahe` for backward compatibility.

## Data Boundary

Do not replace BUPT campus data when importing Summer Palace.

Each map/routing layer must be scoped by scene:

```text
map_nodes.scene_key
map_edges.scene_key
buildings.scene_key
facilities.scene_key
```

Facility categories can remain global.

## Data Directories

Downloaded raw files:

```text
data/external/summer-palace/osm/
data/external/summer-palace/amap_gcj02/
```

Optional manually curated reference files:

```text
data/reference/summer-palace/raw_wgs84/
data/reference/summer-palace/topology/
data/reference/summer-palace/processed/
```

## API Target

Map:

```text
GET /api/v1/map/stats?scene_key=summer_palace
GET /api/v1/map/geojson?scene_key=summer_palace
```

Search:

```text
GET /api/v1/search/places?scope=scenic&scene_key=summer_palace
```

Routes:

```text
POST /api/v1/routes/plan
{
  "scene_key": "summer_palace",
  "start_place_id": "node-...",
  "end_place_id": "facility-...",
  "route_source": "local_graph"
}
```

Nearby facilities:

```text
GET /api/v1/facilities/nearby?scene_key=summer_palace&origin_place_id=...&category=超市
```

## Frontend Target

RoutePlannerPage should support a scene selector:

```text
北京邮电大学沙河校区
北京颐和园
```

Changing scene should reload:

- map layers
- route endpoint search
- default start/end places
- nearby-facility context if reused later

## Data Acquisition Plan

1. Capture OSMnx payload for Summer Palace:

```bash
PYTHONPATH=backend python backend/scripts/import_osm_campus.py \
  --source osmnx \
  --place-name "Summer Palace, Beijing, China" \
  --dist 1800 \
  --download-only \
  --save-payload data/external/summer-palace/osm/osmnx_summer_palace_payload.json
```

2. Import graph/features into `scene_key=summer_palace`.

3. Optionally enrich POIs with AMap Web Service Place Around, saved under `data/external/summer-palace/amap_gcj02/`.

Network imports are optional for tests. Required tests should use an offline fixture or saved payload.

## Acceptance Criteria

- [ ] BUPT Shahe navigation still works as default.
- [ ] Summer Palace has its own visible roads, buildings, and facilities.
- [ ] Scene-specific map API does not mix BUPT and Summer Palace layers.
- [ ] Scene-specific place search returns only places in the selected scene.
- [ ] Route planning supports `scene_key=summer_palace`.
- [ ] Multi-point route planning supports `scene_key=summer_palace`.
- [ ] Nearby facility query supports `scene_key=summer_palace`.
- [ ] Frontend can switch between BUPT Shahe and Summer Palace.
- [ ] Smoke test checks both scenes after reset/import.

## Implementation Order

1. Add `scene_key` columns and schema compatibility upgrades.
2. Make BUPT seed/import paths write `scene_key=bupt_shahe`.
3. Add scene filtering to map, search, route, and nearby-facility services.
4. Add Summer Palace OSM payload capture/import path.
5. Add frontend scene selector.
6. Update tests and smoke.
