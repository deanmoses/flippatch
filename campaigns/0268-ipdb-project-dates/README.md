# 0268 — IPDB project dates

Fills `project_year` (and `project_month` where IPDB names a month) for **187 models the catalog held no date for at all** — not a production date, not a project date, nothing. The dates were always in the IPDB dump we already had; the ingest read the wrong field.

- `project_dates.sql` — the analysis: the classification, the gate, the anchors.
- `gen.py` — the emitter, one entry per `pd_patch_rows` row.
- `patches/0268-ipdb-project-dates.yaml` — 187 entries, attribution `flipcommons-catalog`.

## The signal

IPDB carries two kinds of date and labels them separately on a machine page: a **Date Of Manufacture** (physical assembly, factory rollout) and a **Project Date** (the design milestone logged in the manufacturer's internal records — IPDB's own gloss is "Project Dates (aka Design Dates)"). Per IPDB's stated display rule, the page's header line shows whichever it holds, preferring the manufacture date when it holds both.

Our IPDB baseline came from `ipdb_xantari_2025_02_01.json`, which carries both — and the ingest read only one:

| field | fill | ingested |
| --- | --- | --- |
| `DateOfManufacture` | 5,265 of 6,664 | yes |
| `AdditionalDetails` — the header line, verbatim: `IPD No. 3711 / May, 1989 / 4 Players` | 6,664 of 6,664 | **no** |

The dump builder mapped only rows labelled `Date Of Manufacture:` into `DateOfManufacture` and dropped `Project Date:` rows to null, while the header line carries the date under either label. So a project-date-only listing reached us with a null date and its date surviving only in the field nobody read.

That makes the classification deterministic rather than a judgment call:

> `DateOfManufacture IS NULL` **and** a parsed header date `IS NOT NULL` **is** the definition of "IPDB holds only a project date."

It holds on all 187 without exception — `rejected` is 0, and `pd_checks` asserts the emitted set can never contain a listing carrying a manufacture date. No page fetching was needed to classify a single row.

Deterministic, though, is not the same as sourced. The rule is **our** reading of how IPDB's page and its dump behave; IPDB never labels the header line itself. That is why the patch is attributed to us and not to IPDB — see [Judgment calls](#judgment-calls).

## Totals

From `pd_summary`, against the dev DB at `0267-merchant-paid-reward-description` (6,941 live models), immediately before this patch applied:

| metric | value |
| --- | ---: |
| models_live | 6941 |
| models_undated | 1161 |
| models_undated_with_ipdb_id | 1131 |
| candidates | 187 |
| **patch_rows** | **187** |
| patch_rows_with_month | 135 |
| patch_rows_ipdb_day_precision | 90 |
| patch_rows_unreleased | 59 |
| rejected | 0 |
| dump_rows_with_parsed_year | 5570 |

Applying it takes `models_undated` from **1,161 to 974** and writes nothing to `production_year`, which stays at 5,780.

Concentration is the story in one line: **Bally 98, Williams 32, Gottlieb 31** — 161 of 187. The big three are exactly the makers whose internal project logs IPDB holds. The remaining 26 span 15 small makers, from Lindstrom in 1932 to Dutch Pinball in 2017.

## The corroboration nobody planned

**59 of the 187 already carry `production_status: unreleased`** in the catalog — asserted years earlier, by hand, from IPDB's prose, with no knowledge of the header line. Among the 26 models outside the big three the rate is 19 of 26.

That is the mechanism confirming itself from the other side. A game that was never produced *can only ever have a project date* — there is no manufacture to date. `lazer-lord`, `red-line-fever`, `zingy-bingy`, `godzilla-king-of-the-monsters`, `houdini-master-mystery`, `atari-arcade-classics`: each was independently recorded as never produced, and each turns out to be a listing with a date and no manufacture date. The classification and the existing catalog agree without having consulted each other.

It cuts the other way too, and this is why `Project Date` must not be read as a never-produced marker: Baby Pac-Man (IPDB 125) carries a project date **and** 7,000 confirmed units. The label says where the date came from, not whether the game shipped.

## Judgment calls

**Day precision goes in the evidence, not in prose.** 90 of the 187 dates name a day (`IPD No. 148 / December 09, 1935 / 1 Player`) and the catalog stores year and month only. Rather than discard the day or write 90 notes about it, each entry quotes the **whole header line**, so the day is preserved in the citation a reader can follow. This also makes every quote verbatim by construction: the `ipdb:` resolver reproduces `AdditionalDetails` unlabelled in the document `make verify-quote-verbatim` matches against, so the quote is cut from the source text itself, not reassembled from a parse.

**Every entry carries the same note, and it earns its place.** The usual rule is that a cite with a quote needs no note. Here the quote proves a *date* but cannot say which *kind* of date — and that is the entire question this campaign answers. The note is the only thing standing between the evidence and the field it lands in, so it is on all 187:

