<template>
  <div class="brand-form">
    <el-form label-width="80px" v-loading="loading">
      <el-form-item label="对外店名">
        <el-input v-model="form.name" maxlength="50" placeholder="门店名称（50 字内）" />
      </el-form-item>
      <el-form-item label="标语">
        <el-input v-model="form.slogan" maxlength="50" placeholder="如：给ta最后的体面（留空则不展示）" />
      </el-form-item>
      <el-form-item label="Logo 地址">
        <el-input v-model="form.logo_url" placeholder="站内路径如 /uploads/logo.png 或 http(s) 地址（留空用中性占位标）" />
      </el-form-item>
      <el-form-item label="主色">
        <el-color-picker v-model="form.primary_color" />
        <span class="swatch">{{ form.primary_color }}</span>
        <span class="hint">整套色阶由此色派生（按钮 / 渐变 / 选中态）</span>
      </el-form-item>
      <el-form-item label="预览">
        <div class="preview">
          <span class="preview__mark" :style="{ background: markBackground }">
            <img v-if="form.logo_url && !broken" :src="form.logo_url" alt="logo" @error="broken = true" />
            <template v-else>{{ initial }}</template>
          </span>
          <span class="preview__copy">
            <span class="preview__name">{{ form.name || "未命名门店" }}</span>
            <span class="preview__slogan">{{ form.slogan || "（无标语）" }}</span>
          </span>
          <span class="preview__chip" :style="{ background: form.primary_color }">主色</span>
        </div>
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
const form = reactive({ name: "", slogan: "", logo_url: "", primary_color: "#5B8C85" });

// 未配 logo 时的中性占位：店名首字（不再回落某家门店的品牌资产）
const initial = computed(() => (form.name || "店").trim().slice(0, 1));

// 预览里的小色块要用「这家店」的色，而不是后台自己的主色，否则预览会撒谎
const markBackground = computed(() => {
  const c = isValidHex(form.primary_color) ? form.primary_color : "#5B8C85";
  return `linear-gradient(180deg, ${c}, ${mix(c, "#000000", 0.12)})`;
});

async function load() {
  if (!props.storeId) return;
  loading.value = true;
  broken.value = false;
  try {
    const p = await getStoreBrand(props.storeId);
    form.name = p.name || "";
    form.slogan = p.slogan || "";
    form.logo_url = p.logo_url || "";
    form.primary_color = p.primary_color || "#5B8C85";
  } finally {
    loading.value = false;
  }
}

async function onSave() {
  if (!form.name.trim()) return ElMessage.warning("请填写对外店名");
  saving.value = true;
  try {
    const p = await updateStoreBrand(props.storeId, {
      name: form.name.trim(),
      slogan: form.slogan.trim(),
      logo_url: form.logo_url.trim(),
      primary_color: form.primary_color,
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
.brand-form { max-width: 560px; }
.swatch {
  margin-left: var(--px-sp-2);
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
  font-variant-numeric: tabular-nums;
}
.hint { margin-left: var(--px-sp-2); font-size: var(--px-fs-xs); color: var(--px-text-3); }

.preview {
  display: flex;
  align-items: center;
  gap: var(--px-sp-3);
  width: 100%;
  padding: var(--px-sp-3) var(--px-sp-4);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-md);
  background: var(--px-bg-warm);
}
.preview__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: var(--px-radius-sm);
  background: linear-gradient(180deg, var(--px-primary), var(--px-primary-pressed));
  color: var(--px-text-inverse);
  font-size: var(--px-fs-md);
  font-weight: 600;
}
.preview__mark img { width: 24px; height: 24px; object-fit: contain; }
.preview__copy { display: flex; flex-direction: column; line-height: 1.3; min-width: 0; }
.preview__name { font-size: var(--px-fs-md); font-weight: 600; color: var(--px-text-1); }
.preview__slogan { font-size: var(--px-fs-xs); color: var(--px-text-3); }
.preview__chip {
  margin-left: auto;
  padding: 2px var(--px-sp-2);
  border-radius: 999px;
  color: #fff;
  font-size: var(--px-fs-xs);
}

.actions {
  display: flex;
  align-items: center;
  gap: var(--px-sp-2);
  margin-top: var(--px-sp-4);
}
.saved { font-size: var(--px-fs-xs); color: var(--px-text-3); }
</style>
