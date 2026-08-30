-- IPDB's `Specialty:` row, landed on the catalog's own classification vocabulary.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, liveness
-- filtering, the NULL-spelling regularization) is FLIPCOMMONS' shared foundation; the
-- runner loads it under this file automatically, so nothing is `.read` here.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so that this file's ATTACH resolves.
-- `make analyze` handles that and delegates to flipcommons' shared runner. Do not run
-- this file directly:
--
--     F=campaigns/0290-ipdb-specialties/specialties.sql
--     make analyze FILE=$F PREFIX=spec                 # summary, gated on checks
--     make analyze FILE=$F Q="FROM spec_patch_rows;"   # exactly what gen.py emits
--     make analyze FILE=$F Q="FROM spec_rejected;"     # what the gate held back, and why
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
--
-- == WHY THE CATALOG DOES NOT KNOW THESE CLASSIFICATIONS ====================
--
-- IPDB prints a `Specialty:` row naming what KIND of machine a listing is -- `Bingo
-- Machine`, `Widebody`, `Add-A-Ball`, `Flipperless`. Our IPDB baseline, the Xantari JSON
-- dump, HAS NO COLUMN FOR IT AT ALL: the row appears zero times in all 6,671 records. It
-- is the source of basic classification we have otherwise had to synthesize by reading
-- free-text notes.
--
-- The row is recoverable only from the machine page itself. Pinexplore's web cache holds
-- archive.org captures of IPDB machine pages and publishes the parsed rows as
-- `px.ipdb.model_specialties`, one row per (listing, specialty).
--
--
-- == WHY IT IS SAFE TO READ THIS ONE FIELD FROM A STALE PAGE ================
--
-- The captures run 2018 to 2026; the dump is April 2026. The dump is therefore the newer
-- source in the general case, and NOTHING here may overwrite it. IPDB has visibly moved
-- on since the older captures -- it has relabelled header dates between `Date Of
-- Manufacture` and `Project Date`, and added dates to listings that had none -- so a
-- page's DATE fields are actively untrustworthy and this analysis never reads one.
--
-- What makes Specialty different is the same property that made `Production` safe in
-- 0269: the dump has no column for it, so there is no newer value to lose. The page is
-- the only carrier there has ever been.
--
-- The same rule is enforced a second time, downstream, by the quote gate: flippatch's
-- `ipdb:` resolver renders a page-only label ONLY where the dump rendered no line under
-- it, and `Specialty` is on that short list beside `Production`.
--
--
-- == WHY A SINGLE-VALUED FIELD CAN TURN A GAP INTO A CONFLICT ===============
--
-- `game_format` and `cabinet` hold ONE value; `tag`, `reward_type` and `gameplay_feature`
-- hold many. That distinction decides what "the model does not carry this" means.
--
-- For a multi-valued field it means a gap, and asserting fills it. For a single-valued
-- field it can instead mean the slot is TAKEN, and asserting would overwrite a value the
-- catalog already holds. IPDB routinely prints two specialties that both want that one
-- slot -- `Bingo Machine One Ball Game`, `Horserace Game One Ball Game` -- so the source
-- itself cannot be replayed into the field without a human choosing between them.
--
-- This analysis therefore refuses every single-valued row whose slot is already filled
-- (`catalog_holds_a_conflicting_*` below). Those are not catalog defects: in every case
-- in the corpus the value the catalog holds is one IPDB also asserts on the same page.


INSTALL sqlite;
ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- == 1 · REFERENCE ==========================================================

