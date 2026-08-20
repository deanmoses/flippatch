-- IPDB production months the structured date field could not express: January.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, liveness
-- filtering, the NULL-spelling regularization) is FLIPCOMMONS' shared foundation; the
-- runner loads it under this file automatically, so nothing is `.read` here.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so that this file's ATTACH and the
-- foundation's own resolve. `make analyze` handles that and delegates to flipcommons'
-- shared runner. Do not run this file directly:
--
--     F=campaigns/0277-ipdb-january-months/january_months.sql
--     make analyze FILE=$F PREFIX=jm                 # summary, gated on checks
--     make analyze FILE=$F Q="FROM jm_patch_rows;"    # exactly what gen.py emits
--     make analyze FILE=$F Q="FROM jm_rejected;"      # what the gate held back
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
--
-- == WHY THESE MODELS HAVE A YEAR BUT NO MONTH ==============================
--
-- `DateOfManufacture` in the IPDB dump is a full timestamp, so a listing IPDB dates
-- only to a year arrives padded to the first of January: `1938-01-01`. That padding is
-- indistinguishable, IN THAT FIELD, from a machine genuinely dated January 1938. Our
-- baseline read `-01-01` as year-only precision — the safe call for a field that cannot
-- tell the two apart — and every genuine January without a day lost its month.
--
-- The header line has no such ambiguity, because IPDB renders the two differently:
--
--     IPD No. 12   / January, 1938 / 1 Player     <- month precision
--     IPD No. 6592 / 1990                         <- year precision
--
-- The shortfall is visible in one table. Across every model whose IPDB listing holds a
-- manufacture date naming a month, the catalog carries that month on 100% of every
-- month except January, where IPDB names 374 and the catalog holds 156:
--
--     month     1    2    3    4    5    6    7    8    9   10   11   12
--     IPDB    374  481  314  341  379  392  294  328  282  338  331  306
--     ours    156  481  314  341  379  392  294  328  282  338  331  306
--
-- `jm_month_shortfall` recomputes that table live. And the claim record confirms the
-- mechanism from the other side: of the January listings, `ipdb` asserted a
-- `production_month` only where the date also names a DAY (`1936-01-15`, which is not
-- `-01-01` and so survived the padding rule). Not one January month came from a
-- `-01-01` date. `jm_checks` re-asserts that on the emitted set.
--
--
-- == WHERE THE PARSE COMES FROM =============================================
--
-- Not from here. Pinexplore's `ipdb_machine_additional_details` (sql/04_staging.sql)
-- parses the header line under a full-string-anchored grammar and carries
-- `additional_details_ipd_no` / `_players` purely as a redundancy tripwire — they
-- restate `IpdbId` and `Players`, so a capture-group slip makes them disagree instead of
-- silently writing a wrong month. This file re-asserts that tripwire on the emitted set,
-- and adds the one that matters most here: the header's month must equal
-- `DateOfManufacture`'s month. Corpus-wide that holds on all 4,167 records where both
-- name a month, with zero disagreements — which is what makes the padding story a
-- reading of the data rather than a guess about it.
--
-- The ATTACH below is the only way to reach the parse: `AdditionalDetails` never became
-- catalog data, so it is absent from `models.extra_data` and from every foundation
-- column, and flippatch's `scripts/analysis/evidence.sql` bridge deliberately carries
-- the web-scrape cache alone. The path is relative to the FLIPCOMMONS checkout, because
-- that is where the runner cd's before invoking DuckDB — the same frame `evidence.sql`
-- documents. And like that file, `ATTACH` takes a string LITERAL, so this cannot honour
-- a `PINEXPLORE_DIR` override; the sibling layout is assumed.
INSTALL sqlite;
ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- == 1 · ANALYSIS ===========================================================

