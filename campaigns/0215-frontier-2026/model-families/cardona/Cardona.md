# Cardona family — campaign notes

Patch: `patches/0242-cardona.yaml` (number 0242 assigned by the user 2026-08-15, filling a skipped number; one patch for the whole maker). Four models: **No Good Gofers: Battle for the Green** (Cardona Pinball Designs kit, to create), **Black Rose: Skull & Bones** (Cardona Pinball Designs kit, to create), and their donors **No Good Gofers** (Williams, 1997, `ipdb:4023`?) and **Black Rose** (Bally, 1992) — both already in the catalog, both to enrich.

Predecessor family: [fish-tales](../fish-tales/FishTales.md) (0225 + 0230, shipped) — the Cardona citation root (path-scoped `img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3`), the Cardona corporate entity (Pennsville NJ), the `fast-pinball` system + FAST Pinball manufacturer/corporate-entity, and the conversion-kit ruleset all shipped there. This family cites the root; it does not re-declare anything.

## Scope decisions (user, 2026-08-15)

- **One patch, number 0242** for both kit families plus donor enrichment.
- **Demolition Time is not created** — Cardona's 2014 firmware ROM rewrite for Demolition Man (FreeWPC, free download; Pavlov Pinball 2014-05-10 "Completing the code") is alternate software, not a machine or kit.
- **The unannounced fourth title is not created** — under contract per the Kineticist interview ("I have one more title in my pocket"), but unnamed anywhere; nothing to assert.
- **Donor enrichment: prefer non-IPDB sources where cheap to acquire, in addition to citing IPDB** — the catalog is trying to broaden past IPDB-centrism. Planetary Pinball (root shipped in 0217) and the Williams/Bally document publisher roots (0227) are the obvious lanes.
- **Snapshot baseline**: `db.prod.patch-0238.2026-08-13.sqlite3` (RULEBOOK recipe updated).

## Baseline survey (2026-08-15, dev DB = prod-0238 snapshot + in-flight 0239–0250)

| field | no-good-gofers (1997) | black-rose (1992) |
| --- | --- | --- |
| credits | 8 (ipdb + catalog): design Lawlor + Koziarz, art Youssi, animation Rhine, mechanics Krutsch, music/sound Pontarelli, software Koziarz | 9 (ipdb + catalog): design Eddy + Trudeau, art McMahon, animation Slomiany, mechanics Pizarro + Krutsch, music/sound Heitsch, software Eddy |
| display_type / system | dot-matrix / wpc-95 | dot-matrix / williams-wpc-fliptronics-2 |
| year / month / player_count / production_quantity | 1997 / 12 / 4 / 2,711 | 1992 / 7 / 4 / 3,746 |
| manufacturer_model_identifier / abbreviation | 50061 / NGG | 20013 / (none) |
| gameplay_feature | 11 (ipdb): flippers ×3, pop-bumpers ×3, ramps ×3, slingshots ×2, spinning-targets ×2, spinning-discs ×1, captive-ball ×1, kickback, left-outlane-kickbacks, left-dual-inlanes, newton-ball-posts ×1 | 7 (ipdb): flippers ×3, pop-bumpers ×3, ramps ×3, 3-bank-standup-targets ×3, ball-cannons, lockdown-bar-buttons, 3-ball-multiball — **no slingshots row** (the IPDB-notable-line staples gap 0230 documented) |
| theme | golf, sports | fantasy, fictional, pirates |
| ipdb_toys | Beaver bash toys (2) | (none) |
| production_status, game_format, cabinet, description, tag | all unset | all unset |

The two kit models do not exist under any name or slug ILIKE match. Persons `james-cardona`, `brian-allen`, `jada-holmes` (0225), `scott-gullicks` (P3 credits: art on Lexy Lightspeed, Cosmic Cart Racing, Wrath of Olympus), and `aaron-davis`/`dave-beecher` (in-flight 0247) all exist — **no person creates needed unless a new voice actor surfaces**. The FT kit's relationship row is the shape to mirror: `conversion_kit / licensed / fish-tales`. Unrelated but adjacent: `mega-golf-ball-frenzy` (2006) and `ultimate-golf-ball-frenzy` (2007) are third-party `conversion` edges into no-good-gofers — not Cardona, no overlap.

Duplicate scan ran against `model_claims` (active claims, both donors) — the table above is what other actors already assert; everything the patch adds must be checked against it, not against `patch_claims`.

