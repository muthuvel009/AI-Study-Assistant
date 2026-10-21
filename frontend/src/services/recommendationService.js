import api from './api';

export const recommendationService = {
  async getRecommendations() {
    return await api.get('/api/recommendations');
  },
};

export default recommendationService;
