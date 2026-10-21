/**
 * Centralized API client for AI Study Assistant.
 * Handles base URL configuration, JWT bearer token injection,
 * response parsing, and standard error serialization.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  getToken() {
    return localStorage.getItem('ai_study_token');
  }

  setToken(token) {
    if (token) {
      localStorage.setItem('ai_study_token', token);
    } else {
      localStorage.removeItem('ai_study_token');
    }
  }

  getHeaders(customHeaders = {}, isFormData = false) {
    const headers = { ...customHeaders };
    const token = this.getToken();

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!isFormData && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const isFormData = options.body instanceof FormData;
    
    const config = {
      ...options,
      headers: this.getHeaders(options.headers, isFormData),
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized globally
      if (response.status === 401) {
        this.setToken(null);
        // Only redirect if not already on login/register
        if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }
      }

      const contentType = response.headers.get('content-type');
      let data = null;

      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMessage = (data && (data.detail || data.message)) || `Request failed with status ${response.status}`;
        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (error) {
      // If server is unreachable (e.g. during Phase 1 before backend runs)
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        const offlineError = new Error('Backend server is currently offline or unreachable at ' + this.baseUrl);
        offlineError.isOffline = true;
        offlineError.status = 503;
        throw offlineError;
      }
      throw error;
    }
  }

  get(endpoint, headers = {}) {
    return this.request(endpoint, { method: 'GET', headers });
  }

  post(endpoint, body, headers = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
      headers,
    });
  }

  put(endpoint, body, headers = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
      headers,
    });
  }

  del(endpoint, headers = {}) {
    return this.request(endpoint, { method: 'DELETE', headers });
  }

  upload(endpoint, formData, headers = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: formData,
      headers,
    });
  }

  async checkHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/health`, { method: 'GET' });
      return res.ok;
    } catch {
      return false;
    }
  }
}

export const api = new ApiClient();
export default api;
