import api from './api';

export const progressService = {
  async getProgressSummary() {
    return await api.get('/api/progress/summary');
  },

  async getTopicProgress(topic) {
    return await api.get(`/api/progress/${encodeURIComponent(topic)}`);
  },
};

export default progressService;
