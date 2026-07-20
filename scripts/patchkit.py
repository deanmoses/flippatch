"""Shared helpers for authoring Flipcommons data patches.

``read_view`` reads a campaign's analysis file (flipcommons'
``scripts/analysis/README.md``); ``entry`` / ``write_patch`` and the text helpers
emit the patch YAML from those rows (DataPatches.md). Centralized because every
session that re-derives the escaping and guards gets them subtly wrong.

No Django import, so it runs outside the backend and is unit-testable.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import textwrap
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from common.paths import (
    CAMPAIGNS_DIR,
    FLIPCOMMONS_DIR,
    PATCHES_DIR,
    REPO_ROOT,
    load_env,
)

# Re-exported so a generator never counts parent directories to find them.
__all__ = ["CAMPAIGNS_DIR", "PATCHES_DIR", "REPO_ROOT"]

# --------------------------------------------------------------------------- #
# text / escaping                                                             #
# --------------------------------------------------------------------------- #

_SMART = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "…": "...",
}


def clean_text(s: str) -> str:
    """Normalize copy-paste typography; strip only mojibake. Preserves real non-ASCII.

    IPDB/OPDB free text is full of curly quotes, en/em dashes and the U+FFFD
    replacement character. This straightens that typography and drops U+FFFD, but
    keeps legitimate non-ASCII letters (umlauts, accents) verbatim - notes are stored
    as UTF-8 and quotes must stay faithful to the source (DataPatches.md).
    """
    for k, v in _SMART.items():
        s = s.replace(k, v)
    return s.replace("�", "")


# The only normalizations sanctioned for a verbatim quote: smart quotes
# straightened, "…" spelled out as the "[...]" omission marker. The source's
# own dashes (– —) stay — the verifier requires the exact text.
_QUOTE_SMART = {"‘": "'", "’": "'", "“": '"', "”": '"', "…": "[...]"}


def clean_quote(s: str) -> str:
    """Normalize a verbatim quote: straighten smart quotes, spell out an
    ellipsis, drop mojibake — and nothing else (dashes stay verbatim)."""
    for k, v in _QUOTE_SMART.items():
        s = s.replace(k, v)
    return s.replace("�", "")


def yamlq(s: str) -> str:
    """Render `s` as a quoted YAML scalar, choosing the quote style Prettier does.

    Prettier's default is a double-quoted scalar, but a double-quoted YAML scalar
    escapes `"` and `\\` with backslashes, so any text containing either switches
    to single quotes instead - literal except `'`, which is doubled. That is what
    keeps `... says "<verbatim>"` notes single-quoted and everything else double.
    Emitting the same choice here is what makes a generated patch already
    Prettier-formatted (see the flow-emission section). Always pass clean_text()ed
    text.
    """
    if '"' in s or "\\" in s:
        return "'" + s.replace("'", "''") + "'"
    return '"' + s + '"'


def source_note(source: str, verbatim: str, tail: str = "") -> str:
    """The canonical evidence note: `<Source> says "<verbatim>"<tail>`.

    Quote the source verbatim; mark your own omissions inside `verbatim` with
    ` [...] `. Normalizes typography but preserves the source's own letters
    (umlauts, accents). Feed the return value straight to entry(note=...).
    """
    return clean_text(f'{source} says "{verbatim.strip()}"{tail}')


_SAFE_SCALAR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _./()&'-]*$")
# A string value that would be read back as a JSON number/bool/null and so must be
# quoted to stay a string (e.g. a slug "404", or the literal "null").
_JSON_LITERAL = re.compile(r"^(true|false|null|-?\d+(\.\d+)?([eE][+-]?\d+)?)$")


def _scalar(v: object) -> str:
    """JSON-shaped scalar for a claim value (YAML coercion is off in the loader)."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if _SAFE_SCALAR.match(s) and not _JSON_LITERAL.match(s):
        return s
    return yamlq(s)


def _fold(text: str, width: int = 92) -> list[str]:
    """Collapse whitespace and word-wrap, for `>` folded block bodies."""
    return textwrap.wrap(
        " ".join(text.split()),
        width=width,
        break_on_hyphens=False,
        break_long_words=False,
    ) or [""]


# --------------------------------------------------------------------------- #
# source free-text hygiene                                                    #
# --------------------------------------------------------------------------- #
#
# For quoting IPDB's free-text fields, whose typography and framing need
# normalizing before a span is fit to cite. The catalog carries that text as
# plain columns on the foundation's `models` view (`ipdb_notes`,
# `ipdb_notable_features`), so an analysis file cuts the span and these tidy it.

