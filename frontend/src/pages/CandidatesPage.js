import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Alert } from '../components/ui/Alert';
import { LoadingSpinner } from '../components/ui/LoadingState';
import { EmptyState } from '../components/ui/EmptyState';
import { useNotification } from '../context/NotificationContext';
import {
  Users,
  UserPlus,
  UploadCloud,
  Search,
  Mail,
  Phone,
  Eye,
} from 'lucide-react';

export function CandidatesPage() {
  const notify = useNotification();
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Modal states
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [candidateAnalyses, setCandidateAnalyses] = useState([]);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Form states
  const [activeTab, setActiveTab] = useState('manual'); // 'manual' | 'upload'
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    skills: '',
    experience: 'Fresher',
    education: '',
    projects: '',
  });

  const fetchCandidates = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getCandidates();
      setCandidates(res.candidates || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, []);

  const handleOpenDetails = async (candidate) => {
    setSelectedCandidate(candidate);
    setLoadingDetails(true);
    try {
      const analyses = await api.getCandidateAnalyses(candidate.id);
      setCandidateAnalyses(analyses.runs || []);
    } catch {
      setCandidateAnalyses([]);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      notify.error('Please upload a valid PDF document.');
      return;
    }

    try {
      setUploadingPdf(true);
      notify.info('Uploading resume & running Agent 1 (Resume Parser)...');
      const parsed = await api.uploadResume(file);

      // Populate form fields with extracted data from Agent 1
      setFormData((prev) => ({
        ...prev,
        fullName: parsed.name || prev.fullName,
        email: parsed.email || prev.email,
        phone: parsed.phone || prev.phone,
        skills: Array.isArray(parsed.skills) ? parsed.skills.join(', ') : prev.skills,
        experience: parsed.experience || prev.experience,
        education: parsed.education || prev.education,
        projects: Array.isArray(parsed.projects) ? parsed.projects.join(', ') : prev.projects,
      }));

      setActiveTab('manual');
      notify.success('Resume parsed successfully! Review extracted data and confirm registration.');
    } catch (err) {
      notify.error(err.message);
    } finally {
      setUploadingPdf(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (!formData.fullName.trim()) {
      notify.error('Candidate full name is required.');
      return;
    }

    try {
      setSubmitting(true);
      const skillsArray = formData.skills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      const payload = {
        full_name: formData.fullName.trim(),
        email: formData.email.trim() || null,
        phone: formData.phone.trim() || null,
        parsed_resume_data: {
          name: formData.fullName.trim(),
          skills: skillsArray,
          experience: formData.experience.trim(),
          education: formData.education.trim(),
          projects: formData.projects
            .split(',')
            .map((p) => p.trim())
            .filter(Boolean),
        },
      };

      await api.createCandidate(payload);
      notify.success(`Candidate "${formData.fullName}" registered successfully!`);
      setIsRegisterOpen(false);
      setFormData({
        fullName: '',
        email: '',
        phone: '',
        skills: '',
        experience: 'Fresher',
        education: '',
        projects: '',
      });
      fetchCandidates();
    } catch (err) {
      notify.error(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredCandidates = candidates.filter((c) => {
    const q = searchQuery.toLowerCase();
    return (
      c.full_name?.toLowerCase().includes(q) ||
      c.email?.toLowerCase().includes(q) ||
      (c.parsed_resume_data?.skills || []).some((s) => s.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header & Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            Candidate Directory
          </h2>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Manage candidate profiles, review parsed technical skills, and inspect match histories.
          </p>
        </div>
        <Button
          variant="primary"
          icon={UserPlus}
          onClick={() => {
            setIsRegisterOpen(true);
            setActiveTab('manual');
          }}
        >
          Register Candidate
        </Button>
      </div>

      {/* Search Bar */}
      <Card style={{ padding: '0.75rem 1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Search size={18} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search candidates by name, email, or skills (e.g. Python, FastAPI, SQL)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              backgroundColor: 'transparent',
              fontSize: '0.9375rem',
            }}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              style={{ fontSize: '0.75rem', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              Clear
            </button>
          )}
        </div>
      </Card>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Candidate List Table */}
      <Card>
        <CardContent style={{ padding: 0 }}>
          {loading ? (
            <LoadingSpinner text="Loading candidate profiles..." />
          ) : filteredCandidates.length === 0 ? (
            <EmptyState
              icon={Users}
              title={searchQuery ? 'No matching candidates' : 'No candidates registered yet'}
              description={
                searchQuery
                  ? 'No candidate profiles matched your search criteria.'
                  : 'Get started by registering your first candidate profile or uploading a resume PDF.'
              }
              actionLabel={searchQuery ? null : 'Register Candidate'}
              actionIcon={UserPlus}
              onAction={() => setIsRegisterOpen(true)}
            />
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-card-subtle)' }}>
                    <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>CANDIDATE</th>
                    <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>CONTACT</th>
                    <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>EXPERIENCE</th>
                    <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)' }}>EXTRACTED SKILLS</th>
                    <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--text-muted)', textAlign: 'right' }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map((c) => {
                    const skills = c.parsed_resume_data?.skills || [];
                    return (
                      <tr key={c.id} style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background-color var(--transition-fast)' }}>
                        <td style={{ padding: '1rem 1.25rem' }}>
                          <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)', display: 'block' }}>
                            {c.full_name}
                          </strong>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            ID: {c.id.slice(0, 8)}...
                          </span>
                        </td>
                        <td style={{ padding: '1rem 1.25rem', color: 'var(--text-secondary)' }}>
                          {c.email && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '2px' }}>
                              <Mail size={13} color="var(--text-muted)" /> {c.email}
                            </div>
                          )}
                          {c.phone && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                              <Phone size={13} color="var(--text-muted)" /> {c.phone}
                            </div>
                          )}
                          {!c.email && !c.phone && <span style={{ color: 'var(--text-muted)' }}>None provided</span>}
                        </td>
                        <td style={{ padding: '1rem 1.25rem' }}>
                          <Badge variant="navy">{c.parsed_resume_data?.experience || 'Fresher'}</Badge>
                        </td>
                        <td style={{ padding: '1rem 1.25rem', maxWidth: '320px' }}>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                            {skills.slice(0, 4).map((s, idx) => (
                              <Badge key={idx} variant="primary" size="sm">{s}</Badge>
                            ))}
                            {skills.length > 4 && (
                              <Badge variant="neutral" size="sm">+{skills.length - 4}</Badge>
                            )}
                            {skills.length === 0 && <small style={{ color: 'var(--text-muted)' }}>No skills parsed</small>}
                          </div>
                        </td>
                        <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                          <Button variant="outline" size="sm" icon={Eye} onClick={() => handleOpenDetails(c)}>
                            Profile
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Candidate Registration Modal */}
      <Modal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        title="Register Candidate Profile"
        description="Add a candidate manually or extract structured data automatically from a PDF resume using Agent 1."
        maxWidth="600px"
      >
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
          <Button
            type="button"
            variant={activeTab === 'manual' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setActiveTab('manual')}
          >
            Direct Form Entry
          </Button>
          <Button
            type="button"
            variant={activeTab === 'upload' ? 'primary' : 'ghost'}
            size="sm"
            icon={UploadCloud}
            onClick={() => setActiveTab('upload')}
          >
            Upload Resume (Agent 1 PDF Parser)
          </Button>
        </div>

        {activeTab === 'upload' && (
          <div
            style={{
              padding: '2.5rem 1.5rem',
              textAlign: 'center',
              border: '2px dashed var(--accent-500)',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--accent-50)',
              marginBottom: '1rem',
            }}
          >
            <UploadCloud size={36} color="var(--accent-600)" style={{ margin: '0 auto 0.75rem auto' }} />
            <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)' }}>
              Select a Candidate Resume PDF
            </h4>
            <p style={{ margin: '0 0 1rem 0', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Agent 1 will extract full name, skills, experience, and education directly from the PDF.
            </p>
            <input
              type="file"
              accept=".pdf"
              id="resume-pdf-upload"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              disabled={uploadingPdf}
            />
            <label htmlFor="resume-pdf-upload">
              <span
                style={{
                  display: 'inline-block',
                  padding: '0.55rem 1.25rem',
                  backgroundColor: 'var(--accent-600)',
                  color: 'white',
                  borderRadius: 'var(--radius-md)',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  cursor: uploadingPdf ? 'not-allowed' : 'pointer',
                  opacity: uploadingPdf ? 0.7 : 1,
                }}
              >
                {uploadingPdf ? 'Agent 1 Parsing PDF...' : 'Choose PDF File'}
              </span>
            </label>
          </div>
        )}

        <form onSubmit={handleRegisterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Full Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Alex Morgan"
              value={formData.fullName}
              onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Email Address
              </label>
              <input
                type="email"
                placeholder="alex.morgan@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  outline: 'none',
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Phone Number
              </label>
              <input
                type="text"
                placeholder="+1-555-0199"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Technical Skills (Comma separated)
            </label>
            <input
              type="text"
              placeholder="Python, FastAPI, SQL, Docker, REST APIs, Git"
              value={formData.skills}
              onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Experience Level
              </label>
              <input
                type="text"
                placeholder="e.g. Fresher, 2 years"
                value={formData.experience}
                onChange={(e) => setFormData({ ...formData, experience: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  outline: 'none',
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Education / Degree
              </label>
              <input
                type="text"
                placeholder="Bachelor of Computer Science"
                value={formData.education}
                onChange={(e) => setFormData({ ...formData, education: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={() => setIsRegisterOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              Save Candidate Profile
            </Button>
          </div>
        </form>
      </Modal>

      {/* Candidate Profile Details Modal */}
      <Modal
        isOpen={Boolean(selectedCandidate)}
        onClose={() => setSelectedCandidate(null)}
        title={selectedCandidate?.full_name || 'Candidate Profile'}
        description={`Registered Candidate Profile ID: ${selectedCandidate?.id}`}
        maxWidth="650px"
      >
        {selectedCandidate && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Quick Contact & Info Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', padding: '1rem', backgroundColor: 'var(--neutral-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div>
                <small style={{ color: 'var(--text-muted)' }}>Email Address</small>
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{selectedCandidate.email || 'Not provided'}</div>
              </div>
              <div>
                <small style={{ color: 'var(--text-muted)' }}>Phone</small>
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{selectedCandidate.phone || 'Not provided'}</div>
              </div>
              <div>
                <small style={{ color: 'var(--text-muted)' }}>Experience</small>
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{selectedCandidate.parsed_resume_data?.experience || 'Fresher'}</div>
              </div>
              <div>
                <small style={{ color: 'var(--text-muted)' }}>Education</small>
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{selectedCandidate.parsed_resume_data?.education || 'Not specified'}</div>
              </div>
            </div>

            {/* Extracted Skills */}
            <div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem' }}>Technical Skills</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {(selectedCandidate.parsed_resume_data?.skills || []).map((skill, idx) => (
                  <Badge key={idx} variant="primary">{skill}</Badge>
                ))}
              </div>
            </div>

            {/* Previous Analyses */}
            <div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem' }}>Matching Analyses Run</h4>
              {loadingDetails ? (
                <LoadingSpinner size={20} text="Fetching historical evaluations..." />
              ) : candidateAnalyses.length === 0 ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                  No matching analyses run for this candidate yet. Go to the Matching Analysis tab to evaluate against a job opening.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {candidateAnalyses.map((run) => (
                    <div
                      key={run.id}
                      style={{
                        padding: '0.75rem 1rem',
                        backgroundColor: 'var(--bg-card-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div>
                        <strong style={{ fontSize: '0.875rem' }}>Analysis #{run.id.slice(0, 8)}</strong>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status: {run.status}</div>
                      </div>
                      {run.match_result?.overall_match_score != null && (
                        <Badge variant="success">Match: {run.match_result.overall_match_score}%</Badge>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default CandidatesPage;
