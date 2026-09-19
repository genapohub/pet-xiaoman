// C007 纪念品展示（对齐画布 2:367，纪念品一级 tab 页）
//
// 层级：一级 tab 页 → 自绘衬线页头（无返回）、底部原生 tabBar。
// 交易口径（2026-09-19 起）：**纪念清单（购物车）下单** ——
//   卡片点进详情，卡片 CTA 直接加购；结算在 `/pages/cart/index`。
//   旧的单件直购接口（`POST /api/c/products/{id}/buy`）保留给 B 端代客/随单交付，C 端不再使用。
const app = getApp();
const { get, post } = require("../../utils/request");
const { absUrl } = require("../../utils/url");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

function normalizeProducts(payload) {
  const rows = Array.isArray(payload) ? payload : (payload && (payload.items || payload.list)) || [];
  return rows.map((p) => {
    const image = p.image || p.cover || (Array.isArray(p.images) ? p.images[0] : "");
    return Object.assign({}, p, {
      image: absUrl(image),
      priceText: Number(p.price || 0).toFixed(0),
      // 副文案优先用履约/库存说明（「现货 · 到店取」这类时效承诺），没有再用描述
      subText: p.stock_note || p.description || "",
      // 列表卡上把履约能力点明，客户不用进详情就知道能不能寄
      fulText: p.lead_days > 0
        ? (p.ship_enabled ? `定制 ${p.lead_days} 天 · 可邮寄` : `定制 ${p.lead_days} 天 · 到店取`)
        : (p.ship_enabled ? "现货 · 可邮寄" : "现货 · 到店取"),
    });
  });
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    all: [],
    products: [],
    keyword: "",
    loading: true,
    cartCount: 0,
    addingId: 0,
  },

  onShow() {
    this.loadProducts();
    this.loadCartCount();
  },

  loadProducts() {
    get("/api/c/products")
      .then((rows) => {
        const all = normalizeProducts(rows);
        this.setData({ all, loading: false });
        this.applyFilter(this.data.keyword, all);
      })
      .catch(() => this.setData({ loading: false }));
  },

  // 清单角标：只关心件数，不拉整表也能用（弱网下失败就保持旧值，不弹错）
  loadCartCount() {
    const uid = app.getCustomerId();
    if (!uid) return;
    get("/api/c/cart", { user_id: uid }, { silentError: true })
      .then((res) => this.setData({ cartCount: (res && res.count) || 0 }))
      .catch(() => {});
  },

  // 搜索走客户端过滤：单店 sku 量级小，本地过滤比每次请求更跟手
  onSearch(e) {
    const keyword = e.detail.value;
    this.setData({ keyword });
    this.applyFilter(keyword, this.data.all);
  },

  applyFilter(keyword, all) {
    const kw = String(keyword || "").trim();
    const products = kw ? (all || []).filter((p) => (p.name || "").indexOf(kw) >= 0) : (all || []);
    this.setData({ products });
  },

  imageFailed(e) {
    const index = e.currentTarget.dataset.index;
    if (index === undefined) return;
    this.setData({ ["products[" + index + "].image"]: "" });
  },

  goDetail(e) {
    go("/pages/product-detail/detail?id=" + e.currentTarget.dataset.id);
  },

  goCart() { go("/pages/cart/index"); },

  // 卡片内直接加购（catchtap 阻止冒泡到卡片的进详情）
  addToCart(e) {
    const id = Number(e.currentTarget.dataset.id);
    if (this.data.addingId) return;
    this.setData({ addingId: id });
    app.ensureLogin()
      .then(() => post("/api/c/cart", { product_id: id, qty: 1 }))
      .then(() => {
        wx.showToast({ title: "已加入纪念清单", icon: "success" });
        this.loadCartCount();
      })
      .catch((err) => {
        const detail = err && err.data && err.data.detail;
        wx.showToast({ title: detail || "加入失败，请稍后重试", icon: "none" });
      })
      .finally(() => this.setData({ addingId: 0 }));
  },

  // 空态出口：纪念品由门店自行上架，没有可买的东西时给人工出口而不是死胡同
  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },
}));
