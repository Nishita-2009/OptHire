import React, { useEffect, useState } from 'react';
import { api, API_BASE_URL } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import {
  Database,
  Server,
  Cpu,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';

const AGENTS = [
  { id: 1, name: 'Resume Parser', model: 'gemini-2.5-flash', role: 'Extracts skills, experience & education from raw PDF resumes into structured JSON.' },
  { id: 2, name: 'Job Description Parser', model: 'gemini-2.5-flash', role: 'Extracts mandatory vs preferred skills and seniority criteria from raw job description text.' },
  { id: 3, name: 'Resume Matcher', model: 'gemini-2.5-flash', role: 'Evaluates candidate fit against job requirements and calculates evidence-based ATS scores.' },
  { id: 4, name: 'Skill Gap Analyzer', model: 'gemini-2.5-flash', role: 'Detects missing mandatory requirements and formulates prioritized upskilling timelines.' },
  { id: 5, name: 'Interview Generator', model: 'gemini-2.5-flash', role: 'Generates 21 personalized behavioral and technical questions based on qualifications and gaps.' },
  { id: 6, name: 'Interview Evaluator', model: 'gemini-2.5-flash', role: 'Evaluates candidate answers individually, assessing strengths, missing criteria, and final scores.' },
  { id: 7, name: 'Hiring Report Generator', model: 'gemini-2.5-flash', role: 'Synthesizes entire hiring journey into an authoritative executive decision report.' },
];

export function SettingsPage() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pingLatency, setPingLatency] = useState(null);

  const checkConnectivity = async () => {
    try {
      setLoading(true);
      setError(null);
      const start = performance.now();
      const res = await api.getHealth();
      const end = performance.now();
      setPingLatency(Math.round(end - start));
      setHealthData(res);
    } catch (err) {
      setError(err.message);
      setHealthData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkConnectivity();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Title */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
          System Settings & Platform Health
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          Inspect backend connectivity, database status, and operational multi-agent Gemini configurations.
        </p>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Backend Connectivity Status */}
      <Card>
        <CardHeader>
          <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Server size={20} color="var(--accent-600)" /> FastAPI Backend Connectivity
          </CardTitle>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <a
              href={`${API_BASE_URL}/docs`}
              target="_blank"
              rel="noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8125rem', color: 'var(--navy-600)', textDecoration: 'none', fontWeight: 600 }}
            >
              API Docs <ExternalLink size={13} />
            </a>
            <Button
              variant="outline"
              size="sm"
              icon={RefreshCw}
              isLoading={loading}
              onClick={checkConnectivity}
            >
              Ping Health
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            <div style={{ padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)' }}>
              <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>API BASE URL</small>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', marginTop: '0.25rem', fontFamily: 'var(--font-mono)' }}>
                {API_BASE_URL}
              </div>
            </div>

            <div style={{ padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)' }}>
              <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>STATUS</small>
              <div style={{ marginTop: '0.25rem' }}>
                <Badge variant={healthData?.status === 'healthy' || healthData?.status === 'ok' ? 'success' : 'danger'}>
                  {healthData?.status === 'healthy' || healthData?.status === 'ok' ? 'CONNECTED (HEALTHY)' : 'DISCONNECTED'}
                </Badge>
              </div>
            </div>

            <div style={{ padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)' }}>
              <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>LATENCY</small>
              <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--success-700)', marginTop: '0.25rem' }}>
                {pingLatency != null ? `${pingLatency} ms` : 'Checking...'}
              </div>
            </div>

            <div style={{ padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)' }}>
              <small style={{ color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Database size={13} /> DATABASE LAYER
              </small>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--navy-800)', marginTop: '0.25rem' }}>
                SQLite (opthire.db)
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 7 AI Agents Registry Card */}
      <Card>
        <CardHeader>
          <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={20} color="var(--navy-600)" /> AI Agents Operational Registry (7 Agents)
          </CardTitle>
          <Badge variant="primary">gemini-2.5-flash</Badge>
        </CardHeader>
        <CardContent style={{ padding: 0 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-card-subtle)' }}>
                  <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>AGENT</th>
                  <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>NAME</th>
                  <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>MODEL</th>
                  <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>RESPONSIBILITY & ROLE</th>
                  <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {AGENTS.map((agent) => (
                  <tr key={agent.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: 'var(--accent-600)' }}>
                      Agent {agent.id}
                    </td>
                    <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>
                      {agent.name}
                    </td>
                    <td style={{ padding: '0.85rem 1.25rem', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>
                      {agent.model}
                    </td>
                    <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-secondary)' }}>
                      {agent.role}
                    </td>
                    <td style={{ padding: '0.85rem 1.25rem' }}>
                      <Badge variant="success" size="sm" dot>Active</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default SettingsPage;
