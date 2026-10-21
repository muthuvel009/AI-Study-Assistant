import React from 'react';

export const Card = ({
  children,
  className = '',
  title,
  subtitle,
  icon: Icon,
  action,
  hoverable = false,
  glass = true,
  onClick,
  ...props
}) => {
  const baseClasses = `rounded-2xl transition-all duration-200 overflow-hidden ${
    glass
      ? 'bg-slate-900/60 backdrop-blur-md border border-slate-800/80 shadow-xl'
      : 'bg-slate-900 border border-slate-800 shadow-md'
  } ${hoverable ? 'hover:border-slate-700 hover:shadow-indigo-500/5 hover:-translate-y-0.5 cursor-pointer' : ''} ${className}`;

  return (
    <div className={baseClasses} onClick={onClick} {...props}>
      {(title || subtitle || action || Icon) && (
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800/60">
          <div className="flex items-center gap-3">
            {Icon && (
              <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Icon className="w-5 h-5" />
              </div>
            )}
            <div>
              {title && <h3 className="text-base font-semibold text-slate-100 tracking-tight">{title}</h3>}
              {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
            </div>
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
};

export default Card;
