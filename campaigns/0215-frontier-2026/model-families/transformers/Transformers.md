# Transformers — 0220

## Status

**Reworked 2026-08-10 for the unique-features policy; snapshot-validated; unshipped (committed locally, not pushed).** Patch number **0220** claimed (next free after 0219). One patch for the whole family — vocabulary and assignments ride one file (vocab entries first, per DataPatchKit.md). 76 entries; all gates green: `make validate` clean (incl. the new `feature-grouping-node` lint), `make verify-quote-verbatim` **93 verified / 0 failed / 11 SKIP-PDF** (matrix + manual + flyer transcriptions, author-checked), `make lint`/`typecheck`/`test` clean, and 0219+0220 applied cleanly on the standing snapshot (`db.prod.patch-0214.2026-08-03.sqlite3` → migrate → ingest) with everything resolving as intended — toy attaches are leaf-only across both families. Two `verify-quote-support` catches from 2026-08-09 are folded in: `ramp-diverters` moved off the PR-quoted toys entry onto its own matrix-mark entry, and the LE `variant_of` claim now cites the quote-less matrix mark (the identical PREM/LE columns are the evidence) instead of a PR quote that never stated the relationship.

**`make verify-citations ARGS=0220` (AI lint) ran with warnings, no changes made** — triage: (1) every archived-2011-page cite reports "source unavailable" because the AI lint resolves the `ref` only — unlike `verify_quotes`, it has no fallback through the cite's `archive:` URL. Tooling gap, same class as the verify-quotes gap closed 2026-08-08; until it's fixed, archived-document cites will always warn there. (2) Many "quote is about a different entity" warnings listing hundreds of common-word slugs (`model:time`, `title:magic`, `model:winner`…) — the entity matcher hits generic words in the quote's line; noise. (3) The reveal-video credit quote warns because the ASR spells "Eisman"/"Geski" — the entry note explains this and the Kineticist cite on the same changeset carries the correct spellings. All three left for the user's review; none looked like a real citation defect.

## Models

- Transformers: More Than Meets the Eye (Pro) (Stern • 2026) — `transformers-more-than-meets-the-eye-pro`
- Transformers: More Than Meets the Eye (Premium) (Stern • 2026) — `transformers-more-than-meets-the-eye-premium`
- Transformers: More Than Meets the Eye (Limited Edition) (Stern • 2026) — `transformers-more-than-meets-the-eye-limited-edition`
- Transformers (Pro) (Stern • 2011) — `transformers-pro`, ipdb:5709
- Transformers (Limited Edition) (Stern • 2011) — `transformers-limited-edition`, ipdb:5753 (the "Combo")
- Transformers Autobot Crimson (Limited Edition) (Stern • 2011) — `transformers-autobot-crimson-limited-edition`, ipdb:5754
- Transformers Decepticon Violet (Limited Edition) (Stern • 2011) — `transformers-decepticon-violet-limited-edition`, ipdb:5755
- Transformers The Pin (Stern • 2012) — `transformers-the-pin`, ipdb:5861 — **own Title** (`transformers-the-pin`), see Traps

## Catalog baseline (surveyed 2026-08-08, dev DB at 0219)

Claim-level scan run against `model_claims` from **all actors** (the Houdini lesson — the apply silently swallows exact duplicates, so the scan was done before authoring, not after).

| field | pro 2011 | le 2011 | crimson | violet | the pin | mtmte pro | mtmte prem | mtmte le |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| year / month | 2011/11 | 2011/11 | 2011/1 | 2011/1 | 2012/1 | 2026/— | 2026/— | 2026/— |
| production_status | — | — | — | — | — | — | — | — |
| game_format | — | — | — | — | — | — | — | — |
| tech generation | ss | ss | ss | ss | ss | — | — | — |
| display_type | dot-matrix | dot-matrix | — | — | alphanumeric | — | — | — |
| system | stern-sam | stern-sam | stern-sam | stern-sam | stern-spike-1 | — | — | — |
| model_number | PINBALL I-00C3 | — | — | — | — | — | — | — |
| players | 4 | 4 | 4 | 4 | 4 (ipdb says 2!) | — | — | — |
| production_quantity | — | **500 (ipdb)** | **125 (ipdb)** | **125 (ipdb)** | — | — | — | — |
| tag | — | limited-edition | limited-edition | limited-edition | home-use | — | — | — |
| lineage | — | — | variant_of→le ✓ | variant_of→le ✓ | — | — | — | — |
| credits | 7 (no art, no music) | 8 (no art) | 8 (no art) | 8 (no art) | 6 (incl. art) | — | — | — |
| features | 5 (ipdb) | 4 (ipdb) | **none** | **none** | 2 (ipdb; slingshots dropped) | — | — | — |
| themes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (0215) | ✓ (0215) | ✓ (0215) |

