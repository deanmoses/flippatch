-- IPDB's `Never Produced` production status, for models the catalog files as unknown.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, liveness
-- filtering, the NULL-spelling regularization) is FLIPCOMMONS' shared foundation; the
-- runner loads it under this file automatically, so nothing is `.read` here.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so that this file's ATTACH and its
-- relative JSONL path resolve. `make analyze` handles that and delegates to flipcommons'
-- shared runner. Do not run this file directly:
--
--     F=campaigns/0269-ipdb-never-produced/never_produced.sql
--     make analyze FILE=$F PREFIX=np                 # summary, gated on checks
--     make analyze FILE=$F Q="FROM np_patch_rows;"   # exactly what gen.py emits
--     make analyze FILE=$F Q="FROM np_rejected;"     # what the gate held back, and why
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
--
-- == WHY THE CATALOG DOES NOT KNOW THESE MACHINES WERE CANCELLED ============
--
-- Our IPDB baseline is `ipdb_xantari_2025_02_01.json`, and its `ProductionNumber` is an INTEGER
-- column. IPDB's own `Production:` row is not an integer field: it prints a quantity
-- (`1,750 units (confirmed)`) on machines that shipped and the words `Never Produced` on
-- machines that did not. Only the quantity survives the dump's typing. `Never Produced`
-- appears zero times in all 6,664 records, so a cancelled project arrives with a null
-- indistinguishable from "IPDB does not say" — and the catalog files both as unknown.
--
-- The status is recoverable only from the machine page itself. Pinexplore's web cache now
-- holds archive.org captures of IPDB machine pages, and
-- `scripts/web_scrape/extract_ipdb_to_jsonl.py` renders each through the machine-page
-- parser into `ingest_sources/ipdb_archive/models.jsonl`, where `production.status` is
-- the row's verbatim words when they are not a quantity.
--
--
-- == WHY IT IS SAFE TO READ THIS ONE FIELD FROM A STALE PAGE ================
--
-- The captures are mostly 2018; the dump is February 2025. The dump is therefore the
-- newer and more correct source, and NOTHING here may overwrite it. IPDB has visibly
-- moved on since those captures — it has relabelled header dates between
-- `Date Of Manufacture` and `Project Date`, and it has added dates to listings that had
-- none — so a page's DATE fields are actively untrustworthy and this analysis never
-- reads one.
--
-- What makes the production status different is that the dump has no column for it at
-- all. There is no newer value to lose: either the dump holds a QUANTITY, in which case
-- the dump wins and the row is rejected below, or the dump is silent and the page is the
-- only carrier. The two sources never contradict each other in the corpus — zero rows
-- pair a page status with a dump quantity, and where both state a number they agree
-- everywhere — and `np_checks` asserts the rejection branch that keeps it that way.
--
-- The same rule is enforced a second time, downstream, by the quote gate: flippatch's
-- `ipdb:` resolver renders a page-only label ONLY where the dump rendered no line under
-- it, so a quote of `Production: Never Produced` cannot verify against a record whose
-- dump row states a number.
--
--
-- == WHY `unreleased` AND NOT `one-off` =====================================
--
-- DomainModel.md distinguishes `unreleased` ("a project intended for commercial
-- production, but cancelled -- it may have resulted in prototypes or sample runs") from
-- `one-off` ("built by a manufacturer but never intended for commercial production --
-- gifts, movie props, test pieces"). Every machine here carries a manufacturer's own
-- model listing and, in all but one case, a project date from that manufacturer's design
-- records: it is a catalogued commercial design that was cancelled, which is
-- `unreleased`. IPDB does not use our vocabulary, so this mapping is ours -- hence the
-- patch's `flipcommons-catalog` attribution and the note each entry carries.
--
-- The catalog corroborates the mapping from the other side: 47 of the machines the pages
-- call `Never Produced` were already marked `unreleased` by hand, years ago, from IPDB's
-- prose, with nobody having read a `Production:` row. Not one was marked anything else.
INSTALL sqlite;
ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- == 1 · ANALYSIS ===========================================================

-- One row per cached IPDB machine page, with the dump's production number beside the
-- page's production status. The join is the point: the PAIR decides whether the page may
-- speak, and either column alone cannot.
--
-- `sample_size = -1` is not optional. The rarest labels on these pages sit on a handful
-- of models, and a sampled read types a real struct as NULL and drops it silently.
CREATE OR REPLACE VIEW _np_pages AS
SELECT
  a.ipdb_id                          AS ipdb_id,
  a.name                             AS page_name,
  a.source_url                       AS source_url,
  a.archive_capture_date             AS capture_date,
  a.production.text                  AS production_text,
  a.production.status                AS production_status,
  a.production.units                 AS production_units,
  a.production.never_produced        AS never_produced,
  x.ProductionNumber                 AS dump_production_number
FROM read_json_auto(
       '../pinexplore/ingest_sources/ipdb_archive/models.jsonl', sample_size = -1) AS a
LEFT JOIN px.ipdb_machines AS x ON x.IpdbId = a.ipdb_id;

-- Every live model whose cached page states `Never Produced`.
CREATE OR REPLACE VIEW np_candidates AS
SELECT
  m.id,
  m.slug,
  m.name,
  m.manufacturer_name,
  m.production_status_slug,
  m.production_quantity,
  m.production_year,
  m.project_year,
  p.*
FROM models AS m
JOIN _np_pages AS p ON p.ipdb_id = m.ipdb_id
WHERE p.never_produced;

-- The emitted set. One row per model, asserting `production_status: unreleased`, cited to
-- the machine listing with its own `Production:` row as the verbatim quote.
--
-- The quote is assembled from the page's parsed field text under the label the `ipdb:`
-- resolver renders it beneath, which is what makes it verbatim by construction: the
-- resolver emits `<label>: <field text>` for exactly these page-only labels, and
-- `quote_not_resolver_shape` below asserts the two stay in step.
CREATE OR REPLACE VIEW np_patch_rows AS
SELECT
  c.id,
  c.slug,
  c.name,
  c.manufacturer_name,
  c.ipdb_id,
  'ipdb:' || c.ipdb_id::VARCHAR       AS cite_ref,
  'Production: ' || c.production_text AS quote,
  'unreleased'                        AS production_status,
  c.project_year,
  c.capture_date
FROM np_candidates AS c
WHERE c.dump_production_number IS NULL
  AND c.production_status_slug IS NULL
  AND c.production_quantity IS NULL
  AND c.production_year IS NULL;

-- Held back, and why. One reason per row, most serious first.
--
-- `dump_holds_a_production_number` is the branch that enforces the whole safety argument
-- above: a 2018 page may never contradict the 2025 dump. It is empty today — no page in
-- the corpus states a status for a machine the dump gives a quantity — and it exists so
-- that the day one does, the row is refused rather than emitted.
--
-- `catalog_already_unreleased` is the corroboration set: 47 machines somebody had already
-- read correctly out of IPDB's prose. Re-asserting a value a record already holds changes
-- nothing, and the apply engine rejects a provenance-carrying unit that changes nothing.
CREATE OR REPLACE VIEW np_rejected AS
SELECT
  c.id,
  c.slug,
  c.manufacturer_name,
  c.ipdb_id,
  c.production_status_slug,
  c.production_quantity,
  c.dump_production_number,
  CASE
    WHEN c.dump_production_number IS NOT NULL THEN 'dump_holds_a_production_number'
    WHEN c.production_quantity IS NOT NULL
      OR c.production_year IS NOT NULL      THEN 'catalog_holds_production_data'
    WHEN c.production_status_slug = 'unreleased' THEN 'catalog_already_unreleased'
    ELSE 'catalog_holds_another_status'
  END AS reason
FROM np_candidates AS c
WHERE c.dump_production_number IS NOT NULL
   OR c.production_status_slug IS NOT NULL
   OR c.production_quantity IS NOT NULL
   OR c.production_year IS NOT NULL;

-- == 2 · SUMMARY & CHECKS ===================================================

CREATE OR REPLACE VIEW np_summary AS
            SELECT 'models_live' AS metric, (SELECT count(*) FROM models) AS value
  UNION ALL SELECT 'models_with_production_status',
    (SELECT count(*) FROM models WHERE production_status_slug IS NOT NULL)
  UNION ALL SELECT 'models_unreleased',
    (SELECT count(*) FROM models WHERE production_status_slug = 'unreleased')
  UNION ALL SELECT 'pages_cached',        (SELECT count(*) FROM _np_pages)
  UNION ALL SELECT 'pages_never_produced',
    (SELECT count(*) FROM _np_pages WHERE never_produced)
  UNION ALL SELECT 'pages_with_a_quantity',
    (SELECT count(*) FROM _np_pages WHERE production_units IS NOT NULL)
  UNION ALL SELECT 'candidates',          (SELECT count(*) FROM np_candidates)
  UNION ALL SELECT 'patch_rows',          (SELECT count(*) FROM np_patch_rows)
  UNION ALL SELECT 'patch_rows_with_project_year',
    (SELECT count(project_year) FROM np_patch_rows)
  UNION ALL SELECT 'rejected',            (SELECT count(*) FROM np_rejected)
  UNION ALL SELECT 'rejected_already_unreleased',
    (SELECT count(*) FROM np_rejected WHERE reason = 'catalog_already_unreleased')
  ORDER BY metric;

-- Empty when healthy.
CREATE OR REPLACE VIEW np_checks AS
  -- SAFETY, and the campaign's whole premise: a page may only speak where the dump is
  -- silent. An emitted row whose dump record states a quantity would be a 2018 capture
  -- overwriting a 2025 fact — the one thing this analysis exists to prevent.
  SELECT 'row_contradicts_the_dump' AS check_name, r.id, r.slug AS detail
  FROM np_patch_rows r JOIN np_candidates c ON c.id = r.id
  WHERE c.dump_production_number IS NOT NULL
  UNION ALL
  -- Safety, restated over the whole corpus rather than the emitted set: the two sources
  -- must not disagree about production ANYWHERE, or the "no newer value to lose" argument
  -- above is false and the rejection branch is papering over a real conflict.
  SELECT 'corpus_status_conflicts_with_dump', NULL::BIGINT,
         p.ipdb_id::VARCHAR || ' page says ' || p.production_text
           || ', dump says ' || p.dump_production_number::VARCHAR
  FROM _np_pages p
  WHERE p.production_status IS NOT NULL AND p.dump_production_number IS NOT NULL
  UNION ALL
  SELECT 'corpus_quantity_disagrees_with_dump', NULL::BIGINT,
         p.ipdb_id::VARCHAR || ' page says ' || p.production_units::VARCHAR
           || ', dump says ' || p.dump_production_number::VARCHAR
  FROM _np_pages p
  WHERE p.production_units IS NOT NULL
    AND p.dump_production_number IS NOT NULL
    AND p.production_units <> p.dump_production_number
  UNION ALL
  -- Correctness: this campaign only FILLS an unknown. A row targeting a model that
  -- already carries a status would compete with an existing catalog claim, and one
  -- targeting a model with production data would contradict it outright.
  SELECT 'row_targets_model_with_status', r.id, r.slug
  FROM np_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.production_status_slug IS NOT NULL
  UNION ALL
  SELECT 'row_targets_produced_model', r.id, r.slug
  FROM np_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.production_quantity IS NOT NULL OR m.production_year IS NOT NULL
  UNION ALL
  -- Structural: emitted + rejected must partition the candidates, so a row can never be
  -- silently dropped between detection and emission.
  SELECT 'scored_partition_broken', NULL::BIGINT, 'emitted + rejected != candidates'
  WHERE (SELECT count(*) FROM np_candidates)
     <> (SELECT count(*) FROM np_patch_rows) + (SELECT count(*) FROM np_rejected)
  UNION ALL
  -- Structural: one row per model — gen.py writes one entry per row, and a duplicated
  -- ref collides at apply.
  SELECT 'row_duplicated', r.id, r.slug FROM np_patch_rows r
  GROUP BY r.id, r.slug HAVING count(*) > 1
  UNION ALL
  -- Vocabulary: `unreleased` must still be a production status the catalog knows.
  SELECT 'status_not_in_vocabulary', NULL::BIGINT, 'unreleased'
  WHERE NOT EXISTS (SELECT 1 FROM production_statuses WHERE slug = 'unreleased')
  UNION ALL
  -- Evidence: the quote must be the label-and-value pair flippatch's `ipdb:` resolver
  -- renders for a page-only field. Assemble it any other way and it stops being verbatim
  -- against the document the gate matches, without anything else here noticing.
  SELECT 'quote_not_resolver_shape', r.id, r.quote
  FROM np_patch_rows r JOIN np_candidates c ON c.id = r.id
  WHERE r.quote IS DISTINCT FROM 'Production: ' || c.production_text
  UNION ALL
  -- Evidence: the quote must survive `patchkit.clean_quote` unchanged — that helper
  -- straightens smart quotes and rewrites an ellipsis, either of which would break
  -- verbatim matching. Plain printable ASCII is the sufficient condition.
  SELECT 'quote_not_plain_ascii', r.id, r.quote
  FROM np_patch_rows r WHERE length(r.quote) <> strlen(r.quote)
  UNION ALL
  -- Tripwire: the extract is keyed by the id in the page's own address. A row whose
  -- `source_url` does not restate its `ipdb_id` means the JSONL was mis-keyed, and the
  -- cite would then address a different machine than the quote came from.
  SELECT 'page_id_disagrees_with_url', NULL::BIGINT,
         p.ipdb_id::VARCHAR || ' -> ' || p.source_url
  FROM _np_pages p
  WHERE p.source_url IS DISTINCT FROM
        'https://www.ipdb.org/machine.cgi?id=' || p.ipdb_id::VARCHAR
  UNION ALL
  -- Anchors. These probe the EXTRACT and the JOIN, not `np_patch_rows`: the emitted set
  -- legitimately drains to zero the moment this patch applies — every model it targeted
  -- now carries a status and moves to `catalog_already_unreleased` — so anchoring on it
  -- could not tell "the campaign finished" from "the parse rotted".
  SELECT 'anchor_never_produced_dark', NULL::BIGINT,
         'ipdb 3711 no longer reads Never Produced onto ice-castle'
  WHERE NOT EXISTS (
    SELECT 1 FROM _np_pages p JOIN models m ON m.ipdb_id = p.ipdb_id
    WHERE p.ipdb_id = 3711 AND m.slug = 'ice-castle'
      AND p.never_produced AND p.production_text = 'Never Produced'
      AND p.dump_production_number IS NULL)
  UNION ALL
  -- Anchor, the other direction: a page stating a QUANTITY must still read as one. Without
  -- it the parse could go one-sided — every page reading as never produced — and every
  -- row-level invariant above would still pass.
  SELECT 'anchor_quantity_dark', NULL::BIGINT,
         'ipdb 2049 (San Francisco) no longer reads as 2,000 units produced'
  WHERE NOT EXISTS (
    SELECT 1 FROM _np_pages p
    WHERE p.ipdb_id = 2049 AND NOT p.never_produced AND p.production_units = 2000)
  UNION ALL
  -- Drift: the corpus is what the cache holds. A collapse to near-nothing is a moved
  -- artifact or a failed extract, which no row-level invariant above can see.
  SELECT 'page_corpus_collapsed', NULL::BIGINT,
         'only ' || (SELECT count(*) FROM _np_pages) || ' cached pages extracted'
  WHERE (SELECT count(*) FROM _np_pages) < 250;
