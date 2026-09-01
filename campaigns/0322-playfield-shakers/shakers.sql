-- IPDB's `Shaker Ball Machine` specialty, landed as a gameplay feature.
--
-- ANALYSIS-LOCAL LAYER. The catalog decode is flipcommons' shared foundation; the
-- runner loads it under this file automatically.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so the ATTACH resolves.
--
--     F=campaigns/0322-playfield-shakers/shakers.sql
--     make analyze FILE=$F PREFIX=shk                  # summary, gated on checks
--     make analyze FILE=$F Q="FROM shk_patch_rows;"    # exactly what gen.py emits
--
--
-- == WHY THIS IS NOT A GAME FORMAT =========================================
--
-- pinexplore mapped the heading to an absent `game-format` value, on the reading
-- that IPDB's Specialty row names what KIND of machine a listing is. It does not
-- here. All five members are ordinary machines of some other format carrying an
-- extra CONTROL: three already hold `bingo-pinball` correctly, and the two Allied
-- games are flipper pinballs with pop bumpers and slingshots. Spending the
-- single-valued format slot on the control would overwrite a correct value on
-- three of the five and misdescribe the other two.
--
-- What the heading names is a player-operated device, so it lands as a gameplay
-- feature -- a ROOT one. Every parent in that DAG is a generic device and its
-- children are varieties of it (`flippers` -> kinds of flipper, `playfields` ->
-- kinds of playfield), and a device that ACTS ON the playfield is not a kind of
-- playfield. Every other player-operated device sits at the root for the same
-- reason: `flippers`, `kickback`, `ball-save`, `magna-save`, `shaker-motors`.
--
--
-- == WHY TWO TERMS, AND WHY THE PARENT GOES ON ALL FIVE ====================
--
-- `Shaker Ball` is ALLIED LEISURE'S MARKETING NAME, quoted as such in IPDB's own
-- Notable Features on Sea Hunt and Spooksville. IPDB then borrowed it as the
-- generic heading and hung it on three machines that never used the phrase -- a
-- 1954 Bally bingo with a "Bump-feature" and two c.1971 Japanese payout machines
-- with a "Skill Bumper feature". So the catalog takes the generic term for the
-- heading and keeps Allied's name as a kind of it.
--
-- EACH MODEL CARRIES ONE TERM: THE MOST SPECIFIC ONE THAT APPLIES. The two Allied
-- machines take `shaker-ball` alone and the other three take `playfield-shakers`;
-- nothing asserts a feature a model's own term already implies, because the DAG
-- carries the hierarchy and a model repeating it would be storing the same fact
-- twice, in a second place that can drift.
--
-- One consequence is real and lives outside this campaign: the comparison layer's
-- gameplay-feature carriage is an exact slug match with no descendant walk
-- (`assertions.sql`), so it reads the Allied pair as missing `playfield-shakers`.
-- That is the layer asking the wrong question, not a gap here.

INSTALL sqlite;
ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- == 1 · REFERENCE ==========================================================

-- The sentence each listing uses to DESCRIBE the mechanism, as against the
-- Specialty heading that merely classifies it. Every member has one, so every
-- assertion can cite prose a reader can follow rather than a two-word label.
-- A literal relation because it is a human reading of five listings; the census
-- records only which machines carry the heading.
CREATE OR REPLACE TABLE _shk_mechanism (ipdb_id BIGINT, quote VARCHAR);
INSERT INTO _shk_mechanism VALUES
  -- Allied's two, in the maker's own words -- the span that also earns them the
  -- `shaker-ball` term. Identical wording on both listings.
  (2081, 'The joysticks manually push up to electromechanically nudge the playfield upwards in a jolting "Shaker Ball" action.'),
  (2298, 'The joysticks manually push up to electromechanically nudge the playfield upwards in a jolting "Shaker Ball" action.'),
  -- Hi-Fi is the only listing that spells out the causal chain from jolt to ball,
  -- so both sentences are quoted: the second opens "This action" and says nothing
  -- on its own.
  (1166, 'A button on each side of the cabinet (where flipper buttons would be) allows the player to "bump" the playfield up to ten times per game. This action jolts the playfield away from the player, allowing a playfield post to hit a rolling ball upfield.'),
  -- The Japanese pair, identical wording on both.
  (6759, 'A button on each side of the cabinet activates the Skill Bumper feature. Pressing either button during play will jolt the playfield forward about an inch.'),
  (6763, 'A button on each side of the cabinet activates the Skill Bumper feature. Pressing either button during play will jolt the playfield forward about an inch.');

