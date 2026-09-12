// C004 预约下单（PRD §5.2.1）：套餐预选 + 表单 + 提交（支付开关关闭=到店付提示）
const { get, post } = require("../../utils/request");
const { takeParams } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: {
    packages: [], pkgIndex: 0, currentPackage: null,
    form: { pet_name: "", species: "犬", weight: "", address: "" },
    expectTime: "", submitting: false,
  },
  onLoad(options) {
    this._pendingPkgId = options && options.pkg_id ? +options.pkg_id : 0;
    get("/api/c/service-items").then((rows) => {
      const packages = rows.filter((r) => r.type === "套餐");
      this.setData({ packages, currentPackage: packages[0] || null });
      this._applyPkgId(this._pendingPkgId);
    });
  },
  // 本页是 tabBar 页：从 C002 价格表跳进来只能走 switchTab（不支持 query），
  // 所以 pkg_id 经 utils/nav 的中转参数取；已存在的 tabBar 页不会再触发 onLoad，必须在 onShow 取
  onShow() {
    const params = takeParams();
    if (params && params.pkg_id) {
      this._pendingPkgId = +params.pkg_id;
      this._applyPkgId(this._pendingPkgId);
    }
  },
  _applyPkgId(id) {
    if (!id || !this.data.packages.length) return;
    const idx = this.data.packages.findIndex((p) => p.id === id);
    if (idx >= 0) this.setData({ pkgIndex: idx, currentPackage: this.data.packages[idx] });
  },
  onPkgChange(e) {
    const pkgIndex = +e.detail.value;
    this.setData({ pkgIndex, currentPackage: this.data.packages[pkgIndex] || null });
  },
  onInput(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }); },
  onSpecies(e) { this.setData({ "form.species": this.data.form.species === "犬" ? "猫" : "犬" }); },
  onTime(e) { this.setData({ expectTime: e.detail.value }); },
  onAddress(e) { this.setData({ "form.address": e.detail.value }); },
  submit() {
    const { form, packages, pkgIndex, expectTime, submitting } = this.data;
    if (submitting) return;
    if (!form.pet_name) return wx.showToast({ title: "请填写宠物名字", icon: "none" });
    if (!expectTime) return wx.showToast({ title: "请选择期望服务时间", icon: "none" });
    const app = getApp();
    this.setData({ submitting: true });
    app.ensureLogin().then(() => post("/api/c/orders", {
        pet_name: form.pet_name,
        species: form.species,
        weight: form.weight ? +form.weight : null,
        pkg_id: packages[pkgIndex].id,
        expect_time: expectTime,
        address: form.address || null,
      })).then((data) => {
      wx.showToast({ title: "已提交", icon: "success" });
      setTimeout(() => wx.navigateTo({
        url: `/pages/cashier/index?order_no=${data.order_no}&amount=${data.total_amount || 0}`,
      }), 800);
    }).catch((err) => {
      wx.showToast({ title: err.detail || "提交失败", icon: "none" });
    }).finally(() => this.setData({ submitting: false }));
  },
}));
