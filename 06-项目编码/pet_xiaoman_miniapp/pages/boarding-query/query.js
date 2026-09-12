// C008 骨灰寄存查询（手机号后四位）
const { get } = require("../../utils/request");
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: { tail: "", result: null, searched: false },
  onInput(e) { this.setData({ tail: e.detail.value }); },
  query() {
    if (this.data.tail.length !== 4) return wx.showToast({ title: "请输入后四位", icon: "none" });
    get("/api/c/boardings/query", { phone_tail: this.data.tail })
      .then((rows) => this.setData({ result: rows, searched: true }))
      .catch((err) => this.setData({ result: [], searched: true,
        error: err.detail || "未找到匹配的寄存记录" }));
  },
}));
