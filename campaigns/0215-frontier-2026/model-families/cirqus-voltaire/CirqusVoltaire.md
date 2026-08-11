# Cirqus Voltaire family — campaign notes

Patch **0223** (`patches/0223-cirqus-voltaire.yaml`). Session started 2026-08-10. Family: `cirqus-voltaire-remake` (American Pinball, 2026, created by 0215) + `cirqus-voltaire` (Bally, 1997, seeded).

## User rulings

- **Carry creative credits to the remake** (2026-08-10): the original's creative credits (design, art, animation, music, sound) carry to the remake per the Medieval Madness Remake seed pattern, citing the original's evidence with a note. AP's own new credits get asserted from AP sources as found. See the open question below about the art-credit nuance the Ringmaster Edition raises.
- **Ask before each snapshot rebuild** (2026-08-10): the galactic-tank-force session shares the flipcommons dev DB concurrently, so every snapshot restore/replay gets user clearance first. Research, authoring and `make validate` proceed freely.

## Baseline survey (2026-08-10, dev DB at 0221)

| field | cirqus-voltaire (1997) | cirqus-voltaire-remake (2026) |
| --- | --- | --- |
| year / month | 1997 / 10 (IPDB) | 2026 (0215) / — |
| corporate_entity | Bally (seed) | american-pinball-inc (0215) |
| theme | circus, carnivals (seed; not redundant — siblings under circus-carnival) | circus, carnivals (0215) |
| production_status | — | — |
| game_format | — | — |
| technology_generation | solid-state (seed) | — |
| display | dot-matrix (seed; no subtype) | — |
| system | wpc-95 (seed) | — |
| cabinet | — (campaign convention: not asserted, vocab is form-factor) | — |
| player_count | 4 (IPDB+OPDB) | — |
| production_quantity | set (IPDB) — **do not re-assert** | — |
| credits | 11 (IPDB + Flipcommons Catalog ×11 each) — **do not re-assert** | — |
| gameplay features | 7 counted (IPDB): flippers ×2, pop bumpers ×3, slingshots ×2, standup targets ×9, kick-out holes ×2, spinning targets ×2, stop magnets ×3 | — |
| description | — | — |
| lineage | — | — (remake_of open) |
| tag / rewards | — | — |
| ipdb / opdb | 4059 / GRVjJ-MLq7W | — |

Duplicate-scan done against `model_claims` (actors: IPDB, OPDB, Flipcommons Catalog). The IPDB actor already claims the original's credits, month, player_count, production_quantity, system, technology_generation, theme, gameplay features — none of these may be re-asserted on the original.

## Evidence inventory (all cached in the pinexplore web cache)

### Remake (American Pinball, 2026)

- **`https://americanpinball.com/cirqus-voltaire-announcement`** — AP's own announcement, published 2026-05-16 (article:published_time), modified 2026-07-20. One paragraph: "American Pinball is proud to announce that we are bringing the legendary Cirqus Voltaire back to life for a new generation of players … carefully reimagining this iconic machine with modern craftsmanship and exciting new surprises." Meta description: "American Pinball is remaking Cirqus Voltaire". Supports: `production_status: announced`, `remake_of`, description material. **No specs, no editions, no credits, no dates.**
- **`https://americanpinball.com/coming-soon`** — CV is the only machine on it, as an image (`Cirqus-Green-BG-HD`), no text. Corroborates announced-not-produced; nothing quotable.
- **`https://sdamusements.com/products/cirqus-voltaire-ringmaster-edition`** — distributor (Shopify) pre-order listing, the only fetchable page carrying edition detail: "RINGMASTER EDITION (Limited to 772 units)" with a feature list — New Brian Allen full Art Package (Playfield, Cabinet, Plastics & Backglass), Custom Sculpts, New Scrolls that light up with Interactive Topper, Updated Code with Remastered Sound & Video, LCD Screen, Custom Powder Coating, Custom Shooter Rod, Magic Glass, Shaker & Knocker. Distributor-authored copy, presumably from AP dealer materials AP has not published. **Citing it would need an sdamusements.com citation root — see open questions.**

**Sought and not found (remake):** AP support pages/HubSpot host carry no CV documents (inventory floor 2026-08-06 confirmed, re-checked via site nav 2026-08-10). AP's store has no CV listing. AP's YouTube channel has no CV video. No dedicated Pinball News / Arcade Heroes / Kineticist article found — coverage is forum threads and distributor listings only. Pinside thread reports "Price, details and options have not been discussed by American Pinball at this time".

**Found but uncacheable (research-only):** CoinTaker "CIRQUS VOLTAIRE REMAKE: STANDARD EDITION DEPOSIT" and Great American Pinball "Cirqus Voltaire LE" (both 404 to our fetchers, plain and rendered — bot-blocked); Nitro Pinball "COMING SOON" listing likewise. Together with SD Amusements they imply an edition structure (Standard / Ringmaster / LE?) that AP itself has not announced.

### Original (Bally, 1997)

The licensed Williams/Bally official CV site survives on Planetary Pinball (root seeded by 0217). All cached:

