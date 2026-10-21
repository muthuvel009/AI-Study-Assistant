import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Server,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Sliders,
  Trash2,
  Save,
  Database,
  Cpu,
} from 'lucide-react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';

export const Settings = () => {
  const { success, error, info } = useToast();

  const [backendUrl, setBackendUrl] = useState(
    import.meta.env.VITE_API_URL || 'http://localhost:8000'
  );
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null); // 'online' | 'offline'

  const [preferences, setPreferences] = useState({
    defaultDifficulty: 'Medium',
    defaultQuestionCount: 5,
    showCitationsByDefault: true,
    strictGroundedOnly: true,
    ambientSounds: false,
  });

  const checkConnection = async () => {
    setTestingConnection(true);
    try {
      const isOnline = await api.checkHealth();
      setConnectionStatus(isOnline ? 'online' : 'offline');
      if (isOnline) {
        success('FastAPI backend is responsive and healthy.');
      } else {
        info('FastAPI backend is offline (will be activated in Phase 2).');
      }
    } catch {
      setConnectionStatus('offline');
      info('Backend is offline. Running in Phase 1 frontend UI mode.');
    } finally {
      setTestingConnection(false);
    }
  };

  useEffect(() => {
    checkConnection();
  }, []);

  const handlePreferenceChange = (key, value) => {
    setPreferences((prev) => ({ ...prev, [key]: value }));
  };

  const handleSavePreferences = () => {
    localStorage.setItem('ai_study_preferences', JSON.stringify(preferences));
    success('Study preferences saved.');
  };

  const handleClearCache = () => {
    if (window.confirm('Clear all local offline storage and cached sessions?')) {
      localStorage.removeItem('ai_study_docs');
      localStorage.removeItem('ai_study_quizzes');
      success('Local temporary cache cleared.');
      window.location.reload();
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Platform Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Inspect backend architecture connectivity, configure AI tuning, and manage storage.
        </p>
      </div>

      <div className="space-y-6">
        {/* Backend & Architecture Status */}
        <Card
          title="Backend & AI Engine Architecture"
          subtitle="Verification of FastAPI, PostgreSQL pgvector, and Gemini connectivity"
          icon={Server}
          action={
            <Button
              variant="outline"
              size="sm"
              icon={RefreshCw}
              loading={testingConnection}
              onClick={checkConnection}
            >
              Test Connection
            </Button>
          }
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400">FastAPI API</span>
                  {connectionStatus === 'online' ? (
                    <Badge variant="success" dot>Online</Badge>
                  ) : (
                    <Badge variant="default" dot>Phase 1 Mode</Badge>
                  )}
                </div>
                <p className="text-xs font-mono text-slate-300 mt-2 truncate">{backendUrl}</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400">Database</span>
                  <Badge variant="indigo">PostgreSQL</Badge>
                </div>
                <p className="text-xs text-slate-300 mt-2">pgvector extension (Phase 2)</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400">AI Model</span>
                  <Badge variant="purple">Gemini API</Badge>
                </div>
                <p className="text-xs text-slate-300 mt-2">RAG & text-embedding-004</p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-500/20 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div className="text-xs text-slate-300 leading-relaxed">
                <strong>Phase 1 Architecture Status:</strong> The React + Vite frontend is running with an isolated API service layer. All endpoints are mapped to their respective FastAPI routes (<code className="bg-slate-900 px-1 py-0.5 rounded text-indigo-300">/api/auth</code>, <code className="bg-slate-900 px-1 py-0.5 rounded text-indigo-300">/api/documents</code>, <code className="bg-slate-900 px-1 py-0.5 rounded text-indigo-300">/api/chat</code>, <code className="bg-slate-900 px-1 py-0.5 rounded text-indigo-300">/api/quizzes</code>, <code className="bg-slate-900 px-1 py-0.5 rounded text-indigo-300">/api/progress</code>, <code className="bg-slate-900 px-1 py-0.5 rounded text-indigo-300">/api/recommendations</code>).
              </div>
            </div>
          </div>
        </Card>

        {/* Study Tuning Preferences */}
        <Card
          title="Study Tuning Preferences"
          subtitle="Adjust defaults for automated quiz generation and tutoring"
          icon={Sliders}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Default Quiz Difficulty
                </label>
                <select
                  value={preferences.defaultDifficulty}
                  onChange={(e) => handlePreferenceChange('defaultDifficulty', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="Easy">Easy (Foundation concepts)</option>
                  <option value="Medium">Medium (Application & reasoning)</option>
                  <option value="Hard">Hard (Deep edge cases & analysis)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Default Question Count
                </label>
                <select
                  value={preferences.defaultQuestionCount}
                  onChange={(e) => handlePreferenceChange('defaultQuestionCount', Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value={3}>3 Questions</option>
                  <option value={5}>5 Questions</option>
                  <option value={10}>10 Questions</option>
                  <option value={15}>15 Questions</option>
                </select>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <label className="flex items-center gap-3 p-3 rounded-xl bg-slate-950/40 border border-slate-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.showCitationsByDefault}
                  onChange={(e) => handlePreferenceChange('showCitationsByDefault', e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <div>
                  <div className="text-xs font-semibold text-slate-200">Automatically Expand Grounded Citations</div>
                  <div className="text-[11px] text-slate-400">Always reveal retrieved document chunks under AI tutor responses.</div>
                </div>
              </label>

              <label className="flex items-center gap-3 p-3 rounded-xl bg-slate-950/40 border border-slate-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.strictGroundedOnly}
                  onChange={(e) => handlePreferenceChange('strictGroundedOnly', e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <div>
                  <div className="text-xs font-semibold text-slate-200">Strict Source Grounding Only</div>
                  <div className="text-[11px] text-slate-400">Refuse answering concepts not found in your uploaded materials.</div>
                </div>
              </label>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                icon={Save}
                onClick={handleSavePreferences}
              >
                Save Preferences
              </Button>
            </div>
          </div>
        </Card>

        {/* Local Storage & Cache */}
        <Card
          title="Data Management"
          subtitle="Reset local client state or refresh auth sessions"
          icon={Database}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-rose-950/10 border border-rose-500/20">
            <div>
              <h5 className="text-xs font-semibold text-rose-300">Clear Local App Cache</h5>
              <p className="text-xs text-slate-400 mt-0.5">
                Removes locally stored preview documents and resets client mock state.
              </p>
            </div>
            <Button
              variant="danger"
              size="sm"
              icon={Trash2}
              onClick={handleClearCache}
            >
              Clear Cache
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Settings;
