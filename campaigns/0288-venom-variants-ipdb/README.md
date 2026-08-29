# 0288 — IPDB testimony on the two Venom variants

One patch, attributed `ipdb`: 9 field values and 4 credits across `venom-limited-edition` and `venom-premium`. Restores them to the shape `venom-pro` reached in 0285/0287, which the same machine's third variant had and these two lacked.

## Why these two, when the sweep's scope rule excluded them

Campaigns 0284/0286 fill source content only for models *that pass* linked, on the principle that a model linked earlier has either had its source content ingested already or was skipped for a reason nobody recorded — and reopening the latter silently overwrites a decision.

These two were checked individually against that principle and clear it:

- **No patch has asserted or retracted any field this patch writes.** Their `ipdb_id` comes from the seed baseline. Two patches do touch them — 0204's theme rollup and 0206's `limited-edition` tag — but both decide other things entirely.
- **IPDB held no claims on them at all**, so nothing here supersedes or no-ops.

They are a gap, not a decision.

## The contrast that defines the rule: `road-trip`

`road-trip` looked like the same kind of gap — an OPDB month the catalog does not carry — and is the opposite. OPDB's February is the **2025 world debut** at Pinball at the Beach, not a manufacture date; the machine is unreleased, and the maker's only statement is "Expected Late 2026". Two patches acted deliberately: **0233-ramps-pinball** retracted our own month, calling the resolved value *"a chimera"*, and **0235-road-trip-month-opdb-retract** retracted OPDB's. Re-asserting it would resurrect a value someone had already diagnosed and removed.

That same debut date is also why OPDB's production *year* for `road-trip` reads 2025 against our 2026 — the two sides are dating different events, which is a documented adjudication rather than an open disagreement.

`venom_checks` enforces the distinction **per field, not per model**: it fails if a patch has asserted or retracted one of the very fields being written. Verified against `road-trip`, which both retraction patches would block.

## The month is a recorded disagreement

OPDB claims July for both variants; IPDB says August. `opdb` (priority 200) outranks `ipdb` (100), so **July keeps resolving and nothing a reader sees changes** — what changes is that IPDB's August is on the record instead of invisible. That is the point of a source-attributed claim, and the same reasoning as 0284/0285.

## Evidence

Every field and credit rides its own changeset quoting the line of the IPDB row that states it — the date header carries year and month together because it states both in one line. All 11 quotes verified. `venom_checks` additionally holds each credit's quote against the person slug it asserts, since IPDB prints a name and the slug is our resolution of it.
