<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>地图与目的地</h1>
        <p>可切换全国景点/学校 POI 浏览，或查看校区、景区内部道路、建筑和设施图层。</p>
      </div>
      <div class="heading-actions">
        <el-segmented v-model="viewMode" :options="viewModeOptions" />
        <el-segmented v-if="viewMode === 'scene'" v-model="selectedSceneKey" :options="sceneSegmentOptions" />
        <el-select
          v-if="viewMode === 'scene'"
          v-model="facilityCategory"
          placeholder="设施类别"
          clearable
          class="category-select"
        >
          <el-option
            v-for="item in categories"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
        <el-select
          v-if="viewMode === 'destinations'"
          v-model="destinationCategory"
          placeholder="目的地类别"
          clearable
          class="category-select"
        >
          <el-option
            v-for="item in destinationCategoryOptions"
            :key="item"
            :label="destinationCategoryLabel(item)"
            :value="item"
          />
        </el-select>
        <el-input
          v-if="viewMode === 'destinations'"
          v-model="destinationKeyword"
          clearable
          placeholder="搜索景点或学校"
          class="keyword-input"
          @keyup.enter="loadDestinationPois"
        />
        <el-button v-if="viewMode === 'destinations'" type="primary" :loading="loading" @click="loadDestinationPois">
          查询
        </el-button>
      </div>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon />

    <el-row :gutter="18" class="workbench-layout map-guide-layout">
      <el-col :span="7">
        <el-card shadow="never" class="control-panel">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>{{ viewMode === "scene" ? "内部地图图层" : "目的地 POI" }}</strong>
                <small>{{ viewMode === "scene" ? currentScene.label : destinationSortLabel + "排序" }}</small>
              </div>
              <el-tag effect="plain">{{ viewMode === "scene" ? "Scene" : "China" }}</el-tag>
            </div>
          </template>

          <div v-if="viewMode === 'scene'" class="metric-grid map-metrics">
            <div class="metric-tile"><span>道路</span><strong>{{ payload?.statistics.roads ?? "-" }}</strong></div>
            <div class="metric-tile"><span>建筑</span><strong>{{ payload?.statistics.buildings ?? "-" }}</strong></div>
            <div class="metric-tile"><span>设施</span><strong>{{ filteredFacilities.length }}</strong></div>
            <div class="metric-tile"><span>类别</span><strong>{{ payload?.statistics.categories ?? "-" }}</strong></div>
          </div>

          <template v-else>
            <div class="metric-grid map-metrics">
              <div class="metric-tile"><span>POI</span><strong>{{ destinationMarkers.length }}</strong></div>
              <div class="metric-tile"><span>景区</span><strong>{{ destinationTypeCount.scenic }}</strong></div>
              <div class="metric-tile"><span>学校</span><strong>{{ destinationTypeCount.school }}</strong></div>
              <div class="metric-tile"><span>排序</span><strong>{{ destinationSortLabel }}</strong></div>
            </div>
            <el-segmented v-model="destinationSort" :options="destinationSortOptions" @change="loadDestinationPois" />
            <div class="destination-list">
              <button
                v-for="destination in destinations"
                :key="destination.id"
                class="destination-list-item"
                :class="{ active: selectedDestination?.id === destination.id }"
                type="button"
                @click="selectDestination(destination)"
              >
                <span>
                  <strong>{{ destination.name }}</strong>
                  <small>{{ destinationCategoryLabel(destination.category) }} · 评分 {{ destination.rating }}</small>
                </span>
                <el-tag size="small" effect="plain">{{ destination.popularity }}</el-tag>
              </button>
            </div>
          </template>
        </el-card>

        <el-card v-if="viewMode === 'destinations' && selectedDestination" shadow="never" class="result-card destination-detail">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>{{ selectedDestination.name }}</strong>
                <small>{{ destinationCategoryLabel(selectedDestination.category) }}</small>
              </div>
            </div>
          </template>
          <p class="destination-description">{{ selectedDestination.description }}</p>
          <div class="tag-row">
            <el-tag v-for="tag in selectedDestination.tags" :key="tag" class="tag-item" effect="plain">{{ tag }}</el-tag>
          </div>
          <div class="metric-grid detail-metrics">
            <div class="metric-tile"><span>评分</span><strong>{{ selectedDestination.rating }}</strong></div>
            <div class="metric-tile"><span>热度</span><strong>{{ selectedDestination.popularity }}</strong></div>
          </div>
          <div class="rating-box">
            <el-rate v-model="ratingValue" allow-half />
            <div class="button-row">
              <el-button size="small" @click="favoriteSelected">收藏</el-button>
              <el-button size="small" type="primary" @click="rateSelected">评分</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="17">
        <div class="map-workspace">
          <div class="map-workspace-header">
            <div>
              <h2>{{ activeMapTitle }}</h2>
              <p>{{ activeMapSubtitle }}</p>
            </div>
            <div class="workspace-actions">
              <span class="data-chip">{{ activeFacilities.length }} 标记</span>
              <span class="data-chip">{{ activeBuildings.length }} 建筑</span>
              <span class="data-chip">{{ activeRoadPaths.length }} 道路</span>
            </div>
          </div>
          <AMapView
            v-loading="loading"
            :road-paths="activeRoadPaths"
            :buildings="activeBuildings"
            :facilities="activeFacilities"
            :center="activeCenter"
            @facility-click="handleMarkerClick"
          />
        </div>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import AMapView from "../components/AMapView.vue";
