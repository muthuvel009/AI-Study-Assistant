import api from './api';

export const documentService = {
  async getDocuments() {
    return await api.get('/api/documents');
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    return await api.upload('/api/documents/upload', formData);
  },

  async deleteDocument(id) {
    return await api.del(`/api/documents/${id}`);
  },

  async getDocumentById(id) {
    return await api.get(`/api/documents/${id}`);
  },
};

export default documentService;