_IPD_HEADER = re.compile(r"^\s*\d+\s*/[^.]*?\bPlayers?\b\s*")


def sentences(text: str) -> list[str]:
    """Split free text into sentences, normalizing CR/LF and runs of whitespace."""
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]


def sentence_with(blob: str, needle: str) -> str:
    """The first sentence in `blob` containing `needle` (case-insensitive), or ''.

    The needle pattern that pins a quote: freeze a unique substring of the evidence
    sentence in your classify map, re-extract the live sentence here so the quote
    stays faithful to the current source text. Assert the result still contains the
    keyword you classified on (see DataPatchAuthoring.md's faithfulness-guard gotcha).
    """
    for s in sentences(blob):
        if needle.lower() in s.lower():
            return s
    return ""


_QUOTE_INTRO = re.compile(r'^.*?:\s*"(.+?)"?$')


def clean_ipdb_quote(text: str, limit: int = 240) -> str:
    """Normalize an IPDB sentence's typography, strip its framing and bound its length.

    IPDB glues a punctuation-less header ('6022 / 1946 / 1 Player') onto the first
    sentence, so the splitter keeps it; this drops it. It also frames quoted passages
    with an introducer ('... translates as follows: "<text>'); this keeps the inner
    passage and drops the framing, so we quote the evidence itself rather than a
    dangling open-quote that reads as complete. Over-long run-ons are cut at a word
    boundary with a marked ` [...]` omission (DataPatches.md requires marking
    omissions). Idempotent on already-clean text.
    """
    text = _IPD_HEADER.sub("", clean_text(text)).strip()
    intro = _QUOTE_INTRO.match(text)
    if intro:
        text = intro.group(1).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + " [...]"
    return text


# --------------------------------------------------------------------------- #
# reading a campaign's analysis file                                          #
# --------------------------------------------------------------------------- #
#
# A campaign's detection, gating and quote extraction live in its `<name>.sql`
# plan, layered on flipcommons' shared analysis foundation; `gen.py` is a pure
# emitter over one of that plan's views. `read_view` is the bridge — the single
# supported way to get those rows into Python.


# A bare SQL identifier — what a view name and a checks prefix are allowed to be.
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _flipcommons_dir() -> Path:
    """The flipcommons checkout — ``FLIPCOMMONS_DIR``, this repo's ``.env``, or the
    sibling default.

    ``load_env()`` runs before the environment is read, because ``FLIPCOMMONS_DIR``
    is resolved at that module's import time and an override living only in
    ``.env`` would otherwise be missed.
    """
    load_env()
    return Path(os.environ.get("FLIPCOMMONS_DIR") or FLIPCOMMONS_DIR)


def read_view(
    analysis: str | Path, view: str, *, prefix: str, check: bool = True
) -> list[dict[str, object]]:
    """Rows of one view from a campaign analysis file, via flipcommons' runner.

    Runs ``analysis query … --check <prefix>``, so the analysis's checks gate the
    read. That is the reason to come through here: a patch built on a detector
    that has gone dark is still well-formed YAML, and nothing downstream can tell.

    ``prefix`` is explicit rather than inferred from the filename because the two
    routinely differ — ``exports.sql`` gates on ``export_checks``, ``features.sql``
    on ``gpf_checks``. Pass ``check=False`` only while an analysis's checks are
    still unwritten.

    Returns ``[]`` for an empty view: a campaign whose patch is already applied
    legitimately reads back nothing, and calling that fatal is the generator's job.
    """
    # Both land inside SQL the runner interpolates, so hold them to bare
    # identifiers: a typo becomes one clear error rather than a DuckDB parse
    # failure, and the argv below is provably free of untrusted input.
    for label, value in (("view", view), ("prefix", prefix)):
        if not _IDENTIFIER.match(value):
            raise ValueError(f"{label} must be a bare SQL identifier, got {value!r}")
    analysis_path = Path(analysis)
    if not analysis_path.is_file():
        raise FileNotFoundError(f"no such analysis file: {analysis_path}")

    runner = _flipcommons_dir() / "scripts" / "analysis" / "analysis"
    cmd = [
        str(runner),
        "query",
        str(analysis_path),
        f"FROM {view};",
        "--format",
        "json",
    ]
    if check:
        cmd += ["--check", prefix]
    # FLIPPATCH_DIR locates this repo for a plan reading a checked-in authoring
    # artifact (a TSV extract, a reference list). Set here rather than left to the
    # caller's shell: the analysis's own fallback is the sibling layout, so an unset
    # var doesn't fail — it silently reads a DIFFERENT checkout's artifact.
    env = {**os.environ, "FLIPPATCH_DIR": str(REPO_ROOT)}
    # The runner finds its own root and cd's there, so the caller has no cwd
    # contract to get right. Diagnostics go to stderr; stdout is pure JSON.
    # S603: every argument is a literal, a path we derived, or an identifier
    # validated above. No shell.
    proc = subprocess.run(  # noqa: S603
        cmd, capture_output=True, text=True, check=True, env=env
    )
    rows: list[dict[str, object]] = json.loads(proc.stdout)
    return rows