-- HUMAN JUDGMENT, made checkable. IPDB does not use our vocabulary, so every mapping
-- below is ours -- which is what the patch's `flipcommons-catalog` attribution owns.
--
-- `field` is the catalog field a patch asserts and `value` the record it asserts; NULL
-- `field` DEFERS the specialty, with `deferred_because` saying why. A deferral is a
-- decision to emit nothing, not an oversight: `unmapped_specialty` in the checks fires
-- the day IPDB prints a heading this table has never seen, so the corpus cannot grow a
-- new classification silently.
--
-- `arity` is the catalog's, not IPDB's: `one` for the fields holding a single value.
--
-- The three deferrals share a shape -- IPDB's heading crosses our axes rather than
-- filling a gap in them, so no new term would resolve it and the models have to be read
-- one at a time. `Horserace Game` is deferred on the further question of whether it is a
-- kind of `one-ball` rather than a peer of it; IPDB asserts both on four of its five.
CREATE OR REPLACE TABLE _spec_map (
  specialty        VARCHAR,
  field            VARCHAR,
  value            VARCHAR,
  arity            VARCHAR,
  deferred_because VARCHAR
);
INSERT INTO _spec_map VALUES
  ('Bingo Machine',                       'game_format',      'bingo-pinball',                 'one',  NULL),
  ('One Ball Game',                       'game_format',      'one-ball',                      'one',  NULL),
  ('Bat Game',                            'game_format',      'pitch-and-bat',                 'one',  NULL),
  ('Bagatelle',                           'game_format',      'bagatelle',                     'one',  NULL),
  ('Rolldown Game',                       'game_format',      'rolldown',                      'one',  NULL),
  ('Cocktail Table',                      'cabinet',          'cocktail',                      'one',  NULL),
  ('Widebody',                            'tag',              'widebody',                      'many', NULL),
  ('Non-Commercial Machine [Home Model]', 'tag',              'home-use',                      'many', NULL),
  -- Vocabulary this patch introduces. `flipperless` is a new tag; the catalog has had
  -- `mechanical-backbox-animations` all along under 102 models and simply never knew
  -- IPDB's singular spelling of it, so that one is an alias rather than a new term.
  ('Flipperless',                         'tag',              'flipperless',                   'many', NULL),
  ('Mechanical Backbox Animation',        'gameplay_feature', 'mechanical-backbox-animations', 'many', NULL),
  ('Add-A-Ball',                          'reward_type',      'add-a-ball',                    'many', NULL),
  ('Novelty Play',                        'reward_type',      'novelty',                       'many', NULL),
  ('Head-to-Head Play',                   'gameplay_feature', 'head-to-head',                  'many', NULL),
  ('Zipper Flippers',                     'gameplay_feature', 'zipper-flippers',               'many', NULL),
  -- Deferred.
  ('Payout Machine',         NULL, NULL, NULL,
   'Spans cash-payout, merchant-paid and ticket-payout; which one needs the machine read.'),
  ('Table Top/Counter Game', NULL, NULL, NULL,
   'Spans the tabletop and countertop cabinets; which one needs the machine read.'),
  ('Not A Pinball',          NULL, NULL, NULL,
   'States what a machine is not; the format it IS has to come from somewhere else.'),
  ('Horserace Game',         NULL, NULL, NULL,
   'May be a kind of one-ball rather than a peer of it; IPDB asserts both on four of five.');

-- The one inference this patch draws beyond IPDB's own wording: a machine IPDB calls a
-- widebody has a wider-than-standard PINBALL cabinet and playfield, so the format follows
-- from the designation. It rides the same changeset as the tag because it rests on the
-- same words, and it is withheld wherever the model's single format slot is spoken for --
-- by the catalog, or by another specialty on the same page (Big Inning is a widebody
-- CABINET on a pitch-and-bat baseball game, not a pinball).
CREATE OR REPLACE VIEW _spec_widebody_implies AS SELECT 'pinball' AS game_format;

-- == 2 · ANALYSIS ===========================================================

