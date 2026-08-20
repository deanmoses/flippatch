-- IPDB project dates for models the catalog already dates from ANOTHER source.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, liveness
-- filtering, the NULL-spelling regularization) is FLIPCOMMONS' shared foundation; the
-- runner loads it under this file automatically, so nothing is `.read` here.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so that this file's ATTACH and the
-- foundation's own resolve. `make analyze` handles that and delegates to flipcommons'
-- shared runner. Do not run this file directly:
--
--     F=campaigns/0278-ipdb-project-months/project_months.sql
--     make analyze FILE=$F PREFIX=pm                  # summary, gated on checks
--     make analyze FILE=$F Q="FROM pm_patch_rows;"     # exactly what gen.py emits
--     make analyze FILE=$F Q="FROM pm_rejected;"       # what the gate held back
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
--
-- == WHAT 0268 LEFT BEHIND ==================================================
--
-- 0268 recovered IPDB project dates under a scope test of `models.year IS NULL` — "this
-- model reads as undated on the site". That was the right scope for the question it
-- asked (models with no date at all), and it silently excluded a second population: a
-- model IPDB holds a project date for, which the catalog ALREADY dates from a different
-- source. Those models read as dated, so 0268 never saw them, and their project date is
-- still missing.
--
-- The classification is 0268's, unchanged and stated in its own words:
--
--     `DateOfManufacture IS NULL` and a parsed header date `IS NOT NULL` IS the
--     definition of "IPDB holds only a project date."
--
-- What differs is only the scope test: `project_year IS NULL` — the FIELD is empty —
-- rather than `year IS NULL`, the derived fallback. `models.year` coalesces production
-- over project and `models.month` prefers the production month wholesale, so a model
-- here reads as fully dated on the site while the project field behind it is blank.
--
-- A consequence worth naming before anyone measures this patch by it: filling these
-- changes NOTHING a reader sees. `production_year` wins the derivation, so the site goes
-- on showing the production date. The value is that the catalog stops being silent about
-- a date IPDB holds, and that the two dates become separately attributable.
--
--
-- == WHERE THE EXISTING DATE CAME FROM ======================================
--
-- Not from IPDB, and this is what makes the pair safe to hold at once. Every candidate
-- carries a `production_year` claim, and the claim record names its origin: the bulk of
-- them from 0181's bingo-year campaign, which mined production years from its own
-- source, and the rest from OPDB, the baseline, or a handful of later patches. None of
-- them could have come from the header line this patch reads, because our baseline never
-- read that field — 0268's whole finding.
--
-- So this is not one date filed twice. It is a production date from one source and a
-- project date from another, for the same machine, and IPDB's own listing is the
-- evidence that they are different kinds of date: it holds the project date and no
-- manufacture date at all.
--
-- `pm_existing_year_provenance` prints that breakdown live.
--
--
-- == WHERE THE PARSE COMES FROM =============================================
--
-- Not from here. Pinexplore's `ipdb_machine_additional_details` (sql/04_staging.sql)
-- parses the header line under a full-string-anchored grammar, keeps day precision in
-- its own column, and carries `additional_details_ipd_no` / `_players` purely as a
-- redundancy tripwire — they restate `IpdbId` and `Players`, so a capture-group slip
-- makes them disagree instead of silently writing a wrong month. This file re-asserts
-- that tripwire on the emitted set.
--
-- The ATTACH below is the only way to reach it: `AdditionalDetails` never became catalog
-- data, so it is absent from `models.extra_data` and from every foundation column, and
-- flippatch's `scripts/analysis/evidence.sql` bridge deliberately carries the web-scrape
-- cache alone. The path is relative to the FLIPCOMMONS checkout, because that is where
-- the runner cd's before invoking DuckDB — the same frame `evidence.sql` documents. And
-- like that file, `ATTACH` takes a string LITERAL, so this cannot honour a
-- `PINEXPLORE_DIR` override; the sibling layout is assumed.
INSTALL sqlite;
ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- == 1 · ANALYSIS ===========================================================

