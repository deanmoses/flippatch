# Vector Pinball — family notes

Session start 2026-08-13. Patch number claimed: **0234** (`patches/0234-vector-pinball.yaml`). Not part of 0215's original list — added by user request: Vector released new models in 2025 and the catalog holds them bare.

## The maker

Vector Pinball is a division of **Vector Synergy Pty Ltd**, ABN 82 660 426 344, based in **Brisbane, Australia** (per its own /about and /contact pages — first-party identity evidence). Owner **Jason McNally**, with son **Blake McNally** making up the management. Custom-pinball builder since 2016 (separate division site `custompinball.com.au`); moved to original-title quantity production in 2023 with Eight Ball Fury. All games are "Retro-Classic" style: plywood cabinet, alphanumeric display, no video screen. The `vectorpinball.com` citation root **already resolves** — no root work needed for the maker's own pages.

## The lineup (maker's own numbering, from the homepage carousel)

| # | Model | Catalog? | Units | Licence | Status evidence |
| - | ----- | -------- | ----- | ------- | --------------- |
| 1 | Eight Ball Fury (+ "Pub Edition" carousel entry) | yes (2024) | 50 | original theme | selling since 2024 |
| 2 | Peter Brock KOTM — Torana + VK Commodore editions | yes ×2 (2025) | 105 total across both | Peter Brock & HDT | shown AGE Aug 2024 (AUSRETROGAMER) |
| 3 | Holden Heritage | yes (2025) | 100 | GM Holden | gallery photos Nov–Dec 2024 |
| 4 | Ned Kelly | **no — create** | 100 ("Very Limited Edition") | none (historical figure) | "now available to purchase" (page mod 2026-07-23) |
| 5 | Lost in Space | **no — create** | 300 | Legend Pictures LLC, licensed by Synthesis Entertainment | announced TWIP 2025-09-25, debut Melbourne Pinball Expo Nov 2025, "available now" 2026 |

## Evidence inventory (all cached 2026-08-13 unless noted)

**Maker site — the primary document set.** No PDFs exist anywhere on the site (swept every cached page with `links --ext pdf`); the rules/features/specs pages ARE the spec sheets. Every model has: intro page, gallery, and a dense "Game Rules, Features & Specs" page carrying flipper/pop/target counts, LED counts, display, dimensions, weight, power, trim options, topper, shaker.

- `https://vectorpinball.com/` — homepage; carousel with maker's game numbering incl. "Game # 1 – Eight Ball Fury – Pub Edition" as a separate entry
- `/about` (cached 2026-06-11) — company story, McNally credits, Brisbane, ABN
- `/contact` — Brisbane, ABN, US contact number; enquiry dropdown lists exactly 6 games (both Brocks separate; no Pub Edition)
- `/support` — support form only, no downloads/manuals section
- Per model: `/eight-ball-fury-specs` + `/eight-ball-fury` (gallery) + `/eight-ball-fury-rules-features` (Version 3 game code); `/peter-brock-king-of-the-mountain-pinball-games` + `-game-rules-features-specs` + `/peter-brock-torana-edition` + `/peter-brock-commodore-edition`; `/holden-pinball-games` + `/holden-heritage-edition-gallery` + `/holden-heritage-edition-game-rules`; `/ned-kelly` + `/ned-kelly-pinball-gallery` + `/ned-kelly-pinball-game-rules-features-specs`; `/lost-in-space` (redirect target of `lostinspacepinball.com`) + `/lost-in-space-the-pinball-photo-gallery` + `/lost-in-space-the-pinball-game-rules-features-specs` (Code Version 1.0)

**Maker YouTube** (channel UCufbyvLyRugy9B5QHvjJraw): cached transcripts for Peter Brock "Basic Game Features" (D8otJvdEJYM), Holden Heritage "Rules and Features" (sJGfJBNpLUg) and "Gameplay" (aOUUtBD-H3M). Peter Brock "General Game Play" (q3u4TWC_hHs) has **no captions** — nothing quotable.

**Journalism:**

- AUSRETROGAMER 2024-08-20 (`ausretrogamer.com/peter-brock-king-of-the-mountain-pinball-machines/`) — both Peter Brock models at AGE (Aug 13–15 2024) on Big Top Amusements' booth; AU$11,900 launch price; reprints the maker's feature list
- TWIP "Funkatron Mix" 2025-09-25 (`twip.kineticist.com/p/funkatron-mix`) — Lost in Space announcement: "based on the 1965 classic sci-fi television series", "set to make its debut at the Melbourne Pinball Expo this November"

