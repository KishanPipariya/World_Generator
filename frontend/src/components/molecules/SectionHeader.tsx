import type { ReactNode } from 'react';

export function SectionHeader({ icon, title, children, className }: {
  icon?: ReactNode;
  title: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div className={['section-header', className ?? ''].filter(Boolean).join(' ')}>
      {icon}
      <h2>{title}</h2>
      {children}
    </div>
  );
}