# --------------------------------------------------------------------------- #
# resolution                                                                  #
# --------------------------------------------------------------------------- #

# An entity reference the patch targets (a slug / public-id / 'type:id' form).
type Ref = str
# A catalog field/column name, including resolved-row aliases ('corporate_entity__slug').
type FieldName = str
# A catalog field value: year int, slug str, ipdb_id int.
type FieldValue = object


def check_resolved(requested: Iterable[Ref], found: Iterable[Ref]) -> None:
    """Raise if any requested ref didn't resolve in the live DB (typo or drift)."""
    have = set(found)
    missing = [r for r in requested if r not in have]
    if missing:
        raise SystemExit(f"UNRESOLVED refs ({len(missing)}): {missing}")


# --------------------------------------------------------------------------- #
# inline citations (cites: map + marker correspondence)                       #
# --------------------------------------------------------------------------- #
#
# A description (or string field) may carry inline citation markers
# `[[cite:<handle>]]`. A handle splits by strict lexical grammar - the same split
# the backend uses (see flipcommons DataPatches.md / the patch adapter's process
# step, "classify handles"):
#   - all-digits  (^[0-9]+$)  -> a NEW citation, minted this patch; MUST have a
#                                matching `cites:` entry to mint from.
#   - all-lowercase-letters (^[a-z]+$) -> an EXISTING CitationInstance.slug (the
#                                re-edit / rehydration case); carries no `cites:`
#                                entry. patchkit can't confirm it RESOLVES - the
#                                backend does that at apply time - but the shape is
#                                valid here.
#   - anything else -> a structural error (e.g. a raw-pk `[[cite:id:1]]`, `1a`,
#                                uppercase, punctuation): rejected at author time.
# The numeric/slug split is lexical, so within-entry correspondence needs no DB.
# These rules INTENTIONALLY duplicate the backend's per-entry checks (patchkit
# fails fast; the backend stays authoritative) - keep the two in sync if either
# changes. The cross-entry "one entry per entity" guard is backend-only: entry()
# builds one entry at a time and structurally can't see siblings.

_CITE_MARKER = re.compile(r"\[\[cite:([^\]]+)\]\]")
_NUMERIC_HANDLE = re.compile(r"^[0-9]+$")
_SLUG_HANDLE = re.compile(r"^[a-z]+$")

# A cite handle: the numeric label ('1', '2') wiring a [[cite:N]] marker to its spec.
type Handle = str
# One cite spec: a 'scheme:id' / URL string, or a `{ref, archive, locator, quote}`
# mapping — `ref` required; `locator`/`quote` land on the minted footnote instance,
# exactly like the entry-level `cite:` mapping.
type CiteSpec = str | Mapping[str, str]

# The mapping-form keys the backend's cite grammar accepts (mirrors
# _CITE_MAPPING_KEYS in flipcommons' patches/parsing.py — keep in sync).
_CITE_SPEC_KEYS = frozenset({"ref", "archive", "locator", "quote"})


def _cite_spec_node(spec: Mapping[str, str]) -> _Map:
    """A short cite-spec mapping as a flow node (the printer decides its shape)."""
    return _Map([(k, _scalar(v)) for k, v in spec.items()])


def _cite_spec_flow(spec: Mapping[str, str]) -> str:
    """Render a short cite-spec mapping as a one-line flow map."""
    return _inline(_cite_spec_node(spec))


