# Phase 7 — Comprehensive Health & Readiness Probes

## Probe Endpoints

### 1. Liveness Probe: `GET /api/health/live`
- **Purpose**: Kubernetes / Docker container orchestrator liveness verification.
- **Contract**:
  - HTTP 200: Application event loop is running and accepting HTTP requests.
- **Payload**:
  ```json
  {
    "status": "alive",
    "timestamp": "2026-11-15T11:45:00.000000+00:00"
  }
  ```

### 2. Readiness Probe: `GET /api/health/ready`
- **Purpose**: Traffic admission check. Verifies critical core dependencies are functional before routing client traffic.
- **Contract**:
  - HTTP 200: All required dependencies (database ping, model provider initialization) are operational.
  - HTTP 503: Critical dependency unavailable (e.g. database disk locked or key missing).
- **Payload**:
  ```json
  {
    "status": "ready",
    "timestamp": "2026-11-15T11:45:00.000000+00:00",
    "database_ready": true,
    "model_ready": true
  }
  ```

### 3. Detailed Health Probe: `GET /api/health`
- **Purpose**: SRE diagnostic dashboard inspection. Backward-compatible with Phase 1-4 tests while providing dependency latencies.
- **Contract**:
  - HTTP 200: Healthy or degraded state.
- **Payload**:
  ```json
  {
    "status": "ok",
    "version": "0.2.0",
    "model_provider": "google_genai",
    "model_name": "gemini-2.5-flash",
    "langsmith_tracing": false,
    "uptime_seconds": 1420.5,
    "dependencies": [
      {
        "name": "memory_database",
        "status": "healthy",
        "latency_ms": 1.2
      },
      {
        "name": "telemetry_database",
        "status": "healthy",
        "latency_ms": 0.8
      },
      {
        "name": "model_provider",
        "status": "healthy"
      },
      {
        "name": "langsmith_tracing",
        "status": "degraded",
        "details": { "enabled": false, "active": false }
      }
    ]
  }
  ```
