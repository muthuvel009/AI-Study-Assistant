import React from 'react';
import { useNavigate } from 'react-router-dom';
import { HelpCircle, ArrowLeft } from 'lucide-react';
import Button from '../components/common/Button';

export const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6">
      <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4">
        <HelpCircle className="w-8 h-8" />
      </div>
      <h2 className="text-3xl font-extrabold text-white">404 - Page Not Found</h2>
      <p className="text-sm text-slate-400 max-w-sm mt-2 mb-6">
        The study resource or page you are looking for does not exist in your academic workspace.
      </p>
      <Button
        variant="primary"
        icon={ArrowLeft}
        onClick={() => navigate('/')}
      >
        Return to Dashboard
      </Button>
    </div>
  );
};

export default NotFound;
