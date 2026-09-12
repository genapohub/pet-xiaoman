import http from "./request";

export const login = (username, password) => http.post("/auth/login", { username, password });
export const getMe = () => http.get("/auth/me");

// 门店白标资料：租户只读（后台按店换肤）。
// 写入已收归平台超管（见 api/platform.js 的 updateStoreBrand），
// 故这里刻意不导出 updateStoreProfile —— 那个接口现在恒返回 403，留着只会误导。
export const getStoreProfile = () => http.get("/store/profile");
