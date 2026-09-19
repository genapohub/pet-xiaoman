// C005 我的订单（对齐画布 2:264，我的 · 二级页）
//
// 层级：二级页 → 自绘页头（返回 + 衬线标题）、无 tabBar、底部「去预约」固定条。
// 筛选在客户端做：接口一次返回全部订单（按创建时间倒序），切换 Tab 不重新请求，
// 弱网下切筛选不会闪白。
const app = getApp();
const { get } = require("../../utils/request");
const { decorateOrder } = require("../../utils/format");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

// 进行中 = 未到终态（PRD §6.4 状态机）
const ONGOING = ["待确认", "已预约", "接宠中", "服务中", "待交付"];

const TABS = [
  { key: "进行中", empty: "暂无进行中的订单", hint: "预约服务后，订单会显示在这里" },
  { key: "已完成", empty: "还没有已完成的订单", hint: "服务完成后可以在这里回看影像记录" },
  { key: "全部", empty: "暂无订单", hint: "预约服务后，订单会显示在这里" },
];

// 状态 → 标签色（善终场景：进行中用松绿、待办用陶土、终态用中性；不用亮绿/促销红）
const STATUS_CLASS = {
  待确认: "tag--clay",
  已预约: "tag--primary",
  接宠中: "tag--primary",
  服务中: "tag--primary",
  待交付: "tag--clay",
  已完成: "tag--muted",
  已取消: "tag--muted",
};

/**
 * 订单卡装饰：把时间文案与配色在 JS 里算好。
 * WXML 绑定不支持函数调用/三元链，且「文案随状态变化」是业务规则，不该塞进模板。
 */
function decorate(list) {
  return (list || []).map((o) => {
    const d = decorateOrder(o);
    const short = d.expect_text ? d.expect_text.slice(5) : "";   // "2026-09-15 09:00" → "09-15 09:00"
    let timeText;
    if (o.status === "已完成") timeText = `已完成于 ${short}`;
    else if (o.status === "已取消") timeText = "已取消";
    else if (["接宠中", "服务中", "待交付"].includes(o.status)) timeText = `服务进行中 · 预计 ${short} 完成`;
    else timeText = `期望服务 ${short}`;
    return Object.assign(d, {
      timeText,
      // 终态订单金额降为中性灰，避免已完成订单还在抢视觉
      isDone: o.status === "已完成" || o.status === "已取消",
      tagClass: STATUS_CLASS[o.status] || "tag--muted",
    });
  });
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    tabs: TABS,
    active: "进行中",
    all: [],
    shown: [],
    emptyTitle: TABS[0].empty,
    emptyHint: TABS[0].hint,
    loading: true,
  },

  onShow() { this.load(); },

  load() {
    const uid = app.getCustomerId();
    if (!uid) {
      this.setData({ loading: false, all: [], shown: [] });
      return;
    }
    get("/api/c/orders", { user_id: uid })
      .then((rows) => {
        this.setData({ all: decorate(rows), loading: false });
        this.applyFilter(this.data.active);
      })
      .catch(() => this.setData({ loading: false }));
  },

  applyFilter(key) {
    const tab = TABS.find((t) => t.key === key) || TABS[0];
    const all = this.data.all;
    let shown = all;
    if (key === "进行中") shown = all.filter((o) => ONGOING.includes(o.status));
    else if (key === "已完成") shown = all.filter((o) => o.status === "已完成");
    this.setData({ shown, emptyTitle: tab.empty, emptyHint: tab.hint });
  },

  switchTab(e) {
    const active = e.currentTarget.dataset.tab;
    this.setData({ active });
    this.applyFilter(active);
  },

  goBack() { navbar.back(); },
  goDetail(e) { go(`/pages/order-detail/index?order_no=${e.currentTarget.dataset.no}`); },
  goCreate() { go("/pages/order-create/index"); },
}));
