# Phase 7 — Analytics API Specification

## Endpoints

### 1. `GET /api/analytics/overview`
Returns aggregate throughput, success rate, latency percentiles, and quality averages.
- **Query Parameters**:
  - `start_date` (optional ISO 8601 string)
  - `end_date` (optional ISO 8601 string)
  - `discipline` (optional filter: `writers`, `musicians`, `creators`, `designers`)
- **Response**: `AnalyticsOverviewResponse`

### 2. `GET /api/analytics/requests`
Returns paginated operational telemetry records.
- **Query Parameters**:
  - `start_date`, `end_date`, `discipline`, `status`
  - `limit` (default 50, max 200)
  - `offset` (default 0)

### 3. `GET /api/analytics/disciplines`
Returns per-discipline comparison for all four creative disciplines.

### 4. `GET /api/analytics/personas`
Returns usage frequency, average latency, and average quality scores grouped by specialist persona.

### 5. `GET /api/analytics/evaluation`
Returns evaluation statistics, TrustScore distribution, and coverage.

### 6. `GET /api/analytics/refinement`
Returns autonomous self-correction metrics: attempts, accepted, rejected, reversions, and acceptance percentage.

### 7. `GET /api/analytics/memory`
Returns context retrieval frequency, average retrieved items per request, extracted memory counts, and persistence success rate.

### 8. `GET /api/analytics/model-usage`
Returns total model calls, total tokens, provider name, and model name.

### 9. `GET /api/analytics/events`
Returns paginated execution events filterable by `request_id` or `event_name`.
