"""Tests for common.ai.client — the shared structured-call client.

No network: a fake transport (any object exposing ``messages.create``) stands in
for ``anthropic.Anthropic``, so these exercise the request cap, local schema
validation, explicit-model / override behavior, and usage accounting directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from common.ai.client import (
    MAX_REQUESTS,
    AiBudgetError,
    AiError,
    AnthropicClient,
    require_ai_client,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    Responder = Callable[[dict[str, object]], "_Response"]

SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"ok": {"type": "boolean"}},
    "required": ["ok"],
}


class _Block:
    def __init__(self, type_: str, input_: object = None) -> None:
        self.type = type_
        self.input = input_


class _Usage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _Response:
    def __init__(self, content: list[_Block], usage: _Usage) -> None:
        self.content = content
        self.usage = usage


class _Messages:
    def __init__(self, responder: Responder) -> None:
        self._responder = responder
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> _Response:
        self.calls.append(kwargs)
        return self._responder(kwargs)


class FakeTransport:
    def __init__(self, responder: Responder) -> None:
        self.messages = _Messages(responder)


def _ok_responder(_: dict[str, object]) -> _Response:
    return _Response([_Block("tool_use", {"ok": True})], _Usage(10, 5))


def _client(
    responder: Responder, *, max_requests: int = MAX_REQUESTS
) -> AnthropicClient:
    return AnthropicClient(
        "test-key", _transport=FakeTransport(responder), max_requests=max_requests
    )


def test_returns_validated_tool_input():
    client = _client(_ok_responder)
    result = client.structured(system="s", user="u", schema=SCHEMA, model="m")
    assert result == {"ok": True}


def test_invalid_output_raises_ai_error():
    def bad(_: dict[str, object]) -> _Response:
        return _Response([_Block("tool_use", {"ok": "not-a-bool"})], _Usage(1, 1))

    client = _client(bad)
    with pytest.raises(AiError, match="schema validation"):
        client.structured(system="s", user="u", schema=SCHEMA, model="m")


def test_no_tool_use_block_raises():
    def no_tool(_: dict[str, object]) -> _Response:
        return _Response([_Block("text")], _Usage(1, 1))

    client = _client(no_tool)
    with pytest.raises(AiError, match="no tool_use"):
        client.structured(system="s", user="u", schema=SCHEMA, model="m")


def test_budget_error_escapes_per_item_ai_error_handlers():
    # A runaway-guard abort must NOT be a per-item AiError, or the tools'
    # `except AiError: continue` handlers would swallow it and keep firing
    # calls on every remaining item instead of stopping the run.
    assert not issubclass(AiBudgetError, AiError)


def test_request_cap_aborts():
    client = _client(_ok_responder, max_requests=2)
    client.structured(system="s", user="u", schema=SCHEMA, model="m")
    client.structured(system="s", user="u", schema=SCHEMA, model="m")
    with pytest.raises(AiBudgetError, match="per-invocation AI-call ceiling"):
        client.structured(system="s", user="u", schema=SCHEMA, model="m")


def test_explicit_model_is_passed_through():
    # Each call's tier reaches the transport verbatim — there is no override that
    # could re-tier it (that footgun was removed; models come only from CHEAP_MODEL
    # / TRUSTED_MODEL at the call sites).
    transport = FakeTransport(_ok_responder)
    client = AnthropicClient("k", _transport=transport)
    client.structured(system="s", user="u", schema=SCHEMA, model="my-model")
    assert transport.messages.calls[0]["model"] == "my-model"


def test_usage_accumulates_across_calls():
    client = _client(_ok_responder)
    client.structured(system="s", user="u", schema=SCHEMA, model="m")
    client.structured(system="s", user="u", schema=SCHEMA, model="m")
    assert client.usage.input_tokens == 20
    assert client.usage.output_tokens == 10
    assert client.usage.total_tokens == 30
    assert client.request_count == 2


def test_require_ai_client_fatal_without_key(monkeypatch):
    from common.ai.client import AiUnavailableError

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(AiUnavailableError):
        require_ai_client()
