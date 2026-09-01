-- IPDB's `Table Top/Counter Game` specialty, landed on a single catalog cabinet.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, liveness
-- filtering, the NULL-spelling regularization) is FLIPCOMMONS' shared foundation;
-- the runner loads it under this file automatically, so nothing is `.read` here.
--
-- WHY THE COMPARISON LAYER IS NOT READ. The rows this campaign needs are PER
-- MODEL for a specialty whose target value does not resolve -- a shape the layer
-- deliberately does not publish (`ipdb_specialty_vocabulary_absent` aggregates to
-- one row per specialty, because one row is one decision). Its per-model grain
-- lives in `_eds_ipdb_specialties`, an internal view the baked shim does not
-- carry, and loading `ipdb.sql` alone to reach it leaves the layer's own registry
-- checks failing on the OPDB detail views it did not load. The layer's other
-- contribution -- matching a listing to a model -- is not needed either: every
-- model here already holds an `ipdb_id`, so the link is a join, not a match. So
-- this file attaches the census directly, as 0297 does.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so that this file's ATTACH
-- resolves. `make analyze` handles that:
--
--     F=campaigns/0307-counter-games/counter_games.sql
--     make analyze FILE=$F PREFIX=counter                    # summary, gated on checks
--     make analyze FILE=$F Q="FROM counter_patch_rows;"      # what gen.py emits for 0310
--     make analyze FILE=$F Q="FROM counter_pin_tables;"      # what gen.py emits for 0307
--     make analyze FILE=$F Q="FROM counter_checks;"          # the gates, one row per failure
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
--
-- == WHY ONE CABINET AND NOT TWO ============================================
--
-- pinexplore mapped this heading to the display string `Table Top/Counter Game`
-- rather than a slug, on the reading that it spans two of our cabinets --
-- `tabletop` and `countertop` -- and needs per-model research to split. Reading
-- the population says there is nothing to split.
--
-- EVERY member is a coin-operated counter game. 236 of the 320 matched models are
-- pre-1940 and 65 more carry no year; the 19 post-war members are a ball gum
-- vender, a game with an operator's coin-view window, an MOA trade show counter
-- game, and Williams' 100-unit 4-IN-1 operator run. Not one home or consumer
-- machine is in the set, which is the only thing `tabletop` describes that
-- `countertop` does not.
--
-- Nor is there evidence to split on. 245 of the 320 IPDB notes contain neither
-- the word "counter" nor the word "table", and the period vocabulary in the
-- remainder INVERTS the modern reading: a `pin table` in 1932 is the LEGGED
-- version, as IPDB itself spells out on `official-counter` -- "'Official Pin
-- Table' is often affixed to this counter version even though the term 'pin
-- table' refers to games that have legs". Twenty of the twenty-one members whose
-- notes say `pin table` use it to name a DIFFERENT, legged sibling model.
--
-- So the heading maps to `countertop`, and `tabletop` is retired.
--
--
-- == WHY THE TWO `tabletop` MODELS ARE NOT IN THIS POPULATION ===============
--
-- The catalog's only two `tabletop` models -- `betcha-ball-2` and `lucky-star-3`
-- -- do NOT carry this specialty. IPDB excluded them on purpose: both are the
-- legged siblings of counter games it does list (`betcha-ball`, `lucky-star`,
-- both `countertop`), and `lucky-star-3`'s note opens "This is a pin table."
-- They were labelled `tabletop` by reading "table" out of "pin table".
--
-- That is why `counter_pin_tables` is a literal two-row relation rather than
-- something derived: it is a reading of two sources, and the check below asserts
-- the premise -- that IPDB keeps them out of the specialty -- rather than
-- assuming it.

ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- One row per live catalog model IPDB marks `Table Top/Counter Game`, with what
-- the catalog currently records for its cabinet.
CREATE OR REPLACE VIEW counter_population AS
  SELECT
    s.ipdb_id,
    m.id           AS model_id,
    m.slug,
    m.name,
    m.year,
    m.manufacturer_name,
    m.cabinet_slug AS current_cabinet
  FROM px.ipdb.model_specialties AS s
  JOIN models AS m ON m.ipdb_id = s.ipdb_id
  WHERE s.specialty = 'Table Top/Counter Game';
COMMENT ON VIEW counter_population IS
  'Every live model IPDB marks Table Top/Counter Game, with the cabinet the catalog holds today.';

-- WHAT 0310 EMITS -- one `cabinet: countertop` assertion per model with an empty
-- slot, cited to its own listing's Specialty row.
--
-- The quote names ONE specialty and leans on the `[...]` ellipsis to absorb
-- whatever precedes it, which is what `scripts/quotes/sources.py` prescribes: the
-- census records WHICH specialties a machine carries, not the order the page
-- prints them, so a quote asserting two are adjacent would be asserting something
-- the store cannot back.
CREATE OR REPLACE VIEW counter_patch_rows AS
  SELECT
    ipdb_id,
    slug,
    name,
    year,
    'countertop'                             AS cabinet,
    'ipdb:' || ipdb_id                       AS cite_ref,
    'Specialty: [...] Table Top/Counter Game' AS quote
  FROM counter_population
  WHERE current_cabinet IS NULL;
