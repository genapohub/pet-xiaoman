// C006 订单进度时间线（PRD：状态+节点影像，信任的载体）
const { get } = require("../../utils/request");
const { decorateOrder } = require("../../utils/format");

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
        const nodeMedia = media.filter((m) => m.node === name);
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
