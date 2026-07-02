#!/usr/bin/env python3
"""One-off: move verbatim quotes out of ``note:`` onto the ``cite:`` mapping.

Rewrites the unshipped patches (> 0038 — everything at or below is applied to
prod and frozen; its DB rows are fixed by the flipcommons data migration
instead). For each unit whose ``note:`` the recognizer matches and which
carries a scalar ``cite:``, the quote moves to a ``{ref, quote}`` mapping and
the note becomes its residual (or disappears when empty).

Surgical line edits, not a YAML round-trip: notes and cites are single-line
scalars, so replacing exactly those lines keeps comments, key order and the
rest of the file byte-identical — the git diff IS the human review artifact.

Skips (each reported, never silent): unrecognized notes, quote-notes with no
cite, units whose note names a source that disagrees with the cite (moving
the quote would mis-attribute it) and mapping-form cites.

Usage: PYTHONPATH=scripts uv run python -m quote_rewrite.rewrite_patches [--write]
Without ``--write`` it reports what would change.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

import yaml
from quote_rewrite.extract_quote import extract_quote

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PATCHES_DIR = REPO_ROOT / "patches"

# Patches at or below this number are applied to prod: their files are frozen
# history and their DB rows are migrated in flipcommons instead.
LAST_SHIPPED_PATCH = 38

_NOTE_LINE_RE = re.compile(r"^(?P<indent>\s*)note: (?P<scalar>.+)$")
_CITE_LINE_RE = re.compile(r"^(?P<indent>\s*)cite: (?P<scalar>.+)$")

# The note's source phrase implies a cite shape for the sources we can check.
# A miss means the note quotes one source while the unit cites another —
# moving the quote would mis-attribute it, so the unit is skipped + reported.
_SOURCE_CITE_HINTS = {
    "ipdb": re.compile(r"^ipdb:"),
    "opdb": re.compile(r"^opdb:"),
    "wikipedia": re.compile(r"wikipedia\.org"),
    "kineticist": re.compile(r"kineticist\.com"),
    "eremeka": re.compile(r"thetastates\.com"),
    "early arcades japan": re.compile(r"earlyarcadesjapan"),
}


class Rewrite(NamedTuple):
    """One unit's planned edit: line indexes plus the replacement text."""

    note_index: int
    cite_index: int
    note_replacement: list[str]
    cite_replacement: list[str]


def _load_scalar(line: str) -> object:
    """Parse one ``key: value`` line's value through the YAML scalar grammar."""
    return next(iter(yaml.safe_load(line).values()))


def _emit_scalar(value: str) -> str:
    """Encode *value* as a single-line YAML scalar, matching house style.

    Single-quoted (the patches' predominant style) unless the value needs
    double-quote escaping (control characters); ``yaml.dump`` handles that
    fallback.
    """
    encoded = yaml.dump(
        value, default_style="'", allow_unicode=True, width=10**9
    ).strip()
    # yaml.dump of a bare scalar appends an end-of-document newline marker
    # only sometimes; strip any trailing "\n..." document terminator.
    return encoded.removesuffix("\n...").strip()


def _cite_matches_source(source_phrase: str, cite: str) -> bool:
    """False only when the note names a checkable source the cite disagrees with."""
    phrase = source_phrase.lower()
    for token, pattern in _SOURCE_CITE_HINTS.items():
        if token in phrase:
            return bool(pattern.search(cite))
    return True


def _unit_bounds(lines: list[str], note_index: int, indent: str) -> tuple[int, int]:
    """The contiguous block of lines belonging to the note's unit.

    A unit's fields share the note's indentation; the block ends where a line
    dedents below it or a new list item opens at the same level.
    """

    def in_unit(line: str) -> bool:
        if not line.strip():
            return False
        current = line[: len(line) - len(line.lstrip())]
        if len(current) < len(indent):
            return False
        return not (len(current) == len(indent) and line.lstrip().startswith("- "))

    start = note_index
    while start > 0 and in_unit(lines[start - 1]):
        start -= 1
    end = note_index
    while end + 1 < len(lines) and in_unit(lines[end + 1]):
        end += 1
    return start, end


def plan_file(path: Path) -> tuple[list[Rewrite], list[str]]:
    """Plan every rewrite in one patch file; return (rewrites, skip reports)."""
    lines = path.read_text().split("\n")
    rewrites: list[Rewrite] = []
    reports: list[str] = []

    for i, line in enumerate(lines):
        note_match = _NOTE_LINE_RE.match(line)
        if note_match is None:
            continue
        note = _load_scalar(line)
        if not isinstance(note, str) or '"' not in note:
            continue
        where = f"{path.name}:{i + 1}"
        extracted = extract_quote(note)
        if extracted is None:
            reports.append(f"{where}: unrecognized quote-note (hand-fix): {note[:80]}")
            continue

        indent = note_match.group("indent")
        start, end = _unit_bounds(lines, i, indent)
        cite_indexes = [
            j
            for j in range(start, end + 1)
            if (cite_match := _CITE_LINE_RE.match(lines[j])) is not None
            and cite_match.group("indent") == indent
        ]
        if not cite_indexes:
            # The own-data case: the evidence is the entity itself; the quote
            # stays in the note.
            reports.append(f"{where}: quote-shaped note with no cite (left alone)")
            continue
        if len(cite_indexes) > 1:
            reports.append(f"{where}: multiple cite lines in unit (hand-fix)")
            continue
        cite_index = cite_indexes[0]
        cite = _load_scalar(lines[cite_index])
        if not isinstance(cite, str):
            reports.append(f"{where}: mapping-form cite (hand-fix)")
            continue
        if not _cite_matches_source(extracted.source, cite):
            reports.append(
                f"{where}: note quotes {extracted.source!r} but cite is "
                f"{cite!r} (hand-fix)"
            )
            continue

        note_replacement = (
            [f"{indent}note: {_emit_scalar(extracted.residual)}"]
            if extracted.residual
            else []
        )
        cite_replacement = [
            f"{indent}cite:",
            f"{indent}  ref: {cite}",
            f"{indent}  quote: {_emit_scalar(extracted.quote)}",
        ]
        rewrites.append(Rewrite(i, cite_index, note_replacement, cite_replacement))

    return rewrites, reports


def apply_rewrites(lines: list[str], rewrites: list[Rewrite]) -> list[str]:
    """Apply planned line replacements, working bottom-up so indexes hold."""
    replacements: dict[int, list[str]] = {}
    for rewrite in rewrites:
        replacements[rewrite.note_index] = rewrite.note_replacement
        replacements[rewrite.cite_index] = rewrite.cite_replacement
    out: list[str] = []
    for i, line in enumerate(lines):
        if i in replacements:
            out.extend(replacements[i])
        else:
            out.append(line)
    return out


def main() -> int:
    write = "--write" in sys.argv
    total = 0
    for path in sorted(PATCHES_DIR.glob("*.yaml")):
        number = int(path.name[:4])
        if number <= LAST_SHIPPED_PATCH:
            continue
        rewrites, reports = plan_file(path)
        for report in reports:
            print(f"SKIP  {report}")
        if not rewrites:
            continue
        total += len(rewrites)
        print(f"{'WRITE' if write else 'PLAN '} {path.name}: {len(rewrites)} unit(s)")
        if write:
            lines = path.read_text().split("\n")
            path.write_text("\n".join(apply_rewrites(lines, rewrites)))
    print(f"\n{total} unit(s) {'rewritten' if write else 'would be rewritten'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
