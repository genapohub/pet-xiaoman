<template>
  <el-skeleton v-if="loading" :rows="8" animated />

  <div v-else-if="order">
    <PxPageHeader :title="order.order_no" :subtitle="`下单时间 ${fmtDateTime(order.created_at)}`" back>
      <template #actions>
        <PxStatusTag :value="order.status" />
        <el-tag v-if="order.is_night" type="danger" size="small" effect="plain">夜间单</el-tag>
      </template>
    </PxPageHeader>

    <div class="body">
      <div class="main-col">
        <el-card shadow="never" class="block">
          <template #header><span class="card-title">宠物与预约</span></template>
          <el-descriptions :column="2" size="small">
            <el-descriptions-item label="期望服务时间">{{ fmtDateTime(order.expect_time) }}</el-descriptions-item>
            <el-descriptions-item label="接送地址">{{ order.address || "到店自送" }}</el-descriptions-item>
            <el-descriptions-item label="改期次数">{{ order.reschedule_count }} / 1</el-descriptions-item>
            <el-descriptions-item label="价格版本">{{ order.price_version || "—" }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never" class="block">
          <template #header><span class="card-title">费用明细</span></template>
          <div class="amount-row">
            <span>套餐 + 加购合计</span><b class="num">¥{{ fmtMoney(order.total_amount) }}</b>
          </div>
          <div class="amount-row">
            <span>支付状态</span>
            <span>
              <el-tag size="small">{{ order.pay_type }}</el-tag>
              <span class="amount-note">已付 ¥{{ fmtMoney(order.paid_amount) }}</span>
            </span>
          </div>
          <div v-for="a in order.addons" :key="a.item_id" class="amount-row addon">
            <span>+ {{ a.name }}</span><span class="num">¥{{ fmtMoney(a.price_snapshot) }}</span>
          </div>
        </el-card>

        <el-card shadow="never" class="block">
          <template #header><span class="card-title">服务影像时间线</span></template>
          <PxEmpty v-if="!media.length" variant="image"
            text="还没有上传影像" hint="按服务节点拍照上传，客户可在小程序实时查看" />
          <el-timeline v-else>
            <el-timeline-item v-for="group in groupedMedia" :key="group.node" :type="group.type">
              <b>{{ group.node }}</b>
              <div class="thumbs">
                <template v-for="m in group.items" :key="m.id">
                  <el-image v-if="m.media_type === 'photo'" :src="m.url" fit="cover" class="thumb"
                    :preview-src-list="photoList(group.items)" preview-teleported />
                  <video v-else :src="m.url" class="thumb" controls />
                </template>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </div>

      <div class="side-col">
        <el-card shadow="never" class="block">
          <template #header><span class="card-title">状态操作</span></template>
          <el-button type="primary" class="full" v-if="order.status === '待确认'" @click="doConfirm">
            确认订单（30 分钟 SLA）
          </el-button>
          <el-button class="full" v-if="order.status === '已预约'" @click="doTransition('接宠中')">
            出发接宠
          </el-button>

          <template v-if="['接宠中', '服务中', '待交付'].includes(order.status)">
            <el-upload :show-file-list="false" :auto-upload="false"
              :on-change="(f) => onUpload(f.raw)" accept=".jpg,.jpeg,.png,.webp">
              <el-button class="full upload">
                <el-icon><Upload /></el-icon> 上传{{ uploadNode }}影像
              </el-button>
            </el-upload>
            <el-button v-if="order.status === '接宠中'" type="primary" class="full" @click="doTransition('服务中')">
              到达门店，开始服务
            </el-button>
            <el-button v-if="order.status === '服务中'" type="primary" class="full" @click="doTransition('待交付')">
              火化完成，待交付
            </el-button>
          </template>

          <template v-if="order.status === '待交付'">
            <el-button type="warning" class="full" @click="settleVisible = true">结清收款（到店付）</el-button>
            <el-button type="success" class="full last" @click="doTransition('已完成')">标记完成</el-button>
          </template>

          <div class="secondary">
            <el-button text :disabled="order.reschedule_count >= 1 || terminal"
              @click="rescheduleVisible = true">改期（免费 1 次）</el-button>
            <el-button text type="danger" v-if="!terminal" @click="cancelVisible = true">取消订单</el-button>
          </div>
        </el-card>

        <el-card shadow="never" class="block sticky">
          <template #header><span class="card-title">内部备注（客户不可见）</span></template>
          <el-input v-model="notes" type="textarea" :rows="4" @blur="saveNotesNow" />
          <span v-if="notesSaved" class="saved">已保存</span>
        </el-card>
      </div>
    </div>

    <el-dialog v-model="settleVisible" title="到店付结清" width="360px">
      <el-input-number v-model="settleAmount" :min="0" :precision="2" class="w-full" />
      <template #footer>
        <el-button @click="settleVisible = false">取消</el-button>
        <el-button type="primary" @click="doSettle">确认收款</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="rescheduleVisible" title="改期（免费 1 次）" width="360px">
      <el-date-picker v-model="rescheduleTime" type="datetime" format="YYYY-MM-DD HH:mm" class="w-full" />
      <template #footer>
        <el-button @click="rescheduleVisible = false">取消</el-button>
        <el-button type="primary" @click="doReschedule">确认改期</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="cancelVisible" title="取消订单" width="360px">
      <el-input v-model="cancelReason" type="textarea" placeholder="必填取消原因" :rows="3" />
      <template #footer>
        <el-button @click="cancelVisible = false">取消</el-button>
        <el-button type="danger" @click="doCancel">确认取消</el-button>
      </template>
    </el-dialog>
  </div>

  <PxEmpty v-else text="订单不存在或已被删除" hint="返回订单列表重新进入">
    <template #action>
      <el-button type="primary" @click="$router.push('/orders')">返回订单列表</el-button>
    </template>
  </PxEmpty>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { Upload } from "@element-plus/icons-vue";
import { confirmOrder, getOrderDetail, reschedule, saveNotes,
         settleOrder, transitionOrder, uploadMedia } from "../../api/order";
import PxPageHeader from "../../components/PxPageHeader.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtDateTime, fmtMoney } from "../../utils/format";

const route = useRoute();
const orderNo = route.params.orderNo;
const order = ref(null);
const media = ref([]);
const loading = ref(true);
const notes = ref("");
const notesSaved = ref(false);
const settleVisible = ref(false);
const settleAmount = ref(0);
const rescheduleVisible = ref(false);
const rescheduleTime = ref("");
const cancelVisible = ref(false);
const cancelReason = ref("");

const terminal = computed(() => ["已完成", "已取消"].includes(order.value?.status));
const uploadNode = computed(() =>
  ({ 接宠中: "接宠完成", 服务中: "火化完成", 待交付: "交付完成" }[order.value?.status] || "接宠完成"));

const groupedMedia = computed(() => {
  const groups = {};
  for (const m of media.value) {
    (groups[m.node] ||= { node: m.node, items: [], type: "primary" }).items.push(m);
  }
  return Object.values(groups);
});
const photoList = (items) => items.filter((m) => m.media_type === "photo").map((m) => m.url);

async function load() {
  loading.value = true;
  try {
    const d = await getOrderDetail(orderNo);
    order.value = d;
    media.value = d.media || [];
    notes.value = d.notes || "";
  } finally { loading.value = false; }
}

async function doConfirm() { await confirmOrder(orderNo); refresh("已确认"); }
async function doTransition(target) {
  await transitionOrder(orderNo, { target });
  refresh(`已流转至「${target}」`);
}
async function onUpload(file) {
  await uploadMedia(orderNo, uploadNode.value, file);
  ElMessage.success("影像已上传，客户可见");
  await load();
}
async function doSettle() {
  await settleOrder(orderNo, settleAmount.value);
  settleVisible.value = false;
  refresh("已结清收款");
}
async function doReschedule() {
  if (!rescheduleTime.value) return;
  await reschedule(orderNo, rescheduleTime.value);
  rescheduleVisible.value = false;
  refresh("已改期");
}
async function doCancel() {
  if (!cancelReason.value) return ElMessage.warning("请填写取消原因");
  await transitionOrder(orderNo, { target: "已取消", reason: cancelReason.value });
  cancelVisible.value = false;
  refresh("已取消");
}
async function saveNotesNow() {
  await saveNotes(orderNo, notes.value);
  notesSaved.value = true;
  setTimeout(() => (notesSaved.value = false), 2000);
}
function refresh(msg) { ElMessage.success(msg); load(); }

onMounted(load);
</script>

<style scoped>
.body {
  display: flex;
  gap: var(--px-sp-4);
  align-items: flex-start;
}
.main-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.side-col {
  width: 332px;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: var(--px-sp-2);
}
.block { margin-bottom: var(--px-sp-4); }
.card-title { font-weight: 600; color: var(--px-text-1); }
.sticky { position: relative; }
.full {
  width: 100%;
  margin-bottom: var(--px-sp-2);
}
.full.last { margin-bottom: 0; }
.upload { margin-bottom: var(--px-sp-2); }
.secondary {
  display: flex;
  justify-content: space-between;
  margin-top: var(--px-sp-2);
}
.amount-row {
  display: flex;
  justify-content: space-between;
  gap: var(--px-sp-4);
  padding: var(--px-sp-1) 0;
  color: var(--px-text-2);
}
.amount-row.addon {
  padding-left: var(--px-sp-3);
  font-size: var(--px-fs-sm);
  color: var(--px-text-3);
}
.amount-note { margin-left: var(--px-sp-2); color: var(--px-text-2); }
.num { font-variant-numeric: tabular-nums; }
.thumbs {
  display: flex;
  gap: var(--px-sp-2);
  margin-top: var(--px-sp-2);
  flex-wrap: wrap;
}
.thumb {
  width: 64px;
  height: 64px;
  border-radius: var(--px-radius-sm);
}
.saved {
  position: absolute;
  right: var(--px-sp-4);
  top: 18px;
  font-size: var(--px-fs-xs);
  color: var(--px-success);
}
.w-full { width: 100%; }

@media (max-width: 1366px) {
  /* 窄屏时操作区上移：员工进来是为了推进订单，不是看资料 */
  .body { flex-direction: column-reverse; }
  .side-col { width: 100%; position: static; }
}
</style>
