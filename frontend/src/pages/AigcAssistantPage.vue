<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>AIGC Agent</h1>
        <p>游记、分镜、提示词与模拟视频工作流。</p>
      </div>
      <el-button type="primary" :loading="agentLoading" @click="runAgent">运行 Agent</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="任务">
              <el-select v-model="agentForm.task">
                <el-option label="游记动画" value="diary_animation" />
                <el-option label="游记草稿" value="diary_draft" />
                <el-option label="分镜脚本" value="storyboard" />
              </el-select>
            </el-form-item>
            <el-form-item label="目的地">
              <el-input v-model="agentForm.destination_name" />
            </el-form-item>
            <el-form-item label="风格">
              <el-select v-model="agentForm.style">
                <el-option label="自然" value="natural" />
                <el-option label="轻快" value="lively" />
                <el-option label="正式" value="formal" />
                <el-option label="电影感" value="cinematic" />
              </el-select>
            </el-form-item>
            <el-form-item label="文本">
              <el-input v-model="agentForm.text" type="textarea" :rows="6" />
            </el-form-item>
            <el-form-item label="镜头数">
              <el-input-number v-model="agentForm.scene_count" :min="1" :max="8" />
            </el-form-item>
            <el-form-item label="媒体素材">
              <el-input v-model="mediaText" type="textarea" :rows="4" placeholder="/media/demo/campus-photo.jpg" />
            </el-form-item>
          </el-form>
          <el-button type="primary" :loading="agentLoading" @click="runAgent">运行 Agent</el-button>
        </el-card>

        <el-card v-if="agentResult" shadow="never" class="result-card">
          <div class="stat"><span>工具</span><strong>{{ agentResult.agent_trace.steps.length }}</strong></div>
          <div class="stat"><span>媒体</span><strong>{{ agentResult.result.media_analysis.media_count }}</strong></div>
          <div class="stat"><span>耗时</span><strong>{{ agentResult.agent_trace.total_duration_ms }}ms</strong></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card v-if="agentResult" shadow="never">
          <template #header>{{ agentResult.result.title }}</template>
          <p class="text-block">{{ agentResult.result.draft }}</p>
          <el-divider />
          <el-timeline>
            <el-timeline-item v-for="scene in agentResult.result.storyboard" :key="scene.index">
              <strong>{{ scene.title }}</strong>
              <p>{{ scene.description }}</p>
              <small>{{ scene.narration }} · {{ scene.duration_seconds }}s</small>
            </el-timeline-item>
          </el-timeline>
          <el-divider />
          <p class="text-block">{{ agentResult.result.prompt }}</p>
          <el-link type="primary" :href="agentResult.result.simulated_video_url" target="_blank">模拟视频链接</el-link>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card v-if="agentResult" shadow="never">
          <template #header>Agent 执行轨迹</template>
          <el-table :data="agentResult.agent_trace.steps" size="small">
            <el-table-column prop="step" label="#" width="48" />
            <el-table-column prop="tool" label="工具" min-width="150" />
            <el-table-column prop="status" label="状态" width="76" />
            <el-table-column label="耗时" width="84">
              <template #default="{ row }">{{ row.duration_ms }}ms</template>
            </el-table-column>
          </el-table>
          <el-divider />
          <el-collapse>
            <el-collapse-item
              v-for="step in agentResult.agent_trace.steps"
              :key="step.step"
              :title="`${step.step}. ${step.tool}`"
              :name="step.step"
            >
              <p class="trace-line">{{ step.input_summary }}</p>
              <p class="trace-line">{{ step.output_summary }}</p>
            </el-collapse-item>
          </el-collapse>
          <el-divider />
          <p class="trace-line">{{ agentResult.result.media_analysis.summary }}</p>
          <p class="trace-line">{{ agentResult.result.compression.summary }}</p>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { apiPost, type AigcAgentPayload } from "../services/api";

const agentLoading = ref(false);
const mediaText = ref("/media/demo/campus-photo.jpg");
const agentResult = ref<AigcAgentPayload | null>(null);
const agentForm = reactive({
  task: "diary_animation",
  text: "从沙河校区校门出发，经过食堂和图书馆，记录一次完整的校园游览。",
  destination_name: "北京邮电大学沙河校区",
  style: "cinematic",
  scene_count: 4,
});

async function runAgent() {
  agentLoading.value = true;
  try {
    agentResult.value = await apiPost<AigcAgentPayload>("/api/v1/aigc/agent/run", {
      ...agentForm,
      media_urls: parseMediaUrls(),
    });
  } finally {
    agentLoading.value = false;
  }
}

function parseMediaUrls() {
  return mediaText.value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

onMounted(() => {
  void runAgent();
});
</script>

<style scoped>
.text-block {
  color: #475467;
  line-height: 1.7;
  white-space: pre-wrap;
}

.trace-line {
  margin: 0 0 8px;
  color: #475467;
  line-height: 1.6;
}
</style>
