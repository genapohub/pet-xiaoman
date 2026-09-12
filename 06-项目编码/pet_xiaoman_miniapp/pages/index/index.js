// C001 品牌首页（PRD §5.6.2 C001）：24h 入口 + 三承诺 + 科普入口
const theme = require("../../config/theme");
const { go } = require("../../utils/nav");
// 多租户换肤：brandPage 在 onLoad/onShow 注入 brandStyle（整套主色系）+ theme
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: {
    theme,
    promises: [
      { icon: "shield", text: "明码标价" },
      { icon: "paw", text: "单独火化" },
      { icon: "clock", text: "24小时可约" },
    ],
  },
  // order-create 是 tabBar 页：必须走 go()（内部用 switchTab），
  // 直接 wx.navigateTo 打开 tabBar 页会静默失败 → 表现为「点立即预约没反应」
  goCreate() { go("/pages/order-create/index"); },
  goPrices() { go("/pages/prices/prices"); },
  callShop() { wx.makePhoneCall({ phoneNumber: wx.getStorageSync("shop_phone") || "" }); }, // 门店电话待接入
}));
