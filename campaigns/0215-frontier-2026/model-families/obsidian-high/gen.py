"""Emit patch 0238 — The Fiery End of Obsidian High (UP Pinball homebrew).

See ../../README.md for the family split and ObsidianHigh.md beside this file
for the evidence inventory, the user rulings, the traps and the decisions this
generator encodes (2026-08-13).

SCOPE IS ONE MODEL — a homebrew, so the first-party source is the builder
herself: Ellie Corcoran, posting as Elliemechanical in the machine's Pinside
build thread, which her own site (obsidianhigh.com, rooted here) links as the
canonical build record. Builder posts are her own words carried by a platform
(press-release tier); the Pinside game archive row is crowdsourced and is
never cited.

ONLY THE BUILT MACHINE IS ASSERTED: the rules are a design outline and the
2019 layout was discarded by the 2020 "New plan", so every feature cite comes
from a post-redesign post describing installed hardware (the one exception,
multiball, rides the physical lock tunnel and says so in its note). No
production_status (unfinished, no production intent stated), no month, no
player count — ObsidianHigh.md records each omission.

USER RULINGS (2026-08-13): keep year 2026; corporate entity renamed to
UP Pinball Collective (her own words) with UP Pinball / Yooper Pinball
Collective aliased, manufacturer keeps the trading name; credits go to the
real name from her site's footer; no homebrew tag.

Run: uv run python campaigns/0215-frontier-2026/model-families/obsidian-high/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0238-obsidian-high.yaml"

MODEL = "model.the-fiery-end-of-obsidian-high"
CE = "corporate-entity.up-pinball"

# ── Sources ─────────────────────────────────────────────────────────────
HOME = "https://obsidianhigh.com/"
P1 = "https://pinside.com/pinball/forum/topic/volcano-blast"
P2 = "https://pinside.com/pinball/forum/topic/volcano-blast/page/2"
P3 = "https://pinside.com/pinball/forum/topic/volcano-blast/page/3"
P4 = "https://pinside.com/pinball/forum/topic/volcano-blast/page/4"

BUILDER = "in the builder's own post"


def cite(ref: str, quote: str) -> dict[str, str]:
    if ref == HOME:
        return {"ref": ref, "quote": quote}
    return {"ref": ref, "locator": BUILDER, "quote": quote}


# The connective tissue every credit rests on: the thread's poster is the
# person the site's footer names.
BUILDER_NOTE = (
    "The builder posts as Elliemechanical; the footer of her own site, "
    "obsidianhigh.com, names her Ellie Corcoran."
)

FOOTER_QUOTE = "THE FIERY END OF OBSIDIAN HIGH copyright © 2019-2025 by Ellie Corcoran."

# ── Thread spans (lifted from the cached pages 2026-08-13) ──────────────
WALKTHROUGH_VUK = (
    'From there, it can either be fired upwards to "erupt" via the VUK, or that '
    "repurposed kickback mech pushes it out of the VUK and into the volcano tunnel scoop"
)
WALKTHROUGH_SCOOPS = (
    "into the volcano tunnel scoop (also hittable from the playfield, to the right of "
    "the ramp), where it makes its way down the longer bent subway and eventually "
    "emerges from the left scoop"
)
SKILL_ORBIT = (
    "In the top right (top left in the wiring photo, of course), there is a skill shot "
    "drop hole in the outer orbit."
)
REFLEX_WORK = (
    "Flippers, slingshots, and bumpers work (might need to double check an issue with "
    "the top two jets though)"
)
CABINET_DRIVERS = (
    "the four remaining drivers are used for the Start and Extra Ball button lights, "
    "the knocker, and the shaker motor"
)
LIFT_RAMP = (
    "Not only is it a lot more fun to shoot the elevated loop, there's also the "
    "satisfaction of a fully-working lift ramp here as well. I can't wait to start "
    "locking balls in the tunnel under the ramp!"
)


def main() -> None:
    sources = [
        pk.source_root(
            "Obsidian High",
            description=(
                "Official site for The Fiery End of Obsidian High and the story it "
                "adapts, published by its builder Ellie Corcoran. Its only outbound "
                "link is the machine's Pinside build thread."
            ),
            links=[(HOME, "Obsidian High", "homepage")],
        ),
    ]

    entries = [
        # ── Corporate entity (user ruling: rename + alias) ──────────────
        pk.entry(
            CE,
            note=(
                "The name UP Pinball came from Pinside's crowd-entered game "
                "archive row; the builder's own words name the collective. The "
                "manufacturer keeps the trading name UP Pinball. UP is Michigan's "
                "Upper Peninsula - she also engraved a Yooper Pinball Collective "
                "sign - but no city is stated anywhere, so no location is asserted."
            ),
            cite=[
                cite(
                    P1,
                    "not impossible considering the will of the UP Pinball Collective",
                ),
                cite(
                    P1,
                    "I decided to use it to make an engraved Yooper Pinball "
                    "Collective sign rather than waste the metal",
                ),
            ],
            fields={"name": "UP Pinball Collective"},
        ),
        pk.entry(
            CE,
            relationships={
                "corporate_entity_alias": ["UP Pinball", "Yooper Pinball Collective"]
            },
        ),
        # ── The builder ──────────────────────────────────────────────────
        pk.entry(
            "person.ellie-corcoran",
            create=True,
            cite=cite(HOME, FOOTER_QUOTE),
            fields={"name": "Ellie Corcoran"},
        ),
        # ── Credits (one role per changeset; each span shows her doing it)
        pk.entry(
            MODEL,
            note=BUILDER_NOTE + " The story the game adapts is her own work.",
            cite=cite(HOME, FOOTER_QUOTE),
            credits=[("ellie-corcoran", "concept")],
        ),
        pk.entry(
            MODEL,
            note=BUILDER_NOTE,
            cite=cite(P1, "Tweaked my design a bit last night and will be doing more tonight."),
            credits=[("ellie-corcoran", "design")],
        ),
        pk.entry(
            MODEL,
            note=BUILDER_NOTE,
            cite=cite(
                P4,
                "I drew everything here except the hair and uniforms of the three "
                "main characters",
            ),
            credits=[("ellie-corcoran", "art")],
        ),
        pk.entry(
            MODEL,
            note=BUILDER_NOTE,
            cite=cite(
                P3,
                "immediately wrote up some basic firmware to at least let me test "
                "out the new flippers",
            ),
            credits=[("ellie-corcoran", "software")],
        ),
        pk.entry(
            MODEL,
            note=BUILDER_NOTE,
            cite=cite(
                P1,
                "I'm fairly confident I can engineer a hidden ramp to accomplish "
                "the same task",
            ),
            credits=[("ellie-corcoran", "mechanics")],
        ),
        pk.entry(
            MODEL,
            note=BUILDER_NOTE
            + " Music is not credited: the game's soundtrack was being composed "
            "by a collective member named only Jesse, and music was still a "
            "placeholder years later.",
            cite=cite(
                P4,
                "here's a look at a handful of sound effects as well as some VERY "
                "Sys11-esque bonus counting. I'm going to spend more time on SFX "
                "this week",
            ),
            credits=[("ellie-corcoran", "sound")],
        ),
        # ── Classification fields ─────────────────────────────────────────
        pk.entry(
            MODEL,
            cite=cite(
                P1,
                "Back in 2008, I really wanted to build a pinball machine, and a "
                "significant lack of knowledge and funding didn't stop me from trying.",
            ),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            MODEL,
            note=(
                "Classified from the build's electronics: a PC game computer with "
                "custom Teensy/ATMega controller boards."
            ),
            cite=cite(
                P2,
                "The Teensy has a built-in USB board, which straightforwardly solves "
                "upstream communication to and from the PC with code I can directly "
                "reuse from UT.",
            ),
            fields={"technology_generation": "solid-state"},
        ),
        pk.entry(
            MODEL,
            note=(
                "Commodity PC hardware runs the game - the playfield power switches "
                "on the PC's own ATX supply - which is the ss-pc subgeneration."
            ),
            cite=cite(
                P3,
                "this relay was connected to one of the ATX 5v lines, so when the "
                "computer comes on, so does the playfield",
            ),
            fields={"technology_subgeneration": "ss-pc"},
        ),
        pk.entry(
            MODEL,
            note="A 27-inch backbox monitor.",
            cite=cite(
                P2,
                '27" monitors. [...] I do think this JJP-size screen will catch a '
                "lot of eyes once it's showing off visual novel art and anime girls.",
            ),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            MODEL,
            note=(
                "Classified from the build: a self-built full-size cabinet with "
                "legs and backbox."
            ),
            cite=cite(
                P2,
                "Tomorrow I will be bracing the cabinet with 90-degree corner "
                "brackets and standard leg plates, assembling the neck and attaching "
                "it to the lower cab, and most likely test-fitting it with legs and trim.",
            ),
            fields={"cabinet": "floor"},
        ),
        # ── Themes (one per changeset, each on its own span) ─────────────
        pk.entry(
            MODEL,
            cite=cite(
                P1,
                "The new design, art, and story will be heavily anime-inspired.",
            ),
            relationships={"theme": ["anime"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(
                P1,
                "So each of them has a plan to try to save the school from the "
                "volcano using various strategies, supplies, and magical abilities.",
            ),
            relationships={"theme": ["volcanoes"]},
        ),
        pk.entry(
            MODEL,
            cite=[
                cite(HOME, "a tale of magic, heroism, and despair"),
                cite(
                    P4,
                    "illustrations of the moments that each main character's magic "
                    "powers awaken",
                ),
            ],
            relationships={"theme": ["magic"]},
        ),
        pk.entry(
            MODEL,
            note="The school is the titular Obsidian High; the characters are its students.",
            cite=[
                cite(
                    P1,
                    "So each of them has a plan to try to save the school from the "
                    "volcano using various strategies, supplies, and magical abilities.",
                ),
                cite(
                    P4,
                    "a vertical airball shield featuring classmate Katashi who is "
                    "just now realizing he's not getting the calm day of studying "
                    "he expected",
                ),
            ],
            relationships={"theme": ["high-school"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(
                P1,
                "Canonically, there could have been any number of time loops between "
                "morning and apocalypse, but the game will depict three, one for "
                "each anti-volcano plan.",
            ),
            relationships={"theme": ["time-travel"]},
        ),
        # ── Physical playfield inventory (installed hardware only) ───────
        pk.entry(
            MODEL,
            cite=cite(
                P3,
                "Aside from the flipper switches - which get wired back up to the "
                "three flipper drivers on the playfield - everything in the cabinet "
                "is controlled by the final aux solenoid driver board.",
            ),
            relationships={"gameplay_feature": [{"flippers": 3}]},
        ),
        pk.entry(
            MODEL,
            note=(
                "The builder's own word for them is jets; the count is not asserted "
                "- the spans name the top two and the bottom bumper but state no total."
            ),
            cite=cite(P3, REFLEX_WORK),
            relationships={"gameplay_feature": ["jet-bumpers"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, REFLEX_WORK),
            relationships={"gameplay_feature": ["slingshots"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(
                P3,
                "How did my five-volt microcontrollers and drop target optos manage "
                "to survive the unstoppable onslaught of a twelve-volt assault?",
            ),
            relationships={"gameplay_feature": ["drop-targets"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(
                P4,
                "The light bulbs pictured in this scene sync with the standup "
                "target inserts on the playfield.",
            ),
            relationships={"gameplay_feature": ["standup-targets"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, WALKTHROUGH_VUK),
            relationships={"gameplay_feature": ["vertical-up-kickers"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, WALKTHROUGH_SCOOPS),
            relationships={"gameplay_feature": ["scoops"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, "Yes, there are a couple of subway branches."),
            relationships={"gameplay_feature": ["subways"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(
                P4,
                "With the hallway ramps on both sides in place (more or less), the "
                "diverters can finally become useful.",
            ),
            relationships={"gameplay_feature": ["ramps"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, "the ramp diverters and outhole kicker, which are mounted topside"),
            relationships={"gameplay_feature": ["ramp-diverters"]},
        ),
        pk.entry(
            MODEL,
            note=(
                "The center ramp lifts - pivoting vertically to open the lock "
                "tunnel beneath it - which is the moving-ramps mechanism."
            ),
            cite=cite(P4, LIFT_RAMP),
            relationships={"gameplay_feature": ["moving-ramps"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P4, LIFT_RAMP),
            relationships={"gameplay_feature": ["ball-locks"]},
        ),
        pk.entry(
            MODEL,
            note=(
                "The lock tunnel under the center ramp is built (the lift-ramp "
                "span); the lock count comes from the builder's rules outline, "
                "which is design intent rather than shipped documentation, so "
                "multiball attaches without a ball count."
            ),
            cite=cite(P4, LIFT_RAMP + " [...] 3 locks start multiball"),
            relationships={"gameplay_feature": ["multiball"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, SKILL_ORBIT),
            relationships={"gameplay_feature": ["skill-shot"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, SKILL_ORBIT),
            relationships={"gameplay_feature": ["orbits"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(
                P2,
                "the autolauncher fork holds the ball and would physically conflict",
            ),
            relationships={"gameplay_feature": ["auto-launch"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, CABINET_DRIVERS),
            relationships={"gameplay_feature": ["knockers"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(P3, CABINET_DRIVERS),
            relationships={"gameplay_feature": ["shaker-motors"]},
        ),
        pk.entry(
            MODEL,
            note=(
                "The volcano structure holds locked balls and ejects them upward "
                "via its VUK, so it classifies as a ball-holding toy."
            ),
            cite=cite(P3, WALKTHROUGH_VUK),
            relationships={"gameplay_feature": ["ball-holding-toys"]},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="The Fiery End of Obsidian High (UP Pinball): builder-sourced enrichment.",
        entries=entries,
        sources=sources,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
