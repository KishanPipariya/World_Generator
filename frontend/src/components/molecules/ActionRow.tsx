import type { ReactNode } from 'react';

export function ActionRow({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={['form-actions', className ?? ''].filter(Boolean).join(' ')}>{children}</div>;
}
