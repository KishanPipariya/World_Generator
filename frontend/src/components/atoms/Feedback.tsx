import type { ReactNode } from 'react';

export function LoadingState({ children }: { children: ReactNode }) {
  return <div className="loading-state" role="status">{children}</div>;
}

export function Alert({ children, tone = 'error' }: { children: ReactNode; tone?: 'error' | 'success' }) {
  return (
    <div
      className={`workspace-alert ${tone}`}
      role={tone === 'error' ? 'alert' : 'status'}
      aria-live={tone === 'error' ? 'assertive' : 'polite'}
    >
      {children}
    </div>
  );
}

export function EmptyState({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={['empty-state', className ?? ''].filter(Boolean).join(' ')} role="status">{children}</div>;
}
