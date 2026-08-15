-- Description candidates for the 0239 descriptions campaign.
--
-- The campaign writes descriptions only for records that have none; it never replaces one.
--
--     F=campaigns/0239-descriptions/candidates.sql
--     make analyze FILE=$F PREFIX=desc                          # summary, gated on checks
--     make analyze FILE=$F Q="FROM desc_candidates;"            # the worklist
--     make analyze FILE=$F Q="FROM desc_coverage;"              # gap per type

.read scripts/analysis/catalog.sql

CREATE OR REPLACE VIEW _desc_scope AS
  SELECT unnest([
    'cabinet', 'display-type', 'display-subtype', 'game-format',
    'production-status', 'reward-type', 'tag', 'technology-generation',
    'technology-subgeneration', 'gameplay-feature', 'system', 'manufacturer'
  ]) AS entity_type;

-- The shape every in-scope vocabulary shares. Types carrying more than this —
-- a usage count, a producing filter — are spelled out in _desc_population.
CREATE OR REPLACE MACRO desc_arm(tbl, etype) AS TABLE
  SELECT etype AS entity_type, slug, name, description FROM query_table(tbl);

-- UNION ALL BY NAME: arms align on column name, so `n` simply arrives NULL from
-- the arms that have no usage count, and reordering a SELECT cannot silently
-- shift a value into the wrong column.
CREATE OR REPLACE VIEW _desc_population AS
       SELECT 'gameplay-feature' AS entity_type, slug, name, n, description FROM gameplay_features
  UNION ALL BY NAME SELECT 'tag' AS entity_type, slug, name, n, description FROM tags
  UNION ALL BY NAME SELECT 'reward-type' AS entity_type, slug, name, n, description FROM reward_types
  UNION ALL BY NAME SELECT 'manufacturer' AS entity_type, slug, name,
                           n_models AS n, description
                      FROM manufacturers WHERE presumed_producing
  UNION ALL BY NAME FROM desc_arm('systems', 'system')
  UNION ALL BY NAME FROM desc_arm('game_formats', 'game-format')
  UNION ALL BY NAME FROM desc_arm('cabinets', 'cabinet')
  UNION ALL BY NAME FROM desc_arm('display_types', 'display-type')
  UNION ALL BY NAME FROM desc_arm('display_subtypes', 'display-subtype')
  UNION ALL BY NAME FROM desc_arm('production_statuses', 'production-status')
  UNION ALL BY NAME FROM desc_arm('technology_generations', 'technology-generation')
  UNION ALL BY NAME FROM desc_arm('technology_subgenerations', 'technology-subgeneration');

CREATE OR REPLACE VIEW desc_candidates AS
  SELECT entity_type, slug, entity_type || '.' || slug AS patch_ref, name, n
    FROM _desc_population
   WHERE description IS NULL
   ORDER BY entity_type, n DESC NULLS LAST, slug;
COMMENT ON VIEW desc_candidates IS
  'One row per in-scope record with NO description — THE 0239 worklist. patch_ref is the patch entry key.';

CREATE OR REPLACE VIEW desc_coverage AS
  SELECT entity_type,
         count(*) AS n_records,
         count(description) AS n_described,
         count(*) - count(description) AS n_missing
    FROM _desc_population
   GROUP BY ALL
   ORDER BY n_missing DESC, entity_type;
COMMENT ON VIEW desc_coverage IS
  'One row per in-scope entity type — records, described, missing.';

CREATE OR REPLACE VIEW desc_summary AS
  SELECT count(*) AS candidates,
         count(DISTINCT entity_type) AS types_with_gaps,
         count(*) FILTER (WHERE entity_type = 'gameplay-feature') AS gameplay_features
    FROM desc_candidates;

CREATE OR REPLACE VIEW desc_checks AS
  -- Zero RECORDS for a scoped type is a renamed view. Zero CANDIDATES is the
  -- campaign finishing that type, and never fails.
  SELECT 'entity type resolves to no records' AS check_name, entity_type AS detail
    FROM _desc_scope ANTI JOIN _desc_population USING (entity_type);
