// C006 订单进度时间线（对齐画布 2:312，我的 · 二级页）
//
// 定位：这是全站信任的载体——家属唯一能「看见过程」的地方，故：
//   · 顶部渐变 Hero 给一句情绪定调（不是冷冰冰的订单号大字）
//   · 时间线只显示已发生 / 当前节点（未来节点不列，避免「还差 4 步」的压迫感）
//   · 节点影像走 media 接口，强制作流转证据，与 B 端状态机同源
const { get, post } = require("../../utils/request");
const { decorateOrder } = require("../../utils/format");
const { absUrl } = require("../../utils/url");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");
const { SUBSCRIBE_TEMPLATE_IDS } = require("../../config/store");

// 状态机节点顺序（与 app/services/order_state.py TRANSITIONS 对齐）
const NODES = ["待确认", "已预约", "接宠中", "服务中", "待交付", "已完成"];

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return y + "-" + m + "-" + d;
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    order: null,
    heroSub: "",
    timeline: [],
    loading: true,
    canCustomerEdit: false,
    rescheduleLeft: 0,
    rescheduleStartDate: formatDate(new Date(Date.now() + 24 * 60 * 60 * 1000)),
  },

  onLoad(options) { this.orderNo = options.order_no; },
  onShow() { this.load(); },

  goBack() { navbar.back(); },

  load() {
    Promise.all([
      get(`/api/c/orders/${this.orderNo}`),
      get(`/api/c/orders/${this.orderNo}/media`).catch(() => []),
    ]).then(([order, media]) => {
      const idx = NODES.indexOf(order.status);
      const timeline = NODES.map((name, i) => {
        // 后端媒体 URL 是相对路径（/uploads/...），小程序 <image>/<video>/previewImage
        // 无法解析，必须拼成绝对地址；photoUrls 同样要绝对地址。
        const nodeMedia = (media || [])
          .filter((m) => m.node === name)
          .map((m) => Object.assign({}, m, { url: absUrl(m.url) }));
        return {
          name,
          done: i <= idx,
          current: i === idx,
          media: nodeMedia,
          photoUrls: nodeMedia.filter((m) => m.media_type === "photo").map((m) => m.url),
          hasMedia: nodeMedia.length > 0,
        };
      }).filter((n) => n.done);   // 未来节点不列，只显示已发生/当前
      const decorated = decorateOrder(order);
      const canCustomerEdit = ["待确认", "已预约"].includes(decorated.status);
      this.setData({
        order: decorated,
        heroSub: [order.order_no, order.pkg_name].filter(Boolean).join(" · "),
        timeline,
        canCustomerEdit,
        rescheduleLeft: order.reschedule_quota_left || 0,
        loading: false,
      });
    }).catch(() => this.setData({ loading: false }));
  },

  preview(e) {
    const { urls, current } = e.currentTarget.dataset;
    wx.previewImage({ urls, current });
  },

  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },

  subscribeProgress() {
    const fallback = () => {
      if (!SUBSCRIBE_TEMPLATE_IDS || !SUBSCRIBE_TEMPLATE_IDS.length) {
        wx.showToast({ title: "订阅消息待配置，先以订单时间线为准", icon: "none" });
        return;
      }
      wx.requestSubscribeMessage({
        tmplIds: SUBSCRIBE_TEMPLATE_IDS,
        success: () => wx.showToast({ title: "已记录通知授权", icon: "success" }),
        fail: () => wx.showToast({ title: "未开启通知，可随时看时间线", icon: "none" }),
      });
    };
    get("/api/c/subscribe/config", {}, { silentError: true })
      .then((cfg) => {
        const ids = (cfg && cfg.template_ids && cfg.template_ids.length)
          ? cfg.template_ids : SUBSCRIBE_TEMPLATE_IDS;
        if (!ids || !ids.length) {
          wx.showToast({ title: "订阅消息待配置，先以订单时间线为准", icon: "none" });
          return;
        }
        wx.requestSubscribeMessage({
          tmplIds: ids,
          success: () => wx.showToast({ title: "已记录通知授权", icon: "success" }),
          fail: () => wx.showToast({ title: "未开启通知，可随时看时间线", icon: "none" }),
        });
      })
      .catch(fallback);
  },

  cancelOrder() {
    if (!this.data.canCustomerEdit) return;
    wx.showModal({
      title: "取消预约",
      content: "待确认或已预约的订单可以取消。若已支付，门店会按规则处理退款。",
      confirmText: "确认取消",
      confirmColor: "#D54941",
      success: (res) => {
        if (!res.confirm) return;
        post(`/api/c/orders/${this.orderNo}/cancel`, { reason: "客户在小程序取消" })
          .then((data) => {
            wx.showToast({ title: (data && data.message) || "已取消", icon: "none" });
            this.load();
          })
          .catch((err) => wx.showToast({ title: (err && err.detail) || "取消失败", icon: "none" }));
      },
    });
  },

  onRescheduleDate(e) {
    if (!this.data.canCustomerEdit) return;
    if ((this.data.rescheduleLeft || 0) <= 0) {
      wx.showToast({ title: "免费改期次数已用完，请联系门店", icon: "none" });
      return;
    }
    const pickedDate = e.detail && e.detail.value;
    if (!pickedDate) return;
    wx.showModal({
      title: "确认改期",
      content: `将服务时间改到 ${pickedDate} 10:00，确认提交吗？`,
      confirmText: "确认改期",
      success: (res) => {
        if (!res.confirm) return;
        const nextTime = new Date(`${pickedDate}T10:00:00`);
        post(`/api/c/orders/${this.orderNo}/reschedule`, { expect_time: nextTime.toISOString() })
          .then(() => {
            wx.showToast({ title: "改期已提交", icon: "success" });
            this.load();
          })
          .catch((err) => wx.showToast({ title: (err && err.detail) || "改期失败", icon: "none" }));
      },
    });
  },
}));
