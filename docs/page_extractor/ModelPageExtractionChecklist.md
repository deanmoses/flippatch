# Model Page Extraction Checklist

This is a checklist for an AI to use when extracting data from a source page in order to create scalar claims about a pinball model.

## Goal of the checklist

The primary job of this checklist is to defeat cross-field satisficing — the habit of harvesting the three or four salient facts and moving on — by forcing an explicit decision on every field the catalog can hold.

## Provenance of the checklist items

The checklist items are distilled from the authoritative flipcommons docs — `docs/DataPatchAuthoring.md`, `docs/DataPatches.md`, `docs/DomainModel.md`. Those are the source of truth; this is a derived working aid and will drift when they change. When a rule here and a rule there disagree, they win. Update this file when the domain model grows a field, a vocabulary gains a term, or the authoring rules move.

## How to use it

- **The completeness sweep (Section A) is mandatory and answered field-by-field.** For every field, record one of: a value **with a verbatim quote**; **"absent"** (you looked, the source says nothing); or **"not-applicable"** (the field cannot apply to this machine — e.g. `system` and `technology_subgeneration` on an electromechanical machine, `display_subtype` when the display type has no subtypes). Never leave a field unconsidered, and you cannot honestly mark one "absent" without having looked — that is the whole point.
- **"Absent" is a real, useful answer.** Recording "the page states no year" is a deliverable — it distinguishes _the source lacks it_ from _nobody checked_.
- **Over-include, then prune.** When in doubt whether the source supports a value, surface it as a candidate with its quote and flag the doubt; a false positive is cheap to drop, a forgotten field is the failure this exists to end.
- **Never invent.** Only assert what a source supports. An unset field reads as "unknown"; a wrong claim reads as fact. If you can't quote it, leave it unset and say so.

## A. Completeness sweep — did the source state it?

Answer every box: value + verbatim quote, or "absent". Legal values are listed inline so each option is considered, not just the obvious one. Vocabulary is authoritative in the live catalog; the lists below are a reading aid and may lag the DB.

### A1. Model — the machine

- [ ] **name** — the machine's name as it appeared on the cabinet.
- [ ] **year** (and **month**) — the **manufacture** date. NOT the trade-show presentation, reveal, announcement, or flyer date — those go in the `note:`/description, never in `year`. If two sources disagree, first check whether they date _different events_ before calling it a conflict.
- [ ] **title** — the canonical game-design identity this model belongs to (every model has one, even a one-off).
- [ ] **corporate_entity** — the specific corporate incarnation that produced it (models link to CorporateEntity, not Manufacturer).
- [ ] **technology_generation** — `pure-mechanical` (gravity/springs, no electricity) / `electromechanical` (relays, solenoids, score motors, score reels, backglass lights — no CPU) / `solid-state` (microprocessor-controlled). **Infer it from the machine's mechanisms and display — a sanctioned inference; the page needn't state the generation outright. Lean on the "tells," not the date.**
  - **Solid-state tells** — an electronic or video display of any kind (segmented/alphanumeric LED, dot-matrix/DMD, LCD, CRT/video screen), or any mention of a CPU/microprocessor, circuit boards, ROMs, software, or a named electronic system. **A screen is a near-certain giveaway of solid-state.**
  - **Electromechanical tells** — relays, solenoids, stepping units, a score motor, mechanical score reels, chimes/bells, backglass bulbs — and no CPU.
  - **Pure-mechanical tells** — no electricity at all: gravity, springs, purely mechanical scoring.
  - **Dates** cut only one way, at the low end: a machine predating the electromechanical era (roughly pre-1930s) must be `pure-mechanical`, and nothing before the mid-1970s can be `solid-state` (that narrows to PM-or-EM, not a single answer). **Do not infer `solid-state` from a recent date** — EM and PM machines are still built today, so a late date rules nothing out.
