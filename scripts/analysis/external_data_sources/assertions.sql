-- ASSERTIONS: what the sources claim the catalog's models ARE, landed on the records.
--
-- `.read` this from a campaign analysis after flipcommons' foundation (the per-source
-- files read it themselves, so a campaign normally reaches for `ipdb.sql` or
-- `opdb.sql` rather than this):
--
--     .read ../flippatch/scripts/analysis/external_data_sources/assertions.sql
--
-- It reads `identity.sql` itself (for the model links its landing joins on), which
-- reads `bridge.sql`, so the whole chain comes with it.
--
-- ONE SHAPE FOR BOTH SOURCES. IPDB's Specialty field and OPDB's classification
-- signals (tags, reward types, gameplay features, cabinet, series, relationship
-- edges) are the same kind of claim -- THIS machine carries THAT classification --
-- and both are answered with the same two questions: does the target vocabulary
-- EXIST in the catalog, and does the model CARRY it. The resolution lookup and the
-- carriage CASE live here exactly once; each source contributes its assertions in
-- its own wording, and keeps what is its alone (IPDB's archive provenance and
-- specialty label; the per-source worklists, findings and policy checks stay in
-- `ipdb.sql` / `opdb.sql`).
--
-- The values arrive under the division of labour pinexplore's mapping docs set
-- (`OpdbMappings.md`, the specialties reference): small closed vocabularies arrive
-- pre-translated to catalog slugs, alias-bearing ones in the source's own wording for
-- this side to resolve -- matching a source's phrasing to our slug is what the
-- catalog's aliases are FOR, and whether a value resolves is a question only the
-- catalog answers.

.read ../flippatch/scripts/analysis/external_data_sources/identity.sql

