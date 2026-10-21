import api from './api';

export const quizService = {
  async generateQuiz({ documentId, topic, difficulty = 'Medium', numQuestions = 5 }) {
    return await api.post('/api/quizzes/generate', {
      document_id: documentId || null,
      topic,
      difficulty,
      num_questions: Number(numQuestions),
    });
  },

  async getQuizzes() {
    return await api.get('/api/quizzes');
  },

  async getQuizById(id) {
    return await api.get(`/api/quizzes/${id}`);
  },

  async submitQuiz(id, userAnswers) {
    // userAnswers format: { question_id: selected_option_text_or_index }
    return await api.post(`/api/quizzes/${id}/submit`, {
      answers: userAnswers,
    });
  },

  async getQuizResults(id) {
    return await api.get(`/api/quizzes/${id}/results`);
  },
};

export default quizService;
