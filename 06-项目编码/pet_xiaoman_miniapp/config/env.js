// 后端地址：开发期走本机 HTTP（需开发者工具勾选「不校验合法域名」），上线走云托管 HTTPS。
// 微信平台硬约束：体验版/正式版必须 HTTPS 且域名已在微信后台注册，本地 http 仅用于调试。

// 换 WiFi / 换开发机后改这一行即可（命令行查：ipconfig getifaddr en0）
const DEV_BASE = {
  simulator: "http://127.0.0.1:8000", // 开发者工具模拟器
  device: "http://192.168.1.3:8000", // 真机预览/真机调试（手机与本机的同一局域网）
};

// TODO: 云托管环境域名确认后填入
const PROD_BASE = "https://dev.example.com";

// 临时覆盖：控制台执行 wx.setStorageSync('debug_base_url', 'http://x.x.x.x:8000') 后重启小程序
const OVERRIDE_KEY = "debug_base_url";

function currentEnv() {
  try {
    return wx.getAccountInfoSync().miniProgram.envVersion || "develop";
  } catch (e) {
    return "develop";
  }
}

function isSimulator() {
  try {
    const info = wx.getDeviceInfo ? wx.getDeviceInfo() : wx.getSystemInfoSync();
    return info.platform === "devtools";
  } catch (e) {
    return true;
  }
}

function baseURL() {
  const override = wx.getStorageSync(OVERRIDE_KEY);
  if (override) return override;
  if (currentEnv() !== "develop") return PROD_BASE;
  return isSimulator() ? DEV_BASE.simulator : DEV_BASE.device;
}

module.exports = { baseURL, DEV_BASE, PROD_BASE, OVERRIDE_KEY };