-- One row per (live model, specialty IPDB prints for it), with the catalog's current
-- answer beside it. The join is on `ipdb_id`: these listings are already matched to
-- models, so the identity question the comparison layer's ladder exists to answer does
-- not arise here.
CREATE OR REPLACE VIEW spec_candidates AS
SELECT
  m.id,
  m.slug,
  m.name,
  m.manufacturer_name,
  m.year,
  s.ipdb_id,
  s.specialty,
  s.archive_capture_date            AS capture_date,
  map.field,
  map.value,
  map.arity,
  map.deferred_because,
  -- What the catalog holds in that field today. For a single-valued field this is the
  -- one value; for a multi-valued one it is whether the value is already among them.
  CASE map.field
    WHEN 'game_format' THEN m.game_format_slug
    WHEN 'cabinet'     THEN m.cabinet_slug
  END                               AS current_single_value,
  CASE map.field
    WHEN 'tag'              THEN EXISTS (SELECT 1 FROM model_tags t
                                         WHERE t.model_id = m.id AND t.tag_slug = map.value)
    WHEN 'reward_type'      THEN EXISTS (SELECT 1 FROM model_rewards r
                                         WHERE r.model_id = m.id AND r.reward_type_slug = map.value)
    WHEN 'gameplay_feature' THEN EXISTS (SELECT 1 FROM model_gameplay_features g
                                         WHERE g.model_id = m.id AND g.feature_slug = map.value)
    ELSE FALSE
  END                               AS carried_many
FROM px.ipdb.model_specialties AS s
JOIN models    AS m   ON m.ipdb_id = s.ipdb_id
LEFT JOIN _spec_map AS map ON map.specialty = s.specialty;

-- Every candidate, labelled. `status` partitions the population exactly once, so the
-- emitted and rejected views below are two reads of one classification rather than two
-- predicates that can drift apart.
CREATE OR REPLACE VIEW _spec_classified AS
SELECT
  c.*,
  CASE
    WHEN c.field IS NULL                             THEN 'specialty_deferred'
    WHEN c.arity = 'one' AND c.current_single_value = c.value
                                                     THEN 'catalog_already_carries'
    WHEN c.arity = 'one' AND c.current_single_value IS NOT NULL
                                                     THEN 'catalog_holds_a_conflicting_value'
    WHEN c.arity = 'many' AND c.carried_many         THEN 'catalog_already_carries'
    ELSE 'emit'
  END AS status,
  -- The widebody inference, withheld wherever the format slot is spoken for. A sibling
  -- specialty that is DEFERRED blocks it too: `Not A Pinball` is deferred precisely
  -- because nobody has said what the machine is instead, and that is not a licence to
  -- call it a pinball.
  (c.specialty = 'Widebody'
   AND c.current_single_value IS NULL
   AND NOT EXISTS (
     SELECT 1 FROM spec_candidates AS o
     WHERE o.id = c.id
       AND o.specialty <> c.specialty
       AND (o.field = 'game_format' OR o.field IS NULL))
  ) AS implies_pinball
FROM spec_candidates AS c;

-- The emitted set. One row per (model, specialty), carrying the field to assert, the
-- value, and the verbatim span of the page's own `Specialty:` row that states it.
--
-- The quote is `Specialty: [...] <name>` for every row: two spans in source order, the
-- label that anchors the reader on the page and the one word this row asserts. IPDB runs
-- several specialties together on one line, so quoting the whole line would make one
-- excerpt cover facts belonging to other rows; the join keeps each quote to its own fact
-- and stays verbatim whether the name sits first on the line or last.
CREATE OR REPLACE VIEW spec_patch_rows AS
SELECT
  id,
  slug,
  name,
  manufacturer_name,
  ipdb_id,
  specialty,
  field,
  value,
  arity,
  current_single_value,
  implies_pinball,
  CASE WHEN implies_pinball THEN (SELECT game_format FROM _spec_widebody_implies) END
                                              AS implied_game_format,
  'ipdb:' || ipdb_id::VARCHAR                 AS cite_ref,
  'Specialty: [...] ' || specialty            AS quote,
  capture_date
FROM _spec_classified
WHERE status = 'emit';

