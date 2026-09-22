// C007 纪念品展示（对齐画布 2:367，纪念品一级 tab 页）
//
// 层级：一级 tab 页 → 自绘衬线页头（无返回）、底部自定义胶囊 tabBar。
// 卡片只展示「图片 / 名称 / 价格」，点卡片进入详情页继续了解与下单。
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

// 画布 2:367 的静态商品卡。数据顺序按 flex 两列重排：左1/右1、左2/右2、左3/右3。
const STATIC_PRODUCTS = [
  { id: 1, name: "爪印银牌", priceText: "168", image: "/assets/ardot/images/2_386-20260922_083240971.png" },
  { id: 4, name: "骨灰瓷瓶", priceText: "388", image: "/assets/ardot/images/2_404-20260922_083240976.png" },
  { id: 2, name: "毛发水晶", priceText: "298", image: "/assets/ardot/images/2_392-20260922_083240975.png" },
  { id: 5, name: "姓名项链", priceText: "228", image: "/assets/ardot/images/2_410-20260922_083240976.png" },
  { id: 3, name: "纪念相册", priceText: "128", image: "/assets/ardot/images/2_398-20260922_083240976.png" },
  { id: 6, name: "永生花盒", priceText: "258", image: "/assets/ardot/images/2_416-20260922_083240976.png" },
];

function syncTabBar(page) {
  if (typeof page.getTabBar !== "function") return;
  const tabBar = page.getTabBar();
  if (tabBar && typeof tabBar.setSelected === "function") {
    tabBar.setSelected("/pages/products/products");
  }
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    all: STATIC_PRODUCTS,
    products: STATIC_PRODUCTS,
    keyword: "",
    searchIcon: "/assets/ardot/icons/2_378-20260922_083300133.png",
  },

  onShow() {
    syncTabBar(this);
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

  goDetail(e) {
    go("/pages/product-detail/detail?id=" + e.currentTarget.dataset.id);
  },

  // 空态出口：纪念品由门店自行上架，没有可买的东西时给人工出口而不是死胡同
  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },
}));
