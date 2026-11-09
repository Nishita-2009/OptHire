import React from 'react';

export function Card({ children, className = '', style = {}, hoverable = false, ...props }) {
  const cardStyle = {
    backgroundColor: 'var(--bg-card)',
    borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border)',
    boxShadow: 'var(--shadow-sm)',
    overflow: 'hidden',
    transition: 'all var(--transition-fast)',
    ...(hoverable ? { cursor: 'pointer' } : {}),
    ...style,
  };

  return (
    <div style={cardStyle} className={className} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ children, style = {}, className = '', ...props }) {
  return (
    <div
      style={{
        padding: '1.25rem 1.5rem',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        ...style,
      }}
      className={className}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, style = {}, className = '', ...props }) {
  return (
    <h3
      style={{
        margin: 0,
        fontSize: '1.125rem',
        fontWeight: 700,
        color: 'var(--text-primary)',
        ...style,
      }}
      className={className}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ children, style = {}, className = '', ...props }) {
  return (
    <p
      style={{
        margin: '0.25rem 0 0 0',
        fontSize: '0.875rem',
        color: 'var(--text-muted)',
        ...style,
      }}
      className={className}
      {...props}
    >
      {children}
    </p>
  );
}

export function CardContent({ children, style = {}, className = '', ...props }) {
  return (
    <div
      style={{
        padding: '1.5rem',
        ...style,
      }}
      className={className}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardFooter({ children, style = {}, className = '', ...props }) {
  return (
    <div
      style={{
        padding: '1rem 1.5rem',
        backgroundColor: 'var(--bg-card-subtle)',
        borderTop: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: '0.75rem',
        ...style,
      }}
      className={className}
      {...props}
    >
      {children}
    </div>
  );
}

export default Card;
