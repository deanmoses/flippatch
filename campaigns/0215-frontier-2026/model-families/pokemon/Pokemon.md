# Pokémon — 0237

## Status

**Authored + snapshot-validated 2026-08-13, uncommitted.** Patch number **0237** claimed (next free after 0236). One patch for the whole family, 63 entries; all gates green (see Gate runs below), and 0201–0238 applied cleanly on the standing snapshot (`db.prod.patch-0214.2026-08-03.sqlite3` → migrate → ingest, user-approved rebuild). Everything resolves as intended: 102 claims, 91 cites across all 63 changesets (no duplicate-swallow), features land as leaves (Pro 18 / Premium 21 / LE 28), 5 credits per model, both persons created with the Joshua Henderson alias resolving.

## Models

- Pokémon (Pro) (Stern • 2026) — `pokemon-pro`, opdb GV8wB-Mq12N
- Pokémon (Premium) (Stern • 2026) — `pokemon-premium`, opdb GV8wB-MRjKd-AOVy7
- Pokémon (Limited Edition) (Stern • 2026) — `pokemon-limited-edition`, opdb GV8wB-MRjKd-ARz2r
- No older siblings — this is the first Pokémon pinball machine (Kineticist: the first Nintendo property on a pinball machine since Gottlieb's Super Mario Bros. in 1992).

## Catalog baseline (surveyed 2026-08-13, dev DB with 0231–0236 in flight)

Claim-level scan against `model_claims` from all actors before authoring.

| field               | pro                        | premium         | le                                 |
| ------------------- | -------------------------- | --------------- | ---------------------------------- |
| year / month        | 2026/2                     | 2026/2          | 2026/2                             |
| production_status   | —                          | —               | —                                  |
| game_format         | —                          | —               | —                                  |
| tech generation     | ss (opdb + catalog)        | —               | —                                  |
| display_type        | lcd (opdb + catalog)       | —               | —                                  |
| system              | —                          | —               | —                                  |
| player_count        | 4 (opdb + catalog)         | —               | —                                  |
| production_quantity | —                          | —               | —                                  |
| tag                 | —                          | —               | limited-edition (0206)             |
| lineage             | —                          | —               | variant_of → premium ✓ (catalog)   |
| credits             | none                       | none            | none                               |
| features            | none                       | none            | none                               |
| themes              | ✓ (610 + 520)              | ✓               | ✓                                  |
| abbreviation        | Pokemon (opdb)             | ✓               | ✓                                  |

**Do not re-assert:** year/month (opdb; Kineticist's production timeline corroborates the February manufacture start), themes, LE tag, LE `variant_of`, Pro display/techgen/player_count, abbreviations.

**No lineage work needed:** the LE → Premium `variant_of` edge already exists, and Stern convention gives Premium and Pro no edge (40+ catalog precedents surveyed for 0220).

## Evidence inventory (all cached in pinexplore web cache)

- **Stern press release, 2026-02-13** — `https://www.sternpinball.com/2026/02/13/become-a-top-pokemon-trainer-with-stern-pinballs-newest-line-of-machines` (HTML, gated). The densest source: "revealed and released a new pinball machine – Pokémon by Stern Pinball" (dateline Feb 12), "available now in Pro, Premium, and Limited Edition (LE) models", "Powered by Stern's SPIKE 3 technology", the full LE equipment sentence ("limited to 750 games globally … Expression Lighting System™ and Speaker Expression Lighting System … mirrored backglass … pinball armor … designer-autographed bottom arch … anti-reflection … shaker motor … numbered plaque"), the toys (animatronic Pikachu, mechanically animated Poké Ball, interactive Meowth Balloon), "Premium and Limited Edition games include an interactive electromagnet", custom voiceovers, prices. No people credits. Reveal video URL in the meta description (`youtu.be/78q_9-6PBSY`).
- **Feature matrix** — `https://wp.sternpinball.com/wp-content/uploads/2026/02/PANTS-Matrix-added-%C2%A9_021226.pdf` (1 sheet, real text layer; rendered and grid transcribed 2026-08-13, readings recorded in gen.py). "PANTS" was the game's internal dev codename (per Kineticist) — the filename is not a mislabel. Quotable rows (SKIP-PDF): the LE ONLY block incl. "Production limited to 750 machines." and "Individually Autographed by Game Designers Jack Danger and George Gomez." (the family's only first-party person credits), the SPIKE 3 row, the 18.5" display row. Column membership is a mark — quote-less cite with locator + note per column.
- **Per-edition game pages** (HTML, gated — the per-edition evidence the shared manual can't give): `https://www.sternpinball.com/game/pokemon/pro` ("Pikachu static toy with custom recorded speech.", "RGB illuminated static Poké Ball includes ball stop post on left ramp."), `…/premium` ("Pikachu animatronic toy reacts to playfield action with movement and custom recorded speech.", "Animatronic Poké Ball ball-lock with RGB illumination at the Left Ramp.", "Psyduck Sneak-In ball scoop."), `…/limited-edition` (armor, Speaker Expression Lighting, Squirtle Whirlpool, "The interactive Meowth Balloon Arena magnet provides kinetic action and excitement.", Master Ball plunger). Landing page `…/game/pokemon` is served from `pokemon.sternpinball.com/landing-page/pokemon` (cache alias); all resolve to the Stern root.
- **Pro manual** — `https://wp.sternpinball.com/wp-content/uploads/2026/04/Pokemon_Pro_web.pdf` (72 sheets, real text layer). Sheet 1: `MANUAL #780-50AG-00` + `POKÉMON PRO #500-55AG-01`. Specs on printed page 67 = PDF page 67: 210 lbs, max dims 78 x 27.75 x 57 in. TOC: "SPIKE-3 CPU Node 0". No people credits anywhere (Danger/Gomez/Klyce → 0 matches).
- **LE/Premium manual** — `https://wp.sternpinball.com/wp-content/uploads/2026/04/Pokemon_LE_Pre_web.pdf`. Sheet 1 lists both editions: `MANUAL #780-50AJ-00`, `POKÉMON LE #500-55AJ-01`, `POKÉMON PREMIUM #500-55AH-01`. Specs on printed page 72 = PDF page 72, headed 500-55AJ-01: same 210 lbs / 78 x 27.75 x 57 in. No people credits.
- **Kineticist news article** — `https://www.kineticist.com/news/stern-pinball-reveals-pokemon-pinball` (journalism, root resolves). Design Team block: "Design: Jack Danger, George Gomez", "Code: Tanio Klyce, Andrew Wilkening, Josh Henderson", "Art: All assets and art come from The Pokemon Company". Production timeline ("production starting late February through early March", LE then Premium "later in March"), "The LE sold out before the game shipped.", and the per-edition comparison ("Premium/LE upgrades to a fully animatronic Pikachu…", "Psyduck: Pro gets a stand up target.").
- **Arcade Heroes article** — `https://arcadeheroes.com/2026/02/13/gotta-catch-em-all-stern-pinball-officially-unveils-pokemon` (journalism, root resolves). Corroborates "designed by Jack Danger and George Gomez" and "now considered to be released and available".
- **Stern of the Union June + August 2026** (cached) — Pokémon appears only in accessories/rewards-program contexts; no production-status sentence. Not cited.

## Traps

**The Premium and the LE share one manual.** `Pokemon_LE_Pre_web.pdf` is one document explicitly covering both editions (sheet 1 lists both model numbers) — a per-edition filename is not per-edition evidence (RULEBOOK → Finding and fetching documents). Per-edition facts come from the edition pages, the matrix columns and Kineticist's comparison, never from the shared manual.

**The matrix filename is the dev codename.** `PANTS-Matrix-added-©_021226.pdf` — Kineticist records "PANTS" as the internal codename. The `©` must be percent-encoded (`%C2%A9`) in the cite ref, exactly as cached.

**The reveal video has no captions.** `youtube:78q_9-6PBSY` returns no transcript, so nothing in it is quotable. All credits rest on the matrix autograph row + journalism instead.

**The game landing page is a JS shell.** Its extracted text carries no document links (no wp-content, no PDFs); the matrix was found via web search, not the site. The per-edition subpages extract fine.

## Decided

- **Credits**: Jack Danger + George Gomez design — first-party matrix row ("Individually Autographed by Game Designers Jack Danger and George Gomez.") + Kineticist + Arcade Heroes. Tanio Klyce, Andrew Wilkening, Josh Henderson software — Kineticist's Design Team block only (acceptable: no first-party source names the code team; the manuals carry no credits). **Persons created**: `andrew-wilkening`, `josh-henderson` (collision risk with concurrent in-flight patches accepted — neither name appears in any other 2026 family).
- **Josh vs Joshua Henderson**: Kineticist's credit line says "Josh Henderson" while its own People sidebar links "Joshua Henderson". Created as Josh Henderson (the name on the credit) with Joshua Henderson as a `person_alias` — the GTF Pollitt/Politt pattern for a name variant.
- **Notes pruned to the classification-reasoning minimum** (user directive, 2026-08-13): the only notes in the patch are the matrix mark notes (they are the evidence record for quote-less mark cites), the SPIKE-3→solid-state inference, the cabinet-from-dimensions classification, and the shared-manual explanation on the Premium's cabinet cite. Everything else the quotes carry.
- **No art person credit** — Kineticist: "Art: All assets and art come from The Pokemon Company". No person to credit; left unset.
- **No new vocabulary.** Every attach resolves against existing nodes — incl. `whirlpools` (Squirtle Whirlpool bowl), `magnets` (arena electromagnet), `scoops` (Town scoop, Psyduck Sneak-In) and 0220's LE-equipment set.
- **Toy classifications**: Pro Pikachu and Pro Poké Ball → static ("static" is Stern's own word for both); Premium/LE Pikachu → animatronic; Premium/LE Poké Ball → animatronic + ball-holding + ball-locks (it is a ball-lock); Meowth Balloon → bash (Kineticist: "a physical target to bash"; Stern: "Ball interactive").
- **`ball-locks` only on Premium/LE** — the Pro's static Poké Ball has a ball *stop post*, not a lock; no source calls the Pro's a lock.
- **The Pro's ball stop post is NOT attached as a post feature** (support-gate catch, 2026-08-13): no source states whether the "ball stop post" is an up-post or a stationary post, and both vocab nodes exist — attaching either would invent the mechanism. Recorded in the unique-features worklist instead.
- **`cabinet: floor` on all three** from the manuals' dimensions tables (210 lbs, 78 x 27.75 x 57 in), classification-from-dimensions per the 0228 TOTAN pattern.
- **`production_status: produced` on all three** — PR "available now" + Kineticist's dated production runs per edition (Pro late Feb–early Mar; LE then Premium later in March).
- **Deliberately not represented as features** (0220 precedent): Insider Connected rows (service), video-clip and theme-song rows (licensed content — but `speech` attaches via the PR's custom-voiceovers sentence, the 0218 node), 10-band EQ / line-out / fader (audio internals), snap-latch molding + steel bottom arch (trim minutiae), translites/side-cabinet decals (standard art carriers), COA (paper), LE upgraded speaker system (stereo-sound already attached via GENERAL).

## Sought and not found (authoring-time searches, 2026-08-13)

- **Premium/LE player_count** — no primary or journalism source states a player count for any edition (the Pro's existing 4 is opdb's). Left unset.
- **Reveal-video credits** — no captions on `78q_9-6PBSY`; nothing quotable.
- **Manual credits** — Danger/Gomez/Klyce → 0 matches across both manuals (the Stern pattern; 0220 saw the same).
- **A Stern SOTU production sentence** — June and August 2026 SOTUs mention Pokémon only for accessories/IFPA rewards; production evidence rests on the PR + Kineticist instead.

## Future unique features (UniqueFeature backfill worklist)

Animatronic Pikachu with movement + custom speech (Premium/LE), static Pikachu (Pro), animatronic Poké Ball ball-lock (Premium/LE), RGB illuminated static Poké Ball with ball stop post (Pro), ball interactive Meowth Balloon toy (all), arena electromagnet (Premium/LE), Squirtle Whirlpool bowl (Premium/LE), Psyduck Sneak-In ball scoop (Premium/LE), Pokédex captive ball (all), Charmander optical spinning target (all), Town scoop (all), Limited Master Ball sculpted plunger (LE), B-A-T-T-L-E targets (all).

## Gate runs

- **2026-08-13 `make validate`**: clean after three lint iterations — the 0220-era locator conventions ("page 1 of 1", "no printed folio") and note phrasings ("maps to", "sought", "at authoring time", "no source") are now lint errors; current wording rules differ from the older templates.
- **2026-08-13 `make verify-quote-verbatim`**: 0 failed for 0237; all matrix/manual quotes SKIP-PDF, author-checked against renders.
- **2026-08-13 `make verify-quote-support ARGS="0237"`** (one run, 47 calls / ~590k tokens): 5 warnings, triaged, not re-run. (1) `up-posts` on the Pro — **accepted**: attach dropped, the post's mechanism is unstated (see Decided). (2) Josh vs Joshua Henderson — **accepted**: alias added (see Decided). (3) `technology_generation: solid-state` ×2 — **rejected**: the verifier reads "solid-state" as the 1970s–80s era; the catalog's generation vocabulary classifies every SPIKE machine as solid-state (the Pro's own opdb/catalog claims, 0220's identical assertion). (4) Josh Henderson credit "omits the other two coders" — **rejected**: each credit is its own changeset; the quote names all three. (5) The LE-inheritance hedge on the same credit — same rejection.
