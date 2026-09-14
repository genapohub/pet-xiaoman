// C002/C003 价格表（全量单项价公开，PRD §5.2.1 差异化核心）
const { get } = require("../../utils/request");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: {
    tabs: ["套餐", "单项", "加购"],
    active: "套餐",
    groups: {},
    current: [],   // 当前分类的列表；WXML 不支持 (expr).length，长度判断必须在 JS 里算好
    loading: true,
  },

  onLoad() {
    get("/api/c/service-items").then((rows) => {
      const groups = {};
      for (const r of rows) {
        if (!groups[r.type]) groups[r.type] = [];
        groups[r.type].push(r);
      }
      this.setData({
        groups,
        current: groups[this.data.active] || [],
        loading: false,
      });
    }).catch(() => this.setData({ loading: false }));
  },

  switchTab(e) {
    const active = e.currentTarget.dataset.tab;
    this.setData({ active, current: this.data.groups[active] || [] });
  },

  goCreate(e) {
    // order-create 是 tabBar 页且 switchTab 不支持 query：
    // go() 会自动改用 switchTab 并把 pkg_id 暂存，由预约页 onShow 取用
    go(`/pages/order-create/index?pkg_id=${e.currentTarget.dataset.id}`);
  },
  goDetail(e) {
    go(`/pages/service-detail/detail?id=${e.currentTarget.dataset.id}`);
  },
}));
