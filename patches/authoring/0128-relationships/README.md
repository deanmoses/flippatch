# Bootleg / Licensed-Build / Conversion sweep

This is the hand-maintained preface for a cross-repo data-patch campaign, written so any session can grab one maker and author its patch without re-doing the research. It holds the scope, the policy calls, the authoring recipe, and the per-maker open questions. The candidate models themselves — slugs, resolved targets, classifications, IPDB note snippets — live in the **generated** [Worklist.md](Worklist.md), which is produced mechanically from `cands.json` and carries no editorial judgment. It is not itself a patch. Read [DomainModel.md](../../../../flipcommons/docs/DomainModel.md) (Bootlegs / Licensed builds / Conversions) and [DataPatchAuthoring.md](../../../../flipcommons/docs/DataPatchAuthoring.md) before authoring, and treat every IPDB note in the worklist as a _recall aid to vet against the full page_, not as authority.

## What this campaign does

Three lineage relationships link a derivative machine to the design it reproduces:

- **`licensed_build_of` + tag `licensed-build`** — an authorized twin: a complete machine a licensee/foreign subsidiary built under license for another market (e.g. VIFICO building Gottlieb/Premier in Spain). Keeps normal `produced` status. This is the pattern established by the Bally Wulff patch [0124-bally-wulff-models.yaml](../../0124-bally-wulff-models.yaml).
- **`bootleg_of` + tag `bootleg`** — an unauthorized copy of another maker's design (e.g. Maresa copying Gottlieb). Same shape as licensed builds; the only difference is authorization.
- **`converted_from`** — a conversion kit / re-themed machine built on another game's existing hardware (playfield + backglass swap on donor boards), e.g. the Italian conversion houses on Bally/Williams donors.

**The key structural fact that makes this cheap:** every foreign machine below is _already seeded_ as its own model record (slug + corporate entity), and so is the US original it reproduces. Unlike the Italian sweep (which created models from tilt.it), this campaign mostly just **adds a relationship + tag to an existing seeded model** and cites the IPDB note. No model creation, no title surgery in the common case.

## How the candidates were found

