import http from "./request";

export const listOrders = (params) => http.get("/orders", { params });
export const getOrderDetail = (orderNo) => http.get(`/orders/${orderNo}`);
export const confirmOrder = (orderNo) => http.post(`/orders/${orderNo}/confirm`, {});
export const transitionOrder = (orderNo, payload) => http.post(`/orders/${orderNo}/transition`, payload);
export const uploadMedia = (orderNo, node, file) => {
  const form = new FormData();
  form.append("file", file);
  return http.post(`/orders/${orderNo}/media?node=${encodeURIComponent(node)}`, form,
    { headers: { "Content-Type": "multipart/form-data" } });
};
export const saveNotes = (orderNo, notes) => http.put(`/orders/${orderNo}/notes`, { notes });
export const reschedule = (orderNo, expectTime) => http.post(`/orders/${orderNo}/reschedule`, { expect_time: expectTime });
export const settleOrder = (orderNo, amount) => http.post(`/orders/${orderNo}/settle`, { amount });
export const revokeMedia = (mediaId, reason) => http.post(`/media/${mediaId}/revoke`, { role: "店长", reason });
