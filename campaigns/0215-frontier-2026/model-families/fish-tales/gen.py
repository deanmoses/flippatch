"""Emit patch 0225 — the Fish Tales family: the 1992 Williams original and
Cardona's 2026 Ultimate Fishing Challenge conversion kit.

See ../../README.md for the family split and FishTales.md beside this file for
the evidence inventory, the catalog baseline, the traps and the decisions this
generator encodes (2026-08-11).

SCOPE IS THE WHOLE FAMILY, two models:
  2026  Fish Tales: Ultimate Fishing Challenge (Kit)  (Cardona Pinball Designs)
  1992  Fish Tales  (Williams, ipdb:861)

Only missing facts are asserted; the baseline table in FishTales.md records
what each model already holds. Deliberately absent (each recorded there):
  kit concept/rules/animation credits      Pinside-only role splits
  kit music/sound person credits           no source names the composer
  Aaron Davis (electronics)                full name is Pinside-only
  cabinet on either model                  no source states it
  descriptions                             campaign scope (no 0216-0223 family wrote them)
  donor hardware facts on the kit          the donor machine supplies them

THE PATH-SCOPED ROOT: Cardona's release-notes PDFs live only on GoDaddy's
shared CDN (img1.wsimg.com), citable via the tenant-path `domains:` entry on
the Cardona root — the first patch to use the mechanism (DataPatches.md →
Citation sources; enabled 2026-08-11).

NO CREDITS CARRY from the 1992 donor to the kit: a conversion kit is neither
a variant nor a remake, and the kit replaces art, code, music, sound and
animation wholesale. The kit-to-donor link is a `conversion_kit` model
relationship, `license_status: licensed`.

AUTO-CAPTION SPELLINGS: the transcripts render the title as "Fishtails";
quotes stay verbatim ASR and notes carry the correction where it matters.

Run: uv run python campaigns/0215-frontier-2026/model-families/fish-tales/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0225-fish-tales.yaml"

# ── Models ──────────────────────────────────────────────────────────────
KIT = "model.fish-tales-ultimate-fishing-challenge-kit"
FT92 = "model.fish-tales"

# ── Sources ─────────────────────────────────────────────────────────────
WSIMG_TENANT = "img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3"
NOTES_JUN = (
    "https://img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3/"
    "downloads/6cdf589b-48c6-4fad-8f56-e481d6474fa6/FT%20release%202026%2006%2012.pdf"
)
NOTES_JUL = (
    "https://img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3/"
    "downloads/ebc2f84f-c8c0-4c41-a7ee-dc72c462c785/FT%20release%202026%2007%2013.pdf"
)
KINETICIST = "https://www.kineticist.com/news/james-cardona-interview"
FAST_ABOUT = "https://fastpinball.com/about"
SKILL_SHOT_FAST = "https://skill-shot.com/venue/fast-pinball-hq/"
CITY_DATA_CARDONA = (
    "https://www.city-data.com/business-entities/NJ/"
    "CARDONA-PINBALL-DESIGNS-LLC-0450585629-NJ.html"
)
VID_ANNOUNCE = "youtube:1p6cpLBQJwk"
VID_OVERVIEW = "youtube:mvRdWatAink"
VID_INSTALL = "youtube:o-XezhzIBvg"
IPDB = "ipdb:861"

NOTES_JUN_P2 = "PDF document page 2 of 2; the sheet carries no printed folio"
NOTES_JUL_P1 = "PDF document page 1 of 2; the sheet carries no printed folio"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


# ── Shared quotes ───────────────────────────────────────────────────────
KIN_RELEASED = (
    "Back in April, James Cardona released Fish Tales: Ultimate Fishing "
    "Challenge, the third kit from his company, Cardona Pinball, with a "
    "fourth still to come."
)
KIN_KIT_CATEGORY = (
    "It's a 2.0 kit, a category of officially licensed products that install "
    "into classic Bally/Williams machines and turns them into a new game "
    "experience, while keeping the original intact."
)
KIN_ROLES = (
    "He writes the code, designs the games, and has brought in more "
    "professional artists and voice actors with each title, while FAST "
    "Pinball handles the hardware."
)
KIN_FAST_PLATFORM = (
    "he wanted all the manufacturers on the same hardware which is why I had "
    "to switch to the FAST platform"
)
ANNOUNCE_LICENSED = (
    "our third title, uh, officially licensed title from, uh, you know, "
    "Williams Planetary Pinball Supply is Fishtails"
)
ANNOUNCE_ASR_NOTE = (
    "The announcement video's auto-captions render the title 'Fishtails'; "
    "the quote is verbatim ASR."
)
NOTES_FIRST_RELEASE = "FT 2026 05 05 First Commercial Release"
IPDB_FEATURES = (
    "Flippers (2), Criss-cross Ramps (2), Rollunder spinner (1), Multiball, "
    "Captive ball, Autoplunger (shaped like a fishing rod), ball-launching "
    "catapult next to the rotary reel lock."
)


def main() -> None:
    sources = [
        # The maker's root, carrying the path-scoped slice of GoDaddy's shared
        # CDN where its documents live (DataPatches.md → Citation sources).
        # Single-family root per RULEBOOK.md → Citation roots.
        pk.source_root(
            "Cardona Pinball Designs",
            description="Manufacturer's own site.",
            domains=[WSIMG_TENANT],
            links=[("https://cardonapinball.com/", "Cardona Pinball", "homepage")],
        ),
        # The platform maker's own site, citing the corporate-entity facts.
        pk.source_root(
            "FAST Pinball",
            description="Pinball control-system maker's own site.",
            links=[("https://fastpinball.com/", "FAST Pinball", "homepage")],
        ),
        pk.source_root(
            "Skill Shot",
            description="Seattle's pinball zine.",
            links=[("https://skill-shot.com/", "Skill Shot", "homepage")],
        ),
        pk.source_root(
            "City-Data.com",
            description="U.S. city statistics and public-records aggregator.",
            links=[("https://www.city-data.com/", "City-Data.com", "homepage")],
        ),
    ]
    entries = [
        # ── Scaffolding: the FAST platform system and the new people ────
        # The platform is shared across 2.0-kit makers (Planetary standardized
        # them on FAST hardware; FAST also supplies Barrels of Fun and Euro
        # Pinball Corp per the announcement video), so the node is not
        # Cardona-specific. A System requires a manufacturer, so FAST Pinball
        # is created as one — it genuinely is the system's maker, though it
        # makes no machines of its own. A computerized platform, so the ss-pc
        # subgeneration follows (the 0220 SPIKE 3 pattern).
        pk.entry(
            "manufacturer.fast-pinball",
            create=True,
            note=(
                "The hardware-platform company behind the licensed 2.0 "
                "conversion-kit ecosystem; it makes boardsets, not machines "
                "of its own."
            ),
            cite=[
                cite(KINETICIST, KIN_ROLES),
                cite(
                    VID_INSTALL,
                    "this [snorts] company, Fast, is not my company. We we "
                    "contract out to get these boards from them. They "
                    "designed them.",
                ),
            ],
            fields={"name": "FAST Pinball"},
        ),
        # Every other manufacturer carries a corporate entity; the legal name
        # is the site footer's. The maker's own pages say only "greater
        # Seattle area" (site and LinkedIn alike); the city comes from Skill
        # Shot's venue listing, corroborated by uncitable-host sources named
        # in the note.
        pk.entry(
            "location.usa/wa/gig-harbor",
            create=True,
            cite=cite(
                SKILL_SHOT_FAST,
                "3226 Harborview Drive, Suite 8 Gig Harbor, WA 98335",
                locator="in the venue listing's Address block",
            ),
            fields={"slug": "gig-harbor", "parent": "usa/wa", "name": "Gig Harbor"},
        ),
        # Cardona's own web presence publishes no address; the New Jersey
        # company registry record (republished by City-Data, surfaced by the
        # user 2026-08-11) places the LLC in Pennsville. The corporate entity
        # already exists (0215), so no create — only the location attaches.
        pk.entry(
            "location.usa/nj/pennsville",
            create=True,
            cite=cite(
                CITY_DATA_CARDONA,
                "CARDONA PINBALL DESIGNS, LLC [...] City: PENNSVILLE",
            ),
            fields={"slug": "pennsville", "parent": "usa/nj", "name": "Pennsville"},
        ),
        pk.entry(
            "corporate-entity.cardona-pinball-designs",
            note=(
                "The New Jersey business registry, republished by City-Data, "
                "registers Cardona Pinball Designs, LLC in Pennsville "
                "(registered 2021-01-06). Consistent with James Cardona's own "
                "author bio placing him in southern New Jersey; Pennsville is "
                "in Salem County in the state's southwest corner. The maker's "
                "own sites publish no address."
            ),
            cite=cite(
                CITY_DATA_CARDONA,
                "CARDONA PINBALL DESIGNS, LLC [...] Entity Id: 0450585629 "
                "[...] Registration date: 2021 Jan 06 [...] City: PENNSVILLE",
            ),
            relationships={"location": ["usa/nj/pennsville"]},
        ),
        pk.entry(
            "corporate-entity.fast-pinball",
            create=True,
            note=(
                "The maker's own site and LinkedIn say only 'greater Seattle "
                "area'; Skill Shot's venue listing places FAST Pinball HQ in "
                "Gig Harbor, and the maker's own Facebook page header ('FAST "
                "Pinball, LLC | Gig Harbor WA') and the Washington company "
                "registry (UBI 603387874, incorporated 2014) agree — both on "
                "hosts the citation system cannot register, so they "
                "corroborate here rather than cite."
            ),
            cite=[
                cite(
                    FAST_ABOUT,
                    "FAST Pinball was founded in 2014 by Aaron Davis and Dave "
                    "Beecher. We're based in the greater Seattle area and "
                    "have sold pinball control systems to customers around "
                    "the world, including individual hobbyists, indie pinball "
                    "designers, and to pinball manufacturing companies who "
                    "build upgrade kits and complete machines.",
                ),
                cite(
                    FAST_ABOUT,
                    "© FAST Pinball LLC",
                    locator="in the site footer's copyright line",
                ),
                cite(
                    SKILL_SHOT_FAST,
                    "FAST Pinball HQ [...] 3226 Harborview Drive, Suite 8 "
                    "Gig Harbor, WA 98335",
                    locator="in the venue listing's Address block",
                ),
            ],
            fields={"name": "FAST Pinball LLC", "manufacturer": "fast-pinball"},
            relationships={"location": ["usa/wa/gig-harbor"]},
        ),
        pk.entry(
            "system.fast-pinball",
            create=True,
            note=(
                "FAST Pinball's boardset platform for licensed 2.0 conversion "
                "kits. Cardona's implementation pairs its CPD CPU with the "
                "FAST controller and FAST sound board, per the July 2026 "
                "release notes' install procedure. The CPU is a PC-class "
                "computer — the kit installation video reads its port panel "
                "sticker naming HDMI video outputs, USB and Ethernet — so the "
                "PC subgeneration follows."
            ),
            cite=[
                cite(KINETICIST, KIN_FAST_PLATFORM),
                cite(
                    NOTES_JUL,
                    "DO NOT plug the USB into any slots on the FAST controller "
                    "or the FAST sound board.",
                    locator=NOTES_JUL_P1,
                ),
                cite(
                    VID_INSTALL,
                    "says HDMI 1, playfield monitor, Ethernet, there's no "
                    "connection. HDMI HDMI 2 speaker panel monitor. You got "
                    "two USB cable connections",
                ),
            ],
            fields={
                "name": "FAST Pinball",
                "manufacturer": "fast-pinball",
                "technology_subgeneration": "ss-pc",
            },
        ),
        pk.entry(
            "person.james-cardona",
            create=True,
            cite=cite(KINETICIST, KIN_RELEASED),
            fields={"name": "James Cardona"},
        ),
        pk.entry(
            "person.jada-holmes",
            create=True,
            cite=cite(
                NOTES_JUN,
                "Added announcer voices from Jada Holmes",
                locator=NOTES_JUN_P2,
            ),
            fields={"name": "Jada Holmes"},
        ),
        # ── 2026: Fish Tales: Ultimate Fishing Challenge (Kit) ──────────
        pk.entry(
            KIT,
            note=(
                "An official, licensed, commercially sold product, so "
                "produced rather than aftermarket (DomainModel.md defines "
                "aftermarket as not an official commercial release)."
            ),
            cite=[
                cite(KINETICIST, KIN_RELEASED),
                cite(NOTES_JUN, NOTES_FIRST_RELEASE, locator=NOTES_JUN_P2),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            KIT,
            note=(
                "The maker's own release history labels 2026-05-05 the First "
                "Commercial Release. Kineticist's 'Back in April' and "
                "Pinside's April date read as the launch-event framing; the "
                "maker's own document wins."
            ),
            cite=cite(NOTES_JUN, NOTES_FIRST_RELEASE, locator=NOTES_JUN_P2),
            fields={"month": 5},
        ),
        pk.entry(
            KIT,
            note=(
                "The kit installs into a pinball machine and its result is a "
                "new pinball game, so the format follows."
            ),
            cite=cite(KINETICIST, KIN_KIT_CATEGORY),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            KIT,
            note=ANNOUNCE_ASR_NOTE
            + " The license is from Williams/Planetary Pinball Supply.",
            cite=[
                cite(KINETICIST, KIN_KIT_CATEGORY),
                cite(VID_ANNOUNCE, ANNOUNCE_LICENSED),
            ],
            model_relationship=[
                {
                    "target_machine": "fish-tales",
                    "relationship_type": "conversion_kit",
                    "license_status": "licensed",
                }
            ],
        ),
        pk.entry(
            KIT,
            note=(
                "Two LCD monitors: a 15-inch main screen in the new speaker "
                "panel and a second 5-inch playfield screen in the Stretch "
                "the Truth location."
            ),
            cite=cite(
                VID_OVERVIEW,
                "It's a 15 inch screen [...] there's a second five inch screen",
            ),
            fields={"display_type": "lcd"},
        ),
        # One changeset: the platform statement supports both fields (the
        # 0220 SPIKE 3 pattern — a computerized platform, so solid-state).
        pk.entry(
            KIT,
            note=(
                "The FAST platform is a computerized game system, so the "
                "solid-state generation follows."
            ),
            cite=cite(KINETICIST, KIN_ROLES),
            fields={
                "technology_generation": "solid-state",
                "system": "fast-pinball",
            },
        ),
        pk.entry(
            KIT,
            note=(
                "Kineticist's own reporting names the roles; Cardona's own "
                "words in the same interview corroborate the code ('I write "
                "code and that has always been easy and enjoyable for me')."
            ),
            cite=cite(KINETICIST, KIN_ROLES),
            credits=[("james-cardona", "design"), ("james-cardona", "software")],
        ),
        pk.entry(
            KIT,
            cite=[
                cite(KINETICIST, "Brian Allen did my artwork"),
                cite(
                    VID_ANNOUNCE,
                    "you have um, brand new artwork um, done by Brian Allen",
                ),
            ],
            credits=[("brian-allen", "art")],
        ),
        pk.entry(
            KIT,
            cite=cite(
                NOTES_JUN,
                "Added announcer voices from Jada Holmes",
                locator=NOTES_JUN_P2,
            ),
            credits=[("jada-holmes", "voice")],
        ),
        pk.entry(
            KIT,
            note=(
                "The June 2026 update added the video mode; MB is the "
                "release notes' own abbreviation for the Caster's Club "
                "multiball."
            ),
            cite=[
                cite(NOTES_JUN, "Added video mode", locator=NOTES_JUN_P2),
                cite(
                    NOTES_JUN,
                    "Fixed various display issues when caster's club MB was "
                    "running",
                    locator=NOTES_JUN_P2,
                ),
            ],
            relationships={"gameplay_feature": ["video-modes", "multiball"]},
        ),
        # ── 1992: Fish Tales (Williams) ─────────────────────────────────
        pk.entry(
            FT92,
            note=(
                "A machine produced in five figures was commercially "
                "produced; IPDB records the exact run as 13,640."
            ),
            cite=[
                cite(KINETICIST, "Fish Tales is a perfect example with over 13,000 made"),
                cite(VID_ANNOUNCE, "they made over 13,000 uh of these machines"),
            ],
            fields={"production_status": "produced"},
        ),
        # One changeset: format and the missing playfield hardware rest on
        # the same Notable Features line. Flippers (2), Multiball and the
        # Rollunder spinner are already claimed by the IPDB actor, so only
        # the missing members attach here.
        pk.entry(
            FT92,
            note=(
                "The fishing-rod-shaped Autoplunger is an auto-launch; the "
                "ball-launching catapult attaches as a catapult; the rotary "
                "reel lock as a ball lock."
            ),
            cite=cite(IPDB, IPDB_FEATURES),
            fields={"game_format": "pinball"},
            relationships={
                "gameplay_feature": [
                    {"ramps": 2},
                    "captive-ball",
                    "auto-launch",
                    "catapults",
                    "ball-locks",
                ]
            },
        ),
        pk.entry(
            FT92,
            note=(
                "Toy classifications: the rotary fishing reel locks balls, so "
                "it is a ball-holding toy; the moving fish topper attaches as "
                "a topper (its motion is a bespoke identity recorded in the "
                "family notes as a future unique feature)."
            ),
            cite=cite(IPDB, "Toys: Rotary fishing reel ball lock, moving fish topper."),
            relationships={"gameplay_feature": ["ball-holding-toys", "toppers"]},
        ),
        pk.entry(
            FT92,
            note=(
                "The four named voices are asserted; the note's 'possibly "
                "others' hedge covers only unnamed people."
            ),
            cite=cite(
                IPDB,
                "voices on this game were provided by Mark Ritchie, Steve "
                "Ritchie, Jim Gentile, Chris Granner, and possibly others",
            ),
            credits=[
                ("mark-ritchie", "voice"),
                ("steve-ritchie", "voice"),
                ("jim-gentile", "voice"),
                ("chris-granner", "voice"),
            ],
        ),
        pk.entry(
            FT92,
            note=(
                "The credit vocabulary has no sculptor role; an earlier "
                "ingest classifies sculpting under art (Jerry Pinsler's "
                "existing Party Zone credit is art), so the topper sculpt "
                "attaches the same way, alongside Pat McMahon's package art "
                "credit."
            ),
            cite=cite(IPDB, "Jerry Pinsler sculpted the fish on the topper."),
            credits=[("jerry-pinsler", "art")],
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Fish Tales family: the Williams original and Cardona's 2026 conversion kit",
        entries=entries,
        sources=sources,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