-- One row per IPDB dump record, with the header-line parse beside the structured
-- manufacture date. `manufacture_date IS NOT NULL` is 0268's classifier, used here in
-- the positive: it is what makes the header date a PRODUCTION date.
CREATE OR REPLACE VIEW _jm_ipdb AS
SELECT
  im.IpdbId                              AS ipdb_id,
  im.DateOfManufacture                   AS manufacture_date,
  im.AdditionalDetails                   AS header_line,
  TRY_CAST(im.Players AS UTINYINT)       AS dump_players,
  -- The month the STRUCTURED field carries, for the tripwire below only. Never the
  -- month this campaign emits: on every row here it reads 01 by construction.
  TRY_CAST(regexp_extract(im.DateOfManufacture, '\d{4}-(\d{2})', 1) AS INTEGER)
                                         AS manufacture_date_month,
  ad.additional_details_ipd_no           AS parsed_ipd_no,
  ad.additional_details_players          AS parsed_players,
  ad.additional_details_date_string      AS parsed_date_string,
  ad.additional_details_date_year        AS parsed_year,
  ad.additional_details_date_month       AS parsed_month,
  ad.additional_details_date_day         AS parsed_day
FROM px.ipdb_machines AS im
JOIN px.ipdb_machine_additional_details AS ad USING (IpdbId);

-- The shortfall table from the header comment, recomputed live. Not read by the
-- generator — it is the evidence for WHY this campaign exists, kept queryable so the
-- claim in the README can be re-checked rather than trusted.
CREATE OR REPLACE VIEW jm_month_shortfall AS
SELECT
  i.parsed_month                          AS month,
  count(*)                                AS ipdb_names_it,
  count(m.production_month)               AS catalog_holds_it,
  count(*) - count(m.production_month)    AS shortfall
FROM models AS m
JOIN _jm_ipdb AS i ON i.ipdb_id = m.ipdb_id
WHERE i.manufacture_date IS NOT NULL AND i.parsed_month IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- Every live model whose IPDB listing holds a MANUFACTURE date naming a month, where
-- the catalog holds no production month.
--
-- `production_month IS NULL` is the scope test, and it drains as this patch applies,
-- which is why the anchors below probe the parse and the join rather than this view.
CREATE OR REPLACE VIEW jm_candidates AS
SELECT
  m.id,
  m.slug,
  m.name,
  m.manufacturer_slug,
  m.manufacturer_name,
  m.production_year,
  m.production_month,
  i.*
FROM models AS m
JOIN _jm_ipdb AS i ON i.ipdb_id = m.ipdb_id
WHERE i.manufacture_date IS NOT NULL
  AND i.parsed_month IS NOT NULL
  AND m.production_month IS NULL
  AND m.production_year IS NOT NULL;

-- The emitted set. One `production_month` per model, cited to the machine listing with
-- its own header line as the verbatim quote.
--
-- The quote is the RAW `AdditionalDetails` string, not a reassembled one: the `ipdb:`
-- resolver reproduces that field unlabelled in the document `make verify-quote-verbatim`
-- matches against, so cutting from the source column makes the quote verbatim by
-- construction.
--
-- No `production_year` is emitted. Every candidate already carries one, asserted by
-- `ipdb` from the same listing, and re-asserting it would compete with a claim that
-- already says the same thing.
CREATE OR REPLACE VIEW jm_patch_rows AS
SELECT
  c.id,
  c.slug,
  c.name,
  c.manufacturer_name,
  c.ipdb_id,
  'ipdb:' || c.ipdb_id::VARCHAR AS cite_ref,
  c.header_line                 AS quote,
  c.parsed_month::INTEGER       AS production_month,
  c.production_year,
  c.parsed_year::INTEGER        AS ipdb_year,
  c.parsed_date_string          AS ipdb_date_string
FROM jm_candidates AS c
WHERE c.production_year = c.parsed_year;

-- Held back, and why. One row today: `asteroid-killer`, where the catalog says 1979 and
-- IPDB's listing says January, 1980.
--
-- A year disagreement is not a month gap. Emitting a month from a listing that dates the
-- machine to a different year would attach IPDB's month to our year and produce a date
-- neither source states. These belong in a year review, not in this patch.
CREATE OR REPLACE VIEW jm_rejected AS
SELECT
  c.id,
  c.slug,
  c.manufacturer_name,
  c.ipdb_id,
  c.production_year,
  c.parsed_date_string,
  'catalog_year_disagrees_with_ipdb' AS reason
