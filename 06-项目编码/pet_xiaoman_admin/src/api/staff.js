import http from "./request";

export const listStaff = () => http.get("/staff");
export const createStaff = (payload) => http.post("/staff", payload);
export const updateStaff = (id, payload) => http.put(`/staff/${id}`, payload);
export const disableStaff = (id) => http.post(`/staff/${id}/disable`);
