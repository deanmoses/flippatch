"""The sweep's field registry — what each judgeable field *means*.

One :class:`FieldSpec` per sweepable catalog field: the DB column it diffs
against, the question the model answers, and the hand-crafted recognition
guidance (AiCommon.md §4's layer 2 — the polarity/direction traps the data
itself doesn't state). v1 ships the three relational lineage fields the
0128-relationships campaign works; boolean/tag fields (widebody, nixie) are a
later archetype and get their own spec kind when built.

Guidance is deliberately explicit about the traps the plan documents: a note
may state the relationship about a *companion* machine rather than the one
under judgment; conversion direction (converted FROM vs a donor whose note says
others converted *it*); and hedged language, which must land ``uncertain``
rather than a confident verdict.
"""

from __future__ import annotations

from dataclasses import dataclass

# The guidance block every relational lineage field shares: companion-machine
# polarity, direction, and hedging. Field-specific guidance is appended to it.
_SHARED_RELATIONAL_GUIDANCE = """\
Traps to avoid:
- COMPANION-MACHINE POLARITY: a note often mentions OTHER machines (the \
original, a sibling, a reissue). Only affirm the relationship when the note \
states it about THIS machine. "The other version is a copy" describes the \
other machine, not this one.
- DIRECTION: answer yes only when THIS machine derives from the named target. \
If the note says other makers copied or converted THIS machine, the \
relationship belongs on those other machines — answer no and say so in reason.
- HEDGES: "possibly", "may be", "probably", "whether licensed or not is \
unknown" and similar hedged or disputed statements are verdict uncertain, \
never a confident yes or no.
- JOINT TARGETS: if the note derives this machine from TWO OR MORE games \
jointly ("a kit for X and Y"), answer uncertain and name them in reason — a \
single target cannot be chosen from the note alone.
- Name the target EXACTLY as the note spells it (title as printed, without \
the maker or year folded in), and report the maker and year the note states \
for the target, if any, in their own fields."""


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """One sweepable relational field: its DB column, question, and guidance.

    ``column`` is the ``catalog_machinemodel`` self-FK column the reconciler
    diffs (``converted_from_id``, …). ``target_role`` names what the target *is*
    in prose ("the donor game"), for prompts and review rendering.
    ``companion_tag`` is the tag the catalog pairs with the relationship
    (``bootleg`` / ``licensed-build``), or None where there is none.
    ``target_other_maker`` is True where the target must belong to a DIFFERENT
    maker than the subject (a machine cannot be a licensed build or bootleg of
    its own maker's game; an in-house conversion, however, is legitimate).
    ``claim_verb`` renders the relationship as prose for the fill gate's
    quote-supports-claim check ("<subject> <claim_verb> <target>").
    """

    key: str
    column: str
    question: str
    target_role: str
    guidance: str
    claim_verb: str
    companion_tag: str | None = None
    target_other_maker: bool = False


RELATIONAL_FIELDS: dict[str, FieldSpec] = {
    spec.key: spec
    for spec in (
        FieldSpec(
            key="converted_from",
            column="converted_from_id",
            question=(
                "Is this machine a conversion — a re-themed game built on "
                "another game's existing hardware (a conversion kit: new "
                "playfield/backglass/artwork installed on the donor game's "
                "cabinet and boards)? If yes, name the DONOR game it was "
                "converted from."
            ),
            target_role="the donor game it was converted from",
            claim_verb="is a conversion built on the hardware of",
            guidance=(
                _SHARED_RELATIONAL_GUIDANCE
                + "\n- A conversion REUSES the donor's hardware. A newly "
                "manufactured unauthorized copy is a bootleg, not a conversion "
                "— answer no if the note describes a complete copy rather "
                "than a kit/re-theme on existing hardware."
            ),
        ),
        FieldSpec(
            key="bootleg_of",
            column="bootleg_of_id",
            question=(
                "Is this machine a bootleg — an unauthorized copy of another "
                "maker's design, built as a complete machine without a "
                "license? If yes, name the ORIGINAL design it copies."
            ),
            target_role="the original design it copies",
            claim_verb="is an unauthorized copy (bootleg) of",
            guidance=(
                _SHARED_RELATIONAL_GUIDANCE
                + "\n- 'Under license', 'licensed by', or an authorized "
                "subsidiary/licensee building the game means it is NOT a "
                "bootleg (that is a licensed build) — answer no.\n"
                "- A conversion kit installed on a donor game's hardware is a "
                "conversion, not a bootleg — answer no.\n"
                "- 'Copy of', 'near copy of', or a clone described without "
                "any license supports yes.\n"
                "- The target is another maker's ORIGINAL design. If the note "
                "describes this machine as a version/variant of the SAME "
                "maker's own game, that game is not the target — name the "
                "other maker's original if the note identifies it, else "
                "answer uncertain."
            ),
            companion_tag="bootleg",
            target_other_maker=True,
        ),
        FieldSpec(
            key="licensed_build_of",
            column="licensed_build_of_id",
            question=(
                "Is this machine a licensed build — a complete machine built "
                "under license (an authorized twin, e.g. by a licensee or "
                "foreign subsidiary for another market)? If yes, name the "
                "ORIGINAL machine it is a licensed build of."
            ),
            target_role="the original machine it is a licensed build of",
            claim_verb="is a licensed build of",
            guidance=(
                _SHARED_RELATIONAL_GUIDANCE
                + "\n- The note must actually state authorization ('under "
                "license from', 'licensed'). A copy with no license language "
                "is a bootleg candidate, not a licensed build — answer no.\n"
                "- A THEME license (a licensed movie/band theme) is not a "
                "licensed build of another MACHINE — answer no.\n"
                "- The target is the LICENSOR's original — a machine by "
                "ANOTHER maker. If the note describes this machine as a "
                "version/variant of the SAME maker's own game (e.g. an "
                "add-a-ball export version), that game is a chain link, not "
                "the target — name the other maker's original the license "
                "traces back to if the note identifies it, else answer "
                "uncertain."
            ),
            companion_tag="licensed-build",
            target_other_maker=True,
        ),
    )
}