**Crowdsourced (research only, never sole support):** Kineticist game pages (cached) — Peter Brock/Holden page states the two titles share one playfield layout, credits Design: Jason McNally, Art: Peter Hughes + Jeremy Ham; EBF page credits Design: Jason McNally, Art: Jeremy Ham. Kineticist manufacturer page listed only 2 games as of April 2026 (LIS/NK not yet indexed).

**Distributor listings (cached as volatile backups, superseded by maker pages):** Highway Entertainment LIS listing, Smack Amusements Ned Kelly listing.

## Traps and observations

- **The two "Peter Brock / Holden platform" spec sheets are near-identical** (3 flippers, 6 drops, 1 spinner, 3 pops, captive car shot, 139 LEDs, same dimensions) — Holden Heritage is a re-theme of the Peter Brock playfield. Kineticist says this outright; OPDB encodes it by giving all three models one group+machine id (`Ge1O1-MYeEB-*`, alias-level split).
- **Maker game numbering vs catalog structure**: Peter Brock editions are Game #2, Holden Heritage Game #3, yet the catalog has both Brocks `variant_of` Holden Heritage. See "Open structure questions".
- Eight Ball Fury's platform differs meaningfully (2 flippers, horseshoe, 157 LEDs, countdown timer, 204cm height) — not the same playfield as #2/#3.
- Ned Kelly's platform is close to Brock/Holden (139 LEDs, same dims) but 2 flippers, 4 pops, gun-grip shooter, rebound switch — a derived but distinct layout; Vector calls it "the next in our Aussie Icon series".
- Lost in Space is a bigger departure: 4 flippers, 3 spinners, 3 pop bumpers, dual captive ball, 14 static targets, TV feature under the playfield, 1 triple + 3 single drop targets.
- **Trim finishes are options, not editions** — every model offers two trim finishes at the same price (EBF: Black Satin/Chrome — its gallery calls them "Editions"; Holden: Chrome/Black Satin; NK: Rustic Iron/Satin Black; LIS: Satin Black/Gloss Blue Metallic; Brock: two art packages = the two actual catalog models). Only the EBF "Pub Edition" homepage entry might be a real edition — see open questions.
- The site's own text misspells "Holen" in the homepage carousel; don't quote that span for a name claim.
- AUSRETROGAMER's feature list says "2 & 3 ball Multi Ball modes" where the maker's page says "2,3 & 4" — the reprint drifted or predates code updates; prefer the maker page.
- Dates: EBF `month=1` in the catalog is an OPDB artifact (every Vector model carries OPDB `month: 1`), not evidence.

## Sought and not found

- **PDFs / flyers / manuals**: none exist on the site (all pages swept for pdf links; /support has no downloads).
- **Lost in Space & Ned Kelly YouTube video ids**: the model pages link only to the channel; the channel /videos page is JS-only (no extractable list) and web searches surface only Sega-1998 content. The two models' feature videos exist per the pages but are unlocated.
- **Person credits in a primary source**: no person is named on any maker page except Jason & Blake McNally on /about (management, not per-game credits). Kineticist's design/art credits (McNally; Hughes; Ham) have no first-party corroboration found yet. Peter Hughes is independently a famous Holden factory artist (v8sleuth interview, print shops) which makes the attribution plausible — but plausible ≠ cited. Candidate recovery: art signatures in gallery photos (not yet inspected at zoom).
- **Pinball News / Arcade Heroes coverage**: none found for any Vector title.

## Open structure questions (for the user)