def _check_cites(
    ref: Ref, texts: Sequence[str], cites: Mapping[Handle, CiteSpec] | None
) -> None:
    """Enforce within-entry marker<->cites correspondence (mirrors backend per-entry rules)."""
    cite_keys = {str(k) for k in (cites or {})}
    for key in cite_keys:
        if not _NUMERIC_HANDLE.match(key):
            raise ValueError(
                f"{ref}: cites key {key!r} must be a numeric handle "
                f"(an existing slug marker needs no cites: entry)"
            )
    for key, spec in (cites or {}).items():
        if isinstance(spec, Mapping):
            unknown = set(spec) - _CITE_SPEC_KEYS
            if unknown:
                raise ValueError(
                    f"{ref}: cites[{key!r}] has unknown key(s) {sorted(unknown)}; "
                    f"allowed keys are {', '.join(sorted(_CITE_SPEC_KEYS))}"
                )
            if not spec.get("ref"):
                raise ValueError(
                    f"{ref}: cites[{key!r}] mapping needs a non-empty 'ref'"
                )
    numeric_markers: set[str] = set()
    for text in texts:
        for handle in _CITE_MARKER.findall(text):
            if _NUMERIC_HANDLE.match(handle):
                numeric_markers.add(handle)
            elif _SLUG_HANDLE.match(handle):
                continue  # existing slug; resolution is the backend's job
            else:
                raise ValueError(
                    f"{ref}: malformed cite handle [[cite:{handle}]] "
                    f"(use a numeric handle for a new cite or a slug for an existing one)"
                )
    missing = numeric_markers - cite_keys
    if missing:
        raise ValueError(
            f"{ref}: cite handles {sorted(missing, key=int)} are referenced by a "
            f"marker but have no cites: entry to mint from"
        )
    unused = cite_keys - numeric_markers
    if unused:
        raise ValueError(
            f"{ref}: cites: entries {sorted(unused, key=int)} are not referenced by any marker"
        )


# --------------------------------------------------------------------------- #
# Prettier-compatible flow emission                                           #
# --------------------------------------------------------------------------- #
#
# patches/*.yaml is reformatted by Prettier at commit time (.pre-commit-config)
# and by the IDE on save, so anything emitted in a different-but-equivalent style
# comes straight back as diff noise on every generated patch. These helpers
# reproduce Prettier 3.x's YAML defaults for FLOW collections - printWidth 80,
# bracketSpacing on - so a generated file is already formatted. (Quote style is
# yamlq's job; folded `>` block bodies Prettier never reflows, so _fold's width is
# free to stay wider.)
#
# A flow value is modelled as a tree of already-escaped scalars so the printer can
# measure it before deciding how to break it.


@dataclass(frozen=True)
class _Seq:
    """A flow sequence: `[a, b]`."""

    items: Sequence[_Node]


@dataclass(frozen=True)
class _Map:
    """A flow mapping: `{ k: v }` (`{}` when empty)."""

    pairs: Sequence[tuple[str, _Node]]


type _Node = str | _Seq | _Map

_PRINT_WIDTH = 80


def _inline(node: _Node) -> str:
    """The one-line rendering of `node`, however long it comes out."""
    if isinstance(node, str):
        return node
    if isinstance(node, _Seq):
        return "[" + ", ".join(_inline(i) for i in node.items) + "]"
    if not node.pairs:
        return "{}"
    return "{ " + ", ".join(f"{k}: {_inline(v)}" for k, v in node.pairs) + " }"


def _explode(node: _Seq | _Map, bracket: str) -> list[str]:
    """Break `node` open: one member per line, trailing comma on every member.

    Prettier never *fills* a flow collection - once it breaks, every member gets
    its own line. `bracket` is the indent the brackets sit at; members go one
    level (two spaces) deeper.
    """
    open_ch, close_ch = ("[", "]") if isinstance(node, _Seq) else ("{", "}")
    inner = bracket + "  "
    members = (
        [_value_lines(inner, item) for item in node.items]
        if isinstance(node, _Seq)
        else [_value_lines(inner, v, key=k) for k, v in node.pairs]
    )
    lines = [f"{bracket}{open_ch}"]
    for member in members:
        member[-1] += ","
        lines.extend(member)
    lines.append(f"{bracket}{close_ch}")
    return lines


def _value_lines(indent: str, node: _Node, key: str | None = None) -> list[str]:
    """Lines for `node` at `indent`, as `key: <value>` when `key` is given.

    The Prettier cascade: keep it on one line if it fits; else (for a keyed value)
    drop it to its own line, indented one level, still inline; else explode it.
    A scalar is unbreakable, so it stays on its line at any length.
    """
    prefix = f"{indent}{key}: " if key is not None else indent
    inline = _inline(node)
    if isinstance(node, str) or len(prefix) + len(inline) <= _PRINT_WIDTH:
        return [prefix + inline]
    if key is None:
        return _explode(node, indent)
    if len(indent) + 2 + len(inline) <= _PRINT_WIDTH:
        return [f"{indent}{key}:", f"{indent}  {inline}"]
    return [f"{indent}{key}:", *_explode(node, indent + "  ")]


