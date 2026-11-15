"""
OCTS AI - Memory Identity Provider Abstraction
Defines the IdentityProvider contract and standard implementations.
Provides honest documentation of identity resolution boundaries in unauthenticated vs authenticated environments.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("octs.memory.identity")


class IdentityContext(BaseModel):
    """
    Resolved caller identity context.
    Encapsulates identity boundaries and indicates whether the caller is cryptographically authenticated.
    """
    owner_id: str = Field(..., description="Unique persistent identifier for the identity.")
    is_authenticated: bool = Field(default=False, description="Whether identity is cryptographically verified.")
    identity_source: str = Field(default="anonymous", description="Method used to establish identity.")
    tenant_id: Optional[str] = Field(default=None, description="Optional tenant or organization identifier.")


class IdentityProvider(ABC):
    """
    Abstract interface for resolving caller identity.
    Enforces that caller-supplied owner_id in request bodies is never trusted as proof of identity.
    """

    @abstractmethod
    def resolve_identity(
        self,
        headers: Optional[Dict[str, str]] = None,
        explicit_owner_id: Optional[str] = None,
    ) -> IdentityContext:
        """
        Resolves identity context from request metadata.
        """
        pass


class HeaderIdentityProvider(IdentityProvider):
    """
    Resolves identity from trusted proxy or gateway HTTP headers (e.g. X-User-Id, X-Tenant-Id).
    Suitable for deployments behind an authenticating reverse proxy or API gateway.
    """

    def __init__(self, user_header: str = "x-user-id", default_owner_id: str = "default_user"):
        self.user_header = user_header.lower()
        self.default_owner_id = default_owner_id

    def resolve_identity(
        self,
        headers: Optional[Dict[str, str]] = None,
        explicit_owner_id: Optional[str] = None,
    ) -> IdentityContext:
        headers = headers or {}
        normalized = {k.lower(): v for k, v in headers.items()}

        if self.user_header in normalized and normalized[self.user_header].strip():
            user_id = normalized[self.user_header].strip()
            return IdentityContext(
                owner_id=user_id,
                is_authenticated=True,
                identity_source="header",
                tenant_id=normalized.get("x-tenant-id"),
            )

        # Fallback to local default identity when header is omitted
        return IdentityContext(
            owner_id=self.default_owner_id,
            is_authenticated=False,
            identity_source="local_default",
        )


class AnonymousIdentityProvider(IdentityProvider):
    """
    Fallback identity provider for local single-user installations.
    Binds all requests to a shared local identity.
    Clearly marks is_authenticated=False to acknowledge lack of multi-tenant isolation.
    """

    def __init__(self, default_owner_id: str = "default_user"):
        self.default_owner_id = default_owner_id

    def resolve_identity(
        self,
        headers: Optional[Dict[str, str]] = None,
        explicit_owner_id: Optional[str] = None,
    ) -> IdentityContext:
        # In unauthenticated mode, if an explicit_owner_id is provided in a development setting,
        # it can be accepted for testing purposes, but is flagged as unauthenticated.
        owner = (explicit_owner_id or "").strip() or self.default_owner_id
        return IdentityContext(
            owner_id=owner,
            is_authenticated=False,
            identity_source="anonymous_dev",
        )
