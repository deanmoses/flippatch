"""Emit patch 0220 — the Transformers family: 2026 MTMTE trio, 2011 editions, The Pin.

See ../0215-frontier-2026/ENRICHMENT-PLAN.md for the family split and
Transformers.md beside this file for the evidence inventory, the catalog
baseline, the traps and the decisions this generator encodes (2026-08-08).

SCOPE IS THE WHOLE FAMILY, eight models:
  2026  Transformers: More Than Meets the Eye — Pro / Premium / Limited Edition
  2011  Transformers — Pro / Limited Edition ("Combo") / Autobot Crimson / Decepticon Violet
  2012  Transformers The Pin (its OWN Title — never query by title_slug)

Only missing facts are asserted; the baseline table in Transformers.md records
what each model already holds. Deliberately absent (each recorded there):
  production_quantity + tags on the 2011 LEs and The Pin   already claimed (ipdb/opdb/0215)
  themes                                                   all eight already set
  month on the 2026 trio      the PR dates the release, not manufacture
  player_count on the 2026 trio   no primary source states it
  art credits (2011 and 2026)     sought at authoring time, none found
  descriptions                    a follow-up patch's job (inline-cite rules)
  The Pin player_count 4-vs-2 conflict   existing fact, flagged for the user

THE MATRIX IS MARKS, MOSTLY: a feature row's column membership is a visual
checkmark, so per-edition attaches cite the matrix quote-less (ref + locator +
note recording the checked rows) — see ENRICHMENT-PLAN.md → Citing PDF
evidence. Prose that names its own subject (the PR's LE equipment sentence,
the "GAME FEATURES LE ONLY" block) is quoted normally.

THE VARIANT RULE (user decision 2026-08-07): a variant carries every credit
and the shared design's hardware of its base. Applied here to Autobot Crimson
and Decepticon Violet (variants of the 2011 LE): they carry the LE's playfield
feature set and shared-design facts, cited to the LE's own evidence with a
note saying why the value follows. The 2026 LE needs no carry — the matrix
states its column directly.

Run: uv run python campaigns/0215-frontier-2026/model-families/transformers/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0220-transformers.yaml"

# ── Models ──────────────────────────────────────────────────────────────
M26_PRO = "model.transformers-more-than-meets-the-eye-pro"
M26_PREM = "model.transformers-more-than-meets-the-eye-premium"
M26_LE = "model.transformers-more-than-meets-the-eye-limited-edition"
M11_PRO = "model.transformers-pro"
M11_LE = "model.transformers-limited-edition"
M11_CRIM = "model.transformers-autobot-crimson-limited-edition"
M11_VIOL = "model.transformers-decepticon-violet-limited-edition"
PIN = "model.transformers-the-pin"

# ── Sources ─────────────────────────────────────────────────────────────
PR = (
    "https://www.sternpinball.com/2026/05/20/"
    "roll-out-for-battle-with-transformers-more-than-meets-the-eye-by-stern-pinball"
)
SOTU_AUG = "https://www.sternpinball.com/2026/08/04/stern-of-the-union-address-august-2026"
MATRIX = (
    "https://wp.sternpinball.com/wp-content/uploads/2026/05/"
    "Transformers-More-Than-Meets-the-Eye-Feature-Matrix.pdf"
)
MANUAL26 = (
    "https://wp.sternpinball.com/wp-content/uploads/2026/07/Transformers_MTMTE_Pro_web.pdf"
)
VIDEO = "youtube:zLx93Iiy5yw"
KINETICIST = "https://www.kineticist.com/news/stern-transformers-reveal"

# The 2011-era Stern pages are dead on sternpinball.com; each cite carries the
# original publisher URL as ref and the Wayback id_ snapshot as archive.
PAGE11_PRO = "http://www.sternpinball.com/Games/transformers-pro.aspx"
PAGE11_PRO_AR = (
    "http://web.archive.org/web/20110928030152id_/"
    "http://www.sternpinball.com/Games/transformers-pro.aspx"
)
PAGE11_LE = "http://www.sternpinball.com/Games/transformers-le.aspx"
PAGE11_LE_AR = (
    "http://web.archive.org/web/20111203043615id_/"
    "http://www.sternpinball.com/Games/transformers-le.aspx"
)
PAGE_PIN = "http://www.sternpinball.com/Games/transformers-pin.aspx"
PAGE_PIN_AR = (
    "http://web.archive.org/web/20121207090811id_/"
    "http://www.sternpinball.com/Games/transformers-pin.aspx"
)
# The 2011 manual (one file served under two names — see Transformers.md →
# Traps). OCR-only: its quote below is TRANSCRIBED off the rendered sheet.
MANUAL11 = "https://wp.sternpinball.com/wp-content/uploads/2018/11/Transformers-Manual.pdf"
# The Pin flyer, dead on sternpinball.com, recovered via the Wayback id_
# snapshot. Outlined type: its quote is transcribed off the rendered sheet.
FLYER_PIN = "http://sternpinball.com/upload/Games/PinTransformers-Flyer-1012-01c.pdf"
FLYER_PIN_AR = (
    "http://web.archive.org/web/20130211085308id_/"
    "http://sternpinball.com/upload/Games/PinTransformers-Flyer-1012-01c.pdf"
)

IPDB_PRO11 = "ipdb:5709"
IPDB_LE11 = "ipdb:5753"
IPDB_PIN = "ipdb:5861"

MATRIX_LOCATOR = "PDF document page 1 of 1; the sheet carries no printed folio"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def page11(ref: str, archive: str, quote: str) -> dict[str, str]:
    return {"ref": ref, "archive": archive, "quote": quote}


MATRIX_MARK_CITE = {"ref": MATRIX, "locator": MATRIX_LOCATOR}


def mark_note(column: str, rows: str) -> str:
    """The entry note for a quote-less matrix mark cite.

    A checkmark is a mark, not text — nothing to transcribe, so no quote;
    the note records the visual observation (ENRICHMENT-PLAN.md → Citing
    PDF evidence).
    """
    return f"On the feature matrix sheet, the {column} column carries a checkmark for the rows: {rows}"


def vocab(
    slug: str,
    name: str,
    *,
    parents: list[str] | None = None,
    aliases: list[str] | None = None,
) -> str:
    rel: dict[str, list[str]] = {}
    if parents:
        rel["gameplay_feature_parent"] = parents
    if aliases:
        rel["gameplay_feature_alias"] = aliases
    return pk.entry(
        f"gameplay-feature.{slug}",
        create=True,
        fields={"name": name},
        relationships=rel or None,
    )


# ── Shared MTMTE quotes ─────────────────────────────────────────────────
PR_AVAILABLE = (
    "TRANSFORMERS: More Than Meets the Eye by Stern Pinball is available now "
    "in Pro, Premium, and Limited Edition (LE) models."
)
PR_RELEASED = "revealed and released a new adrenaline-fueled pinball experience"
SOTU_ROLLING = (
    "TRANSFORMERS: More Than Meets The Eye pinball machines are rolling out worldwide"
)
MATRIX_SPIKE3 = (
    "This one-of-a-kind pinball experience is powered by Stern's "
    "next-generation technology with the new SPIKE 3 platform."
)
PR_TOYS = (
    "pushes mechanical innovation to new heights with a fully animatronic "
    "Megatron robot toy with an articulated fusion cannon that rotates and "
    "fires pinballs back at players. Soundwave's cassette deck locks pinballs "
    "before launching them into high-intensity action while a custom sculpted "
    "Optimus Prime robot bash toy stands ready for battle"
)
PR_HEAD_TO_HEAD = (
    "for the first time, includes a head-to-head experience that allows two "
    "players to compete simultaneously in real time"
)
PR_LE_EQUIPMENT = (
    "Limited to 750 games globally, the highly collectible Limited Edition "
    "model includes the updated Expression Lighting System™ and Speaker "
    "Expression Lighting System with TRANSFORMERS-themed game effects, a "
    "full-color mirrored backglass, full-color high-definition cabinet "
    "decals, exclusive custom pinball armor, a custom designer-autographed "
    "bottom arch, upgraded audio system, anti-reflection pinball playfield "
    "glass, shaker motor, a sequentially numbered plaque, a signed "
    "Certificate of Authenticity, and a digital Insider Connected LE owner's "
    "badge on registration."
)
VIDEO_LEADS = (
    "Hi, I'm Elliot Eisman, lead game designer for Transformers more than "
    "meets the eye. [...] Hi, I'm Elizabeth Geski, lead software [...] "
    "developer for Transformers: More Than Meets the Eye."
)
KINETICIST_LEADS = "Design: Elliot Eismin [...] Lead Programmer: Elizabeth Gieske"
KINETICIST_TEAM = (
    "Lead Mechanical: Rob Blakeman [...] Code: Mike Kyzivat [...] "
    "Audio: Jerry Thompson [...] Lead LCD Artist: Tom Kyzivat"
)
ASR_NOTE = (
    "The reveal video's auto-captions misspell both names ('Eisman', "
    "'Geski'); the quote is verbatim ASR. The spellings Eismin and Gieske "
    "follow the feature matrix ('Game Designer Elliot Eismin') and the "
    "Kineticist and Arcade Heroes coverage."
)
TEAM_NOTE = (
    "Kineticist's Design Team block is the only non-crowdsourced source "
    "naming these four; corroborating first-party sources were sought at "
    "authoring time and none found (the manual carries no credits). 'Lead "
    "LCD Artist' maps to the animation role and 'Audio' to sound."
)

# All-editions matrix rows, per section (the check readings are recorded in
# Transformers.md → Evidence inventory; transcribed off the rendered sheet
# 2026-08-08). Row lists inside a note stay verbatim row labels.
ROWS_COMMON_GF = (
    "Custom sculpted Optimus Prime robot bash toy; Optimus Prime V.U.K. "
    "(leads to Soundwave for ball locks, starts Transformers Multiball); "
    "Energon optical spinner; Right Ramp With Laser Cut Decepticon Logo; "
    "3 Bank Drop Targets; Complete Grimlock targets; Left Ramp With Laser "
    "Cut Autobot Logo; Bumblebee Captive Ball; Physical \"Add a Ball\" Ball "
    "Lock Post; 3 Flippers (2 Standard + 1 Upper Flipper); 2 Slingshots "
    "(2 Lower + 1 Upper Left); Full-spectrum RGB LED playfield arrow inserts"
)
# The features those common rows attach. Flipper count is stated by the row;
# the slingshot row contradicts itself (headline 2, enumeration 2+1) so
# slingshots attach count-less — see Transformers.md → Traps.
FEATURES_COMMON_GF: list[str | dict[str, int]] = [
    "bash-toys",
    "vertical-up-kickers",
    "multiball",
    "ball-locks",
    "up-posts",
    "optical-spinners",
    "ramps",
    "3-bank-drop-targets",
    "targets",
    "captive-ball",
    {"flippers": 3},
    "slingshots",
    "rgb-playfield-inserts",
]
SLINGSHOT_NOTE = (
    "The slingshot row's headline count (2) and its own enumeration "
    "(2 Lower + 1 Upper Left) disagree, so slingshots attach without a "
    "count; the flipper row appears twice on the sheet and attaches once."
)

ROWS_PREMLE_TOYS = (
    "Animatronic Megatron robot toy; Megatron Pinball Firing Fusion Cannon; "
    "Soundwave toy with physical Cassette Tape ball locks and ball ejection; "
    "Custom sculpted Grimlock Dinobot toy; Right Ramp Diverter (loads Fusion "
    "Cannon)"
)
FEATURES_PREMLE_TOYS: list[str | dict[str, int]] = [
    "animatronic-toys",
    "ball-cannons",
    "toys",
    "ramp-diverters",
]

ROWS_HW_PROPREM = (
    "Powder-coated black wrinkle finish hand guard side armor, hinges, "
    "front lockdown molding and legs; Multifunction Action Button on "
    "lockdown bar"
)
ROWS_HW_LE = "Multifunction Action Button on lockdown bar"
ROWS_GENERAL = "6 pinballs; Stereo sound system with 3-channel amplifier"

VARIANT_NOTE_2011 = (
    "This model is a cosmetic variant of the 2011 Transformers Limited "
    "Edition, so the base edition's shared design supports the value."
)


def mtmte_shared(model: str, column: str) -> list[str]:
    """The entries every 2026 edition gets; *column* names its matrix column."""
    return [
        pk.entry(
            model,
            cite=[
                cite(PR, PR_AVAILABLE),
                cite(SOTU_AUG, SOTU_ROLLING),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            model,
            cite=cite(PR, PR_RELEASED),
            fields={"game_format": "pinball"},
        ),
        # One changeset: both fields rest on the same SPIKE 3 statement.
        pk.entry(
            model,
            note=(
                "SPIKE 3 is Stern's computerized game platform, so the "
                "solid-state generation follows. The matrix row is checked "
                f"in all three edition columns, including {column}."
            ),
            cite=cite(MATRIX, MATRIX_SPIKE3, locator=MATRIX_LOCATOR),
            fields={
                "technology_generation": "solid-state",
                "system": "stern-spike-3",
            },
        ),
        pk.entry(
            model,
            note=mark_note(
                column, "Custom animations on larger, 18.5\" full HD display"
            ),
            cite=MATRIX_MARK_CITE,
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            model,
            note=ASR_NOTE,
            cite=[
                cite(VIDEO, VIDEO_LEADS),
                cite(KINETICIST, KINETICIST_LEADS, locator="in the Design Team section"),
            ],
            credits=[("elliot-eismin", "design"), ("elizabeth-gieske", "software")],
        ),
        pk.entry(
            model,
            note=TEAM_NOTE,
            cite=cite(KINETICIST, KINETICIST_TEAM, locator="in the Design Team section"),
            credits=[
                ("rob-blakeman", "mechanics"),
                ("mike-kyzivat", "software"),
                ("jerry-thompson", "sound"),
                ("tom-kyzivat", "animation"),
            ],
        ),
        pk.entry(
            model,
            note=mark_note(column, ROWS_COMMON_GF) + " " + SLINGSHOT_NOTE,
            cite=MATRIX_MARK_CITE,
            relationships={"gameplay_feature": FEATURES_COMMON_GF},
        ),
        pk.entry(
            model,
            note=mark_note(
                column, ROWS_HW_LE if column == "LE" else ROWS_HW_PROPREM
            ),
            cite=MATRIX_MARK_CITE,
            relationships={
                "gameplay_feature": (
                    ["lockdown-bar-buttons"]
                    if column == "LE"
                    else ["side-armor", "lockdown-bar-buttons"]
                )
            },
        ),
        pk.entry(
            model,
            note=mark_note(column, ROWS_GENERAL),
            cite=MATRIX_MARK_CITE,
            relationships={"gameplay_feature": [{"balls": 6}, "stereo-sound"]},
        ),
        pk.entry(
            model,
            cite=cite(PR, PR_HEAD_TO_HEAD),
            relationships={"gameplay_feature": ["head-to-head"]},
        ),
    ]


def mtmte_prem_le_toys(model: str, column: str) -> str:
    """The Premium/LE toy tier: PR prose plus the matrix column marks."""
    return pk.entry(
        model,
        note=mark_note(column, ROWS_PREMLE_TOYS),
        cite=[
            cite(PR, PR_TOYS),
            MATRIX_MARK_CITE,
        ],
        relationships={"gameplay_feature": FEATURES_PREMLE_TOYS},
    )


# The 2011 LE page's explicitly-headed feature blocks (HTML, machine-gated).
LE11_BLOCK_QUOTE = (
    '"Megatron Robot Form" rapid fire multiball cannon with "Cyber" ball '
    'lock. [...] "Ironhide" Transformer with "Chromium Cyber Sphere" '
    'player-controlled upper playfield. [...] "Starscream Strike" rotating '
    'action figure target. [...] "Cybertron Zenith and Nadir" orbit shots '
    'via second electronically-controlled gate. [...] "All Spark Cube" '
    'eject hole. [...] "Megatron Cyber Lock Guard" drop target. [...] '
    '"Quake Maker" shaker motor. [...] Elevating ramp to hit "Optimus '
    'Prime" target. [...] "Bumblebee Captive" Camaro target [...] "Full '
    'Spectrum Color Chroma" LED general illumination [...] "Ironhide" '
    "metal ramp."
)
LE11_BLOCK_FEATURES: list[str | dict[str, int]] = [
    "ball-cannons",
    "ball-locks",
    "mini-playfields",
    "rotating-targets",
    "orbits",
    "electric-gates",
    "kick-out-holes",
    "solitary-drop-targets",
    "shaker-motors",
    "moving-ramps",
    "captive-ball",
    "led-general-illumination",
    "ramps",
]
# The Crimson/Violet variant carry adds the base LE's side-armor span (their
# own blocks say "Full cabinet trim", which names the color, not the armor).
LE11_CARRY_QUOTE = LE11_BLOCK_QUOTE + (
    ' [...] "Decepticon Violet" side armor legs, hinge (left side).'
)
LE11_CARRY_FEATURES: list[str | dict[str, int]] = [*LE11_BLOCK_FEATURES, "side-armor"]
LE11_OWN_EXTRAS_QUOTE = (
    "Game Designer George Gomez' signature (#1-35). [...] 1-500 Numbered "
    "plaque and certificate of authenticity. [...] \"Decepticon Violet\" "
    "side armor legs, hinge (left side)."
)
IPDB_LE11_HARDWARE = (
    "Flippers (2), Pop bumpers (3), Slingshots (2). VUK four-ball multiball "
    "rapid-fire ejector."
)


def main() -> None:
    entries = [
        # ── Vocabulary (dependency order: parents before children) ──────
        # NB: `toys` is NOT created here — patch 0219 creates it, and 0220
        # applies after it, so the children below resolve against that node.
        # A "Robot Toy" alias on it would be a fact added to an existing
        # entity — left as a user call (the ball-locks precedent).
        vocab(
            "animatronic-toys",
            "Animatronic Toys",
            parents=["toys"],
            aliases=["Animatronic Robot Toy"],
        ),
        vocab("bash-toys", "Bash Toys", parents=["toys"], aliases=["Robot Bash Toy"]),
        vocab(
            "optical-spinners",
            "Optical Spinners",
            parents=["spinners"],
            aliases=["Optical Spinner"],
        ),
        # Stern's branded cabinet/speaker lighting systems — presentation
        # nodes on the 0218 footing, distinct from LED general illumination.
        vocab(
            "cabinet-expression-lighting",
            "Cabinet Expression Lighting",
            aliases=["Expression Lighting System", "Interactive Cabinet Expression Lighting System"],
        ),
        vocab(
            "speaker-expression-lighting",
            "Speaker Expression Lighting",
            aliases=["Speaker Expression Lighting System"],
        ),
        vocab("mirrored-backglasses", "Mirrored Backglasses", aliases=["Mirrored Backglass"]),
        vocab(
            "numbered-plaques",
            "Numbered Plaques",
            aliases=["Numbered Plaque", "Numbered Plate"],
        ),
        vocab(
            "designer-autographs",
            "Designer Autographs",
            aliases=["Designer Signature", "Game Designer Signature"],
        ),
        # ── Scaffolding: the SPIKE 3 system and the new person ──────────
        # Sibling systems (stern-spike-1/-2) carry manufacturer stern-pinball
        # and the ss-pc technology subgeneration; SPIKE 3 is their successor.
        pk.entry(
            "system.stern-spike-3",
            create=True,
            cite=cite(MATRIX, MATRIX_SPIKE3, locator=MATRIX_LOCATOR),
            fields={
                "name": "Stern SPIKE 3",
                "manufacturer": "stern-pinball",
                "technology_subgeneration": "ss-pc",
            },
        ),
        pk.entry(
            "person.elizabeth-gieske",
            create=True,
            note=(
                "Lead software developer on Transformers: More Than Meets "
                "the Eye, her first credit here. Spelling per Kineticist and "
                "Arcade Heroes; the reveal video's auto-captions render it "
                "'Geski'."
            ),
            cite=cite(
                KINETICIST,
                "Lead Programmer: Elizabeth Gieske",
                locator="in the Design Team section",
            ),
            fields={"name": "Elizabeth Gieske"},
        ),
        # ── 2026: Transformers MTMTE Pro ─────────────────────────────────
        *mtmte_shared(M26_PRO, "PRO"),
        pk.entry(
            M26_PRO,
            note=mark_note(
                "PRO",
                "Static Megatron robot toy starts missions featuring "
                "specific episodes from the TV series with custom recorded "
                "speech by Frank Welker",
            ),
            cite=MATRIX_MARK_CITE,
            relationships={"gameplay_feature": ["toys"]},
        ),
        pk.entry(
            M26_PRO,
            cite=cite(
                MANUAL26,
                "TRANSFORMERS: MORE THAN MEETS THE EYE PRO #500-55AA-01",
                locator="PDF document page 1; the sheet carries no printed folio",
            ),
            fields={"manufacturer_model_identifier": "500-55AA-01"},
        ),
        # ── 2026: Transformers MTMTE Premium ────────────────────────────
        *mtmte_shared(M26_PREM, "PREM"),
        mtmte_prem_le_toys(M26_PREM, "PREM"),
        # ── 2026: Transformers MTMTE Limited Edition ────────────────────
        *mtmte_shared(M26_LE, "LE"),
        mtmte_prem_le_toys(M26_LE, "LE"),
        pk.entry(
            M26_LE,
            note=(
                "Stern's modern Limited Edition models are variants of their "
                "Premium models, and the feature matrix's PREM and LE columns "
                "carry identical game-feature checks — the LE differs only in "
                "its limited-edition equipment tier."
            ),
            cite=cite(PR, PR_AVAILABLE),
            fields={"variant_of": "transformers-more-than-meets-the-eye-premium"},
        ),
        pk.entry(
            M26_LE,
            cite=cite(PR, "Limited to 750 games globally"),
            fields={"production_quantity": 750},
            tags=["limited-edition"],
        ),
        pk.entry(
            M26_LE,
            cite=cite(PR, PR_LE_EQUIPMENT),
            relationships={
                "gameplay_feature": [
                    "cabinet-expression-lighting",
                    "speaker-expression-lighting",
                    "mirrored-backglasses",
                    "cabinet-armor",
                    "designer-autographs",
                    "anti-reflection-playfield-glass",
                    "shaker-motors",
                    "numbered-plaques",
                ]
            },
        ),
        # ── 2011: Transformers (Pro) ────────────────────────────────────
        pk.entry(
            M11_PRO,
            cite=page11(PAGE11_PRO, PAGE11_PRO_AR, "In Production"),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            M11_PRO,
            cite=cite(
                IPDB_PRO11,
                "Flippers (2), Pop bumpers (3), Kick-out hole (1), Spinning "
                "target (1), Captive ball (1).",
            ),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            M11_PRO,
            cite=page11(
                PAGE11_PRO,
                PAGE11_PRO_AR,
                '"Megatron Vehicle Form" Rapid Fire Multiball with "Cyber" '
                "Ball Lock and Illuminated Eyes [...] \"Optimus Prime\" Target "
                'with "M.T.M.T.E." (More Than Meets The Eye) Elevating Ramp to '
                'hit target [...] "Decepticon" Laser-Cut Steel Ramp [...] '
                '"Cybertron Zenith Orbit Shot" with electronically-controlled '
                "gate",
            ),
            relationships={
                "gameplay_feature": [
                    "multiball",
                    "ball-locks",
                    "moving-ramps",
                    "ramps",
                    "orbits",
                    "electric-gates",
                ]
            },
        ),
        # ── 2011: Transformers (Limited Edition, the "Combo") ───────────
        pk.entry(
            M11_LE,
            cite=page11(PAGE11_LE, PAGE11_LE_AR, "In Production"),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            M11_LE,
            cite=cite(IPDB_LE11, IPDB_LE11_HARDWARE),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            M11_LE,
            cite=page11(PAGE11_LE, PAGE11_LE_AR, LE11_BLOCK_QUOTE),
            relationships={"gameplay_feature": LE11_BLOCK_FEATURES},
        ),
        pk.entry(
            M11_LE,
            cite=page11(PAGE11_LE, PAGE11_LE_AR, LE11_OWN_EXTRAS_QUOTE),
            relationships={
                "gameplay_feature": [
                    "designer-autographs",
                    "numbered-plaques",
                    "side-armor",
                ]
            },
        ),
        # ── 2011: Autobot Crimson + Decepticon Violet (variants of the LE)
        *[
            entry
            for model, own_block_quote in (
                (
                    M11_CRIM,
                    "Autobot Crimson LIMITED EDITION Features: [...] Unique "
                    '"Autobot" backglass art. [...] Game Designer George '
                    "Gomez' signature. [...] 1-125 Numbered plaque and "
                    "certificate of authenticity.",
                ),
                (
                    M11_VIOL,
                    "Decepticon Violet LIMITED EDITION Features: [...] Unique "
                    '"Decepticon" backglass art. [...] Game Designer George '
                    "Gomez' signature. [...] 1-125 Numbered plaque and "
                    "certificate of authenticity.",
                ),
            )
            for entry in (
                pk.entry(
                    model,
                    note=(
                        "The archived LE page's edition blocks cover this "
                        "model (its Autobot Crimson and Decepticon Violet "
                        "features lists sit beside the badge)."
                    ),
                    cite=page11(PAGE11_LE, PAGE11_LE_AR, "In Production"),
                    fields={"production_status": "produced"},
                ),
                pk.entry(
                    model,
                    note=VARIANT_NOTE_2011,
                    cite=cite(IPDB_LE11, IPDB_LE11_HARDWARE),
                    fields={"game_format": "pinball"},
                ),
                pk.entry(
                    model,
                    note=(
                        "The 2011 service manual documents the design shared "
                        "by every 2011 Transformers edition; this model is a "
                        "variant of the Limited Edition, so the display "
                        "carries. Transcribed off the rendered sheet "
                        "(OCR-only document)."
                    ),
                    cite=cite(
                        MANUAL11,
                        "128 X 32 Dot Matrix Display PCB",
                        locator="printed page p 3, PDF document page 42",
                    ),
                    fields={"display_type": "dot-matrix"},
                ),
                pk.entry(
                    model,
                    note=VARIANT_NOTE_2011,
                    cite=page11(PAGE11_LE, PAGE11_LE_AR, LE11_CARRY_QUOTE),
                    relationships={"gameplay_feature": LE11_CARRY_FEATURES},
                ),
                pk.entry(
                    model,
                    cite=page11(PAGE11_LE, PAGE11_LE_AR, own_block_quote),
                    relationships={
                        "gameplay_feature": ["designer-autographs", "numbered-plaques"]
                    },
                ),
            )
        ],
        # ── 2012: Transformers The Pin ──────────────────────────────────
        pk.entry(
            PIN,
            cite=page11(PAGE_PIN, PAGE_PIN_AR, "In Production"),
            fields={"production_status": "produced"},
        ),
        # Corrects the unexplained 4 from an earlier ingest (user-approved
        # 2026-08-08): IPDB states 2 players, and the machine's speaker panel
        # carries exactly two score displays, labeled PLAYER 1 and PLAYER 2 —
        # the hardware ceiling on players.
        pk.entry(
            PIN,
            note=(
                "The prior value of 4 arrived uncited via an earlier ingest "
                "and appears propagated from OPDB. The machine has exactly "
                "two score displays: the flyer's product photo shows the "
                "speaker panel's two displays labeled PLAYER 1 and PLAYER 2 "
                "(transcribed off the rendered sheet), matching IPDB's "
                "player count."
            ),
            cite=[
                cite(IPDB_PIN, "Players: 2 [...] Two 8-digit LED score displays."),
                {
                    "ref": FLYER_PIN,
                    "archive": FLYER_PIN_AR,
                    "locator": "PDF document page 2 of 2; the flyer carries no printed folios",
                    "quote": "PLAYER 1 [...] PLAYER 2",
                },
            ],
            fields={"player_count": "2"},
        ),
        # One changeset: format and the slingshot count rest on the same
        # hardware line (its missing comma is IPDB's own — likely why the
        # seed ingest dropped the slingshots).
        pk.entry(
            PIN,
            cite=cite(IPDB_PIN, "Flippers (2), Pop bumpers (3) Slingshots (2)."),
            fields={"game_format": "pinball"},
            relationships={"gameplay_feature": [{"slingshots": 2}]},
        ),
        pk.entry(
            PIN,
            cite=page11(
                PAGE_PIN,
                PAGE_PIN_AR,
                "Genuine Stern Pinball Flippers, Slingshots, and Plunger [...] "
                "All LED lighting to provide optimal color and lighting "
                "performance [...] Licensed Transformers Art, Music, Speech, "
                "and Sound Effects",
            ),
            relationships={
                "gameplay_feature": ["plungers", "led-general-illumination", "speech"]
            },
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Transformers family details across the 2011, 2012 and 2026 Stern models",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
