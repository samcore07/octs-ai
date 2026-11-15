"""
OCTS AI - Memory Content & Privacy Validator
Ensures that persistent memories are free of sensitive PII, passwords, API credentials,
and ephemeral conversational filler, while enforcing size and craft relevance bounds.
"""

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger("octs.memory.validator")

# Sensitive data detection regex patterns
PII_PATTERNS = [
    # Credit Card numbers (13-16 digits)
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "credit_card"),
    # US Social Security Number
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "ssn"),
    # API Keys & Secrets
    (re.compile(r"(AIzaSy[0-9A-Za-z-_]{33})"), "gemini_api_key"),
    (re.compile(r"\b(sk-[a-zA-Z0-9]{20,})\b"), "generic_api_key"),
    (re.compile(r"(?i)\b(bearer\s+[a-zA-Z0-9_\-\.]{20,})\b"), "auth_token"),
    (re.compile(r"(?i)\b(password|passwd|secret)\s*[:=]\s*\S+"), "password"),
]

# Ephemeral conversational commands that should NEVER be stored as permanent memory
EPHEMERAL_COMMAND_PATTERNS = [
    re.compile(r"^(hi|hello|hey|greetings|thanks|thank you|ok|okay|bye|goodbye)[.!]?$", re.IGNORECASE),
    re.compile(r"^(can you|could you|please)\s+(help|write|generate|do this|answer|tell me)[^.?!]*[.?!]?$", re.IGNORECASE),
    re.compile(r"^(make it|do it)\s+(again|faster|shorter|longer)[.!]?$", re.IGNORECASE),
]


class MemoryValidator:
    """
    Validates candidate memory content before persistence.
    Protects user privacy and preserves memory store quality.
    """

    MAX_CONTENT_LENGTH = 10000
    MIN_CONTENT_LENGTH = 5

    def validate_content(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Validates content string. Returns (is_valid, rejection_reason).
        """
        if not content or not isinstance(content, str):
            return False, "Content is empty or invalid type."

        trimmed = content.strip()
        if len(trimmed) < self.MIN_CONTENT_LENGTH:
            return False, f"Content too brief ({len(trimmed)} chars; minimum {self.MIN_CONTENT_LENGTH})."

        if len(trimmed) > self.MAX_CONTENT_LENGTH:
            return False, f"Content exceeds maximum length ({len(trimmed)} chars; maximum {self.MAX_CONTENT_LENGTH})."

        # Check for ephemeral conversational commands
        for pat in EPHEMERAL_COMMAND_PATTERNS:
            if pat.match(trimmed):
                return False, "Content is an ephemeral conversational command, not permanent creative knowledge."

        # Check for sensitive personal information or API secrets
        for pat, name in PII_PATTERNS:
            if pat.search(trimmed):
                logger.warning(f"MemoryValidator rejected content containing sensitive data pattern: {name}")
                return False, f"Content contains prohibited sensitive or credential pattern: {name}."

        return True, None

    def sanitize_content(self, content: str) -> str:
        """
        Sanitizes text by stripping XML prompt injection tags or excessive whitespace.
        """
        if not content:
            return ""
        s = content.strip()
        # Escape delimiter injection attempts
        s = s.replace("<retrieved_memory_context>", "[[MEMORY_TAG_ESCAPED]]")
        s = s.replace("</retrieved_memory_context>", "[[MEMORY_TAG_ESCAPED]]")
        s = s.replace("<untrusted_candidate_output>", "[[CANDIDATE_TAG_ESCAPED]]")
        s = s.replace("</untrusted_candidate_output>", "[[CANDIDATE_TAG_ESCAPED]]")
        return s
