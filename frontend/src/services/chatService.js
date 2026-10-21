import api from './api';

export const chatService = {
  async sendMessage({ query, documentId = null }) {
    return await api.post('/api/chat', {
      query,
      document_id: documentId || null,
    });
  },

  async getChatHistory() {
    return await api.get('/api/chat/history');
  },

  async clearChat() {
    return await api.del('/api/chat/history');
  },
};

export default chatService;
