# Stage 39 Diary Community UI

## Goal

Reduce the crowded diary/community experience and make the diary module easier to demo:

- `/diaries` focuses on browsing, searching, reading, rating, and commenting.
- `/diaries/create` focuses on publishing diaries and running the AIGC Agent.
- Diary list results should read like community content, not an admin table.

## Completed

- Split diary workflows into two frontend routes:
  - `DiaryCommunityPage`: browse/search/detail/rating/comment.
  - `DiaryCreateAigcPage`: publish diary plus AIGC Agent generation.
- Changed `/aigc` to redirect to `/diaries/create`.
- Updated App sidebar and HomePage module cards:
  - 游记社区
  - 发布与 AIGC
- Reworked `/diaries` layout:
  - left card-style result list with title, summary, views, rating, and rating count;
  - active/hover state for selected diary;
  - right reader panel with title, stats, body, media, compression stats, rating, and comments;
  - responsive behavior for narrow screens.
- Kept backend APIs unchanged.

## Verification

```bash
cd frontend
npm run typecheck
npm run build
```

Both commands passed during Stage 39. Vite still reports the existing large chunk warning, which is not caused by this UI stage.

## Acceptance

- [x] `/diaries` no longer uses a dense table-first layout.
- [x] Search and result browsing are visually grouped in one left panel.
- [x] Diary detail is shown in a reader-style panel.
- [x] Rating and comments remain available after the layout change.
- [x] `/diaries/create` remains the single place for publish + AIGC creation.
