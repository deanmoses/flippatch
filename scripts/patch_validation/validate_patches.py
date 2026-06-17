#!/usr/bin/env python3
"""Validate data patches under ``patches/`` for early authoring feedback.

Checks each ``patches/NNNN-slug.yaml`` for:

- a well-formed ``NNNN-slug`` filename and unique numeric prefixes
- strict YAML: duplicate mapping keys are an error
- JSON-shaped values only (no YAML implicit dates/bools beyond JSON)
- structural conformance to ``schema/patch.schema.json``

Authoritative validation (entity resolution, field classification) happens in
flipcommons' ``ingest_patches``; this is a fast structural gate so a typo is
caught before publishing.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PATCHES_DIR = REPO_ROOT / "patches"
SCHEMA_PATH = REPO_ROOT / "schema" / "patch.schema.json"
PATCH_ID_RE = re.compile(r"^\d{4}-[a-z0-9-]+$")


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate keys and YAML implicit coercion.

    Mirrors flipcommons' patch loader so pindata catches the same problems
    *before* publishing. The canonical implementation lives in flipcommons at
    ``backend/apps/catalog/ingestion/patches.py``; this is a hand-maintained
    copy. **Keep the two in sync** — if flipcommons tightens or loosens what it
    accepts, update this loader (and the schema) to match, or the gate goes
    stale. ``tests/test_validate_patches.py`` pins the shared rules (duplicate
    keys, non-string mapping keys, JSON-shaped scalars, rejected non-JSON tags)
    as a drift tripwire.
    """


def _no_duplicate_keys(loader: _StrictLoader, node: yaml.MappingNode) -> dict[str, Any]:
    loader.flatten_mapping(node)
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            # JSON object keys are always strings, so a non-string key is
            # non-JSON-shaped — notably the unquoted `1:` cites handle the patch
            # format forbids (the schema's numeric-handle `propertyNames` pattern
            # silently passes int keys, since JSON Schema `pattern` ignores
            # non-strings). flipcommons' loader rejects these; mirror it here.
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f'mapping key {key!r} is not a string; quote it (e.g. "1":)',
                key_node.start_mark,
            )
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node)
    return mapping


_StrictLoader.add_constructor("tag:yaml.org,2002:map", _no_duplicate_keys)
_StrictLoader.yaml_implicit_resolvers = {}
for _tag, _pattern, _first in [
    ("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), "tf"),
    ("tag:yaml.org,2002:null", re.compile(r"^(?:null|~)$"), "n~"),
    ("tag:yaml.org,2002:int", re.compile(r"^[-+]?[0-9]+$"), "-+0123456789"),
    (
        "tag:yaml.org,2002:float",
        re.compile(r"^[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?$"),
        "-+.0123456789",
    ),
]:
    for _ch in _first:
        # PyYAML's stub marks this classmethod untyped.
        _StrictLoader.add_implicit_resolver(_tag, _pattern, _ch)  # type: ignore[no-untyped-call]


# Reject explicit YAML tags that resolve to non-JSON Python objects. Disabling
# implicit resolvers above only stops *coercion* (`1996-01-01` stays a string);
# an explicit `!!timestamp`/`!!set`/`!!binary` would still be constructed by the
# SafeLoader. flipcommons' apply-time loader rejects these, so reject them here
# too — the gate is only useful if it catches what flipcommons would.
def _reject_tag(loader: _StrictLoader, node: yaml.Node) -> None:
    raise yaml.constructor.ConstructorError(
        None,
        None,
        f"non-JSON YAML tag {node.tag!r} is not allowed in patches",
        node.start_mark,
    )


for _rejected in (
    "tag:yaml.org,2002:timestamp",
    "tag:yaml.org,2002:binary",
    "tag:yaml.org,2002:set",
    "tag:yaml.org,2002:omap",
    "tag:yaml.org,2002:pairs",
):
    _StrictLoader.add_constructor(_rejected, _reject_tag)


def _construct_finite_float(loader: _StrictLoader, node: yaml.ScalarNode) -> float:
    """Construct a float but reject NaN/Infinity (not representable in JSON)."""
    value = yaml.SafeLoader.construct_yaml_float(loader, node)
    if not math.isfinite(value):
        raise yaml.constructor.ConstructorError(
            None,
            None,
            f"non-finite float {value!r} is not valid JSON",
            node.start_mark,
        )
    return value


_StrictLoader.add_constructor("tag:yaml.org,2002:float", _construct_finite_float)


def main() -> int:
    if not PATCHES_DIR.is_dir():
        print("No patches/ directory; nothing to validate.")
        return 0

    validator = Draft7Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    paths = sorted(PATCHES_DIR.glob("*.yaml"))
    errors: list[str] = []
    seen_prefix: dict[str, str] = {}

    for path in paths:
        if not PATCH_ID_RE.match(path.stem):
            errors.append(f"{path.name}: filename must be NNNN-slug.yaml")
            continue
        prefix = path.stem.split("-", 1)[0]
        if prefix in seen_prefix:
            errors.append(
                f"{path.name}: duplicate patch number {prefix} "
                f"(also {seen_prefix[prefix]})"
            )
        seen_prefix[prefix] = path.name

        try:
            # _StrictLoader is a SafeLoader subclass (no arbitrary object
            # construction); it only tightens YAML 1.1 coercion and duplicate keys.
            data = yaml.load(path.read_text(encoding="utf-8"), Loader=_StrictLoader)  # noqa: S506
        except yaml.YAMLError as exc:
            errors.append(f"{path.name}: invalid YAML: {exc}")
            continue

        for err in sorted(
            validator.iter_errors(data), key=lambda e: [str(p) for p in e.path]
        ):
            loc = "/".join(str(p) for p in err.path) or "<root>"
            errors.append(f"{path.name}: {loc}: {err.message}")

    if errors:
        print(f"{len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print(f"All {len(paths)} patch(es) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
