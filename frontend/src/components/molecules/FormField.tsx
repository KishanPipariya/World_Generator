import type { ReactNode } from 'react';

export function FormField({ label, children, className }: {
  label: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <label className={['field-label', className ?? ''].filter(Boolean).join(' ')}>
      <span>{label}</span>
      {children}
    </label>
  );
}
