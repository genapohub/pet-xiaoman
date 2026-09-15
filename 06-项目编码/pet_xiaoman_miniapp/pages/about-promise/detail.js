// 关于我们的承诺：透明定价 + 单独火化 + 过程可见
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: {
    proofs: [
      { value: "价格", label: "下单前公开" },
      { value: "节点", label: "订单内留痕" },
      { value: "联系", label: "服务前确认" },
    ],
    promises: [
      {
        title: "明码标价",
        text: "服务项目和加购项在下单前公开展示，提交预约时锁定价格版本，后续不因沟通环节临时加价。",
        icon: "/assets/icons/price-primary.png",
      },
      {
        title: "单独火化",
        text: "服务套餐默认按单独火化口径履约，关键节点会进入订单时间线，减少家属对混灰和流程草率的担心。",
        icon: "/assets/icons/shield-primary.png",
      },
      {
        title: "过程可见",
        text: "接宠、服务、交付等节点可沉淀影像记录，家属可以在订单详情查看服务进度。",
        icon: "/assets/icons/camera-primary.png",
      },
    ],
    flows: [
      { step: "01", title: "提交预约", text: "填写宠物信息、服务项目与接宠地址。" },
      { step: "02", title: "电话确认", text: "门店确认时间、价格和服务细节后再履约。" },
      { step: "03", title: "节点跟进", text: "关键服务节点进入订单详情，方便家属回看。" },
    ],
  },
  goPrices() { go("/pages/prices/prices"); },
  goCreate() { go("/pages/order-create/index"); },
  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },
}));