FROM jm_candidates AS c
WHERE c.production_year IS DISTINCT FROM c.parsed_year;

-- == 2 · SUMMARY & CHECKS ===================================================

CREATE OR REPLACE VIEW jm_summary AS
            SELECT 'models_live' AS metric, (SELECT count(*) FROM models) AS value
  UNION ALL SELECT 'models_with_ipdb_id',
    (SELECT count(*) FROM models WHERE ipdb_id IS NOT NULL)
  UNION ALL SELECT 'ipdb_manufacture_dates_naming_a_month',
    (SELECT count(*) FROM _jm_ipdb WHERE manufacture_date IS NOT NULL
       AND parsed_month IS NOT NULL)
  UNION ALL SELECT 'candidates',    (SELECT count(*) FROM jm_candidates)
  UNION ALL SELECT 'patch_rows',    (SELECT count(*) FROM jm_patch_rows)
  UNION ALL SELECT 'patch_rows_january',
    (SELECT count(*) FROM jm_patch_rows WHERE production_month = 1)
  UNION ALL SELECT 'patch_rows_makers',
    (SELECT count(DISTINCT manufacturer_name) FROM jm_patch_rows)
  UNION ALL SELECT 'rejected',      (SELECT count(*) FROM jm_rejected)
  UNION ALL SELECT 'january_shortfall',
    (SELECT shortfall FROM jm_month_shortfall WHERE month = 1)
  ORDER BY metric;