- **`…/mm5/Williams/games/cirqus/index.html`** — the main game page: full credits table ("Cirqus performers", matching the catalog's 11 credits), specifications table (H 90", W 29.5", D 52", 300 lbs), marketing prose ("The Greatest Pinball on Earth"), and three feature statements — playfield DMD ("For the first time ever, Cirqus Voltaire brings the Dot-Matrix display to the playfield"), the BOOM! balloon ("The disappearing pop bumper returns, as the BOOM! balloon"), DCS Sound System.
- **`…/cirqus/rules.html`** — the Show Program (rules guide).
- **`…/cirqus/cv_credits.html`** — standalone credits page.
- **`…/cirqus/cv_history.html`** — in-fiction circus/Voltaire history; theme/description color only.
- **`…/cirqus/tech.html`** — ROM v1.4 revision history + design-team maintenance note.
- **15 playfield-tour pages** (`Ballyhoo, Marvels, Ringmaster, Juggler, Menagerie, RING, Volt, Boom, Jets, Join_Cirqus, Neon, mb_highwire, mb_arc, Acrobats, nf_explore`) — per-feature marketing detail (`cannon.html`/`Cannon.html` 404s — the cannon page is gone).
- **Flyer scans** `cv_flyer_front.jpg` / `cv_flyer_back.jpg` — images, no OCR; quoting means transcription from render per RULEBOOK PDF rules.
- **IPDB 4059** (in the foundation) — quotable via `ipdb_row_text`: credits, the 7-feature line, "Electrifying Excitement!" slogan, notable-features free text (menagerie ball, Ringmaster head, playfield-mounted DMD), notes, production run.

**Not fetched:** the PPS manual flipbook (`/reference/gamemanuals/Cirqus_Voltaire/…/basic-html/pageNNN.html`, per-page HTML, no single PDF found) — the index page's spec table covers what the manual would be cited for.

## Rulings on the open questions (user, 2026-08-10)

1. **Edition models: create them from distributor evidence.** Follow-up finding: on direct inspection the CoinTaker Standard Edition deposit listing and the Great American Pinball "LE" listing are both **removed** (404 in a real browser, product gone from CoinTaker's own site search) — SD Amusements is the only live edition source. So 0223 creates **only `cirqus-voltaire-remake-ringmaster-edition`**; Standard/LE stay recorded here until a citable source exists. Naming follows the seed's CGC pattern: "Cirqus Voltaire (Remake Ringmaster Edition)". The sdamusements.com citation root is a single-family root created in 0223 (the Cardona pattern).
2. **Credits: all creative credits carry** (design, art, animation, music, sound — not mechanics, not software). On the **base remake** that is 8 credits: Popadiuk + Silver (design), Deal (art), Rhine + Morris (animation), Zabriskie + Berry (music), Berry (sound). On the **Ringmaster Edition** the art slot goes to **Brian Allen** instead (SD: "New Brian Allen full Art Package including Playfield, Cabinet, Plastics & Backglass" — corroborated by CoinTaker selling Brian Allen's licensed CV art blades); Deal's art credit does not carry there, the other 7 do. Brian Allen needs a person create (not in `people`).

## Not asserted (and why)

- `cabinet` on both models — campaign convention (0220/0221 precedent): the vocabulary is form-factor (floor/cocktail/…) and no source states it in those terms.
- `production_quantity`, credits, month, player_count, the 7 IPDB features on the original — already claimed by the IPDB actor; re-asserting duplicates get silently swallowed.
- `description` on all models — no done family (0216/0219/0220/0221) asserts model descriptions; description work is its own campaign concern (the Italian campaign ran it as a separate phase), so 0223 stays consistent and skips it.
- `year` on the Ringmaster Edition — no source states a release year; AP has published no dates. 0215's base-model 2026 is not evidence about the edition. Revisit when AP publishes.
- Standard Edition / "LE" models — the only sources are dead URLs and stale search snippets (see ruling 1).
- Playfield-mounted DMD as a display subtype on the original — `display_subtype` has no vocabulary values at all; the fact is preserved in quotes (IPDB: "Playfield-mounted dot matrix display") and stays a doc note.
- "Custom Powder Coating" and "Custom Sculpts" on the Ringmaster Edition — ambiguous referents (coating of what? sculpts of what?); recorded here, not classified.
- The neon tube ring and the backbox scrolls on the original — CV-specific signature decor, not generic vocabulary; listed under future unique features. Same for the interactive backglass cannonball mini-game (no vocab node; too design-specific to create on one machine's evidence).
- `production_status` beyond `announced` on the remake models — AP sells nothing yet (no store listing); distributor pages say "Pre-order".

## Future unique features

- The Ringmaster (animated head rising from the playfield) — bash toy classification candidate.
- Menagerie ball (caged captive ball above left slingshot).
- BOOM! balloon (disappearing pop bumper).
- Neon catwalk ring (the neon tube — presentation).
- (to be finalized during authoring)

## Gate-run history

- 2026-08-10 `make validate` — 3 editorial lint rounds: over-long patch description, then "the catalog"/"edges"/"node" internal-term wording in notes. All fixed in gen.py; passes clean.
- 2026-08-10 `make verify-quote-verbatim` — all 0223 quotes verified first emit, 0 failed (including the AP announcement's meta-description quote — the cached text carries the meta block, so it gates like body text).
- 2026-08-10 `make verify-quote-support ARGS="0223"` — 20/20 claims, **0 warnings**, first run (70k tokens). Not re-run.
- 2026-08-10 `make check` — clean.
- 2026-08-10 snapshot loop (user-cleared): restored `db.prod.patch-0214.2026-08-03`, migrated, ingested all 8 patches — 0223 **success, 50 claims asserted, 0 rejected**; 2 citation roots created on replay (Planetary Pinball via 0217, San Diego Amusements via 0223). Verified via `patch_entry_cites` and the model rows: original `produced` + 8 new features; base remake `announced` + `remake_of` + 8 creative credits; Ringmaster Edition created with `variant_of` + `remake_of` + `lcd` + 772/limited-edition + 5 features + Brian Allen art in place of Linda Deal. Patches left applied.
