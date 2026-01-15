-- Migration: Add AI Skill Gap Analysis Tables
-- Description: Creates tables for skill gap analysis, learning recommendations, and progress tracking
-- Version: 003
-- Date: 2025-01-11

-- Skill Gap Analysis main table
CREATE TABLE IF NOT EXISTS skill_gap_analyses (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    job_id VARCHAR(36) NOT NULL,
    missing_skills TEXT NOT NULL,
    learning_recommendations TEXT NOT NULL,
    estimated_timeline TEXT NOT NULL,
    priority_score TEXT NOT NULL,
    market_demand TEXT,
    total_missing_skills INTEGER NOT NULL,
    critical_skills_count INTEGER DEFAULT 0,
    estimated_total_hours INTEGER NOT NULL,
    overall_readiness_score REAL NOT NULL,
    analysis_version VARCHAR(10) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Individual skill gaps
CREATE TABLE IF NOT EXISTS skill_gaps (
    id VARCHAR(36) PRIMARY KEY,
    analysis_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    skill_category VARCHAR(50) NOT NULL,
    importance VARCHAR(20) NOT NULL,
    current_level INTEGER DEFAULT 0,
    required_level INTEGER NOT NULL,
    gap_score REAL NOT NULL,
    market_demand_score REAL,
    salary_impact REAL,
    job_postings_count INTEGER,
    recommended_resources TEXT,
    estimated_learning_hours INTEGER NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT 'intermediate',
    learning_progress REAL DEFAULT 0.0,
    target_completion_date TIMESTAMP,
    last_progress_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learning resources
CREATE TABLE IF NOT EXISTS learning_resources (
    id VARCHAR(36) PRIMARY KEY,
    skill_gap_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(200) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    url VARCHAR(500),
    estimated_hours INTEGER NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    cost REAL,
    rating REAL,
    relevance_score REAL NOT NULL,
    priority_rank INTEGER NOT NULL,
    is_bookmarked BOOLEAN DEFAULT FALSE,
    is_completed BOOLEAN DEFAULT FALSE,
    user_rating REAL,
    completion_date TIMESTAMP,
    data_source VARCHAR(100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skill progress tracking
CREATE TABLE IF NOT EXISTS skill_progress_tracking (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    current_level REAL NOT NULL,
    previous_level REAL,
    progress_percentage REAL NOT NULL,
    hours_invested REAL DEFAULT 0.0,
    resources_completed INTEGER DEFAULT 0,
    certifications_earned TEXT,
    self_assessment_score REAL,
    external_validation TEXT,
    skill_demonstration TEXT,
    learning_goal REAL,
    target_date TIMESTAMP,
    milestone_dates TEXT,
    progress_notes TEXT,
    ai_feedback TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skill market data
CREATE TABLE IF NOT EXISTS skill_market_data (
    id VARCHAR(36) PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    skill_category VARCHAR(50) NOT NULL,
    demand_score REAL NOT NULL,
    job_postings_count INTEGER DEFAULT 0,
    growth_rate REAL,
    average_salary_impact REAL,
    salary_percentile_50 REAL,
    salary_percentile_90 REAL,
    top_locations TEXT,
    remote_friendly BOOLEAN DEFAULT FALSE,
    top_industries TEXT,
    emerging_trend BOOLEAN DEFAULT FALSE,
    average_learning_time INTEGER,
    difficulty_rating REAL,
    prerequisite_skills TEXT,
    data_sources TEXT,
    confidence_score REAL NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learning paths
CREATE TABLE IF NOT EXISTS learning_paths (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    analysis_id VARCHAR(36) NOT NULL,
    path_name VARCHAR(200) NOT NULL,
    description TEXT,
    target_role VARCHAR(100),
    learning_steps TEXT NOT NULL,
    milestones TEXT NOT NULL,
    skill_progression TEXT NOT NULL,
    estimated_total_hours INTEGER NOT NULL,
    estimated_weeks INTEGER NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL,
    current_step INTEGER DEFAULT 0,
    completion_percentage REAL DEFAULT 0.0,
    hours_completed REAL DEFAULT 0.0,
    priority_order TEXT NOT NULL,
    market_alignment_score REAL NOT NULL,
    personalization_score REAL NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP,
    target_completion_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_skill_gap_analyses_user_job ON skill_gap_analyses(user_id, job_id);
CREATE INDEX IF NOT EXISTS idx_skill_gap_analyses_created ON skill_gap_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_skill_gaps_analysis ON skill_gaps(analysis_id);
CREATE INDEX IF NOT EXISTS idx_skill_gaps_user ON skill_gaps(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_gaps_skill_name ON skill_gaps(skill_name);
CREATE INDEX IF NOT EXISTS idx_learning_resources_skill_gap ON learning_resources(skill_gap_id);
CREATE INDEX IF NOT EXISTS idx_learning_resources_user ON learning_resources(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_progress_user_skill ON skill_progress_tracking(user_id, skill_name);
CREATE INDEX IF NOT EXISTS idx_skill_market_data_name ON skill_market_data(skill_name);
CREATE INDEX IF NOT EXISTS idx_learning_paths_user_analysis ON learning_paths(user_id, analysis_id);

-- Insert sample skill market data
INSERT OR IGNORE INTO skill_market_data (
    id, skill_name, skill_category, demand_score, job_postings_count, growth_rate,
    average_salary_impact, remote_friendly, confidence_score
) VALUES 
    ('skill_python', 'python', 'technical', 95.0, 9500, 18.5, 15000.0, TRUE, 90.0),
    ('skill_javascript', 'javascript', 'technical', 92.0, 9200, 15.2, 12000.0, TRUE, 90.0),
    ('skill_react', 'react', 'technical', 90.0, 9000, 20.1, 10000.0, TRUE, 85.0),
    ('skill_aws', 'aws', 'technical', 93.0, 9300, 25.3, 16000.0, TRUE, 88.0),
    ('skill_docker', 'docker', 'technical', 89.0, 8900, 22.7, 12000.0, TRUE, 85.0),
    ('skill_kubernetes', 'kubernetes', 'technical', 85.0, 8500, 28.4, 18000.0, TRUE, 82.0),
    ('skill_machine_learning', 'machine learning', 'domain', 88.0, 8800, 30.2, 22000.0, TRUE, 80.0),
    ('skill_leadership', 'leadership', 'soft', 95.0, 9500, 12.1, 25000.0, FALSE, 75.0),
    ('skill_communication', 'communication', 'soft', 98.0, 9800, 8.5, 15000.0, FALSE, 70.0),
    ('skill_typescript', 'typescript', 'technical', 88.0, 8800, 24.6, 14000.0, TRUE, 85.0);