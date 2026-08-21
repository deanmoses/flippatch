-- The external data sources bridge: pinexplore's dumps, beside the live catalog.
--
-- `.read` this (or a per-source file that reads it) from a campaign analysis AFTER
-- flipcommons' foundation, to compare what an external source says against what the
-- catalog holds. Every per-source file in this directory reads it first, so a campaign
-- normally reaches for `ipdb.sql` rather than this.
--
-- SCOPE — pinexplore's `explore.duckdb`, and only its published marts: the bare
-- `ipdb.*` / `opdb.*` schemas, each holding that source parsed, merged and validated
-- into our vocabulary. Everything under `*_raw`, `*_stg` and `*_ref` is pinexplore's own
-- working material, free to be reshaped without notice, and reading it is what
-- `external_data_sources_boundary_checks` below fails on. Source TEXT for citing a claim is a
-- different concern and lives in `../evidence.sql`, over the web-scrape cache.
--
-- FINDINGS ARE VIEWS, NEVER CHECKS. A comparison view returning rows is the normal,
-- healthy state -- that is the worklist a campaign is built to work down. The runner
-- fails nonzero on a row from ANY public `*_checks` view in the session, so a finding
-- placed in one would break every campaign that reads this layer. `*_checks` here holds
-- only this layer's own invariants: the attach resolved, a join preserved its grain, a
-- classification is exhaustive. Same line flipcommons' `audit.sql` draws between
-- `audit_findings` and `audit_checks`.
--
-- WHERE THE PATHS RESOLVE. Every path is relative to the FLIPCOMMONS checkout, because
-- that is where the analysis runner `cd`s before invoking DuckDB -- the same frame
-- `catalog.sql`'s own literal 'backend/db.analytics.duckdb' is in. `ATTACH` takes a
-- string LITERAL, so this cannot honour a `PINEXPLORE_DIR` override; the sibling layout
-- is assumed, as `evidence.sql` assumes it.
--
-- The alias is `px`, matching what campaigns 0268/0269/0277/0278 already attach, so this
-- layer and a campaign that attaches it directly cannot end up with two handles on one
-- file.

ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- The dump watermark, printed alongside `analysis_context` on every run.
--
-- One row per ingested artifact rather than one per source: IPDB alone arrives as two
-- Xantari snapshots that pinexplore merges, and "which snapshots went in" is the
-- question this answers. `observed_at` is the artifact's claim about its own currency --
-- for a Xantari snapshot, the `LastRefreshDateUtc` in its header -- and is NULL for an
-- export that carries no date, which is an honest absence rather than a missing value.
--
-- pinexplore assembles this itself in `ingest.watermarks`; this view is a pass-through
-- so that a campaign gets the watermark from the same place it gets everything else.
--
-- It exists because a campaign's two inputs move at unrelated rates: the catalog changes
-- with every patch, the dumps change when someone drops in a new scrape. A result that
-- moved because a newer snapshot landed is indistinguishable from a broken query until
-- this row says otherwise.
CREATE OR REPLACE VIEW external_data_sources_context AS
  SELECT source, artifact_kind, artifact, observed_at, n_records
  FROM px.ingest.watermarks;
COMMENT ON VIEW external_data_sources_context IS
  'One row per ingested external-source artifact — source, kind, which artifact, the date it claims for itself, and its record count. Printed by every analysis run that reads this layer.';

-- WHAT THIS LAYER READS FROM PINEXPLORE, AND WHETHER IT SHOULD.
--
-- pinexplore publishes a mart per external source. Everything under it -- the raw reads
-- of the dump files, the staging that parses and corrects them, the hand-curated
-- reference lists -- is that repo's own working material, free to be reshaped whenever
-- the pipeline is. Reaching past the mart into those layers couples a campaign to
-- internals nobody promised to keep still.
--
-- Now a GATE, not a report. It was a `_context` view while pinexplore had no mart and
-- every read below the line was unavoidable; the mart exists, this layer reads only it,
-- and so the `_checks` suffix makes the runner fail on a row instead of printing one.
-- That suffix is the whole difference between a warning and a gate.
--
-- It reads view definitions, so a relation named only in an ad-hoc `query` is invisible.
-- That understates, which is the safe direction.
CREATE OR REPLACE VIEW external_data_sources_boundary_checks AS
  WITH reads AS (
    SELECT
      v.view_name,
      t.relation
    FROM duckdb_views() AS v,
         unnest(regexp_extract_all(
           v.sql, 'px\.[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?')) AS t(relation)
    WHERE v.database_name = current_database()
      AND v.schema_name = 'main'
  )
  SELECT
    relation,
    -- An ALLOWLIST, not a denylist. Naming the internal layers meant the rule was only
    -- as complete as the list of ways to be internal -- `px.checks.violations` is not a
    -- mart and matched none of them. Naming the publishable schemas instead fails
    -- closed: a schema pinexplore adds is off-limits until someone decides otherwise,
    -- which is the right default for another repo's working material.
    CASE
      WHEN NOT regexp_matches(relation, '^px\.[A-Za-z_][A-Za-z0-9_]*\.')
        THEN 'unqualified -- names no schema, so no layer'
      WHEN NOT regexp_matches(relation, '^px\.(ipdb|opdb|fandom|glossary|ingest)\.')
        THEN 'not a published mart'
    END AS layer,
    list_sort(list(DISTINCT view_name)) AS read_by
  FROM reads
  GROUP BY ALL
  HAVING layer IS NOT NULL
  ORDER BY layer, relation;
COMMENT ON VIEW external_data_sources_boundary_checks IS
  'Empty when healthy — one row per pinexplore internal this layer reaches past the mart to read. A row means a campaign has coupled itself to another repo''s working material.';

-- Empty when healthy.
--
-- An unreachable pinexplore never reaches here: the ATTACH above fails first, loudly,
-- with the path in the message. What it cannot catch is a pinexplore whose build died
-- partway, leaving the file readable and the tables empty or absent -- which reads
-- downstream as "the dump agrees with the catalog perfectly" rather than as a fault.
CREATE OR REPLACE VIEW external_data_sources_checks AS
  SELECT 'dump_empty' AS check_name, 'px.ipdb.models has no rows' AS detail
  WHERE (SELECT count(*) FROM px.ipdb.models) = 0
  UNION ALL
  SELECT 'dump_empty', 'px.opdb.machines has no rows'
  WHERE (SELECT count(*) FROM px.opdb.machines) = 0;
COMMENT ON VIEW external_data_sources_checks IS
  'Empty when healthy — invariants of the bridge itself, not findings about the data. A row means the attached dump is unusable.';
