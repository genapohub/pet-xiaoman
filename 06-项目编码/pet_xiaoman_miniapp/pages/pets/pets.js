// C009 宠物档案（对齐画布 2:474，我的 · 二级页）
//
// 数据边界（重要）：C 端 `/api/c/pets` 只返回 pet_id / name / species / weight / orders。
// 画布档案卡上的「中华田园猫 · 女生 · 7岁」用的是品种/性别/年龄——本接口没有这些字段，
// 属数据中心缺口（要补字段 + 迁移，需人工评审）。故此处 meta 只用真实字段拼（物种 · 体重），
// 绝不虚构品种/年龄：否则每位顾客的档案都会显示同一个假品种。
const app = getApp();
const { get } = require("../../utils/request");
const { fmtDate } = require("../../utils/format");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

const STATUS_CLASS = {
  待确认: "tag--clay",
  已预约: "tag--primary",
  接宠中: "tag--primary",
  服务中: "tag--primary",
  待交付: "tag--clay",
  已完成: "tag--muted",
  已取消: "tag--muted",
};

function decorate(pets) {
  return (pets || []).map((p) => {
    const metaText = [p.species, p.weight ? p.weight + " kg" : ""].filter(Boolean).join(" · ");
    const orders = (p.orders || []).map((o) => Object.assign({}, o, {
      date_text: fmtDate(o.created_at),
      tagClass: STATUS_CLASS[o.status] || "tag--muted",
    }));
    return Object.assign({}, p, {
      initial: (p.name || "宠").slice(0, 1),
      metaText,
      orderCount: orders.length,
      orders,
    });
  });
}

Page(brandPage({
  data: { nav: navbar.measure(), pets: [], loading: true },

  onShow() {
    const uid = app.getCustomerId();
    if (!uid) return this.setData({ loading: false });
    get("/api/c/pets", { user_id: uid })
      .then((pets) => this.setData({ pets: decorate(pets), loading: false }))
      .catch(() => this.setData({ loading: false }));
  },

  goBack() { navbar.back(); },
  goOrder(e) { go(`/pages/order-detail/index?order_no=${e.currentTarget.dataset.no}`); },
  goCreate() { go("/pages/order-create/index"); },

  // 档案不提供手工新建：宠物档案在提交预约时由门店建档（PRD 数据流），
  // 手工建会与订单侧同一个宠物产生两条档案。故「新增」引导到预约。
  addPet() {
    wx.showModal({
      title: "新增档案",
      content: "宠物档案会在您提交预约时自动建立，无需手动添加。现在去预约吗？",
      confirmText: "去预约",
      success: (res) => { if (res.confirm) go("/pages/order-create/index"); },
    });
  },
}));
