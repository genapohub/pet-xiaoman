import http from "./request";

export const listItems = (type) => http.get("/service-items", { params: { type } });
export const createItem = (payload) => http.post("/service-items", payload);
export const updateItem = (id, payload) => http.put(`/service-items/${id}`, payload);
export const offSale = (id) => http.post(`/service-items/${id}/off-sale`);
export const listVersions = (id) => http.get(`/service-items/${id}/versions`);
