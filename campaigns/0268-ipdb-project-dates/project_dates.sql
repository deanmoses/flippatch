-- IPDB project dates for models the catalog holds no date for at all.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, liveness
-- filtering, the NULL-spelling regularization) is FLIPCOMMONS' shared foundation; the
-- runner loads it under this file automatically, so nothing is `.read` here.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so that this file's ATTACH and the
-- foundation's own resolve. `make analyze` handles that and delegates to flipcommons'
-- shared runner. Do not run this file directly:
--
--     F=campaigns/0268-ipdb-project-dates/project_dates.sql
--     make analyze FILE=$F PREFIX=pd                          # summary, gated on checks
--     make analyze FILE=$F Q="FROM pd_patch_rows;"             # exactly what gen.py emits
--     make analyze FILE=$F Q="FROM pd_rejected;"               # what the gate held back
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
--
-- == WHY THESE MODELS HAVE NO DATE ==========================================
--
-- Our IPDB baseline came from a JSON dump with two date carriers, and the ingest read
-- only one of them:
--
--   * `DateOfManufacture` — a structured field, populated on 5,265 of 6,664 records.
--     The only one the ingest read.
--   * `AdditionalDetails` — populated on all 6,664, and verbatim the header line the
--     IPDB machine page renders: `IPD No. 3711 / May, 1989 / 4 Players`.
--
-- IPDB carries two kinds of date and labels them separately on the page: a Date Of
-- Manufacture (physical assembly, factory rollout) and a Project Date (the design
-- milestone logged in the manufacturer's own records). Per IPDB's stated display rule,
-- the header line shows whichever it holds, preferring the manufacture date when it
-- holds both. The dump's `DateOfManufacture` is populated if and only if IPDB holds a
-- manufacture date — so a listing with only a project date arrives with that field null
-- and its date surviving only in the header line we never ingested.
--
-- That makes `DateOfManufacture IS NULL AND a parsed header date IS NOT NULL` the
-- definition of "IPDB holds only a project date", with no page fetching and no
-- per-record judgment. `pd_checks` asserts the emitted set never violates it.
--
--
-- == WHERE THE PARSE COMES FROM =============================================
--
-- Not from here. Pinexplore's `ipdb_machine_additional_details` (sql/04_staging.sql)
-- parses the header line under a full-string-anchored grammar, keeps day precision in
-- its own column, and carries `additional_details_ipd_no` / `_players` purely as a
-- redundancy tripwire — they restate `IpdbId` and `Players`, so a capture-group slip
-- makes them disagree instead of silently writing a wrong year. Pinexplore asserts that
-- tripwire itself (sql/05_error_checks.sql); this file re-asserts it on the emitted set,
-- because a wrong year in an identity field is this campaign's worst failure mode.
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
CREATE OR REPLACE VIEW _pd_ipdb AS
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

-- Every live model the catalog holds NO date for — neither a production date nor a
-- project date — whose IPDB listing carries a parsed header date.
--
-- `models.year` is the derived fallback column: production date, else project date. So
-- `year IS NULL` is the honest scope test ("this model reads as undated on the site"),
-- and it drains as this patch applies, which is why the anchors below probe the parse
-- and the join rather than this view.
CREATE OR REPLACE VIEW pd_candidates AS
SELECT
  m.id,
  m.slug,
  m.name,
  m.manufacturer_slug,
  m.manufacturer_name,
  m.production_status_slug,
  i.*
FROM models AS m
JOIN _pd_ipdb AS i ON i.ipdb_id = m.ipdb_id
WHERE m.year IS NULL
  AND i.parsed_year IS NOT NULL;

-- The emitted set. One row per model, one `project_year` and — where IPDB names a month
-- — one `project_month`, cited to the machine listing with its own header line as the
-- verbatim quote.
--
-- The quote is the RAW `AdditionalDetails` string, not a reassembled one: the `ipdb:`
-- resolver reproduces that field unlabelled in the document `make verify-quote-verbatim`
-- matches against, so cutting from the source column makes the quote verbatim by
-- construction. It is also what preserves IPDB's DAY precision — 90 of these dates name
-- a day, the catalog has year and month only, and the quote is where the day survives.
--
-- Day precision is deliberately NOT truncated here into a note; `pd_checks` only requires
-- that the month the patch asserts agrees with the day-precision parse.
CREATE OR REPLACE VIEW pd_patch_rows AS
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
  c.parsed_date_string          AS ipdb_date_string
FROM pd_candidates AS c
WHERE c.manufacture_date IS NULL;

-- Held back, and why. Empty today: every candidate's listing lacks a manufacture date.
--
-- The branch exists because the one candidate this campaign must never emit is a model
-- whose IPDB listing DOES hold a manufacture date — that date is a production date, it
-- belongs in `production_year`, and the reason our ingest missed it would be a different
-- bug than the one this campaign fixes. Routing it here rather than dropping it silently
-- is what makes the partition check below meaningful.
CREATE OR REPLACE VIEW pd_rejected AS
SELECT
  c.id,
  c.slug,
  c.manufacturer_name,
  c.ipdb_id,
  c.parsed_date_string,
  'ipdb_holds_a_manufacture_date' AS reason
FROM pd_candidates AS c
WHERE c.manufacture_date IS NOT NULL;

-- == 2 · SUMMARY & CHECKS ===================================================

CREATE OR REPLACE VIEW pd_summary AS
            SELECT 'models_live' AS metric, (SELECT count(*) FROM models) AS value
  UNION ALL SELECT 'models_undated',      (SELECT count(*) FROM models WHERE year IS NULL)
  UNION ALL SELECT 'models_undated_with_ipdb_id',
    (SELECT count(*) FROM models WHERE year IS NULL AND ipdb_id IS NOT NULL)
  UNION ALL SELECT 'candidates',          (SELECT count(*) FROM pd_candidates)
  UNION ALL SELECT 'patch_rows',          (SELECT count(*) FROM pd_patch_rows)
  UNION ALL SELECT 'patch_rows_with_month',
    (SELECT count(project_month) FROM pd_patch_rows)
  UNION ALL SELECT 'patch_rows_ipdb_day_precision',
    (SELECT count(ipdb_day) FROM pd_patch_rows)
  UNION ALL SELECT 'patch_rows_unreleased',
    (SELECT count(*) FROM pd_candidates c JOIN pd_patch_rows r ON r.id = c.id
     WHERE c.production_status_slug = 'unreleased')
  UNION ALL SELECT 'rejected',            (SELECT count(*) FROM pd_rejected)
  UNION ALL SELECT 'dump_rows_with_parsed_year',
    (SELECT count(*) FROM _pd_ipdb WHERE parsed_year IS NOT NULL)
  ORDER BY metric;

-- Empty when healthy.
CREATE OR REPLACE VIEW pd_checks AS
  -- Correctness, and the campaign's whole premise: an emitted row's listing must hold no
  -- manufacture date. With one, the header date is a PRODUCTION date and this patch would
  -- file it under the wrong field.
  SELECT 'row_has_manufacture_date' AS check_name, r.id, r.slug AS detail
  FROM pd_patch_rows r JOIN pd_candidates c ON c.id = r.id
  WHERE c.manufacture_date IS NOT NULL
  UNION ALL
  -- Correctness: this campaign only FILLS a model with no date at all. A row targeting a
  -- dated model would compete with an existing catalog claim.
  SELECT 'row_targets_dated_model', r.id, r.slug
  FROM pd_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.year IS NOT NULL
  UNION ALL
  -- Structural: emitted + rejected must partition the candidates, so a row can never be
  -- silently dropped between detection and emission.
  SELECT 'scored_partition_broken', NULL::BIGINT, 'emitted + rejected != candidates'
  WHERE (SELECT count(*) FROM pd_candidates)
     <> (SELECT count(*) FROM pd_patch_rows) + (SELECT count(*) FROM pd_rejected)
  UNION ALL
  -- Structural: one row per model — gen.py writes one entry per row, and a duplicated
  -- ref collides at apply.
  SELECT 'row_duplicated', r.id, r.slug FROM pd_patch_rows r
  GROUP BY r.id, r.slug HAVING count(*) > 1
  UNION ALL
  -- Vocabulary: the patch schema types `project_year` at 1800-2100 and `project_month`
  -- at 1-12, and the database enforces the same range. Fail here, not at apply.
  SELECT 'year_out_of_range', r.id, r.project_year::VARCHAR
  FROM pd_patch_rows r WHERE r.project_year NOT BETWEEN 1800 AND 2100
  UNION ALL
  SELECT 'month_out_of_range', r.id, r.project_month::VARCHAR
  FROM pd_patch_rows r WHERE r.project_month NOT BETWEEN 1 AND 12
  UNION ALL
  -- Structural: a month with no year violates the model's own constraint.
  SELECT 'month_without_year', r.id, r.slug
  FROM pd_patch_rows r WHERE r.project_month IS NOT NULL AND r.project_year IS NULL
  UNION ALL
  -- Correctness: a day-precision listing must contribute its month. A date parsed to the
  -- day but emitted without a month means the parse and the emission disagree.
  SELECT 'day_precision_without_month', r.id, r.ipdb_date_string
  FROM pd_patch_rows r WHERE r.ipdb_day IS NOT NULL AND r.project_month IS NULL
  UNION ALL
  -- Evidence: every row must carry a quote.
  SELECT 'row_without_quote', r.id, r.slug
  FROM pd_patch_rows r WHERE r.quote IS NULL OR r.quote = ''
  UNION ALL
  -- Evidence: the quote must be the listing's own header line, opening with the IPD
  -- number the cite addresses. A quote that drifted off its record would still verify as
  -- verbatim against the wrong document.
  SELECT 'quote_not_header_of_cited_record', r.id, r.quote
  FROM pd_patch_rows r
  WHERE NOT starts_with(r.quote, 'IPD No. ' || r.ipdb_id::VARCHAR)
  UNION ALL
  -- Evidence: the quote must survive `patchkit.clean_quote` unchanged. That helper
  -- straightens smart quotes and rewrites an ellipsis, and either would break verbatim
  -- matching against the source. Plain printable ASCII is the sufficient condition, and
  -- the dump's mojibake (`Barrel O? Fun ?61`) lives in TITLES, which the header line does
  -- not carry — so this holds today and says so if that ever changes.
  SELECT 'quote_not_plain_ascii', r.id, r.quote
  FROM pd_patch_rows r WHERE length(r.quote) <> strlen(r.quote)
  UNION ALL
  -- Tripwire, re-asserted on the emitted set: the parse's redundant capture groups must
  -- still restate the record they came from. A capture-group slip in the upstream grammar
  -- shows up here as a disagreeing IPD number or player count, and it means the DATE in
  -- the same row is wrong too.
  SELECT 'parse_ipd_no_disagrees', c.id, c.slug
  FROM pd_candidates c WHERE c.parsed_ipd_no IS DISTINCT FROM c.ipdb_id
  UNION ALL
  SELECT 'parse_players_disagree', c.id, c.slug
  FROM pd_candidates c
  WHERE c.dump_players IS NOT NULL AND c.parsed_players IS DISTINCT FROM c.dump_players
  UNION ALL
  -- Anchors. These probe the PARSE and the JOIN, not `pd_patch_rows`: the emitted set
  -- legitimately drains to zero the moment this patch applies — every model it targeted
  -- now has a date and drops out of scope — so anchoring on it could not tell "the
  -- campaign finished" from "the grammar rotted". One anchor per header-date shape the
  -- grammar admits, each also asserting the dump record still resolves onto its model.
  SELECT 'anchor_month_year_dark', NULL::BIGINT,
         'ipdb 3711 no longer parses May 1989 onto ice-castle'
  WHERE NOT EXISTS (
    SELECT 1 FROM _pd_ipdb i JOIN models m ON m.ipdb_id = i.ipdb_id
    WHERE i.ipdb_id = 3711 AND m.slug = 'ice-castle'
      AND i.parsed_year = 1989 AND i.parsed_month = 5 AND i.parsed_day IS NULL
      AND i.manufacture_date IS NULL)
  UNION ALL
  SELECT 'anchor_year_only_dark', NULL::BIGINT,
         'ipdb 6592 no longer parses a bare 1990 onto a-world-of-clowns'
  WHERE NOT EXISTS (
    SELECT 1 FROM _pd_ipdb i JOIN models m ON m.ipdb_id = i.ipdb_id
    WHERE i.ipdb_id = 6592 AND m.slug = 'a-world-of-clowns'
      AND i.parsed_year = 1990 AND i.parsed_month IS NULL
      AND i.manufacture_date IS NULL)
  UNION ALL
  SELECT 'anchor_day_precision_dark', NULL::BIGINT,
         'ipdb 148 no longer parses December 9 1935 onto bally-derby'
  WHERE NOT EXISTS (
    SELECT 1 FROM _pd_ipdb i JOIN models m ON m.ipdb_id = i.ipdb_id
    WHERE i.ipdb_id = 148 AND m.slug = 'bally-derby'
      AND i.parsed_year = 1935 AND i.parsed_month = 12 AND i.parsed_day = 9
      AND i.manufacture_date IS NULL)
  UNION ALL
  -- Anchor, the other direction: a listing that DOES hold a manufacture date must still
  -- be recognized as one, or the classifier has gone one-sided and every date would read
  -- as a project date.
  SELECT 'anchor_manufacture_date_dark', NULL::BIGINT,
         'ipdb 987 (Gator) no longer reads as holding a manufacture date'
  WHERE NOT EXISTS (
    SELECT 1 FROM _pd_ipdb i
    WHERE i.ipdb_id = 987 AND i.manufacture_date IS NOT NULL AND i.parsed_year = 1969)
  UNION ALL
  -- Drift: the upstream parse covers most of the dump. A collapse to near-nothing is a
  -- rotted grammar or a moved column, which no row-level invariant above can see.
  SELECT 'dump_parse_collapsed', NULL::BIGINT,
         'only ' || (SELECT count(*) FROM _pd_ipdb WHERE parsed_year IS NOT NULL)
           || ' dump rows carry a parsed header year'
  WHERE (SELECT count(*) FROM _pd_ipdb WHERE parsed_year IS NOT NULL) < 5000;
