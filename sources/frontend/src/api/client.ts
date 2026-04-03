import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api",
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const t = localStorage.getItem("edms_token");
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => Promise.reject(err),
);

export default api;
