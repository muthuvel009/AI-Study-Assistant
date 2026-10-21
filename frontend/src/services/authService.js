import api from './api';

export const authService = {
  async register(data) {
    const response = await api.post('/api/auth/register', data);
    if (response.access_token) {
      api.setToken(response.access_token);
    }
    return response;
  },

  async login(credentials) {
    const response = await api.post('/api/auth/login', credentials);
    if (response.access_token) {
      api.setToken(response.access_token);
    }
    return response;
  },

  async getMe() {
    return await api.get('/api/auth/me');
  },

  logout() {
    api.setToken(null);
  },

  isAuthenticated() {
    return !!api.getToken();
  },
};

export default authService;
