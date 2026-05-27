import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

const PUBLIC_PATHS = new Set(['/', '/login', '/signup']);
const AUTH_ENDPOINTS = ['/auth/login', '/auth/signup'];

// Request interceptor — attach token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('ac_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor — handle auth errors
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ac_token');
      delete api.defaults.headers.common.Authorization;

      const requestUrl = err.config?.url || '';
      const isAuthRequest = AUTH_ENDPOINTS.some(path => requestUrl.includes(path));
      const currentPath = window.location.pathname;

      if (!isAuthRequest && !PUBLIC_PATHS.has(currentPath)) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export default api;
