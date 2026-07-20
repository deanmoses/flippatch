# Corpus-sweep hardening notes — first run against 0128-relationships

> **Historical log (pre-redesign).** These notes date from when the sweep judged three separate self-FK fields (`converted_from` / `bootleg_of` / `licensed_build_of`) with a per-field `FieldSpec.target_other_maker`. After ModelRelationships shipped, the sweep was redesigned to judge one `model_relationship` field over the `catalog_modelrelationship` join table (`relationship_type` × `license_status` × target). Field-level API details below (column names, `FieldSpec` flags) no longer match the code, but the _findings_ (defects, calibration, false greens) still hold and carried into the new gates. See the current [CorpusSweepOperating.md](../../../../docs/corpus_sweep/CorpusSweepOperating.md).

Kept while operating `make sweep` on the 298-row 0128 candidate set (the tool's first real use). Ordered by severity. "Report immediately" items were surfaced to the user in-session.

## Run shape (context)

- 298 candidates, one `--no-ai` reconcile + one `--limit 10` trial + one full run (`--resume --max-requests 320`): 288 trusted-tier calls, ~591k tokens, a few minutes, well under a dollar. Resumable `results.json` and the trial→full loop worked exactly as documented.
- Full-run dispositions: fill 140, agrees 70, uncertain 26, unresolved-target 23, ambiguous-target 21, no-claim 7, hint-mismatch 6, conflict 5. Zero `set-but-unsupported`.

## DEFECT 1 — the campaign's own `(Maker)` title-suffix convention hides targets from the resolver (false conflicts + latent false fills)

> **✅ FIXED — verified against the live dev DB 2026-07-17.** The resolver no longer depends on the name/alias index alone: `SweepCatalog.by_base_name` (`scripts/ai_corpus_sweep/catalog.py:125`) keys every model under **both** its full and its `strip_parenthetical`'d name, and `resolve_target` gathers candidates from it alongside the index, looking up both the stated title and its own stripped form. Regression test: `test_resolve_reaches_maker_suffixed_names` (the `supersonic` shape), plus `test_resolve_strips_note_side_parenthetical` for the note-side case.
>
> Re-verified empirically against the rebuilt dev DB (all 117 patches through 0158 applied), replaying every row this section documented: all six suffix-hidden Maresa targets (`jacks-open`, `pro-football`, `road-race`, `surfer`, `target-pool`, `top-card`) now resolve `unique` to the right model; the whole Surf Champ cluster resolves to `surf-champ` from all three copies (including `surf-champ-maresa`, which now correctly `agrees` rather than escalating `ambiguous`); `domino-maresa` → `domino-2` correctly. **One documented row still does not resolve — `fly-high` → `supersonic` — but the suffix is no longer the cause; see DEFECT 6.**

**Severity: high.** `EntityIndex.build` (`scripts/common/catalog/entity_index.py:246`) indexes every model by its **name** and alias rows only — **never its slug**. This campaign's naming convention renames same-name builds/originals to `"<Title> (<Maker>)"` (e.g. `supersonic` → name "Supersonic (Bally)", `domino-2` → "Domino (Gottlieb)"). Those normalize to `supersonicbally` / `dominogottlieb`, so a note's bare "Supersonic" / "Domino" no longer resolves to them by name. When the correct target also lacks a title record named after the bare title, it drops out of the candidate set entirely and the resolver narrows to a **different same-titled sibling**.

Confirmed false **conflicts** (both catalog values are CORRECT; the sweep would have you corrupt them):

- **ipdb:3974 `fly-high` converted_from** — catalog `supersonic` (Bally 1979, name "Supersonic (Bally)") is correct; it was literally just fixed in `0142-geiger-conversions.yaml` today. Sweep resolved the note's "Supersonic" to `supersonic-2` (Zaccaria 1977) — the only record still named exactly "Supersonic" — and flagged a conflict. Note's own "Bally / 1979" contradict the resolved Zaccaria/1977 target, which is the tell.
- **ipdb:4637 `domino-maresa` bootleg_of** — catalog `domino-2` ("Domino (Gottlieb)", 1968) is correct. Sweep resolved "Domino" to `domino-5` (Gottlieb, year unknown) and flagged a conflict.

**This is systemic for this campaign, not an edge case.** The whole premise of 0128 is same-name builds where BOTH the copy and the original get `(Maker)` suffixes — and the original is exactly the resolution target. So every such target is suffix-hidden. Confirmed: all **six** `unresolved-target` Maresa rows have their target seeded and renamed `"<Title> (Gottlieb)"`, which the sweep could not see:

| row (copy)            | reported   | true target (seeded, suffix-hidden)            |
| --------------------- | ---------- | ---------------------------------------------- |
| `jacks-open-maresa`   | unresolved | `jacks-open` (Jacks Open (Gottlieb), 1977)     |
| `pro-football-maresa` | unresolved | `pro-football` (Pro-Football (Gottlieb), 1973) |
| `road-race-maresa`    | unresolved | `road-race` (Road Race (Gottlieb), 1969)       |
| `surfer-maresa`       | unresolved | `surfer` (Surfer (Gottlieb), 1976)             |
| `target-pool-maresa`  | unresolved | `target-pool` (Target Pool (Gottlieb), 1969)   |
| `top-card-maresa`     | unresolved | `top-card` (Top Card (Gottlieb), 1974)         |

Add the Surf Champ trio, `domino-maresa`, `fly-high`, `king-pin-maresa`, and likely more, and a large fraction of the 70-row escalation queue is DEFECT-1 noise a human resolves trivially (the target is right there, just suffixed). **Recommendation: fix the resolver and re-run (sub-dollar) before authoring — hand-correcting 20+ false escalations is both wasteful and risks missing a suffix-hidden `fill` mispick.**

Latent **false-fill** risk from the same mechanism: a `fill` whose correct suffixed target is hidden could silently resolve to a wrong sibling. Across this run the blast radius was small — an audit cross-checking every green/conflict row's resolved-target maker+year against the note's stated maker+year found only the two conflicts above plus DEFECT 2 below; all other suffix-adjacent rows (e.g. `monte-carlo-vifico` → `monte-carlo-gottlieb`) resolved **correctly** because the suffixed target shared a title record named after the bare title, which the `types=("model","title")` title-expansion recovered.

More instances found in the `hint-mismatch` / `ambiguous-target` buckets (same root cause, so DEFECT 1's reach is wider than the two conflicts):

- **Surf Champ cluster.** `surf-champ` is named "Surf Champ (Gottlieb)" (Gottlieb 1976) — the genuine original. All three copies cite "Gottlieb's 1976 'Surf Champ'" but the suffix hid it, so: `surf-champ-2` resolved to `surf-champ-3` (wrong), `surf-champ-3` resolved to `surf-champ-2` (wrong), and `surf-champ-maresa` — which **already correctly holds `surf-champ`** — was flagged `ambiguous-target` instead of `agrees`. Correct target for all three is `surf-champ`. So DEFECT 1 also manufactures false `ambiguous-target` escalations, not just false conflicts.

**Fix candidates (not applied — noting per brief):** index the model `slug` as an additional surface in `EntityIndex.build`; and/or index a suffix-stripped form of `"<Title> (…)"` names; and/or have `resolve_target` also try the note title against title records more aggressively. The audit query lives at `scratchpad/xcheck.py` — worth folding into the tool as a built-in "resolved target's facts disagree with the note" warning on green rows.

## DEFECT 2 — a lone same-named candidate greens as `fill` even when the note's maker AND year both contradict it (silent false green)

**Severity: high (silent).** `resolve_target` (`scripts/ai_corpus_sweep/gate.py:120`) applies year/maker filters but, by design, "never wipes the set to zero" — so when there is exactly **one** catalog match for the title and it matches neither the stated maker nor year, that single wrong candidate still returns `status="unique"` and dispositions as a green `fill`.

- **ipdb:4386 `1963-a-l-twins` converted_from — FALSE GREEN.** Note: "a conversion of Williams' 1963 Major League". The catalog's only "Major League" is **PAMCO, 1934** (`major-league`, ipdb 1525) — a different game; the real donor (Williams 1963) is not seeded. Sweep greened `fill → major-league`. Authoring it verbatim would link the wrong donor. Correct disposition should have been `no-model`/`unresolved`.

**Fix candidate:** when a stated year AND a stated maker BOTH fail to match the sole surviving candidate, escalate (`unresolved`/`uncertain`) instead of returning it as `unique`. A single "filter skipped" is tolerable; two independent stated facts failing on the only candidate is a strong not-in-catalog signal.

**Refinement — year-before-maker short-circuit.** `narrow()` returns early once the set is down to one, so the **maker filter never runs if the year filter already narrowed to a single candidate** — even when that candidate's maker contradicts the note. Seen at **ipdb:5115 `tanforan`** (`hint-mismatch`): note "a conversion of **Bally's** 1949 'Champion'"; the catalog's only 1949 Champion is **Chicago Coin** (`champion`), so year 1949 → 1 (Chicago Coin) and the stated maker "Bally" was never checked. The real donor is a Bally Champion (catalog has `champion-4`, Bally / year-unknown; also `champion-2` Bally 1939, `champion-3` Bally 1934) — neither the sweep's `champion` nor the hint's `champion-2` is clearly right; this needs manual/web-cache resolution. Fix: apply all stated-fact filters before checking uniqueness, or re-check that the lone survivor doesn't contradict an as-yet-unapplied stated fact.

## DEFECT 3 — a same-maker "target" presented as a confident conflict (found by the user, first row reviewed)

**Severity: high (a false accusation against a correct catalog value).** ipdb:6196 `big-ben-segasa-italy` licensed_build_of: the note says "the add-a-ball version of **Segasa's** 1975 'Big Ben'" — Segasa's own replay game, itself the licensed build of Williams' original. The model named that chain link (`big-ben-segasa`) as the target; the quote was verbatim, the resolution unique, the stated facts self-consistent (Segasa == Segasa) — and no gate encoded the domain rule that a machine cannot be a licensed build (or bootleg) of its own maker's game. REVIEW.md led with "catalog holds `big-ben-williams-1975` but the note supports `big-ben-segasa`", which is exactly backwards; the catalog was right.

**Fixed same day (test-first):** `FieldSpec.target_other_maker` (True for licensed_build_of and bootleg_of, False for converted_from — in-house conversions are legitimate) + a `dispose` gate: a unique resolution whose maker equals the subject's maker escalates as the new `same-maker-target` disposition, never a conflict or a fill, with wording that blames the chain, not the catalog. Judge guidance for both fields now instructs the model to follow the license/copy chain to the OTHER maker's original or answer uncertain. Scan confirmed exactly one instance in the 298-row run. Post-regate: the conflict bucket is now precisely the three verified genuine seed errors (`race-stars`, `road-racer`, `flesh-and-blood`).

## DEFECT 4 — fills shipped cite quotes checked only for existence, never for support (reported in this session's final hand-audit)

**Severity: medium (editorial/shipping quality; occasionally masks a claim-level problem).** `check_quote` proves a quote is verbatim, never that it establishes the claim (the documented AiCommon §3 gap) — e.g. `jungle-queen-2`'s auto-selected quote described the kit's contents while the donor was established by a neighboring sentence. The repo already owned the real check (`ai_lint.citation_verify`'s trusted-tier quote-supports-claim rule) and the sweep didn't call it.

**Fixed same day (test-first):** every would-be `fill` now passes a quote-supports-claim call reusing ai_lint's prompt/schema/tier verbatim — the same standard `make verify-citations` holds shipped patches to — failing into the new `quote-unsupported` review disposition; the verdict persists on the row (`quote_supported`) so `--regate` stays offline, and `--verify-fills` retrofits the check onto runs judged before the gate existed. The judge prompt now also instructs the model to quote the note's establishing sentence. Retrofit over this run's 138 fills (138 calls, ~232k tokens): **6 demoted** — mostly claim-level catches (a note hedging between two donors, a kit fitting "many" Gottlieb games, a quote about a different machine) — while `jungle-queen-2` itself passes, because the rule judges the quote in its surrounding source, exactly as the shipped-patch gate will.

## DEFECT 5 resolution (and-joined donors) + maker grouping — fixed

Both items from the first authoring session are addressed (test-first, 426 tests green):

- **And-joined donors:** a would-be `fill` whose quote names a catalog model besides the subject and the resolved target now escalates as `multi-target-quote` (deterministic n-gram scan of the quote against the model/title index, base-name aware so the target's own suffixed name never trips it; runs before the support call, so no AI is spent on it, and `--regate` retrofits it over stored rows for free). Judge guidance now also instructs: two-or-more joint donors → verdict uncertain.
- **Residual (quote-omitted co-donors) closed by re-judge:** the quote-scoped scan cannot see donors the model left out of its quote (`good-year`'s three-game list). A note-level scan found 16 candidate fills; re-judged under the joint-targets guidance (30 calls), 14 re-confirmed as clean fills with fresh support checks and 2 correctly flipped to `uncertain` — `good-year` and `mondial-bank`, the latter a previously-undetected two-donor green.
- **Maker grouping:** REVIEW.md's "Ready to author" section now groups fills under per-maker headings (largest first) — the campaign's one-patch-per-maker work plan, no separate results.json pass needed.

## Feedback incorporation pass (2026-07-13) — all five open items addressed

Every un-addressed item in this file was implemented test-first (433 tests green), then the run was re-gated for free:

- **Exact-name tie-break** (petaco `rey-de-diamantes` observation): when title-group expansion leaves several fact-compatible candidates but exactly the note-named ones are distinguishable, resolution now prefers the exact name match (true same-name pairs stay ambiguous). Promoted `sky-star`, `jet-surf`, `vulcan-iv` (and one straight to `agrees`) out of `ambiguous-target`; the three new fills passed fresh quote-supports-claim checks.
- **Shared-target merge warning** (rmg `space-orbit` pair): REVIEW.md's per-maker fill sections now flag ⚠ when ≥2 same-maker fills resolve to one target — the joint slug/merge decision surfaces before authoring.
- **Per-maker roster** (petaco UX note): REVIEW.md now opens with a maker × (fill / green / escalations-by-disposition) table, so completing a maker no longer needs a results.json scan.
- **Pre-narrow visibility** (hardening UX note): the resolution trail now names the initial candidate set before narrowing, so a silently-dropped better candidate is visible in the artifact.
- **Labeled reasons** (hardening UX nit): the model's own reason renders as "model: …", distinct from gate reasons.

Post-regate state also reflects the authored patches (petaco/rmg rows now `agrees`): fill 87 (all support-checked), agrees 130, review 74.

## Non-defects / false alarms in my own auditing (for calibration)

- **Premier == Gottlieb.** All 13 VIFICO rows show note maker "Premier" resolving to maker slug `gottlieb`. Correct — one brand, many corporate entities (README). Not a mismatch.
- **`royal-skittle` → `miss-bowling` (WIMI Games)** — note says "Willy Michiels'"; WIMI = **Wi**lly **Mi**chiels. Correct maker-alias resolution; only my crude substring check flagged it.
- **±1-year "mismatches"** (lady-death→mata-hari, flash 1979 vs note 1978, jungle-life 1973 vs 1972, spanish-eyes 1972 vs 1971, silverball-mania, xs-os, vector) all resolve to the correct maker and game; note years are just slightly off from catalog years. Genuine, trustworthy fills.

## Genuine catches (the tool doing its job — wrong existing values)

- **ipdb:4015 `race-stars` / ipdb:3971 `road-racer` converted_from** — seed points at `evel-knievel-em` (Bally EM, 1976); both notes say "Bally's **1977** 'Evel Knievel'" = the SS record `evel-knievel` (1977). Same EM→SS seed-error class 0142 already fixed for `lady-death`; corroborated by the sibling `cosmodrome` note citing "the original Bally MPU with EK ROMs" (SS). Neither the catalog nor the Worklist hint had this right — a genuinely new catch.
- **ipdb:5157 `flesh-and-blood` converted_from** — catalog `pinball-champ-82` (Zaccaria "Pinball Champ '82", 1982); note says "Zaccaria's **1983** 'Pinball Champ'" = `pinball-champ` (1983). Worklist hint already suspected this; sweep confirms.

## UX / friction notes

- `results.json` `considered` lists only the **final narrowed** candidate set, not the initial title matches. That makes it hard to tell from the artifact alone whether a clean `fill` silently dropped better candidates during narrowing — the exact info needed to spot DEFECT 1/2 by eye. Consider recording the pre-narrow match count/list too.
- REVIEW.md renders two `**why here:**` bullets per row (one gate reason, one model reason) with the same bold label — mildly confusing; distinct labels ("gate:" / "model:") would read better.
- `--no-ai` RECONCILE reproduced byte-for-byte across reruns against an unchanged DB — good determinism.

## Resolution (2026-07-12) — both defects fixed, all rows re-gated for free

Both defects were fixed in `scripts/ai_corpus_sweep/` the same day, test-first (11 new tests reproducing the exact shapes above: the suffixed Supersonic, Major League, Champion, Premier-vs-Gottlieb, ±1-year noise), and the stored answers were re-bucketed with `--regate` — **zero further AI calls**, since verdict/quote/stated-target were already persisted per row.

- **DEFECT 1 fixed** in the sweep (not `EntityIndex`): `SweepCatalog.by_base_name` indexes every model under its full **and** parenthetical-stripped name, and `resolve_target` gathers from it alongside the entity index (also trying the note title's own stripped form). Verified post-regate: all six Maresa "unresolved" → `agrees`; `domino-maresa`, `fly-high`, `king-pin-maresa` → `agrees`; Surf Champ trio → `fill`/`agrees` on the real `surf-champ`.
- **DEFECT 2 fixed** as recommended, generalized: filters now narrow by **maker first**, then year (exact preferred, ±1 fallback, year-unknown candidates never excluded), and a unique survivor whose maker/year **contradict** the note's stated facts escalates as the new `facts-mismatch` disposition instead of greening. `1963-a-l-twins` no longer greens; `tanforan` resolves to Bally's `champion-4` (escalated `hint-mismatch` for the manual call this file recommends). The scratchpad cross-check (`xcheck.py`) is thereby a built-in deterministic gate on every row.
- **Bonus rule from this file's ambiguous-bucket analysis:** an ambiguous resolution that _contains_ the catalog's current value now dispositions `agrees` (consistency, not doubt) instead of dragging a settled row into review.
- **Net effect:** review queue 81 → 70 → 70-with-honest-contents; `agrees` 70 → 83; the genuine catches (`race-stars`, `road-racer`, `flesh-and-blood`) remain conflicts, ready to author.
- **Ergonomics from the same run's pain:** `--status` (progress off `results.json`, anytime, free), `--regate`, per-row `REVIEW.md` rewrite, and a first-line Ctrl-C safety contract; SESSION-BRIEF.md now mandates backgrounding the full run and checkpointing with the user on systematic defects instead of triaging ahead of a fix.

## Authoring pass notes (2026-07-12) — j-martina maker, 0144

First patch authored purely off the hardened REVIEW.md (15 converted_from rows). Calibration was good; one minor observation.

- **OBSERVATION — a multi-donor note greens as a single `fill` without flagging the second donor.** `the-happy-musketeers` (ipdb:5285): note reads "Conversion of Gottlieb's 1967 'Hi-Score' **and** Gottlieb's 1967 'Super Score' …". The sweep greened it `fill → hi-score`; both donors are seeded and equally valid, and `converted_from` is single-valued. The green is not _wrong_ (Hi-Score is a real donor and the quote supports it), but the tool silently picked the first-resolved of two `and`-joined donors and gave the author no signal that a choice was being made. **Severity: low** (I caught it by reading the note and held the row, matching 0143's `playtime` dual-donor hold). **Fix candidate:** when a note's target span contains a second `'<Title>'` conjoined by "and"/"&"/"and also" that _also_ resolves to a distinct catalog model, escalate as an `ambiguous-target` / new `multi-donor` disposition rather than greening the first. This is the "and" analogue of the "or maybe" hedge the `quote-unsupported` gate already catches (ipdb:6838 `playtime-5`).
- **Calibration — the three j-martina escalations were all correct holds, no false escalations.** `star` (ipdb:6321, "conversion of an unidentified 4-player replay game") and `wine-grower` (ipdb:5537, "a conversion of an unknown 1960's era Gottlieb game") have genuinely unnamed donors; `unknown-25` (ipdb:6594) shares only a _layout_ with Quick Draw and the note never calls it a conversion — correctly `uncertain`, not a converted_from candidate.
- **Calibration — all 15 `fill` rows for this maker verified verbatim against the full note and resolved to the correct Gottlieb donor with matching year.** No false greens in this maker's slice. The DEFECT-2 maker/year gate held: every note's stated "Gottlieb / 19xx" matched the resolved donor.
- **UX nit — `fill` rows give no maker in REVIEW.md's "Ready to author" list**, so grouping the 132 fills into per-maker patches (the campaign's unit of work) requires a separate pass over `results.json`'s `maker` field or a DB join. A `— maker: <slug>` suffix on each Ready-to-author line would let a session pick its maker straight from REVIEW.md. _(Since fixed: the "Ready to author" section is now grouped under per-maker headings, which is what the petaco pass below used to pick its maker.)_

## Authoring pass notes (2026-07-12) — petaco maker, 0145 + 0146

Second bootleg maker authored off REVIEW.md; first same-name-merge patch of this campaign to go through the sweep (Maresa 0140/0141 predated the sweep). 12 `fill` + 1 `ambiguous-target` = 13 rows. Calibration was clean; one recurring friction point.

- **Calibration — all 13 petaco rows correct.** The 12 fills verified verbatim against the full note and resolved to the right Gottlieb/Williams original with matching year (the DEFECT-2 maker/year gate held throughout). No false greens in this maker's slice. The one `ambiguous-target` (`rey-de-diamantes`) was also correct on the merits — see below.
- **Two same-name copies were _already_ co-titled with their original in the seed** (`grand-slam-7` in `grand-slam-world-series`, `spin-a-card-2` in `spin-a-card-hearts-and-spades`). The recipe still applies (slug → `-petaco`, `(Petaco)` name suffix, relationship) but the title move and the 0146 orphan-delete are skipped for those two. The sweep doesn't surface current-title membership, so this only came out of a DB check — fine, but worth knowing that "same-name merge" ≠ "always a title move + orphan delete."
- **OBSERVATION (recurring, low severity) — `ambiguous-target` fires even when one candidate is an exact title match.** `rey-de-diamantes` (ipdb:4368, "A modified copy of Gottlieb's 1967 'King of Diamonds'"): the resolver reported _5 matches for 'King of Diamonds'; maker 'Gottlieb' → 4; year 1967 → 4_ and listed `king-of-diamonds`, `diamond-jack`, `hit-a-card`, `solitaire`. Three of those four are not titled "King of Diamonds" at all — the title search over-matched (shared token/group?), and then the maker+year filters couldn't narrow because all four are Gottlieb 1967, so it escalated. But exactly one candidate's title _equals_ the note's stated title after normalization (`king-of-diamonds`), and it also already shares the copy's OPDB group — an unambiguous answer a human resolves in seconds. **Fix candidate:** before dispositioning `ambiguous-target`, prefer a candidate whose normalized title name exactly equals the note's stated target title; disposition `fill` (or at least rank it first) instead of dragging an exact-title hit into review. This is the same shape as several other `ambiguous-target` rows (`ice-show`, `flag-ship`, `rocket-iii`) where a near-name sibling pads the candidate list around one exact-title original. **Severity: low** (review-time cost, not correctness).
- **UX — authoring "one patch per maker" needs a maker's _escalated_ rows too, not just its fills.** `rey-de-diamantes` was petaco's only non-fill row and it lives in the un-grouped "Needs review" section, so completing the maker required a `results.json` scan for `maker == 'petaco'`. The per-maker grouping that now exists for fills would help in "Needs review" too (or a per-maker roster line: "petaco — 12 fill, 1 ambiguous").

## Authoring pass notes (2026-07-13) — rmg maker, 0148 + 0149

Third bootleg maker off REVIEW.md (R.M.G. / Renato Montanari Giochi, Italy). 14 rmg fills; 12 authored, 2 held. Second sweep-driven same-name-merge patch (6 merges + 5 renamed bootlegs + 1 conversion-kit). Calibration clean on the 12 authored rows; one new same-name-merge gap worth a fix.

- **Calibration — all 12 authored rmg fills correct.** Each verified verbatim against the full IPDB note and resolved to the right original (Gottlieb ×10, Bally ×1 big-valley, Bensa ×1 space-time-2) with matching year/maker. No false greens. The DEFECT-2 maker/year gate held throughout. `the-best-wizard` (ipdb:4919) correctly kept converted_from + conversion-kit (note "Conversion kit for…") rather than bootleg — the sweep's field split held.
- **OBSERVATION (new, medium) — two fills resolving to the SAME target imply an un-authorable same-name merge, and the sweep gives no cross-row signal.** `space-orbit-2` (ipdb:4783) and `space-orbit-3` (ipdb:5458) are BOTH R.M.G. copies named "Space Orbit!" that green as `fill → space-orbit` (the single seeded Gottlieb original). Individually each is a clean, correct fill. But together they are an un-authorable same-name merge: the recipe would rename both slugs to `space-orbit-rmg` (collision) and give both the identical name "Space Orbit (R.M.G.)" in one title, and the naming convention explicitly requires the base name to collide with **exactly one** model in the merged title. **Held both**, pending a call on how to disambiguate the pair (e.g. `-rmg` / `-rmg-2`, or keep them co-titled under their existing shared title without a merge). This is the "multiple copies of one original" analogue of petaco's already-co-titled observation — the sweep processes rows independently and has no notion that N fills pointing at one target with same-name-merge implications need a joint decision. **Fix candidate:** in REVIEW.md's per-maker "Ready to author" grouping, flag when ≥2 same-name fills resolve to the same target (a "shared-target merge" warning), so the author sees the collision before writing. Severity medium — a naive author following the recipe row-by-row would author a slug collision that `make validate`/ingest would reject, or worse, silently pick one.
- **Calibration win — a note-level co-model that is NOT a donor did not trip the multi-target gate.** `univerx` (ipdb:6702): note is "…copy of Gottlieb's 1971 'Galaxie', … its playfield plastics have the same art as the USA add-a-ball version, Gottlieb's 1971 'Dimension'." 'Dimension' is a seeded catalog model but here it is an **art reference**, not a second donor. The sweep greened `bootleg_of → galaxie` and its quote-scoped multi-target scan did not escalate (the establishing clause it quoted doesn't name Dimension). Correct outcome; I quoted only "This is a copy of Gottlieb's 1971 'Galaxie'" to keep Dimension out of the cite entirely.
- **`card-king-2`'s current title is literally slugged `card-king`** (sole-occupant), while the Gottlieb original `card-king` lives in title `drop-a-card-pop-a-card`. So the orphan-delete in 0149 removes a title whose slug equals a still-live model slug — harmless (title vs model are separate namespaces) but a double-take when reading the delete patch. Same shape for `galaxie`, `jungle-king`, `top-hand` copy titles.

## Authoring pass notes (2026-07-13) — ltd-do-brasil maker, 0150

Fourth bootleg maker off REVIEW.md (LTD do Brasil, Campinas, Brazil). 4 fills, all authored; all renamed copies (distinct names → no slug rename, no title merge, no companion removal patch). Calibration clean; one conceptual gap in the fill gate worth recording.

- **Calibration — all 4 ltd-do-brasil fills correct.** Each verified verbatim against the full IPDB note and resolved to the right Bally/Gottlieb original with matching year (`al-capone`→`speakeasy-2` Bally 1982, `haunted-hotel`→`haunted-house` Gottlieb 1982, `zephy`→`xenon` Bally 1980, `cowboy-eight-ball`→`eight-ball-deluxe` Bally 1981). No false greens. `speakeasy-2` (Bally 1982) was the correct target over `speakeasy` (Playmatic 1977) and `speakeasy-4` — the maker/year gate held.
- **OBSERVATION (new, medium/conceptual) — a `fill` in the _bootleg_ bucket greens on a quote that proves "copy", never "unauthorized copy".** The fill gate's quote-supports-claim check greened all four on the strength of the IPDB note's "a copy of Bally's/Gottlieb's X." But `bootleg_of` asserts an **unauthorized** copy — bootleg, not licensed build — and "a copy of X" establishes the copy, not the authorization status. The distinction is the entire bootleg-vs-licensed axis the campaign turns on (cf. 0127 licensed builds, whose IPDB notes _do_ say "under license"). For LTD the bucket happened to be right, but the evidence that the copying was _unauthorized_ is not in the note at all — it came from a maker-level source (Augusto Campos's Brazilian-trade history: LTD used the Reserva de Mercado "como escudo para copiar impunemente" foreign designs). So the authored patch gives each row **two cites that support `bootleg_of` together**: the IPDB note (copy of a named game) + the augustocampos statement (the copying was unauthorized). The sweep can't supply the second half — it inherits the worklist's bucket and the note only carries the first half. **Takeaway for authors:** a bootleg-bucket fill's IPDB quote is necessary but not sufficient; supply a maker-level authorization source (or confirm one exists) before tagging `bootleg`, exactly as you would to _reject_ it toward `licensed-build`. **Fix candidate:** the fill gate could flag bootleg-bucket rows whose only quote is bare "copy of" language (no authorization signal) as "classification-unconfirmed" rather than a clean green — a nudge to attach the authorization evidence, not a blocker.
- **Non-defect — augustocampos.net was already seeded as a citation root** (host `augustocampos.net`, seeded 2026-07-13 by a sibling Brazilian-makers session), so it could be cited formally per-row. `zephy` carries a third cite from the same history naming it directly as LTD's copy of Bally's Xenon.
- **UX — per-maker "Ready to author" grouping worked well** for picking a clean maker (ltd-do-brasil, 4 rows, listed under its own heading). No friction selecting or completing the maker this pass.

## DEFECT 4 (2026-07-17) — the redesign's guidance asked for a field name the schema rejects, killing ~80% of rows

**Severity: high (blocking, silent until you spend).** Found by a 5-row `--limit` trial before any full post-redesign run. Four of five rows came back `ai-error`: _"Additional properties are not allowed ('target_machine' was unexpected)"_. The `model_relationship` redesign (`bbc405d`) rewrote `_GUIDANCE` to name the target field `target_machine` — the **patch-syntax** name from DataPatches.md — while `RELATIONAL_SCHEMA` kept the **judge-side** name `target_title`. The schema is `additionalProperties: False`, so every row whose model obeyed the guidance died. The disposition is `ai-error`, not a verdict, so the failure looks like a flaky API rather than a prompt bug.

This is why the post-redesign sweep had never run at scale: the 2-row trial in `results.json` (2026-07-16 23:40) happened to survive because the model guessed the schema's name over the guidance's. It was luck, not health.

- **Fixed** test-first: guidance now names `target_title` / `target_maker` / `target_year` (the schema's own fields). A new invariant test (`test_guidance_names_only_fields_the_schema_accepts`) regex-scans `SPEC.guidance` for `target_*` / `license_*` / `relationship_*` tokens and asserts every one is a schema property — so guidance and schema can never drift apart silently again. Re-ran the same 5 rows: **5/5 `agrees`, zero errors.**
- **Lesson for the next type/field change:** the guidance is the model's only spec of the answer shape, and `additionalProperties: False` makes a renamed field a hard row failure, not a nudge. Prompt text is code — when the two live in different modules, pin them with a test.

## DEFECT 5 (2026-07-17) — a null in a string field wasted a whole row

**Severity: medium.** The same trial's fifth error: _"None is not of type 'string'"_. `target_year` already tolerated `["integer", "string", "null"]`, but `target_title` / `target_maker` / `target_label` / `quote` were bare `"string"` — yet `_clean` maps any non-string (including `None`) to `""` anyway. So the schema rejected, at the cost of a full AI call, a distinction the parser erases one line later. A model that means "no value" reaches for `null` as readily as `""`.

- **Fixed**: those fields now take `["string", "null"]`; `_clean` needed no change. Test: `test_relational_schema_tolerates_null_string_fields`.

## DEFECT 6 (2026-07-17) — `_maker_compatible`'s substring leniency lets a *different brand* satisfy a stated maker (false ambiguity + latent false fills)

> **✅ FIXED (2026-07-17), test-first.** New `SweepCatalog.brand_keys()` supplies the Manufacturer vocabulary; `_maker_compatible` now requires an **exact** brand match when the stated maker names a real Manufacturer record, and keeps containment only when it does not. So "Bally" no longer satisfies `bally-wulff` (`fly-high` → `supersonic` resolves), and "Taito" no longer satisfies `taito-do-brasil` — while "Premier" still reaches a Gottlieb-brand game via its `premier-technology` corporate entity, which is the case the leniency exists for. Tests: `test_resolve_rejects_a_different_brand_sharing_the_stated_makers_token`, `test_stated_brand_naming_no_manufacturer_stays_lenient`, plus a `bally-wulff` fixture brand.

**Severity: high (can silently green a wrong-brand target).** Found while re-verifying DEFECT 1: `fly-high` → "Bally's 1979 'Supersonic'" still fails to resolve, but no longer because of the `(Maker)` suffix — the base-name map now surfaces the right candidate. The trail is:

```text
3 catalog match(es) for 'Supersonic' [supersonic, supersonic-2, supersonic-bally-wulff]; maker 'Bally' → 2; year 1979 → 2   → ambiguous
```

`_maker_compatible` (`scripts/ai_corpus_sweep/gate.py:94`) tests **substring containment either way** across the Manufacturer brand *and* the corporate entity. The stated "Bally" is a substring of `bally-wulff`, so **Bally Wulff — a genuinely separate Manufacturer record — survives a filter that names Bally**, and the exact-name tie-break can't split them either (both normalize to `supersonic` once their `(…)` suffix is stripped). Result: a false `ambiguous` on a row whose catalog value is correct.

The leniency itself is load-bearing and must not simply be tightened to equality: it exists so a note's "Premier" reaches a Gottlieb-brand game whose *corporate entity* is `premier-technology`, and "Williams" reaches `williams-electronics-incorporated`. Those are one brand under a longer legal name. "Bally" vs "Bally Wulff" is two brands sharing a prefix — string shape alone doesn't separate the two situations.

**Not just a review-time cost — a silent false-fill risk of DEFECT 2's shape.** When a note's true target is *not* seeded but a wrong-brand namesake is, that namesake is the sole survivor → `unique` → green `fill`; and `_fact_problems` cannot catch it, because it re-asks the same lenient `_maker_compatible`, which says the maker is fine. DEFECT 2's contradiction guard is blind exactly where this defect fires.

**Blast radius is campaign-relevant, not hypothetical.** 22 Manufacturer slug pairs collide by prefix/suffix token in the live DB, several of them worklist makers:

```text
bally|bally-wulff        taito|taito-do-brasil        automaticos|automaticos-montecarlo
automaticos|automaticos-cmc   games-incorporated|bay-city-games-incorporated
united|united-manufacturing-company-diversey   universal|universal-manufacturing-company   (…22 total)
```

`taito` / `taito-do-brasil` and `automaticos` / `automaticos-montecarlo` are both in the 0128 worklist (Taito do Brasil has bootleg rows; Automáticos MonteCarlo owns a shipped 0127 licensed build), so a full run will fire this.

**Fix candidates (not applied — noting per the brief's "report, don't expand scope"):** keep containment for the **corporate-entity** surfaces (where the legal-name-is-longer case lives) but require the **Manufacturer brand** to match as a whole token — i.e. compare `maker_slug`/`maker_name` on token-boundary equality (`bally` ≠ `bally-wulff`, while "Bally Midway" → `bally` still matches on the leading token), and only fall back to containment on `ce_slug`/`ce_name`. Failing that, treat "stated maker matched only via a *proper* substring of a different Manufacturer record" as a contradiction in `_fact_problems`, so the sole-candidate case escalates instead of greening. Either way this wants a test per collision shape (Bally/Bally Wulff, Taito/Taito do Brasil, Premier/Gottlieb).

## Single-maker run — fipermatic (2026-07-17): the EM/SS twin shape, and a missing technology tie-break

> **✅ TIE-BREAK IMPLEMENTED (2026-07-17), test-first.** `resolve_target` now takes the `subject` and applies `_technology_tiebreak` after the exact-name one. `--regate` (zero AI spend) turned all three escalations below into the EM twins derived by hand here — two of them correctly surfacing as `hint-mismatch`, since the Worklist's machine-mined guess named the SS twin. Kept a tie-break, never a filter: it is skipped entirely when any candidate's technology is unknown (`test_technology_tiebreak_skipped_when_a_candidate_lacks_technology`) so it can never guess against missing data. Authored as [0159-fipermatic.yaml](../../../0159-fipermatic.yaml); IPDB independently corroborates the pick — it dates the **EM** Charlie's Angels to 1979-02 and the SS one to 1978-11, and the note says "Gottlieb's 1979".

First post-redesign run at any scale, deliberately scoped to one untouched maker (6 rows, 9 AI calls, ~22k tokens) before committing to the 298-row sweep. **Health: good — zero `ai-error`s (DEFECT 4/5 fixes hold), zero false greens.** Artifacts in `../sweep-fipermatic/`.

Dispositions: 3 `fill`, 3 `ambiguous-target`. All three fills hand-audited against the full note and the catalog and all three are **correct** (`jane` → `jungle-queen`, `space-walk-2` → `space-walk`, `zarza-2` → `xenon`; the maker filter correctly kept Pinball Shop's 1985 `jungle-queen-2` out of the first).

**All three escalations are one shape, and it is a fixable one.** Gottlieb shipped **EM and SS twins of the same game in the same year** (`Dragon` / `Dragon (EM)`, `Charlie's Angels` / `Charlie's Angels (EM)`, `Close Encounters of the Third Kind` / `… (EM)`), so the note's bare "Gottlieb's 1978 'Dragon'" narrows by maker and year to exactly two candidates and stops. Escalating is *correct* on the evidence the gate looks at — but the gate is not looking at the one fact that settles it: **the subject's own technology**.

| copy (Fipermatic) | tech | SS twin | EM twin | true target |
| --- | --- | --- | --- | --- |
| `charlies-angels-3` | EM | `charlies-angels` | `charlies-angels-2` | `charlies-angels-2` |
| `close-encounters` | EM | `close-encounters-of-the-third-kind` | `close-encounters-of-the-third-kind-2` | `close-encounters-of-the-third-kind-2` |
| `dragon-5` | EM | `dragon` | `dragon-3` | `dragon-3` |

Every Fipermatic copy is Electromechanical; an EM machine is not built from an SS design. The same fact silently *confirms* all three fills (each copy's technology matches its resolved target's).

**Why the existing tie-breaks can't do it.** `strip_parenthetical` was built for the campaign's `(Maker)` convention, but `(EM)` is a **technology** disambiguator wearing the same syntax — so "Dragon (EM)" and "Dragon" both normalize to `dragon`, the stated title matches both, and the exact-name tie-break narrows nothing. Note the trap in the obvious alternative: making the tie-break prefer the *unstripped* exact name would reintroduce DEFECT 1 wholesale (stated "Surf Champ" would then prefer `surf-champ-2`/`-3` over the correctly-suffixed original `surf-champ`). Technology is the orthogonal, safe discriminator.

**Fix candidate (not applied — noting per the brief):** a **subject-technology tie-break** in `resolve_target`, mirroring the exact-name one — among ≥2 otherwise-surviving candidates, if the subject model's `technology` matches exactly one, prefer it. `ModelFacts.technology` is already loaded and carried (`catalog.py`), so this is gate-only and `--regate` retrofits it over stored answers for **zero** AI spend. Keep it a **tie-break, not a filter** (a candidate with unknown technology must not be excluded by a fact it doesn't carry — the DEFECT-2 lesson), and it should apply to `copy` / `conversion` / `conversion_kit` alike, since all three ride the donor's hardware generation. Worth a confirmation warning too: a fill whose subject technology *contradicts* its resolved target is a false-green signal the current gates would miss.

Impact: this shape auto-resolved **3 of 6 rows (50%)** in this maker, and EM/SS twins are endemic to the 1977–80 Gottlieb corpus that dominates the campaign's bootleg bucket — expect a large share of the full run's `ambiguous-target` bucket to be this and nothing else.

## Single-maker run — europlay (2026-07-17): the tie-break fix confirmed, multi-edge notes work, one new false-green shape

Second single-maker run, chosen for a different shape than fipermatic's all-copy set: 6 models → **9 edge rows** (12 calls, ~27k tokens), mixing copies, a machine-target conversion, a *label*-target conversion, and a retheme. Artifacts in `../sweep-europlay/`. Dispositions: 6 `fill`, 2 `uncertain`, 1 `hint-mismatch`.

**Working well:**

- **Multi-relationship notes decompose correctly.** `jaws`' one note yielded three distinct edges and `fast-draw-2`'s yielded two — the redesign's core promise, exercised for the first time on real data.
- **Label targets land.** `jaws` → `conversion/unknown → “an electromechanical Gottlieb game”` is exactly right: a real conversion whose donor the note never names.
- **The maker filter earns its keep.** All six fills are technology-consistent, and the filter correctly excluded Royal Novelty's 1934 `golden-arrow-2`, Taito do Brasil's SS `volley-2` and NSM's `amazon-hunt-2` from otherwise-tempting same-name sets.
- **Hedging is caught.** `fast-draw-2`'s second reading (`conversion_kit` → “Amazon Hunt donor machines”, on "*Reportedly*, this is a conversion kit") escalated rather than greening a duplicate of its own correct `conversion → amazon-hunt` edge.

**Not authored from this run (rejected on review):** `jaws` copy → `scuba` (DEFECT 7 below), `jaws` retheme → `playboy` (hedged, and playfield borrowing is not a re-theme), `fast-draw-2` conversion_kit → label (hedged, and redundant with its conversion edge).

## DEFECT 7 (2026-07-17) — *artwork* reuse judged as a machine `copy` edge (a false green the hint caught by luck)

> **✅ FIXED (2026-07-17), test-first.** Both halves of the fix candidate below were taken. The deterministic backstop is `gate.asset_scoped_quote`: it finds the first lineage verb (`copy`/`converted`/`re-theme`/…) and escalates as the new `asset-scoped-quote` disposition when an asset noun (`artwork`, `backglass`, `playfield`, `cabinet`, `theme`, `sound card`, …) precedes it. **Position is the whole test** — an asset noun is perfectly normal *after* the verb in a genuine copy's quote, and two real shipped fills prove it ("a copy of [...] 'Vulcan' except the backglass depicts a woman", 0158; "a converted [...] game with a digital display and sound card added", 0160). Both are pinned as regression cases. The judge guidance gained a matching PARTS-ARE-NOT-LINEAGE trap.
>
> **Placement was the subtle part, and the first attempt was wrong.** Gating this at the fill step (beside the multi-target scan) left the real `jaws` specimen untouched: it reached `HINT_MISMATCH` first, because its stale hint named a *differently* wrong target, so the gate never ran. An artwork quote is not a lineage claim in **any** disposition — a seeded artwork edge would likewise have been blessed as `AGREES` by a note that never claimed it. The check now lives in `dispose_claim`, right after the hedge/quote gates and **before** the hint or catalog are consulted. Tests cover all three: no-hint (would-be fill), hinted, and already-seeded-edge.
>
> **Validated on the specimen, free:** `--regate` over the stored europlay answers reclassifies `jaws` copy → `scuba` as `asset-scoped-quote`, while its genuine `conversion` → label edge stays green and the hedged `retheme` stays `uncertain`.

**Severity: high (silent false green).** Found on the second single-maker run (europlay, `../sweep-europlay/`). ipdb:5080 `jaws` — a Europlay conversion of an unnamed Gottlieb EM machine — produced three edges, one of them:

```text
copy/unknown → scuba   quote ✓ “Backglass artwork is in part a copy of Gottlieb's 1970 'Scuba'”
```

**Jaws is not a copy of Scuba.** The note says its *backglass artwork* is "in part" a copy — art reuse across otherwise unrelated machines, which the same note underlines by adding that the artwork "was also used again on AMI's 1976 'The Shark'". A `copy` edge asserts the machine reproduces another maker's *design on newly built hardware*; a shared backglass image is not that, and Jaws' actual lineage is the `conversion` edge the same run greened correctly.

**It only surfaced by luck.** The row landed in `hint-mismatch` solely because the Worklist's stale guess said `playboy` — a *different* wrong answer. Absent a hint (or with a hint that happened to say `scuba`), this was a green `fill` with a verbatim quote and a unique resolution: exactly the profile the campaign authors without review. The quote-supports-claim gate (DEFECT 4's fix) never ran here — `quote_supported` is `null` on the row, because that call is reserved for would-be fills — so it is **untested** whether it would reject "artwork is in part a copy of X" as support for "this machine is a copy of X". The phrase contains the literal words "a copy of Gottlieb's 1970 'Scuba'", so there is a real chance it passes.

The neighbouring hedged edge shows the same category confusion from the other side: `retheme/unknown → playboy` on the quote "The playfield design *appears to borrow* from Bally's 1978 'Playboy'." Borrowing a playfield layout is not a re-theme (a re-theme redresses *a specific machine*). It escalated as `uncertain` — but for the hedging ("appears to"), not for the category error, so the guidance is not what saved it.

**Fix candidates (not applied — noting per the brief):**

- **Judge guidance** (`fields.py`): state that a relationship claim must be about the *machine*, and that reuse of a **component or asset** — backglass/playfield **artwork**, a cabinet, a sound board, a theme — is **not** a `copy`, `conversion`, or `retheme`. The corpus phrases this in a recognizable and narrow way ("backglass artwork is … a copy of", "artwork was also used again on", "the playfield design borrows from", "reuse of the cabinet from"), so it is cheap to name explicitly.
- **A deterministic backstop worth more than the guidance:** these quotes are identifiable without AI — a would-be `fill` whose quote scopes the claim to an asset noun (`artwork`, `backglass`, `playfield`, `cabinet`, `theme`, `sound`) *before* the copy/conversion verb should escalate rather than green. Cheap, `--regate`-able, and it does not depend on the model's category discipline holding.
- Extend the quote-supports-claim check to would-be **hint-mismatch** rows too, or at least record its verdict — right now the campaign's most-reviewed bucket carries no support signal at all.

**Blast radius:** artwork/cabinet reuse is common IPDB note furniture for exactly the Italian and Brazilian conversion houses this campaign is working through, and the hint that caught this one is a stale machine-mined guess that most rows do not have. Assume the full run greens some of these.

## Adding `retheme` to the sweep (2026-07-17)

The retheme relationship type shipped in flipcommons (patches 0155–0157, 39 edges live in the dev DB) but `RELATIONSHIP_TYPES` still read `("copy", "conversion", "conversion_kit")`, so a note describing a re-theme could only be miscast as a copy or conversion — `_parse_claim` drops `retheme` as an invalid type.

- Added `retheme` to `RELATIONSHIP_TYPES` (propagates to the JSON schema enum and the parser), a claim verb for the fill gate's quote-supports-claim check, and recognition guidance for the copy-vs-conversion-vs-retheme distinction plus the "don't infer unlicensed from a different maker" trap (Rethemes.md's rule).
- New `requires_machine_target()` rule mirroring flipcommons' `RELATIONSHIP_TYPE_BEHAVIOR`: a `retheme` **must** carry a machine target. A label-target re-theme is rejected by the planner and a DB CHECK, so greening one as a `fill` would hand the author a patch that cannot ingest — it now escalates as the new `label-target-invalid` disposition.
- `retheme` is deliberately **not** in `_OTHER_MAKER_TYPES`: a maker re-theming its own machine (Shrek) is normal, unlike a same-maker "copy target".
- **Note on coverage:** the 298-row 0128 candidate set has **zero** overlap with the 39 retheme models, so this run will not exercise `retheme` — the unit tests are its only coverage today. The change is about not miscasting a re-theme a note happens to describe, not about sweeping re-themes; a retheme corpus sweep would need its own candidate set.

## Single-maker run — elettrocoin (2026-07-17): the Italy-export sibling shape, and the two fill gates pulling against each other

Third post-redesign single-maker run (Elettrocoin, Italian conversion house — deliberately conversion-heavy, unlike fipermatic's and europlay's copy-dominated sets). 5 models → **8 edge rows** (8 AI calls, ~20k tokens, sub-cent). Artifacts in `../sweep-elettrocoin/`. **Health: good — zero `ai-error`s, zero false greens, every edge the model extracted is correct on the merits.** Dispositions: 3 `fill`, 3 `ambiguous-target`, 1 `multi-target-quote`, 1 `hint-mismatch`.

The multi-edge model works: `good-year` correctly produced **three** donor edges from one list note, and `summer-time-4` correctly produced **two** from one and-joined sentence. That is the ModelRelationships redesign doing exactly what it was built for — neither would have been expressible before.

### OBSERVATION (systematic, medium) — the "(Italy) export sibling" is a genuine ambiguity, and it kills the queued exact-title tie-break fix

All **3 of 5** `ambiguous-target` rows are one shape, and it is not resolver noise — every candidate pair is two real, distinct catalog records:

| subject | note states | candidates | what the sibling is |
| --- | --- | --- | --- |
| `scala-reale` | "Gottlieb's 1970 'Card Trix'" | `card-trix` (ipdb:446) / `card-trix-italy` (ipdb:3748) | ipdb:3748 — "a version of Gottlieb's 1970 'Card Trix' **made for export to Italy**" |
| `mexico-3` | "Bally's 1967 'Rocket III'" | `rocket-iii` (ipdb:1989) / `rocket-iii-italy` (ipdb:6891) | ipdb:6891 — "the Add-a-ball version … **made for Italy**" |
| `derby-3` | "Bally's 1966 'Gold Rush'" | `gold-rush` (ipdb:1035) / `gold-rush-6` (ipdb:6134) | ipdb:6134 — "Model 777-A **made for Italy** … Add-a-ball version" |

The US maker/year filters cannot split these — the export sibling is the *same maker, same year, same title*, differing only in market and reward type. Escalating is **correct**: an Italian conversion house plausibly converted whichever machine was in the Italian market, the note doesn't say which, and no gate can know. Resolving these needs per-model evidence (tilt.it, playfield/backglass detail), not a tie-break.

**This retires the petaco-era fix candidate** recorded above ("prefer a candidate whose normalized title exactly equals the note's stated title, disposition `fill` instead of `ambiguous-target`"). Applied here it would have silently greened all three onto the **US** record — three false greens, on the exact bucket the tool exists to protect. The `king-of-diamonds` case that motivated it is distinguishable (the padding candidates there were *differently titled* near-name siblings; here both candidates carry the same title), so if that fix is ever built it must require the losing candidates to differ in title, not merely in parenthetical. 🛑 **Do not implement the exact-title tie-break as originally worded.**

**Blast radius:** every Italy-export sibling in the catalog sits under an Italian conversion/bootleg house's likely donor set, and the Italian houses dominate the campaign's remaining rows. Expect this shape to be a large share of the full run's `ambiguous-target` bucket, and expect it to need a campaign-level decision (default to the US original? carry a `target_label`? research per row?) rather than per-row heroics.

### DEFECT 8 (medium) — the multi-target gate and the quote-support gate pull in opposite directions on multi-donor notes

The same run produced both halves of a contradiction, one per model, from notes that say the same kind of thing:

- **`summer-time-4`** (ipdb:4072) — note: "this game is a conversion of both Gottlieb's 1967 'Hit-A-Card' and Gottlieb's 1967 'Solitaire'". The model quoted that **establishing sentence** for both of its two (correct) edges. Result: both rows escalated — `multi-target-quote` ("the quote also names `solitaire`") and `hint-mismatch`. But the model **did** claim both donors; the second name in the quote is not an unresolved alternative, it is this model's own other claim.
- **`good-year`** (ipdb:4071) — note: "'Good Year' is a conversion of these games:\r\nWilliams' 1967 'Lunar Shot'\r\nWilliams' 1967 'Blast Off'\r\nWilliams' 1967 'Apollo'". The model quoted each **bare list item** — "Williams' 1967 'Lunar Shot'" — one per edge. Result: three clean `fill`s, `quote_supported: true` for all three.

So the gates reward **fragmenting** the quote down to a bare title and punish quoting the sentence that actually establishes the relationship. That is backwards on both axes:

1. **False escalation.** `multi-target-quote` (`sweep.py`, `gate.other_models_in_quote`) is a pre-redesign gate: it assumes one edge per note, so a second named machine means "decide which applies". Under ModelRelationships the answer can legitimately be *both*, and the model said so. **Fix candidate:** the gate has the claim in hand but not the model's *claim set* — suppress the escalation when every other model named in the quote is itself a resolved target of another claim on the same subject (the caller has all claims; pass them down). Escalate only for a named machine no claim accounts for.
2. **Weak green cites.** `good-year`'s three fills ship quotes that name a game and nothing else — no relationship verb, no subject. `check_support` passes them because it asks whether the quote establishes the claim *read in its source*, and in context it does. But the authored `cite:` travels without that context: a reader sees "Williams' 1967 'Lunar Shot'" and cannot see a conversion claim in it. Not a false green (the edges are right), but a citation-quality gap on the greenest bucket. **Fix candidate:** have the judge guidance require the quote to span the establishing clause (here the lead-in "'Good Year' is a conversion of these games:" plus the item), and/or have `check_support` judge the quote *standalone-first*. **Author-side workaround until then:** these three edges want the lead-in line in the cite quote, not the bare list item.

The two fixes are one design decision: once a quote is allowed (and expected) to carry the establishing sentence for a multi-donor note, the multi-target gate must stop treating that sentence as a red flag. Fixing #2 without #1 turns every multi-donor fill into an escalation.

### `hint-mismatch` — non-defect, tool doing its job

`summer-time-4`'s Worklist guess was `hint-mismatch`-flagged as `hit-a-card` vs the sweep's `solitaire`. Both are right — the machine converts **both** games, and the single-target Worklist could only record one. The hint audit correctly surfaced that the old guess was incomplete rather than wrong.

## DEFECT 9 (2026-07-17) — DEFECT 6's exact-brand rule binds a historical note to the *modern* successor brand (7 false escalations, all LAI)

**Severity: medium (false escalation, fails safe — no false greens).** Found ~1/3 into the full 298-row run. Every one of the run's first 7 `facts-mismatch` rows is the same shape: an LAI licensed build whose note names **"Stern"**, escalated against a target the gate itself prints as correct:

```
dracula-lai → states Dracula / Stern / 1979
  how: 1 catalog match(es) for 'Dracula' [dracula]; note says the target is by
       'Stern' but the only catalog match is dracula — Dracula (Stern Electronics, 1979, Solid State)
```

**Cause.** The catalog holds two Stern Manufacturer records — `stern-electronics` (name "Stern Electronics", the 1977–85 firm) and `stern-pinball` (name **"Stern"**, founded 1999). DEFECT 6's fix requires an **exact** brand match whenever the stated maker names a real Manufacturer; "Stern" *is* exactly `stern-pinball`'s name, so `_maker_compatible` binds a 1979 note to a company that did not exist in 1979 and then rejects `stern-electronics` as contradicting the note. The rule is doing precisely what it was written to do (Bally ≠ Bally Wulff) — it just has no notion that the brand it matched cannot possibly be the referent.

**Not a revert.** DEFECT 6 is real and its fix must stay. The gap is that exactness is enforced against *the stated token*, never sanity-checked against *the candidate the token would select*. Fix candidates, cheapest first:

1. **Year-gate the brand binding.** Before letting an exact brand match veto a candidate, check the matched Manufacturer has any model in the note's stated year (±1). `stern-pinball` has nothing in 1979, so the binding is vacuous and the rule should fall back to containment — which reaches `stern-electronics` correctly. This also happens to be the right rule for the general historical-successor shape.
2. **Never veto on an empty alternative.** A stated maker should only contradict a candidate when the stated brand offers a *rival* candidate for the same title. Here "Stern" (Stern Pinball) offers no Dracula at all, so escalating buys nothing — there is no second machine to confuse it with.

Both want a test per shape: Bally/Bally Wulff (exactness must hold, rival candidate exists), Stern/Stern Pinball (exactness must yield, no rival candidate, year impossible).

**Blast radius:** any historical brand whose modern successor carries the bare token as its full name. Stern Electronics/Stern Pinball is the big one and it sits under LAI's whole licensed-build set. Worth checking Gottlieb/Premier and the Williams entities for the same collision.

**Cost to fix: zero re-judge.** Resolution and disposition are pure code, so `--regate` re-buckets all 7 rows for free. Do not re-run AI over them.

## Full-run triage (2026-07-17) — the `conflict` / `set-but-unsupported` buckets are ~100% tool artifact at the halfway mark

At 160/298 models the two buckets the tool exists for held **19 rows and zero genuine seed errors**. Four distinct causes, all `--regate`-fixable (pure-code resolution/disposition — no re-judge spend). Recording each below. **Calibration warning for future sessions: a rich-looking wrong-value bucket is not evidence of wrong values.** The first read of this run ("13 wrong-value candidates, higher rate than the campaign's 3 known seed errors") was wrong on every row.

`set-but-unsupported` is additionally **inflated by double-counting**: DEFECT 9's 7 LAI rows each appear twice — once as `facts-mismatch` (the claim that couldn't resolve) and once as `set-but-unsupported` (the catalog edge no claim accounted for). Only 2 of that bucket's 9 rows were independent, and both were already known from RECONCILE.md. A row that fails resolution should not also indict the catalog edge it failed to reach.

## DEFECT 10 (2026-07-17) — `retheme` leaked into the licensed-build population and indicts correct 0127 data

**Severity: high (false accusations against verified correct catalog values).** 5 of the run's 10 conflicts at the halfway mark:

| model | catalog (0127, correct) | sweep claims | the judge's stated reason |
| --- | --- | --- | --- |
| `big-ben-segasa` | copy/licensed → `big-ben-williams-1975` | **retheme**/licensed | "made under license, indicating an official re-theme/relicense" |
| `lucky-ace-segasa` | copy/licensed → `lucky-ace` | **retheme**/licensed | "a licensed version … manufactured under license" |
| `travel-time-segasa` | copy/licensed → `travel-time` | **retheme**/licensed | "built under license …, indicating an official re-theme/production of the same design" |
| `the-getaway-high-speed-ii-american-home-entertainment` | copy/licensed → `the-getaway-high-speed-ii` | **retheme**/licensed | "licensed miniature/home version … official re-themed/reproduced version" |
| `lortium-automaticos-montecarlo` | copy/licensed → `lortium` | **retheme**/licensed | "manufactured under license from Juegos Populares" |

**The judge is treating `licensed` as evidence for `retheme`.** It is not. Segasa's *Big Ben* is Williams' *Big Ben* built under license in Spain — same game, same theme, different factory: `copy` + `licensed`. A `retheme` is a **new theme applied to the same design**; a licensed build is the **same theme built by someone else**. The two are orthogonal, and every reason string above conflates "official/authorized" with "re-themed". The recognition guidance added with `retheme` covers copy-vs-conversion-vs-retheme and the don't-infer-unlicensed trap, but nothing tells the model that *licensed says nothing about theme*.

**This run's own prediction was exactly backwards.** The retheme entry above says: _"the 298-row 0128 candidate set has **zero** overlap with the 39 retheme models, so this run will not exercise `retheme`."_ True as written — and irrelevant. The risk was never that the run would sweep re-themes; it is that a newly-offered type gets **over-applied to the population it does overlap**. Adding a type to `RELATIONSHIP_TYPES` puts it on the menu for all 298 rows, not just the 39 it describes. **Takeaway: when adding a relationship type, the regression risk lives in the rows it should NOT claim.**

**Fix candidate:** guidance stating that `license_status` and `relationship_type` are independent axes — a build being licensed/official is never itself evidence of `retheme`; a `retheme` requires the source to establish a **changed theme/artwork** while the design stays. Trial with `--limit` over these 5 known-correct rows as the regression set; they should all return `agrees`.

## DEFECT 11 (2026-07-17) — the sweep judges one note, but authored edges can rest on multi-source evidence (4 false license conflicts)

**Severity: medium-high (false accusations; structural, not a bug).** The 4 LTD do Brasil conflicts — `al-capone`, `cowboy-eight-ball`, `haunted-hotel`, `zephy` — all read: catalog `copy/unlicensed`, sweep `copy/unknown`, reason "no mention of licensing."

**The catalog is right and the sweep is blind, exactly as this file predicted.** The ltd-do-brasil authoring notes above record that a bootleg's IPDB quote establishes *copy*, never *unauthorized*, so the authored patch deliberately carries **two cites**: the IPDB note (copy of a named game) **plus** the augustocampos.net Brazilian trade history establishing the copying was unauthorized. The sweep's candidate rows default to `evidence: ["ipdb:<id>"]`, so it never sees the second cite and cannot reach `unlicensed` on any row whose authorization rests on a maker-level source.

This will fire on **every** such row — i.e. every bootleg whose license status was established the correct way. The candidates contract already supports it (`evidence` accepts arbitrary refs; the web cache resolves URLs), so this is an **input** gap, not a code gap.

**Fix candidates:** (a) `emit_candidates.py` should attach the maker-level authorization source to a maker's rows where one exists (LTD → augustocampos.net), so the judge sees what the author saw; (b) failing that, a `license_status` mismatch of the specific shape *catalog asserts licensed/unlicensed, note says unknown* should disposition as its own soft bucket (`license-unestablished-by-this-source`) rather than `conflict` — the note genuinely establishes nothing either way, which is not the same as disagreeing.

## DEFECT 12 (2026-07-17) — label wording compare trips on a leading article

**Severity: low (single false conflict, trivial).** `jaws` (europlay): catalog label edge `conversion/unknown → “an electromechanical Gottlieb game”` vs the sweep's `“electromechanical Gottlieb game”` — flagged as a `target_label` wording difference. The compare normalizes case, punctuation and whitespace but not a leading article, so `an X` ≠ `X`.

Notable that this is the campaign raising a conflict against a patch **it authored itself two hours ago** (0160-europlay) — a label is prose, and prose the sweep re-derives will never match the authored wording character-for-character. **Fix candidate:** strip leading articles (`a`/`an`/`the`) in the label normalizer. The broader question the doc already flags ("if that proves noisy in practice, `--regate` re-buckets for free") is now answered with a data point: it is noisy, and the noise is the tool's own prose.

## DEFECT 13 (2026-07-17) — the judge reads the note's lead sentence and misses kit language further down (11 false conflicts + 4 at-risk fills)

**Severity: high (false accusations here; a false-green shape elsewhere).** The full run's remaining 11 unexplained conflicts are one shape: catalog `conversion_kit`, sweep `conversion`, same target. The catalog is **right** on every one; the judge quoted the note's opening sentence and never read down to the sentence that disambiguates it:

- `space-rider` (komplett-flipper) — note opens *"A conversion of Bally's 1979 'Harlem Globetrotters On Tour'."*; further down: *"The owner of the uninstalled **kit** pictured here…"* and *"the production run quantity for this **kit** was 200 units."*
- `challenger` (professional-pinball) — *"Conversion of Bally's 1977 'Eight Ball'. **Conversion kit** included a playfield overlay, new decals for covering the existing plastics, a replacement backglass, stencils for repainting the cabinet, and optional playfield posts…"*

The IPDB house style states the *effect* first ("a conversion of X") and the *product* later ("the kit included…"). The lead sentence is the most quotable and the least complete, and the judge stops there. Affected: `space-rider`, `stellar-airship`, `saturn-2`, `super-bowl`, `space-hawks`, `challenger` I–V, `coney-island` (conversion_kit→conversion) and `ice-mania` (conversion_kit→copy).

**The mirror risk is a false green, and it is live.** On an *unauthored* row nothing contradicts the judge, so a kit greens as a `fill` typed `conversion`. Measured blast radius in this run: **4 fills typed `conversion` whose note contains "kit"** — `mythology`, `wizard-3`, `wizard-4`, `miss-america-45`. 🛑 **Do not author these four without reading the full note**; the type is likely `conversion_kit`, and a kit usually wants a plural/unnamed `target_label` rather than the single machine target the sweep resolved.

**Fix candidate:** the recognition guidance must tell the judge that "a conversion of X" describes the *effect* of a kit as readily as a purpose-built machine, and that kit language (*kit*, *uninstalled*, *overlay*, *stencils*, *decals*, production quantity "for this kit") **anywhere in the note** decides `conversion_kit` over `conversion` — the lead sentence does not. Regression set: the 11 conflicts above should all return `agrees`, and the 4 at-risk fills should flip to `conversion_kit`.

## Full-run result (2026-07-17) — 298 models, and what it actually proved

`make sweep ARGS="…/sweep/candidates.jsonl --resume --max-requests 700"`, judged fresh under current guidance (the 10-row pre-guidance trial was set aside as `results.pre-guidance-trial.json.bak`, not resumed). **298 models → 353 edge rows, 392 AI calls, ~1.09M tokens, ~20 min, 1 `ai-error`.**

| disposition | rows | | disposition | rows |
| --- | ---: | --- | --- | ---: |
| `agrees` | 122 | | `hint-mismatch` | 12 |
| `fill` | 89 | | `facts-mismatch` | 9 |
| `uncertain` | 38 | | `multi-target-quote` | 5 |
| `conflict` | 27 | | `quote-unsupported` | 4 |
| `set-but-unsupported` | 23 | | `asset-scoped-quote` / `unresolved-target` | 3 each |
| `ambiguous-target` | 13 | | `no-claim`/`quote-unverified`/`ai-error` | 2/2/1 |

### The headline: **all 27 conflicts are tool artifacts. Zero new seed errors in 298 models.**

| cause | rows |
| --- | ---: |
| DEFECT 13 — kit language below the lead sentence | 11 |
| DEFECT 10 — `retheme` miscast onto licensed builds | 6 |
| DEFECT 12 — label wording (leading article) | 6 |
| DEFECT 11 — license status resting on a second, unseen cite | 4 |

`set-but-unsupported` (23) is **9 rows of DEFECT 9 double-counting** plus 14 others, of which `race-stars`, `road-racer` and `flesh-and-blood` are the **three genuine seed errors this campaign already knew about** (found pre-redesign, evidently never corrected in the catalog — the sweep independently re-flagged all three, which is a real check passing). The rest are mostly DEFECT-13-adjacent kit rows.

**What the run proved, stated honestly:**

- **The prior authoring is sound.** 152 already-set rows were independently re-judged and produced **122 `agrees` and zero new errors**. That is the single most valuable output here, and it is a *negative* result — no hand-authoring pass would ever have produced it, because authoring looks at empty cells. The wrong-seeded-value thesis that justified the tool is, on this corpus, **not confirmed**: the data was already good.
- **The tool's own defect rate dominates its signal.** Of 140 review rows, the large majority are the tool's five systematic bugs, not catalog problems. Review cost is currently a tax on the tool, not on the data.
- **Full-run > single-maker, decisively.** DEFECT 9 (LAI) and DEFECT 13 (kit houses) sit in makers no single-maker run had touched; three runs over 17 rows found neither. One 20-minute pass surfaced five systematic bugs at once, and every one re-buckets for free via `--regate`.
- **Correct-by-design behaviour at scale:** 38 `uncertain` rows are all genuinely hedged notes ("Possible", "probably", "may be", "if we correctly understand the French text"). `merry-old-king`'s two competing donor theories both emitted as separate uncertain rows rather than one confident pick. The multi-edge redesign works.

### Recommended order of work (all free to re-bucket; **do not re-judge**)

1. Fix DEFECTs 9–13 test-first (each has a named regression set in its entry above), then a single `--regate`.
2. Re-read the review queue after regate — expect it to shrink from 140 to well under half.
3. Only then author. 🛑 The 4 DEFECT-13 at-risk fills (`mythology`, `wizard-3`, `wizard-4`, `miss-america-45`) need the full note read regardless.
4. `race-stars` / `road-racer` / `flesh-and-blood` are confirmed-real and still unfixed in the catalog — they deserve a patch on their own merits.

## FINDING (2026-07-17, high value) — Petaco's Gottlieb machines look LICENSED, and the campaign has them as unlicensed copies

**The first genuine wrong-existing-value the sweep has surfaced beyond the three already-known seed errors — and it landed on a maker the campaign considered DONE (13/13 applied, 0145-petaco).**

Attaching petaco's maker-level source (DEFECT 11's fix) made the judge read the whole blogpinball page rather than the one sentence 0145 mined from it. It reports **12 conflicts**, each `copy/unknown` (catalog) vs `copy/licensed` (note + maker source), on verbatim-checked quotes:

> "Lo que realmente ocurrió es que Petaco comenzó a lanzar pinballs **licenciados por Gottlieb** pero adaptados al público español"

> "Este **acuerdo duró una década (1964-1974)** y de ahí salieron un buen puñado de preciosas máquinas: - “Escalera de Color” (1965/04), réplica del pinball “Sweet Hearts” de 1963/09."

The second quote does not merely assert a licensing agreement in the abstract — it **names the machines as its output**. `escalera-de-color` → `sweet-hearts` is listed there by name.

**The evidence was already in a page the author had open.** 0145-petaco cites `blogpinball.blogspot.com/2017/03/petaco-sa-procedimientos.html` on nearly every claim — but only for the *réplica* fact and the model year (`'"Aquarius" (1971), réplica del pinball homónimo de 1970/10.'`), never for licensing, and authored all 13 rows `license_status: unknown`. The authoring notes above call petaco a "bootleg maker" and record "all 13 petaco rows correct". The rows were correct *on the copy axis*; the license axis was never asked of the source that answers it.

**What is and isn't proven.** The source is a blog — but one this campaign already trusts and cites in shipped patches. This upgrades `unknown` → `licensed`, it does not correct a flat error: `unknown` was the right call from the IPDB note alone, which is all 0145's author asked. Before any patch: 🛑 read the full blogpinball page, confirm the licensing passage covers each machine (the source lists them individually — check row by row, do not apply the agreement wholesale), and check the 1964–1974 window against each model's year. **Then ask the user.** The same question hangs over **Maresa** and the other Spanish makers — 0140's 20 Maresa rows are `unlicensed`, and if a comparable Spanish trade source exists, it should be asked the same question rather than assumed.

## DEFECT 14 (2026-07-17) — a second evidence source makes the judge emit TWO claims for ONE target

**Severity: medium (inflates conflicts; would hand an author contradictory edges). Introduced by DEFECT 11's fix — my own regression.**

`aquarius-petaco` produced **two rows for the same target**:

| # | claim | from | disposition |
| --- | --- | --- | --- |
| 1 | `copy/unknown` → `aquarius` | the IPDB note ("a copy of Gottlieb's 1970 Aquarius … no licensing mentioned") | `agrees` |
| 2 | `copy/licensed` → `aquarius` | the maker-level history (the Gottlieb licensing agreement) | `conflict` |

One target must yield **one** claim. Given two sources, the model is treating each as its own relationship and emitting one per source, instead of reconciling them into a single edge whose `quote` carries the relationship and whose `license_quote` carries the authorization — which is exactly the shape `license_quote` was added to express. The row-2 shape is right; row 1 should not exist alongside it.

Consequences: the conflict bucket double-counts, and an author following the rows literally would write two contradictory edges to one target (which the planner would reject, or worse, apply one of).

**Fix candidate:** guidance — one relationship per (target, type); when several sources speak to the same relationship, emit ONE claim, quoting the relationship from the source that establishes it and the authorization in `license_quote`. Never one claim per source. Worth a deterministic gate too: several claims from one model resolving to the same target + type is a contradiction to escalate as its own disposition, not to disposition independently — the gate has all of a model's claims in hand at `_gate_one_claim`'s caller.

**Note for the eval set:** `eval-expected.json` froze petaco's rows as `agrees` from the pre-fix run. If the licensed reading holds, **the expectation is what's wrong**, not the run — the exact failure mode flagged when the eval was built ("a wrong eval set is worse than none"). Audit petaco's labels before treating that file as ground truth.

## Authoring pass notes (2026-07-17) — dama maker, 0163

Six `fill` rows for Dama S.R.L. (Milan), authored as [0163-dama.yaml](../../../0163-dama.yaml): 5 `conversion_kit` + 1 `conversion`, all `license_status: unknown`, all edges only (every derivative is renamed → no slug rename, no title merge, no OPDB group check, no companion removal patch). Applied and verified 6/6 against a fresh `db.pre-0039` replay; `make validate` and `make verify-quotes` pass. Two findings worth recording, one of them a workflow hazard that cost this session its input.

- **HAZARD (new, high/workflow) — `results.json` is a single gitignored path, and the eval harness overwrites the full run.** This session was briefed to read its 6 dama rows from `sweep/results.json`. They were not there: the file had been replaced by a **67-row eval-subset run** (makers maresa/petaco/vifico/segasa/lai/sonic/ahe/automaticos-montecarlo/rmg — i.e. the DEFECT 10/11 regression sets), written 03:28 over the 03:28 full run of **353 rows**. `results.json` is in this dir's `.gitignore` as "regenerable", so there is no copy and no git history: **the 2026-07-17 full run's per-row output is gone**, and with it the triage source behind the "Full-run result" section above. Only `eval-expected.json` (169 hand-triaged rows, 1 of them dama) survives, because someone thought to freeze it. The full run cost ~1.09M tokens and 20 minutes; the eval run silently destroyed it because both write the same path. **"Regenerable" is doing a lot of work in that .gitignore comment — regenerating a *judged* run is not free, it is a re-judge.** Fix candidates: (a) `check_eval.py` / any subset run should write to its own `--results` path, never the default (the flag already exists; nothing enforces it); (b) `make sweep` should refuse to overwrite a results file whose row count exceeds the current run's candidate count without `--force`; (c) drop `results.json` from .gitignore, or snapshot each completed full run to `results.<date>.json`. Recovering was cheap **only** because the notes are in DuckDB and the 6 rows' targets were hand-verified in the task brief — a session without that brief would have had to re-judge.
- **OBSERVATION (medium) — a hedged *second* donor is invisible in a single-donor `fill`, and it is not what DEFECT 8 describes.** `mondial-bank` (ipdb:4069) greened as a clean single-target fill → `harmony`. The full note is: *"A conversion kit for Gottlieb's 1967 'Harmony' **and possibly also for Gottlieb's 1967 'Troubadour'**."* The fill is **not wrong** — Harmony is asserted outright and is the right record (Gottlieb 1967) — but the note names a second, *hedged* donor that the row surfaced nowhere, and `troubadour` **is seeded** (Gottlieb 1967), so it would have resolved. This is the mirror of DEFECT 8: that entry covers *and*-joined donors pulling the multi-target and quote-support gates against each other; here the donors are joined by "**and possibly also**", so the confident half greens alone and the hedged half vanishes rather than emitting its own `uncertain` row. The redesign's multi-edge machinery already handles exactly this shape correctly elsewhere — `merry-old-king`'s two competing donor theories each emitted as separate `uncertain` rows (see "Full-run result" above) — so the gap is that a note mixing *one confident* + *one hedged* donor drops the hedged one instead of splitting it out. **Authored conservatively:** Harmony only, with a public `note:` recording that Troubadour is raised as a possibility and deliberately not recorded pending a source that establishes it. **Fix candidate:** a note whose donor list mixes confidence levels should emit one row per donor at its own confidence, not collapse to the confident one. Regression set: `mondial-bank` should yield a `fill` → `harmony` **plus** an `uncertain` → `troubadour`.
- **Non-defect — the Italian-sweep overlap check came back clean for the 6 subjects.** `dama-srl` is on the README's overlap list, and the Italian series does touch this maker: 0095 *created* four tilt.it models (`golf-dama-srl`, `mexico-70`, `gold-beach`, `hippie`) with their own `conversion_kit` edges, and 0108/0109 added edges to `new-city` and `spider`. None of them collides with the 6 IPDB-seeded subjects here, which carried **zero** prior edges — so a fresh number (0163) was right and no fold into the 0109 series was owed.
- **Calibration — all 6 dama fills correct**, verified verbatim against the full IPDB note; every target resolves on an exact maker+year match (`angels`→`rancho-2` Gottlieb 1966, `frogmen`→`bazaar-2` Bally 1966, `las-vegas-3`→`electra-pool` Gottlieb 1965, `mondial-bank`→`harmony` Gottlieb 1967, `world-star`→`magic-town` Williams 1967, `rally`→`elite-guard` Gottlieb 1968). The `-2` suffixes are ordinary disambiguation from unrelated same-named games and the maker/year gate picked correctly over all of them (3 Bazaars, 3 Ranchos in catalog). **DEFECT 13 does not bite this maker:** the 5 kit notes say "conversion kit" in the lead sentence itself, and `rally`'s note ("this game is a conversion of Gottlieb's 1968 'Elite Guard'") contains no kit language anywhere, so `conversion` is right.

## Post-fix re-judge (2026-07-17) — what the eval caught that a "looks better" read would have missed

Full re-judge under the DEFECT 9–13 fixes, then `--regate` against a healthy dev DB (current through 0163). **298 models → 343 rows, 232 AI calls (122 models resumed from the crashed run), ~824k tokens.** Scored with `check_eval.py` against `eval-expected.json`.

**Eval: 137/169 — versus 138/169 before the guidance changes. Net flat.** That headline hides three real movements in opposite directions, which is exactly why the number is worth having.

### What worked

- **DEFECT 10 (retheme): 8 conflicts → 1.** The independent-axes guidance holds. Only `tiger-woman` (idi) still miscasts `copy` → `retheme`.
- **DEFECT 9 / 12:** confirmed by free regate, no re-judge needed.
- **DEFECT 11 (license):** LTD reaches `unlicensed` legitimately via `license_quote` — but see flakiness below.

### What only half worked — the kit guidance induced a NEW failure

**DEFECT 13: 11 conflicts → 6.** Better. But the three at-risk fills got *worse in a new way*: `mythology`, `wizard-3` and `wizard-4` now emit **two claims each** — a `conversion` fill AND a separate `conversion_kit` row (`hint-mismatch` / `quote-unsupported`). Only `miss-america-45` cleanly flipped to `conversion_kit`.

Told "kit language anywhere in the note decides it", the model **added** a kit claim instead of **replacing** the conversion one. It hedged by emitting both readings rather than choosing. That is DEFECT 14's shape, now induced by my own guidance — the second time today a fix has produced one-claim-per-reading instead of one-claim-per-relationship.

**This makes DEFECT 14 the highest-value remaining fix.** It now explains three separate symptoms: petaco's duplicate license rows, these kit double-claims, and part of the conflict bucket's inflation. Fixing "one claim per (target, type), reconcile sources onto it" is worth more than any further guidance tuning, and it wants the deterministic gate as well as the guidance — the caller of `_gate_one_claim` holds all of a model's claims and can catch a contradiction the prompt failed to prevent.

### The finding that looks like a failure

**12 of the 27 eval failures are petaco `agrees` → `conflict`** — the licensed-build finding above, not a regression. The eval is flagging its own expectation as wrong, precisely the hazard recorded when it was frozen. **Do not "fix" these by tuning guidance; adjudicate the licensing question first, then re-freeze the labels.**

### ⚠️ The judge is NONDETERMINISTIC — a single eval run is not a verdict

`cowboy-eight-ball` (ltd-do-brasil) came back **`agrees` with a `license_quote`** in the isolated LTD run and **`conflict | copy/unknown` with no `license_quote`** in the full run — *same guidance, same evidence, same model*. It found the authorization passage once and missed it the other time.

Consequences for anyone using this harness:

- A few rows of eval movement is **noise, not signal**. Do not chase a 1–3 row delta.
- A guidance change should be judged on a **bucket-level** shift (retheme 8→1 is signal; 137 vs 138 is not), and ideally over more than one run.
- The 17k-char maker-level page is the likely driver: the authorization sentence is a needle, and recall over it is stochastic. Shorter, targeted evidence (a cached excerpt rather than a whole page) would likely stabilize it — worth trying before more prompt words.

## Authoring pass notes (2026-07-17) — US-original conversions, 0165

Seven `fill` rows across the three US-original makers (Bally, Gottlieb, Williams), authored as one cross-cutting file [0165-us-original-conversions.yaml](../../../0165-us-original-conversions.yaml) rather than per-maker (in-house / same-lineage conversions don't split cleanly by house). These are the README's hard-vet-required US-original set. Applied and verified 7/7 against a fresh `db.pre-0039` replay; `make validate` + `make verify-quotes` pass. **All 7 survived vetting — none dropped.** Calibration was clean on the relationship extraction; one license over-inference worth recording.

- **OBSERVATION (new, medium) — a `conversion` fill greened `license_status: unlicensed` off "not done by manufacturer", which establishes a *third-party* converter, not an *unauthorized* one.** `bowl-a-line-2` (ipdb:5090): note is "Conversion of Bally's 1954 'Variety', **not done by manufacturer**." The sweep read "not done by manufacturer" as evidence of `unlicensed`. But that phrase says only *who* performed the conversion (a third party, not Bally) — it is silent on *authorization*. Aftermarket conversions were routinely legitimate, and a conversion reuses the actual physical machine, so "unlicensed" is not even a natural axis here. This is the same discipline the LTD/petaco notes (DEFECT 11, and the ltd-do-brasil "copy ≠ unauthorized" observation) established from the other direction: a note establishing the *conversion/copy* never by itself establishes the *authorization*. **Authored `license_status: unknown`** with a public `note:` recording that the third-party conversion doesn't establish authorization. **Fix candidate (guidance):** state that identifying a *third-party* converter ("not done by manufacturer", "done by <distributor>", "aftermarket") establishes the converter's identity, not the authorization status — `license_status` stays `unknown` unless the source speaks to a license. Regression row: `bowl-a-line-2` should green `conversion` → `variety-2` with `license_status: unknown`, not `unlicensed`.
- **Calibration — the other 6 rows correct on both axes.** Forward direction and unique target on all: `bamboo`→`orient` (in-house Bally conversion), `single-coin-3`→`shoot-a-line` (in-house Bally), `amazon-hunt-ii`→`amazon-hunt` conversion_kit (in-house Gottlieb; the maker filter correctly kept NSM's 1985 `amazon-hunt-2` out), `star-trek-2`→`astro` conversion (in-house Gottlieb export-to-Italy — a genuine conversion, the note says "Conversion of", and there is no `astro-italy` sibling to confuse it), `star-wars-episode-i`→`revenge-from-mars` conversion_kit (the PB2K sibling kit), `congo-2`→`target_label` "narrow body WPC Security games" conversion_kit (plural donor class → label edge, the europlay `jaws` shape). No false greens.
- **Non-defect — `variety-2` is the right donor for a "Bally's 1954 'Variety'" claim despite carrying no seeded year.** IPDB has three Varieties: Atlas 1931 (`variety`), Bally year-unknown (`variety-2`), Bally 1939 (`variety-3`). The note wants Bally 1954; the DEFECT-2 "never exclude a year-unknown candidate" rule kept `variety-2` (unknown) and dropped `variety-3` (1939, contradicts 1954). Correct — `variety-2` is the only Bally *Variety* whose year doesn't contradict the note.