def _item_lines(indent: str, node: _Node) -> list[str]:
    """Lines for `node` as a block-sequence item: `- [a, b]`.

    A block-sequence item can't move its value to the next line the way a mapping
    value can, so an over-long collection breaks with the bracket still hugging
    the dash.
    """
    dash = f"{indent}- "
    inline = _inline(node)
    if isinstance(node, str) or len(dash) + len(inline) <= _PRINT_WIDTH:
        return [dash + inline]
    lines = _explode(node, " " * len(dash))
    lines[0] = dash + lines[0].lstrip()
    return lines


# --------------------------------------------------------------------------- #
# YAML entry / patch emission                                                 #
# --------------------------------------------------------------------------- #


def _cite_spec_fields(spec: Mapping[str, str]) -> list[tuple[str, str]]:
    """Schema-ordered (key, escaped-value) pairs of one {ref, quote, ...} spec
    (quote typography normalized via clean_text)."""
    return [
        (k, _scalar(clean_quote(spec[k]) if k == "quote" else spec[k]))
        for k in ("ref", "archive", "locator", "quote")
        if k in spec
    ]


def _cite_lines(
    cite: str | Mapping[str, str] | Sequence[str | Mapping[str, str]], indent: str
) -> list[str]:
    """Emit `cite:` — inline for a bare ref, a block map for a {ref, quote, ...}
    spec, a block list when several sources back the same claims (each element
    again a bare ref or a spec map). Everything escaped."""
    if isinstance(cite, str):
        return [f"{indent}cite: {cite}"]
    if isinstance(cite, Mapping):
        lines = [f"{indent}cite:"]
        lines.extend(f"{indent}  {k}: {v}" for k, v in _cite_spec_fields(cite))
        return lines
    lines = [f"{indent}cite:"]
    for spec in cite:
        if isinstance(spec, Mapping):
            pairs = _cite_spec_fields(spec)
            lines.append(f"{indent}  - {pairs[0][0]}: {pairs[0][1]}")
            lines.extend(f"{indent}    {k}: {v}" for k, v in pairs[1:])
        else:
            lines.append(f"{indent}  - {_scalar(spec)}")
    return lines


def _rel_member(ref: Ref, namespace: str, member: object) -> _Node:
    """One member of a relationship list: a bare public_id, or a COUNTED member.

    ``gameplay_feature`` is the one namespace whose members can carry a count --
    "4 ramps", "6 bingo cards" (DataPatches.md -> Counted members). The count is
    authored as a one-key ``{public_id: count}`` mapping in place of the bare
    slug, and the two forms mix freely in one list. The count is validated here
    rather than at apply time: it must be a positive integer, since `0` and
    non-ints are rejected by the backend.
    """
    if not isinstance(member, Mapping):
        return _scalar(member)
    items = list(member.items())
    if len(items) != 1:
        raise ValueError(
            f"{ref}: a counted {namespace} member needs exactly one key, got {member!r}"
        )
    public_id, count = items[0]
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError(
            f"{ref}: {namespace} count for {public_id!r} must be a positive integer, "
            f"got {count!r}"
        )
    return _Map([(_scalar(public_id), str(count))])


def _credit_lines(credits: Sequence[tuple[str, str]], indent: str) -> list[str]:
    """Emit `credit:` as a block list of single-key `person: role` mappings —
    the catalog's one multi-key relationship (DataPatches.md → Credits). Flow
    style would quote the colon and turn each member into a string, so credits
    always emit block form."""
    lines = [f"{indent}credit:"]
    for person, role in credits:
        lines.append(f"{indent}  - {_scalar(person)}: {_scalar(role)}")
    return lines


_MARKET_TARGETS = ("target_market_location", "target_market_label")


