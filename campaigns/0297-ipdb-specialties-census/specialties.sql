-- IPDB's `Specialty:` row, landed on the catalog's own classification vocabulary --
-- the full-corpus re-run of 0290, off the advanced-search census.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, liveness
-- filtering, the NULL-spelling regularization) is FLIPCOMMONS' shared foundation; the
-- runner loads it under this file automatically, so nothing is `.read` here.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so that this file's ATTACH resolves.
-- `make analyze` handles that and delegates to flipcommons' shared runner. Do not run
-- this file directly:
--
--     F=campaigns/0297-ipdb-specialties-census/specialties.sql
--     make analyze FILE=$F PREFIX=spec                 # summary, gated on checks
--     make analyze FILE=$F Q="FROM spec_patch_rows;"   # exactly what gen.py emits
--     make analyze FILE=$F Q="FROM spec_rejected;"     # what the gate held back, and why
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
--
-- == WHAT CHANGED SINCE 0290 ================================================
--
-- 0290 read the same field off archive.org captures of IPDB machine pages, and could
-- only see the 151 listings that happened to have one -- a cohort fetched for the 0268
-- project-date work and skewed toward dateless, never-produced, bingo and EM machines.
--
-- IPDB's ADVANCED SEARCH answers the question directly: one query per specialty returns
-- every machine carrying it. Those result pages are what pinexplore now ingests, and
-- `px.ipdb.model_specialties` is the census built from them -- 4,186 assignments over
-- 3,291 listings, against 188 over 151. It is also NEWER than any capture, and it is one
-- read taken at one moment rather than eight years of drift.
--
-- The census is a strict SUPERSET of what the captures held: zero archive rows are
-- absent from it. So this is a widening, not a revision, and 0290's assertions stand.
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
-- The same rule is enforced a second time, downstream, by the quote gate: flippatch's
-- `ipdb:` resolver renders the `Specialty:` line from this same census, so a quote here
-- is checked against the very rows this analysis reads.
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
-- (`catalog_holds_a_conflicting_value` below). Those are not catalog defects: in every
-- case in the corpus the value the catalog holds is one IPDB also asserts on the same
-- page, which `conflict_value_unsupported_by_page` asserts rather than assumes.


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
  -- New in this run. The captures held 8 of these; the census holds 77. `gun-game` has
  -- been a catalog format all along, so this needed no new vocabulary -- only enough
  -- rows to be worth mapping. 77 of them also carry `Not A Pinball`, which is exactly
  -- right and is why that heading stays deferred rather than blocking: `Gun Game` says
  -- what the machine IS, and a heading saying what it is not must not overrule it.
  ('Gun Game',                            'game_format',      'gun-game',                      'one',  NULL),
  ('Cocktail Table',                      'cabinet',          'cocktail',                      'one',  NULL),
  ('Widebody',                            'tag',              'widebody',                      'many', NULL),
  ('Non-Commercial Machine [Home Model]', 'tag',              'home-use',                      'many', NULL),
  ('Flipperless',                         'tag',              'flipperless',                   'many', NULL),
  ('Mechanical Backbox Animation',        'gameplay_feature', 'mechanical-backbox-animations', 'many', NULL),
  ('Add-A-Ball',                          'reward_type',      'add-a-ball',                    'many', NULL),
  ('Novelty Play',                        'reward_type',      'novelty',                       'many', NULL),
  -- New in this run, and the one mapping worth stating a reason for: IPDB's `Redemption
  -- Game` is a machine that pays the player in tickets, which is `ticket-payout` exactly.
  -- It is multi-valued, so it fills a gap beside whatever else a machine rewards.
  ('Redemption Game',                     'reward_type',      'ticket-payout',                 'many', NULL),
  ('Head-to-Head Play',                   'gameplay_feature', 'head-to-head',                  'many', NULL),
  ('Zipper Flippers',                     'gameplay_feature', 'zipper-flippers',               'many', NULL),

  -- == DEFERRED ==============================================================
  --
  -- Deferred for VOCABULARY: IPDB's heading crosses our axes rather than filling a gap
  -- in them, so no new term resolves it and the models have to be read one at a time.
  ('Payout Machine',           NULL, NULL, NULL,
   'Spans cash-payout, merchant-paid and ticket-payout; which one needs the machine read.'),
  ('Table Top/Counter Game',   NULL, NULL, NULL,
   'Spans the tabletop and countertop cabinets; which one needs the machine read.'),
  ('Not A Pinball',            NULL, NULL, NULL,
   'States what a machine is not; the format it IS has to come from somewhere else.'),
  ('Horserace Game',           NULL, NULL, NULL,
   'May be a kind of one-ball rather than a peer of it; IPDB asserts both on four of five.'),
  ('Cue Game',                 NULL, NULL, NULL,
   'No catalog format for a cue-and-ball table; minting one needs the machines read.'),
  ('Shaker Ball Machine',      NULL, NULL, NULL,
   'No catalog format for it, and five machines is too thin a base to mint one from.'),
  ('Vertical Pinball Machine', NULL, NULL, NULL,
   'No catalog cabinet for a vertical playfield; whether it is a cabinet at all is open.'),
  --
  -- Deferred for SHAPE: these three are the only headings naming a model RELATIONSHIP,
  -- and a `model_relationship:` member is not authorable from the heading alone. It
  -- requires a target (`target_machine` XOR `target_label`) and a `license_status`, and
  -- IPDB's one word supplies neither -- it says a machine was converted, never from
  -- what, nor under whose authority. 0290 emitted none of these either.
  ('Conversion Kit',           NULL, NULL, NULL,
   'A relationship edge needs a target and a license_status; the heading gives neither.'),
  ('Converted Game',           NULL, NULL, NULL,
   'A relationship edge needs a target and a license_status; the heading gives neither.'),
  ('Re-themed Game',           NULL, NULL, NULL,
   'A relationship edge needs a target and a license_status; the heading gives neither.'),
  --
  -- Deferred because it is ALREADY DONE. The three machines IPDB marks are asserted in
  -- patch 0298, against the `wwii-contract` tag 0296 had to create first -- two patches
  -- because they are two sources: minting the term is ours (`flipcommons-catalog`),
  -- while who carries it is IPDB's. Mapped here so `unmapped_specialty` stays quiet,
  -- emitting nothing so this patch cannot re-assert what 0298 already said.
  ('WWII Contract',            NULL, NULL, NULL,
   'Asserted in patch 0298, against the tag 0296 had to create first.');

-- ADJUDICATED CONFLICTS. `conflict_value_unsupported_by_page` asserts that every
-- single-valued conflict is a standoff between two of IPDB's OWN headings, with the
-- catalog holding one of them. Across 0290's 151-listing cohort that held for all 8.
-- Across the census it holds for 13 of 18, and these five are the exceptions: the
-- catalog says `bingo-pinball` and IPDB never says it anywhere on the listing.
--
-- NOTHING IS EMITTED FOR THEM EITHER WAY -- the slot is full and this campaign only
-- fills empty ones -- so listing them here changes no output. It keeps the check
-- guarding the other thirteen instead of being deleted for being inconvenient, and it
-- records that a person looked.
--
-- `contest` is the one worth a second look, and it is flagged rather than resolved
-- here: a 1941 Keeney predates the bingo format entirely (Bally's Bright Lights, 1951),
-- so IPDB's `One Ball Game` is very likely right and the catalog very likely wrong.
-- Correcting it means superseding a live claim, which is a different patch than this
-- one and needs the machine read.
CREATE OR REPLACE TABLE _spec_conflict_adjudicated (id BIGINT, note VARCHAR);
INSERT INTO _spec_conflict_adjudicated VALUES
  (1403, 'contest (ipdb:563) — 1941 Keeney predates bingo; IPDB''s one-ball is likely right.'),
  (3870, 'multiplier (ipdb:4057) — catalog reads it as bingo; IPDB files it by wager format.'),
  (2152, 'flipper-bingo (ipdb:6164) — named a bingo; IPDB files it by wager format.'),
  (778,  'bing-o-reno (ipdb:5684) — named a bingo; IPDB files it by mechanism.'),
  (3463, 'lucky-joker (ipdb:6180) — catalog reads it as bingo; IPDB files it by mechanism.');

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
  s.observed_on,
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
    -- The single-valued trap's OTHER face, and the one 0290's corpus never showed.
    -- The two branches above compare IPDB against a value the catalog already holds.
    -- This one fires where the catalog holds NOTHING and IPDB itself names two values
    -- for the one slot -- `sockit` reads `Specialty: Bat Game One Ball Game`, and both
    -- are mapped, so a naive replay emits two entries setting `game_format` on one
    -- record. The apply engine rejects that outright ("field set by more than one entry
    -- on this record"), which is the right answer: choosing between two of IPDB's own
    -- headings is a reading of the machine, not a replay of the source. Emit NEITHER.
    WHEN c.arity = 'one' AND EXISTS (
      SELECT 1 FROM spec_candidates AS o
      WHERE o.id = c.id AND o.field = c.field AND o.value <> c.value
    )                                                THEN 'siblings_contest_an_empty_slot'
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
-- and stays verbatim whether the name sits first on the line or last. That last property
-- is load-bearing here: the resolver renders the line alphabetically rather than in
-- IPDB's own order, and the ellipsis is what makes the ordering irrelevant.
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
  observed_on
FROM _spec_classified
WHERE status = 'emit';

-- Held back, and why. One reason per row.
CREATE OR REPLACE VIEW spec_rejected AS
SELECT
  id, slug, manufacturer_name, ipdb_id, specialty, field, value,
  current_single_value, deferred_because,
  status AS reason
FROM _spec_classified
WHERE status <> 'emit';

-- The five conflicts a person has ruled on, browsable beside the check that would
-- otherwise fire on them. `_spec_conflict_adjudicated` in section 1 carries the reasons.
CREATE OR REPLACE VIEW spec_conflicts_adjudicated AS
SELECT r.id, r.slug, r.ipdb_id, r.specialty, r.value AS ipdb_wants,
       r.current_single_value AS catalog_holds, a.note
FROM spec_rejected r
JOIN _spec_conflict_adjudicated a ON a.id = r.id
WHERE r.reason = 'catalog_holds_a_conflicting_value';

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
  UNION ALL SELECT 'rejected_sibling_contest',
    (SELECT count(*) FROM spec_rejected WHERE reason = 'siblings_contest_an_empty_slot')
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
  -- existing value would overwrite a catalog claim with a reading of the source.
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
    AND NOT EXISTS (
      SELECT 1 FROM _spec_conflict_adjudicated a WHERE a.id = j.id)
  UNION ALL
  -- The adjudication list must not outlive what it adjudicates: an id here that is no
  -- longer a conflict is a stale exemption quietly narrowing the check above.
  SELECT 'stale_conflict_adjudication', a.id, a.note
  FROM _spec_conflict_adjudicated a
  WHERE NOT EXISTS (
    SELECT 1 FROM spec_rejected j
    WHERE j.id = a.id AND j.reason = 'catalog_holds_a_conflicting_value')
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
  -- Every value a row asserts must be a record that exists. No exceptions this run: the
  -- two entries 0290 had to mint are live, and `wwii-contract` -- the only new term this
  -- corpus needs -- is created in 0296 and deferred here, so nothing is emitted against
  -- vocabulary that has yet to land.
  SELECT 'target_vocabulary_missing', NULL::BIGINT, r.field || '=' || r.value
  FROM (SELECT DISTINCT field, value FROM spec_patch_rows) AS r
  WHERE NOT EXISTS (
      SELECT 1 FROM (
                  SELECT 'game_format' AS field, slug FROM game_formats
        UNION ALL SELECT 'cabinet',              slug FROM cabinets
        UNION ALL SELECT 'tag',                  slug FROM tags
        UNION ALL SELECT 'reward_type',          slug FROM reward_types
        UNION ALL SELECT 'gameplay_feature',     slug FROM gameplay_features
      ) AS v WHERE v.field = r.field AND v.slug = r.value)
  UNION ALL
  -- 0290 IS NOT RE-ASSERTED. Its 75 assertions are live in the catalog, so every one of
  -- them must land in `catalog_already_carries` rather than here. This is the check that
  -- a re-run of a shipped campaign needs and a first run does not.
  SELECT 'reasserts_a_0290_row', r.id, r.slug || ' ' || r.field || '=' || r.value
  FROM spec_patch_rows r
  WHERE r.ipdb_id IN (158, 990, 2890, 5083) AND r.field IS NOT NULL
    AND r.value IN ('flipperless', 'pitch-and-bat', 'add-a-ball')
  UNION ALL
  -- The apply engine's rule, enforced here where it can be seen: one entry per record
  -- per field. Two emitted rows setting one single-valued field is a CommandError at
  -- ingest, hundreds of assertions into a replay -- far too late to learn it.
  SELECT 'emitted_two_values_into_one_slot', r.id,
         r.slug || ' ' || r.field || ' = ' || string_agg(r.value, ' / ' ORDER BY r.value)
  FROM spec_patch_rows r
  WHERE r.arity = 'one'
  GROUP BY r.id, r.slug, r.field
  HAVING count(*) > 1
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
  -- Big Inning is a widebody CABINET on a baseball game. It is the case the withholding
  -- rule was written for, so it is the case worth pinning -- 0290 pinned it too.
  SELECT 'anchor_big_inning_called_a_pinball', NULL::BIGINT, 'big-inning-2 (ipdb:5083)'
  WHERE EXISTS (SELECT 1 FROM spec_patch_rows WHERE ipdb_id = 5083 AND implies_pinball);
