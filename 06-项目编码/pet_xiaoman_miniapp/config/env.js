// 后端地址：开发期走本机 HTTP（需开发者工具勾选「不校验合法域名」），上线走云托管 HTTPS。
// 微信平台硬约束：体验版/正式版必须 HTTPS 且域名已在微信后台注册，本地 http 仅用于调试。

// 换 WiFi / 换开发机后改这一行即可（命令行查：ipconfig getifaddr en0）
const DEV_BASE = {
  simulator: "http://127.0.0.1:8010", // 开发者工具模拟器
  device: "http://192.168.1.3:8010", // 真机预览/真机调试（手机与本机的同一局域网）
};

// TODO: 云托管环境域名确认后填入
const PROD_BASE = "https://dev.example.com";

// 临时覆盖：控制台执行 wx.setStorageSync('debug_base_url', 'http://x.x.x.x:8010') 后重启小程序
const OVERRIDE_KEY = "debug_base_url";
const API_PORT = "8010";

function currentEnv() {
  try {
    return wx.getAccountInfoSync().miniProgram.envVersion || "develop";
  } catch (e) {
    return "develop";
  }
}

function isDevelopEnv() {
  return currentEnv() === "develop";
}

function isSimulator() {
  try {
    const info = wx.getDeviceInfo ? wx.getDeviceInfo() : wx.getSystemInfoSync();
    return info.platform === "devtools";
  } catch (e) {
    return true;
  }
}

function normalizeDevBase(url) {
  if (!url || typeof url !== "string") return url;
  const fixed = url.replace(/:8000\b/g, `:${API_PORT}`);
  if (fixed !== url) {
    console.warn(`[接口配置] 检测到旧调试地址 ${url}，已自动切换为 ${fixed}。如果仍异常，请清理 Storage 里的 ${OVERRIDE_KEY}。`);
    try {
      wx.setStorageSync(OVERRIDE_KEY, fixed);
    } catch (e) {
      // storage 写入失败不阻断请求，继续使用修正后的地址。
    }
  }
  return fixed;
}

function repairDebugBaseURL() {
  try {
    const override = wx.getStorageSync(OVERRIDE_KEY);
    if (!override) return;
    normalizeDevBase(override);
  } catch (e) {
    // 仅用于开发期调试地址迁移，失败不影响正式请求。
  }
}

function baseURL() {
  const override = wx.getStorageSync(OVERRIDE_KEY);
  if (override) return normalizeDevBase(override);
  if (currentEnv() !== "develop") return PROD_BASE;
  return normalizeDevBase(isSimulator() ? DEV_BASE.simulator : DEV_BASE.device);
}

module.exports = { baseURL, DEV_BASE, PROD_BASE, OVERRIDE_KEY, repairDebugBaseURL, isDevelopEnv };
