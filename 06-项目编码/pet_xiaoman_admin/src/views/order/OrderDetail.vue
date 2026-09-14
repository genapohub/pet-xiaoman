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
          <div class="amount-row" v-if="order.refund_status && order.refund_status !== '无'">
            <span>退款状态</span>
            <span>
              <el-tag size="small" :type="refundTagType">{{ order.refund_status }}</el-tag>
              <span v-if="order.cancel_reason" class="amount-note">{{ order.cancel_reason }}</span>
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
                  <el-image v-if="m.media_type === 'photo'" :src="mediaUrl(m.url)" fit="cover" class="thumb"
                    :preview-src-list="photoList(group.items)" preview-teleported />
                  <video v-else :src="mediaUrl(m.url)" class="thumb" controls />
                </template>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </div>

      <div class="side-col">
        <el-card shadow="never" class="block">
          <template #header><span class="card-title">状态操作</span></template>
          <div class="operation-guide" :class="{ 'is-terminal': terminal }">
            <strong>{{ operationGuide.title }}</strong>
            <p>{{ operationGuide.text }}</p>
          </div>
          <el-button type="primary" class="full" v-if="order.status === '待确认'" @click="doConfirm">
            <el-icon><CircleCheck /></el-icon>
            确认订单（30 分钟 SLA）
          </el-button>
          <el-button class="full" v-if="order.status === '已预约'" @click="doTransition('接宠中')">
            <el-icon><Van /></el-icon>
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
              <el-icon><House /></el-icon>
              到达门店，开始服务
            </el-button>
            <el-button v-if="order.status === '服务中'" type="primary" class="full" @click="doTransition('待交付')">
              <el-icon><Finished /></el-icon>
              火化完成，待交付
            </el-button>
          </template>

          <template v-if="order.status === '待交付'">
            <el-button type="warning" class="full" @click="openSettle">
              <el-icon><Money /></el-icon> 结清收款（到店付）
            </el-button>
            <el-button type="success" class="full last" :disabled="!canComplete" @click="doTransition('已完成')">
              <el-icon><CircleCheck /></el-icon> 标记完成
            </el-button>
            <p v-if="!canComplete" class="operation-warning">还有 ¥{{ fmtMoney(outstandingAmount) }} 未结清，先确认收款再完成订单。</p>
          </template>

          <div class="secondary">
            <el-button text type="warning" v-if="refundActionable && user.canPerm('order.refund')" @click="openRefund">
              <el-icon><Money /></el-icon> 处理退款
            </el-button>
            <el-tooltip
              v-else-if="refundActionable"
              content="当前账号没有退款处理权限，请联系店长"
              placement="top"
            >
              <el-button text type="warning" disabled>
                <el-icon><Money /></el-icon> 处理退款
              </el-button>
            </el-tooltip>
            <el-button text :disabled="order.reschedule_count >= 1 || terminal"
              @click="rescheduleVisible = true">
              <el-icon><Calendar /></el-icon> 改期（免费 1 次）
            </el-button>
            <el-button text type="danger" v-if="!terminal" @click="cancelVisible = true">
              <el-icon><CircleClose /></el-icon> 取消订单
            </el-button>
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
      <p class="dialog-hint">本单合计 ¥{{ fmtMoney(order.total_amount) }}，已付 ¥{{ fmtMoney(order.paid_amount) }}，待收 ¥{{ fmtMoney(outstandingAmount) }}。</p>
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
    <el-dialog v-model="refundVisible" title="退款处理" width="420px">
      <el-alert
        type="warning"
        :closable="false"
        title="当前为人工退款闭环：确认线下或微信商户后台已处理后，再在这里标记。"
      />
      <el-radio-group v-model="refundStatus" class="refund-status">
        <el-radio-button value="已退款">已退款</el-radio-button>
        <el-radio-button value="退款失败">退款失败</el-radio-button>
      </el-radio-group>
      <el-input v-model="refundNote" type="textarea" placeholder="填写退款单号、失败原因或处理备注" :rows="3" />
      <template #footer>
        <el-button @click="refundVisible = false">取消</el-button>
        <el-button type="primary" @click="doMarkRefund">保存退款结果</el-button>
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
import { ElMessage, ElMessageBox } from "element-plus";
import { Calendar, CircleCheck, CircleClose, Finished, House, Money, Upload, Van } from "@element-plus/icons-vue";
import { confirmOrder, getOrderDetail, reschedule, saveNotes,
         markRefund, settleOrder, transitionOrder, uploadMedia } from "../../api/order";
