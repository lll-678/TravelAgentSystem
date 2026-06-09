<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>个人中心</h1>
        <p>维护当前登录账号的兴趣、收藏、评分和浏览行为，并查看推荐结果如何变化。</p>
      </div>
      <el-button type="primary" :loading="saving" @click="saveInterests">保存兴趣</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="9">
        <el-card shadow="never">
          <template #header>画像与行为</template>
          <el-form label-position="top">
            <el-form-item label="当前用户">
              <el-select v-model="userId" :disabled="!isCurrentAdmin" @change="loadProfile">
                <el-option
                  v-for="user in users"
                  :key="user.id"
                  :label="`${user.nickname} (${user.username})`"
                  :value="user.id"
                />
              </el-select>
              <p class="field-note">
                {{ isCurrentAdmin ? "管理员可切换演示用户。" : "普通用户仅维护自己的账号画像。" }}
              </p>
            </el-form-item>
            <el-form-item label="兴趣">
              <el-checkbox-group v-model="selectedInterests">
                <el-checkbox-button
                  v-for="tag in availableInterests"
                  :key="tag"
                  :label="tag"
                  :value="tag"
                />
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="景点/学校 ID">
              <el-input-number v-model="targetDestinationId" :min="1" :max="207" />
            </el-form-item>
            <el-form-item label="评分">
              <el-rate v-model="ratingValue" allow-half />
            </el-form-item>
          </el-form>
          <div class="button-row wrap">
            <el-button @click="addFavorite">收藏景点/学校</el-button>
            <el-button @click="rateDestination">提交评分</el-button>
            <el-button @click="recordView">记录浏览</el-button>
          </div>
        </el-card>

        <el-card shadow="never" class="result-card">
          <template #header>用户行为摘要</template>
          <div class="stat"><span>收藏</span><strong>{{ profile?.favorites?.length ?? 0 }}</strong></div>
          <div class="stat"><span>评分</span><strong>{{ profile?.ratings?.length ?? 0 }}</strong></div>
          <div class="stat"><span>行为日志</span><strong>{{ profile?.recent_behaviors?.length ?? 0 }}</strong></div>
          <el-tag
            v-for="item in profile?.favorites ?? []"
            :key="`${item.target_type}-${item.target_id}`"
            class="tag-item"
          >
            {{ item.target_name ?? `${item.target_type}#${item.target_id}` }}
          </el-tag>
        </el-card>
      </el-col>

      <el-col :span="15">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>推荐预览</span>
              <el-segmented v-model="strategy" :options="strategyOptions" @change="() => loadRecommendations()" />
            </div>
          </template>
          <el-table :data="recommendations" size="small" v-loading="loadingRecommendations">
            <el-table-column prop="name" label="目的地" min-width="150" />
            <el-table-column prop="score" label="得分" width="80">
              <template #default="{ row }">{{ row.score?.toFixed(3) }}</template>
            </el-table-column>
            <el-table-column prop="behavior_score" label="行为" width="80">
              <template #default="{ row }">{{ row.behavior_score?.toFixed(2) ?? "-" }}</template>
            </el-table-column>
            <el-table-column prop="reason" label="推荐理由" min-width="220" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import {
  apiGet,
  apiPost,
  apiPut,
  type DestinationItem,
  type RecommendationPayload,
  type UserProfileItem,
  type UserListPayload,
  type UserProfilePayload,
} from "../services/api";
import { authState } from "../services/auth";

const users = ref<UserProfileItem[]>([]);
const profile = ref<UserProfilePayload | null>(null);
const userId = ref<number | null>(null);
const availableInterests = ref<string[]>([]);
const selectedInterests = ref<string[]>([]);
const recommendations = ref<DestinationItem[]>([]);
const saving = ref(false);
const loadingRecommendations = ref(false);
const strategy = ref("behavior");
const targetDestinationId = ref(1);
const ratingValue = ref(5);
const isCurrentAdmin = computed(() => authState.role === "admin");
const strategyOptions = [
  { label: "行为", value: "behavior" },
  { label: "兴趣", value: "interest" },
  { label: "综合", value: "composite" },
  { label: "热门", value: "hot" },
  { label: "高分", value: "rating" },
];

async function loadUsers() {
  const payload = await apiGet<UserListPayload>("/api/v1/users");
  users.value = payload.items;
  availableInterests.value = payload.available_interests;
  userId.value = authState.user?.id ?? userId.value ?? payload.items[0]?.id ?? null;
}

async function loadProfile() {
  if (!userId.value) return;
  const payload = await apiGet<UserProfilePayload>(`/api/v1/users/${userId.value}`);
  profile.value = payload;
  selectedInterests.value = [...payload.interests];
  availableInterests.value = payload.available_interests;
  await loadRecommendations();
}

async function saveInterests() {
  if (!userId.value) return;
  saving.value = true;
  try {
    const payload = await apiPut<UserProfilePayload>(`/api/v1/users/${userId.value}/interests`, {
      interests: selectedInterests.value,
    });
    profile.value = payload;
    selectedInterests.value = [...payload.interests];
    await loadRecommendations();
  } finally {
    saving.value = false;
  }
}

async function addFavorite() {
  if (!userId.value) return;
  await apiPost(`/api/v1/users/${userId.value}/favorites`, {
    target_type: "destination",
    target_id: targetDestinationId.value,
    note: "前端演示收藏",
  });
  await loadProfile();
  ElMessage.success("已收藏并写入行为日志");
}

async function rateDestination() {
  if (!userId.value) return;
  await apiPost(`/api/v1/users/${userId.value}/ratings`, {
    target_type: "destination",
    target_id: targetDestinationId.value,
    rating: ratingValue.value,
  });
  await loadProfile();
  ElMessage.success("评分已更新");
}

async function recordView() {
  if (!userId.value) return;
  await apiPost(`/api/v1/users/${userId.value}/behavior`, {
    target_type: "destination",
    target_id: targetDestinationId.value,
    action: "view",
    metadata_text: "profile demo view",
  });
  await loadProfile();
  ElMessage.success("浏览行为已记录");
}

async function loadRecommendations() {
  if (!userId.value) return;
  loadingRecommendations.value = true;
  try {
    const payload = await apiGet<RecommendationPayload>(
      `/api/v1/recommendations?user_id=${userId.value}&strategy=${strategy.value}&limit=10`,
    );
    recommendations.value = payload.items;
  } finally {
    loadingRecommendations.value = false;
  }
}

onMounted(async () => {
  await loadUsers();
  await loadProfile();
});
</script>

<style scoped>
.card-header,
.button-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.button-row.wrap {
  flex-wrap: wrap;
  justify-content: flex-start;
}

.field-note {
  margin: 8px 0 0;
  color: #667085;
  font-size: 12px;
}

.tag-item {
  margin: 0 6px 6px 0;
}
</style>
