<!-- B-团队成员 Staff（对齐画布 2:1341）
     版式：B 端标准列表页（BSidebar220/BTopbar64/Content24 gap16）。
     画布结构：PageHead(标题·副标·添加成员) → Stats(3 卡：在职人数/今日排班/待审核) → MemberTable(5 列)。
     后端现实（staff 模型 v1）：role ∈ {店长,店员}、status ∈ {在职,停用}，无「待审核/排班」字段。
     因此 Stats 的「待审核」按 pending 计（当前恒 0，待后端审批流对齐）、「今日排班」按在职代理（无排班字段）。
     角色/状态 pill 与头像配色严格对齐画布：店长·服务师=松绿系，前台·财务·店员=陶土系。 -->
<template>
  <div>
    <px-table-page class="tp-staff"
      title="团队成员"
      subtitle="门店员工 · 角色与排班"
      :rows="rows"
      :loading="loading"
      :failed="failed"
      @retry="load"
    >
      <template #actions>
        <el-button class="staff-add" type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon> 添加成员
        </el-button>
      </template>

      <!-- 概览统计卡：画布 2:1350，3 卡等高 84、圆角 14、白底描边 -->
      <template #summary>
        <div class="staff-stats">
          <div class="staff-stat">
            <span class="staff-stat__l">在职人数</span>
            <span class="staff-stat__v">{{ activeCount }}</span>
          </div>
          <div class="staff-stat">
            <span class="staff-stat__l">今日排班</span>
            <span class="staff-stat__v">{{ onDutyCount }}</span>
          </div>
          <div class="staff-stat">
            <span class="staff-stat__l">待审核</span>
            <span class="staff-stat__v staff-stat__v--warn">{{ pendingCount }}</span>
          </div>
        </div>
      </template>

      <!-- 成员：头像(角色配色)+姓名，圆角 999 直径 36 -->
      <el-table-column label="成员" min-width="180">
        <template #default="{ row }">
          <div class="staff-member">
            <span class="staff-av" :style="{ background: avatarBg(row) }">{{ avatarText(row) }}</span>
            <span class="staff-name">{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>

      <!-- 角色：浅底 pill，松绿系/陶土系按画布分组 -->
      <el-table-column label="角色" width="110">
        <template #default="{ row }">
          <span class="staff-pill" :class="rolePillClass(row)">{{ row.role_name }}</span>
        </template>
      </el-table-column>

      <el-table-column label="手机号" min-width="130">
        <template #default="{ row }">{{ row.phone || "—" }}</template>
      </el-table-column>

      <!-- 状态：浅底 pill；在职=绿、停用=灰、待审核=陶土描边 -->
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <span class="staff-pill" :class="statusPillClass(row)">{{ statusText(row) }}</span>
        </template>
      </el-table-column>

      <!-- 操作：单行文字链，对齐画布 查看/审核/启用 -->
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'active'" link type="primary" class="staff-link" @click="view(row)">查看</el-button>
          <el-button v-else-if="row.status === 'pending'" link type="warning" class="staff-link" @click="review(row)">审核</el-button>
          <el-button v-else-if="row.status === 'disabled'" link type="primary" class="staff-link" @click="doEnable(row)">启用</el-button>
        </template>
      </el-table-column>

      <template #empty>
        <PxEmpty variant="staff" text="还没有团队成员" hint="点右上角添加成员，归属将自动指向你" />
      </template>
    </px-table-page>

    <px-form-drawer
      v-model="createVisible"
      title="添加成员"
      subtitle="添加后自动归属你（店长）与本门店，初始角色固定为店员"
      :footer-hint="`初始密码：${form.password || '—'}，创建后请告知对方及时修改`"
      :icon="Avatar"
      :saving="saving"
      @cancel="createVisible = false"
      @submit="save"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
        <el-form-item label="姓名" prop="name"><el-input v-model="form.name" maxlength="50" placeholder="如：小李" /></el-form-item>
        <el-form-item label="账号" prop="username"><el-input v-model="form.username" maxlength="32" placeholder="3-32 位字母、数字或下划线" /></el-form-item>
        <el-form-item label="初始密码" prop="password"><el-input v-model="form.password" maxlength="32" placeholder="至少 6 位" /></el-form-item>
        <el-form-item label="手机号" prop="phone"><el-input v-model="form.phone" maxlength="20" placeholder="选填" /></el-form-item>
      </el-form>
    </px-form-drawer>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Avatar, Plus } from "@element-plus/icons-vue";
import { listStaff, createStaff, updateStaff } from "../../api/staff";
import { useTable } from "../../composables/useTable";
import PxEmpty from "../../components/PxEmpty.vue";
import PxFormDrawer from "../../components/PxFormDrawer.vue";
import PxTablePage from "../../components/PxTablePage.vue";

const { rows, loading, failed, load } = useTable(() => listStaff());

// —— 概览统计（画布 2:1350），全部由真实 rows 派生，不虚构 ——
const activeCount = computed(() => rows.value.filter((r) => r.status === "active").length);
const pendingCount = computed(() => rows.value.filter((r) => r.status === "pending").length);
// 今日排班：后端暂无排班字段，v1 以「在职即在岗」代理；待排班模块补齐后替换为真实值
const onDutyCount = computed(() => activeCount.value);