-- Held back, and why. One reason per row.
--
-- `catalog_holds_a_conflicting_value` is the branch the single-valued argument above
-- exists for, and it is not empty: twelve rows, every one of them a listing on which
-- IPDB prints two specialties competing for one field. In each the catalog already holds
-- the OTHER of the two, so the disagreement is between IPDB's own headings and not
-- between IPDB and us -- `conflict_value_unsupported_by_page` asserts exactly that.
CREATE OR REPLACE VIEW spec_rejected AS
SELECT
  id, slug, manufacturer_name, ipdb_id, specialty, field, value,
  current_single_value, deferred_because,
  status AS reason
FROM _spec_classified
WHERE status <> 'emit';

-- == 3 · SUMMARY & CHECKS ===================================================

CREATE OR REPLACE VIEW spec_summary AS
            SELECT 'models_live' AS metric, (SELECT count(*) FROM models) AS value
  UNION ALL SELECT 'listings_with_a_specialty',
    (SELECT count(DISTINCT ipdb_id) FROM px.ipdb.model_specialties)
  UNION ALL SELECT 'candidates',            (SELECT count(*) FROM spec_candidates)
  UNION ALL SELECT 'candidate_models',      (SELECT count(DISTINCT id) FROM spec_candidates)
  UNION ALL SELECT 'patch_rows',            (SELECT count(*) FROM spec_patch_rows)
  UNION ALL SELECT 'patch_models',          (SELECT count(DISTINCT id) FROM spec_patch_rows)
  UNION ALL SELECT 'patch_rows_implying_pinball',
    (SELECT count(*) FROM spec_patch_rows WHERE implies_pinball)
  UNION ALL SELECT 'rejected',              (SELECT count(*) FROM spec_rejected)
  UNION ALL SELECT 'rejected_already_carried',
    (SELECT count(*) FROM spec_rejected WHERE reason = 'catalog_already_carries')
  UNION ALL SELECT 'rejected_conflicting',
    (SELECT count(*) FROM spec_rejected WHERE reason = 'catalog_holds_a_conflicting_value')
  UNION ALL SELECT 'rejected_deferred',
    (SELECT count(*) FROM spec_rejected WHERE reason = 'specialty_deferred')
  ORDER BY metric;

