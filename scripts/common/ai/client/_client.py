"""The one model-call primitive: a schema-constrained structured completion.

Structured output is obtained via a single forced tool call — the model must
call ``report`` with input matching the caller's JSON schema. Forcing the tool
guides the model, but the returned ``tool_use.input`` is still **validated
locally** against that schema (via the repo's existing ``jsonschema``
``Draft7Validator``) before it is handed back, so a drifted or malformed result
fails cleanly and testably instead of surfacing as a downstream ``KeyError``.

Three shared policies live here, not in each tool (see AiCommon.md §1):

- **Explicit model per call.** There is no default model and no run-wide override;
  every ``structured`` call names its tier (:data:`~common.ai.client.CHEAP_MODEL` /
  :data:`~common.ai.client.TRUSTED_MODEL`), so the tiering principle is forced into
  the open — nothing silently inherits the cheap tier, and nothing can globally
  re-tier a tool (which would, e.g., downgrade the trusted citation judgment).
  Changing a tool's model means changing that tier constant, deliberately.
- **A per-run request-count cap.** The only thing worth guarding against is a
  bug firing unbounded calls; the client aborts past ``max_requests``.
- **Token accounting.** Each response's ``usage`` accrues into ``self.usage``;
  the CLIs print the total at the end of a run (visibility, not enforcement).

The AI is the deliverable, so a missing key is fatal: :func:`require_ai_client`
raises rather than degrading to a static-only mode.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Protocol, cast

from jsonschema import Draft7Validator
from jsonschema import ValidationError as SchemaError

from .types import (
    MAX_REQUESTS,
    AiBudgetError,
    AiError,
    AiModelName,
    AiModelResult,
    AiUnavailableError,
    Usage,
)

if TYPE_CHECKING:
    from common.types import JsonSchema


def anthropic_api_key() -> str | None:
    """The Anthropic API key from the environment, or ``None`` if unset.

    Presence is the master switch: these tools are the AI-judgment layer, so a
    missing key is a fatal error at startup, not a degrade-to-static path.
    """
    return os.environ.get("ANTHROPIC_API_KEY", "").strip() or None


def _validate(data: AiModelResult, schema: JsonSchema) -> AiModelResult:
    """Return ``data`` if it satisfies ``schema``, else raise :class:`AiError`."""
    try:
        Draft7Validator(schema).validate(data)
    except SchemaError as exc:
        raise AiError(
            f"structured output failed schema validation: {exc.message}"
        ) from exc
    return data


class _Messages(Protocol):
    """The one transport method used — an injection seam for tests."""

    def create(self, **kwargs: object) -> object: ...


class _Transport(Protocol):
    """Duck-typed stand-in for ``anthropic.Anthropic`` (real or fake)."""

    @property
    def messages(self) -> _Messages: ...


class AnthropicClient:
    """An :class:`~common.ai.client.AiClient` backed by the Messages API.

    ``_transport`` is the test seam: any object exposing ``messages.create(...)``
    works, so unit tests never hit the network.
    """

    def __init__(
        self,
        api_key: str,
        *,
        max_requests: int = MAX_REQUESTS,
        _transport: _Transport | None = None,
    ) -> None:
        if _transport is None:
            import anthropic

            _transport = cast("_Transport", anthropic.Anthropic(api_key=api_key))
        self._client: _Transport = _transport
        self._max_requests = max_requests
        self._requests = 0
        self._usage = Usage()

    @property
    def usage(self) -> Usage:
        """Cumulative token usage across this run's calls."""
        return self._usage

    @property
    def request_count(self) -> int:
        return self._requests

    def structured(
        self,
        *,
        system: str,
        user: str,
        schema: JsonSchema,
        model: AiModelName,
        max_tokens: int = 512,
    ) -> AiModelResult:
        if self._requests >= self._max_requests:
            raise AiBudgetError(
                f"per-invocation AI-call ceiling reached ({self._max_requests}) — "
                f"this run is trying to make more calls than one invocation allows; "
                f"scope it to fewer patches and run again"
            )
        self._requests += 1
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=[
                {
                    "name": "report",
                    "description": "Return the structured result for this check.",
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": "report"},
            messages=[{"role": "user", "content": user}],
        )
        self._accrue(getattr(response, "usage", None))
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "tool_use":
                payload = getattr(block, "input", None)
                if isinstance(payload, dict):
                    data = {str(key): value for key, value in payload.items()}
                    return _validate(data, schema)
        raise AiError("model returned no tool_use block")

    def _accrue(self, usage: object | None) -> None:
        """Add one response's token usage to the running total."""
        if usage is None:
            return
        self._usage += Usage(
            int(getattr(usage, "input_tokens", 0) or 0),
            int(getattr(usage, "output_tokens", 0) or 0),
        )


def require_ai_client(*, max_requests: int = MAX_REQUESTS) -> AnthropicClient:
    """Build the client, or raise :class:`AiUnavailableError` if no key.

    The AI is the deliverable, so a missing key is fatal — call this once at
    startup, before doing any work, and let the exception surface.
    """
    key = anthropic_api_key()
    if key is None:
        raise AiUnavailableError(
            "ANTHROPIC_API_KEY is not set. These tools are AI-backed and require "
            "a key — export ANTHROPIC_API_KEY and re-run."
        )
    return AnthropicClient(key, max_requests=max_requests)
