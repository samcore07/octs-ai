# Phase 3 API Reference: REST Endpoints & Contracts

This document defines the complete API contract for the **Octs AI** FastAPI backend during **Phase 3**, including endpoint specifications, schema fields, validation rules, HTTP status codes, and comprehensive request/response examples for all routing cases.

---

## Table of Contents

- [API Contract Principles](#api-contract-principles)
- [Endpoints Summary](#endpoints-summary)
- [Endpoint Specifications](#endpoint-specifications)
  - [POST /ask](#post-ask)
  - [GET /api/health](#get-apihealth)
  - [GET /](#get-)
  - [GET /ask](#get-ask)
- [Data Models (Pydantic v2)](#data-models-pydantic-v2)
- [Routing Case Examples](#routing-case-examples)
  - [Case A: Discipline & Specialist Clear](#case-a-discipline--specialist-clear)
  - [Case B: Discipline Known, Specialist Vague](#case-b-discipline-known-specialist-vague)
  - [Case C: Discipline Ambiguous (Zero-Token Clarification)](#case-c-discipline-ambiguous-zero-token-clarification)
  - [Case D: Invalid Input Validation Failure](#case-d-invalid-input-validation-failure)
- [Error Codes & Diagnostics](#error-codes--diagnostics)

---

## API Contract Principles

1. **Zero Breaking Changes**: The `reply` field in `POST /ask` is strictly mandatory across all outcomes (including clarification questions and handled fallbacks) to ensure 100% backward compatibility with legacy UI components.
2. **Strict Pydantic v2 Validation**: Request bodies are parsed and validated using Pydantic v2 schemas; whitespace-only strings and invalid discipline values are rejected at the gateway.
3. **Rich Telemetry Exposure**: Modern metadata (`agent_used`, `latency_ms`, `needs_clarification`, `routing_confidence`, `execution_status`) is supplied alongside creative outputs.

---

## Endpoints Summary

| Method | Path | Description | Auth | Response |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/ask` | Primary task execution endpoint powering the LangGraph harness. | None | `PromptResponse` |
| `GET` | `/api/health` | System health check and model diagnostics. | None | `HealthResponse` |
| `GET` | `/` | Serves the single-page application frontend (`index.html`). | None | `HTMLResponse` |
| `GET` | `/ask` | Informational fallback route for accidental browser GET requests. | None | `JSON (405 explanation)` |
| `GET` | `/style.css` | Serves root stylesheet. | None | `CSS` |
| `GET` | `/script.js` | Serves root application controller script. | None | `JavaScript` |

---

## Endpoint Specifications

### POST /ask
Executes a creative task through the single shared LangGraph orchestration pipeline.

- **URL**: `/ask`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body Schema (`PromptRequest`)

| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `prompt` | `string` | **Yes** | — | Creative task, inquiry, or directive (1 to 50,000 characters). Cannot be empty or purely whitespace. |
| `role` | `string` | Optional | `null` | Creative discipline: `writers`, `musicians`, `creators`, or `designers`. |
| `session_id` | `string` | Optional | `null` | Optional conversation or thread identifier for future stateful persistence. |
| `task_type` | `string` | Optional | `null` | Optional explicit task category override. |

#### Response Body Schema (`PromptResponse`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `reply` | `string` | **Mandatory**. The creative output text, or the clarification question if ambiguous. |
| `role` | `string \| null` | The creative discipline utilized (`writers`, `musicians`, `creators`, `designers`). |
| `agent_used` | `string \| null` | The identifier of the specialized persona that produced the output. |
| `trust_score` | `float \| null` | Reserved for Phase 4 craft evaluation rubrics (currently `null`). |
| `trust_breakdown` | `dict \| null` | Reserved for Phase 4 rubric breakdown (currently `null`). |
| `latency_ms` | `integer` | High-precision server execution latency in milliseconds. |
| `recovery_triggered`| `boolean` | Whether autonomous recovery loops were triggered (default: `false`). |
| `model_used` | `string` | The LLM provider model utilized (e.g. `gemini-3.5-flash-lite`). |
| `needs_clarification`| `boolean` | `true` if prompt was discipline-ambiguous (Case C); `false` otherwise. |
| `clarification_question`| `string \| null`| The targeted clarification question when `needs_clarification` is `true`. |
| `routing_confidence`| `float \| null` | Confidence score ($0.0$ to $1.0$) of the routing heuristic decision. |
| `execution_status` | `string` | Lifecycle status (`completed`, `completed_clarification_required`, `failed`). |

---

### GET /api/health
Health check endpoint reporting operational status, package version, active model provider, and distributed tracing status.

- **URL**: `/api/health`
- **Method**: `GET`
- **Example Response**:
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

### GET /
Serves the root single-page application interface.

- **URL**: `/`
- **Method**: `GET`
- **Response**: `200 OK` (Content-Type: `text/html; charset=utf-8`).

---

### GET /ask
Friendly fallback route intercepting accidental browser navigation.

- **URL**: `/ask`
- **Method**: `GET`
- **Response**: `200 OK`
```json
{
  "status": "error",
  "message": "The /ask endpoint requires an HTTP POST request with a JSON body: {\"prompt\": \"...\"}."
}
```

---

## Routing Case Examples

### Case A: Discipline & Specialist Clear

**Request**:
```json
POST /ask
{
  "prompt": "Give me a 2-line lyric with an AABB rhyme scheme about neon rain.",
  "role": "musicians"
}
```

**Response (200 OK)**:
```json
{
  "reply": "## 1. Meter & Prosody Blueprint\n\n* **Line 1:** The chromic puddles catch the gleam (8 syllables, iambic)\n* **Line 2:** As violet drops dissolve the seam (8 syllables, iambic)\n\n## 2. Structured Lyrics\n\n> The chromic **gleam**, the vi-o-**let**\n> Dissolves the **seam**, to drenched re-**gret**\n\n## 3. Rhyme Scheme & Acoustic Network Analysis\n* Exact A-Rhyme (gleam / seam)\n* Slant B-Rhyme (violet / regret)...",
  "role": "musicians",
  "agent_used": "lyricist_meter_engine",
  "trust_score": null,
  "trust_breakdown": null,
  "latency_ms": 3685,
  "recovery_triggered": false,
  "model_used": "gemini-3.5-flash-lite",
  "needs_clarification": false,
  "clarification_question": null,
  "routing_confidence": 0.85,
  "execution_status": "completed"
}
```

---

### Case B: Discipline Known, Specialist Vague

**Request**:
```json
POST /ask
{
  "prompt": "I am having creative block on how to move forward with my song",
  "role": "musicians"
}
```

**Response (200 OK)**:
```json
{
  "reply": "Creative block in arrangement usually happens because you are staring at a blank canvas with too many options... Drop your genre, tempo, and current chords below, and I will construct an arrangement blueprint.",
  "role": "musicians",
  "agent_used": "track_structure_architect",
  "trust_score": null,
  "trust_breakdown": null,
  "latency_ms": 1751,
  "recovery_triggered": false,
  "model_used": "gemini-3.5-flash-lite",
  "needs_clarification": false,
  "clarification_question": null,
  "routing_confidence": 0.5,
  "execution_status": "completed"
}
```

---

### Case C: Discipline Ambiguous (Zero-Token Clarification)

**Request**:
```json
POST /ask
{
  "prompt": "I want to create something interesting today"
}
```

**Response (200 OK)**:
```json
{
  "reply": "Which creative discipline are you working in? (Writers & Storytellers, Musicians & Singers, Content Creators, or Visual Artists & Designers)",
  "role": null,
  "agent_used": null,
  "trust_score": null,
  "trust_breakdown": null,
  "latency_ms": 7,
  "recovery_triggered": false,
  "model_used": "gemini-3.5-flash-lite",
  "needs_clarification": true,
  "clarification_question": "Which creative discipline are you working in? (Writers & Storytellers, Musicians & Singers, Content Creators, or Visual Artists & Designers)",
  "routing_confidence": 0.0,
  "execution_status": "completed_clarification_required"
}
```
*(Notice: Execution time is **7ms**, and **zero** tokens were consumed by the LLM).*

---

### Case D: Invalid Input Validation Failure

**Request (Invalid Role)**:
```json
POST /ask
{
  "prompt": "Design a logo",
  "role": "astrology_expert"
}
```

**Response (422 Unprocessable Entity)**:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "role"],
      "msg": "Value error, Invalid creative role 'astrology_expert'. Allowed roles: creators, designers, musicians, writers",
      "input": "astrology_expert"
    }
  ]
}
```

**Request (Empty Prompt)**:
```json
POST /ask
{
  "prompt": "   "
}
```

**Response (422 Unprocessable Entity)**:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "prompt"],
      "msg": "Value error, Prompt cannot be empty or solely whitespace.",
      "input": "   "
    }
  ]
}
```

---

## Error Codes & Diagnostics

| Status Code | Scenario | Payload Structure |
| :--- | :--- | :--- |
| `200 OK` | Successful execution, handled fallback, or clarification request. | `PromptResponse` JSON object. |
| `422 Unprocessable Entity`| Schema validation failure (empty prompt, whitespace, or invalid role). | Standard FastAPI `{"detail": [...]}` error array. |
| `500 Internal Server Error`| Unrecoverable downstream LLM exception (e.g. Google GenAI quota exceeded). | `{"detail": "Model execution error: <exception details>"}` |
