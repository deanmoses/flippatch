"""Defensive readers for the untrusted structured dicts the model returns.

``AiClient.structured`` validates against the forced-tool JSON schema, but the
return type is ``dict[str, object]``, so these narrow the pieces each rule reads
without scattering ``isinstance`` checks through the rule logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


def rows(result: dict[str, object], key: str) -> Iterator[dict[str, object]]:
    """Yield each object in ``result[key]`` (skips non-object items)."""
    value = result.get(key)
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                yield {str(k): v for k, v in item.items()}


def as_str(row: dict[str, object], key: str) -> str:
    value = row.get(key)
    return value if isinstance(value, str) else ""


def as_bool(row: dict[str, object], key: str) -> bool:
    return row.get(key) is True


def as_int(row: dict[str, object], key: str) -> int | None:
    value = row.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None
