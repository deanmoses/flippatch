# 0031 — maker operating_status (+ model cleanup fixes)

The first **web-sourced** curated patch. Sets `CorporateEntity.operating_status`
for makers with a non-variant model released since 2010 that Wikipedia's
[List of pinball manufacturers] _Present_ section does not cover, and rides a
small set of model cleanup fixes along.

## Signal & method

- **Scope:** the 48 corporate entities with a non-variant model since 2010 minus
  the current-incarnation makers already on Wikipedia's Present list (those are a
  separate, mostly-Wikipedia-sourced set). Each remaining maker was researched
  individually.
- **Recency rule:** `ongoing` requires a **2023-or-newer** source showing current
  production — founding-year references don't count, because "still producing"
  goes stale fast. `ended` is permanent, so any dated source is fine.
- **Announced ⇒ ongoing:** a company with an announced (forthcoming) model is
  producing by definition (this is what keeps Ramp's `ongoing` on its unreleased
  debut, Road Trip).
- **Evidence** comes from the pinexplore web-scrape cache (see
  `pinexplore/docs/WebCache.md`): every page fetched once, verbatim quote pulled
  with `web_cache`/`patchkit.sentence_with`, the page's own date checked for the
  recency rule. We cite the **primary URL**; Wayback archive permalinks are a
  separate base-system concern (not hand-carried here).

## The only question is: are they still producing?

`operating_status` is about production, not legitimacy. Whether a catalogued
manufacturer is a professional firm or a few friends building a machine in a
garage is not the key distinction — if a durable 2023+ source shows they are
producing (or have an announced) pinball machine, they are `ongoing`. If the
source only proves a project exists, a limited run happened, or the entity is
active in a support/software role, leave it deferred.

## Totals (41 claims)

