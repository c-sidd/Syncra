import axios from 'axios';

// Instantiate an Axios HTTP client instance pointing to our local Django backend
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
});

// Register a request interceptor to automatically attach authorization tokens to headers
api.interceptors.request.use(
  (config) => {
    // Read the active token key from the browser's local storage
    const token = localStorage.getItem('token');
    if (token) {
      // If a token is active, inject it into the Authorization header using Django's format
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    // Forward request parsing errors
    return Promise.reject(error);
  }
);

export default api;
