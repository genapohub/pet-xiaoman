import http from "./request";

// request.js 的 baseURL 已是 /api/b，这里不要再写前缀
// （历史 bug：写了 /api/b/products 会拼成 /api/b/api/b/products，全部 404）

// 纪念品（B006/C007）
export const listProducts = () => http.get("/products");
export const createProduct = (payload) => http.post("/products", payload);
export const updateProduct = (id, payload) => http.put(`/products/${id}`, payload);
export const toggleProduct = (id) => http.post(`/products/${id}/toggle`);

// 寄存（B007）
export const listBoardings = () => http.get("/boardings");
export const createBoarding = (payload) => http.post("/boardings", payload);
export const renewBoarding = (id, expireDate) => http.post(`/boardings/${id}/renew`, { expire_date: expireDate });
export const takeBoarding = (id, takenBy) => http.post(`/boardings/${id}/take`, { taken_by: takenBy });

// 客户（B008/B009）
export const listCustomers = (role = "店长") => http.get("/customers", { params: { role } });
export const getCustomer = (id, role = "店长") => http.get(`/customers/${id}`, { params: { role } });
export const setSource = (id, source) => http.post(`/customers/${id}/source`, { source });
export const registerVisit = (id, payload) => http.post(`/customers/${id}/visit`, payload);
