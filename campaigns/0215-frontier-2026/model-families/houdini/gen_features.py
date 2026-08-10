"""Emit patch 0219 — Houdini family presentation & mech features.

Follow-up to 0216, made possible by 0218-presentation-feature-vocab (represent
ALL features, gameplay-affecting or not) and the verbatim-wording policy (use
the manufacturer's wording unless it's extremely clearly a synonym; when in
doubt, create a child feature). Houdini.md beside this file records the user
decisions (2026-08-08): mirrored-art-blades child of both art-blades and
mirror-blades; interior-side-art child of art-blades; flipper-toppers its own
node (NOT under cabinet toppers); plus a vocabulary sweep for the
flyer/site/IPDB features 0216 had to drop. steampunk-flippers is GONE
(2026-08-10): a Houdini-only decoration is a unique feature, not vocabulary.

Toys policy (user decision, 2026-08-10, flipcommons docs/plans/
catalog_data_model/unique_features/UniqueFeatures.md): bespoke toys are NOT
vocab nodes — a model asserts only the generic toy CLASSIFICATION tree built
here (toys → static/interactive → bash/animatronic/pop-up/ball-holding), and
the bespoke identities (Houdini's stage, trunk, planchette, milk can,
steampunk flippers) wait for the future UniqueFeature entity; Houdini.md
keeps their worklist. `toys` and `interactive-toys` are grouping nodes and
are never attached to a model directly.

MUST APPLY AFTER 0218: this patch attaches magic-glass, theater-spotlights,
speakers, anti-reflection-playfield-glass and the blade nodes, all created
there. Patches apply in numeric-prefix order, so 0219 is the earliest slot.

Evidence (all cached in pinexplore's web cache; see Houdini.md → Evidence
inventory):
  SPEC   https://americanpinball.com/houdini/  — covers ALL editions (the
         Choose Your Edition carousel includes the 100th), HTML, machine-gated
  ANN    https://americanpinball.com/houdini-100th-anniversary-pinball/
  IPDB   ipdb:6470 — the base 2017 game's row, machine-gated
  FLYER  the 2017 flyer, dead on american-pinball.com, recovered via the
         Wayback id_ snapshot. OCR-only (outlined type): quotes below are
         TRANSCRIBED off the rendered sheet, exactly as read — verify-quotes
         reports them SKIP-PDF by design.

The glass split: IPDB's "Glare-reduced playfield glass" lands on the base
model as anti-reflection-playfield-glass; the Deluxe and 100th instead carry
magic-glass (AP's branded child node) from the site/announcement, which names
it for those editions specifically.

Multiball count (user-approved 2026-08-08): "5 Multiballs" is five multiball
MODES — the site lists it among mode counts ("10 Stage Modes incl. Straight
Jacket Multiball") and states the 6-ball complement separately — and the
vocab defines multiball as a game state, so the counted grain reads as five
modes. {multiball: 5} rides on all three models; on the base model it
outranks the count-less ipdb seed claim (approved modification), and on the
editions it supersedes 0216's own count-less assertion at apply time.

Run: uv run python campaigns/0215-frontier-2026/model-families/houdini/gen_features.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0219-houdini-features.yaml"

MOM = "model.houdini-master-of-mystery"
DELUXE = "model.houdini-master-of-mystery-deluxe"
ANNIV = "model.houdini-100th-anniversary"

SPEC = "https://americanpinball.com/houdini/"
ANN = "https://americanpinball.com/houdini-100th-anniversary-pinball/"
IPDB = "ipdb:6470"
FLYER = "http://american-pinball.com/games/houdini/Houdini-Pinball-Flyer.pdf"
FLYER_ARCHIVE = (
    "http://web.archive.org/web/20250325113004id_/"
    "https://www.american-pinball.com/games/houdini/Houdini-Pinball-Flyer.pdf"
)

VARIANT_NOTE = (
    "IPDB 6470 is the base Houdini: Master of Mystery row; this model is a "
    "variant of it (same game design), so the base game's value carries."
)
FLYER_NOTE = (
    "The 2017 flyer documents the base machine; this model is a variant of it "
    "(same game design), so the playfield mechs carry."
)


def cite(ref: str, quote: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote}


def flyer_cite(quote: str) -> dict[str, str]:
    return {
        "ref": FLYER,
        "archive": FLYER_ARCHIVE,
        "locator": "PDF sheet 2 of 2; the flyer carries no printed folios",
        "quote": quote,
    }


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


# The spec page's Additional Features blocks, common to every edition; spans in
# page order.
SPEC_PLAYFIELD_QUOTE = (
    "Custom Padlock & Gear Bumper Tops w/ Chains [...] 6 Balls"
)
SPEC_PLAYFIELD_FEATURES: list[str | dict[str, int]] = [
    "bumper-tops",
    {"balls": 6},
]

# Toy classification from the same page. Only the trunk classifies: it
# receives launched balls (ball-holding). The stage, curtain, marquee,
# planchette and milk can are display elements or state no behaviour, so
# they classify nothing — their identities are UniqueFeature material
# (Houdini.md → future unique features).
SPEC_TOYS_QUOTE = 'Over 20" Launch into Houdini\'s Steamer Trunk'
SPEC_TOYS_FEATURES: list[str | dict[str, int]] = ["ball-holding-toys"]
SPEC_TOYS_NOTE = (
    "The steamer trunk toy receives launched balls, so it classifies as a "
    "ball-holding toy."
)

SPEC_CABINET_QUOTE = "4 Stereo Speakers [...] Custom Powder Coated Cabinet Armour"
SPEC_CABINET_FEATURES: list[str | dict[str, int]] = [
    {"speakers": 4},
    "stereo-sound",
    "cabinet-armor",
]

# IPDB's Notable Features prose, in row order. The base model additionally
# takes the glare-reduced glass span (editions carry magic-glass instead).
IPDB_QUOTE = (
    "Theater spotlights (2) [...] Game-specific flipper toppers. "
    "Factory mylar in high-wear areas. [...] Playfield has a 4.3 inch LCD."
)
IPDB_FEATURES: list[str | dict[str, int]] = [
    {"theater-spotlights": 2},
    "flipper-toppers",
    "mylar-playfield-protection",
    "playfield-lcds",
]
IPDB_QUOTE_MOM = IPDB_QUOTE + " [...] Glare-reduced playfield glass."
IPDB_FEATURES_MOM = [*IPDB_FEATURES, "anti-reflection-playfield-glass"]

# The flyer's Interactive Game Features column and callouts, transcribed off
# the rendered sheet in reading order (left column, then callouts).
FLYER_QUOTE = (
    "Upper & Lower 3 Ball Staging/Lock Mechanisms [...] "
    "Hidden Ball Subway System [...] RGB Controlled Playfield Inserts [...] "
    "All LED General Illumination"
)
FLYER_FEATURES: list[str | dict[str, int]] = [
    "ball-locks",
    "subways",
    "rgb-playfield-inserts",
    "led-general-illumination",
]


def model_entries(model: str, *, base: bool) -> list[str]:
    """The feature entries every family member gets; editions carry the notes."""
    return [
        pk.entry(
            model,
            cite=cite(SPEC, SPEC_PLAYFIELD_QUOTE),
            relationships={"gameplay_feature": SPEC_PLAYFIELD_FEATURES},
        ),
        pk.entry(
            model,
            note=SPEC_TOYS_NOTE,
            cite=cite(SPEC, SPEC_TOYS_QUOTE),
            relationships={"gameplay_feature": SPEC_TOYS_FEATURES},
        ),
        pk.entry(
            model,
            cite=cite(SPEC, SPEC_CABINET_QUOTE),
            relationships={"gameplay_feature": SPEC_CABINET_FEATURES},
        ),
        pk.entry(
            model,
            note=None if base else VARIANT_NOTE,
            cite=cite(IPDB, IPDB_QUOTE_MOM if base else IPDB_QUOTE),
            relationships={
                "gameplay_feature": IPDB_FEATURES_MOM if base else IPDB_FEATURES
            },
        ),
        pk.entry(
            model,
            note=None if base else FLYER_NOTE,
            cite=flyer_cite(FLYER_QUOTE),
            relationships={"gameplay_feature": FLYER_FEATURES},
        ),
        # Five multiball MODES (the rules list counts modes; the 6-ball
        # complement is stated separately) — see the module docstring.
        pk.entry(
            model,
            cite=cite(SPEC, "5 Multiballs"),
            relationships={"gameplay_feature": [{"multiball": 5}]},
        ),
    ]


def main() -> None:
    entries = [
        # ── Vocabulary ──────────────────────────────────────────────────
        # Mechs and toys, named by the manufacturer's own wording; broadly
        # reusable nodes get the generic name with the AP phrasing as alias.
        # NB: ball-locks is NOT created here — it already exists in the seed
        # vocabulary (the attach below resolves against it). Its "Ball
        # Staging/Lock Mechanisms" alias is a possible future addition; adding
        # facts to an existing vocab entity stays a user call.
        vocab("balls", "Balls", aliases=["Ball Complement"]),
        vocab("subways", "Subways", aliases=["Hidden Ball Subway System", "Ball Subway"]),
        # The toy classification tree (UniqueFeatures.md → Toys corollary),
        # emitted parents-first — creates resolve top-down within a patch.
        # `toys` and `interactive-toys` are grouping nodes, never attached
        # to a model directly; models attach the leaves.
        vocab("toys", "Toys"),
        vocab("static-toys", "Static Toys", parents=["toys"]),
        vocab("interactive-toys", "Interactive Toys", parents=["toys"]),
        vocab(
            "bash-toys",
            "Bash Toys",
            parents=["interactive-toys"],
            aliases=["Robot Bash Toy"],
        ),
        vocab(
            "animatronic-toys",
            "Animatronic Toys",
            parents=["interactive-toys"],
            aliases=["Animatronic Robot Toy"],
        ),
        vocab("pop-up-toys", "Pop-Up Toys", parents=["interactive-toys"]),
        vocab("ball-holding-toys", "Ball-Holding Toys", parents=["interactive-toys"]),
        vocab("bumper-tops", "Bumper Tops", aliases=["Custom Bumper Tops"]),
        vocab(
            "rgb-playfield-inserts",
            "RGB Playfield Inserts",
            aliases=["RGB Controlled Playfield Inserts"],
        ),
        vocab(
            "led-general-illumination",
            "LED General Illumination",
            aliases=["All LED General Illumination"],
        ),
        vocab(
            "cabinet-armor",
            "Cabinet Armor",
            aliases=["Powder Coated Cabinet Armor", "Cabinet Armour"],
        ),
        vocab("playfield-lcds", "Playfield LCDs", aliases=["Playfield LCD"]),
        vocab(
            "mylar-playfield-protection",
            "Mylar Playfield Protection",
            aliases=["Factory Mylar"],
        ),
        # Flipper caps, decorative — NOT the cabinet `toppers` node; the shared
        # word is the false synonym the verbatim policy exists to catch.
        vocab(
            "flipper-toppers",
            "Flipper Toppers",
            aliases=["Custom Laser Cut Flipper Toppers", "Game-Specific Flipper Toppers"],
        ),
        vocab("interior-side-art", "Interior Side Art", parents=["art-blades"]),
        vocab(
            "mirrored-art-blades",
            "Mirrored Art Blades",
            parents=["art-blades", "mirror-blades"],
        ),
        # ── Houdini: Master of Mystery (2017), the base game ────────────
        *model_entries(MOM, base=True),
        # ── Deluxe: the family set plus its own tier ────────────────────
        *model_entries(DELUXE, base=False),
        pk.entry(
            DELUXE,
            cite=cite(
                SPEC,
                "Deluxe Features [...] Interior Side Art [...] Magic Glass",
            ),
            relationships={
                "gameplay_feature": ["interior-side-art", "magic-glass"]
            },
        ),
        # ── 100th Anniversary: the family set plus its own tier ─────────
        *model_entries(ANNIV, base=False),
        pk.entry(
            ANNIV,
            cite=cite(
                ANN,
                "Each game includes a custom topper, Magic Glass, shaker motor, "
                "knocker, and mirrored art blades as standard equipment.",
            ),
            relationships={"gameplay_feature": ["magic-glass", "mirrored-art-blades"]},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Houdini family presentation and mech features",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