def _check_export_market(ref: Ref, rows: Sequence[Mapping[str, str | None]]) -> None:
    """Enforce the export-market rules ingest can't or won't (DataPatches.md).

    Two of the three are hard apply-time errors worth catching before a snapshot
    restore; the third — "a null-location row must be the model's only row" — is
    NOT validated by ingest at all and applies silently as an illegal mix, so this
    is the only gate it has.
    """
    for row in rows:
        present = [k for k in _MARKET_TARGETS if k in row]
        if len(present) > 1:
            raise ValueError(
                f"{ref}: export_market member has both target keys "
                f"({', '.join(present)}); at most one is allowed"
            )
        for k in present:
            if row[k] is None or str(row[k]).strip() == "":
                raise ValueError(
                    f"{ref}: export_market member has an empty {k}; "
                    f"omit the key instead to mean 'unknown destination'"
                )
    # The cross-row shape rule: a targetless row can only stand alone.
    if len(rows) > 1 and any(
        not [k for k in _MARKET_TARGETS if k in row] for row in rows
    ):
        raise ValueError(
            f"{ref}: an export_market row with no target must be the model's only row; "
            f"got {len(rows)} rows mixing shapes"
        )
    labels = [row for row in rows if "target_market_label" in row]
    if len(rows) > 1 and labels:
        raise ValueError(
            f"{ref}: a target_market_label row must be the model's only row; "
            f"got {len(rows)} rows mixing shapes"
        )