-- The two machines whose listing uses ALLIED'S PHRASE, and so take the child term
-- on top of the generic one.
CREATE OR REPLACE TABLE _shk_allied (ipdb_id BIGINT, slug VARCHAR);
INSERT INTO _shk_allied VALUES (2081, 'sea-hunt'), (2298, 'spooksville');

-- == 2 · ANALYSIS ===========================================================

-- One row per live model IPDB assigns the heading, with what it already carries.
CREATE OR REPLACE VIEW shk_population AS
SELECT
  m.id        AS model_id,
  m.slug,
  m.name,
  m.manufacturer_name,
  m.year,
  s.ipdb_id,
  m.game_format_slug,
  a.slug IS NOT NULL AS is_allied,
  EXISTS (SELECT 1 FROM model_gameplay_features g
          WHERE g.model_id = m.id AND g.feature_slug = 'playfield-shakers') AS carries_parent,
  EXISTS (SELECT 1 FROM model_gameplay_features g
          WHERE g.model_id = m.id AND g.feature_slug = 'shaker-ball')       AS carries_child,
  -- Carried = holds the one term this campaign asserts for it.
  EXISTS (SELECT 1 FROM model_gameplay_features g
          WHERE g.model_id = m.id
            AND g.feature_slug = CASE WHEN a.slug IS NOT NULL
                                      THEN 'shaker-ball' ELSE 'playfield-shakers' END) AS carries_its_term
FROM px.ipdb.model_specialties AS s
JOIN models AS m ON m.ipdb_id = s.ipdb_id
LEFT JOIN _shk_allied AS a ON a.ipdb_id = s.ipdb_id
WHERE s.specialty = 'Shaker Ball Machine';

-- What gen.py emits: the generic feature on every member, plus Allied's name on
-- the two machines whose listing uses it. One entry per model — the two features
-- ride one changeset because the disjoint-fields rule forbids two entries setting
-- `gameplay_feature` on one record.
--
-- DELIBERATELY NOT FILTERED ON WHAT THE CATALOG ALREADY CARRIES. An applied patch
-- is immutable, so a generator has to be able to re-render it and byte-compare;
-- an emit set that empties itself the moment the patch applies can never prove
-- it would still emit the same file. `already_carries` in the summary is where
-- that fact belongs.
CREATE OR REPLACE VIEW shk_patch_rows AS
SELECT
  p.slug,
  p.name,
  p.ipdb_id,
  p.is_allied,
  -- The most specific term only; the DAG supplies the rest.
  CASE WHEN p.is_allied THEN ['shaker-ball']
       ELSE ['playfield-shakers'] END AS features,
  'Specialty: [...] Shaker Ball Machine' AS specialty_quote,
  q.quote AS mechanism_quote
FROM shk_population AS p
JOIN _shk_mechanism AS q ON q.ipdb_id = p.ipdb_id
ORDER BY p.slug;

-- == 3 · GATES ==============================================================

