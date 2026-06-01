import { Filter } from 'lucide-react';
import type { SelectHTMLAttributes } from 'react';

export function FilterSelect({
  label,
  children,
  className,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <label className={className}>
      <Filter size={16} aria-hidden="true" />
      <span>{label}</span>
      <select {...props}>{children}</select>
    </label>
  );
}
