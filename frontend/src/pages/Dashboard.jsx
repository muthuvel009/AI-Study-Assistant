import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FileText,
  MessageSquareText,
  Award,
  Sparkles,
  ArrowUpRight,
  Upload,
  BookOpen,
  TrendingUp,
  Clock,
  CheckCircle2,
  ChevronRight,
  ShieldCheck,
  GraduationCap,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import documentService from '../services/documentService';
import quizService from '../services/quizService';
import progressService from '../services/progressService';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';
import Spinner from '../components/common/Spinner';

export const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [quizzes, setQuizzes] = useState([]);
  const [progressSummary, setProgressSummary] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const loadDashboardData = async () => {
      try {
        setLoading(true);

        // Fetch documents
        try {
          const docData = await documentService.getDocuments();
          if (isMounted) setDocuments(Array.isArray(docData) ? docData : docData?.documents || []);
        } catch {
          if (isMounted) setDocuments([]);
        }

        // Fetch quizzes
        try {
          const quizData = await quizService.getQuizzes();
          if (isMounted) setQuizzes(Array.isArray(quizData) ? quizData : quizData?.quizzes || []);
        } catch {
          if (isMounted) setQuizzes([]);
        }

        // Fetch progress summary
        try {
          const progData = await progressService.getProgressSummary();
          if (isMounted) setProgressSummary(progData);
        } catch {
          if (isMounted) setProgressSummary(null);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadDashboardData();

    return () => {
      isMounted = false;
    };
  }, []);

  const totalDocuments = documents.length;
  const totalQuizzes = quizzes.length;
  const averageMastery = progressSummary?.average_mastery !== undefined
    ? `${Math.round(progressSummary.average_mastery)}%`
    : '0%';
  const questionsAnswered = progressSummary?.total_questions_answered || 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Welcome Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900/60 via-slate-900 to-purple-950/40 border border-indigo-500/20 p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
              <GraduationCap className="w-3.5 h-3.5" />
              <span>{user?.college || 'College Learning Workspace'}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Welcome back, {user?.full_name?.split(' ')[0] || 'Student'}!
            </h1>
            <p className="text-slate-300 text-sm max-w-xl leading-relaxed">
              Your AI Study Assistant is ready. Upload lecture notes, query course materials with source-grounded citations, and generate practice quizzes.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button
              variant="primary"
              icon={Upload}
              onClick={() => navigate('/documents')}
            >
              Upload Material
            </Button>
            <Button
              variant="outline"
              icon={MessageSquareText}
              onClick={() => navigate('/chat')}
            >
              Grounded Chat
            </Button>
          </div>
        </div>

        {/* Grounded reassurance tag */}
        <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center gap-2 text-xs text-indigo-300/80">
          <ShieldCheck className="w-4 h-4 text-indigo-400 shrink-0" />
          <span>Responses and quizzes are strictly grounded in your uploaded documents.</span>
        </div>
      </div>

      {/* Real Statistics Metric Cards (Zero-state authentic, no fake data) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents */}
        <Card className="p-5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Course Materials</p>
            <h3 className="text-2xl font-bold text-white tracking-tight">{totalDocuments}</h3>
            <p className="text-xs text-slate-400">
              {totalDocuments === 0 ? 'No documents yet' : `${totalDocuments} indexed PDF${totalDocuments > 1 ? 's' : ''}`}
            </p>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
        </Card>

        {/* Quizzes Completed */}
        <Card className="p-5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Quizzes Taken</p>
            <h3 className="text-2xl font-bold text-white tracking-tight">{totalQuizzes}</h3>
            <p className="text-xs text-slate-400">
              {totalQuizzes === 0 ? '0 attempts' : `${totalQuizzes} completed`}
            </p>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
            <Award className="w-6 h-6" />
          </div>
        </Card>

        {/* Topic Mastery */}
        <Card className="p-5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Average Mastery</p>
            <h3 className="text-2xl font-bold text-white tracking-tight">{averageMastery}</h3>
            <p className="text-xs text-slate-400">
              {totalQuizzes === 0 ? 'Awaiting first quiz' : 'Across evaluated topics'}
            </p>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
        </Card>

        {/* Questions Answered */}
        <Card className="p-5 flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Questions Answered</p>
            <h3 className="text-2xl font-bold text-white tracking-tight">{questionsAnswered}</h3>
            <p className="text-xs text-slate-400">
              {questionsAnswered === 0 ? 'Ready to practice' : 'Total evaluated'}
            </p>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
            <BookOpen className="w-6 h-6" />
          </div>
        </Card>
      </div>

      {/* Main Grid: Quick Study Workflows + Recent Items */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Action Centers & Materials */}
        <div className="lg:col-span-2 space-y-8">
          {/* Quick Actions Hub */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div
              onClick={() => navigate('/documents')}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 hover:bg-slate-900/90 transition-all cursor-pointer group shadow-lg"
            >
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Upload className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">
                Ingest PDF Notes
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Upload chapters, slides, or papers for semantic indexing.
              </p>
            </div>

            <div
              onClick={() => navigate('/chat')}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/40 hover:bg-slate-900/90 transition-all cursor-pointer group shadow-lg"
            >
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <MessageSquareText className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-semibold text-white group-hover:text-purple-300 transition-colors">
                Ask Study Material
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Source-aware explanations with page & chunk citations.
              </p>
            </div>

            <div
              onClick={() => navigate('/quiz')}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-emerald-500/40 hover:bg-slate-900/90 transition-all cursor-pointer group shadow-lg"
            >
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Award className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-semibold text-white group-hover:text-emerald-300 transition-colors">
                Test Knowledge
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Generate adaptive multiple-choice quizzes with server scoring.
              </p>
            </div>
          </div>

          {/* Recent Documents Table/List */}
          <Card
            title="Recent Study Materials"
            subtitle="Documents parsed for pgvector semantic search and AI retrieval"
            icon={FileText}
            action={
              <Link
                to="/documents"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                <span>View All</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            {loading ? (
              <Spinner size="md" label="Loading study materials..." />
            ) : documents.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No Documents Uploaded Yet"
                description="Upload lecture slides, textbook chapters, or syllabi. They will be chunked and embedded with Gemini for AI chat and quiz generation."
                actionText="Upload First Document"
                actionIcon={Upload}
                onAction={() => navigate('/documents')}
              />
            ) : (
              <div className="divide-y divide-slate-800/80">
                {documents.slice(0, 5).map((doc) => (
                  <div
                    key={doc.id || doc.filename}
                    className="py-3.5 flex items-center justify-between gap-4 group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="p-2 rounded-lg bg-slate-800 text-slate-300">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-200 truncate group-hover:text-indigo-400 transition-colors">
                          {doc.filename || doc.name}
                        </p>
                        <p className="text-xs text-slate-400">
                          {doc.file_size ? `${(doc.file_size / 1024 / 1024).toFixed(1)} MB • ` : ''}
                          {doc.chunks_count ? `${doc.chunks_count} chunks • ` : ''}
                          Uploaded {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'recently'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <Badge status={doc.status || 'Ready'} />
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate('/chat')}
                      >
                        Study
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right Col: Smart Study Assistant & Quizzes */}
        <div className="space-y-8">
          {/* Study Recommendations Card */}
          <Card
            title="Study Recommendations"
            subtitle="Personalized recommendations based on your mastery"
            icon={Sparkles}
            action={
              <Link
                to="/recommendations"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                <span>Details</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            {loading ? (
              <Spinner size="sm" label="Fetching recommendations..." />
            ) : (
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-slate-800/50 border border-slate-700/60 flex items-start gap-3">
                  <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 shrink-0 mt-0.5">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h5 className="text-xs font-semibold text-slate-200">
                      {totalDocuments === 0
                        ? 'Step 1: Ingest Course Material'
                        : totalQuizzes === 0
                        ? 'Step 2: Generate Knowledge Check'
                        : 'Review Weak Topics'}
                    </h5>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      {totalDocuments === 0
                        ? 'Upload your first course syllabus or lecture notes to get tailored study suggestions.'
                        : totalQuizzes === 0
                        ? 'Take a 5-question practice quiz to establish your baseline topic mastery.'
                        : 'Continue regular quizzes to maintain retention and identify gaps.'}
                    </p>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => navigate(totalDocuments === 0 ? '/documents' : '/quiz')}
                >
                  {totalDocuments === 0 ? 'Go to Documents' : 'Take Practice Quiz'}
                </Button>
              </div>
            )}
          </Card>

          {/* Recent Quizzes Card */}
          <Card
            title="Recent Quizzes"
            subtitle="Server-scored evaluation history"
            icon={Award}
            action={
              <Link
                to="/quiz"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                <span>All Quizzes</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            {loading ? (
              <Spinner size="sm" label="Loading quizzes..." />
            ) : quizzes.length === 0 ? (
              <EmptyState
                icon={Award}
                title="No Quizzes Yet"
                description="Test your understanding of uploaded documents with AI-generated quizzes."
                actionText="Create Quiz"
                onAction={() => navigate('/quiz')}
              />
            ) : (
              <div className="space-y-3">
                {quizzes.slice(0, 4).map((q) => (
                  <div
                    key={q.id}
                    className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 flex items-center justify-between"
                  >
                    <div>
                      <p className="text-xs font-semibold text-slate-200 truncate">{q.topic || 'General Practice'}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {q.difficulty || 'Medium'} • {q.num_questions || q.questions?.length || 5} questions
                      </p>
                    </div>
                    {q.score !== undefined && (
                      <span className="text-xs font-bold text-emerald-400">
                        {Math.round(q.score)}%
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
