# Stage 29 Dual POI Source Datasets

## Goal

Keep two POI datasets with different jobs:

- `nearby_facilities`: school-surrounding POIs for nearby facility recommendation.
- `campus_navigation`: BUPT Shahe internal POIs/topology candidates for campus navigation.

## Dataset Boundary

| Dataset | Source | Boundary | Used By |
| --- | --- | --- | --- |
| `nearby_facilities` | AMap Place Around, OSM amenities | radius around BUPT Shahe | nearby facility Top-K, map guide |
| `campus_navigation` | BUPT reference files, OSMnx campus payload, AMap POIs filtered by campus bounds | BUPT Shahe internal boundary | route endpoint search, campus navigation |

## Source File Locations

```text
data/external/bupt-shahe/osm/
data/external/bupt-shahe/amap_gcj02/
data/reference/bupt-shahe/raw_wgs84/
data/reference/bupt-shahe/topology/
```

External source files are not read directly by APIs. They must be cleaned/imported first.

## Download Commands

OSM/OSMnx campus source and topology payload:

```bash
PYTHONPATH=backend python backend/scripts/import_osm_campus.py \
  --source osmnx \
  --center-lng 116.28333 \
  --center-lat 40.15608 \
  --dist 900 \
  --download-only \
  --save-payload data/external/bupt-shahe/osm/osmnx_campus_payload.json
```

AMap surrounding POIs:

```bash
python backend/scripts/import_amap_pois.py \
  --dataset nearby_facilities \
  --radius 3000 \
  --max-pages 3 \
  --download-only \
  --save-raw data/external/bupt-shahe/amap_gcj02/nearby_facilities_raw.json
```

AMap campus-internal POIs:

```bash
python backend/scripts/import_amap_pois.py \
  --dataset campus_navigation \
  --radius 1500 \
  --max-pages 3 \
  --campus-only \
  --download-only \
  --save-raw data/external/bupt-shahe/amap_gcj02/campus_navigation_raw.json
```

## Import Commands

Surrounding facilities can replace the old surrounding set:

```bash
python backend/scripts/import_amap_pois.py \
  --dataset nearby_facilities \
  --radius 3000 \
  --max-pages 3 \
  --reset-facilities
```

Campus POIs can be imported without deleting surrounding POIs:

```bash
python backend/scripts/import_amap_pois.py \
  --dataset campus_navigation \
  --radius 1500 \
  --max-pages 3 \
  --campus-only \
  --reset-dataset
```

Or import from a previously saved raw file without another AMap request:

```bash
python backend/scripts/import_amap_pois.py \
  --dataset campus_navigation \
  --radius 1500 \
  --campus-only \
  --reset-dataset \
  --load-raw data/external/bupt-shahe/amap_gcj02/campus_navigation_raw.json
```

OSM payloads can also be imported from a saved file:

```bash
PYTHONPATH=backend python backend/scripts/import_osm_campus.py \
  --source osmnx \
  --load-payload data/external/bupt-shahe/osm/osmnx_campus_payload.json \
  --graph-only
```

Reference topology remains the preferred offline route graph:

```bash
PYTHONPATH=backend python backend/scripts/import_reference_campus.py --replace-campus-layers
```

## Validation

- `campus_navigation` imports must use `--campus-only`.
- AMap raw files are GCJ-02 and belong under `data/external/.../amap_gcj02/`.
- Cleaned WGS84 reference files belong under `data/reference/...`.
- `scope=campus` route endpoint search must not expose surrounding-only POIs outside the campus boundary.

## Download Attempt On 2026-06-08

Saved source files:

```text
data/external/bupt-shahe/amap_gcj02/campus_navigation_raw.json
data/external/bupt-shahe/osm/osmnx_campus_payload.json
```

Results:

| Source | Raw Count | Campus-Usable Count | Notes |
| --- | ---: | ---: | --- |
| AMap Place Around | 319 POIs | 13 inside BUPT boundary | Raw GCJ-02, import must use `--campus-only` |
| OSMnx/Overpass | 162 nodes, 456 edges, 56 buildings, 24 facilities | same bbox payload | Nominatim place lookup failed; point fallback succeeded |

The AMap result confirms why nearby-facility and campus-navigation POIs must remain separate: most Place Around rows are school-surrounding POIs, not internal route endpoints.

Local import from the saved AMap raw file did not duplicate existing surrounding POIs. It tagged 11 existing facility rows with `dataset=campus_navigation`; the remaining inside-campus raw rows were duplicate/skipped by AMap id or coordinate signature.