-- One row per (source listing, asserted value), landed on the catalog model and
-- answered twice over: does the target vocabulary EXIST, and does the model CARRY it.
--
-- `assertion_label` is the source's own name for the claim where it has one (IPDB's
-- specialty heading); NULL where the entity type is the whole label (OPDB). It is
-- part of the grain: one IPDB machine can carry two specialties aimed at one target.
--
-- `target_exists` is asked of every row except the `model-relationship` ones, whose
-- targets (`conversion`, `conversion_kit`, `retheme`) name a relationship type rather
-- than a record -- neither resolvable nor missing vocabulary, so they resolve
-- structurally.
--
-- CARRIAGE IS `IS NOT DISTINCT FROM` ON THE SINGLE-VALUED DIMS, not `=`. A model
-- with no game format at all yields NULL from `=`, and NULL is neither carried nor a
-- gap -- it silently drops out of both, which is precisely backwards: a model whose
-- game format is unset is the MOST actionable row a source's assertion produces.
-- That mistake cost 27 findings when this was first counted.
--
-- CARRIAGE IS ASKED OF `target_slug`, NOT of the source's wording. The catalog
-- stores slugs on these join rows, so comparing the source's phrasing to them would
-- answer false for every alias-resolved target -- reporting a model as missing a
-- feature it demonstrably carries.
CREATE OR REPLACE VIEW _eds_external_assertions AS
  SELECT
    r.*,
    CASE WHEN r.target_entity_type = 'model-relationship' THEN true
         ELSE r.target_slug IS NOT NULL END AS target_exists,
    -- One CASE for every entity type either source asserts; a source that never
    -- asserts a type simply never reaches that branch (IPDB has no series, OPDB no
    -- game format).
    CASE r.target_entity_type
      WHEN 'tag'              THEN EXISTS (SELECT 1 FROM model_tags AS tg
                                     WHERE tg.model_id = r.model_id AND tg.tag_slug = r.target_slug)
      WHEN 'reward-type'      THEN EXISTS (SELECT 1 FROM model_rewards AS rw
                                     WHERE rw.model_id = r.model_id AND rw.reward_type_slug = r.target_slug)
      WHEN 'gameplay-feature' THEN EXISTS (SELECT 1 FROM model_gameplay_features AS g
                                     WHERE g.model_id = r.model_id AND g.feature_slug = r.target_slug)
      -- `target_slug IS NOT NULL` GUARDS THE SINGLE-VALUED DIMS, and only them.
      -- Vocabulary that does not resolve cannot be carried, and `IS NOT DISTINCT
      -- FROM` says the opposite when both sides are NULL -- every model with no game
      -- format at all would read as carrying `Not A Pinball`. The EXISTS branches
      -- need no guard: they compare inside a join and yield false against NULL.
      WHEN 'game-format'      THEN r.target_slug IS NOT NULL
                                     AND m_game_format_slug IS NOT DISTINCT FROM r.target_slug
      WHEN 'cabinet'          THEN r.target_slug IS NOT NULL
                                     AND m_cabinet_slug     IS NOT DISTINCT FROM r.target_slug
      -- Series hangs off the TITLE in the catalog (`OpdbMappings.md` leaves the
      -- source view at model grain for exactly this reason), so carriage is asked of
      -- the model's title.
      WHEN 'series'           THEN r.target_slug IS NOT NULL
                                     AND m_series_slug IS NOT DISTINCT FROM r.target_slug
      -- Structural, so it reads the raw value: a relationship type is not a record
      -- and never resolves through `target_slug`. `model_edges` is outbound-only,
      -- which suits every relationship assertion: the source is saying THIS machine
      -- is a conversion, a kit, or a retheme of something else.
      WHEN 'model-relationship' THEN EXISTS (SELECT 1 FROM model_edges AS e
                                     WHERE e.model_id = r.model_id
                                       AND e.relationship_type = r.target_value)
      -- No ELSE: a target_entity_type nobody wrote a branch for lands NULL, which
      -- `assertion_carriage_unhandled` fails on. An ELSE false would report every
      -- such row as a gap instead -- a wrong answer rather than a loud one.
    END AS carried
  FROM (
    SELECT
      s.*,
      m.id   AS model_id,
      m.slug AS model_slug,
      m.name AS model_name,
      m.game_format_slug AS m_game_format_slug,
      m.cabinet_slug     AS m_cabinet_slug,
      t.series_slug      AS m_series_slug,
      -- THE CATALOG RECORD THE SOURCE'S WORDING DENOTES, or NULL if none does.
      -- Three ways in, most specific first, so an exact public_id can never lose to
      -- someone else's alias. LIMIT 1 with that ORDER BY makes the answer
      -- deterministic rather than whichever row the scan reached first. Within a
      -- tier, plural answers are refused upstream: `assertion_target_ambiguous`
      -- fails the run on any value that is plural at its winning tier, so the
      -- collision gets adjudicated -- an alias retired, a value re-aimed -- instead
      -- of auto-picked.
      (SELECT es.subject_public_id
       FROM entity_subjects AS es
       WHERE es.subject_type = s.target_entity_type
         AND is_live(es.subject_status)
         AND (es.subject_public_id = s.target_value
              OR lower(es.subject_name) = lower(s.target_value)
              OR EXISTS (SELECT 1 FROM entity_aliases AS ea
                         WHERE ea.entity_type = es.subject_type
                           AND ea.entity_id = es.subject_id
                           AND lower(ea.alias) = lower(s.target_value)))
       ORDER BY CASE WHEN es.subject_public_id = s.target_value THEN 0
                     WHEN lower(es.subject_name) = lower(s.target_value) THEN 1
                     ELSE 2 END,
                es.subject_public_id
       LIMIT 1) AS target_slug
    FROM (
      -- Each source's assertions, in the unified shape. IPDB's specialty label and
      -- census provenance ride along; OPDB's per-entity mart views union in with
      -- the entity type as the whole label.
                SELECT 'ipdb' AS source, ipdb_id::VARCHAR AS external_id,
                       specialty AS assertion_label, target_entity_type, target_value,
                       source_url, observed_on
                FROM px.ipdb.model_specialties
      UNION ALL SELECT 'opdb', opdb_id, NULL, 'tag',                tag,               NULL, NULL FROM px.opdb.model_tags
      UNION ALL SELECT 'opdb', opdb_id, NULL, 'reward-type',        reward_type,       NULL, NULL FROM px.opdb.model_reward_types
      UNION ALL SELECT 'opdb', opdb_id, NULL, 'gameplay-feature',   gameplay_feature,  NULL, NULL FROM px.opdb.model_gameplay_features
      UNION ALL SELECT 'opdb', opdb_id, NULL, 'series',             series,            NULL, NULL FROM px.opdb.model_series
      UNION ALL SELECT 'opdb', opdb_id, NULL, 'model-relationship', relationship_type, NULL, NULL FROM px.opdb.model_relationships
      UNION ALL SELECT 'opdb', opdb_id, NULL, 'cabinet',            cabinet,           NULL, NULL FROM px.opdb.models WHERE cabinet IS NOT NULL
    ) AS s
    -- Landed through the one links relation, so both sources use the same join and a
    -- listing the catalog does not link lands with model_slug NULL -- excluded from
    -- the worklists (already reported under the model rules) but counted in the
    -- summaries' named remainders.
    LEFT JOIN _eds_model_links AS ml
      ON ml.source = s.source AND ml.external_id = s.external_id
    LEFT JOIN models AS m ON m.slug = ml.slug
    LEFT JOIN titles AS t ON t.id = m.title_id
  ) AS r;

