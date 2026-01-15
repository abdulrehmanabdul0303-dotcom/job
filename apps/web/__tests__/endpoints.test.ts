import { describe, it, expect } from 'vitest'
import { API_ENDPOINTS } from '@/lib/api/endpoints'

describe('API Endpoints', () => {
  it('should have all required auth endpoints', () => {
    expect(API_ENDPOINTS.AUTH.REGISTER).toBe('/api/v1/auth/register')
    expect(API_ENDPOINTS.AUTH.LOGIN).toBe('/api/v1/auth/login')
    expect(API_ENDPOINTS.AUTH.REFRESH).toBe('/api/v1/auth/refresh')
    expect(API_ENDPOINTS.AUTH.ME).toBe('/api/v1/auth/me')
    expect(API_ENDPOINTS.AUTH.LOGOUT).toBe('/api/v1/auth/logout')
  })

  it('should generate dynamic resume endpoints correctly', () => {
    const resumeId = 'test-resume-123'
    
    expect(API_ENDPOINTS.RESUME.DETAIL(resumeId)).toBe(`/api/v1/resume/${resumeId}`)
    expect(API_ENDPOINTS.RESUME.SCORECARD(resumeId)).toBe(`/api/v1/resume/${resumeId}/scorecard`)
    expect(API_ENDPOINTS.RESUME.SHARE(resumeId)).toBe(`/api/v1/resume/${resumeId}/share`)
    expect(API_ENDPOINTS.RESUME.DELETE(resumeId)).toBe(`/api/v1/resume/${resumeId}`)
  })

  it('should generate public scorecard endpoint correctly', () => {
    const token = 'public-token-123'
    expect(API_ENDPOINTS.RESUME.PUBLIC(token)).toBe(`/api/v1/resume/public/${token}`)
  })

  it('should have all required job endpoints', () => {
    expect(API_ENDPOINTS.JOBS.LIST).toBe('/api/v1/jobs')
    expect(API_ENDPOINTS.JOBS.CREATE).toBe('/api/v1/jobs')
    
    const jobId = 'job-123'
    expect(API_ENDPOINTS.JOBS.DETAIL(jobId)).toBe(`/api/v1/jobs/${jobId}`)
  })

  it('should have AI endpoints', () => {
    const jobId = 'job-123'
    expect(API_ENDPOINTS.AI.RESUME_VERSION(jobId)).toBe(`/api/v1/ai/resume/version/${jobId}`)
    expect(API_ENDPOINTS.AI.INTERVIEW_PREP(jobId)).toBe(`/api/v1/ai/interview/prepare/${jobId}`)
    expect(API_ENDPOINTS.AI.SKILLS_ANALYZE).toBe('/api/v1/ai/skills/analyze')
  })
})