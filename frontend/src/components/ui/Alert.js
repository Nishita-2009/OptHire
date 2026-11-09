import React from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';

export function Alert({
  variant = 'info',
  title,
  children,
  onClose,
  style = {},
  className = '',
}) {
  const configs = {
    info: {
      bg: 'var(--accent-50)',
      border: 'var(--accent-100)',
      color: 'var(--accent-600)',
      icon: Info,
    },
    success: {
      bg: 'var(--success-50)',
      border: 'var(--success-100)',
      color: 'var(--success-700)',
      icon: CheckCircle,
    },
    warning: {
      bg: 'var(--warning-50)',
      border: 'var(--warning-100)',
      color: 'var(--warning-700)',
      icon: AlertTriangle,
    },
    danger: {
      bg: 'var(--danger-50)',
      border: 'var(--danger-100)',
      color: 'var(--danger-700)',
      icon: AlertCircle,
    },
  };

  const config = configs[variant] || configs.info;
  const Icon = config.icon;

  return (
    <div
      style={{
        backgroundColor: config.bg,
        border: `1px solid ${config.border}`,
        borderRadius: 'var(--radius-md)',
        padding: '0.875rem 1rem',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        ...style,
      }}
      className={className}
      role="alert"
    >
      <Icon size={18} color={config.color} style={{ flexShrink: 0, marginTop: '2px' }} />
      <div style={{ flex: 1, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
        {title && <strong style={{ display: 'block', marginBottom: '0.2rem', color: config.color }}>{title}</strong>}
        {children}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            padding: '0.2rem',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          aria-label="Dismiss alert"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

export default Alert;
