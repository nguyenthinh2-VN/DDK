import axios from "axios";

const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor cho Request: Gắn token và ngôn ngữ vào header
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Đọc ngôn ngữ từ localStorage (mặc định "vi")
    const lang = localStorage.getItem("app_language") || "vi";
    config.headers["Accept-Language"] = lang;

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor cho Response: Xử lý lỗi chung (VD: 401 hết hạn token)
axiosClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      const originalRequest = error.config;
      // Không chuyển hướng nếu lỗi 401 xuất phát từ API login (sai tài khoản/mật khẩu)
      if (originalRequest.url && !originalRequest.url.includes("/api/auth/login")) {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;