-- ═══ SUMMARY & CHECKS ══════════════════════════════════════════════════════

-- The assertion layer's own headline, for a session editing this file
-- (`PREFIX=assertions`). The per-source summaries carry the public partition counts.
CREATE OR REPLACE VIEW assertions_summary AS
  SELECT * FROM (
              SELECT source || '_assertions' AS metric, count(*) AS value
              FROM _eds_external_assertions GROUP BY source
    UNION ALL SELECT source || '_assertions_carried', count(*) FILTER (WHERE carried)
              FROM _eds_external_assertions GROUP BY source
    UNION ALL SELECT source || '_assertion_values', count(DISTINCT target_entity_type || '/' || target_value)
              FROM _eds_external_assertions GROUP BY source
  ) ORDER BY metric;
COMMENT ON VIEW assertions_summary IS
  'The assertion layer''s own headline — assertions, carried assertions and distinct asserted values per source. The public partition counts live in the per-source summaries.';

-- Empty when healthy. Invariants of the assertion machinery, never findings about
-- the data.
CREATE OR REPLACE VIEW assertions_checks AS
  -- The carriage CASE has no ELSE, so a target_entity_type nobody wrote a branch for
  -- lands NULL rather than being silently reported as a gap. This is what turns that
  -- into a loud failure. It fires the day a source maps an assertion onto an entity
  -- type this file has never seen.
  SELECT 'assertion_carriage_unhandled' AS check_name,
         source || ' -> ' || target_entity_type AS detail
  FROM _eds_external_assertions
  WHERE model_slug IS NOT NULL AND carried IS NULL
  GROUP BY ALL

  UNION ALL
  -- One row per (source, listing, label, value); the landing join is a lookup and
  -- must not fan the relation out.
  SELECT 'assertions_not_one_row_per_assertion',
         source || ' / ' || external_id || ' / ' || coalesce(assertion_label, '-')
           || ' / ' || target_entity_type || ' / ' || target_value
  FROM _eds_external_assertions
  GROUP BY source, external_id, assertion_label, target_entity_type, target_value
  HAVING count(*) > 1

  UNION ALL
  -- The anchor for the whole layer, per source: a source publishing NO assertions at
  -- all reads exactly like a catalog that already carries everything.
  SELECT 'source_assertions_missing', s.source
  FROM (VALUES ('ipdb'), ('opdb')) AS s(source)
  WHERE NOT EXISTS (SELECT 1 FROM _eds_external_assertions AS a WHERE a.source = s.source)

  UNION ALL
  -- The target lookup resolves with LIMIT 1 at its best tier (exact public_id, then
  -- name, then alias). Across tiers that ordering is the point; two records answering
  -- at the SAME tier would resolve alphabetically and silently -- the "ignore
  -- multiple matches" bug in miniature. This mirrors the lookup's match conditions
  -- (keep the two in step) and fails on any asserted value that is plural at its
  -- winning tier, so the collision gets adjudicated -- an alias retired, a value
  -- re-aimed -- instead of auto-picked. Checked over every value either source
  -- asserts, plus IPDB's full specialty RULE table so a mapping with no current
  -- assignment is validated too.
  SELECT 'assertion_target_ambiguous', v.target_entity_type || ' -> ' || v.target_value
  FROM (SELECT DISTINCT target_entity_type, target_value FROM _eds_external_assertions
        WHERE target_entity_type <> 'model-relationship'
        UNION
        SELECT target_entity_type, target_value FROM px.ipdb.specialties
        WHERE target_entity_type <> 'model-relationship') AS v
  WHERE (
    WITH matches AS (
      SELECT CASE WHEN es.subject_public_id = v.target_value THEN 0
                  WHEN lower(es.subject_name) = lower(v.target_value) THEN 1
                  ELSE 2 END AS tier
      FROM entity_subjects AS es
      WHERE es.subject_type = v.target_entity_type
        AND is_live(es.subject_status)
        AND (es.subject_public_id = v.target_value
             OR lower(es.subject_name) = lower(v.target_value)
             OR EXISTS (SELECT 1 FROM entity_aliases AS ea
                        WHERE ea.entity_type = es.subject_type
                          AND ea.entity_id = es.subject_id
                          AND lower(ea.alias) = lower(v.target_value)))
    )
    SELECT count(*) FROM matches WHERE tier = (SELECT min(tier) FROM matches)
  ) > 1;
COMMENT ON VIEW assertions_checks IS
  'Empty when healthy — every asserted entity type has a carriage branch, one row per assertion, both sources actually asserting, and no asserted value plural at its winning lookup tier. Invariants of the assertion machinery, never findings about the data.';
