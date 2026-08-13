# The Fiery End of Obsidian High

Patch: `patches/0238-obsidian-high.yaml` (number claimed 2026-08-13).

## Models

- The Fiery End of Obsidian High (UP Pinball • 2026)

## User rulings (2026-08-13)

- **Keep `year: 2026`** — 0215's projection stands; do not retract.
- **`production_status` from the builder's own words**: a first-party statement of production intent → `announced`; a personal one-of-a-kind build with evidence of a built machine → `one-off`; otherwise leave unset. **Outcome: left unset** — as of MGC April 2026 she calls it "this unfinished shell" and states no production intent anywhere in the thread; Pinside's "Production planned" is crowd data.
- **The builder is Ellie Corcoran** — named in the copyright footer of her own site, `https://obsidianhigh.com/`, which the user rates the most primary carrier of the name. Credits go to the real name, not the Pinside username.
- **Corporate entity: rename + alias** — assert `name: "UP Pinball Collective"` (her own words, thread p1: "the will of the UP Pinball Collective"), with `UP Pinball` and `Yooper Pinball Collective` (her engraved sign, thread p1) as aliases. UP = Michigan's Upper Peninsula ("Yooper"). No city/location asserted — only the region is implied, so the locate-the-city rule can't be satisfied. The manufacturer keeps the trading name UP Pinball (the 0232 Turner Logic pattern).
- **No `homebrew` tag** — the vocabulary lacks one and creating it is deferred; recorded under Candidates below.

## Evidence

**A homebrew's first-party source is its builder.** The builder's posts in the Pinside build thread are her own words carried by a platform — press-release tier. That is a wholly different artifact from the Pinside _game archive_ row, which is crowdsourced (cross-check only, never sole support). `pinside.com` resolves to the seeded Pinside root.

**The maker site is `obsidianhigh.com` — not `uppinball.com`.** The 2026-08-06 survey probed only `uppinball.com` (no server) and missed it. The site is one under-construction page, but its footer carries the two facts that matter: "THE FIERY END OF OBSIDIAN HIGH copyright © 2019-2025 by Ellie Corcoran" and the framing that the game is a "pinball tie-in build" to her own story ("a tale of magic, heroism, and despair"). Its only outbound link is the Pinside build thread — the builder's own site endorses the thread as the canonical build record. 0238 creates the single-family citation root.

**The thread**: `pinside.com/pinball/forum/topic/volcano-blast` — 175 posts, 4 pages, all cached 2026-08-13 (p4 refetched; it had grown since the 2026-08-06 fetch). The builder is `Elliemechanical` (formerly `Gornkleschnitzer`); `section <url> "Elliemechanical"` addresses her posts. Cached game archive row: `pinside.com/pinball/machine/fiery-end-of-obsidian-high-the`.

### What the thread carries (builder's posts)

