// C008 骨灰寄存查询（对齐画布 2:512，我的 · 二级页）
//
// 验证口径：手机号后四位（后端 `/api/c/boardings/query`），命中多条时逐条列出。
// 接口在无匹配时返回 404（不是空数组），故「无记录」走 catch 分支——前端必须区分
// 「查询失败」与「查到了 0 条」两种文案，否则用户会以为是自己填错了。
const { get } = require("../../utils/request");
const { fmtDate } = require("../../utils/format");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

// severity 是后端只读属性：正常 / 临期(≤7天) / 已到期
// 「已到期」用告警红——这是真实需要处理的事，不是促销红（规范允许的唯一红字场景之一）
const SEVERITY_CLASS = {
  正常: "tag--primary",
  临期: "tag--clay",
  已到期: "tag--error",
};

function decorate(rows) {
  return (rows || []).map((r) => Object.assign({}, r, {
    expire_text: fmtDate(r.expire_date),
    severityClass: SEVERITY_CLASS[r.severity] || "tag--muted",
    daysText: r.days_left < 0
      ? `已超期 ${Math.abs(r.days_left)} 天`
      : `剩余 ${r.days_left} 天`,
  }));
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    tail: "",
    result: [],
    searched: false,
    loading: false,
    error: "",
  },

  goBack() { navbar.back(); },

  onInput(e) { this.setData({ tail: e.detail.value }); },

  query() {
    const tail = String(this.data.tail || "").trim();
    if (tail.length !== 4) {
      return wx.showToast({ title: "请输入手机号后四位", icon: "none" });
    }
    this.setData({ loading: true, error: "" });
    get("/api/c/boardings/query", { phone_tail: tail }, { silentError: true })
      .then((rows) => this.setData({ result: decorate(rows), searched: true, loading: false }))
      .catch((err) => this.setData({
        result: [],
        searched: true,
        loading: false,
        // 后端的 404 文案是「未找到匹配的寄存记录」，直接透传，不自己编
        error: (err && err.detail) || "未找到匹配的寄存记录",
      }));
  },

  // 续期入口：C 端没有自助续期接口（`POST /api/b/boardings/{id}/renew` 是门店操作），
  // 故引导到门店电话，而不是做一个点了没反应的按钮。
  renew() {
    wx.showModal({
      title: "续期寄存",
      content: "续期需要与门店确认档期与费用，现在拨打门店电话吗？",
      confirmText: "拨打",
      success: (res) => { if (res.confirm) this.callShop(); },
    });
  },

  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },
}));
