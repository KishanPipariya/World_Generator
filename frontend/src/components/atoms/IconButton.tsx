import type { ButtonHTMLAttributes } from 'react';

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  danger?: boolean;
};

export function IconButton({ className, danger, type = 'button', ...props }: IconButtonProps) {
  return (
    <button
      className={['icon-button', danger ? 'danger' : '', className ?? ''].filter(Boolean).join(' ')}
      type={type}
      {...props}
    />
  );
}
