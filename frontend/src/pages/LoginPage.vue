<template>
  <section class="login-shell">
    <div class="login-brand">
      <span class="brand-mark">游</span>
      <div>
        <strong>Smart Tour Guide</strong>
        <small>先登录账号，再选择旅游算法服务。</small>
      </div>
    </div>

    <el-card shadow="never" class="login-card">
      <template #header>
        <div class="card-header">
          <span>账号登录</span>
          <el-tag type="success" effect="plain">全应用账号</el-tag>
        </div>
      </template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form label-position="top">
            <el-form-item label="账号或邮箱">
              <el-input v-model="loginForm.username_or_email" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" show-password />
            </el-form-item>
          </el-form>
          <div class="button-row wrap">
            <el-button type="primary" :loading="authLoading" @click="login">登录并进入系统</el-button>
            <el-button @click="fillDemoLogin">普通用户</el-button>
            <el-button @click="fillAdminLogin">管理员</el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form label-position="top">
            <el-form-item label="用户名">
              <el-input v-model="registerForm.username" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="registerForm.email" />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="registerForm.nickname" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="registerForm.password" type="password" show-password />
            </el-form-item>
          </el-form>
          <el-button type="primary" :loading="authLoading" @click="register">注册并进入系统</el-button>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { apiPost, type AuthPayload } from "../services/api";
import { applyAuthPayload } from "../services/auth";

const route = useRoute();
const router = useRouter();
const activeTab = ref("login");
const authLoading = ref(false);
const loginForm = reactive({
  username_or_email: "user01",
  password: "demo123456",
});
const registerSeed = Date.now().toString().slice(-5);
const registerForm = reactive({
  username: `visitor_${registerSeed}`,
  email: `visitor_${registerSeed}@example.com`,
  nickname: "新游客",
  password: "demo123456",
});

async function login() {
  authLoading.value = true;
  try {
    const payload = await apiPost<AuthPayload>("/api/v1/users/login", loginForm);
    await enterApp(payload);
    ElMessage.success("登录成功");
  } finally {
    authLoading.value = false;
  }
}

async function register() {
  authLoading.value = true;
  try {
    const payload = await apiPost<AuthPayload>("/api/v1/users/register", {
      ...registerForm,
      interests: [],
    });
    await enterApp(payload);
    ElMessage.success("注册成功");
  } finally {
    authLoading.value = false;
  }
}

async function enterApp(payload: AuthPayload) {
  applyAuthPayload(payload);
  const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
  await router.replace(redirect);
}

function fillDemoLogin() {
  loginForm.username_or_email = "user01";
  loginForm.password = "demo123456";
}

function fillAdminLogin() {
  loginForm.username_or_email = "admin01";
  loginForm.password = "admin123456";
}
</script>

<style scoped>
.login-shell {
  display: grid;
  min-height: 100vh;
  place-items: center;
  gap: 18px;
  padding: 40px;
  background:
    linear-gradient(180deg, rgba(231, 245, 242, 0.72), rgba(246, 247, 249, 0) 300px),
    #f6f7f9;
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.login-brand strong {
  display: block;
  color: #101828;
  font-size: 20px;
}

.login-brand small {
  display: block;
  margin-top: 4px;
  color: #667085;
}

.login-card {
  width: min(520px, 100%);
}

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
</style>