-- One row per IPDB dump record, with the header-line parse beside the structured
-- manufacture date. The join is the whole reason both are here: the pair, not either
-- column alone, is what classifies a date as project or manufacture.
CREATE OR REPLACE VIEW _pm_ipdb AS
SELECT
  im.IpdbId                              AS ipdb_id,
  im.DateOfManufacture                   AS manufacture_date,
  im.AdditionalDetails                   AS header_line,
  TRY_CAST(im.Players AS UTINYINT)       AS dump_players,
  ad.additional_details_ipd_no           AS parsed_ipd_no,
  ad.additional_details_players          AS parsed_players,
  ad.additional_details_date_string      AS parsed_date_string,
  ad.additional_details_date_year        AS parsed_year,
  ad.additional_details_date_month       AS parsed_month,
  ad.additional_details_date_day         AS parsed_day
FROM px.ipdb_machines AS im
JOIN px.ipdb_machine_additional_details AS ad USING (IpdbId);

-- Every live model whose IPDB listing holds a project date naming a MONTH, where the
-- catalog holds no project date.
--
-- The month requirement is what separates this from 0268's leftovers generally: a
-- year-only project date on an already-dated model is a thinner claim and a different
-- judgment, and it is not in scope here.
CREATE OR REPLACE VIEW pm_candidates AS
SELECT
  m.id,
  m.slug,
  m.name,
  m.manufacturer_slug,
  m.manufacturer_name,
  m.production_status_slug,
  m.production_year,
  m.production_month,
  m.project_year,
  m.project_month,
  i.*
FROM models AS m
JOIN _pm_ipdb AS i ON i.ipdb_id = m.ipdb_id
WHERE i.manufacture_date IS NULL
  AND i.parsed_month IS NOT NULL
  AND m.project_year IS NULL
  AND m.project_month IS NULL;

-- Who asserted the production_year each candidate already carries. Not read by the
-- generator — it is the evidence that the existing date and this patch's date come from
-- different places, kept queryable so the README's claim can be re-checked.
CREATE OR REPLACE VIEW pm_existing_year_provenance AS
SELECT
  c.ingest_source_slug,
  COALESCE(c.patch_id, '(baseline)') AS patch_id,
  count(*)                           AS n
FROM pm_candidates AS p
JOIN model_claims AS c ON c.model_id = p.id AND c.field_name = 'production_year'
GROUP BY 1, 2
ORDER BY n DESC;

-- The emitted set. One `project_year` and one `project_month` per model, cited to the
-- machine listing with its own header line as the verbatim quote.
--
-- Both fields, always. `project_month` alone would violate the model's own
-- month-needs-a-year constraint, and the year it needs is the project year — not the
-- production year the record already holds, which belongs to a different source and a
-- different kind of date.
--
-- The quote is the RAW `AdditionalDetails` string, not a reassembled one: the `ipdb:`
-- resolver reproduces that field unlabelled in the document `make verify-quote-verbatim`
-- matches against, so cutting from the source column makes the quote verbatim by
-- construction. It is also what preserves IPDB's DAY precision — nearly every date here
-- names a day, the catalog has year and month only, and the quote is where the day
-- survives.
CREATE OR REPLACE VIEW pm_patch_rows AS
SELECT
  c.id,
  c.slug,
  c.name,
  c.manufacturer_name,
  c.ipdb_id,
  'ipdb:' || c.ipdb_id::VARCHAR AS cite_ref,
  c.header_line                 AS quote,
  c.parsed_year::INTEGER        AS project_year,
  c.parsed_month::INTEGER       AS project_month,
  c.parsed_day::INTEGER         AS ipdb_day,
  c.parsed_date_string          AS ipdb_date_string,
  c.production_year
FROM pm_candidates AS c
WHERE c.parsed_year IS NOT NULL
  AND c.parsed_year <= c.production_year;

-- Held back, and why. Two rows today, both under `project_date_after_production_year`.
--
-- A project date is the design milestone that PRECEDES manufacture, so a project year
-- later than the year the machine was produced is a contradiction on its face, and
-- writing one would leave the record stating that the game was designed after it was
-- built. It does not say which of the two dates is wrong — our production year comes
-- from another source and may be the mistaken one — only that they cannot both stand
-- unexamined. That is a review, not a fill.
--
-- The second branch is structural: a month with no year is a row the database rejects
-- outright. It is empty today, because the upstream grammar never yields a month without
-- a year, and it exists so that such a row could never be dropped silently between
-- detection and emission.
CREATE OR REPLACE VIEW pm_rejected AS
SELECT
  c.id,
  c.slug,
  c.manufacturer_name,
  c.ipdb_id,
  c.production_year,
  c.parsed_date_string,
  'project_date_after_production_year' AS reason