- **19 ongoing** — each with a 2023+ source.
- **18 ended** — defunct with a cited closure/cause (deeproot SEC 2021, Haggis
  liquidation 2024, Heighway 2018, Suncoast operations shutdown 2019, MarsaPlay,
  WhizBang, Zidware, Skit-B) or not-a-pinball-OEM (Bandai Namco, Kieswetter, The
  Pinball Company, Valley-Dynamo, Novomatic, American Girl, SIRMO = now bingo/AWP,
  Bifuca), plus two fixed/ended runs (Day One's ScoreGasm Master and Retro
  Pinball's King of Diamonds).
- **4 model fixes** — Bifuca's Pinball Tronic → `game_format: miscellaneous`
  (video-screen "virtual pinball", not pinball); Road Trip → `production_status:
announced` (forthcoming, not a shipped 2025 game); Cactus Canyon Continued and
  Demolition Man on Steroids → `production_status: aftermarket` (OPDB "Converted
  game" — third-party code-patch / retheme of an existing machine, not a new one).

## Review-driven corrections (cite-must-support-the-claim)

An adversarial review caught five over-reaches where the cite didn't carry the
claim. All accepted:

- **suncoast / megaverse / mocean → deferred at first.** Their original cites
  proved distress or existence, not closure: SunCoast's first source was only a
  2019 Chapter 11 (reorganization) filing; Megaverse's and Mocean's pages did not
  carry a closure claim. A later TWIP source moved Suncoast to `ended`; Megaverse
  and Mocean remain deferred.
- **ian-harrower → re-cited.** The Portal credit proved Ian coded a _Multimorphic_
  game, not that his own label produces; re-cited to his Kineticist maker page
  (2023-Present, 2 games).
- **pinball-tronic-gold → dropped.** The Recreativas page names Pinball Tronic, not
  Gold, and Gold isn't `variant_of` it. Needs its own source or a variant link
  first.

## Deferred evidence pass

Follow-up review found five rows strong enough to assert:

- **`dutch-pinball` → ongoing.** Pinball News (2026) says Dutch Pinball is still
  building Alice's Adventures in Wonderland and records Dutch Pinball's stated
  plan to develop and produce its own titles.
- **`retro-pinball-llc` → ended.** IPDB says King of Diamonds production ended in
  2012 after 5 sample games and 50 regular games.
- **`day-one-pinball-manufacturing-incorporated` → ended.** Pinball News says Day
  One would build a fixed total of 30 ScoreGasm Master games: 10 prototypes and
  20 production units.
- **`suncoast-pinball` → ended.** This Week in Pinball quotes Suncoast customer
  correspondence saying Suncoast was shutting down pinball operations because
  continuing was not financially viable.
- **`rebellion-pinball` → ongoing.** Kineticist lists Rebellion as Primary
  `2022-Present` and describes Space Singularity as a pinball creation project
  made from scratch by friends. It is a hobby/homebrew project, but that still
  bears on whether the project is ongoing.

## Deferred (9) — left to the Commit-5 ended baseline, flagged

Not asserted because not-currently-producing can't be cleanly cited, because a
source suggests activity but not current complete-machine production, or because
production status is genuinely ambiguous. (Each still has a model — the question
is only whether they're _producing now_, not whether they're a "real" maker.)

- **Activity adjacent to production, but not enough for `ongoing`:**
  `quetzal-pinball` (its designs are now built by Bitronic; IPDB/Wikipedia list
  it as current, but no clean 2023+ Quetzal production source surfaced),
  `team-pinball` (Pinball News calls it a 2026 software/hardware developer and
  it provides code for Pedretti's Funhouse 2.0 kit; no own machine since 2018),
  `riot-pinball-llc` (a homebrew/design collective that designed Legends of
  Valhalla and licensed commercial production elsewhere; no current machine
  manufacture under Riot's own brand).
- **One model, nothing since — dormant/dead, but no closure event to cite:**
  `headsup-pinball` (Wizard, 2022; Pinside/IPDB prove a planned 16-game run, 14
  made as of March 2023, plus 12 conversion kits), `megaverse-project` (Escape
  From The Megaverse, 2022; one catalogued game, but inactivity is inferred rather
  than directly cited).
- **Active ecosystem/module developer, not primary machine maker:** `mocean`
  (Dungeon Door Defender, 2023). Kineticist lists it as "Not Primary" and
  "2023-Present", which is useful evidence for an active P3 module developer but
  not for current complete-machine production.
- **Aftermarket-conversion makers** (their model is fixed to `aftermarket` above,
  but their own status can't be cleanly cited): `eric-priepke` (Cactus Canyon
  Continued, 2012) and `pinnovating` (Demolition Man on Steroids, 2013). The OPDB
  "Converted game" note proves the model is a conversion, not that the maker
  ended. Dormant, deferred to the baseline.
- **Can't verify:** `wee-chin-electric-machinery-inc` — a sheet-metal cabinet OEM;
  IPDB proves 2017/2019 WeChe pinball/amusement machines and manufacturer-sourced
  files for the 2019 games, but its site blocks automated fetch and no 2023+
  production or closure source surfaced.

## Dead ends / notes

- Sites that block automated fetch were routed around: SIRMO's distributor page
  (seeben.com) → the bingo reference site (bingo.cdyn.com, which fetched); Pinball
  Adventures' own site (broken SSL cert) → Kineticist's maker page.
- **Data-quality finds (not fixed here):** Turner Pinball's catalogued model
  "Carthage" appears wrong — Turner's real titles are Ninja Eclipse (2024) and
  Merlin's Arcade (2025). Worth a follow-up.

## Files

- `classify.py` — the frozen classification (rows + sources + needles + defers).
- `gen.py` — reads the cache (quotes) + live flipcommons DB (`expect:` guards),
  emits `../../0031-maker-operating-status.yaml` via `patchkit`. Re-runnable.

[List of pinball manufacturers]: https://en.wikipedia.org/wiki/List_of_pinball_manufacturers
