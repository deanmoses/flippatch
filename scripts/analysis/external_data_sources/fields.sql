-- Scalar fields against the testimony POOL — every source at once, never one witness
-- at a time.
--
-- Sources disagree with each other; Flipcommons is claims-based for exactly that
-- reason. A per-source field comparison manufactures seesaw work: 88 of IPDB's 106
-- production-year dissents have OPDB agreeing with the catalog, so "fixing" toward
-- IPDB recreates every row in the OPDB bucket. A dissent where another witness backs
-- us is a standoff already adjudicated, not a defect -- which is why there is no
-- ipdb_model_fields_disagreeing and no per-source field rule anywhere in this layer.
-- The design and its measurements: docs/plans/ExternalDataSourceFieldMerge.md.
--
-- Two public shapes over one merge:
--
--   model_fields_unsupported  THE WORKLIST. Some source has a value and none matches
--                             the catalog (a null catalog value matches nothing).
--   model_fields_contested    Sources split and at least one backs the catalog. Not
--                             work -- a standoff we already sided on -- but browsable.
--
-- `.read` from a campaign after flipcommons' foundation; reads `bridge.sql` itself.

.read ../flippatch/scripts/analysis/external_data_sources/bridge.sql

-- One row per (model, field) where at least one source states a value, catalog and
-- source values side by side as VARCHAR, with the shape derived.
--
-- The field routing is the layer's date discipline applied (see bridge.sql's
-- kind-qualification rule): catalog dates are `production_*` / `project_*`, never the
-- coalesced display columns; IPDB dates are the header parse routed by `date_kind`,
-- never the padded `date_of_manufacture`; and `ipdb_date_kind` rides along so a
-- `project_inferred` year is visibly resting on parse inference.
--
-- The shape CASE has no ELSE: a combination nobody derived lands NULL, which
-- `fields_checks` fails on -- loud rather than silently filed somewhere.
CREATE OR REPLACE VIEW _eds_field_merge AS
  WITH j AS (
    SELECT m.slug,
           m.production_year, m.production_month, m.project_year, m.project_month,
           m.player_count, m.technology_generation_slug, m.display_type_slug,
           m.production_quantity,
           nullif(trim(m.manufacturer_model_identifier), '') AS model_number,
           im.additional_details_date_year  AS i_date_year,
           im.additional_details_date_month AS i_date_month,
           im.additional_details_date_kind  AS i_date_kind,
           im.players AS i_players, im.technology_generation_slug AS i_tech,
           im.production_number AS i_production,
           nullif(trim(im.model_number), '') AS i_model_number,
           om.production_year AS o_production_year, om.production_month AS o_production_month,
           om.player_count AS o_players, om.technology_generation AS o_tech,
           om.display_type AS o_display
    FROM models AS m
    LEFT JOIN px.ipdb.models AS im ON im.ipdb_id = m.ipdb_id
    LEFT JOIN px.opdb.models AS om ON om.opdb_id = m.opdb_id
    WHERE im.ipdb_id IS NOT NULL OR om.opdb_id IS NOT NULL
  )
  SELECT *,
    CASE
      WHEN catalog_value IS NULL                 THEN 'backfill'
      WHEN supported AND sources_split           THEN 'contested'
      WHEN supported                             THEN 'supported'
      WHEN n_sources = 1                         THEN 'lone_witness'
      WHEN sources_split                         THEN 'scatter'
      WHEN n_sources >= 2 AND NOT sources_split  THEN 'outvoted'
    END AS shape
  FROM (
    SELECT slug, field, catalog_value, ipdb_value, opdb_value, ipdb_date_kind,
      (ipdb_value IS NOT NULL)::INT + (opdb_value IS NOT NULL)::INT AS n_sources,
      -- Null-safe by construction: a NULL catalog value equals nothing, so every
      -- backfill row reads unsupported, which is the worklist definition.
      (ipdb_value IS NOT NULL AND ipdb_value = catalog_value)
        OR (opdb_value IS NOT NULL AND opdb_value = catalog_value) AS supported,
      (ipdb_value IS NOT NULL AND opdb_value IS NOT NULL
        AND ipdb_value <> opdb_value) AS sources_split
    FROM (
      SELECT slug, 'production_year' AS field, production_year::VARCHAR AS catalog_value,
             CASE WHEN i_date_kind = 'manufacture' THEN i_date_year::VARCHAR END AS ipdb_value,
             o_production_year::VARCHAR AS opdb_value,
             CASE WHEN i_date_kind = 'manufacture' THEN i_date_kind END AS ipdb_date_kind
      FROM j
      UNION ALL
      SELECT slug, 'production_month', production_month::VARCHAR,
             CASE WHEN i_date_kind = 'manufacture' THEN i_date_month::VARCHAR END,
             o_production_month::VARCHAR,
             CASE WHEN i_date_kind = 'manufacture' THEN i_date_kind END
      FROM j
      UNION ALL
      SELECT slug, 'project_year', project_year::VARCHAR,
             CASE WHEN i_date_kind IN ('project', 'project_inferred') THEN i_date_year::VARCHAR END,
             NULL,  -- OPDB has no project concept
             CASE WHEN i_date_kind IN ('project', 'project_inferred') THEN i_date_kind END
      FROM j
      UNION ALL
      SELECT slug, 'project_month', project_month::VARCHAR,
             CASE WHEN i_date_kind IN ('project', 'project_inferred') THEN i_date_month::VARCHAR END,
             NULL,
             CASE WHEN i_date_kind IN ('project', 'project_inferred') THEN i_date_kind END
      FROM j
      UNION ALL
      SELECT slug, 'player_count', player_count::VARCHAR, i_players::VARCHAR, o_players::VARCHAR, NULL FROM j
      UNION ALL
      SELECT slug, 'technology_generation', technology_generation_slug, i_tech, o_tech, NULL FROM j
      UNION ALL
      SELECT slug, 'display_type', display_type_slug, NULL, o_display, NULL FROM j
      UNION ALL
      SELECT slug, 'production_quantity', production_quantity::VARCHAR, i_production::VARCHAR, NULL, NULL FROM j
      UNION ALL
      SELECT slug, 'model_number', model_number, i_model_number, NULL, NULL FROM j
    )
    WHERE ipdb_value IS NOT NULL OR opdb_value IS NOT NULL
  );

