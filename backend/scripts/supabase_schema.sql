-- ============================================================================
-- OCTS AI - Supabase Cloud Database Schema & Migration Script
-- Run this in your Supabase Project SQL Editor to initialize all tables & indexes.
-- ============================================================================

-- 1. Creative Projects Table
CREATE TABLE IF NOT EXISTS public.projects (
    project_id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(128) NOT NULL DEFAULT 'default_user',
    name VARCHAR(200) NOT NULL,
    description TEXT,
    discipline VARCHAR(32),
    metadata_json JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_projects_owner_active ON public.projects (owner_id, is_active);
CREATE INDEX IF NOT EXISTS idx_projects_discipline ON public.projects (discipline);

-- 2. Creative Memory Records Table
CREATE TABLE IF NOT EXISTS public.memory_records (
    memory_id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(128) NOT NULL DEFAULT 'default_user',
    memory_type VARCHAR(32) NOT NULL,
    scope VARCHAR(32) NOT NULL,
    discipline VARCHAR(32),
    project_id VARCHAR(36) REFERENCES public.projects(project_id) ON DELETE SET NULL,
    session_id VARCHAR(128),
    content TEXT NOT NULL,
    structured_data_json JSONB DEFAULT '{}'::jsonb,
    source VARCHAR(32) NOT NULL DEFAULT 'user_explicit',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    importance DOUBLE PRECISION NOT NULL DEFAULT 0.7,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    last_accessed_at TIMESTAMPTZ,
    access_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    version INTEGER NOT NULL DEFAULT 1,
    superseded_by VARCHAR(36)
);

CREATE INDEX IF NOT EXISTS idx_memory_owner_status ON public.memory_records (owner_id, status);
CREATE INDEX IF NOT EXISTS idx_memory_project_status ON public.memory_records (project_id, status);
CREATE INDEX IF NOT EXISTS idx_memory_owner_type ON public.memory_records (owner_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_owner_discipline ON public.memory_records (owner_id, discipline);
CREATE INDEX IF NOT EXISTS idx_memory_scope ON public.memory_records (scope);

-- 3. Operational Request Telemetry Table
CREATE TABLE IF NOT EXISTS public.request_telemetry (
    request_id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    duration_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    discipline VARCHAR(32),
    persona_id VARCHAR(64),
    model_name VARCHAR(64),
    quality_score DOUBLE PRECISION,
    reliability_score DOUBLE PRECISION,
    trust_score DOUBLE PRECISION,
    refinement_triggered BOOLEAN NOT NULL DEFAULT false,
    recovery_attempts INTEGER NOT NULL DEFAULT 0,
    reverted_to_baseline BOOLEAN NOT NULL DEFAULT false,
    memory_injected BOOLEAN NOT NULL DEFAULT false,
    memory_count INTEGER NOT NULL DEFAULT 0,
    error_type VARCHAR(64),
    error_message TEXT,
    client_ip VARCHAR(64),
    user_agent TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON public.request_telemetry (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_status ON public.request_telemetry (status);
CREATE INDEX IF NOT EXISTS idx_telemetry_discipline ON public.request_telemetry (discipline);
CREATE INDEX IF NOT EXISTS idx_telemetry_persona ON public.request_telemetry (persona_id);

-- 4. Execution Events Table
CREATE TABLE IF NOT EXISTS public.execution_events (
    event_id VARCHAR(36) PRIMARY KEY,
    request_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    event_type VARCHAR(64) NOT NULL,
    component VARCHAR(64) NOT NULL,
    duration_ms DOUBLE PRECISION,
    payload_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_events_request_id ON public.execution_events (request_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON public.execution_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_type ON public.execution_events (event_type);

-- 5. Row Level Security (RLS) Configuration
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memory_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.request_telemetry ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.execution_events ENABLE ROW LEVEL SECURITY;

-- Allow public / anon and service_role full access for creative harness API
CREATE POLICY "Allow public read/write on projects" ON public.projects FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public read/write on memory_records" ON public.memory_records FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public read/write on request_telemetry" ON public.request_telemetry FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public read/write on execution_events" ON public.execution_events FOR ALL USING (true) WITH CHECK (true);
