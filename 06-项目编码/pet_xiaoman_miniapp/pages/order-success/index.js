const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: {
    orderNo: "",
    payText: "",
  },
  onLoad(options) {
    this.setData({
      orderNo: options.order_no || "",
      payText: options.pay_text || "到店付款",
    });
  },
  copyOrderNo() {
    const { orderNo } = this.data;
    if (!orderNo) return;
    wx.setClipboardData({
      data: orderNo,
      success: () => wx.showToast({ title: "已复制", icon: "success" }),
      fail: () => wx.showToast({ title: "复制失败，请手动记录", icon: "none" }),
    });
  },
  viewOrder() {
    if (!this.data.orderNo) return;
    wx.navigateTo({ url: `/pages/order-detail/index?order_no=${this.data.orderNo}` });
  },
  backHome() {
    go("/pages/index/index");
  },
}));
