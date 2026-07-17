"""The sweep's field registry — what the judgeable field *means*.

Since ModelRelationships shipped, a model's copy / conversion / conversion-kit
/ re-theme lineage is one join table (`catalog_modelrelationship`), not three
self-FK columns. So the sweep judges a single field, ``model_relationship``:
the model reports *every* relationship its note supports, each carrying a
``relationship_type`` (``copy`` | ``conversion`` | ``conversion_kit`` |
``retheme``) and a ``license_status`` (``licensed`` | ``unlicensed`` |
``unknown``), plus a target that is either a resolvable machine or a
plural/unseeded text label.

This module holds the hand-crafted recognition guidance (AiCommon.md §4's
layer 2 — the polarity/direction/type/license traps the data itself doesn't
state) and the per-type rules the deterministic gate needs. "Bootleg" and
"licensed build" are not fields: they are ``copy`` + ``unlicensed`` / ``copy``
+ ``licensed``, judged as the two axes.
"""

from __future__ import annotations

from dataclasses import dataclass

# The single field key the sweep judges. Kept as a registry key (rather than
# hardcoded everywhere) so a future non-relationship archetype — widebody,
# nixie — can slot in beside it without reworking the candidate contract.
MODEL_RELATIONSHIP = "model_relationship"

RELATIONSHIP_TYPES = ("copy", "conversion", "conversion_kit", "retheme")
LICENSE_STATUSES = ("licensed", "unlicensed", "unknown")

# The relationship types whose target must belong to a DIFFERENT maker: a copy
# reproduces ANOTHER maker's design, so a same-maker "copy target" is a chain
# link (the maker's own variant the note mentions on the way to the real
# original), never valid. Conversions may be in-house, so they are exempt — and
# so are re-themes, which are routinely a maker re-skinning its own machine.
_OTHER_MAKER_TYPES = frozenset({"copy"})

# The relationship types whose target must be a seeded machine. A re-theme's
# donor is always a known machine, so DataPatches rejects a `target_label` on
# one and the DB carries a matching CHECK — a label-target re-theme cannot
# ingest, so the gate escalates rather than greening it into an unauthorable
# patch. Mirrors flipcommons' RELATIONSHIP_TYPE_BEHAVIOR.requires_machine_target.
_MACHINE_TARGET_TYPES = frozenset({"retheme"})

# How each type renders as a prose claim for the fill gate's quote-supports-
# claim check ("<subject> <verb> <target>").
_CLAIM_VERBS = {
    "copy": "is a copy (reproduces the design) of",
    "conversion": "is a conversion built on the hardware of",
    "conversion_kit": "is a conversion kit for the donor",
    "retheme": "is a re-theme (the same gameplay re-skinned with new art and theme) of",
}

# A non-`unknown` license_status is a SECOND fact the source must establish
# (DataPatches: "an unlicensed copy is relationship_type: copy + license_status:
# unlicensed, and the source must establish both facts"), so the fill gate's
# claim asserts it too. `unknown` asserts nothing — it means the source is
# silent on authorization, so there is nothing for a quote to establish.
_LICENSE_CLAUSES = {
    "licensed": "and it was built WITH the design owner's authorization (under license)",
    "unlicensed": (
        "and it was built WITHOUT the design owner's authorization (unlicensed)"
    ),
}


def requires_other_maker(rel_type: str) -> bool:
    """Must a ``rel_type`` target belong to a maker other than the subject's?"""
    return rel_type in _OTHER_MAKER_TYPES


def requires_machine_target(rel_type: str) -> bool:
    """Must a ``rel_type`` target be a seeded machine rather than a text label?"""
    return rel_type in _MACHINE_TARGET_TYPES


def claim_verb(rel_type: str) -> str:
    """The prose verb linking subject to target for a given relationship type."""
    return _CLAIM_VERBS.get(rel_type, "is related to")


def license_clause(license_status: str) -> str:
    """The extra fact a non-`unknown` ``license_status`` asserts, or "".

    Empty for `unknown`: that value means the source establishes no
    authorization either way, so the fill gate has nothing extra to check.
    """
    return _LICENSE_CLAUSES.get(license_status, "")


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """The judgeable field: its question and hand-crafted recognition guidance."""

    key: str
    question: str
    guidance: str


