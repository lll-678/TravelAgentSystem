# Stage 30 Diary Requirement Alignment

## Scope

This is a documentation-only stage. It aligns the diary community with requirement `(4) 旅游日记管理（含旅游日记交流）` in `要求.md` and does not change backend or frontend business code.

The diary module must be presented as a community and management feature, not only as a simple note demo.

## Requirement Mapping

| Requirement | Required Behavior | Current Project State | Next Implementation Focus |
| --- | --- | --- | --- |
| 1. Text, image, and video diary creation | Users write diaries during or after travel with text, image, and video records | `POST /api/v1/diaries` stores title/body/destination; `POST /api/v1/diaries/{id}/media` stores image/video URL metadata | Add multipart upload or local media picker if binary upload is required in demo |
| 2. Unified management of all diaries | All users' diaries can be browsed and managed together | `GET /api/v1/diaries`, `GET /api/v1/admin/diaries`, and admin delete flow exist | Add richer admin moderation fields only if required, such as status/reason |
| 3. Browse/search all diaries, view heat, and rating after browsing | List/detail/search all diaries; each detail view increases heat; user can rate after reading | View count and rating endpoints exist; views are treated as heat | Make frontend flow more explicit: open detail, increment view, then rate/comment |
| 4. Recommend by heat, rating, and personal interest | Browsing all diaries supports Top results by heat/rating/interest | `GET /api/v1/diaries?sort=hot|rating` and `GET /api/v1/diaries/recommend?user_id=...` exist; recommendation uses Top-K helper | Add visible tabs/buttons for hot, rating, and interest recommendation if not already clear |
| 5. Destination-related diary lookup and sorting | User inputs/selects destination, then sorts related diaries by heat/rating | `GET /api/v1/diaries?destination_id=...&sort=hot|rating` exists | Add destination selector/search in diary page for stronger demo flow |
| 6. Exact title lookup | Efficient exact lookup by diary title under fast-changing diary data | `diary_title_indexes` stores normalized titles; `GET /api/v1/diaries/search?mode=exact_title` exists | Keep index rebuild on create/update/delete covered by tests |
| 7. Full-text content search | Search by diary body content | `diary_search_tokens` stores lightweight inverted tokens; `mode=fulltext` searches token hits | Add Chinese segmentation only if higher search quality is needed |
| 8. Lossless compressed storage | Diary text is compressed before storage and decompressed for read | Current implementation uses `zlib+base64`, records original/compressed sizes, and reports `decompress_ok` | Add a hand-written Huffman codec if the teacher requires a visible custom compression algorithm |
| 9. AIGC animation from scenic/school photos | Photo input generates tourism animation or simulated video artifact | `POST /api/v1/aigc/storyboard` accepts `media_urls` and returns storyboard plus simulated video link | Connect selected diary media directly into AIGC page and show the generated artifact clearly |

## Diary API Contract

Core community APIs:

```text
POST /api/v1/diaries
GET /api/v1/diaries?destination_id=&q=&sort=hot|rating|latest
GET /api/v1/diaries/{id}
PUT /api/v1/diaries/{id}
DELETE /api/v1/diaries/{id}
POST /api/v1/diaries/{id}/view
POST /api/v1/diaries/{id}/rating
POST /api/v1/diaries/{id}/comments
POST /api/v1/diaries/{id}/media
GET /api/v1/diaries/{id}/media
GET /api/v1/diaries/search?keyword=&mode=exact_title|fulltext|contains
GET /api/v1/diaries/recommend?user_id=&limit=10
GET /api/v1/diaries/{id}/compression
```

Admin and AIGC APIs:

```text
GET /api/v1/admin/diaries
DELETE /api/v1/admin/diaries/{id}
POST /api/v1/aigc/diary-draft
POST /api/v1/aigc/storyboard
```

## Data Contract

Diary tables involved:

```text
diaries
diary_media
diary_comments
diary_ratings
diary_title_indexes
diary_search_tokens
```

Important fields:

- `diaries.views`: diary heat.
- `diaries.rating_sum` and `diaries.rating_count`: rating aggregate.
- `diaries.compressed_body`: compressed text storage.
- `diary_media.media_type`: `image` or `video`.
- `diary_title_indexes.normalized_title`: exact title lookup key.
- `diary_search_tokens.token`: inverted index token.

## Demonstration Rules

- Show all-user diary list first, not only the current user's records.
- Open a diary detail before rating it so the heat and rating requirement is obvious.
- Demonstrate three diary discovery paths:
  - hot/rating sorted list
  - destination-filtered list
  - exact title and full-text search
- Show compression stats with `original_size`, `compressed_size`, `compression_ratio`, and `decompress_ok`.
- Use image/video URLs as media inputs for the current demo. Do not claim binary upload exists until implemented.
- Present AIGC as deterministic simulated animation generation unless a real external model is integrated.

## Validation

Documentation-only validation:

```bash
bash scripts/check_merge_markers.sh
```

Full regression validation before the next code stage:

```bash
bash scripts/check_all.sh
```
