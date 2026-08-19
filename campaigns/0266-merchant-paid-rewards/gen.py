"""Emit 0266 — the merchant-paid reward type and its population."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import patchkit as pk  # noqa: E402

PATCHES = Path(__file__).resolve().parents[2] / "patches"

# slug -> (cite ref, verbatim quote). Every quote states that someone at the
# location -- merchant, operator, storekeeper -- hands over the award, not the
# machine. Mined from IPDB free text; see README.md for the searches.
ROWS: list[tuple[str, str, str]] = [
    ("monarch-2", "ipdb:3414",
     "shipped from the factory with a set of printed back panel marquees offering a variety of non-cash prizes for high scores"),
    ("3-ring-circus", "ipdb:2543",
     'The awards would indicate how much money "in trade" would be given to the player by the location.'),
    ("odom-special", "ipdb:1693",
     "the prizes range from $5.00 in trade down through twenty-five smaller trade prizes"),
    ("autocount", "ipdb:114",
     "before awarding a prize, the operator can verify that a slug was not used"),
    ("crusader", "ipdb:607",
     'the different awards as payout "in trade" while the other side indicated point awards "For Amusement Only"'),
    ("mat-cha-skor", "ipdb:1560",
     "If the player's final score matches this number, the location would award the player a prize."),
    ("golden-arrow-2", "ipdb:3807",
     "Prizes placed underneath plate glass playfield are visible to the player."),
    ("vend-a-gift", "ipdb:5578",
     "Skillful play of balls awards prizes displayed under playfield glass."),
    ("castle-lite", "ipdb:468",
     "before paying the player any location award at the end of a game."),
    ("flying-colors", "ipdb:903",
     "The merchant checks the rewards through the mirror backboard"),
    ("pedal-pushers", "ipdb:1771",
     "this would be a local payout from the merchant and not from the machine itself."),
    ("bulls-eye-drop-ball-upright-model", "ipdb:5976",
     "The machine awards the player nothing for earning these marbles, but the location could provide under-the-counter cash payouts."),
    ("cueball", "ipdb:6026",
     "holds a card that can be updated weekly by the location to indicate what prize is awarded at the end of the week indicated"),
    ("startime", "ipdb:3400",
     "If the player chooses to cash out, the location would subtract the Sub-Total from the Total Score and pay the difference, one dime for each point."),
    ("el-rancho", "ipdb:769",
     "If the player chooses to cash out, the location would subtract the Sub-Total from the Total Score and pay the difference, one dime for each point."),
]

BILLBOARD = pk.source_child(
    "March 7, 1936", parent="billboard", slug="1936-03-07",
    source_type="periodical", year=1936, month=3, day=7,
    links=[(
        "https://www.worldradiohistory.com/Archive-All-Music/Billboard/30s/1936/BB-1936-03-07.pdf",
        "World Radio History scan", "archive")],
)

# Slots between the machine-dispensing payout types and free play, which the
# entry below shifts down to make room; the default 0 would have placed a rare
# type ahead of every common one.
entries = [
    pk.entry(
        "reward-type.merchant-paid",
        create=True,
        fields={"name": "Merchant-Paid Award", "display_order": 6},
    ),
    pk.entry(
        "reward-type.free-play",
        note="Shifted down one place so the merchant-paid award seats with the payout mechanisms it belongs among.",
        fields={"display_order": 7},
    ),
]

entries += [
    pk.entry(ref_slug and f"model.{ref_slug}", cite={"ref": ref, "quote": quote},
             relationships={"reward_type": ["merchant-paid"]})
    for ref_slug, ref, quote in ROWS
]

# Harvest Moon's evidence is Bally's own trade-press advertisement rather than
# IPDB, whose note records only that the machine does not pay out.
entries.append(
    pk.entry(
        "model.harvest-moon-2",
        cite={
            "ref": "billboard:1936-03-07",
            "locator": "p. 78",
            "quote": "PROGRESSIVE AWARDS [...] Light-up Back-Board, showing all winners, makes a hit with merchants everywhere.",
        },
        relationships={"reward_type": ["merchant-paid"]},
    )
)

pk.write_patch(
    PATCHES / "0266-merchant-paid-reward-type.yaml",
    attribution="flipcommons-catalog",
    description="Merchant-paid award reward type and the machines the location paid on.",
    sources=[BILLBOARD],
    entries=entries,
)
print(f"wrote 0266 with {len(entries)} entries")
