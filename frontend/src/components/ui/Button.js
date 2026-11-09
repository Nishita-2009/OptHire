import React from 'react';
import { Loader2 } from 'lucide-react';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  icon: Icon,
  className = '',
  ...props
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 600,
    borderRadius: 'var(--radius-md)',
    transition: 'all var(--transition-fast)',
    gap: '0.5rem',
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: disabled || isLoading ? 0.65 : 1,
    whiteSpace: 'nowrap',
  };

  const variants = {
    primary: {
      backgroundColor: 'var(--accent-600)',
      color: 'var(--white)',
      border: '1px solid transparent',
      boxShadow: 'var(--shadow-sm)',
    },
    secondary: {
      backgroundColor: 'var(--neutral-100)',
      color: 'var(--neutral-800)',
      border: '1px solid var(--border)',
    },
    outline: {
      backgroundColor: 'transparent',
      color: 'var(--accent-600)',
      border: '1px solid var(--accent-500)',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: 'var(--neutral-600)',
      border: '1px solid transparent',
    },
    danger: {
      backgroundColor: 'var(--danger-600)',
      color: 'var(--white)',
      border: '1px solid transparent',
    },
    navy: {
      backgroundColor: 'var(--navy-900)',
      color: 'var(--white)',
      border: '1px solid var(--navy-800)',
    },
  };

  const sizes = {
    sm: { padding: '0.375rem 0.75rem', fontSize: '0.8125rem' },
    md: { padding: '0.55rem 1rem', fontSize: '0.9375rem' },
    lg: { padding: '0.75rem 1.5rem', fontSize: '1rem' },
  };

  return (
    <button
      style={{
        ...baseStyles,
        ...variants[variant],
        ...sizes[size],
      }}
      disabled={disabled || isLoading}
      className={className}
      {...props}
    >
      {isLoading ? (
        <Loader2 size={16} className="animate-spin" />
      ) : Icon ? (
        <Icon size={16} />
      ) : null}
      {children}
    </button>
  );
}

export default Button;
