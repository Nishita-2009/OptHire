import React from 'react';

export function Badge({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  className = '',
  style = {},
  ...props
}) {
  const variants = {
    neutral: {
      backgroundColor: 'var(--neutral-100)',
      color: 'var(--neutral-700)',
      border: '1px solid var(--neutral-200)',
    },
    primary: {
      backgroundColor: 'var(--accent-50)',
      color: 'var(--accent-600)',
      border: '1px solid var(--accent-100)',
    },
    success: {
      backgroundColor: 'var(--success-50)',
      color: 'var(--success-700)',
      border: '1px solid var(--success-100)',
    },
    warning: {
      backgroundColor: 'var(--warning-50)',
      color: 'var(--warning-700)',
      border: '1px solid var(--warning-100)',
    },
    danger: {
      backgroundColor: 'var(--danger-50)',
      color: 'var(--danger-700)',
      border: '1px solid var(--danger-100)',
    },
    navy: {
      backgroundColor: 'var(--navy-50)',
      color: 'var(--navy-800)',
      border: '1px solid var(--navy-100)',
    },
  };

  const sizes = {
    sm: { padding: '0.125rem 0.45rem', fontSize: '0.6875rem' },
    md: { padding: '0.2rem 0.6rem', fontSize: '0.75rem' },
    lg: { padding: '0.35rem 0.85rem', fontSize: '0.8125rem' },
  };

  const currentVariant = variants[variant] || variants.neutral;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
        fontWeight: 600,
        borderRadius: 'var(--radius-full)',
        textTransform: 'none',
        lineHeight: 1.2,
        ...currentVariant,
        ...sizes[size],
        ...style,
      }}
      className={className}
      {...props}
    >
      {dot && (
        <span
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: 'currentColor',
          }}
        />
      )}
      {children}
    </span>
  );
}

export function ScoreBadge({ score, label, size = 'md' }) {
  let variant = 'neutral';
  const numericScore = typeof score === 'number' ? score : parseFloat(score) || 0;

  if (numericScore >= 80) variant = 'success';
  else if (numericScore >= 60) variant = 'warning';
  else variant = 'danger';

  return (
    <Badge variant={variant} size={size}>
      {label ? `${label}: ` : ''}
      <strong>{numericScore}%</strong>
    </Badge>
  );
}

export default Badge;
