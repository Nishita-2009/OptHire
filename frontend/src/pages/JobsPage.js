import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Alert } from '../components/ui/Alert';
import { LoadingSpinner } from '../components/ui/LoadingState';
import { EmptyState } from '../components/ui/EmptyState';
import { useNotification } from '../context/NotificationContext';
import {
  Briefcase,
  PlusCircle,
  Search,
  Building,
  Sparkles,
  Eye,
} from 'lucide-react';

export function JobsPage() {
  const notify = useNotification();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [parsingJd, setParsingJd] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form states
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    description: '',
    requiredSkills: '',
    preferredSkills: '',
    experience: '0-1 years',
  });

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getJobs();
      setJobs(res.jobs || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleAutoParseJd = async () => {
    if (!formData.description.trim() || formData.description.trim().length < 20) {
      notify.error('Please enter a descriptive job posting before triggering Agent 2.');
      return;
    }

    try {
      setParsingJd(true);
      notify.info('Analyzing job requirements with Agent 2 (JD Parser)...');
      const parsed = await api.parseJobDescription(formData.description.trim());

      setFormData((prev) => ({
        ...prev,
        title: parsed.job_title || prev.title,
        company: parsed.company || prev.company,
        requiredSkills: Array.isArray(parsed.required_skills)
          ? parsed.required_skills.join(', ')
          : prev.requiredSkills,
        preferredSkills: Array.isArray(parsed.preferred_skills)
          ? parsed.preferred_skills.join(', ')
          : prev.preferredSkills,
        experience: parsed.experience || prev.experience,
      }));

      notify.success('Agent 2 extracted structured skills and experience from job text!');
    } catch (err) {
      notify.error(err.message);
    } finally {
      setParsingJd(false);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      notify.error('Job opening title is required.');
      return;
    }

    try {
      setSubmitting(true);
      const reqSkills = formData.requiredSkills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const prefSkills = formData.preferredSkills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      const payload = {
        title: formData.title.trim(),
        company: formData.company.trim() || null,
        description: formData.description.trim() || null,
        parsed_job_data: {
          job_title: formData.title.trim(),
          title: formData.title.trim(),
          company: formData.company.trim() || null,
          required_skills: reqSkills,
          preferred_skills: prefSkills,
          experience: formData.experience.trim(),
        },
      };

      await api.createJob(payload);
      notify.success(`Job opening "${formData.title}" created successfully!`);
      setIsCreateOpen(false);
      setFormData({
        title: '',
        company: '',
        description: '',
        requiredSkills: '',
        preferredSkills: '',
        experience: '0-1 years',
      });
      fetchJobs();
    } catch (err) {
      notify.error(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredJobs = jobs.filter((j) => {
    const q = searchQuery.toLowerCase();
    return (
      j.title?.toLowerCase().includes(q) ||
      j.company?.toLowerCase().includes(q) ||
      (j.parsed_job_data?.required_skills || []).some((s) => s.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header & Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            Job Openings
          </h2>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Configure job openings, specify mandatory vs preferred skills, and automate criteria extraction via Agent 2.
          </p>
        </div>
        <Button variant="primary" icon={PlusCircle} onClick={() => setIsCreateOpen(true)}>
          Create Job Opening
        </Button>
      </div>

      {/* Search Input */}
      <Card style={{ padding: '0.75rem 1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Search size={18} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search job postings by title, company, or required skills..."
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
        </div>
      </Card>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Job Openings Grid */}
      {loading ? (
        <LoadingSpinner text="Loading job openings..." />
      ) : filteredJobs.length === 0 ? (
        <Card>
          <CardContent style={{ padding: 0 }}>
            <EmptyState
              icon={Briefcase}
              title={searchQuery ? 'No matching jobs' : 'No job openings created yet'}
              description={
                searchQuery
                  ? 'No job openings matched your search query.'
                  : 'Post your first role to start matching qualified candidates against your criteria.'
              }
              actionLabel={searchQuery ? null : 'Post Job Opening'}
              actionIcon={PlusCircle}
              onAction={() => setIsCreateOpen(true)}
            />
          </CardContent>
        </Card>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.25rem' }}>
          {filteredJobs.map((job) => {
            const reqSkills = job.parsed_job_data?.required_skills || [];
            const prefSkills = job.parsed_job_data?.preferred_skills || [];
            return (
              <Card key={job.id} hoverable style={{ display: 'flex', flexDirection: 'column' }}>
                <CardHeader>
                  <div>
                    <CardTitle>{job.title}</CardTitle>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.25rem' }}>
                      <Building size={14} color="var(--text-muted)" />
                      <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                        {job.company || 'Direct Employer'}
                      </span>
                    </div>
                  </div>
                  <Badge variant="navy">{job.parsed_job_data?.experience || '0-1 years'}</Badge>
                </CardHeader>
                <CardContent style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {job.description && (
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', margin: 0 }}>
                      {job.description}
                    </p>
                  )}

                  <div>
                    <small style={{ fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                      REQUIRED SKILLS ({reqSkills.length})
                    </small>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                      {reqSkills.slice(0, 5).map((s, idx) => (
                        <Badge key={idx} variant="primary" size="sm">{s}</Badge>
                      ))}
                      {reqSkills.length > 5 && <Badge variant="neutral" size="sm">+{reqSkills.length - 5}</Badge>}
                      {reqSkills.length === 0 && <small style={{ color: 'var(--text-muted)' }}>None specified</small>}
                    </div>
                  </div>

                  {prefSkills.length > 0 && (
                    <div>
                      <small style={{ fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                        PREFERRED SKILLS
                      </small>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                        {prefSkills.slice(0, 4).map((s, idx) => (
                          <Badge key={idx} variant="warning" size="sm">{s}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
                <div style={{ padding: '0.75rem 1.5rem', borderTop: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-card-subtle)', display: 'flex', justifyContent: 'flex-end' }}>
                  <Button variant="outline" size="sm" icon={Eye} onClick={() => setSelectedJob(job)}>
                    View Criteria
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Job Opening Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Job Opening"
        description="Define role title, company, and criteria. Use Agent 2 to extract skills automatically from JD text."
        maxWidth="620px"
      >
        <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Job Title *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Junior Python Developer"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
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
                Company Name
              </label>
              <input
                type="text"
                placeholder="TechNova Solutions"
                value={formData.company}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <label style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                Job Description Text
              </label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                icon={Sparkles}
                isLoading={parsingJd}
                onClick={handleAutoParseJd}
                style={{ color: 'var(--accent-600)', padding: '0.15rem 0.5rem', fontSize: '0.75rem' }}
              >
                Auto-Parse with Agent 2
              </Button>
            </div>
            <textarea
              rows={4}
              placeholder="Paste job description requirements, responsibilities, and qualifications here..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                outline: 'none',
                fontFamily: 'inherit',
                resize: 'vertical',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Mandatory Required Skills (Comma separated)
            </label>
            <input
              type="text"
              placeholder="Python, SQL, FastAPI, REST APIs, Git, Data Structures"
              value={formData.requiredSkills}
              onChange={(e) => setFormData({ ...formData, requiredSkills: e.target.value })}
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Preferred / Nice-to-Have Skills
              </label>
              <input
                type="text"
                placeholder="Docker, PostgreSQL, Unit Testing"
                value={formData.preferredSkills}
                onChange={(e) => setFormData({ ...formData, preferredSkills: e.target.value })}
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
                Target Experience Level
              </label>
              <input
                type="text"
                placeholder="0-1 years"
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
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              Create Job Opening
            </Button>
          </div>
        </form>
      </Modal>

      {/* View Job Criteria Modal */}
      <Modal
        isOpen={Boolean(selectedJob)}
        onClose={() => setSelectedJob(null)}
        title={selectedJob?.title || 'Job Opening'}
        description={`Company: ${selectedJob?.company || 'Internal Opening'}`}
        maxWidth="600px"
      >
        {selectedJob && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {selectedJob.description && (
              <div>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Description</h4>
                <p style={{ fontSize: '0.9rem', marginTop: '0.25rem', whiteSpace: 'pre-line' }}>{selectedJob.description}</p>
              </div>
            )}

            <div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Mandatory Skills</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.4rem' }}>
                {(selectedJob.parsed_job_data?.required_skills || []).map((s, idx) => (
                  <Badge key={idx} variant="primary">{s}</Badge>
                ))}
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Preferred Skills</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.4rem' }}>
                {(selectedJob.parsed_job_data?.preferred_skills || []).map((s, idx) => (
                  <Badge key={idx} variant="warning">{s}</Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default JobsPage;
