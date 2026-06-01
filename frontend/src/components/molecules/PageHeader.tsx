import type { ReactNode } from 'react';

export function PageHeader({
  title,
  subtitle,
  kicker,
  actions,
  className,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  kicker?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header className={className}>
      <div>
        {kicker && <p className="dashboard-kicker">{kicker}</p>}
        <h1>{title}</h1>
        {subtitle && <p className="text-secondary dashboard-subtitle">{subtitle}</p>}
      </div>
      {actions}
    </header>
  );
}
