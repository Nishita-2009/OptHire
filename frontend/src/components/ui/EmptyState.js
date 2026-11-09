import React from 'react';
import { Button } from './Button';

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  actionIcon,
  style = {},
}) {
  return (
    <div
      style={{
        padding: '3.5rem 1.5rem',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        border: '1px dashed var(--border)',
        ...style,
      }}
    >
      {Icon && (
        <div
          style={{
            width: '52px',
            height: '52px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--neutral-100)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1rem',
            color: 'var(--text-muted)',
          }}
        >
          <Icon size={26} />
        </div>
      )}
      <h4 style={{ margin: '0 0 0.35rem 0', fontWeight: 700, color: 'var(--text-primary)' }}>
        {title}
      </h4>
      <p style={{ margin: '0 0 1.25rem 0', maxWidth: '380px', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
        {description}
      </p>
      {actionLabel && onAction && (
        <Button onClick={onAction} icon={actionIcon} variant="primary" size="md">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;
