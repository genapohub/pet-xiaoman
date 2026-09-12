// 后端上传资源地址归一化
//
// 后端 media_service / product.images 存的是**相对路径**：`/uploads/{order_no}/{file}`。
// admin 端靠 Vite 的 `/uploads` 代理兜住了；但小程序 `<image>` / `<video>` / `wx.previewImage`
// 没有「基址」概念，相对路径会按小程序包内路径解析 → 真机图片/视频全裂。
// 所以这里在展示前把后端相对路径拼成绝对 URL：baseURL() + 相对路径。
//
// 判定规则：
//  - 空值 / 绝对地址（http(s)://、wxfile://、data:）→ 原样返回
//  - 本地资源 `/assets/...` → 小程序包内加载，不走网络，原样返回
//  - 其他以 `/` 开头的相对路径（即后端 `/uploads/...`）→ 拼 baseURL()

const { baseURL } = require("../config/env");

function absUrl(u) {
  if (!u) return u;
  if (!u.startsWith("/")) return u; // 绝对地址 / wxfile:// / data: 原样
  if (u.startsWith("/assets/")) return u; // 小程序包内本地资源，不拼 host
  return baseURL() + u; // 后端相对路径（/uploads/...）拼成绝对地址
}

module.exports = { absUrl };
