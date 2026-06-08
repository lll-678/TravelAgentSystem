# Stage 7 OSM Import Pipeline

## Scope

This stage fills the project plan's third-phase gap: OSM map data import. Required tests use an OSM-shaped fixture so the harness does not depend on network access. The real OSMnx path is implemented for local/manual runs.

## Delivered

- Added OSM import settings:
  - `OSM_DEFAULT_PLACE`
  - `OSM_FALLBACK_LAT`
  - `OSM_FALLBACK_LNG`
  - `OSM_FALLBACK_DIST`
- Added `backend/app/services/osm_import_service.py`.
- Added OSM-shaped BUPT Shahe fixture payload.
- Added admin APIs:
  - `POST /api/v1/admin/map/import`
  - `GET /api/v1/admin/map/import/status`
  - `GET /api/v1/admin/stats`
- Added CLI:
  - `backend/scripts/import_osm_campus.py`
- Added `osmnx` to backend requirements.
- Added backend tests for fixture import and admin import/status handlers.

## API Contracts

After Stage 31, admin API calls require an admin bearer token:

```bash
ADMIN_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/users/login \
  -H 'Content-Type: application/json' \
  -d '{"username_or_email":"admin01","password":"admin123456"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

Offline fixture import:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/admin/map/import \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"source":"fixture","reset_existing":true}'
```

Real OSMnx import:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/admin/map/import \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"source":"osmnx","place_name":"Beijing University of Posts and Telecommunications Shahe Campus, Beijing, China","reset_existing":true}'
```

If Nominatim returns no result for `place_name`, the importer automatically falls back to:

```text
OSM_FALLBACK_LAT
OSM_FALLBACK_LNG
OSM_FALLBACK_DIST
```

CLI:

```bash
PYTHONPATH=backend python backend/scripts/import_osm_campus.py --source fixture
PYTHONPATH=backend python backend/scripts/import_osm_campus.py --source osmnx
```

## Imported Tables

The import pipeline writes:

```text
map_nodes
map_edges
buildings
facility_categories
facilities
```

## Validation

Run from repository root:

```bash
bash scripts/reset_dev_db.sh
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

Expected backend result:

```text
21 passed
```

## Known Gaps

- Harness tests do not call Overpass/OSMnx network services.
- The checklist item "At least one real OSM campus/scenic map can be imported" remains unchecked until the OSMnx command is run successfully in a network-enabled environment.
- Some campus names are not discoverable by Nominatim; fallback point import is enabled for that case.
- Imported OSM feature categorization is intentionally simple and should be refined after seeing real Overpass payloads.
- There is no frontend admin dashboard yet; only admin APIs are implemented.

## Next Stage

Continue the project plan's fifth phase:

- diary publish/list/detail/search
- diary compression
- food search and recommendation
- admin dashboard frontend