import {
  apiGet,
  apiPost,
  type BuildingItem,
  type DestinationItem,
  type DestinationListPayload,
  type FacilityItem,
  type MapGeoJsonPayload,
} from "../services/api";
import { authState } from "../services/auth";

const payload = ref<MapGeoJsonPayload | null>(null);
const destinations = ref<DestinationItem[]>([]);
const facilityCategory = ref("");
const destinationCategory = ref("");
const destinationKeyword = ref("");
const destinationSort = ref("popularity");
const selectedDestination = ref<DestinationItem | null>(null);
const ratingValue = ref(5);
const error = ref("");
const loading = ref(false);
const viewMode = ref<"scene" | "destinations">("destinations");
const selectedSceneKey = ref("bupt_shahe");
const scenes = [
  { key: "bupt_shahe", label: "北邮沙河", center: [116.28333, 40.15608] as [number, number] },
  { key: "summer_palace", label: "颐和园", center: [116.2755, 39.9996] as [number, number] },
];

const viewModeOptions = [
  { label: "景点/学校 POI", value: "destinations" },
  { label: "内部地图", value: "scene" },
];
const destinationSortOptions = [
  { label: "热度", value: "popularity" },
  { label: "评分", value: "rating" },
  { label: "名称", value: "name" },
];
const destinationCategoryOptions = ["scenic", "school"];
const currentScene = computed(() => scenes.find((scene) => scene.key === selectedSceneKey.value) ?? scenes[0]);
const sceneSegmentOptions = scenes.map((scene) => ({ label: scene.label, value: scene.key }));
const categories = computed(() => payload.value?.facility_categories ?? []);
const roadPaths = computed(() => payload.value?.roads.map((road) => road.path) ?? []);
const filteredFacilities = computed<FacilityItem[]>(() => {
  const facilities = payload.value?.facilities ?? [];
  if (!facilityCategory.value) return facilities;
  return facilities.filter((item) => item.category === facilityCategory.value);
});
const destinationMarkers = computed<FacilityItem[]>(() =>
  destinations.value.map((destination) => ({
    id: `destination-${destination.id}`,
    name: destination.name,
    category: destinationCategoryLabel(destination.category),
    category_name: destinationCategoryLabel(destination.category),
    lng: destination.lng,
    lat: destination.lat,
    description: `评分 ${destination.rating} · 热度 ${destination.popularity}`,
  })),
);
const destinationTypeCount = computed(() => ({
  scenic: destinations.value.filter((destination) => destination.category !== "school").length,
  school: destinations.value.filter((destination) => destination.category === "school").length,
}));
const destinationSortLabel = computed(() => {
  const option = destinationSortOptions.find((item) => item.value === destinationSort.value);
  return option?.label ?? "热度";
});
const activeRoadPaths = computed(() => (viewMode.value === "scene" ? roadPaths.value : []));
const activeBuildings = computed<BuildingItem[]>(() =>
  viewMode.value === "scene" ? payload.value?.buildings ?? [] : [],
);
const activeFacilities = computed<FacilityItem[]>(() =>
  viewMode.value === "scene" ? filteredFacilities.value : destinationMarkers.value,
);
const activeCenter = computed<[number, number]>(() =>
  viewMode.value === "scene" ? payload.value?.center ?? currentScene.value.center : [104.1954, 35.8617],
);
const activeMapTitle = computed(() =>
  viewMode.value === "scene" ? `${currentScene.value.label}内部地图` : "全国景点/学校目的地",
);
const activeMapSubtitle = computed(() =>
  viewMode.value === "scene"
    ? "展示道路拓扑、建筑区域和服务设施，供路线规划与附近设施查询复用。"
    : "展示真实景区与高校目的地 POI，点击标记可记录浏览并进入评分/收藏反馈。",
);

