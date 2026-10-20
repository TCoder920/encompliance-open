/*
  Description: Customer support API client for authenticated portal actions.
  Purpose: Centralizes configuration, headers, and auth token injection for support tooling.
*/
import axios from 'axios';

const envBaseUrl = (import.meta.env.VITE_SUPPORT_API_BASE_URL || '').trim();
// If an explicit base URL is provided (http/https), use it. Otherwise use relative URLs so
// the frontend dev/prod proxy handles routing to the backend.
const supportBaseURL =
  envBaseUrl && envBaseUrl !== '/' && (envBaseUrl.startsWith('http://') || envBaseUrl.startsWith('https://'))
    ? envBaseUrl
    : '';
const TOKEN_STORAGE_KEY = 'customerSupportToken';

const customerSupportApi = axios.create({
  baseURL: supportBaseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

customerSupportApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) {
      config.headers = config.headers || {};
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default customerSupportApi;
