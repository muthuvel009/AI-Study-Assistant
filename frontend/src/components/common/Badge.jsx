import React from 'react';
import { Loader2, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';

export const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
  status, // 'Processing' | 'Ready' | 'Failed'
}) => {
  // If status is provided, auto-map to standard styling
  let resolvedVariant = variant;
  let statusIcon = null;

  if (status) {
    const s = String(status).toLowerCase();
    if (s === 'ready') {
      resolvedVariant = 'success';
      statusIcon = <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />;
    } else if (s === 'processing') {
      resolvedVariant = 'warning';
      statusIcon = <Loader2 className="w-3 h-3 text-amber-400 animate-spin shrink-0" />;
    } else if (s === 'failed') {
      resolvedVariant = 'danger';
      statusIcon = <AlertCircle className="w-3 h-3 text-rose-400 shrink-0" />;
    }
  }

  const variants = {
    default: 'bg-slate-800 text-slate-300 border-slate-700',
    indigo: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
    purple: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    ai: 'bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-indigo-200 border-indigo-400/30',
  };

  const sizes = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3 py-1.5 gap-2',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${variants[resolvedVariant] || variants.default} ${sizes[size] || sizes.md} ${className}`}
    >
      {statusIcon}
      {dot && !statusIcon && (
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      )}
      <span>{children || status}</span>
    </span>
  );
};

export default Badge;