-- WORKLIST — the catalog value has NO external support while testimony exists.
--
-- `shape` says what a row would take: `backfill` (we hold nothing; both witnesses'
-- values are on the row, so a fill is never blind to a dissent), `outvoted` (the
-- sources agree against us -- the strongest signal, and the fix satisfies every
-- witness at once), `lone_witness` (one source speaks, unopposed and uncorroborated),
-- `scatter` (the sources disagree and none matches us; read the pages).
CREATE OR REPLACE VIEW model_fields_unsupported AS
  SELECT slug AS model_slug, field, catalog_value, ipdb_value, opdb_value,
         ipdb_date_kind, shape
  FROM _eds_field_merge
  WHERE shape IN ('backfill', 'outvoted', 'lone_witness', 'scatter');
COMMENT ON VIEW model_fields_unsupported IS
  'Worklist — one row per (model, field) where at least one external source states a value and none matches the catalog, every witness''s value on the row, shaped backfill / outvoted / lone_witness / scatter. Rows are expected.';

-- NOT A WORKLIST. The sources split and at least one backs the catalog -- a standoff
-- the catalog already adjudicated by siding with a witness, kept browsable because
-- seeing the dissent is useful and re-litigating it is not. No findings come from
-- here; `fields_summary` counts it so the detector is visibly alive.
CREATE OR REPLACE VIEW model_fields_contested AS
  SELECT slug AS model_slug, field, catalog_value, ipdb_value, opdb_value,
         ipdb_date_kind
  FROM _eds_field_merge
  WHERE shape = 'contested';
COMMENT ON VIEW model_fields_contested IS
  'Browse-only — one row per (model, field) where the sources disagree with each other and at least one backs the catalog. A standoff already sided with, never a finding.';

-- ═══ FINDINGS ══════════════════════════════════════════════════════════════
--
-- One rule: at 64 rows the sub-shapes do not earn separate dismissal grain, and the
-- shape is in the message. `source` is the literal 'cross' -- a merge finding has no
-- single witness -- which bridge.sql's findings table blesses.

DELETE FROM _external_data_source_findings WHERE source = 'cross';

INSERT INTO _external_data_source_findings BY NAME
SELECT
  'cross' AS source,
  'content' AS resolution_stage,
  'cross-field-unsupported' AS rule,   -- rules are source-prefixed; 'cross' is the source
  'warning' AS severity,
  NULL::VARCHAR AS external_id,   -- no single witness owns a merge finding
  'model' AS entity_type,
  model_slug AS entity_public_id,
  -- concat_ws drops NULL arguments, so each witness clause appears exactly when that
  -- source spoke; IPDB before OPDB, fixed, for message determinism.
  format('{}: {} is {} here ({}); {}',
         model_slug, field, coalesce(catalog_value, 'unset'), shape,
         concat_ws(', ',
           'IPDB says ' || ipdb_value ||
             CASE WHEN ipdb_date_kind = 'project_inferred' THEN ' (date inferred)' ELSE '' END,
           'OPDB says ' || opdb_value)) AS message,
  'model_fields_unsupported' AS detail_view
