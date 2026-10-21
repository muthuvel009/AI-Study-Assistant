import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Award,
  Sparkles,
  HelpCircle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Clock,
  BookOpen,
  Filter,
  Plus,
  FileText,
  AlertTriangle,
  ChevronRight,
} from 'lucide-react';
import quizService from '../services/quizService';
import documentService from '../services/documentService';
import { useToast } from '../context/ToastContext';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';
import EmptyState from '../components/common/EmptyState';
import Spinner from '../components/common/Spinner';

export const Quiz = () => {
  const location = useLocation();
  const { success, error, warning, info } = useToast();

  const [quizzes, setQuizzes] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Generator modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [formData, setFormData] = useState({
    documentId: location.state?.documentId || '',
    topic: '',
    difficulty: 'Medium',
    numQuestions: 5,
  });

  // Active Quiz taking state
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [quizResults, setQuizResults] = useState(null);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      // Fetch documents
      try {
        const docData = await documentService.getDocuments();
        setDocuments(Array.isArray(docData) ? docData : docData?.documents || []);
      } catch {
        const localDocs = localStorage.getItem('ai_study_docs');
        if (localDocs) setDocuments(JSON.parse(localDocs));
      }

      // Fetch quiz history
      try {
        const quizData = await quizService.getQuizzes();
        setQuizzes(Array.isArray(quizData) ? quizData : quizData?.quizzes || []);
      } catch {
        const localQuizzes = localStorage.getItem('ai_study_quizzes');
        if (localQuizzes) setQuizzes(JSON.parse(localQuizzes));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const saveLocalQuizzes = (updated) => {
    setQuizzes(updated);
    localStorage.setItem('ai_study_quizzes', JSON.stringify(updated));
  };

  const handleGenerateQuiz = async (e) => {
    e.preventDefault();
    if (!formData.topic.trim()) {
      error('Please specify a topic or concept to test.');
      return;
    }

    setGenerating(true);
    try {
      const created = await quizService.generateQuiz({
        documentId: formData.documentId || null,
        topic: formData.topic.trim(),
        difficulty: formData.difficulty,
        numQuestions: formData.numQuestions,
      });

      success(`Quiz generated on "${formData.topic}"!`);
      setModalOpen(false);
      startQuiz(created);
      await loadInitialData();
    } catch (err) {
      error(err.message || 'Failed to generate quiz from study material.');
    } finally {
      setGenerating(false);
    }
  };

  const startQuiz = (quiz) => {
    setActiveQuiz(quiz);
    setCurrentQIndex(0);
    setUserAnswers({});
    setQuizResults(null);
  };

  const handleSelectOption = (questionId, option) => {
    setUserAnswers((prev) => ({
      ...prev,
      [questionId]: option,
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!activeQuiz) return;
    const questions = activeQuiz.questions || [];
    const answeredCount = Object.keys(userAnswers).length;

    if (answeredCount < questions.length) {
      if (!window.confirm(`You answered ${answeredCount} of ${questions.length} questions. Submit anyway?`)) {
        return;
      }
    }

    setSubmitting(true);
    try {
      const results = await quizService.submitQuiz(activeQuiz.id, userAnswers);
      const normalizedResults = {
        ...results,
        questions: results.question_results || results.questions || [],
        correct_answers: results.correct_count !== undefined ? results.correct_count : results.correct_answers,
      };
      setQuizResults(normalizedResults);
      success('Quiz submitted and scored on the server!');
      await loadInitialData();
    } catch (err) {
      error(err.message || 'Failed to submit quiz.');
    } finally {
      setSubmitting(false);
    }
  };

  const currentQuestions = activeQuiz?.questions || [];
  const currentQuestion = currentQuestions[currentQIndex];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Adaptive Quizzes</h1>
          <p className="text-sm text-slate-400 mt-1">
            Semantic RAG-driven multiple-choice assessments with strict server-side grading.
          </p>
        </div>
        {!activeQuiz && (
          <Button
            variant="primary"
            icon={Plus}
            onClick={() => setModalOpen(true)}
          >
            Generate New Quiz
          </Button>
        )}
      </div>

      {/* ACTIVE QUIZ RUNNER MODE */}
      {activeQuiz && !quizResults && (
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Quiz Top bar: Progress, Timer, Topic */}
          <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-900 border border-slate-800">
            <div className="flex items-center gap-3">
              <Badge variant="indigo">{activeQuiz.difficulty || 'Medium'}</Badge>
              <h3 className="text-sm font-bold text-white truncate">{activeQuiz.topic}</h3>
            </div>
            <div className="text-xs font-semibold text-slate-400">
              Question {currentQIndex + 1} of {currentQuestions.length}
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
            <div
              className="h-full bg-indigo-500 transition-all duration-300"
              style={{
                width: `${((currentQIndex + 1) / (currentQuestions.length || 1)) * 100}%`,
              }}
            />
          </div>

          {/* Current Question Card */}
          {currentQuestion && (
            <Card className="p-6 sm:p-8 space-y-6">
              <div className="space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
                  Question {currentQIndex + 1}
                </span>
                <h3 className="text-base sm:text-lg font-medium text-slate-100 leading-relaxed">
                  {currentQuestion.question_text}
                </h3>
              </div>

              {/* 4 Options Selection */}
              <div className="space-y-3">
                {currentQuestion.options?.map((opt, oIdx) => {
                  const isSelected = userAnswers[currentQuestion.id] === opt;
                  return (
                    <div
                      key={oIdx}
                      onClick={() => handleSelectOption(currentQuestion.id, opt)}
                      className={`p-4 rounded-xl border text-sm font-medium transition-all duration-150 cursor-pointer flex items-center gap-3 ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-600/20 text-white shadow-md shadow-indigo-500/10'
                          : 'border-slate-800 bg-slate-950/40 text-slate-300 hover:border-slate-700 hover:bg-slate-800/40'
                      }`}
                    >
                      <div
                        className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                          isSelected
                            ? 'bg-indigo-600 text-white'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {String.fromCharCode(65 + oIdx)}
                      </div>
                      <span className="flex-1 leading-relaxed">{opt}</span>
                    </div>
                  );
                })}
              </div>

              {/* Navigation controls */}
              <div className="flex items-center justify-between pt-6 border-t border-slate-800">
                <Button
                  variant="outline"
                  size="sm"
                  icon={ArrowLeft}
                  disabled={currentQIndex === 0}
                  onClick={() => setCurrentQIndex((prev) => Math.max(0, prev - 1))}
                >
                  Previous
                </Button>

                <div className="flex items-center gap-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (window.confirm('Are you sure you want to exit? Your progress will be lost.')) {
                        setActiveQuiz(null);
                      }
                    }}
                  >
                    Exit
                  </Button>

                  {currentQIndex < currentQuestions.length - 1 ? (
                    <Button
                      variant="primary"
                      size="sm"
                      icon={ArrowRight}
                      iconPosition="right"
                      onClick={() => setCurrentQIndex((prev) => prev + 1)}
                    >
                      Next
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      loading={submitting}
                      icon={CheckCircle2}
                      onClick={handleSubmitQuiz}
                    >
                      Submit Quiz
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* QUIZ RESULTS MODE (Scored Server-Side) */}
      {quizResults && (
        <div className="max-w-3xl mx-auto space-y-8 animate-in zoom-in-95 duration-200">
          {/* Score Header Card */}
          <div className="p-8 rounded-3xl bg-gradient-to-r from-indigo-900/60 to-purple-900/40 border border-indigo-500/30 text-center space-y-4 shadow-2xl backdrop-blur-xl">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 mx-auto flex items-center justify-center">
              <Award className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">Quiz Evaluation Complete</h2>
            <p className="text-sm text-slate-300">
              Scored on the server against verified study material for topic: <strong>{quizResults.topic}</strong>
            </p>

            <div className="text-5xl font-black text-indigo-400 tracking-tight my-2">
              {quizResults.score}%
            </div>
            <p className="text-xs text-slate-400">
              {quizResults.correct_answers} of {quizResults.total_questions} questions correct
            </p>

            <div className="flex justify-center gap-3 pt-2">
              <Button
                variant="primary"
                icon={RotateCcw}
                onClick={() => {
                  setQuizResults(null);
                  setActiveQuiz(null);
                }}
              >
                Back to Quizzes
              </Button>
              <Button
                variant="outline"
                onClick={() => setModalOpen(true)}
              >
                Retake or New Topic
              </Button>
            </div>
          </div>

          {/* Question Breakdown with Explanations (Grounded in Material) */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white">Question Review</h3>
            {quizResults.questions?.map((q, idx) => (
              <div
                key={idx}
                className={`p-6 rounded-2xl border ${
                  q.is_correct
                    ? 'bg-emerald-950/20 border-emerald-500/30'
                    : 'bg-rose-950/20 border-rose-500/30'
                } space-y-3`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Question {idx + 1}
                  </span>
                  {q.is_correct ? (
                    <Badge variant="success" dot>Correct</Badge>
                  ) : (
                    <Badge variant="danger" dot>Incorrect</Badge>
                  )}
                </div>

                <p className="text-sm font-medium text-slate-100 leading-relaxed">
                  {q.question_text}
                </p>

                <div className="text-xs space-y-1 pt-1">
                  <p className="text-slate-400">
                    Your Answer: <span className="font-semibold text-slate-200">{q.student_answer || q.user_answer || 'Not Answered'}</span>
                  </p>
                  {!q.is_correct && (
                    <p className="text-emerald-400">
                      Correct Answer: <span className="font-semibold">{q.correct_answer}</span>
                    </p>
                  )}
                </div>

                {q.explanation && (
                  <div className="mt-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300">
                    <span className="font-semibold text-indigo-400">Explanation: </span>
                    {q.explanation}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* QUIZ DASHBOARD / HISTORY LIST (When not taking a quiz) */}
      {!activeQuiz && !quizResults && (
        <div className="space-y-6">
          <Card
            title="Quiz History"
            subtitle="Previous evaluation attempts and server scores"
            icon={Award}
          >
            {loading ? (
              <Spinner size="md" label="Loading past quizzes..." />
            ) : quizzes.length === 0 ? (
              <EmptyState
                icon={Award}
                title="No Quizzes Attempted Yet"
                description="Use the generator to create an AI practice quiz from your uploaded materials or custom topics."
                actionText="Generate First Quiz"
                actionIcon={Plus}
                onAction={() => setModalOpen(true)}
              />
            ) : (
              <div className="divide-y divide-slate-800">
                {quizzes.map((quiz) => (
                  <div
                    key={quiz.id}
                    className="py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group"
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
                        <Award className="w-5 h-5" />
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-sm font-semibold text-slate-200 truncate group-hover:text-indigo-400 transition-colors">
                          {quiz.topic || 'General Practice'}
                        </h4>
                        <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                          <Badge variant="default" size="sm">
                            {quiz.difficulty || 'Medium'}
                          </Badge>
                          <span>•</span>
                          <span>{quiz.num_questions || quiz.questions?.length || 5} questions</span>
                          <span>•</span>
                          <span>
                            {quiz.created_at ? new Date(quiz.created_at).toLocaleDateString() : 'Recent'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 self-end sm:self-auto shrink-0">
                      {quiz.score !== undefined && (
                        <div className="text-right mr-2">
                          <div className="text-sm font-bold text-emerald-400">{Math.round(quiz.score)}%</div>
                          <div className="text-[10px] text-slate-500">Score</div>
                        </div>
                      )}
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => startQuiz(quiz)}
                      >
                        {quiz.score !== undefined ? 'Retake' : 'Start'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* QUIZ GENERATION MODAL */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Generate AI Practice Quiz"
        subtitle="RAG retrieves relevant document chunks to construct grounded multiple choice questions"
      >
        <form onSubmit={handleGenerateQuiz} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Source Material
            </label>
            <select
              value={formData.documentId}
              onChange={(e) => setFormData({ ...formData, documentId: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">All Uploaded Documents</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.filename || doc.name}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400 mt-1">
              Select a specific document or let the system search all indexed materials.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Topic or Subject Focus *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Graph Algorithms, Neural Networks, Thermodynamics"
              value={formData.topic}
              onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Difficulty
              </label>
              <select
                value={formData.difficulty}
                onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="Easy">Easy (Fundamentals)</option>
                <option value="Medium">Medium (Application)</option>
                <option value="Hard">Hard (Deep Analysis)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Number of Questions
              </label>
              <select
                value={formData.numQuestions}
                onChange={(e) => setFormData({ ...formData, numQuestions: Number(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value={3}>3 Questions (Quick Sprint)</option>
                <option value={5}>5 Questions (Standard)</option>
                <option value={10}>10 Questions (Comprehensive)</option>
                <option value={15}>15 Questions (Exam Prep)</option>
              </select>
            </div>
          </div>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <Button
              variant="outline"
              size="md"
              type="button"
              onClick={() => setModalOpen(false)}
              disabled={generating}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              type="submit"
              loading={generating}
              icon={Sparkles}
            >
              Generate Quiz
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Quiz;
