# Stage 4 Route Planning

## Scope

This stage connects `POST /api/v1/routes/plan` to the seeded map graph. It does not implement real OSMnx import yet.

## Delivered

- Added reusable route algorithms in `backend/app/algorithms/route_planning.py`.
- Added DB-backed route orchestration in `backend/app/services/route_service.py`.
- `POST /api/v1/routes/plan` now:
  - snaps start/end coordinates to nearest `map_nodes`
  - builds a bidirectional graph from `map_edges`
  - runs Dijkstra shortest path
  - returns path coordinates, node ids, distance, duration, steps, mode, and `algorithm_trace`
- Added tests for:
  - Dijkstra path selection on a small graph
  - seeded DB route planning
  - route API handler contract

## API Contract

Request:

```json
{
  "start_lng": 116.28333,
  "start_lat": 40.15608,
  "end_lng": 116.2862,
  "end_lat": 40.1582,
  "strategy": "shortest_distance",
  "mode": "walk"
}
```

Response includes:

```text
distance: integer meters
duration: integer seconds
path: [lng, lat][]
node_ids: graph node id sequence
steps: text + distance entries
algorithm_trace.stage: stage-4-db-graph
algorithm_trace.algorithm: Dijkstra shortest path
```

Strategies:

```text
shortest_distance -> edge distance weight
shortest_time / fastest -> edge walk_time weight
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
12 passed
```

## Known Gaps

- The graph is deterministic seed data for 北京邮电大学沙河校区.
- Real OSMnx / Overpass import is still planned.
- Transport mode filtering is not implemented because seeded `map_edges` do not yet store walk/bike/cart permission flags.
- Multi-point route planning is still planned.
- Nearby facilities are not yet sorted by graph distance.

## Next Stage

Implement nearby facility search on the graph:

- category filtering
- candidate nearest-node lookup
- Dijkstra distance from current location to each facility
- Top-K nearest facilities by real graph distance
- optional direct route path from current point to selected facility
