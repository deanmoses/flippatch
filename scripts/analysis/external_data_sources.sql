-- A layer that compares the Flipcommons catalog against external data sources like IPDB and OPDB.
-- `.read` this from a campaign analysis after flipcommons' foundation:
--
--     .read ../flippatch/scripts/analysis/external_data_sources.sql
--
-- The external data source files below read `external_data_sources/bridge.sql` -- the
-- cross-source worklist, `external_data_source_findings`, the dismissals, and the layer's
-- own checks live there.
-- A new source is one `.read` below plus its own file under `external_data_sources/`.

.read ../flippatch/scripts/analysis/external_data_sources/ipdb.sql
.read ../flippatch/scripts/analysis/external_data_sources/opdb.sql
.read ../flippatch/scripts/analysis/external_data_sources/fields.sql

-- Every source's summary, source-labelled, in the one view the gated run prints. The
-- per-source summaries already carry their findings rollups, worklist and coverage
-- counts, and stale-adjudication tallies -- and counting per VIEW is what tells "no
-- findings" from "no detector", so printing them whole is the point. The per-rule
-- breakdown is `external_data_source_findings_summary` in `bridge.sql`.
--
-- Completes the runner's summary+checks contract for PREFIX=external_data_sources
-- (`bridge.sql` carries the checks and context under the same prefix).
CREATE OR REPLACE VIEW external_data_sources_summary AS
  SELECT * FROM (
              SELECT 'ipdb' AS source, metric, value FROM ipdb_summary
    UNION ALL SELECT 'opdb',           metric, value FROM opdb_summary
    UNION ALL SELECT 'cross',          metric, value FROM fields_summary
  )
  ORDER BY source, metric;
COMMENT ON VIEW external_data_sources_summary IS
  'Every per-source summary metric, source-labelled: findings rollups, worklist and coverage counts, stale adjudications. An absent-listing count is bounded by dump age — read it beside the watermarks in external_data_sources_context.';
