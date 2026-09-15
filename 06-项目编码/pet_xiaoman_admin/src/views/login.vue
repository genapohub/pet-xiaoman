<template>
  <div class="login-page">
    <div class="login-shell">
      <aside class="login-aside" aria-label="后台工作台说明">
        <span class="login-aside__kicker">PET XIAOMAN / OPERATIONS</span>
        <h2>把每一次告别，<br />交付得更稳。</h2>
        <p>从新订单确认，到服务节点与影像记录，今天的工作都在一个清晰的工作台里。</p>
        <div class="login-aside__points">
          <span><i class="point-dot" />待办优先</span>
          <span><i class="point-dot" />过程可查</span>
          <span><i class="point-dot" />门店隔离</span>
        </div>
      </aside>

      <main class="login-card">
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
        <p class="login-footnote">平台管理员与门店账号使用各自分配的权限登录</p>
      </main>
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
  padding: var(--px-sp-6);
  background: var(--px-bg-page);
}
.login-shell {
  display: grid;
  grid-template-columns: minmax(280px, 0.86fr) minmax(360px, 1fr);
  width: min(820px, 100%);
  min-height: 480px;
  overflow: hidden;
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-xl);
  box-shadow: var(--px-shadow-popup);
}
.login-aside {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: var(--px-sp-8);
  color: var(--px-text-inverse);
  background: var(--px-primary-pressed);
}
.login-aside__kicker {
  color: rgba(255, 255, 255, 0.68);
  font-size: var(--px-fs-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}
.login-aside h2 {
  margin: auto 0 var(--px-sp-4);
  font-size: 30px;
  line-height: 1.35;
  font-weight: 600;
}
.login-aside p {
  max-width: 24ch;
  margin: 0;
  color: rgba(255, 255, 255, 0.78);
  font-size: var(--px-fs-sm);
  line-height: 1.75;
}
.login-aside__points {
  display: flex;
  flex-wrap: wrap;
  gap: var(--px-sp-2) var(--px-sp-4);
  margin-top: var(--px-sp-8);
  color: rgba(255, 255, 255, 0.86);
  font-size: var(--px-fs-xs);
}
.login-aside__points span {
  display: inline-flex;
  align-items: center;
  gap: var(--px-sp-1);
}
.point-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--px-chart-2);
}
.login-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: auto;
  padding: var(--px-sp-8);
  background: var(--px-bg-card);
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
  background: var(--px-primary);
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
.login-footnote {
  margin: var(--px-sp-4) 0 0;
  color: var(--px-text-3);
  font-size: var(--px-fs-xs);
  line-height: 1.6;
  text-align: center;
}
@media (max-width: 680px) {
  .login-page { padding: var(--px-sp-4); }
  .login-shell { display: block; min-height: auto; }
  .login-aside { min-height: 190px; padding: var(--px-sp-6); }
  .login-aside h2 { margin: var(--px-sp-8) 0 var(--px-sp-2); font-size: 24px; }
  .login-aside p { max-width: 40ch; }
  .login-aside__points { margin-top: var(--px-sp-4); }
  .login-card { padding: var(--px-sp-6); }
}
</style>
