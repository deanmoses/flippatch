-- The BAKE ENTRY for the external data source comparison layer. Executed only by the
-- analysis runner's layer bake (see ../external_data_sources.layer), never by a query
-- session: the runner runs this file with the foundation attached, materializes every
-- public view it creates into ../external_data_sources.duckdb, and regenerates the
-- pass-through shim that ../external_data_sources.sql reads. Campaigns keep reading
-- ../external_data_sources.sql; a session editing one source deeply can still `.read`
-- that source's file directly for live SQL (its prefix is the source name).
--
-- A new source is one `.read` below plus its own file under this directory.

-- `ipdb.sql` and `opdb.sql` each read `identity.sql` (the shared decode + matching
-- ladder + replay) so they stay individually loadable; under this bake that means the
-- identity file executes twice, which is deterministic and idempotent -- the second read
-- recreates the same relations from the same inputs -- and bake-time only.
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
    -- Already source-labelled: the replay measures each source's own ladder, so its
    -- metrics belong beside that source's, not under a fourth label of their own.
    UNION ALL SELECT source,           metric, value FROM known_good_replay_summary
  )
  ORDER BY source, metric;
COMMENT ON VIEW external_data_sources_summary IS
  'Every per-source summary metric, source-labelled: findings rollups, worklist and coverage counts, stale adjudications. An absent-listing count is bounded by dump age — read it beside the watermarks in external_data_sources_context.';
