import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_URL });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A saved login that the server no longer accepts (expired after 24h, the server's
// JWT_SECRET_KEY changed, or the account isn't in this database) must not keep the user
// "logged in" on a dashboard that can't load anything. Clear it and go to the login page.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || "";
    const rejectedSavedLogin =
      error.response?.status === 401 && localStorage.getItem("token") && !url.startsWith("/auth/");
    if (rejectedSavedLogin) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

export default client;
export { API_URL };
