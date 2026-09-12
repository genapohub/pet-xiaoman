import { defineStore } from "pinia";
import { getMe, getStoreProfile, login as loginApi } from "../api/auth";
import { applyBrandColor, resetBrandColor } from "../utils/theme";

// 用户登录态（角色权限对齐 PRD §8.5：平台超管 / 店长 / 店员，接口侧 RBAC）
// 多租户：登录后拉取本店白标资料，按店主色换肤 + 展示门店店名/logo。
// 超管不属于任何门店（store_id=null），菜单只有「门店管理」——品牌由他配给别人，自己不需要。
export const useUserStore = defineStore("user", {
  state: () => ({
    token: localStorage.getItem("token") || "",
    id: null,
    username: "",
    name: "",
    role: "",
    roleName: "",
    menus: [],
    permissions: [],
    storeProfile: null,
    loaded: false,
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    isSuperAdmin: (state) => state.role === "super_admin",
    canMenu: (state) => (key) => !key || state.menus.includes(key),
    canPerm: (state) => (code) => state.permissions.includes(code),

    // 品牌兜底一律中性：绝不回落到平台或别家门店的名字，否则新门店会顶着别人的品牌上线
    storeName: (state) => {
      if (state.storeProfile?.name) return state.storeProfile.name;
      return state.role === "super_admin" ? "平台管理台" : "门店后台";
    },
    storeSlogan: (state) => {
      if (state.storeProfile?.slogan) return state.storeProfile.slogan;
      return state.role === "super_admin" ? "多门店统一管理" : "";
    },
    storeLogo: (state) => state.storeProfile?.logo_url || "",
    storeColor: (state) => state.storeProfile?.primary_color || "#5B8C85",
    // 未配 logo 时的占位字：取店名首字，而不是某家门店的品牌资产
    storeInitial: (state) => {
      const own = state.storeProfile?.name?.trim();
      if (own) return own.slice(0, 1);
      return state.role === "super_admin" ? "平" : "店";
    },
  },
  actions: {
    async login(username, password) {
      const data = await loginApi(username, password);
      localStorage.setItem("token", data.token);
      this.token = data.token;
      this.applyStaff(data.staff);
      this.loaded = true;
      await this.fetchStoreProfile();
    },
    async fetchMe() {
      if (!this.token) return null;
      const data = await getMe();
      this.applyStaff(data);
      this.loaded = true;
      await this.fetchStoreProfile();
      return data;
    },
    async fetchStoreProfile() {
      try {
        const profile = await getStoreProfile();
        this.applyStoreProfile(profile);
      } catch {
        // 门店资料缺失不阻断登录（兼容旧门店），仅用默认品牌
      }
      return this.storeProfile;
    },
    applyStoreProfile(profile) {
      this.storeProfile = profile;
      if (profile?.primary_color) applyBrandColor(profile.primary_color);
    },
    applyStaff(staff) {
      this.id = staff.id;
      this.username = staff.username;
      this.name = staff.name;
      this.role = staff.role;
      this.roleName = staff.role_name || staff.role;
      this.menus = staff.menus || [];
      this.permissions = staff.permissions || [];
    },
    logout() {
      localStorage.removeItem("token");
      this.$reset();
      this.token = "";
      this.storeProfile = null;
      resetBrandColor();
    },
  },
});