// —— 头像：店长/服务师=松绿，前台/财务/店员=陶土，对齐画布 2:1371/2:1382 ——
const SAGE = "#5B8C85";
const CLAY = "#D9A468";
function isSenior(roleName = "") {
  return roleName.includes("店长") || roleName.includes("服务师");
}
function avatarBg(row) {
  return isSenior(row.role_name) ? SAGE : CLAY;
}
function avatarText(row) {
  return (row.name || "?").charAt(0);
}

// —— 角色 pill 配色分组 ——
function rolePillClass(row) {
  return isSenior(row.role_name) ? "staff-pill--sage" : "staff-pill--clay";
}

// —— 状态文案与 pill 配色 ——
function statusText(row) {
  if (row.status === "pending") return "待审核";
  return row.status === "active" ? "在职" : "停用";
}
function statusPillClass(row) {
  if (row.status === "pending") return "staff-pill--warn";
  return row.status === "active" ? "staff-pill--ok" : "staff-pill--off";
}

// —— 操作 ——
function view(row) {
  ElMessageBox.alert(
    `姓名：${row.name}\n角色：${row.role_name}\n手机号：${row.phone || "未填写"}\n状态：${statusText(row)}`,
    `${row.name} · 成员资料`,
    { confirmButtonText: "知道了", type: "info" },
  );
}
function review(row) {
  // 画布有「审核」动作，但后端 staff 模型暂无 pending 审批流（新建即激活），归口后端待对齐
  ElMessage.info("成员审核功能待后端审批流对齐（当前新建即激活，无待审状态）");
}
async function doEnable(row) {
  await updateStaff(row.id, { status: "active" });
  ElMessage.success("已启用");
  load();
}

// —— 新建 ——
const createVisible = ref(false);
const saving = ref(false);
const form = ref({ name: "", username: "", password: "", phone: "" });
const formRef = ref(null);
const usernamePattern = /^[A-Za-z0-9_]{3,32}$/;
const phonePattern = /^$|^1\d{10}$|^0\d{2,3}-?\d{7,8}$/;
const rules = {
  name: [{ required: true, message: "请填写姓名", trigger: "blur" }],
  username: [
    { required: true, message: "请填写登录账号", trigger: "blur" },
    { pattern: usernamePattern, message: "账号需为 3-32 位字母、数字或下划线", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请填写初始密码", trigger: "blur" },
    { min: 6, message: "初始密码至少 6 位", trigger: "blur" },
  ],
  phone: [{ pattern: phonePattern, message: "手机号或座机格式不正确；不填也可以", trigger: "blur" }],
};

function openCreate() {
  form.value = { name: "", username: "", password: "", phone: "" };
  createVisible.value = true;
}

async function save() {
  await formRef.value?.validate();
  saving.value = true;
  try {
    await createStaff({
      name: form.value.name.trim(),
      username: form.value.username.trim(),
      password: form.value.password,
      phone: form.value.phone.trim() || null,
    });
    createVisible.value = false;
    ElMessage.success("成员已创建，归属本店");
    load();
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
/* 添加按钮：画布 2:1348 松绿实色、圆角 10、白字 13 Medium */
.staff-add { border-radius: 10px; padding: 9px 16px; }

/* 概览统计卡：画布 2:1350/1351~1359 */
.staff-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.staff-stat {
  display: flex; flex-direction: column; gap: 6px;
  padding: 16px; background: #fff;
  border: 1px solid #ECE9E3; border-radius: 14px;
}
.staff-stat__l { font-size: 12px; color: #86909C; }
.staff-stat__v {
  font-size: 24px; font-weight: 600; color: #1F2422;
  font-family: var(--px-font-num, "Inter"); line-height: 1.1;
}
.staff-stat__v--warn { color: #D9A468; }

/* 成员：头像 + 姓名 */
.staff-member { display: flex; align-items: center; gap: 10px; }
.staff-av {
  flex: 0 0 auto; width: 36px; height: 36px; border-radius: 999px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 14px; font-weight: 600;
}
.staff-name { font-size: 14px; font-weight: 500; color: #1F2422; }

/* 通用浅底 pill：圆角 6、padding 4/10，对齐画布 role/st 容器 */
.staff-pill {
  display: inline-flex; align-items: center;
  padding: 4px 10px; border-radius: 6px;
  font-size: 12px; line-height: 1; white-space: nowrap;
}
.staff-pill--sage { background: #EEF4F3; color: #3D5C57; }       /* 店长/服务师 */
.staff-pill--clay { background: #F6EADB; color: #C08A4E; }       /* 前台/财务/店员 */
.staff-pill--ok   { background: #EEF4F3; color: #2E9E6B; }       /* 在职 */
.staff-pill--off  { background: #F2F0EA; color: #86909C; }       /* 停用 */
.staff-pill--warn { background: #F6EADB; color: #C08A4E; border: 1px solid #D9A468; } /* 待审核 */

/* 操作文字链 */
.staff-link { font-weight: 500; }
</style>
