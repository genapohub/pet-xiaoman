// C004 预约下单（对齐画布 2:219，服务 · 二级页）
//
// 结构（画布）：已选套餐 → 附加服务（多选）→ 宠物信息 → 服务安排 → 底部费用条（合计 + 提交）。
// 三个关键口径：
//   1. **附加服务是设计新增的能力**——后端 `POST /api/c/orders` 本来就收 `addon_ids`，
//      但旧版页面没有入口，等于该能力没被用上；这里按画布补出多选，并计入合计。
//   2. **合计 = 套餐 + 已勾选加购**，价格只在提交时由后端按版本号锁定（前端算的只是展示值）。
//   3. **手机号不做输入框**：订单表无联系方式字段，而通知号码可从客户资料取（`/api/c/auth/me`），
//      故此处只读展示并引导去「资料编辑」改号——不新增库表字段，也不做假输入框。
const { get, post } = require("../../utils/request");
const { takeParams, go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");
const storeConfig = require("../../config/store");

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function maskPhone(phone) {
  const raw = String(phone || "").trim();
  if (!raw) return "未绑定通知手机号 · 去资料编辑修改";
  if (raw.length < 7) return `${raw} · 去资料编辑修改`;
  return `通知手机号 ${raw.slice(0, 3)}****${raw.slice(-4)} · 去资料编辑修改`;
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    packages: [], pkgIndex: 0, currentPackage: null,
    addons: [], addonIds: [], addonSelectedCount: 0,
    totalText: "0",
    form: { pet_name: "", species: "犬", weight: "", address: "" },
    speciesOptions: [
      { label: "狗狗", value: "犬" },
      { label: "猫猫", value: "猫" },
      { label: "其他", value: "其他" },
    ],
    expectTime: "",
    minServiceDate: formatDate(new Date()),
    notifPhone: "",
    notifPhoneText: "未绑定通知手机号 · 去资料编辑修改",
    submitting: false,
    mapPickerEnabled: storeConfig.MAP_PICKER_ENABLED !== false,
    mapProviderLabel: storeConfig.MAP_PROVIDER === "manual" ? "手动填写" : "微信位置选择",
  },

  onLoad(options) {
    this._pendingPkgId = options && options.pkg_id ? +options.pkg_id : 0;
    this.loadItems();
    this.loadPhone();
  },

  // 本页是普通子页（已由 tabBar 页降级）：pkg_id 走 navigateTo 的 query，
  // onShow 保留用于兼容 switchTab 时代的中转参数。
  onShow() {
    const params = takeParams();
    if (params && params.pkg_id) {
      this._pendingPkgId = +params.pkg_id;
      this._applyPkgId(this._pendingPkgId);
    }
  },

  goBack() { navbar.back(); },

  loadItems() {
    get("/api/c/service-items").then((rows) => {
      const list = rows || [];
      const packages = list.filter((r) => r.type === "套餐");
      const addons = list.filter((r) => r.type === "加购").map((a) => ({
        id: a.id,
        name: a.name,
        priceText: Number(a.price || 0).toFixed(0),
        price: Number(a.price || 0),
        checked: false,
      }));
      this.setData({ packages, addons, currentPackage: packages[0] || null });
      this._applyPkgId(this._pendingPkgId);
      this._recalc();
    }).catch(() => {});
  },

  // 通知号码：从客户资料读，不在订单里另存一份（避免两处号码不一致）
  loadPhone() {
    const app = getApp();
    if (!app.getCustomerId()) return;
    get("/api/c/auth/me", {}, { silentError: true })
      .then((me) => {
        const phone = (me && me.phone) || "";
        this.setData({ notifPhone: phone, notifPhoneText: maskPhone(phone) });
      })
      .catch(() => {});
  },

  _applyPkgId(id) {
    if (!id || !this.data.packages.length) return;
    const idx = this.data.packages.findIndex((p) => p.id === id);
    if (idx >= 0) {
      this.setData({ pkgIndex: idx, currentPackage: this.data.packages[idx] });
      this._recalc();
    }
  },

  _recalc() {
    const { currentPackage, addons } = this.data;
    const base = currentPackage ? Number(currentPackage.price || 0) : 0;
    const extra = (addons || []).reduce((s, a) => s + (a.checked ? a.price : 0), 0);
    this.setData({ totalText: (base + extra).toFixed(0) });
  },

  onPkgChange(e) {
    const pkgIndex = +e.detail.value;
    this.setData({ pkgIndex, currentPackage: this.data.packages[pkgIndex] || null });
    this._recalc();
  },

  onAddonToggle(e) {
    const id = +e.currentTarget.dataset.id;
    const addons = this.data.addons.map((a) =>
      (a.id === id ? Object.assign({}, a, { checked: !a.checked }) : a));
    this.setData({
      addons,
      addonIds: addons.filter((a) => a.checked).map((a) => a.id),
      addonSelectedCount: addons.filter((a) => a.checked).length,
    });
    this._recalc();
  },

  onInput(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }); },

  onSpeciesSelect(e) {
    const species = e.currentTarget.dataset.species;
    if (species && species !== this.data.form.species) {
      this.setData({ "form.species": species });
    }
  },

  onTime(e) { this.setData({ expectTime: e.detail.value }); },
  chooseAddress() {
    if (storeConfig.MAP_PICKER_ENABLED === false || storeConfig.MAP_PROVIDER === "manual") {
      wx.showToast({ title: "位置选择未开启，请手动填写接送地址", icon: "none" });
      return;
    }
    wx.chooseLocation({
      success: (res) => {
        const address = [res.address, res.name].filter(Boolean).join(" ");
        this.setData({ "form.address": address });
      },
      fail: () => wx.showToast({ title: "可手动填写接送地址", icon: "none" }),
    });
  },

  goProfile() { go("/pages/profile-detail/detail"); },

  submit() {
    const { form, packages, pkgIndex, expectTime, addonIds, submitting } = this.data;
    if (submitting) return;
    if (!packages.length || !packages[pkgIndex]) {
      return wx.showToast({ title: "暂无可预约套餐，请联系门店", icon: "none" });
    }
    if (!form.pet_name) return wx.showToast({ title: "请填写宠物名字", icon: "none" });
    if (!expectTime) return wx.showToast({ title: "请选择期望服务时间", icon: "none" });
    const app = getApp();
    this.setData({ submitting: true });
    app.ensureLogin().then(() => post("/api/c/orders", {
      pet_name: form.pet_name,
      species: form.species,
      weight: form.weight ? +form.weight : null,
      pkg_id: packages[pkgIndex].id,
      addon_ids: addonIds || [],
      // 后端 expect_time 精确到小时，统一按 10:00 落库（与门店排期口径一致）
      expect_time: `${expectTime}T10:00:00`,
      address: form.address || null,
    })).then((data) => {
      wx.showToast({ title: "已提交", icon: "success" });
      setTimeout(() => wx.navigateTo({
        url: `/pages/cashier/index?order_no=${data.order_no}&amount=${data.total_amount || 0}`,
      }), 800);
    }).catch((err) => {
      wx.showToast({ title: (err && err.detail) || "提交失败", icon: "none" });
    }).finally(() => this.setData({ submitting: false }));
  },
}));
