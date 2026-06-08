<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>室内导航</h1>
        <p>中国科学技术馆主展厅示意图，支持入口、电梯、扶梯、楼梯、楼层和展厅路径。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="planRoute">规划室内路线</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="建筑">
              <el-select v-model="buildingName" @change="loadNodes">
                <el-option
                  v-for="building in buildings"
                  :key="building.building_name"
                  :label="building.building_name"
                  :value="building.building_name"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="路线模式">
              <el-segmented v-model="routeMode" :options="routeModeOptions" />
            </el-form-item>
            <el-form-item label="起点">
              <el-select v-model="startNodeId" filterable>
                <el-option-group v-for="group in groupedNodes" :key="group.floor" :label="group.label">
                  <el-option
                    v-for="node in group.items"
                    :key="node.id"
                    :label="node.name"
                    :value="node.id"
                  />
                </el-option-group>
              </el-select>
            </el-form-item>
            <el-form-item label="终点">
              <el-select v-model="endNodeId" filterable>
                <el-option-group v-for="group in groupedNodes" :key="group.floor" :label="group.label">
                  <el-option
                    v-for="node in group.items"
                    :key="node.id"
                    :label="node.name"
                    :value="node.id"
                  />
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="route" shadow="never" class="result-card">
          <div class="stat"><span>总距离</span><strong>{{ route.distance }} m</strong></div>
          <div class="stat"><span>预计时间</span><strong>{{ Math.round(route.duration) }} s</strong></div>
          <div class="stat"><span>模式</span><strong>{{ routeModeLabel(route.route_mode) }}</strong></div>
          <el-timeline>
            <el-timeline-item v-for="step in route.steps" :key="`${step.from_node_id}-${step.to_node_id}`">
              {{ step.text }} · {{ step.distance }} m
            </el-timeline-item>
          </el-timeline>
          <div class="trace-grid">
            <div v-for="(value, key) in route.algorithm_trace" :key="key">
              <span>{{ key }}</span>
              <strong>{{ value }}</strong>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="17">
        <el-card shadow="never">
          <el-tabs v-model="activeFloor">
            <el-tab-pane
              v-for="floor in floors"
              :key="floor"
              :label="floorLabel(floor)"
              :name="String(floor)"
            >
              <div class="floor-plan">
                <div
                  v-for="node in nodesByFloor(floor)"
                  :key="node.id"
                  class="indoor-node"
                  :class="{ active: routeNodeIds.has(node.id) }"
                  :style="{ left: `${node.x}%`, top: `${node.y + 36}%` }"
                >
                  <span>{{ node.name }}</span>
                  <small>{{ floorLabel(node.floor) }} · {{ node.node_type }}</small>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { apiGet, apiPost, type IndoorBuildingItem, type IndoorNodeItem, type IndoorRoutePayload } from "../services/api";

const loading = ref(false);
const buildings = ref<IndoorBuildingItem[]>([]);
const nodes = ref<IndoorNodeItem[]>([]);
const route = ref<IndoorRoutePayload | null>(null);
const buildingName = ref("综合教学楼");
const startNodeId = ref<number | null>(null);
const endNodeId = ref<number | null>(null);
const routeMode = ref<"normal" | "accessible">("accessible");
const activeFloor = ref("1");
const preferredBuildingName = "中国科学技术馆主展厅";
const routeModeOptions = [
  { label: "无障碍", value: "accessible" },
  { label: "普通", value: "normal" },
];

const floors = computed(() => {
  const current = buildings.value.find((building) => building.building_name === buildingName.value);
  return current?.floors ?? [1];
});

const routeNodeIds = computed(() => new Set(route.value?.path.map((node) => node.id) ?? []));
const groupedNodes = computed(() =>
  floors.value.map((floor) => ({
    floor,
    label: floorLabel(floor),
    items: nodes.value.filter((node) => node.floor === floor),
  })),
);

async function loadBuildings() {
  const payload = await apiGet<{ items: IndoorBuildingItem[] }>("/api/v1/indoor/buildings");
  buildings.value = payload.items;
  buildingName.value =
    payload.items.find((building) => building.building_name === preferredBuildingName)?.building_name ??
    payload.items[0]?.building_name ??
    buildingName.value;
}

async function loadNodes() {
  const params = new URLSearchParams({ building_name: buildingName.value });
  const payload = await apiGet<{ items: IndoorNodeItem[] }>(`/api/v1/indoor/nodes?${params}`);
  nodes.value = payload.items;
  route.value = null;
  startNodeId.value =
    preferredStartNode()?.id ??
    nodes.value.find((node) => node.node_type === "entrance")?.id ??
    nodes.value[0]?.id ??
    null;
  endNodeId.value = preferredEndNode()?.id ?? nodes.value.at(-1)?.id ?? null;
  activeFloor.value = String(
    nodes.value.find((node) => node.id === startNodeId.value)?.floor ?? floors.value[0] ?? 1,
  );
}

async function planRoute() {
  if (!startNodeId.value || !endNodeId.value) return;
  loading.value = true;
  try {
    route.value = await apiPost<IndoorRoutePayload>("/api/v1/indoor/routes", {
      building_name: buildingName.value,
      start_node_id: startNodeId.value,
      end_node_id: endNodeId.value,
      route_mode: routeMode.value,
    });
    activeFloor.value = String(route.value.end.floor);
  } finally {
    loading.value = false;
  }
}

function nodesByFloor(floor: number) {
  return nodes.value.filter((node) => node.floor === floor);
}

function floorLabel(floor: number) {
  if (floor < 0) return `B${Math.abs(floor)}`;
  return `${floor}F`;
}

function routeModeLabel(mode: string) {
  return mode === "accessible" ? "无障碍" : "普通";
}

function preferredStartNode() {
  if (buildingName.value === preferredBuildingName) {
    return nodes.value.find((node) => node.name === "西门入口");
  }
  return nodes.value.find((node) => node.name === "一层大门");
}

function preferredEndNode() {
  if (buildingName.value === preferredBuildingName) {
    return nodes.value.find((node) => node.name === "4F 挑战与未来 C 厅");
  }
  return nodes.value.find((node) => node.name.includes("305"));
}

onMounted(async () => {
  await loadBuildings();
  await loadNodes();
  await planRoute();
});
</script>

<style scoped>
.floor-plan {
  position: relative;
  min-height: 420px;
  border: 1px solid #d7dde8;
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(148, 163, 184, 0.14) 1px, transparent 1px),
    linear-gradient(rgba(148, 163, 184, 0.14) 1px, transparent 1px);
  background-size: 48px 48px;
  overflow: hidden;
}

.indoor-node {
  position: absolute;
  width: 128px;
  min-height: 54px;
  transform: translate(-50%, -50%);
  border: 1px solid #c9d3e3;
  border-radius: 8px;
  background: #ffffff;
  padding: 6px 8px;
  box-sizing: border-box;
  text-align: center;
  font-size: 12px;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

.indoor-node span,
.indoor-node small {
  display: block;
  overflow-wrap: anywhere;
}

.indoor-node small {
  color: #64748b;
  margin-top: 2px;
}

.indoor-node.active {
  border-color: #0f766e;
  background: #ecfdf5;
  color: #0f766e;
}

.trace-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.trace-grid div {
  display: grid;
  grid-template-columns: minmax(96px, 0.45fr) 1fr;
  gap: 8px;
  font-size: 12px;
}

.trace-grid span {
  color: #64748b;
}

.trace-grid strong {
  color: #0f172a;
  font-weight: 600;
  overflow-wrap: anywhere;
}
</style>