> IPDB has no date of manufacture for this model, which means the quoted header date here is a project date.

**Attribution is `flipcommons-catalog`, not `ipdb`.** IPDB supplies the date, and it is cited and quoted as such — but IPDB never labels that header line, and the claim being asserted is not "this date" but "this date is a **project** date". That classification is read out of an *unlabelled* string plus the absence of a second field, under a rule about IPDB's page behaviour that we apply on IPDB's behalf. The reasoning is ours, so the attribution is ours. Attributing it to IPDB would dress our inference as the source's own statement, and would rank it against genuinely IPDB-asserted claims as though IPDB had said it.

**The parse is upstream and stays there.** Pinexplore's `ipdb_machine_additional_details` (`sql/04_staging.sql`) does the parsing under a full-string-anchored grammar. This campaign reads that view rather than re-parsing the dump — a second parser would be a second thing to rot. `project_dates.sql` re-asserts pinexplore's own redundancy tripwire (`additional_details_ipd_no` / `_players` restate `IpdbId` / `Players`) on the emitted set, because a capture-group slip writing a wrong year into an identity field is the worst failure available to this campaign.

## Reaching the parse

`project_dates.sql` opens with `ATTACH '../pinexplore/explore.duckdb'`, which no other campaign in this repo does. It is unavoidable: `AdditionalDetails` never became catalog data, so it is absent from `models.extra_data` and every foundation column, and flippatch's `scripts/analysis/evidence.sql` bridge deliberately carries the web-scrape cache alone. The path resolves from the **flipcommons** checkout, since that is where the runner `cd`s — the same frame `evidence.sql` documents, and with the same limitation, that `ATTACH` takes a string literal and so cannot honour a `PINEXPLORE_DIR` override.

## Anchors, and why they don't point at the patch

The emitted set **legitimately drains to zero the moment this patch applies** — every model it targeted now has a date and drops out of scope. Verified: re-running `pd_summary` after apply gives `patch_rows: 0` with `pd_checks` still clean.

So anchoring the checks on `pd_patch_rows` could not tell "the campaign finished" from "the grammar rotted" — the failure 0181's own comments record hitting. The anchors here probe the **parse and the join** instead, one per header-date shape the grammar admits, each also asserting the dump record still resolves onto its model:

| anchor | shape |
| --- | --- |
| `ipdb 3711` → May 1989 on `ice-castle` | month + year |
| `ipdb 6592` → bare 1990 on `a-world-of-clowns` | year only |
| `ipdb 148` → December 9 1935 on `bally-derby` | day precision |
| `ipdb 987` (Gator) still reads as holding a manufacture date | the negative case |

The fourth is the one that matters most. Without it the classifier could go one-sided — every date reading as a project date — and every row-level invariant above it would still pass.

## Dead ends, from the wider investigation

Recorded so they are not re-attempted. The full account is in [docs/plans/MissingYears.md](../../docs/plans/MissingYears.md).

- **`ipdb.org` returns HTTP 403** to the fetcher. There is no live re-scrape path to IPDB; the Feb-2025 dump is our IPDB access.
- **archive.org serves IPDB pages, and harvesting them recovers no years for the obscure-maker population.** An 85-model batch (Maresa + SIRMO + Splin) came back with **zero** years: the strings `Date Of Manufacture` and `Project Date` appear zero times across all 85 cached pages. IPDB has no date for those machines and the dump was faithful about that absence. The harvest's value is `Specialty` / `Production` enrichment, not dates.
- **Regex over IPDB `Notes` is a trap.** 708 of the remaining undated models mention a four-digit year somewhere in their prose, but the year almost always belongs to a *different* machine — "This is a conversion of Bally's 1967 'Orient'", "Replica of Gottlieb's 1977 'Centigrade 37'". What those give is a lower bound, not a date.
- **Manufacturer operating spans and lineage neighbours are not assertable.** A single-year maker span is strong evidence but it is our own inference over our own data — circular and uncitable. Their use is as a QA filter ("proposed 1954 for a maker that only operated 1966–1970 → reject").

## Out of scope

Deliberately, and not to be revived without a separate decision:

- **Models that already have a year.** No existing date is changed, including the IPDB-over-OPDB question.
- **The January retractions.** IPDB renders a year-only date as `1961` and a real January as `January, 1961`, which disambiguates the ~350 models sitting at a defaulted January against the 125 whose January is real. The evidence stands on its own; the attribution was never verified, and it is a separate campaign.
- **`production_status`.** The dump carries no production-status field at all (`Never Produced` appears zero times in 6,664 records; `ProductionNumber` is a quantity, and null there is indistinguishable from unknown). Recovering it is worth its own campaign and needs a decision on what NULL should mean.
- **The 974 models still undated**, 944 of which have an `ipdb_id` and no header date. IPDB does not know their dates. They need national and specialist sources, on the model of the Italian tilt.it campaigns (0079–0110).
