<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <span class="brand__mark">宠</span>
        <div>
          <h1 class="brand__name">宠小满</h1>
          <p class="brand__sub">门店管理后台</p>
          <p class="brand__slogan">爱意小满，不留遗憾</p>
        </div>
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
import { useRouter } from "vue-router";
import { useUserStore } from "../stores/user";

const router = useRouter();
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
    router.push("/dashboard");
  } finally { loading.value = false; }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 暖松绿到页面灰的柔和过渡，呼应品牌主色而不喧宾夺主 */
  background: linear-gradient(135deg, #EAF1EF 0%, #F7F8FA 55%);
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
  align-items: center;
  gap: var(--px-sp-3);
  margin-bottom: var(--px-sp-6);
}
.brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--px-radius-md);
  background: var(--px-primary);
  color: var(--px-text-inverse);
  font-size: var(--px-fs-lg);
  font-weight: 600;
}
.brand__name {
  margin: 0;
  font-size: var(--px-fs-xl);
  font-weight: 600;
  color: var(--px-text-1);
}
.brand__sub {
  margin: 2px 0 0;
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}
.brand__slogan {
  margin: 4px 0 0;
  font-size: var(--px-fs-xs);
  color: var(--px-primary);
  letter-spacing: 1px;
}
.login-btn { width: 100%; margin-top: var(--px-sp-2); }
</style>
