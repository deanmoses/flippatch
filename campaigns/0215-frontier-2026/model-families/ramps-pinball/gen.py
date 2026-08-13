"""Emit patch 0233 — the Ramp's Pinball family: Road Trip, Monster League Hockey,
Little Shop of Horrors — plus 0235, the opdb-attributed Road Trip month retract.

See RampsPinball.md beside this file for the evidence inventory, the catalog
baseline, the traps, and the rulings this generator encodes (2026-08-13).

SCOPE IS THE WHOLE FAMILY, three models, none with an IPDB row and no maker
PDFs at all — the maker publishes four thin site pages. The evidence is
journalism (Knapp Arcade's dead posts recovered via Wayback, Arcade Heroes),
the creators' own words on camera (YouTube ASR transcripts — quotes are
verbatim ASR, misheard names included), Jake Danzig's own Pinside build
thread (first-party for a homebrew), and one USPTO trademark record.

Only missing facts are asserted; already-present (duplicate-scanned against
model_claims 2026-08-13): Road Trip designer credit (Bob Nies), cabinet,
display, player_count, themes, tags [limited-edition, widebody], year 2026;
MLH themes; the corporate entity's TiltBob aliases and Bob Nies's "Bob Neis"
person alias — all pre-existing, none re-asserted.

THE MONTH FIX (user-approved 2026-08-13): "February 2026" is a chimera —
month 2 rode in from OPDB's Feb-2025 world-debut dating, the year was later
corrected to 2026 without touching the month; the maker says only "Expected
Late 2026". Retract drops only the patch's own source's claim, and BOTH
flipcommons-catalog and opdb hold month=2, so 0233 retracts the catalog's
and 0235 (attribution: opdb — the DataPatches.md retract example's own
pattern) retracts OPDB's. OPDB's outranked year-2025 claim stays.

THE MLH DESIGN-VS-HARDWARE LINE (RampsPinball.md → Rulings): the catalog
model is the announced Ramp's production machine; most evidence describes
the homebrew prototype. Design-level facts carry (format, head-to-head,
player support, flipper/LCD counts, credits) with notes naming the prototype
basis; prototype hardware internals (the FAST control system) do not.

Run: uv run python campaigns/0215-frontier-2026/model-families/ramps-pinball/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0233-ramps-pinball.yaml"
OUT_OPDB = (
    Path(__file__).resolve().parents[4] / "patches" / "0235-road-trip-month-opdb-retract.yaml"
)

# ── Models ──────────────────────────────────────────────────────────────
RT = "model.road-trip"
MLH = "model.monster-league-hockey"
LSOH = "model.little-shop-of-horrors"

# ── Sources ─────────────────────────────────────────────────────────────
# Knapp Arcade's old Wix blog is dead (the site relaunched as a different
# product on knapparcade.com); every post cites its original URL with the
# Wayback id_ snapshot as archive.
KNAPP_REVEAL = (
    "https://www.knapparcade.org/post/"
    "exclusive-new-company-ramps-pinball-manufacturing-to-reveal-first-game-road-trip-this-week-at-p"
)
KNAPP_REVEAL_AR = "http://web.archive.org/web/20250215191243id_/" + KNAPP_REVEAL
KNAPP_SNEAK = (
    "https://www.knapparcade.org/post/"
    "exclusive-sneak-peek-at-tiltbob-pinball-s-upcoming-new-pinball-machine-road-trip"
)
KNAPP_SNEAK_AR = "http://web.archive.org/web/20231004150126id_/" + KNAPP_SNEAK
KNAPP_LSOH = (
    "https://www.knapparcade.org/post/a-little-shop-of-horrors-pinball-machine-is-in-the-works"
)
KNAPP_LSOH_AR = "http://web.archive.org/web/20240223102257id_/" + KNAPP_LSOH

AH = (
    "https://arcadeheroes.com/2026/03/22/"
    "newsbytes-resident-evil-2-arcade-texas-pinball-festival-konami-more"
)
PN_TPF26 = "https://www.pinballnews.com/site/2026/03/21/texas-pinball-festival-2026"
BASH = "https://www.bashpinball.com/2025/11/14/s2-expointerviews"
PINSIDE_MLH_1 = "https://pinside.com/pinball/forum/topic/monster-league-hockey"
PINSIDE_MLH_2 = "https://pinside.com/pinball/forum/topic/monster-league-hockey/page/2"

# Videos (cached caption transcripts; quotes are verbatim ASR)
V_TAMPA_CREDITS = "youtube:VRnWFKFr-bQ"  # TampaTech: Paul Fusco names the Road Trip team
V_TAMPA_LAUNCH = "youtube:NK3EhukuXcY"  # TampaTech at Pinball at the Beach
V_LOSERKID = "youtube:JdajgyTpvKk"  # Loser Kid Pinball Podcast: Jake Danzig interview
V_EXPO = "youtube:2U3aIFxkeKA"  # MLH crew interviews at Pinball Expo 2025

TM_MLH = "uspto:monster-league-hockey-trademark-application-2025"
TM_MLH_PAGE = "https://uspto.report/TM/99129999"

ASR = "the quote is verbatim ASR from the video's caption track"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def knapp(ref: str, archive: str, quote: str) -> dict[str, str]:
    return {"ref": ref, "archive": archive, "quote": quote}


def main() -> None:
    sources = [
        # Single-family journalism roots (Cardona precedent — RULEBOOK.md →
        # Citation roots). Knapp Arcade broke every Ramp's story 2023-2025;
        # BASH Pinball's episode page is the cleanest text naming MLH's artist.
        pk.source_root(
            "Knapp Arcade",
            description=(
                "Jason Knapp's arcade and pinball news blog. Its 2021-2025 Wix-era "
                "posts (knapparcade.org) are dead since the site relaunched as a "
                "community product; cites carry Wayback snapshots."
            ),
            links=[("https://www.knapparcade.org/", "Knapp Arcade", "homepage")],
        ),
        pk.source_root(
            "BASH Pinball",
            description="The BASH Pinball podcast's episode pages.",
            links=[("https://www.bashpinball.com/", "BASH Pinball", "homepage")],
        ),
        # The USPTO trademark record for MLH, declared under the 0227 uspto
        # publisher root. The captured copy is the USPTO.report republication;
        # the library capture carries this ref as its citation_ref.
        pk.source_child(
            "Monster League Hockey Trademark Application (April 2025)",
            parent="uspto",
            slug="monster-league-hockey-trademark-application-2025",
            year=2025,
            month=4,
            day=10,
            description=(
                "USPTO trademark application 99129999, MONSTER LEAGUE HOCKEY, "
                "standard character mark for pinball machines; filed 2025-04-10 "
                "as intent-to-use by Jake Danzig (individual, Maricopa, Arizona)."
            ),
            links=[
                (
                    "https://tsdr.uspto.gov/#caseNumber=99129999&caseType=SERIAL_NO&searchType=statusSearch",
                    "USPTO TSDR status record",
                    "reference",
                ),
                (TM_MLH_PAGE, "USPTO.report record", "catalog"),
            ],
        ),
    ]

    # People created by this patch; each credit below carries its own cite.
    people = [
        pk.entry("person.jake-danzig", create=True, fields={"name": "Jake Danzig"}),
        pk.entry("person.brad-albright", create=True, fields={"name": "Brad Albright"}),
        pk.entry("person.austin-carrigan", create=True, fields={"name": "Austin Carrigan"}),
        pk.entry("person.glenn-waechter", create=True, fields={"name": "Glenn Waechter"}),
        pk.entry("person.joe-farnsworth", create=True, fields={"name": "Joe Farnsworth"}),
        pk.entry(
            "person.antoinette-johnson", create=True, fields={"name": "Antoinette Johnson"}
        ),
        pk.entry("person.paul-fusco", create=True, fields={"name": "Paul Fusco"}),
    ]

    road_trip = [
        # The maker states no month, only "Expected Late 2026"; the catalog's
        # month claim is the OPDB Feb-2025 debut month left behind when the
        # year was corrected. 0234 drops OPDB's copy of the same claim.
        pk.entry(
            RT,
            retract=["month"],
            note=(
                "The resolved 'February 2026' is a chimera: month 2 is OPDB's "
                "dating of the February 2025 world debut at Pinball at the Beach, "
                "kept when the year was later corrected to 2026. The maker's only "
                "release statement is 'Expected Late 2026' (rampspinball.com, "
                "fetched 2026-08-13), so no month is assertable. A companion "
                "opdb-attributed patch retracts OPDB's copy of the same claim."
            ),
        ),
        pk.entry(
            RT,
            cite=knapp(
                KNAPP_REVEAL,
                KNAPP_REVEAL_AR,
                "Road Trip production is limited to 500 units.",
            ),
            fields={"production_quantity": "500"},
        ),
        pk.entry(
            RT,
            cite=knapp(
                KNAPP_REVEAL,
                KNAPP_REVEAL_AR,
                "the World debut of the brand new pinball machine Road Trip by "
                "Ramp's Pinball Manufacturing",
            ),
            fields={"game_format": "pinball"},
        ),
        # The reveal post's feature list, quoted in source order. Mapping notes:
        # Invisaglass (the post's spelling) attaches the InvisiGlass brand node;
        # the "Cow Tippin'" bash targets attach the generic targets leaf; the
        # Dynamic Playfield's rotating mechanism is a unique-feature identity
        # (RampsPinball.md → Future unique features), not vocabulary.
        pk.entry(
            RT,
            note=(
                "The 'Cow Tippin'' bash targets attach the generic targets leaf "
                "(Knapp's text says bash targets, not drop targets); the Dynamic "
                "Playfield's rotating pop bumper/ramp mechanism is a one-off "
                "identity recorded in the family notes for future one-off-feature "
                "cataloguing, so only its constituent generics attach here."
            ),
            cite=knapp(
                KNAPP_REVEAL,
                KNAPP_REVEAL_AR,
                "A Dynamic Playfield where players hit a target to change the "
                "physical game flow. [...] A Drain-Save pop up VUK [...] "
                "4 Flippers [...] Multiple Ramps [...] 4 Pop Bumpers [...] "
                "A Car Bash Toy [...] 3 “Cow Tippin’ Bash Targets [...] "
                "2 Mechanical Ball Locks [...] Playfield Screen that acts as "
                "Navigation and a Car Radio [...] Invisaglass [...] Knocker "
                "[...] Shaker Motor",
            ),
            relationships={
                "gameplay_feature": [
                    "vertical-up-kickers",
                    {"flippers": 4},
                    "ramps",
                    {"pop-bumpers": 4},
                    "bash-toys",
                    "targets",
                    {"ball-locks": 2},
                    "playfield-lcds",
                    "invisiglass",
                    "knockers",
                    "shaker-motors",
                ]
            },
        ),
        pk.entry(
            RT,
            cite=knapp(
                KNAPP_SNEAK,
                KNAPP_SNEAK_AR,
                "It has an old-school physical ball kickback.",
            ),
            relationships={"gameplay_feature": ["kickback"]},
        ),
        pk.entry(
            RT,
            note=(
                "TampaTech is team member Paul Fusco's channel (Knapp Arcade's "
                "company-reveal post names 'Paul Fusco of the TampaTech YouTube "
                "channel' on the TiltBob team); "
                + ASR
                + " — 'Clippers' is the track's rendering of flippers."
            ),
            cite=cite(
                V_TAMPA_LAUNCH,
                "four Clippers magnets as invisiglass car bash toy rotating raccoon",
            ),
            relationships={"gameplay_feature": ["magnets"]},
        ),
        # Credits. Bob Nies's design credit already exists (0215-era); the new
        # facts are his software credit and Fusco's rules design, both stated
        # by Fusco on his own channel. Art is NOT asserted: Bob credits "my
        # daughter and Joe, which is my partner" on camera, and neither full
        # name appears in any text source (RampsPinball.md → Sought and not
        # found).
        pk.entry(
            RT,
            note=(
                "Spoken by Paul Fusco on his own TampaTech channel; Knapp "
                "Arcade's company-reveal post places Fusco on the team. 'I did "
                "the rules' is credited as design (rules design; no closer "
                "role exists) and 'Bob is doing the code' as software — Bob "
                "Nies's design credit is already recorded. "
                + ASR
            ),
            cite=cite(
                V_TAMPA_CREDITS,
                "Joe did the art and I did the rules and Bob is doing the code "
                "and he actually did the pinball design the layout",
            ),
            credits=[("bob-nies", "software"), ("paul-fusco", "design")],
        ),
    ]

    mlh = [
        # Status and year: Arcade Heroes' TPF 2026 Newsbytes carries the only
        # public statement that Ramp's is the manufacturer; Jake Danzig's own
        # build-thread post (May 2026) dates the release year. A homebrew
        # builder's own thread is first-party (RULEBOOK.md → sources).
        pk.entry(
            MLH,
            note=(
                "The manufacturer deal was unannounced for months (the January "
                "2026 Loser Kid interview says only 'we have made a deal'); "
                "Arcade Heroes' Texas Pinball Festival coverage is the public "
                "statement naming Ramp's, with production targeted at Q4 2026. "
                "The year rests on that target plus Jake Danzig's May 2026 post "
                "in his own build thread."
            ),
            cite=[
                cite(
                    AH,
                    "It is now set to enter actual production thanks to Ramp’s "
                    "Pinball, a new entrant out of Florida who are also working on "
                    "their own upcoming game Road Trip, with a view to building "
                    "both by Q4 2026.",
                ),
                cite(
                    PINSIDE_MLH_2,
                    "the games are still coming out this year",
                    locator="post #93 by Danzig, the game's creator",
                ),
            ],
            fields={"production_status": "announced", "year": "2026"},
        ),
        pk.entry(
            MLH,
            note=(
                "The trademark record's goods classification states the product "
                "category; the captured copy is USPTO.report's republication of "
                "the USPTO TSDR record."
            ),
            cite={
                "ref": TM_MLH,
                "locator": "the Mark For line of the record",
                "quote": (
                    "MONSTER LEAGUE HOCKEY™ trademark registration is intended "
                    "to cover the categories of pinball machines; Pinball machines."
                ),
            },
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            MLH,
            note=(
                "Arcade Heroes states the production machine's player support; "
                "4 is the supported maximum (one or two players, three or four "
                "with split flippers)."
            ),
            cite=cite(
                AH,
                "Completed by Danzig with his Killdozer Studios team, this is "
                "being made to support both one or two players (three or four "
                "with split flippers)",
            ),
            fields={"player_count": "4"},
        ),
        # Display and flipper count: stated by the crew at Pinball Expo 2025
        # about the machine as designed. The prototype basis is in the note;
        # the FAST control system is deliberately NOT asserted
        # (RampsPinball.md → Rulings: design facts carry to the announced
        # production machine, prototype hardware internals do not).
        pk.entry(
            MLH,
            note=(
                "Stated by the build crew at the machine's Pinball Expo 2025 "
                "debut (the homebrew the announced production machine is built "
                "from); six screens at a 1:1 flipper-to-LCD ratio — two large "
                "and four small — are the game's design. "
                + ASR
            ),
            cite=cite(V_EXPO, "We got six flippers, six LCD screens."),
            fields={"display_type": "lcd"},
            relationships={"gameplay_feature": [{"flippers": 6}, "playfield-lcds"]},
        ),
        pk.entry(
            MLH,
            note=(
                "Head-to-head is the game's defining format (two facing "
                "players, simultaneous play); multiball is the designed ball "
                "count (the game starts with two balls in play); the drop "
                "targets and spinner drive the power-play and fight-mode "
                "rules. Video quotes are verbatim ASR."
            ),
            cite=[
                cite(AH, "Homebrew head-to-head pinball piece Monster League Hockey"),
                cite(
                    V_LOSERKID,
                    "I also wanted to make it multiball and I always wanted to "
                    "start the game off with two balls in play",
                ),
                cite(
                    V_EXPO,
                    "You got these drop targets. You clear them three times and "
                    "it starts a power play.",
                ),
                cite(
                    V_EXPO,
                    "if you complete enough spins in the bash spinner, it'll "
                    "fill up your monster meter.",
                ),
            ],
            relationships={
                "gameplay_feature": [
                    "head-to-head",
                    "multiball",
                    "drop-targets",
                    "spinners",
                ]
            },
        ),
        # Credits, one entry per source. Every crew surname is garbled by the
        # caption tracks, so each note records the corroborating spelling
        # source (GTF precedent: cross-reference the reading, record the aid).
        pk.entry(
            MLH,
            cite=cite(AH, "its creator, Jake Danzig"),
            credits=[("jake-danzig", "design")],
        ),
        pk.entry(
            MLH,
            note=(
                "BASH Pinball's episode page for its Expo 2025 crew interviews "
                "names the artist in clean text; Pinball News's TPF 2026 "
                "captions corroborate the spelling (the caption tracks render "
                "it 'Albbright')."
            ),
            cite=cite(BASH, "Brad Albright, artist on MLH as well as Winchester Mystery House and Portal."),
            credits=[("brad-albright", "art")],
        ),
        pk.entry(
            MLH,
            note=(
                "Speaker identified in the interview sequence as Austin, the "
                "game's coder; the caption track renders the surname 'Carrian'. "
                "Spelling per Kineticist's Pinball Expo 2024 coverage of SAW "
                "('Whipped up by Austin Carrigan'), the same crew's previous "
                "homebrew. "
                + ASR
            ),
            cite=cite(V_EXPO, "I did the coding for the game."),
            credits=[("austin-carrigan", "software")],
        ),
        pk.entry(
            MLH,
            note=(
                "Glenn did all audio and composed the production music (the "
                "licensed playlist is stripped for production; his compositions "
                "remain). The caption tracks render the surname 'Wetner'; "
                "spelling per the Pinside SAW game-archive design-team block, "
                "the only written source carrying it — crowdsourced, used as a "
                "spelling aid only. Quotes are verbatim ASR."
            ),
            cite=[
                cite(V_EXPO, "I did all the audio. I wrote a lot of the call outs."),
                cite(
                    V_LOSERKID,
                    "there's not going to be, uh, any music other than what "
                    "Glenn Rec Glenn Wetner composed.",
                ),
            ],
            credits=[("glenn-waechter", "sound"), ("glenn-waechter", "music")],
        ),
        pk.entry(
            MLH,
            note=(
                "Physical and electrical build is credited as mechanics. Joe "
                "speaks in the Pinball Expo interview; Jake Danzig's podcast "
                "crew rundown names him in full ('the guys that Bill saw' is "
                "the track's rendering of 'built SAW', the crew's previous "
                "homebrew), and the Pinside SAW game-archive roster "
                "corroborates the spelling. Quotes are verbatim ASR."
            ),
            cite=[
                cite(
                    V_EXPO,
                    "My name is Joe. Uh I do uh like the physical build, the "
                    "electrical build",
                ),
                cite(
                    V_LOSERKID,
                    "the Nashville crew is um the guys that Bill saw. That's "
                    "Glenn Wetner, um Eric Clotsz, Joe Farnsworth",
                ),
            ],
            credits=[("joe-farnsworth", "mechanics")],
        ),
        pk.entry(
            MLH,
            note=(
                "Antoinette voiced a large share of the callouts (one of the "
                "three callout characters is herself); spelling per Pinball "
                "News's TPF 2026 caption naming her an MLH game creator. Her "
                "wider creative contributions (ideas, promotion) have no "
                "catalog role and are recorded in the family notes. Quotes are "
                "verbatim ASR and Pinball News caption text."
            ),
            cite=[
                cite(V_LOSERKID, "Antuinette did uh did a ton of call outs"),
                cite(
                    PN_TPF26,
                    "MLH game creators, Antoinette Johnson & Jake Danzig",
                    locator="photo caption in the show-floor gallery",
                ),
            ],
            credits=[("antoinette-johnson", "voice")],
        ),
    ]

    lsoh = [
        pk.entry(
            LSOH,
            cite=knapp(
                KNAPP_LSOH,
                KNAPP_LSOH_AR,
                "A new pinball company is actively working on developing a "
                "pinball machine based on Little Shop of Horrors.",
            ),
            fields={"game_format": "pinball"},
        ),
    ]

    entries = people + road_trip + mlh + lsoh
    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description=(
            "Ramp's Pinball family details: Road Trip, Monster League Hockey, LSoH"
        ),
        entries=entries,
        sources=sources,
    )
    print(f"wrote {OUT} — {len(entries)} entries")

    # 0234: OPDB's copy of the Road Trip month claim (see module docstring).
    pk.write_patch(
        OUT_OPDB,
        attribution="opdb",
        description=(
            "Drop OPDB's stale Road Trip month claim (February, from the 2025 debut)."
        ),
        entries=[
            pk.entry(
                RT,
                retract=["month"],
                note=(
                    "OPDB dated the machine to its February 2025 world debut at "
                    "Pinball at the Beach; the machine is unreleased and "
                    "rampspinball.com states only 'Expected Late 2026'."
                ),
            )
        ],
    )
    print(f"wrote {OUT_OPDB} — 1 entry")


if __name__ == "__main__":
    main()
