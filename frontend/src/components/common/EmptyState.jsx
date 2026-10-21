import React from 'react';
import Button from './Button';

export const EmptyState = ({
  icon: Icon,
  title,
  description,
  actionText,
  onAction,
  actionIcon,
  className = '',
  secondaryActionText,
  onSecondaryAction,
}) => {
  return (
    <div className={`flex flex-col items-center justify-center text-center p-8 sm:p-12 rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 backdrop-blur-sm ${className}`}>
      {Icon && (
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 shadow-inner">
          <Icon className="w-8 h-8" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-slate-100 tracking-tight">{title}</h3>
      <p className="text-sm text-slate-400 max-w-md mt-2 mb-6 leading-relaxed">
        {description}
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        {actionText && onAction && (
          <Button
            variant="primary"
            icon={actionIcon}
            onClick={onAction}
          >
            {actionText}
          </Button>
        )}
        {secondaryActionText && onSecondaryAction && (
          <Button
            variant="outline"
            onClick={onSecondaryAction}
          >
            {secondaryActionText}
          </Button>
        )}
      </div>
    </div>
  );
};

export default EmptyState;
