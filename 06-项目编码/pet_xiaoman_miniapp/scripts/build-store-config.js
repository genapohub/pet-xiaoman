#!/usr/bin/env node
/**
 * 生成单门店独立小程序发布配置。
 *
 * 用法：
 *   STORE_SLUG=chongxiaoman \
 *   MINIAPP_APPID=wx667ddd8e0d8dd8fb \
 *   MINIAPP_NAME="宠小满·示例门店" \
 *   PROJECT_NAME=pet_xiaoman_chongxiaoman \
 *   node scripts/build-store-config.js
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const STORE_CONFIG_PATH = path.join(ROOT, "config/store.js");
const PROJECT_CONFIG_PATH = path.join(ROOT, "project.config.json");

function env(name, fallback = "") {
  return String(process.env[name] || fallback).trim();
}

const storeSlug = env("STORE_SLUG", env("DEFAULT_STORE_SLUG"));
const miniappAppid = env("MINIAPP_APPID");
const miniappName = env("MINIAPP_NAME");
const projectName = env("PROJECT_NAME", `pet_xiaoman_${storeSlug || "miniapp"}`);
const mapProvider = env("MAP_PROVIDER", "wechat");
const mapPickerEnabled = env("MAP_PICKER_ENABLED", "true").toLowerCase() !== "false";
const mapKey = env("MAP_KEY");
const subscribeTemplateIds = env("SUBSCRIBE_TEMPLATE_IDS")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

function assert(cond, message) {
  if (!cond) {
    console.error(`配置生成失败：${message}`);
    process.exit(1);
  }
}

assert(/^[A-Za-z0-9_-]{2,50}$/.test(storeSlug), "STORE_SLUG 只能包含字母、数字、下划线与短横线，2-50 位");
assert(/^wx[A-Za-z0-9]{8,62}$/.test(miniappAppid), "MINIAPP_APPID 需以 wx 开头，仅包含字母数字");
assert(miniappName && miniappName.length <= 50, "MINIAPP_NAME 必填且不超过 50 字");
assert(projectName && projectName.length <= 64, "PROJECT_NAME 必填且不超过 64 字");
assert(["wechat", "tencent", "manual"].includes(mapProvider), "MAP_PROVIDER 仅支持 wechat / tencent / manual");
subscribeTemplateIds.forEach((id) => {
  assert(/^[A-Za-z0-9_-]{10,100}$/.test(id), `订阅模板 ID 格式不正确：${id}`);
});

const storeConfig = `// 每个门店独立小程序发布前写入的默认入口配置。
// 同一套源码可以按门店生成不同 AppID 包；微信搜索进入时没有 scene/query，就用这里的 slug。
module.exports = {
  DEFAULT_STORE_SLUG: ${JSON.stringify(storeSlug)},
  MINIAPP_NAME: ${JSON.stringify(miniappName)},
  MINIAPP_APPID: ${JSON.stringify(miniappAppid)},
  SUBSCRIBE_TEMPLATE_IDS: ${JSON.stringify(subscribeTemplateIds)},
  MAP_PROVIDER: ${JSON.stringify(mapProvider)},
  MAP_PICKER_ENABLED: ${JSON.stringify(mapPickerEnabled)},
  MAP_KEY: ${JSON.stringify(mapKey)},
};
`;

const projectConfig = JSON.parse(fs.readFileSync(PROJECT_CONFIG_PATH, "utf8"));
projectConfig.appid = miniappAppid;
projectConfig.projectname = projectName;

fs.writeFileSync(STORE_CONFIG_PATH, storeConfig, "utf8");
fs.writeFileSync(PROJECT_CONFIG_PATH, `${JSON.stringify(projectConfig, null, 2)}\n`, "utf8");

console.log(`已生成门店发布配置：${miniappName}`);
console.log(`- 默认门店 slug：${storeSlug}`);
console.log(`- 小程序 AppID：${miniappAppid}`);
console.log(`- 项目名：${projectName}`);
console.log(`- 订阅模板数：${subscribeTemplateIds.length}`);
console.log(`- 地图 provider：${mapProvider}（位置选择${mapPickerEnabled ? "启用" : "关闭"}）`);
