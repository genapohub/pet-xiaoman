import http from "./request";

export const getStats = (month) => http.get("/stats", { params: { month } });