-- Empty when healthy.
CREATE OR REPLACE VIEW jm_checks AS
  -- Correctness, and the campaign's whole premise: an emitted row's listing must hold a
  -- manufacture date. Without one the header date is a PROJECT date and this patch would
  -- file it under the wrong field — 0268's job, inverted.
  SELECT 'row_has_no_manufacture_date' AS check_name, r.id, r.slug AS detail
  FROM jm_patch_rows r JOIN jm_candidates c ON c.id = r.id
  WHERE c.manufacture_date IS NULL
  UNION ALL
  -- Correctness: this campaign only FILLS a model with no production month.
  SELECT 'row_targets_model_with_a_month', r.id, r.slug
  FROM jm_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.production_month IS NOT NULL
  UNION ALL
  -- Correctness: the month rides the catalog's existing year, so the two sources must
  -- agree on that year. `jm_rejected` is where a disagreement goes.
  SELECT 'row_year_disagrees', r.id, r.slug
  FROM jm_patch_rows r WHERE r.production_year IS DISTINCT FROM r.ipdb_year
  UNION ALL
  -- Correctness: a model with a month and no year violates the model's own constraint.
  -- This campaign never emits a year, so every target must already have one.
  SELECT 'row_target_has_no_year', r.id, r.slug
  FROM jm_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.production_year IS NULL
  UNION ALL
  -- Structural: emitted + rejected must partition the candidates, so a row can never be
  -- silently dropped between detection and emission.
  SELECT 'scored_partition_broken', NULL::BIGINT, 'emitted + rejected != candidates'
  WHERE (SELECT count(*) FROM jm_candidates)
     <> (SELECT count(*) FROM jm_patch_rows) + (SELECT count(*) FROM jm_rejected)
  UNION ALL
  -- Structural: one row per model — gen.py writes one entry per row, and a duplicated
  -- ref collides at apply.
  SELECT 'row_duplicated', r.id, r.slug FROM jm_patch_rows r
  GROUP BY r.id, r.slug HAVING count(*) > 1
  UNION ALL
  -- Vocabulary: the patch schema types `production_month` at 1-12, and the database
  -- enforces the same range. Fail here, not at apply.
  SELECT 'month_out_of_range', r.id, r.production_month::VARCHAR
  FROM jm_patch_rows r WHERE r.production_month NOT BETWEEN 1 AND 12
  UNION ALL
  -- Evidence: every row must carry a quote.
  SELECT 'row_without_quote', r.id, r.slug
  FROM jm_patch_rows r WHERE r.quote IS NULL OR r.quote = ''
  UNION ALL
  -- Evidence: the quote must be the listing's own header line, opening with the IPD
  -- number the cite addresses. A quote that drifted off its record would still verify as
  -- verbatim against the wrong document.
  SELECT 'quote_not_header_of_cited_record', r.id, r.quote
  FROM jm_patch_rows r
  WHERE NOT starts_with(r.quote, 'IPD No. ' || r.ipdb_id::VARCHAR)
  UNION ALL
  -- Evidence: the quote must survive `patchkit.clean_quote` unchanged. That helper
  -- straightens smart quotes and rewrites an ellipsis, and either would break verbatim
  -- matching. Plain printable ASCII is the sufficient condition, and the dump's mojibake
  -- lives in TITLES, which the header line does not carry.
  SELECT 'quote_not_plain_ascii', r.id, r.quote
  FROM jm_patch_rows r WHERE length(r.quote) <> strlen(r.quote)
  UNION ALL
  -- Tripwire, re-asserted on the emitted set: the parse's redundant capture groups must
  -- still restate the record they came from. A capture-group slip in the upstream grammar
  -- shows up here as a disagreeing IPD number or player count, and it means the MONTH in
  -- the same row is wrong too.
  SELECT 'parse_ipd_no_disagrees', c.id, c.slug
  FROM jm_candidates c WHERE c.parsed_ipd_no IS DISTINCT FROM c.ipdb_id
  UNION ALL
  SELECT 'parse_players_disagree', c.id, c.slug
  FROM jm_candidates c
  WHERE c.dump_players IS NOT NULL AND c.parsed_players IS DISTINCT FROM c.dump_players
  UNION ALL
  -- THE load-bearing check. The header line and the structured field are two renderings
  -- of one date, and this campaign trusts the header over the field on precision alone.
  -- That is only safe while the two never disagree on the month itself. Asserted over
  -- the WHOLE corpus, not the emitted set: a disagreement anywhere falsifies the
  -- premise, and the emitted set is the last place it would show up.
  SELECT 'header_month_disagrees_with_structured_field', i.ipdb_id, i.header_line
  FROM _jm_ipdb i
  WHERE i.parsed_month IS NOT NULL AND i.manufacture_date_month IS NOT NULL
    AND i.parsed_month IS DISTINCT FROM i.manufacture_date_month
  UNION ALL
  -- Anchors. These probe the PARSE and the JOIN, not `jm_patch_rows`: the emitted set
  -- legitimately drains to zero the moment this patch applies, so anchoring on it could
  -- not tell "the campaign finished" from "the grammar rotted".
  --
  -- One: the padding shape this campaign exists for — a header naming January against a
  -- structured field reading `-01-01`.
  SELECT 'anchor_january_padding', NULL::BIGINT,
         'ipdb 12 no longer parses January 1938 onto across-the-board'
  WHERE NOT EXISTS (
    SELECT 1 FROM _jm_ipdb i JOIN models m ON m.ipdb_id = i.ipdb_id
    WHERE i.ipdb_id = 12 AND m.slug = 'across-the-board'
      AND i.parsed_year = 1938 AND i.parsed_month = 1 AND i.parsed_day IS NULL
      AND starts_with(i.manufacture_date, '1938-01-01'))
  UNION ALL
  -- Two: the contrast case. A day-precision January is NOT padding, its month survived
  -- into the catalog, and it must stay out of scope.
  SELECT 'anchor_january_day_precision_out_of_scope', NULL::BIGINT,
         'a day-precision January is no longer excluded from jm_candidates'
  WHERE EXISTS (
    SELECT 1 FROM jm_candidates c WHERE c.parsed_day IS NOT NULL);
