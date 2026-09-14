// 品牌视觉默认值（PRD §5.6.3 视觉总纲；PRD §12.3 白标）。
//
// 这里是「多租户平台默认」而不是「某家门店的品牌」：
// 真实店名 / 标语 / logo / 主色一律由后端 store_profile 在运行时覆盖（utils/brand.js）。
// 所以本文件不得写入任何一家门店的名字或 slogan ——
// 否则新门店在还没拉到资料的那一帧，会顶着别家的品牌出现在顾客眼前。
module.exports = {
  colorPrimary: "#5B8C85",      // 平台默认主色（暖松绿）
  colorPrimaryPressed: "#4A756E",
  colorPrimaryDisabled: "#B9CFCB",
  colorAccent: "#D9A468",       // 暖陶土（告别/纪念场景点缀）
  colorSuccess: "#2BA471",
  colorWarning: "#E37318",
  colorError: "#D54941",
  shopName: "宠物善终服务",      // 中性兜底：拉到门店资料后必被覆盖
  slogan: "",                    // 空 = 不展示（由门店资料提供，不硬编码）
  contactPhone: "",
  contactAddress: "",
  businessHours: "",
};
