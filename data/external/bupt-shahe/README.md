# BUPT Shahe External Map Sources

This directory is for downloaded third-party source files before they are cleaned and imported.

## Dataset Split

- `nearby_facilities`: school-surrounding POIs for nearby facility recommendation.
- `campus_navigation`: BUPT Shahe internal POIs and topology candidates for campus navigation.

## Source Contract

```text
data/external/bupt-shahe/
  osm/         OSMnx/Overpass payloads in WGS84
  amap_gcj02/  raw AMap Web Service responses in GCJ-02
```

Do not read these files directly from API handlers. Import scripts must validate, convert coordinates where needed, deduplicate, and write cleaned records into the database.

AMap raw files are GCJ-02. Converted WGS84 campus reference files may be promoted to `data/reference/bupt-shahe/` only after cleaning.
