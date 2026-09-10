import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";

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
    proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } },
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
