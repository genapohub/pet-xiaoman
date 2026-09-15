// 个人资料详情：客户自己的登录资料 + 当前门店信息
const { get } = require("../../utils/request");
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: {
    me: null,
    loading: true,
  },
  onShow() {
    this.load();
  },
  load() {
    this.setData({ loading: true });
    get("/api/c/auth/me", {}, { silentError: true })
      .then((me) => this.setData({ me, loading: false }))
      .catch(() => this.setData({ loading: false }));
  },
  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },
}));
