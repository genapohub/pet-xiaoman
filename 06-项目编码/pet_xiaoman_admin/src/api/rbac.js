import http from "./request";

export const listMenus = () => http.get("/menus");
export const listPermissions = () => http.get("/permissions");
export const listRoles = () => http.get("/roles");
export const updateRole = (roleKey, payload) => http.put(`/roles/${roleKey}`, payload);
