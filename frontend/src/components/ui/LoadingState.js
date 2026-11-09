import React from 'react';
import { Loader2 } from 'lucide-react';

export function LoadingSpinner({ size = 28, text = 'Loading data...' }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 1rem',
        gap: '0.75rem',
        color: 'var(--text-muted)',
      }}
    >
      <Loader2 size={size} className="animate-spin" color="var(--accent-600)" />
      {text && <span style={{ fontSize: '0.875rem' }}>{text}</span>}
    </div>
  );
}

export function SkeletonRow({ count = 3, height = '48px' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          style={{
            height,
            backgroundColor: 'var(--neutral-100)',
            borderRadius: 'var(--radius-md)',
            animation: 'fadeIn 0.5s infinite alternate ease-in-out',
          }}
        />
      ))}
    </div>
  );
}

export default LoadingSpinner;