- [ ] **technology_subgeneration** — a refinement of the generation above; only meaningful once the generation is settled. For `solid-state`: `ss-discrete` (off-the-shelf CPU boards, 1977–1990) / `ss-integrated` (purpose-built platforms like WPC, 1986+) / `ss-pc` (commodity PC/ARM hardware, 2013+).
- [ ] **game_format** — one of: `pinball` / `bagatelle` / `shuffle` / `pitch-and-bat` / `slot-machine` / `video-game` / `gun-game` / `miscellaneous`. (A non-pinball machine silently defaulting to `pinball` is a classic error — decide it explicitly.)
- [ ] **production_status** — one of: `announced` (not yet shipped) / `produced` (commercially sold, even in tiny quantity) / `unreleased` (intended for production but cancelled; may have prototypes) / `one-off` (one/few-of-a-kind, never meant for sale — gifts, props, tests) / `aftermarket` (modified by someone other than the maker; usually paired with the `unofficial-retheme` tag).
- [ ] **display_type** — one of: `score-reels` (mechanical drums) / `backglass-lights` (fixed bulbs) / `alphanumeric` (segmented LED) / `cga` (color CRT) / `dot-matrix` (DMD) / `lcd` (HD video screen).
- [ ] **display_subtype** — a refinement of the display type; only meaningful once the type is settled. `alphanumeric`: `nixie-tube` / `7-segment` / `16-segment`. `dot-matrix`: `plasma-dmd` / `color-led-dmd`.
- [ ] **cabinet** — one of: `floor` (standard free-standing) / `tabletop` / `countertop` / `cocktail` (horizontal, flat glass top).
- [ ] **system** — the electronic hardware platform it runs on. **Look for this field only when both hold: the machine is solid-state, and its manufacturer has systems in the catalog.** Systems belong to a manufacturer, and only certain makers (the major solid-state houses — Williams, Bally, Gottlieb, Stern, Data East/Sega, Atari, …) have any; a maker with none catalogued, and every electromechanical or pure-mechanical machine (which runs no system at all), is _not-applicable_, not "absent." When it does apply it's a large, manufacturer-scoped vocabulary (70+ entries and growing — e.g. Williams System 11B, Bally AS-2518-35, Gottlieb System 80B, Stern SPIKE 2, CGC Pinball Controller/OS), so it isn't enumerated here: capture the platform as the source names it and resolve it against that manufacturer's systems in the live catalog, flagging an unrecognized one as a possible new System.
- [ ] **player_count** — max number of players the machine supports.
- [ ] **flipper_count** — the number of flippers, when stated. A dedicated scalar field, distinct from the `gameplay_feature` flipper count — set both when known.
- [ ] **reward_type(s)** — what reward mechanism(s) are at work? One or more of: `replay` (free game for a high score/objective/match) / `add-a-ball` (extra ball, not a free game) / `novelty` (no reward, amusement only) / `cash-payout` (coins dispensed by scoring) / `ticket-payout` (redeemable tickets by score) / `free-play` (no coin required to start).
- [ ] **tag(s)** — labels that don't fit a structured field; a bounded set of independent binary labels, so decide each present/absent. (The copy/conversion lineage relationships and the `remake` tag are handled as the lineage questions in A2, not here.)
  - [ ] `home-use` — designed or marketed for home use rather than commercial coin-op routes.
  - [ ] `prototype` — an engineering sample, design proof, or pre-production test unit.
  - [ ] `widebody` — a wider-than-standard cabinet and playfield.
  - [ ] `export` — manufactured for markets outside the United States.
  - [ ] `unofficial-retheme` — a re-skin by a non-manufacturer (fan/operator/modder); pairs with the `aftermarket` production status.
  - [ ] `manufacturer-retheme` — an official re-theme a manufacturer applied to one of its own designs.

The Model also carries three open, catalog-resolved collections — **themes**, **gameplay features**, and **credits** — handled together in A6, and the lineage relationships below.

### A2. Lineage & derivation — is this machine a copy, remake, conversion, or variant of another?

Copy and conversion are **`model_relationship`** edges (`relationship_type` × `license_status` × target); remake is a tag; variant is `variant_of`. A copy/conversion edge names its target with `target_machine` when the source names the specific game, or a `target_label` (plain text) when the source describes the kind — _"a copy of a Gottlieb game"_, _"a kit for several late-70s Gottliebs"_ — without naming one. Each relationship claim needs its own cite (the line stating the lineage). Watch the polarity trap: _"its companion model is a widebody"_ does **not** make _this_ model a widebody.

- [ ] **copy?** — a reproduction of another maker's design on newly built hardware (a copy/clone/bootleg; common among mid-century Italian/Spanish makers). If yes: add a **`model_relationship`** with `relationship_type: copy` and a `license_status` — `unlicensed` for a bootleg, `licensed` for an authorized build, else `unknown` (do not guess from silence) — targeting the copied game (`target_machine`, or `target_label` when unnamed). Keeps a normal `produced` status; a copy target routinely points across Titles.
- [ ] **remake?** — a newly manufactured recreation of an earlier title with new technology. If yes: set the **`remake` tag**, and **`remake_of`** → the original when named. Original and remakes share one Title.
- [ ] **conversion?** — reuses another machine's physical cabinet with a new playfield/theme. If yes: add a **`model_relationship`** with `relationship_type: conversion` — or **`conversion_kit`** when it's sold as a kit of parts to install rather than a complete machine — targeting the donor (`target_machine`, or `target_label` for a plural/unnamed donor set).
- [ ] **variant?** — set **`variant_of`** → the model it's a cosmetic/packaging variant of (same gameplay, different dress: art, plaques, toppers, plastics). No paired tag. (A source listing EM and SS versions, or 1P/2P/4P editions, describes **separate Models**, not variants.)

### A6. Open collections — enumerate, resolve, create-if-new

These are not single-value fields; each is an open collection resolved against the live catalog. The same discipline applies to all three: **list every member the source supports — don't stop at the obvious** (the within-field satisficing trap); resolve each against the live catalog's vocabulary; and treat a member the catalog doesn't hold yet as a candidate **new entity to create** (`create: true`), never something to silently drop. These are large or hierarchical vocabularies, so they aren't enumerated here — how to check what already exists (a DB query or otherwise) is the calling session's call.

- [ ] **theme(s)** — the subjects/settings the machine evokes (a DAG hierarchy). An unmatched theme → a candidate new **Theme**.
- [ ] **gameplay_feature(s)** — the play mechanisms it has (multiball, ramps, drop targets, …; a DAG hierarchy), each with a **count** where the source gives one ("4 ramps", "3 flippers"). An unmatched feature → a candidate new **GameplayFeature**.
- [ ] **credit(s)** — every person credited, **with the reason** (a bare name is nearly useless; the reason is what maps to a role). Each credit is a person + a role from: `Design` / `Concept` / `Art` / `Dots/Animation` / `Mechanics` / `Music` / `Sound` / `Voice` / `Software` / `Other` (one person may hold several — each is a distinct credit). A person not in the catalog → a candidate new **Person** to create before crediting. Put a credit on the **series** only when it applies to the whole line; otherwise on the specific **model**.
  - [ ] **biographical facts** — birth/death dates, nationality, aliases — capture when the source states them.
