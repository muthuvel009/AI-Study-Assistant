import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  TrendingUp,
  Award,
  BookOpen,
  Calendar,
  Sparkles,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  Filter,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  CartesianGrid,
} from 'recharts';
import progressService from '../services/progressService';
import quizService from '../services/quizService';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';
import Spinner from '../components/common/Spinner';

export const Progress = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [quizzes, setQuizzes] = useState([]);

  useEffect(() => {
    let mounted = true;
    const loadProgress = async () => {
      try {
        setLoading(true);
        // Load summary
        try {
          const sumData = await progressService.getProgressSummary();
          if (mounted) setSummary(sumData);
        } catch {
          if (mounted) setSummary(null);
        }

        // Load quizzes for history chart
        try {
          const qData = await quizService.getQuizzes();
          if (mounted) {
            setQuizzes(Array.isArray(qData) ? qData : qData?.quizzes || []);
          }
        } catch {
          if (mounted) setQuizzes([]);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadProgress();
    return () => {
      mounted = false;
    };
  }, []);

  const totalQuestions = summary?.total_questions_answered || 0;
  const correctAnswers = summary?.correct_answers || 0;
  const averageMastery = summary?.average_mastery !== undefined ? Math.round(summary.average_mastery) : 0;
  const topicBreakdown = summary?.topics || [];

  // Prepare chart data from completed quizzes
  const scoredQuizzes = quizzes
    .filter((q) => q.score !== undefined)
    .map((q, idx) => ({
      name: `Quiz ${idx + 1}`,
      score: Math.round(q.score),
      topic: q.topic || 'General',
      date: q.created_at ? new Date(q.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' }) : `Attempt ${idx + 1}`,
    }));

  const hasLearningData = scoredQuizzes.length > 0 || topicBreakdown.length > 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Learning Analytics & Mastery</h1>
          <p className="text-sm text-slate-400 mt-1">
            Track concept retention, topic mastery progression, and quiz scoring over time.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          icon={Sparkles}
          onClick={() => navigate('/quiz')}
        >
          Practice Weak Topics
        </Button>
      </div>

      {/* KPI Metric Summary (Authentic, no fake stats) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall Topic Mastery</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-white">{averageMastery}%</span>
            <span className="text-xs text-slate-400">weighted avg</span>
          </div>
          <div className="w-full h-1.5 bg-slate-800 rounded-full mt-3 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400"
              style={{ width: `${averageMastery}%` }}
            />
          </div>
        </Card>

        <Card className="p-5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Evaluated Questions</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-white">{totalQuestions}</span>
            <span className="text-xs text-slate-400">total questions</span>
          </div>
          <p className="text-xs text-slate-400 mt-3">
            {correctAnswers} correct ({totalQuestions > 0 ? Math.round((correctAnswers / totalQuestions) * 100) : 0}% accuracy)
          </p>
        </Card>

        <Card className="p-5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Quizzes Evaluated</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-white">{scoredQuizzes.length}</span>
            <span className="text-xs text-slate-400">completed</span>
          </div>
          <p className="text-xs text-slate-400 mt-3">
            {quizzes.length - scoredQuizzes.length} drafts / pending
          </p>
        </Card>

        <Card className="p-5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Topics</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-white">{topicBreakdown.length}</span>
            <span className="text-xs text-slate-400">tracked concepts</span>
          </div>
          <p className="text-xs text-slate-400 mt-3">
            Indexed across course PDFs
          </p>
        </Card>
      </div>

      {loading ? (
        <div className="p-12 flex justify-center">
          <Spinner size="lg" label="Computing mastery analytics..." />
        </div>
      ) : !hasLearningData ? (
        <EmptyState
          icon={BarChart3}
          title="No Learning Activity Recorded Yet"
          description="Progress metrics, accuracy rates, and performance trends will appear here once you take your first quiz."
          actionText="Take Your First Quiz"
          actionIcon={Award}
          onAction={() => navigate('/quiz')}
          secondaryActionText="Upload Study Material"
          onSecondaryAction={() => navigate('/documents')}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Performance Timeline Chart */}
          <Card
            title="Score Progression"
            subtitle="Historical quiz accuracy (%) across study sessions"
            icon={TrendingUp}
          >
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={scoredQuizzes}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '12px',
                      color: '#f8fafc',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#6366f1"
                    strokeWidth={3}
                    dot={{ fill: '#818cf8', r: 5 }}
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Topic Mastery Distribution */}
          <Card
            title="Topic Mastery Breakdown"
            subtitle="Calculated retention across assessed academic subjects"
            icon={BarChart3}
          >
            {topicBreakdown.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-center p-4">
                <p className="text-sm text-slate-400">
                  Topic mastery levels will populate as you complete quizzes on specific concepts.
                </p>
              </div>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topicBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                    <XAxis dataKey="topic" stroke="#94a3b8" fontSize={11} />
                    <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        borderRadius: '12px',
                        color: '#f8fafc',
                      }}
                    />
                    <Bar dataKey="mastery_score" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          {/* Granular Topic Breakdown Table */}
          <div className="lg:col-span-2">
            <Card
              title="Subject Mastery Index"
              subtitle="Topic-by-topic analytics with attempts, scores, and last review dates"
              icon={BookOpen}
            >
              {topicBreakdown.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-6">
                  No individual topic records found. Complete a quiz to index topic mastery.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
                        <th className="py-3 px-4">Topic / Concept</th>
                        <th className="py-3 px-4">Attempts</th>
                        <th className="py-3 px-4">Latest Score</th>
                        <th className="py-3 px-4">Average Score</th>
                        <th className="py-3 px-4">Mastery</th>
                        <th className="py-3 px-4">Last Studied</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {topicBreakdown.map((t, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-3 px-4 font-medium text-slate-100">{t.topic}</td>
                          <td className="py-3 px-4 text-slate-300">{t.quiz_attempts || 1}</td>
                          <td className="py-3 px-4 text-slate-300">{Math.round(t.latest_score || 0)}%</td>
                          <td className="py-3 px-4 text-slate-300">{Math.round(t.average_score || 0)}%</td>
                          <td className="py-3 px-4">
                            <span
                              className={`font-semibold ${
                                (t.mastery_score || 0) >= 80
                                  ? 'text-emerald-400'
                                  : (t.mastery_score || 0) >= 60
                                  ? 'text-amber-400'
                                  : 'text-rose-400'
                              }`}
                            >
                              {Math.round(t.mastery_score || 0)}%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-400 text-xs">
                            {t.last_studied ? new Date(t.last_studied).toLocaleDateString() : 'Recent'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default Progress;
