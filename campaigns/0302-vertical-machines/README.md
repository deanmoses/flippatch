# 0302–0306 — IPDB's `Vertical Pinball Machine` specialty

IPDB's Specialty field carries 27 values; this campaign works one of the ones the comparison layer still reported as pointing at absent target values: **Vertical Pinball Machine**, on 27 models.

## The finding that shaped it

The obvious move was a `vertical` cabinet form factor. Reading all 27 IPDB listings ruled that out: IPDB uses the heading for a playfield **orientation**, and hangs it on three different footprints at once.

- **11 of the 27** carry `Vertical Pinball Machine` *and* `Table Top/Counter Game` on the same listing. Gottlieb's Chuck-O-Luck (`ipdb:511`) says it outright — "This is a table top game with a vertical playfield."
- Bat-A-Ball (`ipdb:6022`, "This is a floor-standing upright game") and Junior League Bat-A-Ball (`ipdb:4675`, "This counter game was available with a floor stand") are the same game in two footprints. Both are marked Vertical.
- The rest split between floor uprights (Genco's early-1950s run, Boomerang at 84″, Zingo at 86″), wall boxes (Flik Flak, Match-Ball Wall-Flipper, Mini-Baseball) and counter games.

`cabinet` is a single FK. Spending it on the orientation would have made the footprint unrecordable for 11 models and left a contradiction waiting for whoever works the `Table Top/Counter Game` specialty (321 models, still open). So the specialty maps to a **tag**, and the cabinet is a separate per-model reading.

## The patches

| patch | what |
| --- | --- |
| `0302-upright-cabinet-vertical-tag.yaml` | creates the `upright` cabinet and the `vertical` tag |
| `0303-vertical-playfield-machines.yaml` | the `vertical` tag on all 27, cited to each listing's Specialty line |
| `0304-vertical-playfield-cabinets.yaml` | 14 `upright` + 12 `countertop`, each cited to what its source says about how the machine stood |
| `0305-upright-cabinet-description.yaml` | description for the cabinet |
| `0306-vertical-tag-description.yaml` | description for the tag |

`gen.py` emits 0302, 0303 and 0304. The descriptions are hand-written.

## Cabinet readings

**upright (14)** — 400, Golden Nugget, Jumpin' Jacks, Silver Chest and Sky Line on Genco's repeated "This is an upright game with a vertical playfield"; Bat-A-Ball on "floor-standing upright game"; Boomerang (84″) and 2005 World Car Racing Pinball (71½″) on their measurements; Zingo (86″) on an auction record; Still Crazy on four flippers over a playfield its own designers called large; Flik Flak, Match-Ball Wall-Flipper and Mini-Baseball as wall boxes; Pickwick on the 1889 Pessers design being "mounted vertically on a wall, instead of inclined on a table".

**countertop (12)** — the 11 that also carry `Table Top/Counter Game`, plus `ipdb:5714` (23″ × 12″ × 10½″). None reaches the `tabletop` bucket (2–4 ft, 30–80 lb, a miniaturized full-sized game): every one is under 2½ feet and sits on a bar. IPDB gives no dimensions and no whole-cabinet photo for the four 4-IN-1 models, so those rest on a Pinside listing giving 30″ × 22″ × 9.25″ and "Unique bar or counter top game" — near-identical to bowling (alle neune) at 28 × 22 × 9.

**no cabinet (1)** — Bouncing Ball (`ipdb:4837`, Royal Novelty, 1933). Its listing is a name, a date and a maker; it gets the tag and nothing else.

## Two roots seeded

`liveauctioneers.com` (Zingo's measurements) and `encyclopedia.com` (the Pickwick patent). `pinside.com` and `en.wikipedia.org` were already seeded.

## Also changed outside `patches/`

- `pinexplore/sql/05_reference.sql` — `Vertical Pinball Machine` now maps to the `vertical` tag instead of an absent cabinet value.
- `flipcommons/docs/DomainModel.md` — `upright` added under Cabinet, `vertical` under Tag.

## Still open

`Table Top/Counter Game` (321 models) and the other unmapped specialties — Cue Game, Horserace Game, Not A Pinball, Payout Machine, Shaker Ball Machine — are untouched. The 12 countertop readings here settle that specialty for those models in advance.

## Follow-on: 0311–0312, from IPDB's free text

The Specialty field is not the only place IPDB states the orientation. Sweeping `notable_features` and `notes` for "vertical playfield" turned up five more machines the specialty misses:

| model | IPDB says |
| --- | --- |
| Whiz-Bowler (`ipdb:5702`) | "10 balls for 1 cent. Vertical playfield." |
| Zipper (`ipdb:5701`) | "5 balls for 1-cent. Vertical playfield." |
| Pickwick (Improved) (`ipdb:5432`) | "Vertical playfield bagatelle." |
| Flipper (`ipdb:7040`) | "a small vertical playfield of pins to scoring pockets at the bottom" |
| Hi Fly (`ipdb:5615`) | "This is a table top game with a vertical playfield." |

`0311-vertical-playfield-free-text.yaml` tags all five; `0312-improved-pickwick-cabinet.yaml` gives the improved Pickwick the `upright` cabinet its predecessor already has.

### Deliberately not tagged

The same sweep matched six more, none of which is a vertical *machine*:

- **A secondary vertical playfield in the backbox**, on an otherwise ordinary floor machine — Banzai Run (`ipdb:175`), Wreck'n Ball (`ipdb:6167`), Double Action (`ipdb:706`), Springtime (`ipdb:2326`). This is a gameplay feature, and there is no record for it to land on yet.
- **Varkon** (`ipdb:2721`) — "Both playfields are tilted away from the player and viewed through a mirror", so the vertical playfield is an illusion the mirror creates.
- **Play Ball** (`ipdb:1813`) — the vertical playfield belongs to a smaller Play Ball in a 1926 patent drawing, not to this 1932 model.

A second sweep for "upright game", "wall-mounted", "vertical cabinet" found only IPDB's *other* sense of upright — its flasher-type gambling consoles (Black Dragon, Skill Derby, Bulls-Eye Drop Ball) — plus Bally Alley, a wall-mounted light game with no playfield at all. The Euromat trio (`ipdb:5171`, `5173`, `5174`) is the instructive case: wall-mounted, so `upright` by cabinet, but "The playfield is sloped towards the player", so not `vertical`. Those three still have no cabinet.