FROM pm_candidates AS c
WHERE c.parsed_year IS NOT NULL AND c.parsed_year > c.production_year
UNION ALL
SELECT
  c.id,
  c.slug,
  c.manufacturer_name,
  c.ipdb_id,
  c.production_year,
  c.parsed_date_string,
  'month_parsed_without_a_year' AS reason
FROM pm_candidates AS c
WHERE c.parsed_year IS NULL;

-- == 2 · SUMMARY & CHECKS ===================================================

CREATE OR REPLACE VIEW pm_summary AS
            SELECT 'models_live' AS metric, (SELECT count(*) FROM models) AS value
  UNION ALL SELECT 'models_with_a_project_year',
    (SELECT count(*) FROM models WHERE project_year IS NOT NULL)
  UNION ALL SELECT 'ipdb_project_dates_naming_a_month',
    (SELECT count(*) FROM _pm_ipdb WHERE manufacture_date IS NULL
       AND parsed_month IS NOT NULL)
  UNION ALL SELECT 'candidates',   (SELECT count(*) FROM pm_candidates)
  UNION ALL SELECT 'patch_rows',   (SELECT count(*) FROM pm_patch_rows)
  UNION ALL SELECT 'patch_rows_ipdb_day_precision',
    (SELECT count(ipdb_day) FROM pm_patch_rows)
  UNION ALL SELECT 'patch_rows_already_holding_a_production_year',
    (SELECT count(production_year) FROM pm_patch_rows)
  UNION ALL SELECT 'patch_rows_where_the_two_years_agree',
    (SELECT count(*) FROM pm_patch_rows WHERE production_year = project_year)
  UNION ALL SELECT 'patch_rows_makers',
    (SELECT count(DISTINCT manufacturer_name) FROM pm_patch_rows)
  UNION ALL SELECT 'rejected',     (SELECT count(*) FROM pm_rejected)
  UNION ALL SELECT 'rejected_project_after_production',
    (SELECT count(*) FROM pm_rejected WHERE reason = 'project_date_after_production_year')
  ORDER BY metric;

