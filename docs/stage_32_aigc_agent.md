# Stage 32 AIGC Agent

## Scope

This stage upgrades the current AIGC placeholder into a lightweight workflow Agent. The implementation keeps deterministic local behavior, adds tool orchestration, and exposes trace output for course demonstration.

The goal is not to claim real external video generation. The Agent demonstrates an orchestration pattern with deterministic local tools, clear trace output, and replaceable external-model boundaries.

## Delivered

- Added backend endpoint:
  - `POST /api/v1/aigc/agent/run`
- Added `backend/app/services/aigc_agent_service.py`.
- Added deterministic local tools:
  - `media_analyzer`
  - `diary_writer`
  - `storyboard_planner`
  - `prompt_builder`
  - `video_generator_mock`
  - `diary_compressor_summary`
- Added backend tests for Agent result shape, media-aware output, trace timing, and legacy endpoint compatibility.
- Updated `AigcAssistantPage` into an Agent workspace with result, storyboard, simulated video link, media summary, compression summary, and trace table/collapse.
- Kept existing endpoints backward-compatible:
  - `POST /api/v1/aigc/diary-draft`
  - `POST /api/v1/aigc/storyboard`

## Target Behavior

The AIGC assistant accepts diary text, destination/campus context, and scenic/school media URLs, then orchestrates several tools:

```text
input context
  -> media_analyzer
  -> diary_writer
  -> storyboard_planner
  -> prompt_builder
  -> video_generator_mock
  -> diary_compressor_summary
  -> final artifact
```

## API Contract

```text
POST /api/v1/aigc/agent/run
```

Request fields:

```text
task: diary_animation | diary_draft | storyboard
text: user description or diary body
destination_name: optional attraction/school/campus name
style: natural | lively | formal | cinematic
media_urls: image/video URL or path list
scene_count: 1-8
user_id: optional personalization context
diary_id: optional source diary
```

Response fields:

```text
result.title
result.draft
result.storyboard
result.prompt
result.simulated_video_url
agent_trace.steps[]
agent_trace.total_duration_ms
algorithm_trace.mode
algorithm_trace.tool_count
algorithm_trace.media_inputs
```

Each `agent_trace.steps[]` item should include:

```text
step
tool
input_summary
output_summary
status
duration_ms
```

## Compatibility Rule

Keep the existing endpoints for backward compatibility:

```text
POST /api/v1/aigc/diary-draft
POST /api/v1/aigc/storyboard
```

They may call the new Agent internally later, but public behavior should not break existing tests.

## Frontend

`AigcAssistantPage` is a single Agent workspace:

- task selector
- destination/campus context input
- text/media inputs
- scene count/style controls
- generated title/draft/storyboard/video artifact
- compact Agent trace timeline/table

The page should not present the result as real video generation. Use labels such as `模拟视频链接` and `Agent 执行轨迹`.

## Acceptance Criteria

- [x] `POST /api/v1/aigc/agent/run` works without network access.
- [x] Response includes both `result` and `agent_trace`.
- [x] Agent trace lists at least 4 tool steps.
- [x] `media_urls` affects media analysis and storyboard output.
- [x] Existing `diary-draft` and `storyboard` endpoints still pass.
- [x] Frontend can call the Agent endpoint and display trace/result.
- [x] Tests verify deterministic output and trace shape.

## Validation

Run from repository root:

```bash
pytest backend/tests/test_stage32_aigc_agent.py
cd frontend && npm run typecheck
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```