## Evidence inventory

### First party (Cardona)

- **Live shop product pages** — cached 2026-08-15, `--render`: `https://cardonapinball.com/shop/ols/products/no-good-gofers-battle-for-the-green-upgrade-kit` and `.../black-rose-skull-and-bones-20-pinball-kit`. The OLS store's body is JS, but each page's **meta description carries the complete product copy** (quotable per RULEBOOK → meta descriptions): kit contents (speaker/display panel with the industrial 15.6-inch monitor, FAST interface controller, CPU panel with FAST audio, power supply; BR adds a translite), the full story copy, NGG's whole mode roster with two wizard modes, the licensing paragraph ("Cardona Pinball Designs is licensed by Planetary Pinball Supply to create 2.0 game kits for Bally-Williams titles"), show history, and each kit's official video URL list. The NGG page's description also embeds the BR "About" text — one store-wide blob, quote what you need.
- **Change-log PDFs** (wsimg, same 0225 tenant path; cached under the bare URLs, no `?ver=`): `NGG rev changes 2025 06 01.pdf` — "version 20221215 … First commercial release" (all text on PDF page 1); `BRose 20250610 change log.pdf` — "Black Rose: Skull and Bones / version 2023_06_22 … 1st production release", plus FAST hardware IDs ("sound board ID: EMU FP-CPU-1060 / fast controller ID: NET FP-SBI-0095 02.5") (single page).
- **Archived 2023 static pages** (Wayback, gzip-trap recovery — see Traps): `cardonapinball.com/ngg` and `/br` (snapshots 2023-05-31), headed "A Licensed "2.0" Upgrade Kit by Cardona Pinball Designs", with the stronger 2023 license wording **"licensed by Williams Electronic Gaming and Planetary Pinball Supply"**, kit contents (NGG names "Flipper Fidelity" speakers), beta locations (NGG at The Pinball Gallery, Malvern PA and the Delaware Pinball Collective "since September 2020"; BR at DPC "since 2022"), and show lists. `/ngg-videos` and `/br-videos` also cached.
- **Teaser videos** (auto-captions, cached): NGG `youtube:_4bWVwbZb6c`, BR `youtube:vZGUFB7W32A` — in-game audio only, atmosphere not specs; research color.
- **YouTube channel page** (`@CardonaPinball/videos`, cached, rendered): About text "our '2.0' upgrade kits that are now available for No Good Gofers and Black Rose pinball machines"; the old `/products/ols/` store URLs it links are dead (404) — see Traps.

### Licensor's store

