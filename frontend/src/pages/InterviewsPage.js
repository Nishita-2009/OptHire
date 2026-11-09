import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge, ScoreBadge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { EmptyState } from '../components/ui/EmptyState';
import { useNotification } from '../context/NotificationContext';
import {
  MessageSquareText,
  Play,
  Send,
  FileText,
} from 'lucide-react';

export function InterviewsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const notify = useNotification();

  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);

  // Active session
  const [activeSessionId, setActiveSessionId] = useState('');
  const [sessionData, setSessionData] = useState(null);
  const [, setLoadingPrereqs] = useState(false);
  const [loadingSession, setLoadingSession] = useState(false);

  // Creation form
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState(searchParams.get('candidateId') || '');
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get('jobId') || '');
  const selectedAnalysisId = searchParams.get('analysisId') || '';
  const [creatingSession, setCreatingSession] = useState(false);

  // Answer Submission
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [answerText, setAnswerText] = useState('');
  const [evaluatingAnswer, setEvaluatingAnswer] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [latestEvaluation, setLatestEvaluation] = useState(null);

  useEffect(() => {
    async function fetchPrereqs() {
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
        notify.error(err.message);
      } finally {
        setLoadingPrereqs(false);
      }
    }

    fetchPrereqs();
  }, [selectedCandidateId, selectedJobId, notify]);

  const fetchSession = async (sessionId) => {
    if (!sessionId) return;
    try {
      setLoadingSession(true);
      const res = await api.getInterviewSession(sessionId);
      setSessionData(res);
      if (res.questions?.length > 0 && !selectedQuestion) {
        setSelectedQuestion(res.questions[0]);
      }
    } catch (err) {
      notify.error(err.message);
    } finally {
      setLoadingSession(false);
    }
  };

  const handleCreateSession = async () => {
    if (!selectedCandidateId || !selectedJobId) {
      notify.error('Please select both a candidate and job opening.');
      return;
    }

    try {
      setCreatingSession(true);
      notify.info('Agent 5 (Interview Generator) is creating 21 personalized questions...');
      const newSession = await api.createInterviewSession({
        candidate_id: selectedCandidateId,
        job_id: selectedJobId,
        analysis_run_id: selectedAnalysisId || null,
        generate_questions: true,
      });

      notify.success(`Interview session created with ${newSession.total_questions} questions!`);
      setIsCreateOpen(false);
      setActiveSessionId(newSession.session_id);
      setSessionData(newSession);
      if (newSession.questions?.length > 0) {
        setSelectedQuestion(newSession.questions[0]);
      }
    } catch (err) {
      notify.error(err.message);
    } finally {
      setCreatingSession(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!activeSessionId || !selectedQuestion || !answerText.trim()) {
      notify.error('Please enter an answer before submitting for evaluation.');
      return;
    }

    try {
      setEvaluatingAnswer(true);
      notify.info('Agent 6 (Interview Evaluator) is evaluating your answer...');
      const evalRes = await api.submitInterviewAnswer(activeSessionId, selectedQuestion.id, answerText.trim());

      setLatestEvaluation(evalRes.evaluation);
      notify.success(`Answer evaluated! Score: ${evalRes.score}/100 (${evalRes.evaluation?.rating || 'Evaluated'})`);
      setAnswerText('');

      // Refresh session
      fetchSession(activeSessionId);
    } catch (err) {
      notify.error(err.message);
    } finally {
      setEvaluatingAnswer(false);
    }
  };

  const handleFinalizeSession = async () => {
    if (!activeSessionId) return;
    try {
      setFinalizing(true);
      notify.info('Synthesizing final interview evaluation via Agent 6...');
      const completed = await api.finalizeInterview(activeSessionId);
      setSessionData(completed);
      notify.success('Interview session successfully finalized!');
    } catch (err) {
      notify.error(err.message);
    } finally {
      setFinalizing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            AI Interview Sessions
          </h2>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Conduct stateful AI interviews generated by Agent 5, evaluate responses via Agent 6, and track provisional scoring.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Button variant="primary" icon={Play} onClick={() => setIsCreateOpen(true)}>
            New Interview Session
          </Button>
        </div>
      </div>

      {/* Session Lookup or Active Session View */}
      {!sessionData ? (
        <Card>
          <CardContent style={{ padding: 0 }}>
            <EmptyState
              icon={MessageSquareText}
              title="No active interview session loaded"
              description="Click 'New Interview Session' to generate 21 personalized questions with Agent 5, or enter an existing session UUID below."
              actionLabel="Launch New Session"
              actionIcon={Play}
              onAction={() => setIsCreateOpen(true)}
            />
            <div style={{ padding: '1.25rem 1.5rem', borderTop: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-card-subtle)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input
                type="text"
                placeholder="Enter existing session UUID (e.g. 4b0ff0db-2213-4f4c-9457-9579c9ff5f92)..."
                value={activeSessionId}
                onChange={(e) => setActiveSessionId(e.target.value.trim())}
                style={{ flex: 1, padding: '0.55rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', fontSize: '0.875rem' }}
              />
              <Button variant="secondary" size="sm" isLoading={loadingSession} onClick={() => fetchSession(activeSessionId)}>
                Load Session
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Active Session Info Bar */}
          <Card style={{ padding: '1.25rem 1.5rem', backgroundColor: 'var(--navy-900)', color: 'var(--white)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <Badge variant={sessionData.status === 'completed' ? 'success' : 'warning'}>
                    Status: {sessionData.status}
                  </Badge>
                  <span style={{ fontSize: '0.8125rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                    Session ID: {sessionData.session_id}
                  </span>
                </div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--white)' }}>
                  Interactive AI Interview ({sessionData.total_questions} Questions)
                </h3>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                {sessionData.status !== 'completed' && (
                  <Button
                    variant="outline"
                    style={{ color: '#ffffff', borderColor: 'rgba(255, 255, 255, 0.3)' }}
                    isLoading={finalizing}
                    onClick={handleFinalizeSession}
                  >
                    Finalize Interview (Agent 6)
                  </Button>
                )}
                <Button
                  variant="primary"
                  icon={FileText}
                  onClick={() => navigate(`/reports?sessionId=${sessionData.session_id}`)}
                >
                  Generate Report
                </Button>
              </div>
            </div>
          </Card>

          {/* Two Columns: Question List & Answer Runner */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '1.5rem' }}>
            {/* Question Selector List */}
            <Card style={{ height: '650px', display: 'flex', flexDirection: 'column' }}>
              <CardHeader>
                <CardTitle style={{ fontSize: '1rem' }}>
                  Question Rubric ({(sessionData.questions || []).length})
                </CardTitle>
              </CardHeader>
              <CardContent style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {(sessionData.questions || []).map((q, idx) => {
                    const isSelected = selectedQuestion?.id === q.id;
                    return (
                      <div
                        key={q.id || idx}
                        onClick={() => setSelectedQuestion(q)}
                        style={{
                          padding: '0.75rem 0.85rem',
                          borderRadius: 'var(--radius-md)',
                          cursor: 'pointer',
                          backgroundColor: isSelected ? 'var(--accent-50)' : 'transparent',
                          border: `1px solid ${isSelected ? 'var(--accent-500)' : 'var(--border-subtle)'}`,
                          transition: 'all var(--transition-fast)',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                          <strong style={{ fontSize: '0.8125rem', color: isSelected ? 'var(--accent-600)' : 'var(--text-primary)' }}>
                            Q{idx + 1}: {q.category || 'Technical'}
                          </strong>
                          <Badge variant="neutral" size="sm">{q.difficulty || 'medium'}</Badge>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                          {q.question}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Answer Evaluator Interface */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {selectedQuestion ? (
                <Card>
                  <CardHeader>
                    <div>
                      <Badge variant="primary" size="sm" style={{ marginBottom: '0.35rem' }}>
                        {selectedQuestion.category || 'General'} • {selectedQuestion.difficulty || 'medium'}
                      </Badge>
                      <CardTitle style={{ fontSize: '1.1rem' }}>{selectedQuestion.question}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                        Candidate Answer
                      </label>
                      <textarea
                        rows={5}
                        placeholder="Type candidate verbal or written response here to evaluate against expected answer points..."
                        value={answerText}
                        onChange={(e) => setAnswerText(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--border)',
                          outline: 'none',
                          fontFamily: 'inherit',
                          fontSize: '0.9375rem',
                          resize: 'vertical',
                        }}
                      />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <Button
                        variant="primary"
                        icon={Send}
                        isLoading={evaluatingAnswer}
                        disabled={!answerText.trim()}
                        onClick={handleSubmitAnswer}
                      >
                        Submit & Evaluate with Agent 6
                      </Button>
                    </div>

                    {/* Latest Evaluation Feedback Card */}
                    {latestEvaluation && (
                      <div
                        className="animate-fade-in"
                        style={{
                          padding: '1.25rem',
                          backgroundColor: 'var(--bg-card-subtle)',
                          borderRadius: 'var(--radius-lg)',
                          border: '1px solid var(--border)',
                          marginTop: '0.5rem',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Agent 6 Feedback</span>
                          <ScoreBadge score={latestEvaluation.score} label="Score" />
                        </div>
                        <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                          {latestEvaluation.answer_summary || latestEvaluation.feedback}
                        </p>
                        {latestEvaluation.strengths && latestEvaluation.strengths.length > 0 && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <small style={{ fontWeight: 600, color: 'var(--success-700)' }}>Strengths:</small>
                            <ul style={{ paddingLeft: '1.25rem', fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.2rem 0' }}>
                              {latestEvaluation.strengths.map((s, i) => (
                                <li key={i}>{s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {latestEvaluation.missing_points && latestEvaluation.missing_points.length > 0 && (
                          <div>
                            <small style={{ fontWeight: 600, color: 'var(--danger-700)' }}>Missing Points:</small>
                            <ul style={{ paddingLeft: '1.25rem', fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.2rem 0' }}>
                              {latestEvaluation.missing_points.map((m, i) => (
                                <li key={i}>{m}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent>
                    <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                      Select a question from the rubric on the left to start evaluation.
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      )}

      {/* New Interview Session Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create AI Interview Session"
        description="Agent 5 will formulate 21 personalized questions based on candidate qualifications and job description criteria."
        maxWidth="550px"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Candidate Profile *
            </label>
            <select
              value={selectedCandidateId}
              onChange={(e) => setSelectedCandidateId(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                outline: 'none',
              }}
            >
              {candidates.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name} ({c.email || 'No email'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Target Job Opening *
            </label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                outline: 'none',
              }}
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} • {j.company || 'Direct Employer'}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              isLoading={creatingSession}
              onClick={handleCreateSession}
              disabled={!selectedCandidateId || !selectedJobId}
            >
              Generate 21 Questions (Agent 5)
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default InterviewsPage;
