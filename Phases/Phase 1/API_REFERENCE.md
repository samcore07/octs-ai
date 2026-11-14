# Phase 1: API Reference

This document provides complete technical specifications for all API endpoints and static file routes implemented in **Phase 1** of **Octs AI**.

---

## Table of Contents

- [Overview & Base URL](#overview--base-url)
- [Endpoints Summary](#endpoints-summary)
- [Endpoint Details](#endpoint-details)
  - [1. Health Check — GET /api/health](#1-health-check--get-apihealth)
  - [2. Creative Prompt Inference — POST /ask](#2-creative-prompt-inference--post-ask)
  - [3. Fallback Method Guard — GET /ask](#3-fallback-method-guard--get-ask)
  - [4. Frontend Entrypoint — GET /](#4-frontend-entrypoint--get-)
  - [5. Static Asset Mounting — GET /*](#5-static-asset-mounting--get-)
- [Validation & Error Codes](#validation--error-codes)
- [CORS Policies & Headers](#cors-policies--headers)

---

## Overview & Base URL

The API is exposed via FastAPI and runs on an ASGI server (Uvicorn).

- **Default Local Base URL**: `http://127.0.0.1:8000`
- **Content Type**: `application/json` (except static routes which return `text/html`, `text/css`, or `application/javascript`)
- **API Version**: `0.2.0`

---

## Endpoints Summary

| Method | Path | Purpose | Auth | Schema In | Schema Out |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health & telemetry status | Public | None | `HealthResponse` |
| `POST` | `/ask` | Submit prompt for creative inference | Public | `PromptRequest` | `PromptResponse` |
| `GET` | `/ask` | Method not allowed guard with guidance | Public | None | Error JSON (405) |
| `GET` | `/` | Serve main creative dashboard | Public | None | HTML |
| `GET` | `/{path:path}` | Serve static assets (`pages/`, `css/`, `js/`) | Public | None | Static files |

---

## Endpoint Details

### 1. Health Check — `GET /api/health`

#### Purpose
Returns operational telemetry, server version, configured model provider, model identifier, and LangSmith tracing state. Suitable for container health checks, uptime monitors, and integration verifications.

#### Request
- **Headers**: None required.
- **Parameters**: None.
- **Body**: None.

#### Response Schema (`HealthResponse`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "HealthResponse",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "example": "ok"
    },
    "version": {
      "type": "string",
      "example": "0.2.0"
    },
    "model_provider": {
      "type": "string",
      "example": "google_genai"
    },
    "model_name": {
      "type": "string",
      "example": "gemini-3.5-flash-lite"
    },
    "langsmith_tracing": {
      "type": "boolean",
      "example": false
    }
  },
  "required": ["status", "version", "model_provider", "model_name", "langsmith_tracing"]
}
```

#### Example cURL
```bash
curl -X GET http://127.0.0.1:8000/api/health
```

#### Example Response (HTTP 200 OK)
```json
{
  "status": "ok",
  "version": "0.2.0",
  "model_provider": "google_genai",
  "model_name": "gemini-3.5-flash-lite",
  "langsmith_tracing": false
}
```

---

### 2. Creative Prompt Inference — `POST /ask`

#### Purpose
Processes a creative query or prompt against the configured LLM engine. Maintains strict backward compatibility with the frontend's expected `{ "reply": "..." }` response contract while attaching execution metadata.

#### Request Schema (`PromptRequest`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PromptRequest",
  "type": "object",
  "properties": {
    "prompt": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50000,
      "description": "Creative input text or instructions."
    },
    "role": {
      "type": "string",
      "default": "general",
      "enum": ["writers", "musicians", "creators", "designers", "general"],
      "description": "Creative discipline targeting the task."
    },
    "session_id": {
      "type": "string",
      "nullable": true,
      "description": "Optional session or thread identifier."
    }
  },
  "required": ["prompt"]
}
```

#### Request Validation Rules
- `prompt`: Must not be null or empty. Leading and trailing whitespace is automatically stripped. Must not be empty after stripping. Length must be $\le 50,000$ characters.
- `role`: Normalized to lowercase string. Must match one of the allowed disciplines: `writers`, `musicians`, `creators`, `designers`, or `general`. Defaults to `general` if omitted.

#### Response Schema (`PromptResponse`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PromptResponse",
  "type": "object",
  "properties": {
    "reply": {
      "type": "string",
      "description": "Generated response text (strictly backward-compatible)."
    },
    "role": {
      "type": "string",
      "description": "Discipline role applied during inference."
    },
    "agent_used": {
      "type": "string",
      "default": "direct_model",
      "description": "Agent persona used to generate the output."
    },
    "trust_score": {
      "type": "number",
      "nullable": true,
      "description": "Craft evaluation score (Phase 2 feature; currently null)."
    },
    "trust_breakdown": {
      "type": "object",
      "nullable": true,
      "description": "Evaluation breakdown dictionary (Phase 2 feature; currently null)."
    },
    "latency_ms": {
      "type": "number",
      "description": "Model execution latency in milliseconds."
    },
    "recovery_triggered": {
      "type": "boolean",
      "default": false,
      "description": "Whether error recovery was performed."
    },
    "model_used": {
      "type": "string",
      "description": "Identifier of the model that executed the task."
    }
  },
  "required": ["reply", "role", "agent_used", "latency_ms", "recovery_triggered", "model_used"]
}
```

#### Example cURL (Standard Prompt)
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How can I introduce dramatic irony in chapter three of a mystery novel?",
    "role": "writers"
  }'
```

#### Example Response (HTTP 200 OK)
```json
{
  "reply": "To introduce dramatic irony in chapter three, allow the audience to observe a clue that your detective overlooks...",
  "role": "writers",
  "agent_used": "direct_model",
  "trust_score": null,
  "trust_breakdown": null,
  "latency_ms": 1142.85,
  "recovery_triggered": false,
  "model_used": "gemini-3.5-flash-lite"
}
```

---

### 3. Fallback Method Guard — `GET /ask`

#### Purpose
Prevents confusing `405 Method Not Allowed` default HTML responses when developers or users accidentally navigate to `/ask` in a web browser.

#### Response Status
- `HTTP 405 Method Not Allowed`

#### Response Body
```json
{
  "status": "error",
  "message": "The /ask endpoint requires an HTTP POST request with a JSON body: {\"prompt\": \"...\", \"role\": \"...\"}."
}
```

#### Example cURL
```bash
curl -X GET http://127.0.0.1:8000/ask
```

---

### 4. Frontend Entrypoint — `GET /`

#### Purpose
Serves the primary single-page application entrypoint `index.html`.

#### Request
- **Headers**: `Accept: text/html`

#### Response
- **Status**: `200 OK`
- **Content-Type**: `text/html; charset=utf-8`
- **Body**: Complete raw contents of `index.html`.

---

### 5. Static Asset Mounting — `GET /*`

#### Purpose
Mounts the root project directory via FastAPI `StaticFiles` to serve frontend styles, JavaScript bundles, subpages, and asset files.

#### Accessible Routes
- `/pages/writers.html`
- `/pages/musicians.html`
- `/pages/creators.html`
- `/pages/designers.html`
- `/css/style.css`
- `/css/dashboard.css`
- `/js/main.js`
- `/js/dashboard.js`

---

## Validation & Error Codes

FastAPI and Pydantic enforce standard HTTP error responses:

| HTTP Status | Error Scenario | Example Trigger |
| :--- | :--- | :--- |
| **400 Bad Request** | Invalid role discipline | `{"prompt": "hello", "role": "astronaut"}` |
| **405 Method Not Allowed** | Unsupported HTTP method on `/ask` | `GET /ask` |
| **422 Unprocessable Entity** | Empty prompt or invalid JSON structure | `{"prompt": ""}` or `{"prompt": "   "}` |
| **500 Internal Server Error** | Model provider or downstream runtime error | Provider API error or quota depletion |

### Example 422 Validation Error Response
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "prompt"],
      "msg": "String should have at least 1 characters",
      "input": ""
    }
  ]
}
```

### Example 400 Bad Request Response
```json
{
  "detail": "Invalid role 'astronaut'. Allowed roles: writers, musicians, creators, designers, general."
}
```

---

## CORS Policies & Headers

CORS behavior is governed by `backend.config.settings.cors_origins`.
- By default, allowed origins are:
  - `http://127.0.0.1:8000`
  - `http://localhost:8000`
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- Configurable at runtime via the `CORS_ORIGINS` environment variable (e.g., `CORS_ORIGINS="https://app.octsai.com,http://localhost:8000"`).
- Supported methods: `*`
- Supported headers: `*`
- Credentials supported: `allow_credentials=True`
