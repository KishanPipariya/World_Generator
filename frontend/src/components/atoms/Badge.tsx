import type { HTMLAttributes } from 'react';

type BadgeVariant = 'default' | 'primary' | 'good' | 'muted';

export function Badge({ className, variant = 'default', ...props }: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  const variantClass = variant === 'default' ? '' : `badge-${variant}`;
  return <span className={['badge', variantClass, className ?? ''].filter(Boolean).join(' ')} {...props} />;
}
