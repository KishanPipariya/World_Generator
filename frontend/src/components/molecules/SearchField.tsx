import { Search } from 'lucide-react';
import type { InputHTMLAttributes } from 'react';

export function SearchField({ label, className, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className={className}>
      <Search size={16} aria-hidden="true" />
      <span className="sr-only">{label}</span>
      <input type="search" {...props} />
    </label>
  );
}
