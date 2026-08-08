# Model Extraction Test Cases

The reusable test corpus for the [AI Page Data Extractor](../plans/AiPageDataExtractor.md). Each row is a `(model, source page)` we re-run the extractor against after a slice batch, to measure recall (and precision) against a careful manual extraction. This exists to make extraction **repeatable and audited** — two of the failures the tool is built to end — rather than re-deciding the test set every time.

The cases are chosen to span every major group in the current data patches (the eremeka Japanese models, the tilt.it Italian models, the active-maker models) plus a classic well-known reference, and to spread across page _shapes_ (rich single-model page, terse maker-index, IPDB free-text Notes, whole-lineup marketing page) and _languages_ (English, Italian, Japanese) — because each stresses recall differently.

The field spec each case is scored against is [ModelPageExtractionChecklist.md](ModelPageExtractionChecklist.md).

## How to run one

```sh
make extract-page ARGS="<source-ref>"
```

The `source-ref` is an `http(s)` URL, or an `ipdb:<id>` / `opdb:<id>` / `youtube:<id>` scheme ref (resolved out of the pinexplore web cache / `explore.duckdb`). A page must be in the pinexplore cache first (`web_fetch.py <url>` there); an `ipdb:` ref needs `explore.duckdb`. **One packet per page** — a model with several source pages is run once per page and the master session unions the candidates; pages are never combined into a single call (they would share a satisficing budget).

## The corpus

