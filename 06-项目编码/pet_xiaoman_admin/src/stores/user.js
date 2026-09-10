import { defineStore } from "pinia";

// 用户登录态（角色权限对齐 PRD §8.5：店长/店员，接口侧 RBAC）
export const useUserStore = defineStore("user", {
  state: () => ({ token: "", name: "", role: "" }),
  actions: {
    async login(username, password) {
      // TODO: POST /api/b/auth/login（开发闭环任务）
      this.token = "dev-token";
      this.name = username;
    },
    logout() { this.$reset(); localStorage.removeItem("token"); },
  },
});
