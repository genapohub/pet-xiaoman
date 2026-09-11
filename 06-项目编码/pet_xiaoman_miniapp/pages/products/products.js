// C007 纪念品展示（单件直购：支付开关关闭时提示到店选购）
const { get, post } = require("../../utils/request");
const { absUrl } = require("../../utils/url");

Page({
  data: { products: [], loading: true },
  onShow() {
    get("/api/c/products")
      .then((rows) => this.setData({ products: normalizeProducts(rows), loading: false }))
      .catch(() => this.setData({ loading: false }));
  },
  imageFailed(e) {
    const index = e.currentTarget.dataset.index;
    if (index === undefined) return;
    this.setData({ [`products[${index}].image`]: "" });
  },
  buy(e) {
    const app = getApp();
    post(`/api/c/products/${e.currentTarget.dataset.id}/buy`,
      { customer_id: app.getCustomerId(), fulfillment: "到店自取" })
      .then(() => wx.showToast({ title: "已预留，到店取", icon: "success" }))
      .catch((err) => wx.showToast({ title: err.detail || "购买失败", icon: "none" }));
  },
});

function normalizeProducts(payload) {
  const rows = Array.isArray(payload) ? payload : (payload?.items || payload?.list || []);
  return rows.map((p) => {
    const image = p.image || p.cover || (Array.isArray(p.images) ? p.images[0] : "");
    return Object.assign({}, p, { image: absUrl(image) });
  });
}