def entry(
    ref: Ref,
    *,
    create: bool = False,
    note: str | None = None,
    cite: str | Mapping[str, str] | Sequence[str | Mapping[str, str]] | None = None,
    fields: Mapping[FieldName, FieldValue] | None = None,
    description: str | None = None,
    cites: Mapping[Handle, CiteSpec] | None = None,
    changesets: Sequence[Mapping[str, object]] | None = None,
    tags: Sequence[str] | None = None,
    credits: Sequence[tuple[str, str]] | None = None,
    relationships: Mapping[str, Sequence[str | Mapping[str, int]]] | None = None,
    model_relationship: Sequence[Mapping[str, str]] | None = None,
    export_market: Sequence[Mapping[str, str | None]] | None = None,
    remove: Mapping[str, Sequence[str]] | None = None,
    retract: Sequence[str] | None = None,
    comment: str | None = None,
    commented: bool = False,
) -> str:
    """Emit one YAML `claims:` entry block, correctly indented and escaped.

    ref:    '<entity_type>.<public_id>'  e.g. 'model.mazatron', 'game-format.slot-machine'.
    create: emit `create: true` (new entity).
    note:   free text -> single-quoted scalar (use source_note() to build it).
    cite:   'scheme:id' e.g. 'ipdb:4443'.
    fields: scalar/FK claims; value used as-is for scalars, target public_id for FKs.
    description: folded `>` block (for vocab creation).
    cites:  inline-citation map for new cites referenced from `description`/`fields`
        markers: `{ handle: spec }` where handle is a numeric string ('1', '2' -
        no ordering) and spec is a 'scheme:id', a URL string, or a
        `{ref, archive, locator, quote}` mapping (`ref` required; `locator`/`quote`
        land on the minted footnote instance, exactly like the entry-level `cite:`).
        A quote-bearing spec is emitted as a block map so the prose stays readable.
        Each numeric `[[cite:<handle>]]` marker must have an entry here; each entry
        must be referenced by a marker. Existing-slug markers (`[[cite:<slug>]]`,
        from rehydration) need no entry. Emitted with the handle key quoted (the
        backend loader rejects bare integer YAML keys).
    tags / retract: lists -> `tag: [...]` / `retract: [...]`.
    relationships: namespace -> members, the general relationship emitter
        (`tags=` is the `tag` shorthand). Members are bare strings — FK
        public_ids (`theme: [medieval]`) or string members for aliases /
        abbreviations (`manufacturer_alias: [Stern Pinball, Stern Inc]`). Each
        member is escaped, so free-text alias strings with commas/colons are safe.
    export_market: ModelExportMarket rows — a block list of explicit-key mappings,
        each with AT MOST ONE of `target_market_location` (a country public_id) or
        `target_market_label` (a multi-country region). `{}` is the legal
        unknown-destination row. Guards what ingest does not: at most one target key
        per member, no explicit nulls, and the "a null-location row must be the
        model's only row" convention (DataPatches.md calls that author discipline —
        the illegal mix applies SILENTLY, so this is the only place it is caught).
        `export_edition_of` is a plain scalar FK; pass it in `fields`.
    remove: namespace -> members to drop, emits `remove: { ns: [...] }` (the
        relationship counterpart of `retract`).
    commented: prefix every line with '# ' (FLAGGED rows kept in-file for a human call).
    comment: trailing `# ...` on the ref line.
    """
    if create and retract:
        raise ValueError(
            f"{ref}: create + retract are invalid (nothing to retract on a new entity)"
        )
    cite_texts = [description] if description is not None else []
    cite_texts += [v for v in (fields or {}).values() if isinstance(v, str)]
    _check_cites(ref, cite_texts, cites)
    pre = "  # " if commented else "  "
    sub = "  #     " if commented else "      "
    head = f"{pre}- {ref}:"
    if comment:
        head += f"  # {comment}"
    lines = [head]
    if create:
        lines.append(f"{sub}create: true")
    if note is not None:
        lines.append(f"{sub}note: {yamlq(clean_text(note))}")
    if cite:
        lines.extend(_cite_lines(cite, sub))
    for k, v in (fields or {}).items():
        lines.append(f"{sub}{k}: {_scalar(v)}")
    if description is not None:
        lines.append(f"{sub}description: >")
        lines.extend(f"{sub}  {line}" for line in _fold(clean_text(description)))
    if cites:
        lines.append(f"{sub}cites:")
        for handle, spec in cites.items():
            key = yamlq(str(handle))
            if isinstance(spec, Mapping) and "quote" in spec:
                # A quote is prose — a one-line flow map would be unreadable, so
                # emit a block map with each field escaped.
                lines.append(f"{sub}  {key}:")
                lines.extend(f"{sub}    {k}: {_scalar(v)}" for k, v in spec.items())
            elif isinstance(spec, Mapping):
                lines.extend(_value_lines(f"{sub}  ", _cite_spec_node(spec), key=key))
            else:
                lines.append(f"{sub}  {key}: {_scalar(spec)}")
    if tags:
        lines.extend(_value_lines(sub, _Seq(list(tags)), key="tag"))
    if credits:
        lines.extend(_credit_lines(credits, sub))
    for namespace, members in (relationships or {}).items():
        rel_node = _Seq([_rel_member(ref, namespace, m) for m in members])
        lines.extend(_value_lines(sub, rel_node, key=namespace))
    if model_relationship:
        # A typed lineage edge (DataPatches.md -> Model relationships) is a list of
        # MAPPINGS -- relationship_type, license_status, and a target_machine slug
        # XOR a free-text target_label -- so it needs a BLOCK list. `fields` emits
        # scalars and `relationships` a flow list of strings; neither can carry a
        # per-edge payload. Values go through _scalar, so an apostrophe in a
        # target_label ("an unidentified O'Brien game") can't break the YAML.
        lines.append(f"{sub}model_relationship:")
        for edge in model_relationship:
            items = list(edge.items())
            if not items:
                raise ValueError(f"{ref}: empty model_relationship edge")
            k, v = items[0]
            lines.append(f"{sub}  - {k}: {_scalar(v)}")
            lines.extend(f"{sub}    {k}: {_scalar(v)}" for k, v in items[1:])
    if export_market:
        _check_export_market(ref, export_market)
        # Like model_relationship, a list of MAPPINGS -- but with an OPTIONAL target,
        # so the empty mapping is a legal member and must survive as `- {}` rather
        # than collapsing to a null list item.
        lines.append(f"{sub}export_market:")
        for row in export_market:
            market_items = list(row.items())
            if not market_items:
                lines.extend(_item_lines(f"{sub}  ", _Map([])))
                continue
            mk, mv = market_items[0]
            lines.append(f"{sub}  - {mk}: {_scalar(mv)}")
            lines.extend(f"{sub}    {mk}: {_scalar(mv)}" for mk, mv in market_items[1:])
    if changesets:
        lines.append(f"{sub}changesets:")
        for cs in changesets:
            item: list[str] = []
            cs_note = cs.get("note")
            if cs_note is not None:
                item.append(f"note: {yamlq(clean_text(str(cs_note)))}")
            cs_cite = cs.get("cite")
            if isinstance(cs_cite, (str, Mapping, Sequence)) and cs_cite:
                item.extend(ln[len(sub) :] for ln in _cite_lines(cs_cite, sub))
            cs_fields = cs.get("fields")
            if isinstance(cs_fields, Mapping):
                item.extend(f"{k}: {_scalar(v)}" for k, v in cs_fields.items())
            cs_rels = cs.get("relationships")
            if isinstance(cs_rels, Mapping):
                # Rendered at the final indent (a changeset member sits four
                # columns in from `sub`) so the width decisions are measured
                # against where the lines actually land, then dedented back.
                cs_indent = f"{sub}    "
                for namespace, members in cs_rels.items():
                    cs_node = _Seq([_scalar(m) for m in members])
                    item.extend(
                        ln[len(cs_indent) :]
                        for ln in _value_lines(cs_indent, cs_node, key=namespace)
                    )
            cs_credits = cs.get("credits")
            if isinstance(cs_credits, Sequence):
                item.extend(ln[len(sub) :] for ln in _credit_lines(cs_credits, sub))
            if not item:
                raise ValueError(f"{ref}: empty changesets item")
            lines.append(f"{sub}  - {item[0]}")
            lines.extend(f"{sub}    {ln}" for ln in item[1:])
    if remove:
        remove_node = _Map(
            [
                (ns, _Seq([_scalar(m) for m in members]))
                for ns, members in remove.items()
            ]
        )
        lines.extend(_value_lines(sub, remove_node, key="remove"))
    if retract:
        lines.extend(_value_lines(sub, _Seq(list(retract)), key="retract"))
    return "\n".join(lines)


