import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";

const apiTarget = process.env.VITE_API_TARGET || "http://127.0.0.1:8010";

function printApiProxyHelp(err, req) {
  const path = req?.url || "/api/...";
  const code = err?.code || "UNKNOWN";
  const isRefused = code === "ECONNREFUSED";
  const title = isRefused
    ? "后台前端已启动，但 API 服务没有连上"
    : "后台前端代理 API 时出错";

  console.error(`
========== 宠小满后台 API 代理提示 ==========
问题：${title}
接口：${path}
目标：${apiTarget}
错误：${code}${err?.message ? ` · ${err.message}` : ""}

怎么处理：
1. 先在 PyCharm 启动「API FastAPI 8010 Shell」。
2. 看到 Uvicorn running on http://127.0.0.1:8010 后，再启动「后台前端 Vite 5173」。
3. 浏览器验证 http://127.0.0.1:8010/healthz，应返回 {"ok":true}。
4. 如果你改了 API 端口，要同步修改后台前端配置里的 VITE_API_TARGET。
============================================
`);
}

export default defineConfig({
  plugins: [
    vue(),
    // 按需引入 Element Plus：全量包会让 index.js 膨胀到 1MB，这里只打包模板里实际用到的组件
    Components({ resolvers: [ElementPlusResolver({ directives: true })], dts: false }),
  ],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
        configure(proxy) {
          proxy.on("error", printApiProxyHelp);
        },
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // 把 element-plus / vue 拆出去，业务代码改动时长期命中 CDN/浏览器缓存
        manualChunks(id) {
          if (id.includes("node_modules/element-plus")) return "el-plus";
          if (id.includes("node_modules/vue") || id.includes("node_modules/@vue")) return "vue-vendor";
        },
      },
    },
  },
});