_GUIDANCE = """\
Report EVERY copy / conversion / conversion-kit / re-theme relationship the \
note supports FOR THIS MACHINE — a machine can have more than one (a copy of \
two designs, a kit that fits several donors, a re-theme of two donors). For \
each, give its relationship_type, its license_status, its target, and a \
verbatim quote. If the note supports none, return an empty list.

RELATIONSHIP TYPE:
- copy — reproduces another maker's design on NEWLY BUILT hardware (a clone / \
"copy of" / "near copy of").
- conversion — a COMPLETE machine built by reusing another machine or its \
components with a new playfield, rules or theme.
- conversion_kit — a set of PARTS sold to convert a compatible donor machine; \
its target means "works with this donor", and is often plural or unnamed \
(use a text label then, not a single machine).
  READ THE WHOLE NOTE BEFORE CHOOSING conversion vs conversion_kit. Notes \
state the EFFECT first and the PRODUCT later: "A conversion of Bally's 1979 \
'Harlem Globetrotters On Tour'." opens a note whose later sentences say "the \
owner of the uninstalled KIT pictured here" and "the production run quantity \
for this kit was 200 units" — that machine is a conversion_kit, and the lead \
sentence alone would have you call it a conversion. Kit language ANYWHERE in \
the note decides it: "kit", "uninstalled", a playfield "overlay", "decals", \
"stencils", parts "included", a production quantity counted in kits. "A \
conversion of X" describes what a kit DOES as readily as a purpose-built \
machine, so it never settles the question by itself.
- retheme — keeps another machine's GAMEPLAY and re-skins it with new art and \
a new theme ("a re-theme of", "the same game as X with new artwork", "X \
re-skinned as"). The re-theme is newly built or factory-reissued, not made \
from the donor's own hardware — that is a conversion — and it does not \
reproduce the donor's identity — that is a copy. A maker re-theming its OWN \
machine is normal and common; a re-theme's donor is ALWAYS a specific named \
machine, so never give a re-theme a text label.

LICENSE STATUS — an INDEPENDENT axis from relationship_type. Authorization \
says WHO permitted the machine; the type says WHAT the machine is. Neither is \
evidence for the other. In particular, a build being licensed, official or \
factory-authorized is NEVER evidence that it is a `retheme`: a licensed build \
is the SAME game with the SAME theme, built by someone else under license — \
that is `copy` + `licensed` (Segasa's Big Ben is Williams' Big Ben made in \
Spain under license: a copy, not a re-theme). A `retheme` requires the source \
to establish a CHANGED theme or artwork over kept gameplay; without that, no \
amount of "under license" makes one. Judge only what the note states:
- licensed — the note states authorization ("under license", "licensed by", an \
authorized subsidiary/licensee building it). For a re-theme this is the \
OFFICIAL/factory one: the note has the donor's maker (or its licensee) doing \
the re-skin.
- unlicensed — the note calls it a bootleg / unauthorized / pirate copy, or a \
copy explicitly built without a license. For a re-theme, an explicitly \
unofficial/homebrew re-skin.
- unknown — the note establishes the copy/conversion/re-theme but says nothing \
about authorization. This is the correct answer whenever licensing is not \
stated; do NOT guess licensed or unlicensed from silence, and do NOT infer a \
re-theme is unlicensed merely because a different maker made it.

AUTHORIZATION MAY LIVE IN A DIFFERENT SOURCE. You are sometimes given more \
than one source: the machine's own note, plus a maker-level history of the \
company. A machine note typically establishes only the COPY ("a copy of \
Bally's 1980 'Xenon'") and is silent on authorization, while the maker-level \
source establishes that this maker's copying was unauthorized. When BOTH are \
present, say so: give the machine note's sentence in `quote` (it names the \
target) and the maker-level sentence in `license_quote`, and set \
license_status accordingly. Each must be verbatim from whichever source \
carries it. Use `license_quote` ONLY for a real second source — if one \
sentence already establishes both ("an unauthorized copy of X"), it is just \
`quote` and license_quote stays empty. And silence is still silence: with no \
authorization statement in ANY provided source, the answer remains `unknown`.

A maker-level source is long and is often FRAMED around a different company \
than this machine's — a trade history titled for one manufacturer routinely \
names its competitors in passing ("X was not the only company doing this: Y, \
based in Z, did the same"). Do not judge such a source by its subject or \
title: search its whole text for THIS machine's maker by name. A passage that \
names this maker applies to this maker, whoever the page is mostly about. It \
must genuinely name them, though — a statement about the industry, or about \
some other company only, establishes nothing here.

TARGET — a machine XOR a text label:
- target_title — name ONE resolvable game (title as printed, without the \
maker or year folded in), and report its maker and year as the note states \
them, in target_maker and target_year. One relationship, one machine.
- target_label — use this instead when the target is plural or unidentified \
("many late-1970s solid-state Gottliebs"): put the phrase in target_label and \
leave the machine fields empty. Never fill both. NOT available for a re-theme \
(its donor is always a specific machine).

TRAPS:
- PARTS ARE NOT LINEAGE: every relationship here is about the MACHINE. A note \
saying this game shares a COMPONENT or ASSET with another — backglass or \
playfield ARTWORK, a cabinet, a sound board, a theme — reports no \
relationship at all. "Backglass artwork is in part a copy of X" means the ART \
was copied, not that this machine reproduces X's design; the same is true of \
"the playfield design borrows from X" and "reuse of the cabinet from X". \
Artwork and cabinets travel between unrelated machines routinely. Report a \
relationship only when the note derives the MACHINE from the target.
- COMPANION-MACHINE POLARITY: a note often mentions OTHER machines (the \
original, a sibling, a reissue). Only report a relationship the note states \
about THIS machine. "The other version is a copy" describes the other machine.
- DIRECTION: report a relationship only when THIS machine derives from the \
target. If the note says other makers copied or converted THIS machine, that \
relationship belongs on those other machines — do not report it here.
- HEDGES: "possibly", "may be", "probably", "whether licensed or not is \
unknown" and similar hedged or disputed statements are hedged=true, not a \
confident relationship.
- The quote for each relationship must be the sentence that ESTABLISHES it \
(normally the one naming the target); join spans with `[...]` if the \
establishing words are apart."""


SPEC = FieldSpec(
    key=MODEL_RELATIONSHIP,
    question=(
        "What copy, conversion, conversion-kit, or re-theme relationships does "
        "THIS machine have to other games?"
    ),
    guidance=_GUIDANCE,
)

# One-entry registry (see MODEL_RELATIONSHIP): the candidate contract still
# carries a ``field`` key, and this is the only valid value today.
RELATIONAL_FIELDS: dict[str, FieldSpec] = {SPEC.key: SPEC}
