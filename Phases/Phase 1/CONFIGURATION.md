# Phase 1: Environment & Configuration Guide

This document describes the configuration system, environment variables, validation mechanisms, and security rules implemented in **Phase 1** of **Octs AI**.

---

## Table of Contents

- [Overview](#overview)
- [The Pydantic Settings Architecture](#the-pydantic-settings-architecture)
- [Canonical Environment Template (`.env.example`)](#canonical-environment-template-envexample)
- [Configuration Reference Matrix](#configuration-reference-matrix)
- [Detailed Variable Specifications](#detailed-variable-specifications)
  - [Google Gemini Settings](#google-gemini-settings)
  - [LangSmith Tracing Settings](#langsmith-tracing-settings)
  - [Security & CORS Settings](#security--cors-settings)
  - [Execution Limits & Guards](#execution-limits--guards)
- [Validation & Coercion Rules](#validation--coercion-rules)
- [Local Development Setup](#local-development-setup)
- [Troubleshooting Configuration Issues](#troubleshooting-configuration-issues)

---

## Overview

In Phase 1, configuration management was upgraded from scattered `os.getenv()` statements to a centralized, validated `Settings` class defined in `backend/config.py` using `pydantic-settings`.

Key benefits:
- **Strict Typing**: Environment variables are parsed into typed Python values (`str`, `int`, `float`, `bool`, `list[str]`, `set[str]`).
- **Default Fallbacks**: Safe production defaults are established for non-sensitive parameters.
- **Fail-Safe Loading**: The `.env` file is loaded automatically without crashing if optional variables are absent.
- **Zero Hardcoded Secrets**: Secrets are isolated to local `.env` files that are ignored by Git.

---

## The Pydantic Settings Architecture

Configuration is defined in `backend/config.py`:

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # Typed settings fields...
```

At application boot, `server.py` imports a singleton instance:
```python
from backend.config import settings
```

This guarantees consistent configuration across all server modules and test fixtures.

---

## Canonical Environment Template (`.env.example`)

The official template for configuring the Octs AI backend is `.env.example`:

```bash
# Model Provider Configuration
GEMINI_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-3.5-flash-lite
MODEL_PROVIDER=google_genai
MODEL_TEMPERATURE=0.0

# LangSmith Observability & Tracing (Optional)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=octs-ai
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# CORS Configuration (comma-separated list of allowed origins)
CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000,http://localhost:3000,http://127.0.0.1:3000
```

> [!CAUTION]
> Never commit actual API keys or secrets to version control. The repository `.gitignore` ensures that `.env` remains untracked. Always reference `.env.example` when sharing configuration templates.

---

## Configuration Reference Matrix

| Variable Name | Type | Default Value | Required? | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | `str` | `None` | **Yes** (at runtime) | Authentication key for Google Gemini GenAI API. |
| `MODEL_NAME` | `str` | `"gemini-3.5-flash-lite"` | No | Target Gemini model identifier. |
| `MODEL_PROVIDER` | `str` | `"google_genai"` | No | Provider abstraction identifier. |
| `MODEL_TEMPERATURE`| `float` | `0.0` | No | Sampling temperature ($0.0$ = deterministic). |
| `LANGSMITH_TRACING` | `bool` | `False` | No | Enables or disables LangSmith trace export. |
| `LANGSMITH_API_KEY` | `str` | `None` | Optional | API key for LangSmith tracing platform. |
| `LANGSMITH_PROJECT` | `str` | `"octs-ai"` | No | Project workspace name inside LangSmith. |
| `LANGSMITH_ENDPOINT`| `str` | `"https://api.smith.langchain.com"` | No | Ingestion endpoint URL for LangSmith traces. |
| `CORS_ORIGINS` | `list[str]` | `["http://127.0.0.1:8000", ...]` | No | Comma-separated list of allowed web origins. |

---

## Detailed Variable Specifications

### Google Gemini Settings

#### `GEMINI_API_KEY`
- **Type**: `Optional[str]`
- **Purpose**: Authenticates calls made to Google Generative AI (`ChatGoogleGenerativeAI`).
- **Behavior**: If missing during a live model invocation, the provider raises an authentication error. During testing or offline development, the model object is mocked.
- **Provider Synchronization**: `server.py` sets both `GEMINI_API_KEY` and `GOOGLE_API_KEY` in `os.environ` from this setting to satisfy different Google client library conventions.

#### `MODEL_NAME`
- **Type**: `str`
- **Default**: `"gemini-3.5-flash-lite"`
- **Purpose**: Identifies the Gemini model version. Defaults to the lightweight, low-latency Flash Lite model optimized for creative craft analysis.

#### `MODEL_TEMPERATURE`
- **Type**: `float`
- **Default**: `0.0`
- **Validation**: Bounded between `0.0` and `2.0`.
- **Purpose**: Governs model randomness. A value of `0.0` ensures predictable and structured evaluation results.

---

### LangSmith Tracing Settings

#### `LANGSMITH_TRACING`
- **Type**: `bool`
- **Default**: `False`
- **Behavior**: Coerced by Pydantic from `"true"`, `"1"`, `"false"`, or `"0"`. When `False`, LangSmith tracing is completely bypassed.

#### `LANGSMITH_API_KEY`
- **Type**: `Optional[str]`
- **Default**: `None`
- **Behavior**: Evaluated by `backend.tracing.setup_tracing()`. If `LANGSMITH_TRACING=true` but `LANGSMITH_API_KEY` is missing or contains the placeholder string `"your_langsmith_api_key_here"`, the system disables tracing and logs a warning instead of failing.

#### `LANGSMITH_PROJECT`
- **Type**: `str`
- **Default**: `"octs-ai"`
- **Purpose**: The project container under which LangChain execution traces, tokens, and latencies are recorded in LangSmith.

#### `LANGSMITH_ENDPOINT`
- **Type**: `str`
- **Default**: `"https://api.smith.langchain.com"`
- **Purpose**: The destination REST endpoint for trace collection.

---

### Security & CORS Settings

#### `CORS_ORIGINS`
- **Type**: `list[str]`
- **Default**:
  ```python
  [
      "http://127.0.0.1:8000",
      "http://localhost:8000",
      "http://localhost:3000",
      "http://127.0.0.1:3000",
  ]
  ```
- **Parsing Logic**: If specified in `.env` as a string (e.g., `http://example.com,http://localhost:8000`), a Pydantic `@field_validator` automatically splits the comma-separated tokens, strips extraneous whitespace, and discards empty values.

---

### Execution Limits & Guards

These settings are built into `backend/config.py` to prevent runaway agent loops and malicious resource exhaustion:

- `max_recursion_limit`: `15` — Maximum depth of future LangGraph state transitions.
- `max_recovery_attempts`: `2` — Maximum automated recovery cycles before raising a craft halt.
- `max_prompt_length`: `50,000` — Maximum length of prompt input strings.
- `allowed_disciplines`: `{"writers", "musicians", "creators", "designers"}` — Canonical whitelist of valid creative roles.

---

## Validation & Coercion Rules

Pydantic validates each setting upon class instantiation:
1. **Type Coercion**: String values from `.env` are automatically cast to target types (e.g., `"0.0"` to `float(0.0)`, `"true"` to `bool(True)`).
2. **Custom Validators**:
   - `parse_cors_origins`: Converts comma-delimited strings to `list[str]`.
   - `validate_temperature`: Enforces `0.0 <= model_temperature <= 2.0`.
3. **Extra Keys**: Set to `extra="ignore"`, preventing crashes if additional environment variables exist on the host.

---

## Local Development Setup

To configure a local environment:

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Add your Gemini API Key**:
   Open `.env` in your editor and assign your key:
   ```bash
   GEMINI_API_KEY=AIzaSy...
   ```

3. **Verify Configuration Parsing**:
   Run the automated configuration test suite:
   ```bash
   python3 -m pytest backend/tests/test_config.py -v
   ```

4. **Optional: Enable LangSmith Tracing**:
   If you have a LangSmith account and wish to observe latency and token metrics:
   ```bash
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=lsv2_pt_...
   LANGSMITH_PROJECT=octs-ai
   ```

---

## Troubleshooting Configuration Issues

### 1. `ValidationError: 1 validation error for Settings`
- **Cause**: An invalid data type was provided in `.env` (e.g., `MODEL_TEMPERATURE=warm`).
- **Fix**: Check `.env` and ensure `MODEL_TEMPERATURE` is a floating-point number between `0.0` and `2.0`.

### 2. Tracing Warning in Logs
- **Log message**: `[tracing] LANGSMITH_TRACING is true but no valid LANGSMITH_API_KEY is configured. Tracing disabled.`
- **Cause**: `LANGSMITH_TRACING=true` was set without providing a real key.
- **Fix**: Either provide a valid `LANGSMITH_API_KEY` or set `LANGSMITH_TRACING=false`. The application will continue running normally.

### 3. Cross-Origin (CORS) Block in Browser
- **Cause**: The client frontend is being served from an origin not present in `CORS_ORIGINS`.
- **Fix**: Append the client origin to `CORS_ORIGINS` in `.env`:
  ```bash
  CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:5173
  ```
