import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Link, type LinkProps } from 'react-router-dom';

type ButtonVariant = 'primary' | 'secondary' | 'danger';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  compact?: boolean;
};

type ButtonLinkProps = LinkProps & {
  variant?: ButtonVariant;
  compact?: boolean;
  children: ReactNode;
};

const classNames = (variant: ButtonVariant, compact?: boolean, className?: string) => [
  'btn',
  `btn-${variant}`,
  compact ? 'compact-button' : '',
  className ?? '',
].filter(Boolean).join(' ');

export function Button({
  variant = 'secondary',
  compact,
  className,
  type = 'button',
  ...props
}: ButtonProps) {
  return <button className={classNames(variant, compact, className)} type={type} {...props} />;
}

export function ButtonLink({
  variant = 'secondary',
  compact,
  className,
  ...props
}: ButtonLinkProps) {
  return <Link className={classNames(variant, compact, className)} {...props} />;
}
