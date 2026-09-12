import axios from "axios";
import { ElMessage } from "element-plus";

// 统一请求封装：带 token、401 跳登录、错误 Toast
const http = axios.create({ baseURL: "/api/b", timeout: 10000 });

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// 报错文案统一在这里翻译，页面不必各自处理 detail
function pickMessage(err) {
  const status = err.response?.status;
  const detail = err.response?.data?.detail;
  if (!err.response) return "网络异常，请检查门店网络后重试";
  if (status === 401) return "登录已过期，正在跳转登录";
  // 403 优先用后端给的说明（如「仅平台超管可执行此操作」），比泛化文案更可诊断
  if (status === 403) return typeof detail === "string" && detail ? detail : "当前角色无此操作权限";
  if (status === 404) return "接口不存在（可能已下线或地址变更）";
  if (status >= 500) return "服务异常，已通知技术侧";
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg; // FastAPI 422 校验结构
  return typeof detail === "string" ? detail : "操作失败，请重试";
}

http.interceptors.response.use(
  (res) => res.data.data !== undefined ? res.data.data : res.data,
  (err) => {
    const msg = pickMessage(err);
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      setTimeout(() => (location.href = "/login"), 800);
    }
    ElMessage.error(msg); // 任何调用方都有反馈，不再靠页面各自 catch
    return Promise.reject(err);
  }
);

export default http;
