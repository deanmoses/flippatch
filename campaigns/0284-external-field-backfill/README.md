# 0284 / 0285 — External field values, source-attributed

What IPDB and OPDB say about the models linked in `0281`/`0283`, recorded as each source's own claims. Two patches because a patch carries one attribution.

| patch                     | attribution | models | claims |
| ------------------------- | ----------- | ------ | ------ |
| `0284-opdb-model-fields`  | `opdb`      | 20     | 64     |
| `0285-ipdb-model-fields`  | `ipdb`      | 7      | 30     |

OPDB: production year ×20, month ×20, player count ×8, technology generation ×8, display type ×8. IPDB: year ×7, month ×7, player count ×7, technology generation ×7, production quantity ×2.

Effect: `cross-field-unsupported` for 2023+ models fell from 54 to 10.

## Attributed to the source, not to Flipcommons

The identity links in 0281/0283 were Flipcommons work — deciding which catalog record is which external record is our judgment. These field values are not: the source supplies them directly and there is no judgment of ours to own.

`flipcommons-catalog` outranks both sources, so **nothing a reader sees changes**. What changes is that the catalog now records what each source says. Where a source agrees, that is corroboration; where it disagrees, the dissent is on the record instead of being invisible. `alice-goes-to-wonderland` is the worked example: `flipcommons-catalog` 2026 resolves at rank 1, `opdb` 2025 sits active at rank 2.

This is safe against the apply engine's no-op rejection because `_diff_claims` compares **within a source** — it filters on `actor_id` — and neither source held any claim on these models. Every row is a new claim, never a re-assertion.

## Scope: the models this pass linked

Read from `patch_claims`, not inferred from a date or a NULL. A model linked before this pass has already had its external field data ingested; one that is linked and still has none was skipped for a reason nobody recorded, and reopening that is how a deliberate omission gets silently overwritten.

Six field values sit just outside the line and stay there: `venom-limited-edition` and `venom-premium` (IPDB player count, technology generation, quantity) and `road-trip` (OPDB month).

## Judgment calls

**The OPDB rows carry a note and no cite.** An `opdb:` cite resolves to a cached `opdb.org/machines/<id>` page, and that URL is keyed by a numeric database id the published export does not carry — our Group-Model-Alias identifier is not addressable there, so there is no page to point at. The note is `From the OPDB API.` and exists because `note-required` needs a note or a quoted cite.

**The IPDB rows carry a cite and no note.** Each field rides its own changeset quoting the line of the rendered row that states it, so one quote supports one fact and the verbatim gate checks each independently. The date header states year and month in a single line, so those two share a changeset — which is why the emitter groups by quote rather than by field name. All 23 quotes verified.

**Only `manufacture`-kind IPDB dates reach production fields.** A project date is a different fact; `fb_checks` refuses anything else.

**`production_quantity` is a JSON string, not a number** — the one field here that breaks the pattern. The schema keeps it a string so it can eventually carry an approximate or ranged quantity, and the whole seed uses the string form.

## The OPDB January trap, checked

OPDB defaults a year-only manufacture date to January 1, which is the defect patches 0055/0277/0278 exist to undo — a January from OPDB may carry no month information at all. None of this scope's 20 months is January (they spread February through December), so the trap is not present here. `fb_checks` now stops the run if an OPDB January ever enters this scope, rather than importing a default as a fact.

## Re-running

`fb_checks` asserts the source holds no claim on each field it is about to write. Once these patches are applied those checks **fail by design** — that guard is what stops a second emission silently no-op'ing or superseding. Regenerating requires a database restored to before 0284.
