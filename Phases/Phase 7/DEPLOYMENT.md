# Phase 7 — Production Deployment Guide

## Environment Configuration
The following environment variables govern observability and monitoring:

```bash
# Server & Logging
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR
STRUCTURED_LOGGING=true                 # Enable RFC 8259 JSON structured logging

# Telemetry Persistence
TELEMETRY_DATABASE_URL=sqlite:///./octs_telemetry.db
TELEMETRY_RETENTION_DAYS=30

# Health & Metrics Probes
HEALTH_CHECK_TIMEOUT_SECONDS=2.0
```

## Running the Application
```bash
python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

## Container Orchestration Integration (Kubernetes / ECS)
- **Liveness Probe**:
  - Path: `/api/health/live`
  - Port: 8000
  - Initial Delay: 5s
  - Period: 10s
- **Readiness Probe**:
  - Path: `/api/health/ready`
  - Port: 8000
  - Initial Delay: 5s
  - Period: 10s
  - Failure Threshold: 3
