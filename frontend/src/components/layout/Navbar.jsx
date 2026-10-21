import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Menu, ShieldCheck, Sparkles, User, Settings, Database, Activity } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

const routeTitles = {
  '/': { title: 'Dashboard', category: 'Study Hub' },
  '/documents': { title: 'Study Materials', category: 'Documents & Syllabi' },
  '/chat': { title: 'Grounded AI Tutor', category: 'Semantic RAG Chat' },
  '/quiz': { title: 'Adaptive Practice Quizzes', category: 'Evaluation' },
  '/progress': { title: 'Learning Analytics', category: 'Mastery Tracking' },
  '/recommendations': { title: 'Smart Recommendations', category: 'Personalized Plan' },
  '/profile': { title: 'Student Profile', category: 'Academic Details' },
  '/settings': { title: 'Platform Settings', category: 'Preferences' },
};

export const Navbar = ({ onOpenSidebar }) => {
  const location = useLocation();
  const { user } = useAuth();
  const [backendOnline, setBackendOnline] = useState(false);
  const [checkingBackend, setCheckingBackend] = useState(true);

  const routeMeta = routeTitles[location.pathname] || {
    title: 'Study Assistant',
    category: 'Portal',
  };

  useEffect(() => {
    let mounted = true;
    const testConnection = async () => {
      try {
        const ok = await api.checkHealth();
        if (mounted) {
          setBackendOnline(ok);
          setCheckingBackend(false);
        }
      } catch {
        if (mounted) {
          setBackendOnline(false);
          setCheckingBackend(false);
        }
      }
    };

    testConnection();
    const interval = setInterval(testConnection, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 h-20 bg-slate-900/80 backdrop-blur-xl border-b border-slate-800/80 px-4 sm:px-8 flex items-center justify-between">
      {/* Left section: Hamburger & Breadcrumb */}
      <div className="flex items-center gap-4">
        <button
          onClick={onOpenSidebar}
          className="lg:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400">
            {routeMeta.category}
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
            {routeMeta.title}
          </h2>
        </div>
      </div>

      {/* Right section: System status badges & student avatar */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Grounded RAG pill */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
          <span>RAG Grounded</span>
        </div>

        {/* Backend health status badge */}
        <div
          title={
            backendOnline
              ? 'FastAPI + PostgreSQL Backend Connected'
              : 'Backend not running yet (Phase 1 UI Mode)'
          }
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium border ${
            backendOnline
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-slate-800/80 text-slate-400 border-slate-700/60'
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
            }`}
          />
          <span className="hidden sm:inline">
            {checkingBackend
              ? 'Checking...'
              : backendOnline
              ? 'API Online'
              : 'Phase 1 Frontend'}
          </span>
        </div>

        {/* Quick links to Profile */}
        <Link
          to="/profile"
          className="flex items-center gap-2 p-1.5 sm:px-3 sm:py-1.5 rounded-xl hover:bg-slate-800/60 border border-transparent hover:border-slate-700/60 transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 font-bold text-xs flex items-center justify-center">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <span className="hidden md:inline text-xs font-medium text-slate-200">
            {user?.full_name || 'Student'}
          </span>
        </Link>
      </div>
    </header>
  );
};

export default Navbar;
