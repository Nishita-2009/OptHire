import { render, screen } from '@testing-library/react';
import App from './App';
import { api, ApiError, API_BASE_URL } from './services/api';

test('renders OptHire brand and navigation sidebar', () => {
  render(<App />);
  const brandElements = screen.getAllByText(/OptHire/i);
  expect(brandElements.length).toBeGreaterThan(0);

  expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /candidates/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /job openings/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /matching analysis/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /ai interviews/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /hiring reports/i })).toBeInTheDocument();
});

test('api client exposes standard endpoints and base URL', () => {
  expect(API_BASE_URL).toBeDefined();
  expect(typeof api.getHealth).toBe('function');
  expect(typeof api.getCandidates).toBe('function');
  expect(typeof api.createCandidate).toBe('function');
  expect(typeof api.getJobs).toBe('function');
  expect(typeof api.createJob).toBe('function');
  expect(typeof api.createAnalysis).toBe('function');
  expect(typeof api.createInterviewSession).toBe('function');
  expect(typeof api.submitInterviewAnswer).toBe('function');
  expect(typeof api.createReport).toBe('function');
});

test('ApiError encapsulates status and payload message', () => {
  const err = new ApiError('Candidate not found', 404, { detail: 'Candidate not found' });
  expect(err.message).toBe('Candidate not found');
  expect(err.status).toBe(404);
  expect(err.data.detail).toBe('Candidate not found');
});
