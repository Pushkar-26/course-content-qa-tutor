
import axios from "axios";

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
if (typeof FormData !== "undefined" && config.data instanceof FormData) {
  if (typeof config.headers.delete === "function") {
    config.headers.delete("Content-Type");
  } else {
    delete config.headers["Content-Type"];
  }
}
  return config;
});

export default api;
