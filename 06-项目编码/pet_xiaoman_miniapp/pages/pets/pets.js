// C009 宠物档案（含服务历史）
const app = getApp();
const { get } = require("../../utils/request");
const { fmtDate } = require("../../utils/format");
const { go } = require("../../utils/nav");

Page({
  data: { pets: [], loading: true },

  onShow() {
    const uid = app.getCustomerId();
    if (!uid) return this.setData({ loading: false });
    get("/api/c/pets", { user_id: uid })
      .then((pets) => {
        // 服务历史日期在 JS 里格式化好；WXML 绑定不支持 .slice() 这类函数调用
        const list = (pets || []).map((p) => Object.assign({}, p, {
          orders: (p.orders || []).map((o) =>
            Object.assign({}, o, { date_text: fmtDate(o.created_at) })),
        }));
        this.setData({ pets: list, loading: false });
      })
      .catch(() => this.setData({ loading: false }));
  },

  goOrder(e) { go(`/pages/order-detail/index?order_no=${e.currentTarget.dataset.no}`); },
});
