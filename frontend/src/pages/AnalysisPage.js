import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { LoadingSpinner } from '../components/ui/LoadingState';
import { EmptyState } from '../components/ui/EmptyState';
import { useNotification } from '../context/NotificationContext';
import {
  GitCompare,
  Play,
  CheckCircle,
  AlertTriangle,
  FileText,
  MessageSquare,
} from 'lucide-react';

export function AnalysisPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const notify = useNotification();

  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loadingPrereqs, setLoadingPrereqs] = useState(true);

  // Form selections
  const [selectedCandidateId, setSelectedCandidateId] = useState(searchParams.get('candidateId') || '');
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get('jobId') || '');
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [error, setError] = useState(null);

  // Results
  const [analysisResult, setAnalysisResult] = useState(null);

  useEffect(() => {
    async function loadPrereqs() {
      try {
        setLoadingPrereqs(true);
        const [candRes, jobRes] = await Promise.all([
          api.getCandidates(0, 100).catch(() => ({ candidates: [] })),
          api.getJobs(0, 100).catch(() => ({ jobs: [] })),
        ]);
        setCandidates(candRes.candidates || []);
        setJobs(jobRes.jobs || []);

        if (!selectedCandidateId && candRes.candidates?.length > 0) {
          setSelectedCandidateId(candRes.candidates[0].id);
        }
        if (!selectedJobId && jobRes.jobs?.length > 0) {
          setSelectedJobId(jobRes.jobs[0].id);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingPrereqs(false);
      }
    }

    loadPrereqs();
  }, [selectedCandidateId, selectedJobId]);

  const handleRunAnalysis = async () => {
    if (!selectedCandidateId || !selectedJobId) {
      notify.error('Please select both a candidate profile and target job opening.');
      return;
    }

    try {
      setRunningAnalysis(true);
      setError(null);
      notify.info('Triggering Agent 3 (Resume Matcher) & Agent 4 (Skill Gap Analyzer)...');

      const result = await api.createAnalysis(selectedCandidateId, selectedJobId);
      setAnalysisResult(result);
      notify.success('Matching analysis completed successfully!');
    } catch (err) {
      setError(err.message);
      notify.error(err.message);
    } finally {
      setRunningAnalysis(false);
    }
  };

  const matchData = analysisResult?.match_result;
  const skillGapData = analysisResult?.skill_gap_result;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Page Title */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
          Candidate-versus-Job Matching Analysis
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          Evaluate alignment, calculate ATS score tiers, detect critical missing skills, and formulate upskilling paths via Agents 3 & 4.
        </p>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Selection Control Card */}
      <Card style={{ padding: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
              1. Select Candidate Profile *
            </label>
            {loadingPrereqs ? (
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Loading candidates...</div>
            ) : (
              <select
                value={selectedCandidateId}
                onChange={(e) => setSelectedCandidateId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--bg-card)',
                  outline: 'none',
                  fontSize: '0.9375rem',
                }}
              >
                {candidates.length === 0 ? (
                  <option value="">No candidates available</option>
                ) : (
                  candidates.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.full_name} ({c.email || 'No email'}) • {c.parsed_resume_data?.experience || 'Fresher'}
                    </option>
                  ))
                )}
              </select>
            )}
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
              2. Select Target Job Opening *
            </label>
            {loadingPrereqs ? (
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Loading jobs...</div>
            ) : (
              <select
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--bg-card)',
                  outline: 'none',
                  fontSize: '0.9375rem',
                }}
              >
                {jobs.length === 0 ? (
                  <option value="">No job openings available</option>
                ) : (
                  jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title} • {j.company || 'Internal Opening'}
                    </option>
                  ))
                )}
              </select>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-subtle)' }}>
          <Button
            variant="primary"
            size="md"
            icon={Play}
            isLoading={runningAnalysis}
            disabled={!selectedCandidateId || !selectedJobId || candidates.length === 0 || jobs.length === 0}
            onClick={handleRunAnalysis}
          >
            Execute Matching Analysis (Agent 3 & 4)
          </Button>
        </div>
      </Card>

      {/* Analysis Results Display */}
      {runningAnalysis ? (
        <Card>
          <CardContent>
            <LoadingSpinner text="Analyzing candidate fit against job requirements with Agent 3 (Resume Matcher) and Agent 4 (Skill Gap Analyzer)..." />
          </CardContent>
        </Card>
      ) : !analysisResult ? (
        <Card>
          <CardContent style={{ padding: 0 }}>
            <EmptyState
              icon={GitCompare}
              title="No analysis run selected"
              description="Select a candidate and target job role above and click 'Execute Matching Analysis' to see AI evaluation results."
            />
          </CardContent>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Top Score Banner */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
            }}
          >
            <Card style={{ padding: '1.25rem', borderLeft: '4px solid var(--accent-600)' }}>
              <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>OVERALL ATS MATCH</small>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-600)', marginTop: '0.25rem' }}>
                {matchData?.overall_match_score != null ? `${matchData.overall_match_score}%` : 'N/A'}
              </div>
              <small style={{ color: 'var(--text-muted)' }}>
                Confidence: {matchData?.confidence_score != null ? `${matchData.confidence_score}%` : 'N/A'}
              </small>
            </Card>

            <Card style={{ padding: '1.25rem', borderLeft: '4px solid var(--success-600)' }}>
              <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>SKILL MATCH SCORE</small>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success-600)', marginTop: '0.25rem' }}>
                {matchData?.skill_match?.score != null ? `${matchData.skill_match.score}%` : 'N/A'}
              </div>
              <small style={{ color: 'var(--text-muted)' }}>Verified required skills</small>
            </Card>

            <Card style={{ padding: '1.25rem', borderLeft: '4px solid var(--navy-600)' }}>
              <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>EXPERIENCE MATCH</small>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-600)', marginTop: '0.25rem' }}>
                {matchData?.experience_match?.score != null ? `${matchData.experience_match.score}%` : 'N/A'}
              </div>
              <small style={{ color: 'var(--text-muted)' }}>Alignment with seniority</small>
            </Card>

            <Card style={{ padding: '1.25rem', borderLeft: '4px solid var(--warning-600)' }}>
              <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>ESTIMATED UPSKILLING</small>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--warning-700)', marginTop: '0.35rem' }}>
                {skillGapData?.estimated_upskilling_time || '2-4 weeks'}
              </div>
              <small style={{ color: 'var(--text-muted)' }}>Agent 4 development projection</small>
            </Card>
          </div>

          {/* Candidate Fit Summary */}
          {matchData?.candidate_summary && (
            <Card>
              <CardHeader>
                <CardTitle>Candidate Fit Narrative (Agent 3)</CardTitle>
                <Badge variant={matchData.recommendation?.includes('Strong') ? 'success' : 'primary'}>
                  {matchData.recommendation || 'Evaluated'}
                </Badge>
              </CardHeader>
              <CardContent>
                <p style={{ fontSize: '0.95rem', lineHeight: 1.6, color: 'var(--text-primary)', margin: 0 }}>
                  {matchData.candidate_summary}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Skills Comparison: Matched vs Missing */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            {/* Matched Skills */}
            <Card>
              <CardHeader>
                <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success-700)' }}>
                  <CheckCircle size={18} /> Matched Skills ({(matchData?.matched_skills || []).length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {(matchData?.matched_skills || []).map((s, idx) => (
                    <Badge key={idx} variant="success">{s}</Badge>
                  ))}
                  {(matchData?.matched_skills || []).length === 0 && (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No direct skill matches detected.</span>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Missing Skills */}
            <Card>
              <CardHeader>
                <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--danger-700)' }}>
                  <AlertTriangle size={18} /> Missing / Gap Skills ({(matchData?.missing_skills || []).length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {(matchData?.missing_skills || []).map((s, idx) => (
                    <Badge key={idx} variant="danger">{s}</Badge>
                  ))}
                  {(matchData?.missing_skills || []).length === 0 && (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No mandatory skill gaps identified!</span>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Priority Skill Gaps from Agent 4 */}
          {skillGapData?.priority_gaps && skillGapData.priority_gaps.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Skill Gap & Upskilling Roadmap (Agent 4)</CardTitle>
              </CardHeader>
              <CardContent style={{ padding: 0 }}>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-card-subtle)' }}>
                        <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>SKILL GAP</th>
                        <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>PRIORITY</th>
                        <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>WHY CRITICAL</th>
                        <th style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>TIMELINE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {skillGapData.priority_gaps.map((gap, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>{gap.skill || gap}</td>
                          <td style={{ padding: '0.85rem 1.25rem' }}>
                            <Badge variant={gap.priority === 'High' ? 'danger' : 'warning'}>{gap.priority || 'Medium'}</Badge>
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-secondary)' }}>{gap.reason || 'Required job qualification'}</td>
                          <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-muted)' }}>{gap.estimated_learning_time || '2 weeks'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Next Steps Quick Launch Bar */}
          <Card style={{ padding: '1.25rem 1.5rem', backgroundColor: 'var(--navy-50)', border: '1px solid var(--navy-100)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <strong style={{ fontSize: '1rem', color: 'var(--navy-900)' }}>Ready for Next Pipeline Steps?</strong>
                <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--navy-700)' }}>
                  Launch a stateful 21-question AI interview session with Agent 5, or generate an executive hiring report.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <Button
                  variant="outline"
                  icon={MessageSquare}
                  onClick={() => navigate(`/interviews?candidateId=${selectedCandidateId}&jobId=${selectedJobId}&analysisId=${analysisResult.id}`)}
                >
                  Start AI Interview
                </Button>
                <Button
                  variant="primary"
                  icon={FileText}
                  onClick={() => navigate(`/reports?analysisId=${analysisResult.id}`)}
                >
                  Generate Hiring Report
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

export default AnalysisPage;
