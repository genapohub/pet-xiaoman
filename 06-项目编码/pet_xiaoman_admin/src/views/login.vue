<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <!-- 中性爪印占位：登录时还不知道是哪家店，所以不预置任何一家门店的 logo/品牌名 -->
        <span class="brand__mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <ellipse cx="12" cy="16.8" rx="4.7" ry="3.7" />
            <ellipse cx="5.9" cy="11.4" rx="2.1" ry="2.6" transform="rotate(-16 5.9 11.4)" />
            <ellipse cx="9.9" cy="8.6" rx="2.1" ry="2.7" />
            <ellipse cx="14.1" cy="8.6" rx="2.1" ry="2.7" />
            <ellipse cx="18.1" cy="11.4" rx="2.1" ry="2.6" transform="rotate(16 18.1 11.4)" />
          </svg>
        </span>
        <h1 class="brand__title">门店管理后台</h1>
        <p class="brand__sub">请使用平台或门店分配的账号登录</p>
      </div>
      <el-form @submit.prevent>
        <el-form-item><el-input v-model="username" placeholder="账号" size="large" /></el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" show-password size="large"
            @keyup.enter="onLogin" />
        </el-form-item>
        <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="onLogin">
          登录后台
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "../stores/user";

const router = useRouter();
const route = useRoute();
const user = useUserStore();
const username = ref("");
const password = ref("");
const loading = ref(false);

// 登录失败要留在当前页并给出原因，不要莽撞捕获后照样跳首页
async function onLogin() {
  if (!username.value || !password.value) return;
  loading.value = true;
  try {
    await user.login(username.value, password.value);
    router.push(route.query.redirect || "/dashboard");
  } finally { loading.value = false; }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 主色浅底到页面灰的柔和过渡：跟着 token 走，换店不换代码 */
  background: linear-gradient(135deg, var(--px-primary-weak) 0%, var(--px-bg-page) 55%);
}
.login-card {
  width: 380px;
  padding: var(--px-sp-8);
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-lg);
  box-shadow: var(--px-shadow-card);
}
.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: var(--px-sp-6);
}
.brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  margin-bottom: var(--px-sp-3);
  border-radius: var(--px-radius-lg);
  background: linear-gradient(180deg, var(--px-primary), var(--px-primary-pressed));
  color: #fff;
  box-shadow: 0 12px 26px rgba(91, 140, 133, 0.22);
}
.brand__mark svg { width: 30px; height: 30px; }
.brand__title {
  margin: 0;
  font-size: var(--px-fs-xl);
  font-weight: 600;
  color: var(--px-text-1);
}
.brand__sub {
  margin: 6px 0 0;
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}
.login-btn { width: 100%; margin-top: var(--px-sp-2); }
</style>
