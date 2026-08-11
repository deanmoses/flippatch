"""Emit patch 0226 — the Tales of the Arabian Nights family.

See ../../README.md for the family split and ArabianNights.md beside this
file for the evidence inventory, the catalog baseline, the traps and the
decisions this generator encodes (2026-08-11).

SCOPE IS THE WHOLE FAMILY, three models:
  2026  Tales of the Arabian Nights — 30th Anniversary Remake / Legacy Edition Remake (Pedretti)
  1996  Tales of the Arabian Nights (Williams, ipdb:3824)

Only missing facts are asserted; the baseline in ArabianNights.md records
what each model already holds (the 1996 original is richly IPDB/OPDB-seeded;
the remakes hold only 0215's name/theme/title/year). Deliberately absent
(each recorded there under "Not asserted"):
  Legacy production_quantity      "Initial production run only" — a first-run size, not a cap
  system on the remakes           FAST is the vendor; no platform product named; Funhouse precedent
  Scorbit / Wi-Fi connectivity    service integrations, not modeled (Bon Jovi precedent)
  month on the remakes            announced, not released (CV remake precedent)
  Athyrio software credit         a company, not a person
  themes                          all three already set

USER DECISIONS (2026-08-11, recorded in ArabianNights.md → Decisions):
  location     corporate-entity.pedretti-gaming corrected Podenzano → Bagnatica
  lineage      both editions remake_of the 1996 original; 30th variant_of Legacy
               (the seed's Pedretti Funhouse remake shape)
  GameSync     one brand leaf under interactive-lighting (the aura-lighting pattern)
  glass        invisible-magic-glass as its own brand child of
               anti-reflection-playfield-glass (possible identity with
               magic-glass recorded in the family notes, not asserted)

THE REMAKE CREDIT RULE (user decision 2026-08-10): creative credits carry
from the original, cited to the original's evidence; mechanics and software
do not. The art credit carries ONLY to the Legacy Edition (it keeps the 1996
artwork package); the 30th Anniversary's art is new (Brian Allen).

Run: uv run python campaigns/0215-frontier-2026/model-families/arabian-nights/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0226-arabian-nights.yaml"

# ── Models ──────────────────────────────────────────────────────────────
M96 = "model.tales-of-the-arabian-nights"
M_LEG = "model.tales-of-the-arabian-nights-legacy-edition-remake"
M_30 = "model.tales-of-the-arabian-nights-30th-anniversary-remake"

# ── Sources ─────────────────────────────────────────────────────────────
# Pedretti's own site is pinballremakes.com (pedrettigaming.it redirects
# there; pedrettigaming.com is dead with an empty Wayback CDX). The Pedretti
# Gaming citation root already covers it — no root work in this patch.
PN = (
    "https://www.pinballnews.com/site/2026/06/15/"
    "tales-of-the-arabian-nights-remake-revealed"
)
HOME = "https://www.pinballremakes.com/"
LEG = (
    "https://www.pinballremakes.com/prodotto/"
    "acconto-preordine-tales-of-the-arabian-nights-legacy-edition"
)
TH30 = (
    "https://www.pinballremakes.com/prodotto/"
    "deposit-preorder-europe-only-tales-of-the-arabian-nights-30th-anniversary-edition"
)
PPS_AE = (
    "https://www.planetarypinball.com/mm5/merchant.mvc"
    "?Product_Code=PPS-TOTAN-AE-DEPOSIT&Screen=PROD"
)
PPS_LE = (
    "https://www.planetarypinball.com/mm5/merchant.mvc"
    "?Product_Code=PPS-TOTAN-LE-DEPOSIT&Screen=PROD"
)
KIN = "https://www.kineticist.com/news/totan-remake-launch"
IPDB = "ipdb:3824"

PN_LOC = "in the manufacturer's press release reprinted verbatim in the article"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


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


# ── Shared quotes ───────────────────────────────────────────────────────
PN_REMAKE = (
    "Inspired by the legendary and mesmerizing 1996 original, this remake "
    "combines the magical gameplay of the classic machine with updated "
    "technology, immersive atmospheric lighting, enhanced visual effects, "
    "and modern features to create an unforgettable pinball experience for "
    "players and collectors alike. [...] Tales of the Arabian Nights Remake "
    "will be available in two different models: Legacy Edition and 30th "
    "Anniversary Edition."
)
PN_PINBALL = (
    "proudly announces its newest pinball machine: "
    "Tales of the Arabian Nights Remake."
)
PN_DISTRIBUTOR = (
    "Please contact your authorized distributor for availability and to "
    "secure your game allocation."
)
PN_399_ART = (
    "Strictly limited to only 399 units worldwide, the 30th Anniversary "
    "Edition features a completely reimagined hand-drawn art package "
    "created by renowned pinball artist Brian Allen and Flyland Designs."
)
PN_LEGACY_ART = (
    "The Legacy Edition features the original artwork package from the "
    "1996 game along with custom-painted metallic trims."
)
PN_BOTH_MODELS = (
    "Both models include all of the newly developed features created "
    "specifically for this project."
)

IPDB_CREDITS_ALL = (
    "Design by: John Popadiuk [...] Art by: Pat McMahon [...] "
    "Dots/Animation by: Adam Rhine, Brian Morris [...] "
    "Music by: Dave Zabriskie [...] Sound by: Dave Zabriskie"
)
IPDB_CREDITS_NO_ART = (
    "Design by: John Popadiuk [...] "
    "Dots/Animation by: Adam Rhine, Brian Morris [...] "
    "Music by: Dave Zabriskie [...] Sound by: Dave Zabriskie"
)
IPDB_FEATURES = (
    "Flippers (2), Pop bumpers (3), Slingshots (2), Electromagnets (3), "
    "Spinning posts (2), Captive balls (2), Newton ball posts (2), "
    "Kick-out hole (1), 2- 3- and 4-ball multiball, Shooter lane skill shot."
)
IPDB_TOYS = "Toys: Lamp on top of spinning posts. Genie bash toy."

CARRIED_CREDITS = [
    ("john-popadiuk", "design"),
    ("adam-rhine", "animation"),
    ("brian-morris", "animation"),
    ("dave-zabriskie", "music"),
    ("dave-zabriskie", "sound"),
]

REMAKE_NOTE = (
    "A remake preserves the original's creative work, so the original's "
    "creative credits - design, art, animation, music, sound - carry to the "
    "remake, as with Medieval Madness and its Chicago Gaming remake. The "
    "maker frames the remake as preserving the classic machine's gameplay. "
    "Mechanics and software credits do not carry: the remake is re-engineered."
)
ART_CARRIES_NOTE = (
    " The art credit carries to this edition because it retains the "
    "original 1996 artwork package."
)
ART_REPLACED_NOTE = (
    " The art credit does not carry to this edition: its art package is "
    "new (Brian Allen)."
)
TOYS_NOTE = (
    "IPDB names the Genie a bash toy; the Lamp atop the spinning posts "
    "states no motion or ball interaction of its own, so it classifies as "
    "a static toy."
)
ANNOUNCED_NOTE = (
    "The maker and its partners sell pre-order deposits only, with the "
    "balance due before delivery and no machine yet shipping, so the "
    "machine is announced, not produced."
)
LCD_NOTE = (
    "The press release's 'New DMD display animations' describes the "
    "animation content of the enhanced code; the maker's product page "
    "states the hardware is a 21.5-inch HD LCD."
)
DECOR_NOTE = (
    "PPS's wording, 'Infinite mirror side blades', names the playfield "
    "side blades the maker's page calls Side Rails, so mirror-blades "
    "attaches. The edition's trim name and the Glowing Stars Ramp LEDs are "
    "model-specific presentation identities, recorded in the family notes."
)
GAMESYNC_NOTE = (
    "GameSync Lighting is Pedretti's brand of interactive lighting, here "
    "on the speakers and sidebars. The upgraded Lamp and Genie toys are "
    "the original 1996 machine's toys, retained by the remake: " + TOYS_NOTE
)

LEG_LCD = (
    "The machine features a large 21.5” HD LCD display, bringing the "
    "world of the Arabian Nights to life with upgraded video animations "
    "and a more dynamic visual presentation."
)
LEG_DECOR = (
    "The cabinet is enhanced with special “Night Sky” metal armor "
    "trims, Invisible Magic Glass, Infinite Mirror Side Rails, Glowing "
    "Stars Ramp LEDs, and a Playfield Lighted Backpanel, adding depth, "
    "elegance, and modern visual presence without losing the iconic look "
    "of the original game."
)
LEG_GAMESYNC = (
    "The Premium Sound System, combined with GameSync Lighting™ RGB "
    "speakers and GameSync Lighting™ RGB sidebars, creates a more "
    "powerful and engaging atmosphere. The machine also includes a shaker "
    "motor, upgraded Lamp and Genie toys, the Glitter Gold Lamp, Scorbit "
    "integration, and online software updates, allowing the game to remain "
    "current over time."
)
DEPOSIT_SPAN = "This payment is required to pre-order the pinball machine."

TH30_LIKE_LEGACY = (
    "Like the Legacy Edition, the 30th Anniversary Edition features the "
    "21.5” HD LCD display, the original game code, and the enhanced "
    "1.5+ game code, combining classic gameplay with expanded modern "
    "features."
)
TH30_DECOR = (
    "The cabinet is further enhanced with special “Purple Glitter” "
    "metal armor trims, giving the game a distinctive and luxurious "
    "appearance. Combined with the Invisible Magic Glass, Infinite Mirror "
    "Side Rails, Glowing Stars Ramp LEDs, Playfield Lighted Backpanel, and "
    "Glitter Gold Lamp, the result is a machine with a bold, elegant, and "
    "unmistakably magical presence."
)
TH30_GAMESYNC = (
    "The 30th Anniversary Edition also includes the Premium Sound System, "
    "GameSync Lighting™ RGB speakers, GameSync Lighting™ RGB "
    "sidebars, Backbox GameSync Lighting, shaker motor, upgraded Lamp and "
    "Genie toys, Scorbit integration, and online software updates."
)
TH30_PLAQUE = (
    "To complete its collector status, the 30th Anniversary Edition "
    "includes a limited certificate and metal plaque, making each machine "
    "part of a special commemorative production."
)

PPS_BLADES = "Infinite mirror side blades"
PPS_NO_SECOND_RUN = "399 units worldwide. No second run planned."
PPS_PLAQUE = "Numbered limited certificate + metal plaque"
PPS_ALLEN = "Reimagined artwork by Brian Allen / Flyland Designs"

DECOR_FEATURES: list[str | dict[str, int]] = [
    "cabinet-armor",
    "invisible-magic-glass",
    "mirror-blades",
    "lighted-backpanels",
]
GAMESYNC_FEATURES: list[str | dict[str, int]] = [
    "gamesync-lighting",
    "shaker-motors",
    "bash-toys",
    "static-toys",
]


def remake_shared(model: str, deposit_page: str) -> list[str]:
    """The entries both 2026 editions get."""
    return [
        pk.entry(
            model,
            cite=cite(PN, PN_REMAKE, locator=PN_LOC),
            fields={"remake_of": "tales-of-the-arabian-nights"},
        ),
        pk.entry(
            model,
            note=ANNOUNCED_NOTE,
            cite=[
                cite(PN, PN_DISTRIBUTOR, locator=PN_LOC),
                cite(deposit_page, DEPOSIT_SPAN),
            ],
            fields={"production_status": "announced"},
        ),
        pk.entry(
            model,
            cite=cite(PN, PN_PINBALL, locator=PN_LOC),
            fields={"game_format": "pinball"},
        ),
    ]


def main() -> None:
    entries = [
        # ── Vocabulary (user-ruled 2026-08-11) ──────────────────────────
        # Pedretti's interactive-lighting brand as a single leaf, the JJP
        # aura-lighting shape — not the 0220 Expression DAG; the locations
        # (speakers, sidebars, backbox) live in the attach notes.
        vocab(
            "gamesync-lighting",
            "GameSync Lighting",
            parents=["interactive-lighting"],
            aliases=["GameSync"],
        ),
        # Pedretti's anti-reflection glass brand (the InvisiGlass pattern).
        # Possibly the same product as magic-glass (0223); kept separate
        # rather than risk a wrong conflation — see ArabianNights.md.
        vocab(
            "invisible-magic-glass",
            "Invisible Magic Glass",
            parents=["anti-reflection-playfield-glass"],
        ),
        # Generic: an illuminated panel at the back of the playfield.
        vocab(
            "lighted-backpanels",
            "Lighted Backpanels",
            aliases=["Playfield Lighted Backpanel", "Illuminated Playfield Back Panel"],
        ),
        # ── Corporate entity: the location correction (user-approved) ───
        pk.entry(
            "corporate-entity.pedretti-gaming",
            note=(
                "An earlier ingest's Podenzano (PC) survives only in "
                "third-party dealer copy, possibly describing the parent "
                "Pedretti Group. The maker's own site footer gives the Bagnatica "
                "street address and a Bergamo company-registry number "
                "(REA: BG 445013), and its June 2026 press release is "
                "datelined Bagnatica, so the coarser claim is removed and "
                "Bagnatica asserted."
            ),
            cite=[
                cite(
                    HOME,
                    "Via Martin Luther King, 3 24060 - Bagnatica (BG) Italy "
                    "[...] REA: BG 445013",
                    locator="in the site footer's Contacts block and copyright line",
                ),
                cite(
                    PN,
                    "Bagnatica, Italy – June 15, 2026 – Pedretti "
                    "Gaming (Pedretti), in partnership with Planetary "
                    "Pinball Supply Inc.",
                    locator=PN_LOC,
                ),
            ],
            relationships={"location": ["italy/bg/bagnatica"]},
            remove={"location": ["italy/pc/podenzano"]},
        ),
        # ── 1996: Tales of the Arabian Nights (Williams) ────────────────
        pk.entry(
            M96,
            cite=cite(
                KIN,
                "The original Tales of the Arabian Nights shipped from "
                "Williams in 1996, designed by John Popadiuk",
            ),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            M96,
            cite=cite(IPDB, IPDB_FEATURES),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            M96,
            note=TOYS_NOTE,
            cite=cite(IPDB, IPDB_TOYS),
            relationships={"gameplay_feature": ["bash-toys", "static-toys"]},
        ),
        # ── 2026: Legacy Edition Remake (the base edition) ──────────────
        *remake_shared(M_LEG, LEG),
        pk.entry(
            M_LEG,
            note=LCD_NOTE,
            cite=cite(LEG, LEG_LCD),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            M_LEG,
            note=REMAKE_NOTE + ART_CARRIES_NOTE,
            cite=[
                cite(IPDB, IPDB_CREDITS_ALL),
                cite(PN, PN_LEGACY_ART, locator=PN_LOC),
            ],
            credits=[*CARRIED_CREDITS, ("pat-mcmahon", "art")],
        ),
        pk.entry(
            M_LEG,
            note=DECOR_NOTE,
            cite=[
                cite(LEG, LEG_DECOR),
                cite(PPS_LE, PPS_BLADES, locator="in the Every Legacy Edition Includes list"),
            ],
            relationships={"gameplay_feature": DECOR_FEATURES},
        ),
        pk.entry(
            M_LEG,
            note=GAMESYNC_NOTE,
            cite=[
                cite(LEG, LEG_GAMESYNC),
                cite(IPDB, IPDB_TOYS),
            ],
            relationships={"gameplay_feature": GAMESYNC_FEATURES},
        ),
        # ── 2026: 30th Anniversary Remake ───────────────────────────────
        *remake_shared(M_30, TH30),
        pk.entry(
            M_30,
            note=(
                "An edition is a variant of its base, and the Legacy "
                "Edition is the base: Pedretti's own Funhouse "
                "remakes take this shape (the Limited Edition is a variant "
                "of the Collector's Edition), the pricier strictly-limited "
                "edition pointing at the standard one. The maker describes "
                "this edition relative to the Legacy Edition and states "
                "both models share the newly developed feature set."
            ),
            cite=[
                cite(TH30, TH30_LIKE_LEGACY),
                cite(PN, PN_BOTH_MODELS, locator=PN_LOC),
            ],
            fields={
                "variant_of": "tales-of-the-arabian-nights-legacy-edition-remake"
            },
        ),
        pk.entry(
            M_30,
            note=LCD_NOTE,
            cite=cite(TH30, TH30_LIKE_LEGACY),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            M_30,
            cite=[
                cite(PN, PN_399_ART, locator=PN_LOC),
                cite(PPS_AE, PPS_NO_SECOND_RUN, locator="in the Shipping & Support section"),
            ],
            fields={"production_quantity": 399},
            tags=["limited-edition"],
        ),
        pk.entry(
            M_30,
            note=REMAKE_NOTE + ART_REPLACED_NOTE,
            cite=cite(IPDB, IPDB_CREDITS_NO_ART),
            credits=CARRIED_CREDITS,
        ),
        pk.entry(
            M_30,
            note=(
                "Flyland Designs is Brian Allen's studio, so the person "
                "credit is Brian Allen, who also created the Cirqus "
                "Voltaire remake's Ringmaster Edition art package."
            ),
            cite=[
                cite(PN, PN_399_ART, locator=PN_LOC),
                cite(
                    PPS_AE,
                    PPS_ALLEN,
                    locator="in the What Makes the Anniversary Edition Different list",
                ),
            ],
            credits=[("brian-allen", "art")],
        ),
        pk.entry(
            M_30,
            note=DECOR_NOTE,
            cite=[
                cite(TH30, TH30_DECOR),
                cite(
                    PPS_AE,
                    PPS_BLADES,
                    locator="in the Every Anniversary Edition Includes list",
                ),
            ],
            relationships={"gameplay_feature": DECOR_FEATURES},
        ),
        pk.entry(
            M_30,
            note=(
                "GameSync Lighting is Pedretti's brand of interactive "
                "lighting, here on the speakers, sidebars and backbox. The "
                "upgraded Lamp and Genie toys are the original 1996 "
                "machine's toys, retained by the remake: " + TOYS_NOTE
            ),
            cite=[
                cite(TH30, TH30_GAMESYNC),
                cite(IPDB, IPDB_TOYS),
            ],
            relationships={"gameplay_feature": GAMESYNC_FEATURES},
        ),
        pk.entry(
            M_30,
            cite=[
                cite(TH30, TH30_PLAQUE),
                cite(
                    PPS_AE,
                    PPS_PLAQUE,
                    locator="in the What Makes the Anniversary Edition Different list",
                ),
            ],
            relationships={"gameplay_feature": ["numbered-plaques"]},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description=(
            "Tales of the Arabian Nights: 1996 original + 2026 Pedretti remakes"
        ),
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
