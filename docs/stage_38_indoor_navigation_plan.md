# Stage 38 Indoor Navigation Plan

## Decision

Use `中国科学技术馆主展厅` as the upgraded indoor-navigation building.

This replaces the next-stage plan of continuing with only the generic `综合教学楼` seed. The existing `综合教学楼` graph remains a runnable fallback until the new graph is implemented.

## Why This Building

China Science and Technology Museum is the best fit among reviewed candidates:

- Official guide exposes a clear multi-floor venue structure: `B1`, `1F`, `2F`, `3F`, `4F`, `5F`.
- The same guide lists indoor service primitives such as elevator, escalator, stairs, toilet, storage, ticket center, restaurant, and store.
- Official exhibition pages identify floor-specific halls, for example:
  - `挑战与未来`: fourth floor, A/B/C/D halls.
  - `科技与生活`: third floor, A/B/C/D halls.

Sources:

- `https://www.cstm.org.cn/index.html`
- `https://www.cstm.org.cn/cgzn/cszl/tzywl/index.html`
- `https://www.cstm.org.cn/cgzn/cszl/kjysh/index.html`

## Comparison

| Candidate | Fit | Reason |
| --- | --- | --- |
| 中国科学技术馆 | Best | Public floor guide, many floors, explicit elevators/stairs/services, exhibition halls by floor. |
| 中国国家博物馆 | Good but too large | Official floor plan exists, but gallery scale is larger than needed for one-building course demo. |
| 清华大学艺术博物馆 | Good | Real public museum and school-related, but public floor/room structure is less directly machine-friendly. |
| 北邮综合教学楼 | Fast fallback | Already implemented, but less public-source-backed and less impressive for the museum-building requirement. |

## Indoor Graph Target

Building name:

```text
中国科学技术馆主展厅
```

Floors:

```text
B1
1F
2F
3F
4F
5F
```

Node groups:

- Entrances: west entrance, security check, first-floor lobby.
- Services: ticket center, storage, service desk, toilet, restaurant, store.
- Vertical traffic: elevator hall, escalator, stairs on each floor.
- Halls:
  - `2F 探索与发现 A/B/C/D 厅`
  - `3F 科技与生活 A/B/C/D 厅`
  - `4F 挑战与未来 A/B/C/D 厅`
  - `5F 短期展厅`
  - `B1 报告厅/观众餐厅`

Expected graph scale:

```text
indoor_nodes: 45-70
indoor_edges: 70-110
```

## Required Routes

The implementation must demonstrate:

- Main entrance to first-floor lobby.
- First-floor lobby to elevator hall.
- First-floor elevator to third/fourth/fifth floor elevator hall.
- Elevator hall to a target exhibition hall.
- Same-floor hallway route to toilet/store/service point.
- Accessible mode that uses elevator and avoids stairs.

## Algorithm

Keep Dijkstra over `indoor_nodes` and `indoor_edges`.

Edge types:

```text
corridor
elevator
stairs
escalator
```

Route modes:

```text
normal
accessible
```

Rules:

- `normal`: corridor + elevator + stairs + escalator.
- `accessible`: corridor + elevator only.
- Elevator/stair/escalator edges carry floor-changing steps.
- Output must include floor changes in route steps.

## Frontend Plan

`IndoorNavigationPage` should show:

- building selector
- start/end selectors grouped by floor
- route mode segmented control
- floor tabs: `B1`, `1F`, `2F`, `3F`, `4F`, `5F`
- schematic floor plan with nodes and highlighted path
- route step list with access type and floor change
- `algorithm_trace`

The floor plan should be presented as a schematic graph, not as a copied official CAD/map image.

## Acceptance

- [ ] `中国科学技术馆主展厅` appears in indoor building list.
- [ ] Indoor node count is at least 45 and edge count is at least 70 for this building.
- [ ] Route from entrance to elevator hall works.
- [ ] Route from entrance to `4F 挑战与未来 C 厅` uses elevator and reaches floor 4.
- [ ] Same-floor route to toilet/store works.
- [ ] Accessible mode avoids stairs/escalators.
- [ ] Algorithm trace reports Dijkstra, node count, edge count, route mode, and vertical traffic choice.
- [ ] Existing `综合教学楼` tests remain passing until it is retired.
