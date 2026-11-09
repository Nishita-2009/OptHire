import React, { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { LoadingSpinner } from '../components/ui/LoadingState';
import { EmptyState } from '../components/ui/EmptyState';
import { useNotification } from '../context/NotificationContext';
import {
  FileText,
  Sparkles,
  CheckCircle,
  ShieldAlert,
  Printer,
} from 'lucide-react';

export function ReportsPage() {
  const [searchParams] = useSearchParams();
  const notify = useNotification();

  const [analysisRunId, setAnalysisRunId] = useState(searchParams.get('analysisId') || '');
  const [interviewSessionId, setInterviewSessionId] = useState(searchParams.get('sessionId') || '');
  const [reportIdInput, setReportIdInput] = useState(searchParams.get('reportId') || '');

  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  // If a reportId is present in URL or entered, fetch it
  const fetchReport = useCallback(async (id) => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.getReport(id);
      setReportData(res);
    } catch (err) {
      setError(err.message);
      notify.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [notify]);

  useEffect(() => {
    const rId = searchParams.get('reportId');
    if (rId) {
      fetchReport(rId);
    }
  }, [searchParams, fetchReport]);

  const handleGenerateReport = async () => {
    if (!analysisRunId.trim()) {
      notify.error('Please enter an Analysis Run UUID to synthesize the hiring report.');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      notify.info('Synthesizing candidate journey via Agent 7 (Hiring Report Generator)...');

      const res = await api.createReport(analysisRunId.trim(), interviewSessionId.trim() || null);
      setReportData(res);
      notify.success('Hiring report generated and persisted successfully!');
    } catch (err) {
      setError(err.message);
      notify.error(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const fullReport = reportData?.report_data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Title */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
          Executive Hiring Reports
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          Synthesized multi-agent hiring decisions combining resume analysis, ATS scoring, skill gaps, and AI interview evaluations.
        </p>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Report Generator / Lookup Bar */}
      <Card style={{ padding: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Analysis Run UUID *
            </label>
            <input
              type="text"
              placeholder="e.g. 7d78af9e-41f2-4f7a-91cf-2c45ea7d0bf6"
              value={analysisRunId}
              onChange={(e) => setAnalysisRunId(e.target.value)}
              style={{ width: '100%', padding: '0.6rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', fontSize: '0.875rem' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Interview Session UUID (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. 4b0ff0db-2213-4f4c-9457-9579c9ff5f92"
              value={interviewSessionId}
              onChange={(e) => setInterviewSessionId(e.target.value)}
              style={{ width: '100%', padding: '0.6rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', fontSize: '0.875rem' }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="text"
              placeholder="Or load by Report UUID..."
              value={reportIdInput}
              onChange={(e) => setReportIdInput(e.target.value.trim())}
              style={{ width: '280px', padding: '0.45rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', fontSize: '0.8125rem' }}
            />
            <Button variant="secondary" size="sm" onClick={() => fetchReport(reportIdInput)}>
              Load
            </Button>
          </div>

          <Button
            variant="primary"
            icon={Sparkles}
            isLoading={generating}
            disabled={!analysisRunId.trim()}
            onClick={handleGenerateReport}
          >
            Generate Executive Report (Agent 7)
          </Button>
        </div>
      </Card>

      {/* Report Display */}
      {loading ? (
        <LoadingSpinner text="Fetching executive hiring report..." />
      ) : !reportData ? (
        <Card>
          <CardContent style={{ padding: 0 }}>
            <EmptyState
              icon={FileText}
              title="No hiring report loaded"
              description="Enter an Analysis Run UUID above and click 'Generate Executive Report', or load an existing report by UUID."
            />
          </CardContent>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Provisional Alert Banner */}
          {reportData.is_provisional && (
            <Alert variant="warning" title="Provisional Hiring Report (Interview in Progress)">
              {fullReport?.provisional_details?.score_calculation ||
                'This report is provisional based on an in-progress interview session. The interview session remains open for the candidate to complete remaining questions.'}
            </Alert>
          )}

          {/* Main Executive Report Card */}
          <Card style={{ padding: '2rem' }}>
            {/* Header / Candidate & Decision Overview */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <Badge variant={reportData.is_provisional ? 'warning' : 'primary'} style={{ marginBottom: '0.5rem' }}>
                  {reportData.is_provisional ? 'PROVISIONAL REPORT' : 'FINAL REPORT'}
                </Badge>
                <h2 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.25rem 0', color: 'var(--text-primary)' }}>
                  {fullReport?.candidate?.name || 'Candidate'}
                </h2>
                <div style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                  Target Role: <span style={{ color: 'var(--accent-600)' }}>{fullReport?.candidate?.target_role || 'Position'}</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Recommendation:</span>
                  <Badge variant={reportData.recommendation?.includes('Hire') ? 'success' : 'warning'} size="lg">
                    {reportData.recommendation || 'Consider'}
                  </Badge>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Risk Level:</span>
                  <Badge variant={fullReport?.final_decision?.risk_level === 'Low' ? 'success' : 'warning'}>
                    {fullReport?.final_decision?.risk_level || 'Medium'}
                  </Badge>
                </div>
                <Button variant="secondary" size="sm" icon={Printer} onClick={() => window.print()} style={{ marginTop: '0.25rem' }}>
                  Print Report
                </Button>
              </div>
            </div>

            {/* Scores Overview Row */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '1rem',
                margin: '1.5rem 0',
              }}
            >
              <div style={{ padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>RESUME ATS MATCH</small>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-600)', marginTop: '0.2rem' }}>
                  {fullReport?.scores?.resume_match_score != null ? `${fullReport.scores.resume_match_score}%` : 'N/A'}
                </div>
              </div>

              <div style={{ padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>
                  {reportData.is_provisional ? 'PROVISIONAL INTERVIEW' : 'INTERVIEW SCORE'}
                </small>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--success-600)', marginTop: '0.2rem' }}>
                  {fullReport?.scores?.interview_score != null ? `${fullReport.scores.interview_score}%` : 'N/A'}
                </div>
              </div>

              <div style={{ padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>SYNTHESIZED HIRING SCORE</small>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--navy-600)', marginTop: '0.2rem' }}>
                  {reportData.overall_score != null ? `${reportData.overall_score}%` : 'N/A'}
                </div>
              </div>

              <div style={{ padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>DECISION CONFIDENCE</small>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--warning-700)', marginTop: '0.2rem' }}>
                  {fullReport?.scores?.decision_confidence != null ? `${fullReport.scores.decision_confidence}%` : 'N/A'}
                </div>
              </div>
            </div>

            {/* Executive Summary */}
            {fullReport?.executive_summary && (
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>Executive Summary</h3>
                <p style={{ fontSize: '0.95rem', lineHeight: 1.7, color: 'var(--text-primary)', margin: 0, whiteSpace: 'pre-line' }}>
                  {fullReport.executive_summary}
                </p>
              </div>
            )}

            {/* Candidate Summary */}
            {fullReport?.candidate?.candidate_summary && (
              <div style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem', backgroundColor: 'var(--bg-card-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <small style={{ fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Candidate Profile Narrative</small>
                <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-secondary)', margin: '0.35rem 0 0 0' }}>
                  {fullReport.candidate.candidate_summary}
                </p>
              </div>
            )}

            {/* Reasons to Hire vs Caution */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', margin: '1.5rem 0' }}>
              <div style={{ padding: '1.25rem', backgroundColor: 'var(--success-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--success-100)' }}>
                <h4 style={{ color: 'var(--success-700)', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.95rem', marginBottom: '0.5rem' }}>
                  <CheckCircle size={16} /> Key Reasons to Hire
                </h4>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.875rem', color: 'var(--neutral-800)', margin: 0 }}>
                  {(fullReport?.key_reasons_to_hire || []).map((r, i) => (
                    <li key={i} style={{ marginBottom: '0.25rem' }}>{r}</li>
                  ))}
                </ul>
              </div>

              <div style={{ padding: '1.25rem', backgroundColor: 'var(--warning-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--warning-100)' }}>
                <h4 style={{ color: 'var(--warning-700)', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.95rem', marginBottom: '0.5rem' }}>
                  <ShieldAlert size={16} /> Key Reasons for Caution
                </h4>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.875rem', color: 'var(--neutral-800)', margin: 0 }}>
                  {(fullReport?.key_reasons_for_caution || []).map((r, i) => (
                    <li key={i} style={{ marginBottom: '0.25rem' }}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Final Decision & Next Actions */}
            {fullReport?.final_decision && (
              <div style={{ padding: '1.25rem', backgroundColor: 'var(--neutral-100)', borderRadius: 'var(--radius-md)', marginTop: '1.5rem' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 0.35rem 0' }}>
                  Final Strategic Decision
                </h4>
                <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  {fullReport.final_decision.reasoning}
                </p>
                {fullReport.final_decision.next_action && (
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-600)' }}>
                    Immediate Next Action: {fullReport.final_decision.next_action}
                  </div>
                )}
              </div>
            )}

            {/* Disclaimer */}
            <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)', textAlign: 'center' }}>
              <small style={{ color: 'var(--text-muted)' }}>
                {fullReport?.disclaimer ||
                  'This AI-generated report is decision support only. Final hiring decisions should include appropriate human review.'}
              </small>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

export default ReportsPage;