import PxPageHeader from "../../components/PxPageHeader.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtDateTime, fmtMoney } from "../../utils/format";
import { mediaUrl } from "../../utils/url";
import { useUserStore } from "../../stores/user";

const route = useRoute();
const user = useUserStore();
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
const refundVisible = ref(false);
const refundStatus = ref("已退款");
const refundNote = ref("");

const terminal = computed(() => ["已完成", "已取消"].includes(order.value?.status));
const refundActionable = computed(() => ["退款中", "退款失败"].includes(order.value?.refund_status));
const outstandingAmount = computed(() => Math.max(Number(order.value?.total_amount || 0) - Number(order.value?.paid_amount || 0), 0));
const canComplete = computed(() => outstandingAmount.value <= 0.0001);
const refundTagType = computed(() => ({
  退款中: "warning",
  已退款: "success",
  退款失败: "danger",
}[order.value?.refund_status] || "info"));
const uploadNode = computed(() =>
  ({ 接宠中: "接宠完成", 服务中: "火化完成", 待交付: "交付完成" }[order.value?.status] || "接宠完成"));
const operationGuide = computed(() => ({
  待确认: { title: "下一步：确认订单", text: "核对预约时间、地址和费用后确认；确认后客户会看到订单进入待服务状态。" },
  已预约: { title: "下一步：出发接宠", text: "准备接宠时再点击，便于客户知道服务已经启动。" },
  接宠中: { title: "下一步：上传接宠影像并开始服务", text: "建议先上传接宠完成照片，再流转到服务中。" },
  服务中: { title: "下一步：上传火化完成影像", text: "完成服务后上传节点影像，再进入待交付。" },
  待交付: { title: "下一步：结清收款并完成", text: "到店付需要先标记收款；结清后再完成订单，避免账务漏记。" },
  已完成: { title: "订单已完成", text: "可继续补充内部备注，订单主流程已闭环。" },
  已取消: { title: "订单已取消", text: "取消订单不可再继续流转，如涉及已付款请走退款处理。" },
}[order.value?.status] || { title: "等待处理", text: "按当前状态推进订单即可。" }));

const groupedMedia = computed(() => {
  const groups = {};
  for (const m of media.value) {
    (groups[m.node] ||= { node: m.node, items: [], type: "primary" }).items.push(m);
  }
  return Object.values(groups);
});
const photoList = (items) => items.filter((m) => m.media_type === "photo").map((m) => mediaUrl(m.url));

async function load() {
  loading.value = true;
  try {
    const d = await getOrderDetail(orderNo);
    order.value = d;
    media.value = d.media || [];
    notes.value = d.notes || "";
  } finally { loading.value = false; }
}

