"""The public type vocabulary of the AI client.

Everything here describes the *shape* of the client's public interface — the
:data:`AiModelName` tier vocabulary a caller must speak, the
:data:`AiModelResult` alias, the cumulative :class:`Usage` counter, the
request-count backstop, the :class:`AiClient` protocol the tools depend on, and
the three error types. The generic :data:`~common.types.JsonSchema` a call
constrains its output with is domain-neutral and lives in :mod:`common.types`.
The implementation (:mod:`common.ai.client._client`) lives separately; both are
re-exported from the package, so callers write ``from common.ai.client
import structured, TRUSTED_MODEL, AiError``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from common.types import JsonSchema

# The JSON Schema-validated structured result returned by an AI model.
type AiModelResult = dict[str, object]

# A model-tier identifier accepted by ``AiClient.structured(model=...)``. The
# type and its only two legal values live together so the tiering vocabulary has
# one home (see AiCommon.md §5): cheap where something trusted disposes
# downstream, trusted otherwise (e.g. the polarity-sensitive
# quote-supports-claim judgment). There is **no default** — every call site
# names its tier explicitly, so nothing can silently inherit the cheap one.
type AiModelName = str
CHEAP_MODEL: AiModelName = "claude-haiku-4-5"
TRUSTED_MODEL: AiModelName = "claude-sonnet-5"

# Hard per-invocation ceiling on AI calls. A manually-run tool's call count is
# knowable up front, so a tool sizes its scoped work and refuses (telling the
# caller to run over fewer patches) rather than exceeding this — it is a real
# spend/time cap, not just a runaway-loop backstop. Set just above the largest
# single patch's needs (~212 description-lint calls) so any one patch runs whole
# while a too-broad multi-patch run is stopped before it spends.
MAX_REQUESTS = 250


@dataclass(frozen=True, slots=True)
class Usage:
    """Cumulative token counts for a run. Summed, never priced (see AiCommon.md).

    Lives with the client because that is its sole producer and consumer: the
    ``structured`` calls accrue into it and the CLIs read the running total off
    :attr:`AnthropicClient.usage`.
    """

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
        )


class AiUnavailableError(RuntimeError):
    """Raised at startup when no API key is configured — a fatal condition."""


class AiError(RuntimeError):
    """Raised when one model call fails or returns no valid structured result.

    Recoverable *per item*: a caller may catch it, note the skipped item, and
    carry on with the rest of the run.
    """


class AiBudgetError(RuntimeError):
    """Raised when a run exceeds its request-count cap — a fatal runaway guard.

    Deliberately **not** an :class:`AiError`: it must abort the whole run, so
    the per-item ``except AiError`` handlers never swallow it.
    """


class AiClient(Protocol):
    """The one call the tools need: a schema-constrained structured completion."""

    def structured(
        self,
        *,
        system: str,
        user: str,
        schema: JsonSchema,
        model: AiModelName,
        max_tokens: int = 512,
    ) -> AiModelResult: ...
