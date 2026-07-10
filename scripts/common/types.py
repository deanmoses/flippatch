"""Shared type vocabulary.

Lives in a package submodule (``common.types``), never a top-level
``scripts/types.py``: ``scripts`` is on the module path, so a top-level module
named ``types`` would shadow the standard library's ``types`` for the whole
process. As a submodule it is imported ``from common.types import Json`` and
collides with nothing.
"""

from __future__ import annotations

# The exact shape ``json.dumps`` accepts and ``json.loads`` yields: a
# JSON-serializable value. Recursive by construction — an object's values, and a
# list's items, are themselves ``Json``. Use it on the *output* side, where code
# builds a value it fully controls to serialize (a ``to_json`` return); it states
# the real contract that ``dict[str, object]`` leaves implicit. On the *input*
# side — arbitrary parsed model/API output narrowed with ``isinstance`` readers —
# ``dict[str, object]`` stays the honest type (see ``common.ai.client``).
#
# The PEP 695 ``type`` statement is lazily evaluated, so the self-reference needs
# no quoting.
type Json = str | int | float | bool | None | list[Json] | dict[str, Json]

# A JSON Schema document — the ``dict``-shaped schema handed to a validator (the
# repo uses ``jsonschema.Draft7Validator``). Deliberately ``dict[str, object]``
# rather than ``Json``: a schema is consumed by that library as an opaque mapping,
# not a value this code builds to serialize, so the looser input-side type is the
# honest one (the same reasoning as the ``Json`` note above). Domain-neutral, so
# it lives here beside ``Json`` rather than inside any one tool.
type JsonSchema = dict[str, object]
