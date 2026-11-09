import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { LoadingSpinner } from '../components/ui/LoadingState';
import { Alert } from '../components/ui/Alert';
import {
  Users,
  Briefcase,
  FileCheck2,
  ArrowRight,
  UserPlus,
  Play,
  TrendingUp,
} from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    candidatesCount: 0,
    jobsCount: 0,
    recentCandidates: [],
    recentJobs: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        setLoading(true);
        const [candidatesRes, jobsRes] = await Promise.all([
          api.getCandidates(0, 5).catch(() => ({ total: 0, candidates: [] })),
          api.getJobs(0, 5).catch(() => ({ total: 0, jobs: [] })),
        ]);

        setStats({
          candidatesCount: candidatesRes.total || 0,
          jobsCount: jobsRes.total || 0,
          recentCandidates: candidatesRes.candidates || [],
          recentJobs: jobsRes.jobs || [],
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Welcome Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, var(--navy-900) 0%, var(--navy-800) 100%)',
          color: 'var(--white)',
          padding: '2rem 2.5rem',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div>
          <Badge variant="primary" style={{ marginBottom: '0.75rem', backgroundColor: 'rgba(37, 99, 235, 0.3)', color: '#93c5fd', border: 'none' }}>
            Autonomous AI Recruitment Pipeline
          </Badge>
          <h2 style={{ color: 'var(--white)', fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.5rem 0' }}>
            Welcome to OptHire
          </h2>
          <p style={{ color: 'rgba(255, 255, 255, 0.75)', maxWidth: '600px', margin: 0, fontSize: '0.95rem' }}>
            Evaluate candidates fairly using multi-agent Gemini intelligence. Parse resumes, match job criteria, conduct personalized AI interviews, and generate authoritative hiring reports.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <Button
            variant="outline"
            icon={UserPlus}
            style={{ color: '#ffffff', borderColor: 'rgba(255, 255, 255, 0.3)' }}
            onClick={() => navigate('/candidates')}
          >
            Add Candidate
          </Button>
          <Button
            variant="primary"
            icon={Play}
            onClick={() => navigate('/analysis')}
          >
            Run Matching Analysis
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Metrics Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1.25rem',
        }}
      >
        <Card style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                REGISTERED CANDIDATES
              </p>
              <h3 style={{ fontSize: '2rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                {loading ? '...' : stats.candidatesCount}
              </h3>
            </div>
            <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--accent-50)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-600)' }}>
              <Users size={24} />
            </div>
          </div>
        </Card>

        <Card style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                ACTIVE JOB OPENINGS
              </p>
              <h3 style={{ fontSize: '2rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                {loading ? '...' : stats.jobsCount}
              </h3>
            </div>
            <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--navy-50)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--navy-600)' }}>
              <Briefcase size={24} />
            </div>
          </div>
        </Card>

        <Card style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                AI PIPELINE AGENTS
              </p>
              <h3 style={{ fontSize: '2rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                7 / 7
              </h3>
            </div>
            <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--success-50)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--success-600)' }}>
              <TrendingUp size={24} />
            </div>
          </div>
        </Card>

        <Card style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                PERSISTENT SESSIONS
              </p>
              <h3 style={{ fontSize: '2rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                SQLite
              </h3>
            </div>
            <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--warning-50)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--warning-600)' }}>
              <FileCheck2 size={24} />
            </div>
          </div>
        </Card>
      </div>

      {/* Two Column Section: Recent Candidates & Recent Jobs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* Recent Candidates */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Candidates</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => navigate('/candidates')}>
              View All <ArrowRight size={14} />
            </Button>
          </CardHeader>
          <CardContent style={{ padding: 0 }}>
            {loading ? (
              <LoadingSpinner size={24} text="Loading candidates..." />
            ) : stats.recentCandidates.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                No candidates registered yet. Click &quot;Add Candidate&quot; to begin.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {stats.recentCandidates.map((c, i) => (
                  <div
                    key={c.id}
                    style={{
                      padding: '1rem 1.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      borderBottom: i < stats.recentCandidates.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                    }}
                  >
                    <div>
                      <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)', display: 'block' }}>
                        {c.full_name}
                      </strong>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                        {c.email || 'No email provided'} • {c.parsed_resume_data?.experience || 'Fresher'}
                      </span>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => navigate('/candidates')}>
                      View
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Job Postings */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Job Openings</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => navigate('/jobs')}>
              View All <ArrowRight size={14} />
            </Button>
          </CardHeader>
          <CardContent style={{ padding: 0 }}>
            {loading ? (
              <LoadingSpinner size={24} text="Loading job openings..." />
            ) : stats.recentJobs.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                No job postings created yet. Click &quot;Job Openings&quot; to create one.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {stats.recentJobs.map((j, i) => (
                  <div
                    key={j.id}
                    style={{
                      padding: '1rem 1.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      borderBottom: i < stats.recentJobs.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                    }}
                  >
                    <div>
                      <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)', display: 'block' }}>
                        {j.title}
                      </strong>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                        {j.company || 'Internal Opening'}
                      </span>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => navigate('/jobs')}>
                      View
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default DashboardPage;
