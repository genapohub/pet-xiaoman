// C006 订单进度时间线（PRD：状态+节点影像，信任的载体）
const { get } = require("../../utils/request");
const { decorateOrder } = require("../../utils/format");
const { absUrl } = require("../../utils/url");

Page({
  data: { order: null, media: [], loading: true },
  onLoad(options) { this.orderNo = options.order_no; },
  onShow() { this.load(); },
  load() {
    Promise.all([
      get(`/api/c/orders/${this.orderNo}`),
      get(`/api/c/orders/${this.orderNo}/media`).catch(() => []),
    ]).then(([order, media]) => {
      const nodes = ["待确认", "已预约", "接宠中", "服务中", "待交付", "已完成"];
      const timeline = nodes.map((name, i) => {
        const idx = nodes.indexOf(order.status);
        // 后端媒体 URL 是相对路径（/uploads/...），小程序 <image>/<video>/previewImage
        // 无法解析，必须拼成绝对地址；photoUrls 同样要绝对地址。
        const nodeMedia = media
          .filter((m) => m.node === name)
          .map((m) => Object.assign({}, m, { url: absUrl(m.url) }));
        return {
          name,
          done: i <= idx,
          current: i === idx,
          media: nodeMedia,
          photoUrls: nodeMedia.filter((m) => m.media_type === "photo").map((m) => m.url),
        };
      }).filter((n) => n.done || n.current);
      this.setData({ order: decorateOrder(order), media, timeline, loading: false });
    }).catch(() => this.setData({ loading: false }));
  },
  preview(e) {
    const { urls, current } = e.currentTarget.dataset;
    wx.previewImage({ urls, current });
  },
  callShop() { wx.makePhoneCall({ phoneNumber: wx.getStorageSync("shop_phone") || "" }); },
});