-- Empty when healthy.
CREATE OR REPLACE VIEW pm_checks AS
  -- Correctness, and the campaign's whole premise, inherited from 0268: an emitted row's
  -- listing must hold NO manufacture date. With one, the header date is a production
  -- date and this patch would file it under the wrong field.
  SELECT 'row_has_manufacture_date' AS check_name, r.id, r.slug AS detail
  FROM pm_patch_rows r JOIN pm_candidates c ON c.id = r.id
  WHERE c.manufacture_date IS NOT NULL
  UNION ALL
  -- Correctness: this campaign only FILLS an empty project date. A row targeting a model
  -- that already has one would compete with an existing catalog claim.
  SELECT 'row_targets_model_with_a_project_date', r.id, r.slug
  FROM pm_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.project_year IS NOT NULL OR m.project_month IS NOT NULL
  UNION ALL
  -- Correctness: this campaign never touches the production date, which belongs to
  -- another source. A row whose target lost its production year is a different case than
  -- the one analysed here and should be re-read, not emitted.
  SELECT 'row_target_lost_its_production_year', r.id, r.slug
  FROM pm_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.production_year IS NULL
  UNION ALL
  -- Correctness: a design milestone cannot postdate the manufacture it precedes.
  -- `pm_rejected` is where such a row goes.
  SELECT 'row_project_date_after_production_year', r.id, r.slug
  FROM pm_patch_rows r WHERE r.project_year > r.production_year
  UNION ALL
  -- Structural: a month with no year violates the model's own constraint. `pm_rejected`
  -- is where such a row goes.
  SELECT 'month_without_year', r.id, r.slug
  FROM pm_patch_rows r WHERE r.project_month IS NOT NULL AND r.project_year IS NULL
  UNION ALL
  -- Structural: emitted + rejected must partition the candidates, so a row can never be
  -- silently dropped between detection and emission.
  SELECT 'scored_partition_broken', NULL::BIGINT, 'emitted + rejected != candidates'
  WHERE (SELECT count(*) FROM pm_candidates)
     <> (SELECT count(*) FROM pm_patch_rows) + (SELECT count(*) FROM pm_rejected)
  UNION ALL
  -- Structural: one row per model — gen.py writes one entry per row, and a duplicated
  -- ref collides at apply.
  SELECT 'row_duplicated', r.id, r.slug FROM pm_patch_rows r
  GROUP BY r.id, r.slug HAVING count(*) > 1
  UNION ALL
  -- Vocabulary: the patch schema types `project_year` at 1800-2100 and `project_month`
  -- at 1-12, and the database enforces the same range. Fail here, not at apply.
  SELECT 'year_out_of_range', r.id, r.project_year::VARCHAR
  FROM pm_patch_rows r WHERE r.project_year NOT BETWEEN 1800 AND 2100
  UNION ALL
  SELECT 'month_out_of_range', r.id, r.project_month::VARCHAR
  FROM pm_patch_rows r WHERE r.project_month NOT BETWEEN 1 AND 12
  UNION ALL
  -- Evidence: every row must carry a quote.
  SELECT 'row_without_quote', r.id, r.slug
  FROM pm_patch_rows r WHERE r.quote IS NULL OR r.quote = ''
  UNION ALL
  -- Evidence: the quote must be the listing's own header line, opening with the IPD
  -- number the cite addresses. A quote that drifted off its record would still verify as
  -- verbatim against the wrong document.
  SELECT 'quote_not_header_of_cited_record', r.id, r.quote
  FROM pm_patch_rows r
  WHERE NOT starts_with(r.quote, 'IPD No. ' || r.ipdb_id::VARCHAR)
  UNION ALL
  -- Evidence: the quote must survive `patchkit.clean_quote` unchanged. That helper
  -- straightens smart quotes and rewrites an ellipsis, and either would break verbatim
  -- matching. Plain printable ASCII is the sufficient condition, and the dump's mojibake
  -- lives in TITLES, which the header line does not carry.
  SELECT 'quote_not_plain_ascii', r.id, r.quote
  FROM pm_patch_rows r WHERE length(r.quote) <> strlen(r.quote)
  UNION ALL
  -- Tripwire, re-asserted on the emitted set: the parse's redundant capture groups must
  -- still restate the record they came from. A capture-group slip in the upstream grammar
  -- shows up here as a disagreeing IPD number or player count, and it means the DATE in
  -- the same row is wrong too.
  SELECT 'parse_ipd_no_disagrees', c.id, c.slug
  FROM pm_candidates c WHERE c.parsed_ipd_no IS DISTINCT FROM c.ipdb_id
  UNION ALL
  SELECT 'parse_players_disagree', c.id, c.slug
  FROM pm_candidates c
  WHERE c.dump_players IS NOT NULL AND c.parsed_players IS DISTINCT FROM c.dump_players
  UNION ALL
  -- Anchors. These probe the PARSE and the JOIN, not `pm_patch_rows`: the emitted set
  -- legitimately drains to zero the moment this patch applies, so anchoring on it could
  -- not tell "the campaign finished" from "the grammar rotted".
  --
  -- One: the shape this campaign reads — a day-precision project date on a model the
  -- catalog dates from elsewhere. Baby Pac-Man is 0268's own worked example of why a
  -- project date is not a never-produced marker: a project date AND 7,000 units built.
  SELECT 'anchor_day_precision_project_date', NULL::BIGINT,
         'ipdb 125 no longer parses October 11, 1982 onto baby-pac-man'
  WHERE NOT EXISTS (
    SELECT 1 FROM _pm_ipdb i JOIN models m ON m.ipdb_id = i.ipdb_id
    WHERE i.ipdb_id = 125 AND m.slug = 'baby-pac-man'
      AND i.parsed_year = 1982 AND i.parsed_month = 10 AND i.parsed_day = 11
      AND i.manufacture_date IS NULL)
  UNION ALL
  -- Two: the exclusion that defines the scope. A listing holding a manufacture date must
  -- never reach the candidates, however its header line reads.
  SELECT 'anchor_manufacture_dates_excluded', NULL::BIGINT,
         'a listing with a manufacture date reached pm_candidates'
  WHERE EXISTS (
    SELECT 1 FROM pm_candidates c WHERE c.manufacture_date IS NOT NULL);
