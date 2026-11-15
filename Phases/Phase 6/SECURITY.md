# OCTS AI — Phase 6: Security, Isolation & Identity Boundaries

## 1. Multi-Tenant Scoping & User Isolation

In production environments, memory records must be strictly isolated by tenant identity.

### Invariants:
1. **Repository Scope Filtering**: Every candidate query in `MemoryRepository.query_retrieval_candidates()` appends `MemoryRecordORM.owner_id == owner_id`. It is architecturally impossible to retrieve memories belonging to another user.
2. **Project Scope Filtering**: Memories with `scope="project"` require an exact match on `project_id`. If a user does not specify an active project, all project-scoped memories are excluded from retrieval.
3. **Discipline Isolation**: Discipline-scoped memories (`scope="discipline"`) are isolated to their domain. For example, a music tempo constraint will never contaminate a screenplay generation prompt.

---

## 2. Identity Provider Abstraction

OCTS AI models authentication boundaries cleanly via `IdentityProvider`:

```python
class IdentityProvider(ABC):
    @abstractmethod
    def resolve_identity(self, headers: Optional[Dict[str, str]] = None) -> IdentityContext:
        """Resolves identity from trusted proxy headers or returns fallback."""
        pass
```

### Production vs Local Development:
- **Authenticated Proxy (`HeaderIdentityProvider`)**: Resolves caller identity from verified headers (e.g., `X-User-Id`, `X-Forwarded-User`, or API gateway JWT claims).
- **Local Development (`AnonymousIdentityProvider`)**: Falls back to `default_user` when headers are absent, allowing local testing without authentication infrastructure.
- **Architectural Boundary Honesty**: Raw incoming HTTP headers in public environments cannot be trusted without an upstream reverse proxy (Envoy, NGINX, Cloudflare) that validates credentials and strips spoofed headers.

---

## 3. Privacy, PII & Secret Scrubbing

The `MemoryValidator` executes proactive regex sanitization before candidate records are admitted:
1. **Credit Cards**: Matches standard Visa, MasterCard, and Amex PAN patterns.
2. **Social Security Numbers**: Matches standard `XXX-XX-XXXX` formats.
3. **API Keys & Tokens**: Matches provider key formats (Google AI Studio `AIzaSy...`, AWS `AKIA...`, OpenAI `sk-...`, GitHub `ghp_...`).
4. **Delimiter Sanitization**: Strips injected XML delimiters (`<retrieved_memory_context>`, `</retrieved_memory_context>`) from candidate text to prevent prompt injection breakouts.