**Do not re-assert:** production_quantity on the three 2011 LEs (ipdb), tags on 2011 LEs + The Pin, all themes, 2011 credits/features listed above, Crimson/Violet `variant_of`.

## Evidence inventory (all cached in pinexplore web cache)

### 2026 MTMTE

- **Stern press release, 2026-05-20** — `https://www.sternpinball.com/2026/05/20/roll-out-for-battle-with-transformers-more-than-meets-the-eye-by-stern-pinball` (HTML, gated). The densest 2026 source: "revealed and released", "available now in Pro, Premium, and Limited Edition (LE) models", "Limited to 750 games globally", the full LE equipment sentence (Expression Lighting ×2, mirrored backglass, pinball armor, autographed bottom arch, upgraded audio, anti-reflection glass, shaker, numbered plaque, COA), the three toys (animatronic Megatron + fusion cannon that "fires pinballs back", Soundwave cassette-deck ball locks, Optimus bash toy), MSRPs. No people credits (only voice actors + Stan Bush + Knights of Unicron).
- **Feature matrix** — `https://wp.sternpinball.com/wp-content/uploads/2026/05/Transformers-More-Than-Meets-the-Eye-Feature-Matrix.pdf` (1 sheet, text layer + render). The ~44-row × 3-edition grid, fully transcribed 2026-08-08 (renders in scratchpad during authoring; the grid readings are recorded in gen.py's tables). Quotable rows (SKIP-PDF): row labels, LE-only block, GENERAL block, MAIN ATTRACTIONS prose, "Individually Autographed by Game Designer Elliot Eismin." Column membership is a **mark** — quote-less cite with locator + note per column (ENRICHMENT-PLAN → Citing PDF evidence).
- **Pro manual** — `https://wp.sternpinball.com/wp-content/uploads/2026/07/Transformers_MTMTE_Pro_web.pdf` (66 sheets, real text layer). Sheet 1: `TRANSFORMERS: MORE THAN MEETS THE EYE PRO #500-55AA-01` (the Pro model number) and manual #780-50AA-00. TOC: "SPIKE-3 CPU Node 0". **No people credits anywhere** (Eismin/Gieske/Blakeman/Kyzivat/Thompson/designer → 0 matches). Premium/LE manuals unpublished as of 2026-08-08.
- **Reveal video** — `youtube:zLx93Iiy5yw` ("TRANSFORMERS: More Than Meets the Eye Presented by Stern Pinball", auto-captions, gated). ASR: "Hi, I'm Elliot Eisman, lead game designer" and "Hi, I'm Elizabeth Geski, lead software developer" — **both names are ASR misspellings**, quoted verbatim per the video-citation rules. Trailer `youtube:3J9JGgUiRlc` carries no credits.
- **Stern of the Union June + August 2026** (HTML, gated) — August: "TRANSFORMERS: More Than Meets The Eye pinball machines are rolling out worldwide" (production evidence).
- **Kineticist news article** — `https://www.kineticist.com/news/stern-transformers-reveal` (journalism, root resolves). Full Design Team block: Design Eismin, Lead Programmer Gieske, Lead Mechanical Rob Blakeman, Code Mike Kyzivat, Audio Jerry Thompson, Lead LCD Artist Tom Kyzivat, Producer John Blakely. Correct "Gieske" spelling.
- **Arcade Heroes article** — `https://arcadeheroes.com/2026/05/20/stern-pinball-transformers-more-than-meets-the-eye` (journalism, root resolves). Corroborates "Elliot Eismin & Elizabeth Gieske" as the designers.
- **Stern game page** — `https://www.sternpinball.com/game/transformers-more-than-meets-the-eye` (rendered). Marketing blurbs + edition prices only; no credits, no per-edition data.

### 2011/2012 family — the Wayback jackpot

Stern's 2011-era game pages are dead on sternpinball.com but archived; fetched via `id_` snapshots (cite `ref` = original URL + `archive:` = snapshot; verify-quotes resolves through `archive:` since 2026-08-08). **These are HTML, so their quotes are machine-gated** — the first-party per-edition evidence IPDB lacks:

- **Pro page** — ref `http://www.sternpinball.com/Games/transformers-pro.aspx`, archive `http://web.archive.org/web/20110928030152id_/...`. "In Production" + a 17-row feature list (Megatron Vehicle Form Rapid Fire Multiball with Cyber Ball Lock, M.T.M.T.E. Elevating Ramp, Bumblebee Captive Camaro Target, Decepticon Laser-Cut Steel Ramp, Ironhide Ramp, 3 Devastator Pop Bumpers, Autobot/Decepticon Spinning Target, All Spark Cube Eject Hole, Cybertron Zenith Orbit Shot with electronically-controlled gate…).
- **LE page** — ref `http://www.sternpinball.com/Games/transformers-le.aspx`, archive `http://web.archive.org/web/20111203043615id_/...`. **Explicitly-headed per-edition blocks** — "Transformers LIMITED EDITION Features:", "Autobot Crimson LIMITED EDITION Features:", "Decepticon Violet LIMITED EDITION Features:" — the same shape as Houdini's "Deluxe Features". LE: multiball cannon + Cyber ball lock, Chromium Cyber Sphere player-controlled upper playfield, Starscream Strike rotating action figure target, Zenith and Nadir orbit shots via second electronically-controlled gate, Megatron Cyber Lock Guard drop target, Quake Maker shaker motor, Full Spectrum Color Chroma LED GI, side armor, Gomez signature (#1-35), 1-500 numbered plaque. Crimson/Violet blocks: cabinet trim, unique backglass art, signature plates, Gomez signature, 1-125 numbered plaque.
- **The Pin page** — ref `http://www.sternpinball.com/Games/transformers-pin.aspx`, archive `http://web.archive.org/web/20121207090811id_/...`. "In Production", "Designed Specifically for Home Use", "Genuine Stern Pinball Flippers, Slingshots, and Plunger", "All LED lighting", "Licensed Transformers Art, Music, Speech, and Sound Effects".
- **2011 news announcement** — ref `http://sternpinball.com/About/News/transformers-pinball.aspx`, archive `.../20111008151533id_/...`. Dated Sept 20 2011; no machine facts beyond pricing; research-only.
- **LE flyer** — ref `http://www.sternpinball.com/upload/Games/TransformersLE-Flyer.pdf`, archive `http://web.archive.org/web/20111226195649id_/...` (2 sheets, outlined type, OCR'd 2026-08-08). Sheet 2 duplicates the LE page's three edition blocks. The LE **page** is the preferred cite (HTML, gated); the flyer corroborates.
- **The Pin flyer** — ref `http://sternpinball.com/upload/Games/PinTransformers-Flyer-1012-01c.pdf`, archive `http://web.archive.org/web/20130211085308id_/...` (2 sheets, outlined, OCR'd). Corroborates the Pin page.
- **The two 2011 manuals** — byte-identical, OCR-only; see Traps. Not needed: the archived pages carry everything citable.
- **IPDB rows** ipdb:5709/5753/5754/5755/5861 — quotable via `ipdb_row_text` incl. credit lines. 5754/5755 carry no hardware line (only cabinet dims); 5753's hardware line serves their shared design via the variant rule.

## Traps

**The two 2011 manuals are the same file.** `Transformers-Manual.pdf` and `Transformers-Manual-LE.pdf` (both `wp.sternpinball.com/wp-content/uploads/2018/11/`) are **byte-identical** — one `content_sha`, `9a4ff4cc3f5391bf730d226eb969c855c7c8c0f429c33e66d846d4069c7898b8`, 134 sheets each. Stern serves one document under two names, so the `-LE` filename promises a per-edition source that does not exist: **the 2011 manuals cannot distinguish Pro from Limited Edition.** Do not read the filename as evidence — check the sha before treating two Stern manuals as two sources. (Same shape as the Pokémon trap.)

**Both 2011 manuals are OCR-only.** No text layer — `quote` returns nothing, `search` answers from the `(ocr)` tier. Render and transcribe; `make verify-quotes` reports PDF quotes `SKIP-PDF`. (Superseded in practice: the archived game pages carry the same facts as gated HTML.)

**`transformers-the-pin` is not under the `transformers` Title.** It has its own Title, so `title_slug = 'transformers'` silently misses it. Enumerate the eight models by slug.

**IPDB says The Pin is 2 players; the seed said 4 — CORRECTED (user-approved 2026-08-08).** The winning flipcommons-catalog claim of 4 carried no citation and no note (a seed-era ingest, apparently propagated from OPDB's 4). Primary evidence says 2: IPDB's `Players: 2` + "Two 8-digit LED score displays", and the flyer's product photo shows the speaker panel's exactly-two displays labeled PLAYER 1 / PLAYER 2 — the hardware ceiling on players. 0220 asserts `player_count: "2"` with both cites (the flyer via its Wayback `archive:`), superseding the uncited claim; verified rank 1 with the old 4 inactive after replay.

**The matrix contradicts itself on slingshots.** "2 Slingshots (2 Lower + 1 Upper Left)." — headline 2, enumeration 3. 0220 attaches `slingshots` **count-less** with the verbatim quote and a note; a count would invent precision the source argues with itself about.

**The matrix duplicates its flipper row.** "3 Flippers (2 Standard + 1 Upper Flipper)." appears twice, both all-editions — one `{flippers: 3}` attach.

**Matrix typos are verbatim.** "Theme song fom the first season", "Challnge Modes", "Deceptions" (for Decepticons, also in the PR) — quotes keep them.

**The reveal video's ASR misspells both leads.** "Elliot Eisman" / "Elizabeth Geski". Quotes stay as the transcript has them; correct spellings (Eismin/Gieske) rest on the matrix (Eismin) and Kineticist + Arcade Heroes (Gieske).

**IPDB 5861's missing comma.** "Flippers (2), Pop bumpers (3) Slingshots (2)." — likely why the seed ingest dropped The Pin's slingshots; the quote must keep the missing comma.

## Sought and not found (authoring-time searches, 2026-08-08)

- **2011 family art credit** — no primary source names an artist: not in IPDB rows, not on the archived Stern pages, not in either flyer (OCR + render). Left unset.
- **2011 Pro music credit** — IPDB 5709 carries no Music line (5753/54/55 do: David Thiel). Catalog mirrors IPDB exactly; left as-is.
- **MTMTE art credit** — no source (incl. Pinside) credits an artist; the game uses original-animated-series artwork. Left unset.
- **MTMTE Premium/LE manuals** — unpublished; Premium/LE model numbers unknown, only the Pro's is asserted.
- **MTMTE player count** — no primary or journalism source states it (the head-to-head mode muddies "4 players" anyway). Left unset; user may wish to add when a manual/spec sheet states it.
- **MTMTE month** — the PR dates the *release* (May 20), the plan's rule wants the *manufacture* date; August SOTU says machines still "rolling out". Left unset.

## Decided

- **Matrix volume: emit the full grid** (user, pre-session): all rows × 3 editions, including features common to all three.
- **One patch, 0220** — vocab entries first, then models (dependency order within one file).
- **MTMTE LE → `variant_of` → Premium**, matching the catalog's uniform Stern convention (every modern Stern LE points at its Premium; 40+ precedents surveyed 2026-08-08) and the matrix's identical PREM/LE game-feature columns (mark evidence). Premium and Pro carry no edge, also per convention. 2011 LE ↛ Pro: different playfield (VUK 4-ball multiball vs Pro's kick-out hole), consistent with the seed leaving them unlinked.
- **Credits, MTMTE**: Eismin design (matrix quote + reveal-video ASR), Gieske software (reveal video + Kineticist; person **created** in 0220, spelling per Kineticist/Arcade Heroes with the ASR noted). Blakeman mechanics, Mike Kyzivat software, Jerry Thompson sound, Tom Kyzivat animation: **Kineticist only** (journalism; acceptable — no first-party source states them; Pinside is crowdsourced and barred for models with manufacturer PDFs). John Blakely "Producer": no matching credit-role; skipped.
- **Toys are classified, not named (user decision, 2026-08-10).** Per flipcommons `docs/plans/catalog_data_model/unique_features/UniqueFeatures.md`, models attach only the generic toy classification leaves 0219 creates (`static-toys` / `bash-toys` / `animatronic-toys` / `ball-holding-toys`); grouping nodes are never attached (lint-enforced). 0220's classifications: animatronic Megatron → animatronic; static Megatron → static (Stern's own word); Soundwave cassette deck → ball-holding; sculpted Grimlock → static (no motion stated); 2011 figure lists → static; the Camaro captive-ball car → bash ("captive ball accelerates car into target"); 2011 LE Megatron Robot Form (locks and fires balls) → ball-holding; Starscream rotating figure target → bash.
- **Future unique features (UniqueFeature backfill worklist):** animatronic Megatron with pinball-firing fusion cannon (PR + matrix), static Megatron (matrix), Soundwave cassette-deck ball lock (PR + matrix), custom sculpted Optimus Prime bash toy (PR + matrix), Grimlock Dinobot toy (matrix); 2011: Megatron Vehicle/Robot Form multiball cannon (pages), Bumblebee Captive Camaro (pages + IPDB toys), Starscream Strike rotating figure (LE page), Chromium Cyber Sphere upper playfield (LE page), the IPDB figure lists (ipdb:5709/5753).
- **The interactive-lighting DAG lives in 0220** (user-approved taxonomy, 2026-08-10): `interactive-lighting` → `interactive-cabinet-lighting` / `interactive-speaker-lighting` / `expression-lighting-system` (Stern's brand family), with the two product leaves (`Interactive Cabinet Expression Lighting System`, `Speaker Expression Lighting System`) each carrying a location parent and the brand parent. Other makers' brand nodes (JJP, Pedretti's GameSync, HAL) are deliberately NOT created — their family patches create them from their own primary documents, if the terms prove to be real brands.
- **New vocab in 0220** (all flagged for review): the six lighting nodes above; `optical-spinners` (child of spinners); `cabinet-expression-lighting` + `speaker-expression-lighting` (Stern's branded systems, kept distinct — not LED GI); `mirrored-backglasses`; `numbered-plaques`; `designer-autographs`. Attach-not-create: `ball-cannons` for "Megatron Pinball Firing Fusion Cannon" / "rapid fire multiball cannon" (clear synonym: a cannon firing pinballs), `mini-playfields` for the 2011 LE's "player-controlled upper playfield" (standard cataloguing term), `vertical-up-kickers` for "V.U.K.", `lockdown-bar-buttons` for "Multifunction Action Button on lockdown bar", `3-bank-drop-targets`, `solitary-drop-targets` for the LE's single "Cyber Lock Guard" drop target, `rotating-targets` for "Starscream Strike rotating action figure target", `moving-ramps` for the elevating ramp, `electric-gates` + `orbits` for the electronically-controlled-gate orbit shots, `targets` (not standup — the source doesn't say) for "Complete Grimlock targets".
- **Matrix rows deliberately not represented as features** (recorded here so the omission is a decision, not a miss): COA (paper), side cabinet decals/translites (standard art carriers), Insider Connected rows (service), video-clip and theme-song rows (licensed content, not a mechanism — The Pin's `speech` attach differs because 0218 created a `speech` node), 10-band EQ / line-out / fader (audio internals), snap-latch molding & steel bottom arch (trim minutiae), LE "upgraded speaker system" (stereo-sound already attached via GENERAL block).
- **production_status: produced on all 8** — 2011/2012 from the archived pages' "In Production" badge text, MTMTE from PR "revealed and released" + August SOTU "rolling out worldwide".
- **`stern-spike-3` System created** in 0220 (name "Stern SPIKE 3", matching "Stern SPIKE 2"), evidence: matrix "powered by Stern's next-generation technology with the new SPIKE 3 platform." + manual TOC "SPIKE-3 CPU Node 0". Shared with future families (Pokémon runs SPIKE 3) — theirs must NOT re-create it (numbered after 0220, so a plain reference works).
- **Variant rule applications**: Crimson/Violet carry the LE's playfield features, cited to the LE page/ipdb:5753 with the variant note (edges already seeded). Their carry includes `side-armor` via the base LE's own side-armor span — their own blocks say "Full cabinet trim", which names the color, not the armor. MTMTE LE carries nothing extra by rule — the matrix states its column directly.
- **Toys on the 2011 models are NOT attached.** IPDB's Toys line (`ipdb.toys` raw claims exist on the 2011 Pro and LE) is not rendered by `ipdb_row_text`, so it can't carry a gated quote, and the archived pages describe the figures as targets/ramps rather than toys. If `ipdb_row_text` later learns the Toys line, a follow-up can attach `toys` to the 2011 four.
