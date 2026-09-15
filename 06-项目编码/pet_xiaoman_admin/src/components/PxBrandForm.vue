<template>
  <div class="brand-form">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="92px" v-loading="loading">
      <h3 class="section">品牌呈现</h3>
      <el-form-item label="对外店名" prop="name">
        <el-input v-model="form.name" maxlength="50" placeholder="门店名称（50 字内）" />
      </el-form-item>
      <el-form-item label="标语" prop="slogan">
        <el-input v-model="form.slogan" maxlength="50" placeholder="如：给ta最后的体面（留空则不展示）" />
      </el-form-item>
      <el-form-item label="Logo 地址" prop="logo_url">
        <el-input v-model="form.logo_url" placeholder="站内路径如 /uploads/logo.png 或 http(s) 地址（留空用中性占位标）" />
      </el-form-item>
      <el-form-item label="主色" prop="primary_color">
        <el-color-picker v-model="form.primary_color" />
        <span class="swatch">{{ form.primary_color }}</span>
        <span class="hint">整套色阶由此色派生（按钮 / 渐变 / 选中态）</span>
      </el-form-item>
      <el-form-item label="预览">
        <div class="preview">
          <div class="preview__device">
            <span class="preview__mark" :style="{ background: markBackground }">
              <img v-if="form.logo_url && !broken" :src="form.logo_url" alt="logo" @error="broken = true" />
              <template v-else>{{ initial }}</template>
            </span>
            <span class="preview__copy">
              <span class="preview__name">{{ form.name || "未命名门店" }}</span>
              <span class="preview__slogan">{{ form.slogan || "（无标语）" }}</span>
              <span class="preview__meta">{{ previewMeta }}</span>
            </span>
            <span class="preview__chip" :style="{ background: form.primary_color }">主色</span>
          </div>
          <div class="preview__readiness">
            <span :class="{ ok: contactReady }">联系信息 {{ contactReady ? "已完整" : "待补齐" }}</span>
            <span :class="{ ok: miniappReady }">独立小程序 {{ miniappReady ? "已绑定" : "未绑定" }}</span>
          </div>
        </div>
      </el-form-item>

      <h3 class="section">联系信息</h3>
      <el-form-item label="咨询电话" prop="contact_phone">
        <el-input v-model="form.contact_phone" placeholder="如 0371-66668888 或 13800000000（用于一键拨号）" />
      </el-form-item>
      <el-form-item label="门店地址" prop="contact_address">
        <el-input v-model="form.contact_address" placeholder="用于导航与小程序展示；按格式：xx 区 xx 路 xx 号" />
      </el-form-item>
      <el-form-item label="营业时间" prop="business_hours">
        <el-input v-model="form.business_hours" placeholder="如 09:00-21:00 / 全年无休" />
      </el-form-item>

      <h3 class="section">独立小程序（多店发布）</h3>
      <el-form-item label="小程序名称" prop="miniapp_name">
        <el-input v-model="form.miniapp_name" maxlength="50" placeholder="微信搜索入口名（独立发布时用）" />
        <span class="hint">多店模式下：每家门店一个独立小程序；不配就走默认包 + slug 换肤</span>
      </el-form-item>
      <el-form-item label="AppID" prop="miniapp_appid">
        <el-input v-model="form.miniapp_appid" placeholder="wx 开头的 18 位字符串" />
      </el-form-item>
      <el-form-item label="搜索入口">
        <el-switch v-model="form.miniapp_entry_enabled" />
        <span class="hint">关闭后此门店不进入微信「附近 / 搜一搜」入口</span>
      </el-form-item>
    </el-form>

    <div class="actions">
      <el-button type="primary" :loading="saving" @click="onSave">保存品牌</el-button>
      <el-button @click="load">重置</el-button>
      <span v-if="savedAt" class="saved">已保存：{{ savedAt }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { getStoreBrand, updateStoreBrand } from "../api/platform";
import { isValidHex, mix } from "../utils/theme";

const props = defineProps({ storeId: { type: Number, required: true } });
const emit = defineEmits(["saved"]);

const loading = ref(false);
const saving = ref(false);
const broken = ref(false);
const savedAt = ref("");
const formRef = ref(null);
// 联系方式与小程序发布信息——C 端按门店「真实电话/地址/营业时间」展示，超管集中维护。
// miniapp_entry_enabled 后端默认 true；空表单里也要给个 fallback，否则 switch 显示为关闭态。
const form = reactive({
  name: "", slogan: "", logo_url: "", primary_color: "#5B8C85",
  contact_phone: "", contact_address: "", business_hours: "",
  miniapp_name: "", miniapp_appid: "", miniapp_entry_enabled: true,
});
const optionalUrlPathPattern = /^$|^https?:\/\/.+|^\/uploads\/.+/i;
const phonePattern = /^$|^1\d{10}$|^0\d{2,3}-?\d{7,8}$/;
const appidPattern = /^$|^wx[A-Za-z0-9]{8,62}$/;
const hexPattern = /^#[0-9A-Fa-f]{6}$/;
const rules = {
  name: [{ required: true, message: "请填写对外店名", trigger: "blur" }],
  slogan: [{ max: 50, message: "标语最多 50 字", trigger: "blur" }],
  logo_url: [
    { pattern: optionalUrlPathPattern, message: "Logo 地址需为 http(s) 地址或 /uploads/ 开头；不填也可以", trigger: "blur" },
  ],
  primary_color: [
    { required: true, message: "请选择主色", trigger: "change" },
    { pattern: hexPattern, message: "主色需为 6 位 HEX 颜色值", trigger: "change" },
  ],
  contact_phone: [{ pattern: phonePattern, message: "电话格式不正确；可填写手机号或座机", trigger: "blur" }],
  contact_address: [{ max: 120, message: "门店地址最多 120 字", trigger: "blur" }],
  business_hours: [{ max: 60, message: "营业时间最多 60 字", trigger: "blur" }],
  miniapp_name: [{ max: 50, message: "小程序名称最多 50 字", trigger: "blur" }],
  miniapp_appid: [{ pattern: appidPattern, message: "AppID 需以 wx 开头，仅包含字母数字；暂未申请可留空", trigger: "blur" }],
};

// 未配 logo 时的中性占位：店名首字（不再回落某家门店的品牌资产）
const initial = computed(() => (form.name || "店").trim().slice(0, 1));

// 预览里的小色块要用「这家店」的色，而不是后台自己的主色，否则预览会撒谎
const markBackground = computed(() => {
  const c = isValidHex(form.primary_color) ? form.primary_color : "#5B8C85";
  return `linear-gradient(180deg, ${c}, ${mix(c, "#000000", 0.12)})`;
});
const contactReady = computed(() => Boolean(form.contact_phone && form.contact_address));
const miniappReady = computed(() => Boolean(form.miniapp_appid && form.miniapp_entry_enabled));
const previewMeta = computed(() => {
  if (form.business_hours) return form.business_hours;
  if (form.contact_phone) return form.contact_phone;
  return "C 端首页展示预览";
});

async function load() {
  if (!props.storeId) return;
  loading.value = true;
  broken.value = false;
  try {
    const p = await getStoreBrand(props.storeId);
    Object.assign(form, {
      name: p.name || "",
      slogan: p.slogan || "",
      logo_url: p.logo_url || "",
      primary_color: p.primary_color || "#5B8C85",
      contact_phone: p.contact_phone || "",
      contact_address: p.contact_address || "",
      business_hours: p.business_hours || "",
      miniapp_name: p.miniapp_name || "",
      miniapp_appid: p.miniapp_appid || "",
      miniapp_entry_enabled: p.miniapp_entry_enabled !== false,
    });
  } finally {
    loading.value = false;
  }
}

async function onSave() {
  await formRef.value?.validate();
  saving.value = true;
  try {
    const p = await updateStoreBrand(props.storeId, {
      name: form.name.trim(),
      slogan: form.slogan.trim(),
      logo_url: form.logo_url.trim(),
      primary_color: form.primary_color,
      contact_phone: form.contact_phone.trim(),
      contact_address: form.contact_address.trim(),
      business_hours: form.business_hours.trim(),
      miniapp_name: form.miniapp_name.trim(),
      miniapp_appid: form.miniapp_appid.trim(),
      miniapp_entry_enabled: form.miniapp_entry_enabled,
    });
    form.logo_url = p.logo_url ?? "";
    savedAt.value = new Date().toLocaleTimeString();
    ElMessage.success("品牌已保存，C 端与后台即刻生效");
    emit("saved", p);
  } finally {
    saving.value = false;
  }
}

watch(() => props.storeId, load, { immediate: true });
</script>

<style scoped>
.brand-form { max-width: 760px; }
.section {
  margin: var(--px-sp-4) 0 var(--px-sp-2);
  font-size: var(--px-fs-md);
  font-weight: 600;
  color: var(--px-text-1);
  border-left: 3px solid var(--px-primary);
  padding-left: var(--px-sp-2);
}
.section:first-of-type { margin-top: 0; }
.swatch {
  margin-left: var(--px-sp-2);
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
  font-variant-numeric: tabular-nums;
}
.hint { margin-left: var(--px-sp-2); font-size: var(--px-fs-xs); color: var(--px-text-3); }

.preview {
  display: grid;
  gap: var(--px-sp-3);
  width: 100%;
  padding: var(--px-sp-3) var(--px-sp-4);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-md);
  background: var(--px-bg-warm);
}
.preview__device {
  display: flex;
  align-items: center;
  gap: var(--px-sp-3);
}
.preview__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: var(--px-radius-sm);
  background: var(--px-primary);
  color: var(--px-text-inverse);
  font-size: var(--px-fs-md);
  font-weight: 600;
}
.preview__mark img { width: 24px; height: 24px; object-fit: contain; }
.preview__copy { display: flex; flex-direction: column; line-height: 1.3; min-width: 0; }
.preview__name { font-size: var(--px-fs-md); font-weight: 600; color: var(--px-text-1); }
.preview__slogan { font-size: var(--px-fs-xs); color: var(--px-text-3); }
.preview__meta {
  margin-top: 2px;
  color: var(--px-text-2);
  font-size: var(--px-fs-xs);
}
.preview__chip {
  margin-left: auto;
  padding: 2px var(--px-sp-2);
  border-radius: 999px;
  color: #fff;
  font-size: var(--px-fs-xs);
}
.preview__readiness {
  display: flex;
  flex-wrap: wrap;
  gap: var(--px-sp-2);
  padding-top: var(--px-sp-2);
  border-top: 1px solid rgba(201, 205, 212, 0.52);
}
.preview__readiness span {
  padding: 3px var(--px-sp-2);
  border-radius: 999px;
  background: rgba(217, 139, 43, 0.10);
  color: var(--px-warning);
  font-size: var(--px-fs-xs);
}
.preview__readiness span.ok {
  background: var(--px-primary-softer);
  color: var(--px-primary-pressed);
}

.actions {
  display: flex;
  align-items: center;
  gap: var(--px-sp-2);
  margin-top: var(--px-sp-4);
}
.saved { font-size: var(--px-fs-xs); color: var(--px-text-3); }
</style>
