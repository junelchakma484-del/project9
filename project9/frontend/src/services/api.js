import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Unauthorized - redirect to login
          localStorage.removeItem('authToken');
          window.location.href = '/login';
          break;
        case 403:
          // Forbidden
          console.error('Access forbidden');
          break;
        case 404:
          // Not found
          console.error('Resource not found');
          break;
        case 500:
          // Server error
          console.error('Server error');
          break;
        default:
          console.error('API error:', error.response.data);
      }
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.request);
    } else {
      // Other error
      console.error('Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// API methods
export const apiService = {
  // System status
  getStatus: () => api.get('/api/status'),
  
  // Cameras
  getCameras: () => api.get('/api/cameras'),
  controlCamera: (cameraId, action) => api.post(`/api/cameras/${cameraId}/control`, { action }),
  
  // Detections
  getDetections: (params = {}) => api.get('/api/detections', { params }),
  
  // Analytics
  getAnalytics: (period = 'today') => api.get('/api/analytics', { params: { period } }),
  
  // Alerts
  getAlerts: (params = {}) => api.get('/api/alerts', { params }),
  
  // Settings
  getSettings: () => api.get('/api/settings'),
  updateSettings: (settings) => api.put('/api/settings', settings),
};

export { api };
