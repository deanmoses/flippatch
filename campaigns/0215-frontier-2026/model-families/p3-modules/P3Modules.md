# P3 Modules — 0231

## Status

**Snapshot-validated and complete (2026-08-13).** The user hand-restructured the emitted patch (one assertion per changeset; notes deleted where the cite carries the change — both rules promoted to RULEBOOK.md → Asserting claims) and the sweep section was reworked to match; the hand-edited YAML is authoritative; `gen.py` was synced to that shape and has since been deleted along with the campaign's other generators (2026-08-13). Applied cleanly on the 0214 snapshot with patches through 0232; all fields, credits, features, quantities and per-field citation instances verified through the analytics foundation. Awaiting user commit; not pushed.

## Scope (user decisions, 2026-08-13)

- **Full enrichment for the 2026 two** (Dungeon Crawler Carl, Ender's Game) **plus a platform-facts sweep** across all 22 catalog Multimorphic models: `system`, `cabinet`, `game_format`, `display_type` where missing, `production_status`, and evidenced `production_quantity`. Full enrichment of the older 20 (credits, features) is out of scope.
- **No P3 chassis model.** The platform is represented as manufacturer + the existing `multimorphic-p3-roc` System; platform hardware facts assert on each game model, cited to the maker's platform/FAQ pages with a carry note. The bare chassis ("P3 Machine (Deposit only)", $8,500 as of the TPB launch post) stays unrepresented as a model.
- **No creation of the ~11 P3 games the catalog lacks** — see [Missing games](#missing-p3-games-not-in-the-catalog).

## Models

The whole family shares: manufacturer Multimorphic (Round Rock, TX), System `multimorphic-p3-roc` (already in catalog — created by seed, used by American Pinball and Bob Nies models; **reference, never re-create**), playfield-LCD display, standard floor cabinet, `game_format: pinball`.

Maker's own two-class game taxonomy (games index page):

- **Full game kits with playfield modules** — physical upper-playfield module + software: Lexy Lightspeed EFE, Cannon Lagoon, Cosmic Cart Racing, Heist, Weird Al, Final Resistance, The Princess Bride, Portal (Std/Ext), DCC, Ender's Game.
- **Add-on games** — software-only, runs on another game's module: Barnyard, Grand Slam Rally, Hoopin' It Up, Lexy Lightspeed SAS, ROCs, Shoot 'n Scoot, Heads Up!, Sorcerer's Apprentice. OPDB already seeded `conversion_kit` edges for four of these (Hoopin' → Lexy EFE, GSR → Cannon Lagoon, Sorcerer's → CCR, Lexy SAS → Lexy EFE) — the edge target is the module-donor game. **Keep as-is; don't duplicate.**

Baselines saved beside this file: `baseline-fields.txt` (per-model field state), `baseline-claims.txt` (all claims per model — duplicate-scan source). Older models already carry OPDB/IPDB claims for month, player_count, display_type, credits (some), themes, tags. **Only the platform fields above are missing catalog-wide.**

## Evidence inventory (all cached in pinexplore web cache)

### 2026 two — first-party

- `https://www.multimorphic.com/dungeon-crawler-carl` — product page: full credits block, theme/narrative copy, Upper Playfield Module feature list (Carl, Princess Donut and Magnet Ball Lock, Mongo, Safe Room/Desperado Club, Tunnel, Disk Loop, HEAL targets, playfield display), "3-flipper game", machine-vs-kit purchase links, mature-audiences warning.
- `https://www.multimorphic.com/enders-game` — product page: full credits block, feature list (Captive Ball Balance Mech, wireforms, Center Scoop, Friend Magnet, Fight Ring, Disk Cannon, Projected HUD), "3-flipper game".
- Store (all four cached): `store/p3-pinball-machine/p3-machine-with-dcc` ($12,350 full, $2,500 deposit), `p3-machine-with-enders-game` ($11,750), `store/p3-game-kits/multimorphic-game-kits/dcc-game-kit` ($5,250 kit; kit = upper playfield module + lower playfield module extension), `enders-game-game-kit` ($4,400). All: "Production of this title begins in late 2026" → `production_status: announced`.
- Official trailers (subtitled transcripts cached): `youtube.com/watch?v=95SKuPLagXo` (DCC), `youtube.com/watch?v=YkOB05jwjhQ` (Ender's Game).

### 2026 two — journalism (reveal date evidence)

- Pinball News `2026/07/27/dungeon-crawler-carl-revealed/` and `2026/07/27/enders-game-revealed/` — deeply detailed: shared-design story ("use the same playfield layout and gameplay mechanisms"; design originally developed for Ender's Game), disk mech internals (183 RGB LEDs, 10 switches, slip rings, cannon), SlingLocks, Gerry Stellenberg interview, full credit tables matching the maker's pages, prices, "Production … currently planned for late 2026".
- Kineticist `news/multimorphic-dcc-enders-game`, Arcade Heroes `2026/07/27/dungeon-crawler-carl-enders-game/` + press-release reprint `news/press-releases/multimorphic-inc-launches-enders-game-for-the-p³-pinball-platform/`. DCC was unveiled Saturday July 25 at San Diego Comic-Con (Audible panel), full announcement July 27.

### Platform pages — first-party (the sweep's citation base)

- `https://www.multimorphic.com/p3-pinball-platform` — "modular multi-game pinball platform", "adds dynamic LCD graphics and ball tracking", modular upper playfields, 60-second module swap.
- `.../frequently-asked-questions-faq` — "REAL and PHYSICAL! The P3 is the same size/shape as traditional pinball machines … replaces a traditional wooden lower playfield with a touchscreen LCD" → `cabinet: floor` (dimensional-classification note per 0228 precedent) + `display_type: lcd`.
- `.../hardware-control-system` — "The P3 Pinball Platform is built on top of our P3-ROC, PD-16, PD-LED, and SW-16 boards" → the `system` cite for every model.
- `.../games` — the two-class game taxonomy + per-class game lists.
- `.../3rd-party-developers`, homepage — context.

### Older games — per-model production evidence

- Store category listings (cached 2026-08-13): `category/p3-game-kits/multimorphic-game-kits` — sold-from-stock kits with prices: Final Resistance $3,400, Weird Al $3,500, Heist $3,250, Cosmic Cart Racing $3,000, Lexy EFE $3,000, Cannon Lagoon $1,800; deposit rows for DCC/EG/Portal Std+Ext/TPB Std+LE. `category/add-on-software/multimorphic-add-on-game-software` — Elemental $0, Sorcerer's Apprentice $499, Shoot 'n Scoot $169, Lexy SAS $99, ROCs $199, Barnyard $149.
- News posts (cached): TPB launch `news/introducing-the-princess-bride-pinball-game` (2024-02-18) — editions Standard/LE/CE with kit and machine prices, **CE "limited to only 500 units"**, "Production begins this summer!", base P3 $8,500, per-edition product links, "All editions include the same playfield module and game software". Weird Al launch `news/weird-als-museum-of-natural-hilarity` (2022-02-24) — **LE "limited to 227 copies"**, $3,000 kit / $8,300 base machine, 17 songs + 2000 custom callouts, LE package contents (motorized topper, autographed translite). `news/multimorphic-public-update-june-2026` — "approximately 13 months after launching Portal in March 2025, we finished shipping all 2025 Portal orders" → Portal `produced`. `news/hoopin-it-up-free-download-and-4-way-simultaneous-play-on-cosmic-cart-racing` (2019). `news/portal-production-update-october-2025`. `news/stumblor_partnership` (2026-07-05).
- Per-game store pages cached earlier by prior sessions: hoopin-it-up, grand-slam-rally, sorcerers-apprentice, drained, ranger-in-the-ruins, bird-watcher, blood-bank-billiards, drained-bite-sized, dungeon-door-defender, flipper-foxtrot, silver-falls (mostly 3rd-party).

### Documents

- **P3 Quick Start Guide** (Pinside-hosted PDF, cached 2017): `o.pinside.com/9/6a/8f/96a8ff44d4bfcb2a771fcb6da6886bf7c6574ce2.pdf` — "Know Your Machine", module handling. Publisher Multimorphic → would cite as a document (`multimorphic:<slug>`) if used; Pinside URL rides as `catalog`/`archive` link.
- **P3 Machine Dimensions** — a JPEG on Google Drive (`drive.google.com/file/d/1kS6qtGxG4AzWkzx4yiHNqj6VjGcGvK-q`), fetched into cache via the `uc?export=download` URL (stored under `drive.usercontent.google.com`). OCR reads 28¾″ × 75½″ × 24¾″, 335 lbs (360 lbs shipping). **Citability problem**: Google Drive is a shared host not in the shared-hosts allowlist; treat as research-only. The FAQ's "same size/shape as traditional pinball machines" carries the cabinet classification instead.
- The TPB launch post references a per-edition **feature matrix image** — not transcribed; would need `web_import.py --text-file` if edition-differentiating claims are ever wanted.

## Traps

- The maker's per-game store categorization does not match corporate attribution one-for-one: Grand Slam Rally and Hoopin' It Up sit in the **3rd-Party** game-kit store category while the catalog attributes them to Multimorphic. Not our fight this patch (don't overwrite); noted for a future corporate-entity pass.
- Multimorphic's news index paginates and its month-archive URLs are `news/2026/07`-style (the `news//2026` double-slash links on the page normalize to the same place).
- The p3-pinball-platform nav link "P-ROC Control System" resolves to `/p3-pinball-platform/hardware-control-system` (the `/p-roc-control-system` guess 404s).
- Store category listing pages live under `/category/...`, not `/store/<category>` (those 404).
- `web_cache.py search "<term>" --url <substring>` does not act as a domain filter; `--url` wants one document's URL. Enumerate a domain by searching a term and grepping `^url:`.
- Credits punctuation on the maker's pages is irregular ("Rules; Colin MacAlpine", "Mechanicals; TJ Weaver") — lift spans verbatim, semicolons included.

## Sought and not found (authoring-time searches, 2026-08-13)

- **Player count for DCC / Ender's Game** — not stated on product, store, or reveal pages. (Older P3 games carry OPDB player_count 1–4.)
- **A DCC or Ender's Game announcement post on multimorphic.com's own news index** — the reveal ran via SDCC + outlet coverage + product pages; the June 2026 public update only teases "our next launch coming soon".
- **Maker PDFs for the 2026 two** (manual, flyer) — none published yet; the inventory floor's "product pages only" still holds, except the QSG + dimensions image above.
- **Heads Up!** (catalog 2021) — absent from the maker's current games index and store; evidence for its production status needs Wayback or its 2021 announcement (news archive 2021/08 or 2021/09), not yet fetched.

## Missing P3 games not in the catalog

From the maker's games index (recorded 2026-08-13; user decision: do not create): Drained, Drained Bite-Sized, Bird Watcher, Blood Bank Billiards, Dungeon Door Defender, Elemental Pinball, Flipper Foxtrot Rhythm Explosion, Ranger in the Ruins, Nezzex City, Row Mania, Silver Falls, Young Martial Artist. Mostly 3rd-party (For Amusement Only Games, Ian Harrower Games, …); store pages for most are already cached.

## Not asserted (and why)

- **month on DCC / Ender's Game** — a Model's `year`/`month` is the **manufacture date**, never the announcement (DataPatchAuthoring.md; user ruling 2026-08-13). The first emit asserted the July 27 reveal month following 0229's precedent; the user hand-deleted those entries from 0231 and had 0229's matching claims removed too. A future patch records the real month once production starts (planned late 2026).
- **player_count on DCC / Ender's Game** — no primary source states it (see Sought and not found).
- **production_status on Hoopin' It Up** — the game is an official but **free** download ("is a free download for all P3 owners"); `produced` means commercially produced and sold, and no other vocabulary value fits an official free release. Flagged to the user as a possible vocabulary gap. Its `system` still asserts.
- **Heads Up! — everything** — absent from the maker's live games index and store; no citable evidence without a Wayback hunt nobody has done yet.
- **game_format on Cannon Lagoon and the add-on games** (Barnyard, Hoopin', Lexy SAS, ROCs, Shoot 'n Scoot, Sorcerer's Apprentice) — no source states a genre, and several are visibly not flipper pinball (Cannon Lagoon is timed cannon-lane play). Grand Slam Rally is the exception: the maker's own "Pitch-and-Bat on the P3!" → `pitch-and-bat`.
- **cabinet/display on add-on games** — they are software running on another game's module; the fish-tales conversion-kit rule keeps donor hardware off them.
- **descriptions** — ride the `flipcommons-ai-desc-model` attribution, a separate patch by convention; the DCC↔EG shared-design fact waits there and in this doc.
- **The TPB launch post's per-edition feature matrix** — an image, untranscribed; edition-differentiating equipment claims would need `web_import.py --text-file` first.

## Decided

- **Credit role mappings (2026-08-13)**: Creative Director and Rules → `design`; Cabinet Artist / Playfield Artist / Art Direction / Technical Artist / Sculpts → `art`; "Music and Sound Design: Matt Kern" → `music` + `sound`. Sculpts credit goes to the person (Davey Price, named by Pinball News) not the studio (Stumblor); Renegade Game Studios (Digital Assets) and Playmates Toys (Special Thanks) are companies with no person to credit — skipped.
- **"Tyson and Eli Silver"** in EG's Voices line are two people, each credited.

- **Scope**: 2026 two full + platform sweep (user, 2026-08-13).
- **No chassis model; no missing-game creation** (user, 2026-08-13).
- **System**: reference existing `multimorphic-p3-roc` on all 22 models, cited to the maker's hardware-control-system page.
- **`production_status`**: DCC/EG `announced` ("Production of this title begins in late 2026", deposits only). Sold-from-stock older games `produced` via the store category listings; Portal via the June 2026 update; TPB and Weird Al via their launch posts.
- **No month on the 2026 two (user, 2026-08-13)** — `month` is the manufacture date per DataPatchAuthoring.md; the announcement date is not evidence for it. 0229's announcement-month claims were removed under the same ruling.
- **DCC↔EG shared design** — no relationship type fits; recorded here and deferred to the future descriptions patch. Candidate for a future relationship vocabulary value.

## Future unique features

- DCC: the rotating clear disk mech (curved 7-target bank + ball cannon + 183 RGB LEDs, slip-ring wiring), SlingLocks (a.k.a. StevieStops) inlane ball stoppers, Mongo Cage (cover-lifting 6-target arena with disruptor magnet), MANA ball-stacker level indicator, Safe Room scoop, Princess Donut magnet ball lock.
- Ender's Game: the same disk mech and SlingLocks, Captive Ball Balance Mech, Fight Ring (same arena hardware as Mongo Cage, differently themed), Valentine/Peter ball stackers, Projected HUD.

## Gate runs

- **2026-08-13 verbatim**: 0 failures on the first emit (all 0231 quotes verified; no SKIP-PDF — every source is HTML).
- **2026-08-13 support** (95 claims, ~442k tokens): 2 warnings. `portal-extended production_status` — fair catch that "all 2025 Portal orders" doesn't name Extended; folded in a note (Extended is an ordering option of the same launch) plus PN's "Portal's extended option" quote. `weird-al LE player_count` — the carry ladder's base value wasn't named; note now says OPDB supplies the base's 4. Kept both claims; not re-run per RULEBOOK.
- **2026-08-13 editorial lint, first emit**: 40 wording findings (banned phrases "the existing catalog", "No source", "maps to", "vocabulary", "entity" in notes) — all reworded, second emit clean.
- **2026-08-13 post-restructure**: after the hand-restructure (splits + note deletions, including new tighter FAQ spans for cabinet/format/display), verbatim re-ran clean (0 failures repo-wide) and both fast gates pass.
- **2026-08-13 snapshot apply**: 0231 applied cleanly (0214 snapshot + patches through 0232). 187 field-level citation instances landed; sweep fields, DCC/EG credits (17/23) and features (15/13) verified. Ingest stopped at 0233-ramps-pinball, which `create`s person.glenn-waechter — already created by 0231 (he is credited on both Ender's Game and a Ramp's title). That collision is the ramps session's to fix (reference, not create).