- **Planetary Pinball NGG kit listing** (`merchant.mvc?Product_Code=PPM-KIT-NGG-BATTLE`, cached) — PPS is the licensor selling the kit itself (RULEBOOK → licensor's own store): full hardware inventory matching the maker's copy, $2,000, "Out of Stock", the 120v USA-only note, and the "Gofer Motion" Topper expansion. Its related-products row surfaces a Whirlwind 2.0 "Total Chaos" kit (EPC/Pedretti) — out of family scope, noted for a future campaign.

### Journalism

- **Kineticist interview** (cached, 0225's source) — names the full lineup and order ("from No Good Gofers to Black Rose to Fish Tales"), the P-Roc→FAST recode ("I had only written No Good Gofers: Battle For The Green and developed the game for P-Roc hardware"), the release framing ("when we finally released No Good Gofers: Battle For the Green"), **"I hired Scott Gullicks to do my Black Rose artwork"**, the 2.0-kit category definition (game_format lane), the four-title license contract, and the BR story details.
- **Pinball News Expo 2023** (cached) — "Cardona Pinball Designs were showing their two 2.0 kits – No Good Gofers: Battle for the Green and Black Rose: Skull & Bones" (photo captions; note PN's "&" spelling).
- **Pinball Profile ep. 386** (2024-01-17, cached) — audio-only podcast page, no transcript; research context.

### Structured rows

- **`ipdb:4338`** (No Good Gofers 1997) — Notable Features line (game_format lane), `Production: 2711`, a **full dimensions block** (Height/Width/Depth/Weight → `cabinet: floor` from the row itself, no manual needed), `Toys: Beaver bash toys (2)` (not yet attached as a feature), and the Notes voice credit line **"Voices of Jon Hey as Bud and Vince Pontarelli as Buzz."** — both persons already exist.
- **`ipdb:313`** (Black Rose 1992) — Notable Features line naming the Broadside VUK, the center habitrail, and the mechanically raised/lowered left ramp (all with generic vocab leaves: `vertical-up-kickers`, `habitrails`, `moving-ramps`), `Production: 3746`. **No dimensions block** — BR's cabinet stays unasserted. Ed Boon is explicitly disclaimed in the Notes (video at Midway), not a credit.

### Crowdsourced (research-only, never cited)

- **Pinside pages** (cached): NGG kit `pinside.com/pinball/machine/ngg-battle-for-the-green` (PinsideID 3197, "February 2023", $2000, design team all-Cardona + Davis/Beecher electronics); BR kit `.../black-rose-skull-and-bones` (PinsideID 3198, "August 2023", $2200, adds **Eli Curtz software** and Scott Gullicks artwork). Dates conflict with the maker's own change logs — maker wins, see Decisions.
- `draft-evidence-aggregator.csv` has no rows for either kit.

## Traps

- **Carried from fish-tales**: Cardona's documents live on GoDaddy's shared `img1.wsimg.com` CDN — citable only through the 0225 root's path-scoped domain (same tenant id `4bd466e8-…` verified on the BRose/NGG change-log URLs, 2026-08-15). Auto-captions misspell titles ("No Good Gophers", "Fishtails"). Livestream-style videos without captions cache nothing.
- **The OLS store body is JS, but the product page meta description carries the full copy.** FishTales.md recorded "no per-product page found"; the pages exist at `/shop/ols/products/<slug>` (the store moved there from `/products/ols/products/` — the old URLs, still linked from the YouTube channel About, 404). The `/downloads` page's wsimg links carry a `?ver=` query — **cite and cache the bare URL without it**, matching 0225's refs (the first fetch here cached the `?ver=` form; both PDFs were re-fetched bare).
- **Wayback stores the 2023 cardonapinball.com captures gzip-compressed** — `id_` fetches returned raw gzip bytes (clean 200, "(no title)", binary text). Recovered per RULEBOOK: `curl -sL | gunzip -c`, then `web_import.py --force` under the snapshot URL. Applies to `/ngg`, `/br`, and the archived product pages.
- **`person.aaron-davis` and `person.dave-beecher` are created by in-flight 0247** — 0242 applies before it numerically but must not re-create them if it ever cites them (it currently doesn't).

## Decisions

- **Kit names: "No Good Gofers: Battle for the Green (Kit)" and "Black Rose: Skull and Bones (Kit)"** — the FT kit's "(Kit)" suffix pattern. "Skull **and** Bones" per the maker's own change log and Pinside (PN wrote "&"). "Battle **for the** Green" uses standard title casing (Pinside, PN); the maker's own copy title-cases "For The" — recorded here, flagged to the user.
- **Kit months from the maker's own release histories** — NGG `month: 12`/`year: 2022` ("version 20221215 … First commercial release"), BR `month: 6`/`year: 2023` ("version 2023_06_22 … 1st production release"). Pinside says February 2023 / August 2023 — crowdsourced, and the FT precedent (maker's release history beats later framing) applies. Slugs mirror FT: `no-good-gofers-battle-for-the-green-kit`, `black-rose-skull-and-bones-kit`; each kit gets its own Title node like FT's.
- **Kit ruleset carried from 0225/RULEBOOK** — `conversion_kit` edge + `license_status: licensed` (product pages: "A Licensed "2.0" Upgrade Kit"; archived 2023 wording "licensed by Williams Electronic Gaming and Planetary Pinball Supply"), `production_status: produced` not aftermarket, no donor credit carry, no donor hardware facts on the kits, `system: fast-pinball` + `technology_generation: solid-state`, `display_type: lcd` (each kit's industrial 15.6-inch monitor).
- **NGG donor `cabinet: floor` from the IPDB row's own dimensions block** — ipdb:4338 prints Height/Width/Depth/Weight, so the 2026-08-12 classification-from-dimensions ruling applies without a manual. BR's row has no dimensions → cabinet unasserted.
- **NGG donor voice credits ×2** (Jon Hey as Bud, Vince Pontarelli as Buzz) from the ipdb:4338 Notes line — the FT 1992 voice-credit pattern; both persons exist.
- **Donor feature additions stay inside the quotable Notable/Toys lines**: NGG `bash-toys ×2` (Beaver bash toys); BR `vertical-up-kickers ×1` (Broadside VUK), `habitrails ×1`, `moving-ramps ×1` (mechanically raised/lowered left ramp). All existing generic leaves; nothing new coined.

## Sought and not found

- **Voice actors for either kit** — the product pages say "we also use several artists and voice actors for content creation" and the interview says professionals came "with each title", but nobody is named for NGG or BR anywhere first-party or journalistic (Jada Holmes is FT-only). Not asserted.
- **Kit production quantities and player counts** — no first-party statement.
- **An NGG kit artist** — the archived /ngg says backglass art was commissioned ("we have contacted an industry leading artist… as an upgrade option") but names nobody; the kit itself shipped without new art. Nothing to assert.
- **NGG/BR kit flyers or spec sheets** — none exist; the product pages and change logs are the maker's documents.
- **Black Rose donor slingshots and other IPDB-staple gaps** — the staples live in the manual's switch matrix (the 0230 route); BR's manual and handbook are IPDB-only (403), and DocumentsAudit's hold on browser-driven IPDB acquisition stands. Recorded for whoever reopens the family.

## Not asserted (and why)

- **Eli Curtz (BR software, Pinside-only)** — he is FAST Pinball's own software person (fastpinball.com/about team list), so the row reads as platform-level contribution; no citable source credits him on the game. Same reasoning as Aaron Davis on FT.
- **Aaron Davis / Dave Beecher electronics (both kits, Pinside-only)** — `electronics` is not a credit role; the FAST facts live in the system/manufacturer nodes (0225 ruling).
- **James Cardona animation/sound/music/callouts on the kits (Pinside-only role splits)** — the asserted design + software rest on Kineticist's "He writes the code, designs the games"; the rest matches the FT ruling (animation "muddling through" too oblique to credit).
- **Kit `cabinet`** — a kit installs into the donor's cabinet; asserting the donor's form factor on the kit would double-count donor hardware (0225 rule).
- **`description` for any model** — campaign scope, matching every prior family.
- **NGG kit mode roster / wizard modes** (19th Hole, Sorcerer, etc.) — rules content, not mechanism vocabulary; `multiball` is asserted from the mode list's own "multiball mode" wording.
- **NGG kit's "Gofer Motion" Topper and BR's interactiveTopper** — optional expansion accessories, not shipped kit hardware.
- **BR kit gameplay features** — the BR product copy carries story, not mechanisms; nothing quotable.
- **Ed Boon on Black Rose** — the IPDB Notes explicitly disclaim it.
- **Show/beta history, prices, 120v note** — preserved in the quotes and this file; no catalog fields.

## Future unique features

- **NGG 1997**: the two beaver bash toys; ramp entrances that elevate to expose the bash targets; the removed pop-up gopher of the whitewood/prototypes (IPDB Notes).
- **NGG kit**: "Gofer Motion" Topper expansion; drives/putt-out golf scoring system.
- **BR 1992**: Broadside below-playfield oscillating ball cannon fired from the lockdown-bar Fire button; mechanically raised/lowered left ramp that loads the cannon.
- **BR kit**: interactiveTopper expansion; new translite in the kit.

## Gate-run history

- **2026-08-15 `make validate`**: structural pass; one editorial catch (patch description over 80 chars), fixed and re-emitted.
- **2026-08-15 `verify-quote-verbatim`**: 157 verified / **0 failed** on the first emit; the 6 wsimg PDF cites report `SKIP-PDF` (quotes transcribed directly from the extracted text). Every HTML/meta/ipdb span was pre-checked with `web_cache.py quote` / `make show-source --check` before emitting.
- **2026-08-15 `verify-quote-support 0242`**: **did not run** — the Anthropic API key's credit balance is too low (`Your credit balance is too low to access the Anthropic API`). Run it once credits are topped up; triage per RULEBOOK → Operating the quote gates.
- **2026-08-15 snapshot validate**: restored `db.prod.patch-0238.2026-08-13.sqlite3`, migrated, applied all 8 in-flight patches cleanly (0242 included; left applied). Verified through the foundation: all four models resolve every asserted field, both `conversion_kit / licensed` edges present, kit credits (Cardona ×2 each, Gullicks on BR), NGG donor voice credits, features (NGG `bash-toys ×2` + `moving-ramps`, BR `moving-ramps`/`vertical-up-kickers`/`habitrails`, NGG kit `multiball`), themes on both kits, and `patch_entry_cites` shows every cite resolved to its root (Cardona / Kineticist / IPDB).
