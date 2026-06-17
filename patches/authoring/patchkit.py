"""patchkit - shared helpers for authoring Flipcommons data patches.

Pure Python (NO Django import) so it imports anywhere and is unit-testable.

Why this exists: prior patch-authoring sessions each re-derived YAML escaping,
the missing-ref assert and the review-doc scaffolding - each slightly
differently, some subtly wrong. This centralizes the parts that kept getting
reinvented so a new session writes classification data, not scaffolding.

See DataPatches.md for the patch file format this emits.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

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


def yamlq(s: str) -> str:
    """Render `s` as a single-quoted YAML scalar (the only note escaping needed).

    A single-quoted YAML scalar is literal except `'`, which is doubled. This
    safely carries both the double quotes in `... says "<verbatim>"` and the
    apostrophes in the verbatim text - no backslashes, unlike json.dumps. Always
    pass clean_text()ed text.
    """
    return "'" + s.replace("'", "''") + "'"


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
# source-text extraction (classify.py side)                                   #
# --------------------------------------------------------------------------- #
#
# These run on the pinexplore side, against DuckDB free text - patchkit is pure
# stdlib, so a classify.py can `import patchkit` too (add the authoring dir to
# sys.path, as gen.py does). They were re-derived in every classify.py; pull the
# next one's from here instead.

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
# One cite spec: a 'scheme:id' / URL string, or a `{url, archive}` map of URLs.
type CiteSpec = str | Mapping[str, str]


def _cite_spec(spec: CiteSpec) -> str:
    """Render one cite spec value: a `{url, archive}` flow map, or a scalar string."""
    if isinstance(spec, Mapping):
        inner = ", ".join(f"{k}: {_scalar(v)}" for k, v in spec.items())
        return f"{{ {inner} }}"
    return _scalar(spec)


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
# YAML entry / patch emission                                                 #
# --------------------------------------------------------------------------- #


def entry(
    ref: Ref,
    *,
    create: bool = False,
    note: str | None = None,
    cite: str | None = None,
    fields: Mapping[FieldName, FieldValue] | None = None,
    description: str | None = None,
    cites: Mapping[Handle, CiteSpec] | None = None,
    tags: Sequence[str] | None = None,
    relationships: Mapping[str, Sequence[str]] | None = None,
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
        no ordering) and spec is a 'scheme:id', a URL string, or `{url, archive}`.
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
        lines.append(f"{sub}cite: {cite}")
    for k, v in (fields or {}).items():
        lines.append(f"{sub}{k}: {_scalar(v)}")
    if description is not None:
        lines.append(f"{sub}description: >")
        lines.extend(f"{sub}  {line}" for line in _fold(clean_text(description)))
    if cites:
        lines.append(f"{sub}cites:")
        for handle, spec in cites.items():
            lines.append(f"{sub}  '{handle}': {_cite_spec(spec)}")
    if tags:
        lines.append(f"{sub}tag: [{', '.join(tags)}]")
    for namespace, members in (relationships or {}).items():
        inner = ", ".join(_scalar(m) for m in members)
        lines.append(f"{sub}{namespace}: [{inner}]")
    if remove:
        inner = ", ".join(
            f"{ns}: [{', '.join(_scalar(m) for m in members)}]"
            for ns, members in remove.items()
        )
        lines.append(f"{sub}remove: {{ {inner} }}")
    if retract:
        lines.append(f"{sub}retract: [{', '.join(retract)}]")
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
        out.append(
            f"      - {{ url: {_scalar(url)}, label: {_scalar(label)}, link_type: {link_type} }}"
        )
    return "\n".join(out)


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
    out = [f"attribution: {attribution}", "description: >"]
    out += [f"  {line}" for line in _fold(description)]
    if sources:
        out.append("sources:")
        out += list(sources)
    out.append("claims:")
    out += list(entries)
    p = Path(path)
    p.write_text("\n".join(out) + "\n")
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
                    "url": "https://pinside.com/thread",
                    "archive": "https://web.archive.org/x",
                },
            },
            note="Narrative compiled from IPDB and Pinside.",
        )
    )
