<template>
  <div>
    <px-table-page
      title="团队成员"
      subtitle="单店两级结构：1 名店长 + N 名店员，店员由店长创建并自动归属本门店"
      :rows="rows"
      :loading="loading"
      :failed="failed"
      @retry="load"
    >
      <template #actions>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon> 新建成员
        </el-button>
      </template>

      <el-table-column label="角色" width="92">
        <template #default="{ row }">
          <el-tag v-if="row.role === 'manager'" type="warning" effect="plain">店长</el-tag>
          <el-tag v-else type="info" effect="plain">店员</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="姓名" width="110" />
      <el-table-column prop="username" label="账号" width="130" />
      <el-table-column label="手机号" width="140">
        <template #default="{ row }">{{ row.phone || "—" }}</template>
      </el-table-column>
      <el-table-column label="归属" min-width="130">
        <template #default="{ row }">
          <span v-if="row.role === 'manager'" class="muted">本店负责人</span>
          <span v-else>归属店长 · {{ managerName }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="84">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'active'" type="success" effect="light">在职</el-tag>
          <el-tag v-else type="info" effect="plain">停用</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <PxActionButton
            v-if="row.status === 'active' && row.role !== 'manager'"
            label="停用" :icon="Hide" tone="danger"
            tip="停用后该账号无法登录后台" @click="doDisable(row)"
          />
          <PxActionButton
            v-else-if="row.status === 'disabled'"
            label="启用" :icon="Check" tone="primary" @click="doEnable(row)"
          />
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>

      <template #empty>
        <PxEmpty variant="user" text="还没有团队成员" hint="点右上角新建店员，归属将自动指向你" />
      </template>
    </px-table-page>

    <px-form-drawer
      v-model="createVisible"
      title="新建成员"
      subtitle="新建后自动归属你（店长）与本门店，初始角色固定为店员"
      :footer-hint="`初始密码：${form.password || '—'}，创建后请告知对方及时修改`"
      :icon="Avatar"
      :saving="saving"
      @cancel="createVisible = false"
      @submit="save"
    >
      <el-form label-width="72px">
        <el-form-item label="姓名"><el-input v-model="form.name" maxlength="50" placeholder="如：小李" /></el-form-item>
        <el-form-item label="账号"><el-input v-model="form.username" maxlength="32" placeholder="登录账号，唯一" /></el-form-item>
        <el-form-item label="初始密码"><el-input v-model="form.password" maxlength="32" placeholder="至少 6 位" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" maxlength="20" placeholder="选填" /></el-form-item>
      </el-form>
    </px-form-drawer>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Avatar, Check, Hide, Plus } from "@element-plus/icons-vue";
import { listStaff, createStaff, disableStaff, updateStaff } from "../../api/staff";
import { useTable } from "../../composables/useTable";
import PxActionButton from "../../components/PxActionButton.vue";
import PxTablePage from "../../components/PxTablePage.vue";
import PxEmpty from "../../components/PxEmpty.vue";

const { rows, loading, failed, load } = useTable(() => listStaff());
const managerName = computed(() => rows.value.find((r) => r.role === "manager")?.name || "店长");

const createVisible = ref(false);
const saving = ref(false);
const form = ref({ name: "", username: "", password: "", phone: "" });

function openCreate() {
  form.value = { name: "", username: "", password: "", phone: "" };
  createVisible.value = true;
}

async function save() {
  if (!form.value.name || !form.value.username || !form.value.password) {
    return ElMessage.warning("请填写姓名、账号与初始密码");
  }
  saving.value = true;
  try {
    await createStaff({ ...form.value });
    createVisible.value = false;
    ElMessage.success("成员已创建，归属本店");
    load();
  } finally {
    saving.value = false;
  }
}

async function doDisable(row) {
  try {
    await ElMessageBox.confirm(
      `确认停用「${row.name}」？停用后该账号将无法登录后台。`,
      "停用成员",
      { type: "warning", confirmButtonText: "确认停用", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  await disableStaff(row.id);
  ElMessage.success("已停用");
  load();
}

async function doEnable(row) {
  await updateStaff(row.id, { status: "active" });
  ElMessage.success("已启用");
  load();
}
</script>

<style scoped>
.muted { color: var(--px-text-3); font-size: var(--px-fs-sm); }
</style>
