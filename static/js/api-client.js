// API client for making authenticated requests to Django backend
import { getCurrentUserToken } from './auth.js';

// Base API URL - adjust based on your environment
const API_BASE_URL = window.location.origin + '/api';

// Make authenticated API request
export const apiRequest = async (endpoint, options = {}) => {
  const token = await getCurrentUserToken();
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }
  
  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
};

// Convenience methods
export const apiGet = (endpoint) => apiRequest(endpoint);

export const apiPost = (endpoint, data) => 
  apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const apiPut = (endpoint, data) => 
  apiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const apiDelete = (endpoint) => 
  apiRequest(endpoint, {
    method: 'DELETE',
  });

// Upload file with authentication
export const uploadFile = async (endpoint, file, additionalData = {}) => {
  const token = await getCurrentUserToken();
  
  const formData = new FormData();
  formData.append('file', file);
  
  // Add any additional form data
  Object.keys(additionalData).forEach(key => {
    formData.append(key, additionalData[key]);
  });
  
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers,
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
};