async function loadMap() {
  try {
    loading.value = true;
    facilityCategory.value = "";
    const params = new URLSearchParams({ scene_key: selectedSceneKey.value });
    payload.value = await apiGet<MapGeoJsonPayload>(`/api/v1/map/geojson?${params}`);
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "地图数据加载失败";
  } finally {
    loading.value = false;
  }
}

async function loadDestinationPois() {
  try {
    loading.value = true;
    error.value = "";
    const collected: DestinationItem[] = [];
    let offset = 0;
    let total = Number.POSITIVE_INFINITY;
    while (offset < total) {
      const params = new URLSearchParams({
        sort: destinationSort.value,
        limit: "100",
        offset: String(offset),
      });
      if (destinationCategory.value) {
        params.set("category", destinationCategory.value);
      }
      if (destinationKeyword.value.trim()) {
        params.set("q", destinationKeyword.value.trim());
      }
      const response = await apiGet<DestinationListPayload>(`/api/v1/destinations?${params}`);
      collected.push(...response.items);
      total = response.total;
      offset += response.items.length;
      if (response.items.length === 0) break;
    }
    destinations.value = collected;
    selectedDestination.value = collected[0] ?? null;
    ratingValue.value = selectedDestination.value?.rating ?? 5;
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : "目的地 POI 加载失败";
  } finally {
    loading.value = false;
  }
}

function selectDestination(destination: DestinationItem) {
  selectedDestination.value = destination;
  ratingValue.value = destination.rating;
  void recordDestinationView(destination.id);
}

function handleMarkerClick(facility: FacilityItem) {
  if (!facility.id.startsWith("destination-")) return;
  const destinationId = Number(facility.id.replace("destination-", ""));
  const destination = destinations.value.find((item) => item.id === destinationId);
  if (destination) {
    selectDestination(destination);
  }
}

async function favoriteSelected() {
  if (!selectedDestination.value || !authState.user) return;
  await apiPost(`/api/v1/users/${authState.user.id}/favorites`, {
    target_type: "destination",
    target_id: selectedDestination.value.id,
    note: "地图与目的地页收藏",
  });
  ElMessage.success("已收藏，推荐会读取该行为");
}

async function rateSelected() {
  if (!selectedDestination.value || !authState.user) return;
  await apiPost(`/api/v1/users/${authState.user.id}/ratings`, {
    target_type: "destination",
    target_id: selectedDestination.value.id,
    rating: ratingValue.value,
  });
  await loadDestinationPois();
  ElMessage.success("评分已更新");
}

async function recordDestinationView(destinationId: number) {
  if (!authState.user) return;
  await apiPost(`/api/v1/users/${authState.user.id}/behavior`, {
    target_type: "destination",
    target_id: destinationId,
    action: "view",
    metadata_text: "map destination poi click",
  });
}

function destinationCategoryLabel(category: string) {
  return category === "school" ? "学校" : "景区";
}

watch(selectedSceneKey, () => {
  void loadMap();
});

watch(viewMode, (nextMode) => {
  if (nextMode === "scene" && !payload.value) {
    void loadMap();
  }
  if (nextMode === "destinations" && destinations.value.length === 0) {
    void loadDestinationPois();
  }
});

onMounted(async () => {
  await loadDestinationPois();
  await loadMap();
});
</script>

<style scoped>
.heading-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.keyword-input {
  width: 220px;
}

.map-guide-layout {
  align-items: start;
}

.map-metrics {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.destination-list {
  display: grid;
  gap: 9px;
  max-height: 420px;
  overflow: auto;
  padding-right: 2px;
}

.destination-list-item {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #ffffff;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.16s ease,
    background 0.16s ease,
    box-shadow 0.16s ease;
}

.destination-list-item:hover,
.destination-list-item.active {
  border-color: #87d0c6;
  background: #f4fbfa;
  box-shadow: 0 8px 20px rgba(16, 24, 40, 0.06);
}

.destination-list-item strong,
.destination-list-item small {
  display: block;
}

.destination-list-item strong {
  color: #101828;
  font-size: 14px;
  line-height: 1.35;
}

.destination-list-item small {
  margin-top: 5px;
  color: #667085;
  font-size: 12px;
}

.destination-detail h2 {
  margin: 0;
}

.destination-description {
  color: #667085;
  line-height: 1.7;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0;
}

.tag-item {
  margin: 0 6px 6px 0;
}

.detail-metrics {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 12px;
}

.rating-box {
  display: grid;
  gap: 12px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #edf1f5;
}

.button-row {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
</style>