CREATE OR REPLACE VIEW shk_checks AS
  -- An empty population means the census moved, not that the work is done.
  SELECT 'specialty_absent_from_census' AS check_name, NULL::BIGINT AS model_id,
         'no listing carries Shaker Ball Machine' AS detail
  WHERE NOT EXISTS (SELECT 1 FROM shk_population)
  UNION ALL
  -- A listing the census carries that no live model answers: the assertion has
  -- nowhere to land, and creating a record is a different campaign.
  SELECT 'listing_matches_no_model', NULL::BIGINT,
         'ipdb:' || s.ipdb_id::VARCHAR
  FROM px.ipdb.model_specialties AS s
  WHERE s.specialty = 'Shaker Ball Machine'
    AND NOT EXISTS (SELECT 1 FROM models AS m WHERE m.ipdb_id = s.ipdb_id)
  UNION ALL
  -- EVERY QUOTED SPAN MUST STILL BE IN ITS LISTING. This is also the premise of
  -- the two-term split for the Allied pair: if IPDB rewords a note, the assertion
  -- loses its evidence and the reading must be re-argued.
  SELECT 'mechanism_quote_absent', NULL::BIGINT, 'ipdb:' || q.ipdb_id::VARCHAR
  FROM _shk_mechanism AS q
  WHERE NOT EXISTS (
    SELECT 1 FROM px.ipdb.models AS d
    WHERE d.ipdb_id = q.ipdb_id
      AND replace(coalesce(d.notable_features, ''), '  ', ' ')
          LIKE '%' || q.quote || '%')
  UNION ALL
  -- Drift guard on the mechanism relation: a member with no quote would emit a
  -- bare-heading cite again, silently.
  SELECT 'mechanism_quote_missing', p.model_id, p.slug
  FROM shk_population AS p
  WHERE NOT EXISTS (SELECT 1 FROM _shk_mechanism AS q WHERE q.ipdb_id = p.ipdb_id)
  UNION ALL
  -- Drift guard on the literal relation: a slug that no longer names the model
  -- that ipdb_id is on is a patch that will not resolve.
  SELECT 'allied_does_not_resolve', NULL::BIGINT, a.slug
  FROM _shk_allied AS a
  WHERE NOT EXISTS (
    SELECT 1 FROM models AS m WHERE m.slug = a.slug AND m.ipdb_id = a.ipdb_id)
  UNION ALL
  -- The converse of the split: a NON-Allied member whose listing does use the
  -- phrase would be a machine owed the child term too.
  SELECT 'non_allied_uses_allied_wording', p.model_id, p.slug
  FROM shk_population AS p
  JOIN px.ipdb.models AS d ON d.ipdb_id = p.ipdb_id
  WHERE NOT p.is_allied
    AND coalesce(d.notable_features, '') || coalesce(d.notes, '') LIKE '%Shaker Ball%'
  UNION ALL
  -- The rule this campaign follows, asserted: a model holding both the child and
  -- the parent is storing the hierarchy twice.
  SELECT 'member_carries_redundant_ancestor', p.model_id, p.slug
  FROM shk_population AS p
  WHERE p.carries_child AND p.carries_parent
  UNION ALL
  -- The vocabulary 0322 mints must exist before these assertions can land.
  SELECT 'feature_vocabulary_absent', NULL::BIGINT, v.slug
  FROM (VALUES ('playfield-shakers'), ('shaker-ball')) AS v(slug)
  WHERE NOT EXISTS (SELECT 1 FROM gameplay_features AS f WHERE f.slug = v.slug);
COMMENT ON VIEW shk_checks IS
  'Gates for the playfield-shaker campaign — one row per failure; empty is a pass.';

CREATE OR REPLACE VIEW shk_summary AS
  SELECT 'population'          AS metric, count(*) AS n FROM shk_population
  UNION ALL SELECT 'allied_members',      count(*) FROM shk_population WHERE is_allied
  UNION ALL SELECT 'already_carries',     count(*) FROM shk_population WHERE carries_its_term
  UNION ALL SELECT 'patch_rows',          count(*) FROM shk_patch_rows
  UNION ALL SELECT 'CHECK_FAILURES',      count(*) FROM shk_checks;
