# Stage 24 Destination-Scoped Food

## Scope

This stage closes the food recommendation scope gap:

- link restaurants to destinations
- filter restaurant/food/search/recommend/nearby APIs by selected destination
- use selected destination as current location when explicit coordinates are not supplied

## Delivered

- `restaurants.destination_id`
- Non-destructive schema compatibility for existing SQLite dev databases.
- Incremental seed enrichment assigns old restaurants to nearest destinations.
- `GET /api/v1/foods/restaurants?destination_id=...`
- `GET /api/v1/foods/items?destination_id=...`
- `GET /api/v1/foods/search?destination_id=...`
- `GET /api/v1/foods/recommend?destination_id=...`
- `GET /api/v1/foods/nearby?destination_id=...`
- FoodRecommendPage can select a destination scope and re-query all food workflows.

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage9_food_aigc_admin.py
npm run typecheck
```

Expected:

- scoped restaurants are non-empty for seeded BUPT destinations
- food recommendation trace reports `stage-24-destination-scoped-food`
- search/recommend/nearby APIs keep cuisine, distance, and Top-K behavior while applying destination scope

## Remaining Limits

- If real external restaurant data is imported later, each restaurant should be linked to the nearest selected campus/scenic destination during import.
- Destination scope currently uses explicit `destination_id` or a 1500m spatial fallback, which is enough for the campus demo but not a full regional geofence engine.
