import React from 'react';

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  color?: 'blue' | 'green' | 'purple' | 'yellow' | 'red';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color = 'blue',
}) => {
  const colorClasses = {
    blue: 'bg-brand-secondary border-brand-accent/20 text-brand-accent',
    green: 'bg-brand-secondary border-emerald-500/20 text-emerald-400',
    purple: 'bg-brand-secondary border-purple-500/20 text-purple-400',
    yellow: 'bg-brand-secondary border-amber-500/20 text-amber-400',
    red: 'bg-brand-secondary border-red-500/20 text-red-400',
  };

  return (
    <div
      className={`p-5 rounded-xl border ${colorClasses[color]} shadow-lg hover:shadow-xl transition-all duration-300`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-70 text-slate-400 mb-1">
            {title}
          </p>
          <p className="text-3xl font-bold mb-1 text-white">{value}</p>
          {subtitle && <p className="text-xs opacity-60 text-slate-300">{subtitle}</p>}
        </div>
        {icon && <div className="text-3xl opacity-80 ml-3">{icon}</div>}
      </div>
    </div>
  );
};