`pinexplore/explore.duckdb` → `ipdb_machines.Notes` joined to seeded `models` on `ipdb_id`. Self-description regexes classified each note: license language (`under licen…`) → licensed; copy language (`(this is) a copy of…`) → bootleg; conversion language (`conversion kit for…`) → conversion. Targets were auto-resolved by parsing the note's `Maker's YEAR 'Name'` reference back to a seeded slug. The generator scripts (`gen_worklist.py`, `gen_doc.py`) and intermediate data (`cands.json`) live alongside this README. To refresh: run `gen_worklist.py` from the pinexplore repo root (it reads `explore.duckdb` and writes `cands.json`), then `gen_doc.py` (it reads `cands.json` and writes `Worklist.md`). `gen_doc.py` emits **only** tables — it never writes prose or judgment, so regenerating can't clobber this README or launder a guess into the worklist. Anything you want a future session to weigh belongs here in the README, never in the generator.

**Caveats when using the tables:**

- `→ target slug` is best-effort — most are right, but a handful resolve to the wrong game when the note's first quoted title isn't the original (e.g. LAI `cosmic-princess`); always confirm the target before writing `*_of:`.
- Rows marked **TODO** in the target column need manual resolution.
- Re-read the full IPDB note (and prefer a web-cache source where one exists) for the verbatim `cite` quote.
- In the conversion section, a few "makers" are the US originals themselves (`bally-manufacturing-corporation`, `williams-electronics-incorporated`, `d-gottlieb-company`, `premier-technology`). These are in-house or same-lineage conversions, or reverse-direction note matches — vet each one hard; some may not be `converted_from` candidates at all.

## Decisions made

- **One patch per maker** — _except the licensed-build batch below._ The default is one file per maker covering all its relationships. The exception: the clear-cut licensed builds (IPDB note literally says "under license") were pulled across makers into a single patch, [0128-licensed-builds.yaml](../../0128-licensed-builds.yaml). So Segasa's and Alben's remaining _bootleg_ rows, and Taito do Brasil's _bootleg_ rows, still get their own per-maker patches later.
- **1965+.** Let's first focus on 1965+ models. Pre-1965 "copy of" curiosities (1930s–50s French/US/German copies, wartime conversions) are in the Deferred section of [Worklist.md](Worklist.md), let's do the others first.
- **Excluded false positives** (not in the tables): Stern Electronics / Bally Midway / Genco _originals_ whose notes merely mention _their_ licensees; theme licenses that aren't builds of another machine (Spooky's Domino's Pizza); video recreations (Global VR UltraPin); and never-produced / prototype announcements (Dutch Pinball Bride 25th, The Pinball Factory Crocodile Hunter, Retro Pinball Bank-A-Ball).
- **Reverse-mine of US originals** ("also produced as …") was run per request: it surfaced 28 references but on inspection they are almost all player-count/technology _variants_ and same-maker _reissues_ (correctly not bootleg/licensed), with only a couple of Brazilian cross-maker items already caught by the forward pass. The forward self-description mine is authoritative; the reverse pass added nothing new in-scope.
- **Bally Wulff is done** (0124) and omitted here.

## Progress

- **[0128-licensed-builds.yaml](../../0128-licensed-builds.yaml) — done.** 27 licensed builds whose IPDB note explicitly states "under license", each adding `licensed_build_of` + `tag: [licensed-build]` to the existing seeded model: VIFICO ×13 (Gottlieb/Premier), LAI ×7 (Stern), Segasa ×4 (Williams), plus Taito do Brasil `meteor-2`, Automaticos MonteCarlo `lortium-2`, American Home Entertainment `the-getaway-high-speed-ii-2`. Structural + editorial lint pass; applied and verified 27/27 against a fresh db.pre-0039 → ingest snapshot (correct target + tag on every row). Three licensed rows were **held back** — see the open questions below.

Everything else in the worklist (all bootlegs, all conversions, and the three held-back licensed rows) is still unauthored.

## Italian-sweep overlap — check these makers before authoring

Several Italian (and a few German) conversion/bootleg houses in the worklist were already touched by the Italian sweep (patches 0079–0116), which _created_ models from tilt.it data. The seeded IPDB records in the worklist are usually _separate_ records from the sweep's — but before authoring any of the makers below, rebuild the localhost dev DB (db.pre-0039 → migrate → ingest `~/dev/flippatch/patches/`) and check whether the maker's models are already tagged or duplicated. These may belong folded into the Italian series near 0109 rather than in a fresh patch:

`renato-montanari-giochi`, `skillgame-dba-renato-montanari-giochi`, `bell-games`, `nuova-bell-games`, `bell-coin-matics`, `l-v-mambelli`, `dama-srl`, `europlay`, `elettrocoin`, `idi`, `emmepi`, `ripepi`, `ditta-ripepi-spa`, `giuliano-lodola`, `nordamatic`, `pinball-shop`, `lori`.

## Authoring recipe (mirror [0124-bally-wulff-models.yaml](../../0124-bally-wulff-models.yaml))

For each model: `expect: { ipdb_id: NNNN }`, a `cite` with `ref: ipdb:NNNN` and a **verbatim** quote from the note establishing the relationship, then set `licensed_build_of:` / `bootleg_of:` / `converted_from:` to the target slug and `tag: [licensed-build|bootleg]`. Same-name derivatives may share the original's title; renamed ones sit under their own title (title placement is independent of the lineage link). Validate behind the flipcommons SQLite snapshot loop, then `make validate` here. Committing and `make push` are the user's call.

## Slug convention (applies to licensed, bootleg, and conversion patches)

When a derivative's slug ends in a disambiguation number (`spin-out-2`, `arena-2`), rename it to end in the maker instead (`spin-out-maresa`, `arena-vifico`) — **but only when the derivative carries the same name as the original it reproduces.** That is the whole point of the rename: a same-named build (VIFICO's _Arena_ vs Premier's _Arena_; Maresa's _Spin Out_ vs Gottlieb's _Spin Out_) has a numeric suffix only to separate it from the identically-named original, and `-maker` says which one it is. When the names differ — Maresa's _Tahiti_ copies Gottlieb's _Tropic Isle_, its _King Ball_ copies _Rack-A-Ball_ — the number is separating unrelated same-named games, not the original, so appending the maker clarifies nothing. **Leave those slugs alone.** (Across the in-scope bootleg/conversion rows this splits almost exactly in half.)

The maker suffix is the IPDB **trade name** slugified where the manufacturer has one (`[Trade Name: LAI]` → `lai`, `[Trade Name: Maresa]` → `maresa`), else the corporate-entity slug with legal-form and parent tails stripped (`vifico-sa` → `vifico`, `taito-do-brasil-a-division-of-taito-japan` → `taito-do-brasil`). Treat that as a **default to vet, not gospel**: some trade names slugify awkwardly (`R.M.G.` → `r-m-g` — prefer `rmg`?), some entities have no trade name and a long legal slug (`fipermatic-industria-comercio-…` — pick a hand-short form), two entities can share a suffix (both RMG rows → `r-m-g`), and the US-maker rows in the conversion section (`bally-…`, `williams-…`) collapse to `bally`/`williams` — check each result against existing slugs for collisions before writing.

Both rules are implemented in [`slug_convention.py`](slug_convention.py) (`maker_suffix()` and `rename()`, pure functions) — import it from each patch's generator rather than re-deriving. 0128 followed this; its 25 renames were all same-name builds, so nothing there needed holding back on name grounds.

## Per-maker open questions

Maker-specific doubts that need a session's judgment before authoring, keyed by the corporate-entity slug used in [Worklist.md](Worklist.md). These are leads and doubts, not verdicts — resolve each against a source you trust, and let the evidence pick the tag.

### `procedimientos-electromagneticos-de-tanteo-y-color` (Petaco) — licensed or bootleg?

The IPDB notes say only "a copy of Gottlieb's …", which on its own points to bootleg. A quick web pass turned up secondary accounts that Petaco/Recel (founder Juan Paredes) imported and adapted Gottliebs and then built their own copies — rather than under a Gottlieb licence — with VIFICO cast as the actually-licensed Spanish Gottlieb builder: <https://www.flippers.be/recel.html>, <https://www.flippers.be/vifico.html>. Treat those as leads, not proof. Confirm against a source you trust before tagging these `bootleg`; if you find evidence of a real licence, some may be `licensed-build` instead. Note too that `recel` and `petaco` exist as separate corporate-entity slugs in the catalog with 0 models — worth understanding how they relate to this `procedimientos-…` entity before authoring.

### `fipermatic-industria-comercio-importacao-e-exportacao-ltda` — licensed or bootleg?

The classifier defaulted these to `bootleg` on the "a copy of" wording, but every note also says "Gottlieb Made in Brazil": IPDB describes Gottlieb shipping unassembled components to the Manaus free-trade zone for local assembly by Fipermatic — which could be _sanctioned_ (→ `licensed-build`) rather than a bootleg. The IPDB note never uses the word "licence", so it cannot by itself support a `licensed-build` claim. Don't inherit the `bootleg` default without looking: find a source that establishes or denies Gottlieb's authorization, and tag whatever your source actually supports. (The `zarza-2` row copies Bally's Xenon, not Gottlieb — the "Gottlieb Made in Brazil" framing may not even apply to it; check separately.)

### Three licensed rows held back from 0128 — which single original?

These three carry an explicit "under license" note (so `licensed-build` is not in doubt) but were left out of [0128-licensed-builds.yaml](../../0128-licensed-builds.yaml) because `licensed_build_of` takes _one_ target and theirs isn't clear-cut:

- `cosmic-princess` (LAI, ipdb:3967) — note says "manufactured in Australia by LAI under license from Stern Electronics", but the **only** "Cosmic Princess" in IPDB/the catalog _is_ this LAI record; there is no seeded Stern original to point at. Decide whether the Stern original should be created first, or whether this is effectively the primary record and shouldn't carry a `licensed_build_of` at all.
- `high-ace-2` (Segasa, ipdb:5424) — the note names two Williams originals: "Same design as Williams' 1973 'Dealer's Choice'. Same design and coloring as Williams' 1974 'Lucky Ace'." Pick the one it actually reproduces (`dealers-choice-2` vs `lucky-ace`).
- `star-flite` (Sonic/Segasa, ipdb:4979) — note names "the 2-player Williams' 1974 'Super-Flite' and the 4-player Williams' 1974 'Strato-Flite'" (`super-flite` vs `strato-flite`). Pick one, or reconsider how a two-original export build should be linked.

## The worklist

The candidate tables — 298 in-era models grouped licensed / bootleg / conversion, plus the deferred pre-1965 list — are in the generated **[Worklist.md](Worklist.md)**. Regenerate with the scripts described under [How the candidates were found](#how-the-candidates-were-found); never hand-edit it.
