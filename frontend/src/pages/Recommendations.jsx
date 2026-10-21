import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  AlertTriangle,
  RotateCcw,
  BookOpen,
  ArrowRight,
  TrendingDown,
  CheckCircle2,
  Clock,
  Compass,
  Award,
  MessageSquareText,
} from 'lucide-react';
import recommendationService from '../services/recommendationService';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';
import Spinner from '../components/common/Spinner';

export const Recommendations = () => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        const data = await recommendationService.getRecommendations();
        if (mounted) {
          setRecommendations(Array.isArray(data) ? data : data?.recommendations || []);
        }
      } catch (err) {
        setRecommendations([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchRecommendations();
    return () => {
      mounted = false;
    };
  }, []);

  const getPriorityBadge = (priority) => {
    switch ((priority || '').toLowerCase()) {
      case 'high':
        return <Badge variant="danger" dot>High Priority</Badge>;
      case 'medium':
        return <Badge variant="warning" dot>Medium Priority</Badge>;
      default:
        return <Badge variant="indigo" dot>Study Suggestion</Badge>;
    }
  };

  const getTypeIcon = (type) => {
    const clean = (type || '').toLowerCase();
    switch (clean) {
      case 'revision':
      case 'low_mastery':
      case 'revision_needed':
        return <TrendingDown className="w-5 h-5 text-rose-400" />;
      case 'practice':
      case 'quiz':
        return <Award className="w-5 h-5 text-amber-400" />;
      case 'continue learning':
      case 'continue_learning':
        return <Sparkles className="w-5 h-5 text-emerald-400" />;
      default:
        return <Sparkles className="w-5 h-5 text-indigo-400" />;
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Personalized Study Plan</h1>
          <p className="text-sm text-slate-400 mt-1">
            Algorithmic study recommendations derived from low mastery, incorrect quiz answers, and concept recency.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="p-12 flex justify-center">
          <Spinner size="lg" label="Analyzing learning gaps..." />
        </div>
      ) : recommendations.length === 0 ? (
        <EmptyState
          icon={Compass}
          title="No Learning Recommendations Yet"
          description="Your personalized study plan builds automatically as you complete quizzes and identify concepts that need revision."
          actionText="Take a Practice Quiz"
          actionIcon={Award}
          onAction={() => navigate('/quiz')}
          secondaryActionText="Upload Course Notes"
          onSecondaryAction={() => navigate('/documents')}
        />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec, idx) => (
              <Card
                key={rec.id || idx}
                className="p-6 flex flex-col justify-between hover:border-slate-700 transition-all"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
                        {getTypeIcon(rec.recommendation_type || rec.type)}
                      </div>
                      <div>
                        <h4 className="text-base font-semibold text-slate-100">{rec.topic}</h4>
                        <span className="text-xs text-slate-400">{rec.subject || 'Course Topic'}</span>
                      </div>
                    </div>
                    {getPriorityBadge(rec.priority)}
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-slate-800/80">
                    {rec.reason}
                  </p>
                </div>

                <div className="flex items-center gap-2 pt-5 mt-4 border-t border-slate-800/80">
                  <Button
                    size="sm"
                    variant="primary"
                    icon={Award}
                    className="flex-1 text-xs"
                    onClick={() => navigate('/quiz', { state: { topic: rec.topic } })}
                  >
                    {rec.action_label || 'Practice Quiz'}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    icon={MessageSquareText}
                    className="text-xs"
                    onClick={() => navigate('/chat', { state: { topic: rec.topic } })}
                  >
                    Ask Tutor
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Recommendations;
