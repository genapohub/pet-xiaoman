// C005 我的订单
const app = getApp();
const { get } = require("../../utils/request");
const { decorateOrder } = require("../../utils/format");
const { go } = require("../../utils/nav");

Page({
  data: {
    orders: [],
    loading: true,
    tabs: ["进行中", "已完成", "全部"],
    active: "进行中",
    // 状态 → 标签配色（善终场景：进行中用松绿、待办用陶土、终态用中性，不用亮绿/促销红）
    statusClass: {
      待确认: "tag--clay",
      已预约: "tag--primary",
      服务中: "tag--primary",
      待交付: "tag--clay",
      已完成: "tag--muted",
      已取消: "tag--muted",
    },
  },
  onShow() { this.load(); },
  load() {
    const uid = app.getCustomerId();
    if (!uid) return this.setData({ loading: false });
    get("/api/c/orders", { user_id: uid }).then((rows) => {
      // 时间/金额在 JS 里格式化好——WXML 绑定不支持 .slice()/.replace() 这类函数调用
      this.setData({ orders: (rows || []).map(decorateOrder), loading: false });
    }).catch(() => this.setData({ loading: false }));
  },
  switchTab(e) { this.setData({ active: e.currentTarget.dataset.tab }); },
  goDetail(e) { go(`/pages/order-detail/index?order_no=${e.currentTarget.dataset.no}`); },
  goCreate() { go("/pages/order-create/index"); },
});