async function doConfirm() {
  if (!(await confirmAction("确认接下这笔订单？确认后订单会进入待服务状态。", "确认订单"))) return;
  await confirmOrder(orderNo);
  refresh("已确认");
}
async function doTransition(target) {
  if (target === "已完成" && !canComplete.value) {
    return ElMessage.warning(`还有 ¥${fmtMoney(outstandingAmount.value)} 未结清，先确认收款再完成订单`);
  }
  if (!(await confirmAction(transitionMessage(target), `流转至${target}`))) return;
  await transitionOrder(orderNo, { target });
  refresh(`已流转至「${target}」`);
}
async function onUpload(file) {
  if (!file) return ElMessage.warning("请选择要上传的影像文件");
  await uploadMedia(orderNo, uploadNode.value, file);
  ElMessage.success("影像已上传，客户可见");
  await load();
}
function openSettle() {
  settleAmount.value = Number(outstandingAmount.value.toFixed(2));
  settleVisible.value = true;
}
async function doSettle() {
  if (!settleAmount.value || settleAmount.value <= 0) {
    return ElMessage.warning("请填写大于 0 的收款金额");
  }
  if (settleAmount.value > outstandingAmount.value + 0.0001) {
    return ElMessage.warning("收款金额不能超过当前待收金额");
  }
  if (!(await confirmAction(`确认已实际收到 ¥${fmtMoney(settleAmount.value)}？`, "确认收款"))) return;
  await settleOrder(orderNo, settleAmount.value);
  settleVisible.value = false;
  refresh("已结清收款");
}
async function doReschedule() {
  if (!rescheduleTime.value) return ElMessage.warning("请选择新的服务时间");
  if (!(await confirmAction("确认修改本单期望服务时间？免费改期只有 1 次。", "确认改期"))) return;
  await reschedule(orderNo, rescheduleTime.value);
  rescheduleVisible.value = false;
  refresh("已改期");
}
async function doCancel() {
  const reason = cancelReason.value.trim();
  if (reason.length < 2) return ElMessage.warning("请填写至少 2 个字的取消原因");
  if (!(await confirmAction("确认取消订单？取消后不可继续流转。", "取消订单", "warning"))) return;
  await transitionOrder(orderNo, { target: "已取消", reason });
  cancelVisible.value = false;
  refresh("已取消");
}
function openRefund() {
  refundStatus.value = order.value?.refund_status === "退款失败" ? "退款失败" : "已退款";
  refundNote.value = "";
  refundVisible.value = true;
}
async function doMarkRefund() {
  if (refundStatus.value === "退款失败" && !refundNote.value.trim()) {
    return ElMessage.warning("退款失败时请填写失败原因，方便后续追踪");
  }
  if (!(await confirmAction(`确认将退款状态标记为「${refundStatus.value}」？`, "保存退款结果"))) return;
  await markRefund(orderNo, refundStatus.value, refundNote.value);
  refundVisible.value = false;
  refresh("退款结果已保存");
}
async function saveNotesNow() {
  await saveNotes(orderNo, notes.value);
  notesSaved.value = true;
  setTimeout(() => (notesSaved.value = false), 2000);
}
function refresh(msg) { ElMessage.success(msg); load(); }
function transitionMessage(target) {
  return ({
    接宠中: "确认已经准备出发接宠？客户会看到订单进入接宠中。",
    服务中: "确认宠物已到达门店并开始服务？",
    待交付: "确认服务已完成并进入待交付？建议先上传火化完成影像。",
    已完成: "确认已经完成交付？完成后订单主流程结束。",
  }[target] || `确认流转至「${target}」？`);
}
async function confirmAction(message, title, type = "info") {
  try {
    await ElMessageBox.confirm(message, title, {
      type,
      confirmButtonText: "确认",
      cancelButtonText: "取消",
    });
    return true;
  } catch {
    return false;
  }
}

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
  justify-content: flex-start;
}
.full :deep(.el-icon) { margin-right: var(--px-sp-1); }
.full.last { margin-bottom: 0; }
.upload { margin-bottom: var(--px-sp-2); }
.operation-guide {
  margin-bottom: var(--px-sp-3);
  padding: var(--px-sp-3);
  border: 1px solid rgba(91, 140, 133, 0.22);
  border-radius: var(--px-radius-md);
  background: var(--px-primary-softer);
}
.operation-guide strong {
  display: block;
  color: var(--px-text-1);
  font-size: var(--px-fs-sm);
}
.operation-guide p {
  margin: 4px 0 0;
  color: var(--px-text-2);
  font-size: var(--px-fs-xs);
  line-height: 1.6;
}
.operation-guide.is-terminal {
  border-color: var(--px-border);
  background: var(--px-bg-warm);
}
.operation-warning,
.dialog-hint {
  margin: var(--px-sp-2) 0 0;
  color: var(--px-warning);
  font-size: var(--px-fs-xs);
  line-height: 1.5;
}
.dialog-hint {
  color: var(--px-text-3);
}
.secondary {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--px-sp-1);
  margin-top: var(--px-sp-2);
}
.secondary :deep(.el-button) {
  margin-left: 0;
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
.refund-status {
  display: flex;
  margin: var(--px-sp-3) 0;
}
.w-full { width: 100%; }

@media (max-width: 1366px) {
  /* 窄屏时操作区上移：员工进来是为了推进订单，不是看资料 */
  .body { flex-direction: column-reverse; }
  .side-col { width: 100%; position: static; }
}
</style>
