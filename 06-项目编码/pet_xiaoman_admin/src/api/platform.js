import http from "./request";

// 平台层（超管）接口：统一开店 / 启停门店 / 配品牌与 UI / 开门店账号。
// 租户侧接口不提供这些能力（品牌配置已收归超管）。
const BASE = "/platform";

export const listStores = () => http.get(`${BASE}/stores`);
export const getStore = (storeId) => http.get(`${BASE}/stores/${storeId}`);
export const createStore = (payload) => http.post(`${BASE}/stores`, payload);
export const setStoreStatus = (storeId, status) =>
  http.post(`${BASE}/stores/${storeId}/status`, { status });

// 品牌与 UI
export const getStoreBrand = (storeId) => http.get(`${BASE}/stores/${storeId}/profile`);
export const updateStoreBrand = (storeId, payload) =>
  http.put(`${BASE}/stores/${storeId}/profile`, payload);

// 门店账号
export const listStoreStaff = (storeId) => http.get(`${BASE}/stores/${storeId}/staff`);
export const createStoreStaff = (storeId, payload) =>
  http.post(`${BASE}/stores/${storeId}/staff`, payload);
export const updateStoreStaff = (storeId, staffId, payload) =>
  http.put(`${BASE}/stores/${storeId}/staff/${staffId}`, payload);
export const disableStoreStaff = (storeId, staffId) =>
  http.post(`${BASE}/stores/${storeId}/staff/${staffId}/disable`);
