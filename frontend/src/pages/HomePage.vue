<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>Smart Tour Guide</h1>
        <p>请选择要演示的旅游算法服务。推荐、导航、设施、游记、美食和 AIGC 各模块保持独立入口。</p>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="8" v-for="item in visibleModules" :key="item.path">
        <el-card shadow="never" class="module-card">
          <h2>{{ item.title }}</h2>
          <p>{{ item.description }}</p>
          <el-button type="primary" @click="$router.push(item.path)">进入</el-button>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { isAdmin } from "../services/auth";

const modules = [
  {
    title: "个人偏好",
    description: "维护当前账号的兴趣画像、收藏、评分和浏览行为。",
    path: "/profile",
  },
  {
    title: "景点/学校",
    description: "浏览真实景区与高校目的地，支持分类筛选、关键词搜索和热度/评分排序。",
    path: "/destinations",
  },
  {
    title: "地图导览",
    description: "展示道路、建筑区域和设施点，并支持设施类别过滤。",
    path: "/map",
  },
  {
    title: "校内导航",
    description: "选择校门、楼宇、设施或命名校内点，使用参考校园拓扑绘制校内路线。",
    path: "/routes",
  },
  {
    title: "附近设施",
    description: "按类别查询设施，并使用道路图距离进行 Top-K 排序。",
    path: "/facilities",
  },
  {
    title: "游记社区",
    description: "发布、搜索、评分和评论游记，并展示文本压缩统计。",
    path: "/diaries",
  },
  {
    title: "美食推荐",
    description: "按菜系、热度、评分和距离推荐校区餐厅与菜品。",
    path: "/foods",
  },
  {
    title: "AIGC 辅助",
    description: "生成游记草稿、标题和短视频分镜提示词。",
    path: "/aigc",
  },
  {
    title: "管理后台",
    description: "查看地图、用户、目的地、游记和美食数据规模。",
    path: "/admin",
    adminOnly: true,
  },
];

const visibleModules = computed(() => modules.filter((item) => !item.adminOnly || isAdmin()));
</script>

<style scoped>
.module-card {
  min-height: 180px;
}

.module-card h2 {
  margin: 0 0 10px;
  color: #101828;
  font-size: 18px;
}

.module-card p {
  min-height: 52px;
  margin: 0 0 18px;
  color: #667085;
  line-height: 1.55;
}
</style>