COMMENT ON VIEW counter_patch_rows IS
  'What 0310 emits — one countertop assertion per Table Top/Counter Game model with no cabinet yet.';

-- WHAT 0307 EMITS -- the two models mislabelled `tabletop`, corrected to `floor`.
--
-- Literal because it is a reading of two sources, not a rule. Each quote is
-- verbatim in its listing (`make show-source ARGS="ipdb:6606 --check '...'"`).
CREATE OR REPLACE VIEW counter_pin_tables AS
  SELECT * FROM (VALUES
    ('betcha-ball-2', 6925, 'floor',
     'Model RT is Radio Table only (on legs) Model GRT is combination Game on Radio Table (a pin table)'),
    ('lucky-star-3',  6606, 'floor',
     'This is a pin table.')
  ) AS t(slug, ipdb_id, cabinet, quote);
COMMENT ON VIEW counter_pin_tables IS
  'What 0307 emits — the two legged pin tables mislabelled tabletop, and the span of each listing that says so.';

CREATE OR REPLACE VIEW counter_checks AS
  -- The specialty must still be in the census. An empty population means the
  -- census moved under us, not that the work is done.
  SELECT 'specialty_absent_from_census' AS check_name,
         NULL::BIGINT AS id,
         'counter_population is empty' AS detail
  WHERE NOT EXISTS (SELECT 1 FROM counter_population)
  UNION ALL
  -- A member holding a cabinet we did not put there, and not the one IPDB's
  -- heading states, is a real disagreement with the source -- the one thing this
  -- campaign's blanket assertion is not entitled to paper over.
  SELECT 'member_holds_a_non_counter_cabinet', p.model_id,
         p.slug || ' cabinet=' || p.current_cabinet
  FROM counter_population AS p
  WHERE p.current_cabinet IS NOT NULL
    AND p.current_cabinet <> 'countertop'
  UNION ALL
  -- THE PREMISE OF 0307, ASSERTED. The two legged models are corrected to `floor`
  -- precisely because IPDB does not call them counter games. If the census ever
  -- lists one, that reading is wrong and the correction must be re-argued.
  SELECT 'pin_table_now_carries_the_specialty', p.model_id,
         p.slug || ' is in counter_population'
  FROM counter_population AS p
  WHERE p.slug IN (SELECT slug FROM counter_pin_tables)
  UNION ALL
  -- Drift guard on the literal relation: a slug that no longer names a live
  -- model, or an ipdb_id that no longer matches it, is a patch that will not
  -- resolve.
  SELECT 'pin_table_does_not_resolve', NULL::BIGINT, t.slug
  FROM counter_pin_tables AS t
  WHERE NOT EXISTS (
    SELECT 1 FROM models AS m WHERE m.slug = t.slug AND m.ipdb_id = t.ipdb_id)
  UNION ALL
  -- 0309 soft-deletes the `tabletop` cabinet, and the delete planner refuses
  -- while an active PROTECT referrer would dangle. Every referrer must be one
  -- 0307 reassigns.
  SELECT 'tabletop_referrer_unaccounted', m.id, m.slug
  FROM models AS m
  WHERE m.cabinet_slug = 'tabletop'
    AND m.slug NOT IN (SELECT slug FROM counter_pin_tables)
  UNION ALL
  -- Same guard for prose: a wikilink into a soft-deleted record is a broken link.
  -- 0308 clears the only one; anything else appearing here needs its own edit
  -- before the delete lands.
  SELECT 'tabletop_wikilink_unaccounted', r.source_id,
         r.source_entity_type || '.' || r.source_public_id
  FROM record_references AS r
  WHERE r.target_entity_type = 'cabinet'
    AND r.target_public_id = 'tabletop'
    AND NOT (r.source_entity_type = 'technology-generation'
             AND r.source_public_id = 'pure-mechanical');
COMMENT ON VIEW counter_checks IS
  'Gates for the counter-game campaign — one row per failure; empty is a pass.';

-- Summary, printed by `make analyze FILE=… PREFIX=counter`.
CREATE OR REPLACE VIEW counter_summary AS
  SELECT 'population'            AS metric, count(*) AS n FROM counter_population
  UNION ALL
  SELECT 'cabinet_already_set',  count(*) FROM counter_population WHERE current_cabinet IS NOT NULL
  UNION ALL
  SELECT 'emitted_countertop',   count(*) FROM counter_patch_rows
  UNION ALL
  SELECT 'pin_tables_corrected', count(*) FROM counter_pin_tables
  UNION ALL
  SELECT 'CHECK_FAILURES',       count(*) FROM counter_checks;