def source_root(
    name: str,
    *,
    source_type: str = "web",
    description: str | None = None,
    links: Sequence[tuple[str, str, str]],
) -> str:
    """Emit one `sources:` block entry: a citation-source root (header + links).

    Seeds the website/book/magazine root a later `cite:` URL nests under (a web
    `cite:` errors unless its domain matches a seeded homepage link — DataPatches.md).
    Same escaping safety as entry(): name/label/url go through _scalar so a stray
    apostrophe or colon in a description or label can't break the YAML.

    name:        source name; identity is (name, source_type), so keep it stable.
    source_type: 'web' | 'book' | 'magazine'.
    description: optional folded `>` blurb.
    links:       (url, label, link_type) tuples; link_type is 'homepage' for the
                 root's domain link (what later cites domain-match against),
                 else 'reference' / 'archive'.
    """
    out = [f"  - name: {_scalar(name)}", f"    source_type: {source_type}"]
    if description:
        out.append("    description: >")
        out += [f"      {line}" for line in _fold(clean_text(description))]
    out.append("    links:")
    for url, label, link_type in links:
        link = _Map(
            [
                ("url", _scalar(url)),
                ("label", _scalar(label)),
                ("link_type", link_type),
            ]
        )
        out.extend(_item_lines("      ", link))
    return "\n".join(out)


def render_patch(
    *,
    attribution: str,
    description: str,
    entries: Sequence[str],
    sources: Sequence[str] = (),
) -> str:
    """The complete patch file as text (header + folded description + sources + claims).

    Split out of write_patch so a generator can regenerate an ALREADY-APPLIED patch
    and byte-compare it without touching the file. An applied patch is immutable
    (the ledger fingerprints it), so a generator whose inputs keep growing needs a
    way to prove it would still emit the same bytes -- see gen.py's `emit`.
    """
    out = [f"attribution: {attribution}", "description: >"]
    out += [f"  {line}" for line in _fold(description)]
    if sources:
        out.append("sources:")
        out += list(sources)
    out.append("claims:")
    out += list(entries)
    return "\n".join(out) + "\n"


def write_patch(
    path: str | Path,
    *,
    attribution: str,
    description: str,
    entries: Sequence[str],
    sources: Sequence[str] = (),
) -> Path:
    """Write a complete patch file (header + folded description + sources + claims).

    `sources` is a sequence of source_root() blocks, emitted before `claims:` so a
    `cite:` URL below can nest under a root created here.
    """
    p = Path(path)
    p.write_text(
        render_patch(
            attribution=attribution,
            description=description,
            entries=entries,
            sources=sources,
        )
    )
    return p


# --------------------------------------------------------------------------- #
# demo                                                                        #
# --------------------------------------------------------------------------- #
#
# `python patchkit.py` prints sample output so an author can eyeball the emitted
# YAML. The authoritative checks live in tests/test_patchkit.py (run `pytest`).

if __name__ == "__main__":
    print(
        entry(
            "model.mazatron",
            note=source_note("IPDB", 'exists only as a "prototype" machine'),
            cite="ipdb:4443",
            fields={"production_status": "unreleased"},
            tags=["prototype"],
        )
    )
    print(
        entry(
            "model.mazatron",
            description="A 1990 solid-state prototype by Mac Pinball.[[cite:1]] "
            "Only two units are known to survive.[[cite:2]]",
            cites={
                "1": "ipdb:4443",
                "2": {
                    "ref": "https://pinside.com/thread",
                    "archive": "https://web.archive.org/x",
                    "quote": "Only two are known to survive.",
                },
            },
            note="Narrative compiled from IPDB and Pinside.",
        )
    )
