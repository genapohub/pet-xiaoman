<!-- B-登录 Login（对齐画布 2:713）
     版式（含画布导出实测的原尺寸，勿凭印象改）：
       1440×900 全屏（根节点 CENTER/CENTER）、**居中单卡**（画布无左右分栏）
      背景：纸感底 → 浅松绿底 垂直渐变（gradientTransform [[0,1,0],[-1,0,1]]）
       Card：宽 **440**、白底、radius **20**、padding **44/40/36**、gap **16**、内容水平居中
         → logo **52×52** 松绿圆角方（radius **14**，内含 **30×30** 品牌标，带松绿柔光）
         → 「宠小满 · 门店管理」**20px 衬线** SemiBold
         → 「爱意小满，不留遗憾」**13px** 中性灰
         → 账号（label 13px + 纸感底 input：radius **10**、内边距 14/12、**实测高 41px**）
         → 密码（同上）
         → 「登 录」sage 实色**胶囊**（radius 999、**实测高 50px**、文字 **15px**）
         → 「忘记密码？请联系平台管理员」12px 灰
       卡片阴影取画布原值：0 16px 40px -8px rgba(0,0,0,.06)（tokens 的 --px-shadow-popup
       是 0 18px 54px rgba(32,52,48,.16)，明显更重，登录页不适用）。
     注意：**首版做成了「左侧深绿说明栏 + 右侧白卡」的左右分栏，与画布不符，已纠正。**
     白标边界：登录时还不知道是哪家店，故此处**不预置任何门店的品牌**——
     「宠小满」是平台名（非门店名），平台级标识不参与门店换肤。 -->
<template>
  <div class="login-page">
    <section class="login-card">
      <span class="brand__mark" aria-hidden="true">
        <!-- 中性品牌标：登录时未知门店，不预置任何门店的 logo/品牌名 -->
        <svg viewBox="0 0 24 24" fill="currentColor">
          <ellipse cx="12" cy="16.8" rx="4.7" ry="3.7" />
          <ellipse cx="5.9" cy="11.4" rx="2.1" ry="2.6" transform="rotate(-16 5.9 11.4)" />
          <ellipse cx="9.9" cy="8.6" rx="2.1" ry="2.7" />
          <ellipse cx="14.1" cy="8.6" rx="2.1" ry="2.7" />
          <ellipse cx="18.1" cy="11.4" rx="2.1" ry="2.6" transform="rotate(16 18.1 11.4)" />
        </svg>
      </span>

      <h1 class="brand__title">宠小满 · 门店管理</h1>
      <p class="brand__sub">爱意小满，不留遗憾</p>

      <form class="login-form" @submit.prevent="onLogin">
        <label class="field">
          <span class="field__label">账号</span>
          <el-input v-model="username" class="field__input" placeholder="请输入账号" @keyup.enter="onLogin" />
        </label>

        <label class="field">
          <span class="field__label">密码</span>
          <el-input v-model="password" class="field__input" type="password" show-password
            placeholder="请输入密码" @keyup.enter="onLogin" />
        </label>

        <el-button type="primary" class="login-btn" :loading="loading" @click="onLogin">
          登 录
        </el-button>
      </form>

      <p class="login-footnote">忘记密码？请联系平台管理员</p>
    </section>
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
/* 全屏底色：纸感 → 浅松绿（画布 gradientTransform [[0,1,0],[-1,0,1]] = 自上而下）
   末端色取画布原值，已沉淀为 --px-primary-light，不使用 --px-primary-weak */
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: var(--px-sp-6);
  box-sizing: border-box;
  background: linear-gradient(180deg, var(--px-bg-paper), var(--px-primary-light));
}

/* 居中单卡：宽 440（画布实测），内容水平居中；阴影取画布原值（y16/blur40/spread-8/6%） */
.login-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--px-sp-4);
  width: 440px;
  max-width: 100%;
  padding: 40px 44px 36px;
  box-sizing: border-box;
  background: var(--px-bg-card);
  border-radius: 20px;
  box-shadow: 0 16px 40px -8px rgba(0, 0, 0, 0.06);
}

/* logo：52×52 松绿圆角方（radius 14），内含 30×30 品牌标
   柔光也来自画布节点 2:715（DROP_SHADOW y6/blur14/30% 松绿） */
.brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--px-primary);
  color: #fff;
  box-shadow: 0 6px 14px rgba(91, 140, 133, 0.3);
}
.brand__mark svg { width: 30px; height: 30px; }

/* 标题用衬线：画布为 Noto Serif SC SemiBold 20px */
.brand__title {
  margin: 0;
  font-family: var(--px-font-serif);
  font-size: var(--px-fs-xl);
  font-weight: 600;
  line-height: 1.3;
  color: var(--px-text-1);
  text-align: center;
}
.brand__sub {
  margin: 0;
  font-size: var(--px-fs-sm);
  color: var(--px-text-3);
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--px-sp-4);
  width: 100%;
  margin-top: var(--px-sp-2);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field__label {
  font-size: var(--px-fs-sm);
  font-weight: 500;
  color: var(--px-text-2);
}
/* 输入框按画布改为「纸感底 + radius 10 + 无描边 + 高 41px」：
   41px 是画布节点 2:721 导出实测值（内边距 12/12 + 13px 文字行高），
   此前写的 44px 是凭印象定的，偏高 3px。
   tokens.css 的默认 input 是白底 + 1px inset 描边（36px 高），与此处设计不符。
   白卡片上纸感底本身就能辨位，故去掉描边；聚焦态保留品牌色环。 */
.field__input :deep(.el-input__wrapper) {
  height: 41px;
  border-radius: 10px;
  background: var(--px-bg-paper);
  box-shadow: none;
  padding: 0 14px;
}
.field__input :deep(.el-input__wrapper:hover) { box-shadow: none; }
.field__input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--px-primary) inset, var(--px-shadow-focus);
  background: var(--px-bg-card);
}

/* 主按钮：胶囊（画布 radius 999）、高 50px（画布节点 2:727 导出实测）、文字 15px。
   注意不要加 letter-spacing —— 画布文案本身就是带空格的「登 录」，再加字距就比画布松了。 */
.login-btn {
  width: 100%;
  height: 50px;
  margin-top: var(--px-sp-2);
  border-radius: 999px;
  font-size: 15px;
  font-weight: 500;
  box-shadow: 0 6px 16px rgba(91, 140, 133, 0.28);
}

.login-footnote {
  margin: 0;
  font-size: var(--px-fs-xs);
  color: var(--px-text-3);
  text-align: center;
}

@media (max-width: 480px) {
  .login-page { padding: var(--px-sp-4); }
  .login-card { padding: var(--px-sp-8) var(--px-sp-6); }
}
</style>