| Model                                    | Group              | Source ref                                                                                                   | Page shape / language                                             | What it exercises                                                                                                                                                                                                                                                                                                       |
| ---------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `soccer-ace`                             | eremeka (Japanese) | `https://thetastates.com/eremeka/eremekaDisplay.php?mentionOnly=1&search=yes&tag=yokomono+~+flipper+pinball` | maker-index, Japanese/English                                     | recall from a shared index page where one machine's facts sit among many; non-English text                                                                                                                                                                                                                              |
| `home-run-nihon-tenbo`                   | eremeka (Japanese) | `https://earlyarcadesjapan.blogspot.com/2023/01/home-run-by-japan-outlook-entertainment.html`                | thin dedicated blog page (~480 chars), Japanese/English           | precision on a thin source (the San Marco role) — must not over-assert                                                                                                                                                                                                                                                  |
| `ultra-attack-nihon-gorakuki`            | eremeka (Japanese) | `https://earlyarcadesjapan.blogspot.com/2024/03/1972-ultra-attack-by-nihon-gorakuki.html`                    | rich lineage/attribution blog page (~8.6K), Japanese/English      | a licensed-art re-theme of a sibling base game (`variant_of` Jumbo Kick — **not** `conversion`); heavy people-mention traps (company reps, researchers, preservers surfaced as non-credits); EM tells (backbox lamps) vs a `pure-mechanical` misread                                                                    |
| `the-world-series-sankyo`                | eremeka (Japanese) | `https://earlyarcadesjapan.blogspot.com/2022/06/the-world-series-by-sankyo.html`                             | medium blog page (~3.3K), Japanese/English                        | a same-maker re-release (weak `variant`) vs a look-alike predecessor that is only a comparison (Home Run) — the `conversion`/lineage over-fire trap; `pinball` format from "buttons on the side, like a proper pinball machine"                                                                                         |
| `matador-gottlieb`                       | eremeka (Japanese) | `https://earlyarcadesjapan.blogspot.com/2024/02/matador-by-gottlieb-presumed.html`                           | medium blog page (~2.5K), English                                 | the rename-as-`variant` win (Matador = renamed Gottlieb Toreador) under uncertain attribution; a red-herring same-name game ("Toreador, Spain") and an `export`-tag over-fire                                                                                                                                           |
| `asteroid-killer-universal`              | eremeka (Japanese) | `https://earlyarcadesjapan.blogspot.com/2026/05/1979-asteroid-killer-by-universal.html`                      | thin blog page (~790 chars), English — **HOLD-OUT (blind)**       | precision floor: name/year/maker only. Must not infer `solid-state` or `video-game` from the 1979 date or the space name (the arcade-video-game-era trap)                                                                                                                                                               |
| `crazy-15-mark-iii-komaya`               | eremeka (Japanese) | `https://earlyarcadesjapan.blogspot.com/2022/04/1970-15-2nd-version-crazy-15-by-komaya.html`                 | medium blog page (~2.8K), Japanese/English — **HOLD-OUT (blind)** | a dated version/`variant` of a 1965 original; a founder interview is a `credits` + `themes` trap (company history and the founder watching children, not the machine's crew or theme)                                                                                                                                   |
| `joker-manilamatic`                      | tilt.it (Italian)  | `https://www.tilt.it/flipper_pinball/ipdb/manilamatic`                                                       | terse maker-index, Italian                                        | copy lineage in one list line (_"Joker (copia del Gottlieb's 'Monte Carlo')"_); the lineage slice on non-English text; siblings that entity-discovery will later surface                                                                                                                                                |
| `satellite-tv`                           | tilt.it (Italian)  | `https://www.tilt.it/flipper_pinball/ipdb/model-racing`                                                      | terse maker-index, Italian                                        | a re-run / variant lineage signal (_"Satellite TV (UFO re-run)"_); a different Italian maker for group breadth                                                                                                                                                                                                          |
| `alice-goes-to-wonderland`               | active maker       | `https://nicole.express/2026/nicole-in-blunderland.html`                                                     | long third-party review, English                                  | rich prose recall (anecdote/context material a field pass skips) — **run separately from the maker page below**                                                                                                                                                                                                         |
| `alice-goes-to-wonderland`               | active maker       | `https://wonderlandamusements.com/products/alice-goes-to-wonderland-pinball`                                 | maker product page, English                                       | the maker's own claims; unioned with the review packet by the master session                                                                                                                                                                                                                                            |
| `medieval-madness`                       | classic reference  | `ipdb:4032`                                                                                                  | IPDB Notes prose (no web page)                                    | the IPDB free-text (`free_text_for`) path; credits + gameplay recall from prose — see the [IPDB sub-corpus](#the-ipdb-sub-corpus)                                                                                                                                                                                       |
| `medieval-madness-remake-merlin-edition` | active maker       | `https://www.chicago-gaming.com/coinop/medieval-madness`                                                     | whole-lineup marketing page, English                              | **propose/dispose + attribution stress**: the page covers the whole remake lineup but most text is the Merlin edition — the cheap fan-out over-includes and the expensive arbiter must decide which claims attach to _this_ model vs. the line or other editions; solid-state tells (modern electronics, color display) |

## The IPDB sub-corpus

An `ipdb:<id>` ref's free-text Notes are a primary source of unstructured prose, so the sub-corpus spreads across nine decades (1937–2022) and both note sizes — a **large** note is a rich recall test, a **small** note is a precision test. All resolve out of `explore.duckdb`; the AI-extractable text is the editor-authored machine prose — Notable Features, Toys, Notes and Marketing Slogans, each under the IPDB page's own `Label:` (`ipdb_notes_text`, via `_Sources.free_text_for`). IPDB's structured fields — Manufacturer, Type, Players, Theme, and `DateOfManufacture` — are deterministic data resolved directly from the columns, so they are scored outside this recall corpus, as are IPDB's `Source:` / `Photos in:` rows, which describe IPDB's own paperwork rather than the machine. These cases probe tech-generation tells and other signals as they surface in the prose across eras.

What the Notes prose actually stresses is the slices the structured columns can't feed: **gameplay features** (every note lists them), **credits named in prose**, **conversion / remake lineage**, **reward type**, and occasionally **player_count** or a **tech-generation tell** inferred from the described mechanisms. The `What it exercises` column below reflects the prose, not the structured record.

| Model                    | Source ref  | Decade / note | What the Notes prose exercises                                                                                                                                                     |
| ------------------------ | ----------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mars-chicago-coin`      | `ipdb:3395` | 1937 · large  | 13 spring bumpers + mechanical backbox animation; EM tells (motor / stepping unit / relays) in prose; a cash-for-high-score _operator_ practice (enrichment, not a machine reward) |
| `grand-canyon`           | `ipdb:1065` | 1943 · small  | conversion lineage in a tiny note (_"a World War II conversion of Exhibit's 1941 'Double Play'"_) + a short feature list                                                           |
| `thing-chicago-coin`     | `ipdb:2531` | 1951 · large  | EM mechanics prose; **replay** reward stated outright; naming-origin anecdote (Phil Harris's "The Thing" song)                                                                     |
| `curling-rally`          | `ipdb:3037` | 1965 · small  | gameplay-only thin note — precision (flippers / pop bumpers / captive ball); no tech-gen/credit/lineage tell                                                                       |
| `six-million-dollar-man` | `ipdb:2165` | 1978 · large  | **player_count from prose** ("Six players can play"); credits in prose (designer Kmiec, artist Christensen); SS tells (6-/7-digit displays); long bulb-socket anecdote             |
| `solar-wars-sega`        | `ipdb:3273` | 1986 · small  | gameplay-only thin note — precision; must not invent a tech-gen/credit the prose doesn't hold                                                                                      |
| `funhouse`               | `ipdb:966`  | 1990 · large  | rich gameplay + disambiguated credits in prose (Ed Boon voices Rudy; Brian Eddy did **not** do sound)                                                                              |
| `big-bang-bar`           | `ipdb:5244` | 2007 · large  | **remake** lineage in prose (remake of Capcom's 1996 'Big Bang Bar'); production saga; note lists no features                                                                      |
| `big-buck-hunter-pro`    | `ipdb:5513` | 2010 · small  | near-empty note — only dimensions + MSRP; the precision floor (must surface enrichment, hallucinate no field)                                                                      |
| `wizard-headsup`         | `ipdb:6994` | 2022 · large  | **add-a-ball / novelty** reward + **conversion** lineage (of Gottlieb's 1977 'Team One') from prose; wedge-head cabinet; EM mechanics                                              |

**Year (and Manufacturer, Type, Players, Theme) are out of scope for AI recall here** — they live in structured columns, resolved directly and exactly, so no model reads them. The free-text pass reports `year` only where the Notes prose incidentally states it, and marking it absent otherwise is correct, not a miss. Note the tech-generation _tell_ still applies: where the prose describes the mechanisms (Mars's stepping unit → EM, SMDM's digit displays → SS), the tech-gen slice may legitimately infer from the prose — that is prose-derived, not a read of the structured `Type` column.

### IPDB sub-corpus ground truth (Notes-prose only)

Compact per case — only what the Notes/NotableFeatures prose supports; structured fields are excluded by construction.

| Case                     | Expected from prose                                                                                                                                                          | Must-NOT (traps)                                                                                                                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `mars`                   | gameplay: spring bumpers (13), backbox animation, Repeater bumpers; tech-gen `electromechanical` (motor/stepping/relay tells)                                                | reward `cash-payout` (the cash-for-score is a manual operator practice, not a machine mechanism); any `replay` ("no replays are given by the machine")                                           |
| `grand-canyon`           | gameplay: passive bumpers (12), kick-out hole; **lineage** `conversion` → Exhibit's 'Double Play'                                                                            | —                                                                                                                                                                                                |
| `thing`                  | gameplay: flippers (2), pop bumpers (2), passive bumpers (5), kick-out holes (3), blocking gate; **reward** `replay`; tech-gen `electromechanical`                           | a theme from the "The Thing" song (that's a naming anecdote, not a theme)                                                                                                                        |
| `curling`                | gameplay: flippers (2), pop bumpers (3), captive ball, kick-out hole. Everything else absent                                                                                 | any tech-gen/credit/lineage (prose gives none)                                                                                                                                                   |
| `six-million-dollar-man` | gameplay (7 listed); **player_count 6**; credits Greg Kmiec (Design), Dave Christensen (Art); tech-gen `solid-state` (digit displays)                                        | lineage from the Wizard / Capt. Fantastic / Skateball / Eight Ball Deluxe mentions (comparisons, not this game's lineage); a `variant` from the "City Slicker" whitewood name (a prototype name) |
| `solar-wars`             | gameplay (7 listed). Everything else absent                                                                                                                                  | tech-gen / credits / lineage — none in the prose                                                                                                                                                 |
| `funhouse`               | gameplay (rich); credits Ed Boon (Voice, "voice of Rudy"), Pat Lawlor, Brian Eddy                                                                                            | crediting Brian Eddy with **sound** (the prose explicitly denies it)                                                                                                                             |
| `big-bang-bar`           | **lineage** `remake` / `remake_of` → Capcom's 1996 'Big Bang Bar'; production_status `produced`; tech-gen `solid-state` (circuit boards)                                     | gameplay features (this note lists none); asserting Capcom as the maker (the prose complicates that — a structured-field matter)                                                                 |
| `big-buck-hunter-pro`    | nothing but enrichment (dimensions, MSRP $4,999) → catch-all `other`                                                                                                         | **any field at all** — the precision floor; no gameplay/tech-gen/reward/lineage is in this note                                                                                                  |
| `wizard`                 | gameplay (rich); **reward** `add-a-ball` + `novelty`; **lineage** `conversion` → Gottlieb's 1977 'Team One'; tech-gen `electromechanical` (drop targets, wedge head, no CPU) | inferring solid-state from the 2022 date (the prose describes an EM machine)                                                                                                                     |

## Notes / known wrinkles

- **`joker-manilamatic` and `satellite-tv` are maker-index pages, not single-model pages.** The relevant evidence for the target model is one terse line among a list of the maker's other machines. Extraction for these must focus on the target's line; the sibling machines are the raw material for the (later) entity-discovery slices, not fields of this model.
- **`home-run-nihon-tenbo` is deliberately thin.** It is the corpus's precision check — the tool should report the two or three facts the page supports and mark everything else absent, without parroting catalog defaults.
- **`medieval-madness` has no web page in the cache**; it is mined from its IPDB free-text Notes via `ipdb:4032` (structured columns excluded). It sits with the [IPDB sub-corpus](#the-ipdb-sub-corpus).
- **`medieval-madness-remake-merlin-edition`** was fetched into the cache from the manufacturer site; the URL is nominally the whole Medieval Madness remake lineup, so it is the natural home for the "which edition does this claim belong to" attribution test. A specific expected win: the lineage slice should flag it as a **`remake` of `medieval-madness`** (the page says _"the rebirth of the original... this remake"_) — the relationship, not just the tag.

## Ground truth

Per-case expected candidates are filled in as the field slices mature — a case's ground truth is only meaningful once the slices that would surface it exist. The model-info **field** slices (Section A of [ModelPageExtractionChecklist.md](ModelPageExtractionChecklist.md)) are now in, so those fields are scoreable; the entity-discovery, description-enrichment, and source-discovery slices are **not built yet**, so the "siblings / anecdotes / leads" a case exercises are out of scope for this round and their ground truth is deferred until those slices exist.

### How ground truth is scored

Ground truth is **page-scoped and target-scoped**: it records what a careful manual pass finds _on this page_ for _this model_ — not what is externally true of the machine. If the page is silent on `year`, ground truth is **absent** even when the year is well known elsewhere; if a fact on the page belongs to a sibling model, it is **not** part of the target's ground truth (it's a trap — see below).

Each run yields two independent scores against the table:

- **Field recall** — of the values in ground truth, how many did the tool surface as a candidate (verified quote)? Misses are the recall failure the tool exists to end.
- **Target-attribution precision** — how many candidates the tool attributed to the target actually belong to it? On maker-index and whole-lineup pages the fan-out has no notion of _which_ model is the target, so it surfaces sibling-model facts against the target; the **Traps** rows are the answer key for those false-includes. This is the score the index-page target-context fix is meant to move.

Two scoring conventions from the baseline runs:

- **Free-text redundancy is not a precision miss.** Enumerative slices (themes, gameplay features) over-include in the page's own words — `home-run` surfaced `Baseball / Home Run`, `Sports`, `Sport — Baseball`, `baseball/sports` for one theme. Count the _distinct real value_ once for recall; the redundant variants are prunable over-inclusion (the map-to-vocab step's job), not a false attribution.
- **Fields no slice covers yet read as n/a, not miss.** `system` and corporate-entity `location` are deferred in `build_slices`, so every case reports them `not-checked`; don't score them.
- **Hold-outs are blind — never tune against them.** Cases marked **HOLD-OUT (blind)** in the corpus table (`asteroid-killer-universal`, `crazy-15-mark-iii-komaya`) exist to catch overfitting: score them, but do **not** adjust a prompt, heuristic, or vocab in response to how they scored. When a hold-out regresses while the tuned cases hold, the tuning overfit. Promote a hold-out to a tuned case (and pick a fresh blind one) only deliberately, noting the swap.

Legend: **value** = expected candidate (with the quote basis); **absent** = page looked-at, says nothing; **n-a** = field cannot apply to this machine. Only fields with a non-absent expectation or a notable must-stay-absent are listed; every other Section-A field is plain absent.

### `joker-manilamatic` — `tilt.it/.../manilamatic` (maker-index, Italian)

The whole page is one maker's machine list; the target's evidence is a single line: _"Joker (copia del Gottlieb's 'Monte Carlo')"_. Nearly everything else on the page belongs to siblings.

| Field                             | Ground truth                                                                      | Basis                                             |
| --------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------- |
| name                              | Joker                                                                             | "Joker (copia del Gottlieb's 'Monte Carlo')"      |
| corporate_entity                  | Manilamatic (Roma, Italy)                                                         | "Manilamatic (Roma, Italy – Sig. Antonio Manili)" |
| copy (lineage)                    | `model_relationship` copy / unlicensed → Gottlieb's Monte Carlo                   | "Joker (copia del Gottlieb's 'Monte Carlo')"      |
| year                              | absent for Joker (the "1976" sits at maker/list level, not attributable to Joker) | "1976" (unattributed header)                      |
| themes, credits, all other fields | absent                                                                            | the one line states nothing else                  |

**Traps (must NOT attach to Joker):** themes `Tag Team` / `Arena` (sibling machines Out Law / Defender's copied games) and `Monte Carlo` (the _copied_ game's name, not a theme); credits `Tito Bresca` (designed sibling _Lucky Man_) and `Antonio Manili` (the company operator); lineage `copy` for Out Law→Tag Team and Defender→Arena (sibling copies). The baseline run surfaced all of these against Joker.

### `satellite-tv` — `tilt.it/.../model-racing` (maker-index, Italian)

Target evidence is one line: _"Satellite TV (UFO re-run)"_; the rest (a 1975 date, "video flipper") is stated about the sibling **UFO**, not Satellite TV.

| Field             | Ground truth                                  | Basis                                         |
| ----------------- | --------------------------------------------- | --------------------------------------------- |
| name              | Satellite TV                                  | "Satellite TV (UFO re-run)"                   |
| corporate_entity  | Model Racing (Montemarciano, Ancona, Italy)   | "MODEL RACING (Montemarciano, Ancona, Italy)" |
| variant (lineage) | re-run / `variant_of` → UFO                   | "Satellite TV (UFO re-run)"                   |
| year              | absent for Satellite TV (the "1975" is UFO's) | "l'UFO Model Racing e' del 1975"              |
| all other fields  | absent                                        | the one line states nothing else              |

**Traps (belong to UFO, not Satellite TV):** `year: 1975`; `game_format: video-game` / "video flipper".

### `home-run-nihon-tenbo` — earlyarcadesjapan blog (thin, Japanese/English)

The precision case — assert only the three or four facts the ~480-char page states.

| Field            | Ground truth                                         | Basis                                   |
| ---------------- | ---------------------------------------------------- | --------------------------------------- |
| name             | Home Run (ホームランゲーム)                          | "Name: Home Run - ホームランゲーム"     |
| year             | ~~1967 (approximate; page marks it "~~")             | "Year: ~1967"                           |
| corporate_entity | Nihon Tenbo (日本展望娯楽社)                         | "Company: 日本展望娯楽社 (Nihon Tenbo)" |
| themes           | baseball (weak — inferred from the name)             | "Home Run - ホームランゲーム"           |
| all other fields | absent — no display, tech-gen, format, status stated | —                                       |

**Must stay absent (the precision check):** `technology_generation`, `display_type`, `game_format`, `production_status` — the page supports none; the tool must not parrot catalog defaults.

### `medieval-madness` — `ipdb:4032` (IPDB Notes prose)

The credits-recall yardstick. Scored against the **machine prose only** (`free_text_for`): the AI never sees `Manufacturer`/`Type`/`Players`/`Theme`/year — those are structured columns, resolved deterministically, out of scope here.

| Field                | Ground truth (Notes prose only)                                                                                                   | Basis                                                                                               |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| gameplay_features    | flippers ×2, pop bumpers ×3, ramps ×2, autoplunger, catapult, habitrail, pop-up trolls (multiball via "Trolls!" mode)             | "Flippers (2), Pop bumpers (3), Ramps (2), Autoplunger. A left-side catapult…"                      |
| flipper_count        | 2                                                                                                                                 | "Flippers (2)"                                                                                      |
| credits (Voice)      | Tina Fey, Andrea Farrell, Greg Freres, Vince Pontarelli                                                                           | "Tina Fey … did the voices …" (etc.)                                                                |
| lineage              | a **remake** relationship is stated (the 2015 remake derives from this original) — informational on the original, not a tag on it | "This game was remade as Chicago Gaming Company's 2015 'Medieval Madness (Remake Limited Edition)'" |
| enrichment (`other`) | backglass vs. cabinet-sides naming; flyer dimensions/weight                                                                       | "The backglass shows … 'Medieval Madness' while the sides … 'Ye Olde Medieval Madness'"             |
| **out of scope**     | corporate_entity, technology_generation, player_count, themes, year, display — all structured, not in the Notes prose             | —                                                                                                   |

### `medieval-madness-remake-merlin-edition` — chicago-gaming.com (whole-lineup marketing, English)

Propose/dispose + attribution stress: the page covers the whole remake lineup, most prose is Merlin-edition-exclusive. The expected win is the lineage flag.

| Field                 | Ground truth                                                     | Basis                                                              |
| --------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------ |
| name                  | Medieval Madness (Merlin Edition)                                | page title / "Medieval Madness Merlin Edition"                     |
| corporate_entity      | Chicago Gaming Company                                           | "Chicago Gaming is pleased to offer…"                              |
| remake (lineage)      | `remake` tag + `remake_of` → Medieval Madness (the expected win) | "the rebirth of the original… this remake"                         |
| technology_generation | solid-state                                                      | "modern electronics… class D digital audio amplifier"              |
| display_type          | color DMD (candidate — "four times the number of dots"/color)    | "fully adjustable color display… four times the number of dots"    |
| game_format           | pinball                                                          | "this multi-ball game"                                             |
| gameplay_features     | multiball, exploding castle, motorized drawbridge, pop-up trolls | "the exploding castle, motorized drawbridge and two pop-up trolls" |
| themes                | Medieval, 15th-century kingdoms                                  | "Step back in time to the Middle Ages of the 15th century"         |

**Traps (Merlin-edition-exclusive vs. base-remake vs. line):** the King of Payne 3D topper is Merlin-only ("included on the Merlin Edition"); RGB General Illumination and the XL/HD color display are "Medieval Madness Remake" line features, not necessarily this edition's defining fields; the upgrade-kit table rows (`0611`, `0711-*`) are catalog SKUs, not model fields. The arbiter decides which attach to _this_ model.

### `soccer-ace` — thetastates eremeka index (89-machine maker index, Japanese/English)

The extreme over-surface case: the target's evidence is one four-line entry among **89 machines** spanning 1965–2019. Everything about the other 88 is a trap.

The target entry: _"1969 Socker Ace - サッカーエース (Soccer Ace) by 日本展望娯楽社 (Nihon Tenbo Entertainment Company — Nitten) / players ~ head-to-head / theme ~ sports ~ football (soccer) / yokomono ~ flipper pinball"_.

| Field            | Ground truth                                                       | Basis                                                            |
| ---------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| name             | Socker Ace / Soccer Ace (サッカーエース)                           | "1969 Socker Ace - サッカーエース (Soccer Ace)"                  |
| year             | 1969 (exact — not "~")                                             | "1969 Socker Ace"                                                |
| corporate_entity | Nihon Tenbo Entertainment Company (Nitten)                         | "by 日本展望娯楽社 (Nihon Tenbo Entertainment Company — Nitten)" |
| game_format      | pinball                                                            | "yokomono ~ flipper pinball"                                     |
| themes           | soccer / football                                                  | "theme ~ sports ~ football (soccer)"                             |
| player_count     | 2 / head-to-head                                                   | "players ~ head-to-head"                                         |
| all other fields | absent — the entry carries no display, tech-gen, cabinet, gameplay | —                                                                |

**Traps (belong to the other 88 machines):** the year of any other entry (baseline surfaced `1965`, the first machine — a recall MISS of the target's 1969); every theme on the page except soccer (baseline surfaced ~50); any `variant` from the "payout re-theme" / re-run entries (baseline surfaced 8, none the target's); the `Kinnikuman II` franchise (a 2002 Banpresto machine); and non-flipper gameplay (medal/prize/candy/videogame) from the arcade machines.

### `alice-goes-to-wonderland` — nicole.express review (long third-party review, English)

Rich single-model prose. Strong solid-state evidence (the review names the CPU) and the display, plus a textbook polarity trap.

| Field                    | Ground truth                                                            | Basis                                                                                                                     |
| ------------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| name                     | Alice Goes to Wonderland                                                | "Alice Goes to Wonderland"                                                                                                |
| corporate_entity         | Wonderland Amusements                                                   | "another: Wonderland Amusements"                                                                                          |
| year                     | 2026                                                                    | "Pinball in my House, 2026: Alice Goes to Wonderland"                                                                     |
| game_format              | pinball                                                                 | "a sub-$1000 home actual pinball machine"                                                                                 |
| technology_generation    | solid-state                                                             | "An STM32F103ZET6 ARM, a Cortex-M3 32-bit ARM CPU core"                                                                   |
| technology_subgeneration | ss-pc (commodity ARM, 2013+)                                            | "STM32F103ZET6 ARM … CPU core"                                                                                            |
| display_type             | lcd                                                                     | "The score is displayed on a small LCD screen"                                                                            |
| cabinet                  | floor                                                                   | "The playing height is pretty good for me at 6'1\""                                                                       |
| production_status        | produced                                                                | shipped Kickstarter unit, assembled and played                                                                            |
| reward_type              | free-play                                                               | "There are a series of controls on the front, in lieu of a coin slot"                                                     |
| tag                      | home-use                                                                | "home pinball machine … Especially for home use"                                                                          |
| themes                   | Alice in Wonderland (Mad Hatter, Queen of Hearts, Caterpillar)          | "the Queen of Hearts's castle … a bouncy Mad Hatter … the Hookah Caterpillar"                                             |
| gameplay_feature         | flippers, pop bumpers, loops, multiball, ball lock, mechanical launcher | "a few loops and pop bumpers … does have a multiball … based around locking in balls … The launcher is purely mechanical" |
| credits                  | absent (no named individual — "minds behind Arcade1up" is a company)    | —                                                                                                                         |

**Must-NOT-assert (polarity / comparison traps):** `drop-targets` — the page states it **lacks** them (_"lacks proper drop targets, relying on LED lights on the drop-like panels instead"_); `ss-discrete` / a 1980s year — _"If you like 1980's machines … you'll be right at home"_ is an aesthetic comparison, the ARM CPU pins it to `ss-pc`; the machines named for comparison (Terminator 2, Attack from Mars, Firepower II, ToyShock, Arcade1up, Stern) and the forthcoming TMNT game are entity-discovery leads, not this model's fields.

### `alice-goes-to-wonderland` — wonderlandamusements product page (maker product page, English)

The maker's own spec sheet — dense structured facts. Same model, unioned with the review by the master session.

| Field                    | Ground truth                                                 | Basis                                                                                                     |
| ------------------------ | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| name                     | Alice Goes to Wonderland Pinball                             | "Alice Goes to Wonderland Pinball"                                                                        |
| corporate_entity         | Wonderland Amusements                                        | "180-day limited warranty from Wonderland Amusements"                                                     |
| game_format              | pinball                                                      | "a fully mechanical home pinball machine"                                                                 |
| technology_generation    | solid-state (tells: game code, Wi-Fi, software updates)      | "triggering real flippers, bumpers, spinners, and modern game code … Wi-Fi-enabled … software updates"    |
| technology_subgeneration | ss-pc                                                        | "Wi-Fi-enabled … software updates"                                                                        |
| production_status        | produced                                                     | "We plan to produce as many as we can reasonably support"                                                 |
| cabinet                  | floor                                                        | "steel legs with leveling feet … 60\" H"                                                                  |
| reward_type              | free-play                                                    | "It is not equipped with coin operation"                                                                  |
| tag                      | home-use                                                     | "designed for home use only … built for home arcade fans"                                                 |
| themes                   | Alice in Wonderland (Mad Hatter, Cheshire Cat, White Rabbit) | "the Mad Hatter, Cheshire Cat, White Rabbit, and other curious characters"                                |
| gameplay_feature         | flippers, slingshots, bumpers, ramps, multiball, spinners    | "Real mechanical flippers, slingshots, bumpers, ramps, and multi-ball … real flippers, bumpers, spinners" |
| credits                  | Carlos Mendoza III (Art)                                     | "Original illustrations by Carlos Mendoza III"                                                            |
| display_type             | absent (no score display described)                          | —                                                                                                         |

**Must-NOT-assert:** `export` — the page is emphatic US-only (_"THIS PRODUCT SHIPS TO US ADDRESSES ONLY … we currently only ship to the United States"_), which is the opposite of the `export` tag; `technology_generation: pure-mechanical` — _"fully mechanical"_ is marketing for the real (non-virtual) flippers, contradicted by the game code / Wi-Fi tells. The `TMNT Pinball` mention and other-manufacturer parts (`Stern`, `Jersey Jack`) are stray FAQ references, not this model's facts.

### `ultra-attack-nihon-gorakuki` — earlyarcadesjapan blog (rich lineage/attribution, Japanese/English)

The eremeka recall + lineage yardstick. Most of the ~8.6K-char page is manufacturer history and a detailed argument that Ultra Attack is a licensed-art re-theme of an earlier Nihon Tenbo game — so the target's own fields are few, and the page is dense with people and sibling machines that are entity-discovery material, not this model's fields.

| Field                 | Ground truth                                                                              | Basis                                                                                                                          |
| --------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| name                  | Ultra Attack (ウルトラアタック)                                                           | title / "ウルトラアタック (Ultra Attack)"                                                                                      |
| year                  | ~1972 (approximate — the page explicitly hedges)                                          | "he places the year 'around 1972', so … I will stick with '~1972'"                                                             |
| corporate_entity      | Nihon Gorakuki (日本娯楽機); Nihon Tenbo [presumed collaborator]                          | "by 日本娯楽機 (Nihon Gorakuki) & 日本展望娯楽社 (Nihon Tenbo) [presumed]"                                                     |
| technology_generation | electromechanical (backbox/bulb-lamp tells; no CPU)                                       | "all of the lamps are in the exact same position"; "the bulb lights at the bottom right and left corners"                      |
| themes                | Ultraman / Return of Ultraman (Ultraman Jack, MAT / Monster Attack Team)                  | "references characters and images from 帰ってきたウルトラマン / Return of Ultraman, like Ultraman Jack, and the MAT logo"      |
| lineage               | `variant_of` → Jumbo Kick (a licensed-art re-theme on the Beat & Spark / Jumbo Kick base) | "Ultra Attack is a Jumbo Kick with new artwork"; "utilize the Nihon Tenbo game Beat & Spark as a base … a fresh … art package" |
| gameplay_feature      | kick controls (L Kick / R Kick), bulb lights                                              | "the Ultraman Attack control panel say 'L Kick' and 'R Kick'"                                                                  |
| all other fields      | absent                                                                                    | —                                                                                                                              |

**Traps (must NOT attach to Ultra Attack):** `credits` for **Kaichi Endo** (the maker's company representative), **@naosunjer** (a collector who _preserved_ a copy), **Onitama-san** (an eremeka _researcher_), **Jay Stafford** (IPDB _photographer_) — all named in prose, none a game creator (baseline surfaced all four); `lineage: conversion` (the derivation is an art-only re-theme = `variant`, not a cabinet-reuse conversion — baseline fired `conversion` twice alongside the correct relation); `tag: manufacturer-retheme` (the re-theme is **across makers**, NGK over Nihon Tenbo — not a maker re-theming its own design — baseline fired it); `technology_generation: pure-mechanical` (the lamps/backbox wiring make it EM — baseline misread it PM); a `year` in the "late 1970s" (the address sticker — the page argues the Ultraman theme forces ≥1971 and settles ~1972). Sibling machines (Soccer Ace, Socker, Beat & Spark) are entity-discovery leads.

### `the-world-series-sankyo` — earlyarcadesjapan blog (medium, Japanese/English)

A same-maker re-release vs. a look-alike predecessor — the lineage over-fire trap.

| Field            | Ground truth                                                                         | Basis                                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| name             | The World Series (ワールドシリーズ)                                                  | "Name: The World Series - ワールドシリーズ"                                                                    |
| year             | 1972 (first appearance; a 1976 re-release is noted but is not the manufacture year)  | "The earliest mention I can find of The World Series is in 1972"                                               |
| corporate_entity | Sankyo (三共)                                                                        | "Manufacturer: 三共 (Sankyo)"                                                                                  |
| game_format      | pinball                                                                              | "the buttons are now on the side, like a proper pinball machine"                                               |
| themes           | baseball / sports                                                                    | "a baseball diamond which uses balls to simulate players running around the bases"                             |
| gameplay_feature | baseball-diamond playfield, side buttons                                             | same                                                                                                           |
| lineage          | weak `variant` → New World Series (the 1976 re-release, art change) — flag the doubt | "The 1976 re-release is referred to as ニューワールドシリーズ (New World Series) … just a different backglass" |
| all other fields | absent                                                                               | —                                                                                                              |

**Traps:** `lineage: conversion` / any derivation from **Home Run** — the Home Run playfield resemblance is an explicit _comparison / influence_ ("echoes"; "appears to be nearly identical"), not a derivation of World Series (baseline fired `conversion → Home Run`); `tag: manufacturer-retheme` (the 1976 re-release is better modeled as a `variant`; the page doesn't frame it as an official retheme — baseline fired it); `technology_generation: pure-mechanical` (baseline fired it; the page gives no clear PM/EM tell, so tech-gen is absent/weak, not PM); `year: 1976` as the manufacture year (that is the re-release).

### `matador-gottlieb` — earlyarcadesjapan blog (medium, English)

The rename-as-`variant` win under uncertain attribution.

| Field            | Ground truth                                                                             | Basis                                                            |
| ---------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| name             | Matador                                                                                  | "Company: Gottlieb [presumed]" / title                           |
| year             | ~1966                                                                                    | "Matador appears in a 1966 Senyo Kogyo catalogue"                |
| corporate_entity | Gottlieb [presumed] — attribution explicitly uncertain                                   | "Company: Gottlieb [presumed]"                                   |
| lineage          | `variant_of` → Toreador (Gottlieb 1956) — a rename with an alternate backglass (the win) | "appears to be a renamed version of Gottlieb 1956 game Toreador" |
| themes           | bullfighting / matador (weak — from the name)                                            | title / "Matador"                                                |
| all other fields | absent                                                                                   | —                                                                |

**Traps:** any lineage / relation to **"Toreador, Spain"** (a _different_ 1972 Japanese game the page raises only to _dismiss_ the name theory); `tag: export` (the page frames a rename mystery, not a manufacturer export program — baseline fired `export`); `technology_generation` (no mechanism tell on the page, and pre-1970s narrows only to PM-or-EM — leave absent, do not invent). Toyo Playing Machine and Senyo Kogyo are entity-discovery leads.

### `asteroid-killer-universal` — earlyarcadesjapan blog (thin, English) — **HOLD-OUT (blind)**

The precision floor. A ~790-char page that is mostly dating methodology and source provenance — it supports only name, year, maker (and a weak theme from the name). **Do not tune against this case** (see [scoring](#how-ground-truth-is-scored)).

| Field            | Ground truth                                                     | Basis                                                    |
| ---------------- | ---------------------------------------------------------------- | -------------------------------------------------------- |
| name             | Asteroid Killer                                                  | title                                                    |
| year             | 1979 (the archive's first-appearance rule; it flags IPDB's 1980) | "if it's shown in 1979, we're marking that down as 1979" |
| corporate_entity | Universal (ユニバーサル)                                         | "by ユニバーサル (Universal)"                            |
| themes           | space / asteroids (weak — from the name only)                    | title / "Asteroid Killer"                                |
| all other fields | absent                                                           | —                                                        |

**Must stay absent (the precision check):** `technology_generation`, `game_format`, `display_type`, `gameplay_feature`, `lineage` — the page describes no mechanism. Specifically the tool must **not** infer `solid-state` or `video-game` from the 1979 date or the space/"Asteroid" name (the arcade-video-game-era association is the trap). Baseline passed this — it surfaced only year/status/theme and left tech-gen and format absent.

### `crazy-15-mark-iii-komaya` — earlyarcadesjapan blog (medium, Japanese/English) — **HOLD-OUT (blind)**

A dated version/`variant` of an earlier original, on a page whose bulk is a founder interview — a `credits` and `themes` trap. **Do not tune against this case.**

| Field            | Ground truth                                                                                                                  | Basis                                                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| name             | Crazy 15 game mark III (クレイジー15ゲーム [マークIII])                                                                       | "Name: クレイジー15ゲーム [マークIII] (Crazy 15 game mark III)"                                                    |
| year             | 1969                                                                                                                          | "This version came out in 1969"                                                                                    |
| corporate_entity | Komaya (こまや)                                                                                                               | "Manufacturer: こまや (Komaya)"                                                                                    |
| title            | Crazy 15 (shared across the series)                                                                                           | "Crazy 15 was first released in 1965"                                                                              |
| lineage          | `variant_of` → Crazy 15 (the 1965 original) — new art + slightly altered geometry; flag the doubt (borderline separate Model) | "Crazy 15 was first released in 1965. This version came out in 1969 and has a few differences. The art is all new" |
| gameplay_feature | flippers (side-mounted flipper buttons)                                                                                       | "flipper buttons are on the side of the cabinet now"                                                               |
| all other fields | absent                                                                                                                        | —                                                                                                                  |

**Traps:** `credits` for the **Komaya founder** and his **cousin** (the interview recounts founding the company in 1960/1965 — company history, not a game crew — baseline surfaced both); `themes` of **children** / **amusement parks** (these come from the founder describing watching children play, not the machine's subject — baseline surfaced them); separate Komaya models named in the interview — **New Crazy 15** (a 1977 audio sequel), **Baseball**, **Rock Paper Scissors** (グーチョキパー) — and competitor machines (Kansai Seiki's "Stereo Talkie", "Mini Drive") are entity-discovery leads, not this model's fields or lineage.
