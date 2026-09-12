// 后端媒体（服务影像 / 商品图）URL 归一化
//
// 后端 media_service / product.images 返回的是相对路径 `/uploads/...`。
// 两端解析方式不同，但拿到的始终是同一个后端文件，因此渲染内容完全一致：
//   - 小程序：必须拼绝对地址（utils/url.js 的 absUrl）——它没有 origin 可代理，
//     且真机要用局域网 IP（192.168.x.x），模拟器用 127.0.0.1。
//   - 后台：默认同源 —— dev 由 Vite 的 /uploads 代理转发，生产由 nginx 把
//     /api 与 /uploads 反代到同一后端。同源方案无跨域、无需微信域名白名单。
//
// 若后台与 API 分开部署（不同域名），构建时显式指定基址即可切成绝对地址：
//   VITE_MEDIA_BASE=https://api.example.com npm run build
// 未设置时保持相对路径（= 依赖同源反代）。

const MEDIA_BASE = import.meta.env.VITE_MEDIA_BASE || "";

export function mediaUrl(u) {
  if (!u) return u;
  if (/^(https?:|data:|blob:|\/\/)/i.test(u)) return u; // 已是绝对地址/本地 blob
  if (u.startsWith("/assets/")) return u;               // 前端包内资源
  return MEDIA_BASE ? MEDIA_BASE + u : u;               // 未配置 → 同源相对路径
}
