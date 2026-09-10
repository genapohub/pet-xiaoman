import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/tokens.css";

// Element Plus 改为按需引入（见 vite.config.js 的 ElementPlusResolver）。
// Message/MessageBox 以 JS 调用，不在模板中出现，样式需手动补。
import "element-plus/theme-chalk/el-message.css";
import "element-plus/theme-chalk/el-message-box.css";
import "element-plus/theme-chalk/el-notification.css";
import "element-plus/theme-chalk/el-loading.css";

createApp(App).use(createPinia()).use(router).mount("#app");
