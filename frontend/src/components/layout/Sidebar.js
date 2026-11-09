import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Briefcase,
  GitCompare,
  MessageSquareText,
  FileText,
  Settings,
  Sparkles,
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Candidates', path: '/candidates', icon: Users },
  { name: 'Job Openings', path: '/jobs', icon: Briefcase },
  { name: 'Matching Analysis', path: '/analysis', icon: GitCompare },
  { name: 'AI Interviews', path: '/interviews', icon: MessageSquareText },
  { name: 'Hiring Reports', path: '/reports', icon: FileText },
  { name: 'Settings & Health', path: '/settings', icon: Settings },
];

export function Sidebar({ isOpen, onClose }) {
  return (
    <aside
      style={{
        width: '260px',
        backgroundColor: 'var(--bg-sidebar)',
        color: 'var(--text-inverse)',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        zIndex: 40,
        height: '100vh',
        position: 'sticky',
        top: 0,
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          padding: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.35)',
          }}
        >
          <Sparkles size={20} color="#ffffff" />
        </div>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.03em', color: '#ffffff', margin: 0 }}>
            OptHire
          </h2>
          <small style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '0.75rem', display: 'block' }}>
            AI Recruitment Intelligence
          </small>
        </div>
      </div>

      {/* Nav Menu */}
      <nav
        style={{
          flex: 1,
          padding: '1.25rem 0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem',
          overflowY: 'auto',
        }}
      >
        <div style={{ padding: '0 0.75rem 0.5rem', fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'rgba(255, 255, 255, 0.4)' }}>
          Core Pipeline
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'rgba(255, 255, 255, 0.65)',
                backgroundColor: isActive ? 'var(--bg-sidebar-active)' : 'transparent',
                textDecoration: 'none',
                transition: 'all var(--transition-fast)',
                borderLeft: isActive ? '3px solid var(--accent-500)' : '3px solid transparent',
              })}
            >
              <Icon size={18} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div
        style={{
          padding: '1rem 1.25rem',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          backgroundColor: 'rgba(0, 0, 0, 0.15)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />
          <span style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.75)' }}>
            7 AI Agents Active
          </span>
        </div>
        <small style={{ color: 'rgba(255, 255, 255, 0.4)', fontSize: '0.6875rem', display: 'block', marginTop: '2px' }}>
          Phase 4 • FastAPI Connected
        </small>
      </div>
    </aside>
  );
}

export default Sidebar;
