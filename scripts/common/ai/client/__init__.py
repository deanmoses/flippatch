"""The shared structured-call client and its public type vocabulary.

Public surface split across two modules — :mod:`~common.ai.client.types`
(the declarations: the :data:`AiModelName` tier vocabulary, the
:data:`AiModelResult` alias, :class:`Usage`, the :class:`AiClient` protocol,
the errors) and :mod:`~common.ai.client._client` (the implementation) — and
re-exported here so every caller imports from one namespace::

    from common.ai.client import structured, TRUSTED_MODEL, AiError
"""

from __future__ import annotations

from ._client import AnthropicClient, require_ai_client
from .types import (
    CHEAP_MODEL,
    MAX_REQUESTS,
    TRUSTED_MODEL,
    AiBudgetError,
    AiClient,
    AiError,
    AiModelName,
    AiModelResult,
    AiUnavailableError,
    Usage,
)

__all__ = [
    "CHEAP_MODEL",
    "MAX_REQUESTS",
    "TRUSTED_MODEL",
    "AiBudgetError",
    "AiClient",
    "AiError",
    "AiModelName",
    "AiModelResult",
    "AiUnavailableError",
    "AnthropicClient",
    "Usage",
    "require_ai_client",
]