- **History**: a 2008 high-school shell named _Volcano Blast!_ (nothing survives); the current build started 2019 ("physical stuff in 2020"). Renamed to "The Fiery End of Obsidian High" as of 2024-11-11 (p1 edit note; p4 #171 announces the rebrand).
- **Layout (final)**: three flippers — lower left, upper left, lower right ("the three flipper drivers on the playfield", p3 #963; the 2019 upper-*right*-flipper layout was discarded by the 2020 "New plan", p1 #27). Jet bumpers in the "courtyard" (top two + bottom, p3 #848 / p2 #281). Hallway ramps both sides + lifting center ramp with lock tunnel beneath (p4 early posts, Oct 2023). Ramp diverters (p3 #339, p4). Three scoops (volcano tunnel, hot spring, left eject) + VUKs (hot spring VUK p2, far-back VUK + eruption VUK p3 #189). Two-branch subway (p3 #189). Skill-shot drop hole in the outer orbit (p3 #189). B-L-A-S-T / H-O-T / 1-2-3 standup targets ("standup target inserts", p4 #171; last two B-L-A-S-T targets mounted p4). Drop targets (optos, p3). Auto-launcher fork at the apron (p2 #1363). Knocker + shaker motor on the cabinet driver board (p3 #963). Self-built full-size cabinet + backbox, standard leg plates (p2).
- **Display**: 27" backbox monitor ("this JJP-size screen", p2 #776-784; supply chain forced up from ~17").
- **Electronics**: PC ("ATX", p3) + Teensy LC hub + ATMega328P module boards, her own KiCad flipper driver boards (p2 #938-1006) → `solid-state` / `ss-pc`. **Bespoke — no System entity created.**
- **Story/theme**: heavily anime-inspired (p1); the three main characters' magic powers (p4 #172); saving the school from the volcano (p1 #261); a time-loop day ("any number of time loops between morning and apocalypse", p1 #1437). Characters: Yumi, Saki, Hinata Akiyama; classmate Katashi.
- **Status**: at MGC April 2026 the "unfinished shell" **won an award** (p4 #175); she hopes it motivates finishing. No production intent stated anywhere.

## Traps

- **The rules are a design outline, not documentation of a shipped game.** "I think I've finalized my outline for the main rules at last" (p4 #174). Modes changed between posts ("you may notice the modes are different now"). No mode/rule content asserted; physical inventory only, verified against late-thread (post-whitewood-2) posts.
- **Early-thread layout facts are discarded.** The 2019 rule-of-three list (3 saucers, 3 wireforms, 3-bank drop targets, upper right flipper) predates the 2020 "New plan" redesign — never cite it for the final machine. Every asserted feature has a late-thread cite.
- **The maker name is crowd-derived on Pinside but corroborated in-thread** — see User rulings.
- **`uppinball.com` has no server** (DNS resolves, connection refused; checked 2026-08-06). The real site is `obsidianhigh.com`.

## Sought and not found

- **Jesse's surname** — "Jesse - audio enthusiast of the Collective - is working at composing the game's soundtrack" (p2 #161, ~2021) is the only mention in the thread; music was still "placeholders" in 2024 (p4). No music credit asserted: first-name-only person, in-progress work.
- **The MGC 2026 award's name** — the photo (p4 #175) presumably shows it; the post text doesn't name it. No catalog field wants it anyway.
- ~~A city for the corporate entity~~ — **found (user, 2026-08-13)**: the collective's own Facebook page (`facebook.com/yooperpinballcollective`) names Escanaba, MI and carries a street address (2301 9th Ave.). Citing it required extending flipcommons' shared-host allowlist (`apps/citation/shared_hosts.py`) with `facebook.com` — a maker's Facebook page is a tenant slice of a shared host, the same recognition shape as a CDN tenant path — and 0238 path-scopes `facebook.com/yooperpinballcollective` onto the Obsidian High root. The flipcommons change (spec + tests) is uncommitted in that repo.
- **Player count** — only the Pinside archive row says 4 players (crowdsourced sole support); the builder never states it.
- **Manufacture date** — nothing dates manufacture; the machine is unfinished. Pinside's "April 2026" is the MGC showing. No `month` asserted; `year: 2026` kept per user ruling.

## Not asserted (and why)

- **Captive ball** — a 2019 design decision (p1 #204) with no post-redesign mention; may not have survived.
- **Wireforms/habitrails** — "3 wireforms" is the discarded 2019 list; late thread has only oblique "rail" mentions.
- **`production_status`, `month`, `players`, model number, production_quantity** — see Sought and not found / User rulings.
- **Mode-derived features** (lane change, mystery award, video mode) — rules outline only.
- **Feature counts beyond flippers: 3** — ramp/scoop/VUK/jet counts evolved across the build; only the flipper count has a single late-thread span stating it.

## Future unique features

- **The volcano** — stacked laser-cut light-shield structure (p1 #27) holding locked balls and "erupting" them via VUK (p3 #189); classified `ball-holding-toys`.
- **The lifting center ramp** — "a fully-working lift ramp" (p4) over the lock tunnel; classified `moving-ramps` (pivots vertically).
- **The simulated segment-display HUD** — vector-recreated BK2K-style tube rendered on the LCD (p4 #226).

## Candidates for later

- **A `homebrew` tag** (user deferred 2026-08-13): the vocabulary has no way to mark home-brew machines; this model and any future homebrews (e.g. the builder's earlier Undertale) would take it.
- **Person alias** `Elliemechanical` for `person.ellie-corcoran` if username-keyed resolution ever matters.

## Gate runs

- 2026-08-13 emit (38 entries): `make validate` clean after three note-wording lint fixes (no site named, absence claim, "entity" jargon) and one patch-number-in-note fix. `make verify-quote-verbatim`: **0 failed** on the first pass.
- 2026-08-13 `make verify-quote-support ARGS="0238"`: **blocked — Anthropic API credit balance too low**; not yet run.
- Snapshot validation: pending (waiting on the user's go-ahead — other sessions share the dev DB).

**The patch is hand-edited from here on (user, 2026-08-13).** `gen.py` emitted the initial 38 entries and has been deleted, along with the campaign's other generators, precisely because re-running one would overwrite the hand edits.
