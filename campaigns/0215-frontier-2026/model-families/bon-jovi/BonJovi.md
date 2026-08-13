# Bon Jovi (Barrels of Fun, 2026) — family record

Patch **0224** (`patches/0224-bon-jovi.yaml`), originally emitted by a `gen.py` beside this file (deleted 2026-08-13; in git history). Single-model family: `model.bon-jovi`, one edition, no variants, no older siblings — Barrels of Fun's other machines (Labyrinth 2023, Dune 2025, Winchester Mystery House 2025) are separate Titles and out of scope. Authored 2026-08-10.

## Catalog baseline (surveyed 2026-08-10)

0215 created the model with name, slug, year 2026, corporate_entity barrels-of-fun, title bon-jovi, status active, and themes licensed + hard-rock. Every other field was empty: no month, player_count, production_status, production_quantity, game_format, display, system, cabinet, technology generation, tag, credits, gameplay features, or description. `model_claims` for the model held only the eight 0215 rows (actor Flipcommons Catalog), so nothing here duplicate-swallows.

## Evidence inventory

| document | cache status | carries |
| --- | --- | --- |
| [Maker reveal post](https://www.barrelsoffun.com/2026/07/28/bon-jovi-pinball-is-ready-to-rock-build-the-setlist-and-play-it-loud) (2026-07-28) | cached, gated HTML | The press-release lede, the 700-unit limited-release paragraph, the purchase CTA ("Order Bon Jovi Pinball from Barrels of Fun!"), and the **complete 11-person credit block with roles** — the family's credit source. Does **not** carry the Game Attractions / Game Features spec blocks. |
| [Pinball News reveal](https://www.pinballnews.com/site/2026/07/28/bon-jovi-revealed) (2026-07-28) | cached, gated HTML | PN's own playfield walkthrough (journalism) **plus the full press release reprinted verbatim**, including the Game Attractions and Game Features blocks, the display/audio package, "currently in production", and "available for purchase now". The reprint is the maker's own words (RULEBOOK → press releases), and being HTML it is the family's machine-gated spec source. |
| [BJ Flyer PDF](https://www.barrelsoffun.com/wp-content/uploads/2026/07/BJ-Flyer.pdf) (uploaded 2026-07) | cached, 2 pages, **no text layer** (outlined type — RULEBOOK already records this) | Page 1: hero shot, iconic-hits teaser, boxed/unboxed dimensions, BoF LLC 2026 legal line, "GAME SUBJECT TO CHANGE". Page 2: Game Features counts, Premium Presentation (HAL, EverGloss, Infinity Glass, inner blade art, cabinet armor), Feedback (shaker), Display and Custom Audio Package, Game Attractions, tracks list, and the art credit "Featuring Amped Up Original Art by Jonathan Bergeron". Quotes are transcribed off the rendered sheets (150 dpi, 2026-08-10); they gate SKIP-PDF. |
| [Maker SFGE post](https://www.barrelsoffun.com/2026/07/28/play-bon-jovi-pinball-sfge-2026) | cached | Show debut logistics (SFGE 2026, Jul 31–Aug 2, Classic Gamerooms booth). Color only; nothing asserted from it. |
| [Maker gameplay-overview post](https://www.barrelsoffun.com/2026/07/28/bon-jovi-pinball-gameplay-overview-w-karl-deangelo) | cached | Just a video embed, no body text. |
| [Gameplay reveal video](https://www.youtube.com/watch?v=3_FSKmOsYlg) (BoF channel, 9:12) | cached, auto-captions | First-party but casual ASR chat; notable color: nine of the 17 songs launch with the game; "outlane ball save flipper". Not cited — everything it supports is stated cleanly elsewhere. |
| [Pinside game page](https://pinside.com/pinball/machine/bof-bon-jovi) | cached | Crowdsourced; per RULEBOOK never sole support. Lists the same 11 credits (with two spelling variances, below) and player_count 4 (uncorroborated — not asserted). |
| Maker homepage, flyers page, videos page, kollectfun safety-manuals page | cached | Discovery surfaces. The flyers page links all four BoF flyers; the safety-manuals page carries Winchester/Dune/Labyrinth manuals only — **no Bon Jovi manual exists yet**. |

Citation roots: `barrelsoffun.com` and `pinballnews.com` both already resolve — no root work in this patch. The maker's store lives on `shop.kollectfun.com` (different company domain, unrooted); nothing needed citing from it.

## Traps

- **The maker's own reveal post is shorter than its press release.** The Game Attractions / Game Features blocks exist only in Pinball News's verbatim reprint (and on the flyer). Spec quotes therefore cite PN; credits and the 700-unit paragraph cite the maker's post.
- **PN's reprint contains two joined-word spans in the HTML text itself** — "Cabinet Armor &Matching Speaker Panel" and "Bon JoviHeart & Dagger". These are the page's own text, not scrape artifacts: a quote lifted verbatim from `web_cache.py quote` output matches them fine (user correction, 2026-08-10 — the patch's ending its armor span at "Cabinet Armor" was unnecessary caution, though harmless).
- **The press release and the flyer word HAL's tagline differently**: PR "Complete Concert Experience Lighting Effects", flyer "Complete Concert-In-A-Pin Lighting Effects". Each quote follows its own document exactly.
- The two short promo videos (trailer et al.) have **no captions** — nothing quotable; not cached as a result.
- The two 2-minute trailer videos on the BoF channel could not be identified by title without captions; the 9:12 gameplay reveal is the identified, cached one.

## Decisions (user, 2026-08-10)

- **Patch number 0224** (user-assigned; parallel sessions running).
- **production_quantity: "700"** with a note recording the maker's caveat: possible Barrels Reserve overrun, final edition number to be announced after ordering closes.
- **production_status: produced** — the user's criterion: if it's for sale, it's 'produced'. The PR states "currently in production", and both "available for purchase now" (PN reprint) and the maker's own "Order Bon Jovi Pinball from Barrels of Fun!" CTA establish for-sale.
- **Person-name spellings (user-approved rename, 2026-08-10)**: the maker writes "David **van** Es" and "Parker Dillman**n**" where the existing people carried Pinside's "David Van Es" / "Parker Dillman". Per the GTF ruling the maker's spelling wins: the patch renames both people to the maker's forms and keeps the Pinside forms as `person_alias`. Josh Clay keeps his short-form name ("Joshua" is the maker's long form, aliased — a diminutive, not a spelling conflict).

## Credits (all from the maker reveal post's credit block)

| block label | person | role | person status |
| --- | --- | --- | --- |
| Game Design | David van Es | design | exists (`david-van-es`) — renamed to "David van Es", Pinside form aliased |
| Rules | Phil Grimaldi | other | **created** |
| Rules | Jess DeNardo | other | **created** |
| Coding | Eric Priepke | software | exists |
| Sound Design | Jeff Dodson | sound | **created** |
| Artwork | Jonathan Bergeron | art | exists; flyer corroborates ("Featuring Amped Up Original Art by Jonathan Bergeron") |
| Animations | Joshua Clay | animation | exists (`josh-clay`, as "Josh Clay") — alias "Joshua Clay" added |
| Animations | Trent Armstrong | animation | **created** |
| Mechanical Engineering | Luke Underwood | mechanics | **created** |
| Mechanical Engineering | Paul Sulisz | mechanics | **created** |
| Electrical Engineering | Parker Dillmann | other | exists (`parker-dillman`) — renamed to "Parker Dillmann", Pinside form aliased |

Role mapping: Rules and Electrical Engineering have no dedicated role in the closed vocabulary (animation/art/design/mechanics/music/other/software/sound/voice), so both map to `other` with the block label recorded in the note — matching the draft-evidence-aggregator's mapping. No music credit exists to assert: the soundtrack is the band's licensed catalog.

## Feature mapping

Existing nodes attached: `{balls: 6}`, `{lightning-flippers: 2}` (created), `{mini-flippers: 2}` (created), `ramps` (count-less: 2 plastic + 1 metal + 2 jump ramps makes any single count ambiguous), `{jump-ramps: 2}` (created), `{habitrails: 4}`, `{subways: 1}`, `{scoops: 2}`, `{vertical-up-kickers: 1}`, `{magnets: 3}`, `{spinners: 2}`, `{diverters: 2}`, `{drop-targets: 2}`, `{ball-locks: 2}`, `{captive-ball: 1}`, `captive-ball-spinners` (the Crowd Amp-Up loop's spinner-inside-captive-loop is exactly this node), `standup-targets` (count-less: "3 standup targets" is scoped to the Backstage block, machine total unstated), `stop-magnets` ("magnet catch"), `diverter-magnets` ("hidden magnet … can divert"), `shaker-motors`, `led-general-illumination`, `interactive-speaker-lighting` ("Stereo Speakers with Interactive Full RGBW Illumination"), `stereo-sound`, `subwoofers`, `cabinet-armor`, `art-blades`, `{stage-spotlights: 3}`, `anti-reflection-playfield-glass` via new branded child, `ball-holding-toys` (Heart & Dagger catches and holds the ball), `static-toys` (Jon's New Jersey Guitar sculpt states no motion or ball interaction).

Created vocabulary (all generic or established branded-child pattern):

- `lightning-flippers` [flippers] — maker's own term; generic: Bally shipped Lightning Flippers on mid-80s machines, so an unrelated title plausibly attaches it.
- `mini-flippers` [flippers] — generic; mini flippers appear across makers.
- `jump-ramps` [ramps] — generic; the machine itself carries two.
- `infinity-glass` [anti-reflection-playfield-glass] — BoF's branded anti-reflective glass, the InvisiGlass/Magic Glass pattern exactly.
- `horizon-atmospheric-lighting` [interactive-cabinet-lighting] — BoF's branded inner-cabinet interactive lighting product, per the 0220 interactive-lighting DAG (maker product leaf under the location node, the AURA shape). Alias "HAL".

## Future unique features worklist

For the coming UniqueFeature entity (identities preserved in cite quotes): Bon Jovi Heart & Dagger magnetic ball catch and diverter (3-level, jump ramp, sculpt); Jon's New Jersey Guitar sculpt; Steel Horse 3-ball lock (back-orbit hidden magnet → VUK → lock); Crowd Amp-Up Loop ("first-ever loop-de-loop captive ball" with internal spinner); Crowd Surf jump ramp (outlane mini-flipper save shot); Backstage Access (3 standups, spinner, exit ramp, hidden scoop, magnet catch, second 3-ball lock); Bon Jovi Stage Sign (RGBW backlit); Sound Board Apron (backlit tape deck, meter, switch, gameplay-driven sliders); Spotlights & Trusses (3 functional spotlights); "Thunder From Down Under" shaker branding; "EverGloss" decal-art branding.

## Sought and not found

- A Bon Jovi service/safety manual or QRG — the maker's safety-manuals page (fetched 2026-08-10) carries only the three older titles.
- A primary player_count statement — only Pinside's crowdsourced 4.
- Any naming of BoF's control system / platform — no source names it for any BoF machine.
- An IPDB row — none exists yet for the model.
- Music-role credits — the soundtrack is the licensed band catalog; no composer credited anywhere.

## Not asserted (and why)

- **month** — the PR dates the reveal (July) and shipping (mid-August), not manufacture; 0220's precedent skips month on PR-dated models.
- **player_count** — crowdsourced-only support.
- **system / technology_generation** — no source names the platform; inferring solid-state from the LCD would be author inference, not evidence.
- **cabinet** — no source states the cabinet type in words.
- **multiball** — two physical 3-ball locks imply it but no source says the word; nothing quotable.
- **EverGloss / high-gloss decal art** — no decal-art vocabulary node exists, and creating one for cabinet decals (universal on modern machines) failed the Houdini granularity bar; branding kept in the worklist above.
- **standup-target count** — stated only within the Backstage block; machine total unknown.
- **dimensions** — the flyer states boxed/unboxed dimensions; the catalog has no field for them.
- **description** — a follow-up patch's job (inline-cite rules), matching 0220/0221.
- **themes beyond 0215's** — hard-rock already carries parent music in the DAG.

## Gate-run history

- 2026-08-10 `make validate`: first emit failed editorial lint (description over 80 chars; notes using 'the catalog' and 'node'); notes reworded to public-safe phrasing, then clean.
- 2026-08-10 `make verify-quote-verbatim`: one FAIL — the lighting quote's `[...]` spans were out of source order (Spotlights & Trusses sits in the Game Attractions block, before the Game Features HAL lines); reordered, then 253 verified / 0 failed / 41 SKIP-PDF (the flyer transcriptions, author-checked against the 150 dpi renders).
- 2026-08-10 `make verify-quote-support ARGS="0224"` (24 claims, ~160k tokens): **one warning, kept** — `static-toys` for Jon's New Jersey Guitar sculpt is classification-by-absence ("the note's reasoning, not the quoted text"), the same taxonomy-level warn 0220/0221 triaged and kept; the note records the reasoning per the charter. No re-run.
