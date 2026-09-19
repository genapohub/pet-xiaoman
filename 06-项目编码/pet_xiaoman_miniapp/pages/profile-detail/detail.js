// C-资料编辑 profile-detail（对齐画布 58:494，我的 · 二级页）
//
// 数据落点：`PUT /api/c/auth/me`（本次联调补的接口，只开放 nickname / phone）。
// 画布「其他信息」里的「收货地址」**未实现**：纪念品当前是「到店自取」口径，
// Customer 也没有地址字段——等 V2.0 定稿邮寄口径后，再加字段与迁移，不先做个空壳输入框。
const { get, put } = require("../../utils/request");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

Page(brandPage({
  data: {
    nav: navbar.measure(),
    me: null,
    loading: true,
    form: { nickname: "", phone: "" },
    initial: "客",
    submitting: false,
    links: [
      { label: "宠物档案", icon: "/assets/icons/paw.png", url: "/pages/pets/pets" },
      { label: "骨灰寄存查询", icon: "/assets/icons/box.png", url: "/pages/boarding-query/query" },
    ],
  },

  onShow() { this.load(); },
  goBack() { navbar.back(); },

  load() {
    this.setData({ loading: true });
    get("/api/c/auth/me", {}, { silentError: true })
      .then((me) => {
        const nickname = (me && me.nickname) || "";
        this.setData({
          me,
          loading: false,
          form: { nickname, phone: (me && me.phone) || "" },
          initial: (nickname || "客").slice(0, 1),
        });
      })
      .catch(() => this.setData({ loading: false }));
  },

  onInput(e) {
    this.setData({ ["form." + e.currentTarget.dataset.field]: e.detail.value });
  },

  save() {
    const { form, submitting, me } = this.data;
    if (submitting) return;
    if (!me || !me.logged_in) {
      return wx.showToast({ title: "请先登录后再修改资料", icon: "none" });
    }
    if (!String(form.nickname || "").trim()) {
      return wx.showToast({ title: "昵称不能为空", icon: "none" });
    }
    this.setData({ submitting: true });
    // silentError：request 的错误 toast 读的是 res.data.detail，而 reject 出来的是整个响应，
    // 这里自己取一次 detail，避免「保存失败」把后端的「请输入 11 位手机号」盖掉。
    put("/api/c/auth/me", { nickname: form.nickname, phone: form.phone }, { silentError: true })
      .then(() => {
        wx.showToast({ title: "已保存", icon: "success" });
        this.load();
      })
      .catch((err) => {
        const detail = err && err.data && err.data.detail;
        wx.showToast({ title: detail || "保存失败，请稍后重试", icon: "none" });
      })
      .finally(() => this.setData({ submitting: false }));
  },

  goLink(e) { go(e.currentTarget.dataset.url); },
}));
