// 每个门店独立小程序发布前写入的默认入口配置。
// 同一套源码可以按门店生成不同 AppID 包；微信搜索进入时没有 scene/query，就用这里的 slug。
module.exports = {
  DEFAULT_STORE_SLUG: "chongxiaoman",
  MINIAPP_NAME: "宠小满·示例门店",
  MINIAPP_APPID: "wx667ddd8e0d8dd8fb",
  SUBSCRIBE_TEMPLATE_IDS: [],
  MAP_PROVIDER: "wechat",
  MAP_PICKER_ENABLED: true,
  MAP_KEY: "",
};