FROM model_fields_unsupported;

-- ═══ SUMMARY & CHECKS ══════════════════════════════════════════════════════

-- Per FIELD, all three states -- and `supported_<field>` is the one that cannot be
-- dropped: without it, a field with sparse testimony reads exactly like a field in
-- full external agreement. A field with NO testimony at all emits nothing here; that
-- is source data quality, pinexplore's to gate, and the scope note on `fields_checks`
-- says why this side deliberately does not. Shape-level counts are deliberately
-- absent; a shape at zero is a success, not a dark detector, and the worklist carries
-- the breakdown.
CREATE OR REPLACE VIEW fields_summary AS
  SELECT 'unsupported_' || field AS metric, count(*) AS value
  FROM model_fields_unsupported GROUP BY field
  UNION ALL SELECT 'contested_' || field, count(*)
  FROM model_fields_contested GROUP BY field
  UNION ALL SELECT 'supported_' || field, count(*)
  FROM _eds_field_merge WHERE shape = 'supported' GROUP BY field
  UNION ALL SELECT 'FINDINGS warnings', count(*)
    FROM external_data_source_findings WHERE source = 'cross'
  UNION ALL SELECT 'FINDINGS dismissed', count(*)
    FROM external_data_source_findings_all WHERE source = 'cross' AND dismissed
  ORDER BY metric;
COMMENT ON VIEW fields_summary IS
  'Headline counts for the field merge — unsupported, contested and supported rows per field, and the cross-source findings rollup. A field absent entirely has no testimony in the dumps; read the watermarks in external_data_sources_context beside it.';

-- Empty when healthy. Invariants of this layer, never findings about the data.
--
-- SCOPE — checks here guard THIS LAYER'S OWN LOGIC: the routing, the grain, and the
-- closed vocabularies at the pinexplore seam (`date_kind` is matched by literal string
-- here, so its drift breaks here). Source DATA QUALITY is pinexplore's job -- its
-- build gates its own parses on every rebuild -- and is deliberately not re-audited
-- from this side: a witness thinning out moves the per-field summary counts, which the
-- watermarks contextualize, and that is the intended visibility. The input-existence
-- anchor for this file is the bridge's `dump_empty`; there is deliberately no
-- per-field surveillance of the sources, and a check that a source still supplies
-- values belongs in pinexplore's build if anywhere.
CREATE OR REPLACE VIEW fields_checks AS
  -- The field roster is closed; a row outside it means a UNION branch was added
  -- without its consumers knowing.
  SELECT 'field_unknown' AS check_name, field AS detail
  FROM _eds_field_merge
  WHERE field NOT IN
    ('production_year', 'production_month', 'project_year', 'project_month',
     'player_count', 'technology_generation', 'display_type',
     'production_quantity', 'model_number')
  GROUP BY ALL

  UNION ALL
  -- The date routing matches `date_kind` values by literal string, so a kind pinexplore
  -- renames or adds would silently drop every row it labels -- the one failure a
  -- binder error cannot catch. This makes vocabulary drift loud instead.
  SELECT 'ipdb_date_kind_unknown', additional_details_date_kind
  FROM px.ipdb.models
  WHERE additional_details_date_kind IS NOT NULL
    AND additional_details_date_kind NOT IN ('manufacture', 'project', 'project_inferred')
  GROUP BY ALL

  UNION ALL
  -- The shape CASE has no ELSE; this is what makes an underived combination loud.
  SELECT 'shape_underived', slug || ' / ' || field
  FROM _eds_field_merge
  WHERE shape IS NULL

  UNION ALL
  -- One row per (model, field): the source joins are lookups on unique external ids
  -- (asserted per source) and must not fan the merge out.
  SELECT 'merge_not_one_row_per_model_field', slug || ' / ' || field
  FROM _eds_field_merge
  GROUP BY slug, field HAVING count(*) > 1;
COMMENT ON VIEW fields_checks IS
  'Empty when healthy — closed field roster, closed date-kind vocabulary at the pinexplore seam, every row''s shape derived, one row per (model, field). Guards this layer''s logic only; source data quality is pinexplore''s build.';
