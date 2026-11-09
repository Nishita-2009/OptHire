import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '../../services/api';
import { Activity, CheckCircle2, XCircle } from 'lucide-react';

const pageTitles = {
  '/dashboard': 'Executive Overview',
  '/candidates': 'Candidate Directory & Profiles',
  '/jobs': 'Job Openings & Requirements',
  '/analysis': 'Resume Matching & Gap Analysis',
  '/interviews': 'AI Interview Sessions',
  '/reports': 'Executive Hiring Reports',
  '/settings': 'System Settings & Connectivity',
};

export function TopNav() {
  const location = useLocation();
  const [backendHealth, setBackendHealth] = useState({ status: 'checking', message: 'Checking...' });

  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        const res = await api.getHealth();
        if (isMounted) {
          if (res && res.status === 'healthy') {
            setBackendHealth({ status: 'healthy', message: 'Backend Connected' });
          } else {
            setBackendHealth({ status: 'degraded', message: 'Degraded' });
          }
        }
      } catch (err) {
        if (isMounted) {
          setBackendHealth({ status: 'offline', message: 'Backend Offline' });
        }
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const currentTitle = pageTitles[location.pathname] || 'OptHire Platform';

  return (
    <header
      style={{
        height: '64px',
        backgroundColor: 'var(--bg-card)',
        borderBottom: '1px solid var(--border)',
        padding: '0 2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 30,
      }}
    >
      <div>
        <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
          {currentTitle}
        </h1>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Backend Connectivity Status Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.35rem 0.75rem',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.75rem',
            fontWeight: 600,
            backgroundColor:
              backendHealth.status === 'healthy'
                ? 'var(--success-50)'
                : backendHealth.status === 'offline'
                ? 'var(--danger-50)'
                : 'var(--neutral-100)',
            color:
              backendHealth.status === 'healthy'
                ? 'var(--success-700)'
                : backendHealth.status === 'offline'
                ? 'var(--danger-700)'
                : 'var(--neutral-600)',
            border: `1px solid ${
              backendHealth.status === 'healthy'
                ? 'var(--success-100)'
                : backendHealth.status === 'offline'
                ? 'var(--danger-100)'
                : 'var(--neutral-200)'
            }`,
          }}
          title="OptHire FastAPI Backend Health"
        >
          {backendHealth.status === 'healthy' ? (
            <CheckCircle2 size={13} color="var(--success-600)" />
          ) : backendHealth.status === 'offline' ? (
            <XCircle size={13} color="var(--danger-600)" />
          ) : (
            <Activity size={13} className="animate-spin" />
          )}
          <span>{backendHealth.message}</span>
        </div>
      </div>
    </header>
  );
}

export default TopNav;