1. **Variant direction on the Brock/Holden platform**: catalog has Torana + VK Commodore `variant_of` Holden Heritage. Maker numbering (Brock=#2 first, Holden=#3 later), AUSRETROGAMER (Brocks at AGE Aug 2024), and gallery photo dates (Holden Nov–Dec 2024) all say Peter Brock came first and Holden Heritage is the re-theme. The Brock editions are two art packages of one game (105 builds *total across both*), i.e. genuinely each other's peers.
2. **Eight Ball Fury "Pub Edition"**: a separate homepage carousel entry, but no page of its own and absent from the contact form's game list. Likely the alternate-backglass trade dress. Create or ignore?
3. **Lost in Space and Ned Kelly creates** — user pre-approved creating well-sourced missing models (2026-08-13).

## Decisions (user)

- 2026-08-13: family joins the 0215 campaign folder; missing Vector models get created in 0234.
- 2026-08-13: **variant structure stays as-is** (both Brocks `variant_of` Holden Heritage) despite the maker-numbering evidence — recorded in "Open structure questions" above, no structural claims in 0234.
- 2026-08-13: **Peter Brock year corrected to 2024** — asserted over OPDB's 2025, cited to AUSRETROGAMER (AGE retail, Aug 2024) + the maker's About page ("2024 brought more new titles").
- 2026-08-13: **EBF "Pub Edition" not created** — treated as the alternate-backglass trade dress; homepage carousel entry only, no page of its own, absent from the contact form's game list.

## Not asserted (and why)

- **Per-model `production_quantity` on the Peter Brocks** — the 105-build run is total across BOTH art packages; no per-model split exists to assert.
- **`limited-edition` tag on the Peter Brocks** — already set by 0206 under the same actor; an exact duplicate is silently swallowed along with its citation.
- **Credits on Ned Kelly and Lost in Space** — no source names anyone for these two (Kineticist hadn't indexed them as of April 2026).
- **`player_count` everywhere** — no primary source states it; EBF carries OPDB's 4.
- **Months everywhere** — OPDB's `month: 1` rows on every Vector model are an ingest artifact, not evidence; no source dates a release to a month.
- **Descriptions** — a follow-up patch's job (inline-cite rules), per the campaign norm.
- **Lower rollover lanes ("B A L L", "K I N G", "G U N S", "C A R S", "S-H-I-P")** — no confident vocab mapping (could be inlane/outlane rollovers, unstated); only the counted `top-lanes` attach.
- **"Ball gate with Lift Control (top left)"** (Brock/Holden/NK platform) — no confident vocab leaf for it.
- **EBF countdown timer under playfield** — recorded as a future unique feature instead.
- **Holden Heritage year** — stays 2025 (catalog); gallery photos are from Nov–Dec 2024 (likely MPE 2024) but no source states a release date.

## Apply loop (2026-08-13, snapshot db.prod.patch-0214.2026-08-03)

Three apply-time failures the structural gates can't see, each fixed by regenerating:

1. **Credits need their people to exist** — `relationship 'credit' member 'jason-mcnally' does not resolve to a Person`. People new to the catalog are created in the same patch (`person.<slug>`, create + name), the 0233 pattern. Promoted to RULEBOOK → Asserting claims.
2. **A journalism cite needs its outlet rooted** — `ausretrogamer.com` had no citation root; added as a single-family web root in 0234's own `sources:` block. (`twip.kineticist.com` resolved for free — TWIP already has its own root.)
3. **The ordered apply stops at 0233** — `0233-ramps-pinball` fails on a `person.brad-albright` create collision (that person now exists in the shared DB, so 0233's baseline is stale — the ramps session needs to know). 0234 was validated by applying it alone from a staging directory on top of the 0215–0232 state; a full-directory replay still needs 0233 fixed first.

Applied clean: 125 entries, 1 citation source created. Verified via `make analyze`: all six Vector rows carry status/format/display/generation/cabinet, quantities 50/100/100/300, Brock years now 2024, 23–28 features per model, credits on four models, corporate entity located at `australia/qld/brisbane`, and `patch_entry_cites` shows 151 evidence rows across the Vector Pinball, Kineticist, AUSRETROGAMER and This Week in Pinball roots.

## Gate runs

- 2026-08-13 `make validate`: first emit failed the editorial lint on note wording (process language: 'sought', 'none found', 'at authoring time', 'No source', 'entity', 'seeded', 'user-approved'); notes rewritten as public prose, then clean.
- 2026-08-13 `make verify-quote-verbatim`: 0 failures for 0234 on first pass (all quotes lifted verbatim from cache extractions, typographic punctuation preserved).
- 2026-08-13 `make verify-quote-support ARGS="0234"`: 119 claims, 631k tokens, 11 warnings, triaged:
  - **ball-save ×5** — checker rejects the minimum-play-time = ball-save equivalence. KEPT: a drained ball auto-returned within a time window is a ball save; note rewritten to describe the mechanic.
  - **numbered-plaques ×3** — "build plate isn't a gameplay feature". KEPT: presentation features are vocabulary by charter (0218), and Stern's sequentially numbered LE plaques attach the same node (0220). Note added.
  - **VK Commodore counts** — fair provenance catch: the spec sheet covers both Brock editions but the cite didn't say so. FOLDED IN: sheet-scope note added to both Brocks' platform entries.
  - **Brisbane location structure** — standard structured-fields warning every location create draws (0225 shipped the same shape). KEPT.
  - Not re-run after the note fixes (a clean pass is not the goal).

## Future unique features (for the coming UniqueFeature entity)

- LIS: "TV Feature Under the lower playfield, displays video snippets from the show relevant to the game play"; 3D Plastic LED-animated topper; force-field mystery award
- NK: gun-grip ball shooter (standard shooter optional); hand-made 1/3-scale metal Ned Kelly helmet topper option ($990/$900, subject to availability)
- EBF: illuminated 3D Flame Topper; 2-digit countdown timer under playfield for challenge modes
- Brock/Holden: Captive Car shot (captive-ball with car figure); build plate + licence certificate