-- Empty when healthy.
CREATE OR REPLACE VIEW spec_checks AS
  -- COMPLETENESS, and the reason the reference table is a table rather than a CASE: the
  -- day IPDB prints a heading nobody has mapped, it must stop the run rather than vanish.
  SELECT 'unmapped_specialty' AS check_name, NULL::BIGINT AS id, s.specialty AS detail
  FROM (SELECT DISTINCT specialty FROM px.ipdb.model_specialties) AS s
  WHERE NOT EXISTS (SELECT 1 FROM _spec_map m WHERE m.specialty = s.specialty)
  UNION ALL
  -- SAFETY: this campaign only FILLS an empty slot. A single-valued row emitted over an
  -- existing value would overwrite a catalog claim with a reading of a stale page.
  SELECT 'emitted_over_a_filled_slot', r.id, r.slug || ' ' || r.field || '=' || r.value
  FROM spec_patch_rows r
  WHERE r.arity = 'one' AND r.current_single_value IS NOT NULL
  UNION ALL
  -- Re-asserting a member a record already holds changes nothing, and the apply engine
  -- rejects a provenance-carrying unit that changes nothing.
  SELECT 'emitted_a_member_already_carried', c.id, c.slug || ' ' || c.field || '=' || c.value
  FROM _spec_classified c
  WHERE c.status = 'emit' AND c.arity = 'many' AND c.carried_many
  UNION ALL
  -- The conflict branch's justification, asserted rather than assumed: where we hold a
  -- different value than IPDB's heading wants, IPDB's OWN page must also assert the value
  -- we hold. A row here would be a real disagreement with the source, wrongly filed as a
  -- standoff between two of its headings.
  SELECT 'conflict_value_unsupported_by_page', j.id,
         j.slug || ' catalog=' || j.current_single_value || ' ipdb=' || j.value
  FROM spec_rejected j
  WHERE j.reason = 'catalog_holds_a_conflicting_value'
    AND NOT EXISTS (
      SELECT 1 FROM spec_candidates o
      WHERE o.id = j.id AND o.value = j.current_single_value)
  UNION ALL
  -- The widebody inference, held to its own rule from both sides.
  SELECT 'pinball_implied_over_a_filled_slot', r.id, r.slug
  FROM spec_patch_rows r
  WHERE r.implies_pinball AND r.current_single_value IS NOT NULL
  UNION ALL
  SELECT 'pinball_implied_beside_another_format', r.id, r.slug
  FROM spec_patch_rows r
  WHERE r.implies_pinball
    AND EXISTS (SELECT 1 FROM spec_candidates o
                WHERE o.id = r.id AND o.specialty <> r.specialty
                  AND (o.field = 'game_format' OR o.field IS NULL))
  UNION ALL
  -- Every value a row asserts must be a record that exists, EXCEPT the one this patch
  -- creates. `flipperless` is listed by name so that the day it lands the check starts
  -- covering it too, rather than staying permanently blind to one slug.
  SELECT 'target_vocabulary_missing', NULL::BIGINT, r.field || '=' || r.value
  FROM (SELECT DISTINCT field, value FROM spec_patch_rows) AS r
  WHERE r.value <> 'flipperless'
    AND NOT EXISTS (
      SELECT 1 FROM (
                  SELECT 'game_format' AS field, slug FROM game_formats
        UNION ALL SELECT 'cabinet',              slug FROM cabinets
        UNION ALL SELECT 'tag',                  slug FROM tags
        UNION ALL SELECT 'reward_type',          slug FROM reward_types
        UNION ALL SELECT 'gameplay_feature',     slug FROM gameplay_features
      ) AS v WHERE v.field = r.field AND v.slug = r.value)
  UNION ALL
  -- Structural: emitted + rejected must partition the candidates, so a row can never be
  -- silently dropped between detection and emission.
  SELECT 'partition_leaks', NULL::BIGINT,
         (SELECT count(*) FROM spec_candidates)::VARCHAR || ' <> '
           || ((SELECT count(*) FROM spec_patch_rows)
             + (SELECT count(*) FROM spec_rejected))::VARCHAR
  WHERE (SELECT count(*) FROM spec_candidates)
     <> (SELECT count(*) FROM spec_patch_rows) + (SELECT count(*) FROM spec_rejected)
  UNION ALL
  -- ANCHORS. A rotted join or a renamed column zeroes a whole detector with no error, and
  -- no row-level invariant can see a set silently shrink. Each names a case read by hand
  -- off the page it cites.
  SELECT 'anchor_flipperless_gone', NULL::BIGINT, 'gay-cruise (ipdb:990)'
  WHERE NOT EXISTS (SELECT 1 FROM spec_patch_rows
                    WHERE ipdb_id = 990 AND value = 'flipperless')
  UNION ALL
  SELECT 'anchor_bat_game_gone', NULL::BIGINT, 'big-inning-2 (ipdb:5083)'
  WHERE NOT EXISTS (SELECT 1 FROM spec_patch_rows
                    WHERE ipdb_id = 5083 AND value = 'pitch-and-bat')
  UNION ALL
  -- Big Inning is a widebody CABINET on a baseball game. It is the case the withholding
  -- rule was written for, so it is the case worth pinning.
  SELECT 'anchor_big_inning_called_a_pinball', NULL::BIGINT, 'big-inning-2 (ipdb:5083)'
  WHERE EXISTS (SELECT 1 FROM spec_patch_rows WHERE ipdb_id = 5083 AND implies_pinball)
  UNION ALL
  SELECT 'anchor_bingo_one_ball_standoff_gone', NULL::BIGINT, 'one-ball-circus (ipdb:5845)'
  WHERE NOT EXISTS (SELECT 1 FROM spec_rejected
                    WHERE ipdb_id = 5845
                      AND reason = 'catalog_holds_a_conflicting_value');
