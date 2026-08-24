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

-- The cross-source headline. The per-rule breakdown is
-- `external_data_source_findings_summary` in `bridge.sql`; per-source totals and
-- coverage sit in each source's own `<source>_summary`.
--
-- Completes the runner's summary+checks contract for PREFIX=external_data_sources
-- (`bridge.sql` carries the checks and context under the same prefix).
CREATE OR REPLACE VIEW external_data_sources_summary AS
  SELECT * FROM (
              SELECT source, severity, count(*) AS n
              FROM external_data_source_findings
              GROUP BY ALL
    UNION ALL SELECT source, 'dismissed', count(*)
              FROM external_data_source_findings_all
              WHERE dismissed
              GROUP BY source
  )
  ORDER BY source, CASE severity WHEN 'error' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END;
COMMENT ON VIEW external_data_sources_summary IS
  'The layer''s headline — findings per (source, severity), errors first, plus dismissed tallies. The per-rule breakdown is external_data_source_findings_summary.';
