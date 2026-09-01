-- IPDB's `Cue Game` and `Horserace Game` specialties.
--
-- ANALYSIS-LOCAL LAYER. The catalog decode is flipcommons' shared foundation; the
-- runner loads it under this file automatically.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so the ATTACH resolves.
--
--     F=campaigns/0325-cue-games/cue_games.sql
--     make analyze FILE=$F PREFIX=cue                    # summary, gated on checks
--     make analyze FILE=$F Q="FROM cue_patch_rows;"      # what gen.py emits for 0326
--     make analyze FILE=$F Q="FROM hr_patch_rows;"       # what gen.py emits for 0327
--
--
-- == CUE GAME IS A FORMAT; HORSERACE GAME IS A THEME ========================
--
-- pinexplore mapped both headings to absent `game-format` values. Reading the
-- census says they are different kinds of thing.
--
-- `Cue Game` (41 listings) names what the machine IS: a coin-operated table on
-- which the player drives the ball with a hand-held cue, pool-fashion, rather
-- than a plunger -- the 1931 Karom Golf tables, the 1955-56 electric-pool wave
-- from Williams, Genco, United and Chicago Coin, US Billiards' 1966 Electro-Pool.
-- Nothing in the format vocabulary says that, so `cue-game` is minted (it rides
-- `0302-new-vocab-terms`) and lands on every member with an EMPTY format slot.
--
-- `Horserace Game` (79 listings) does not name a format. 68 of the 79 also carry
-- `One Ball Game`, and every one of the 10 with an empty format slot is a listing
-- IPDB itself declines to call a one-ball ("we cannot find any information ...
-- to verify if it was a one-ball payout"). The heading names the SUBJECT of the
-- machine -- and the catalog already says so: 71 of the 79 carry the
-- `horse-racing` theme. So the heading lands as that theme on the 8 that do not,
-- and asserts nothing about format. The one-ball definition already reads "often
-- horse-race themed".
--
--
-- == THE SINGLE-VALUED SLOT ==================================================
--
-- `game_format` holds one value. This campaign only ever fills an EMPTY slot, the
-- rule 0297 and 0310 follow. Ten Cue Game members hold another format already:
-- eight are Witzig Corinthian tables on which IPDB asserts `Bagatelle` too -- a
-- contest between two of IPDB's own headings, not a disagreement with us -- and
-- two (`spot-pool-3` as miscellaneous, `hi-score-pool-3` as rolldown) are live
-- claims that would need superseding by hand. `member_holds_unexplained_format`
-- fails the run if a member ever holds a format this file does not account for.

INSTALL sqlite;
ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- == 1 · REFERENCE ==========================================================

-- Members holding a format this campaign knowingly leaves alone, and why. A
-- literal relation because it is a human reading; the gates hold it to the census.
CREATE OR REPLACE TABLE _cue_held_back (slug VARCHAR, holds VARCHAR, why VARCHAR);
INSERT INTO _cue_held_back VALUES
  ('spot-pool-3',     'miscellaneous', 'live claim; supersede by hand after reading the machine'),
  ('hi-score-pool-3', 'rolldown',      'live claim; supersede by hand after reading the machine');

-- == 2 · CUE GAME ===========================================================

-- One row per live model IPDB assigns the heading, with what it already carries.
CREATE OR REPLACE VIEW cue_population AS
SELECT
  m.id   AS model_id,
  m.slug,
  m.name,
  m.manufacturer_name,
  m.year,
  s.ipdb_id,
  m.game_format_slug,
  EXISTS (SELECT 1 FROM px.ipdb.model_specialties AS o
          WHERE o.ipdb_id = s.ipdb_id AND o.specialty = 'Bagatelle') AS ipdb_also_bagatelle,
  h.holds IS NOT NULL AS held_back
FROM px.ipdb.model_specialties AS s
JOIN models AS m ON m.ipdb_id = s.ipdb_id
LEFT JOIN _cue_held_back AS h ON h.slug = m.slug
WHERE s.specialty = 'Cue Game';

-- What gen.py emits for 0326: the format on every member whose slot is empty.
CREATE OR REPLACE VIEW cue_patch_rows AS
SELECT
  p.slug,
  p.name,
  p.ipdb_id,
  'cue-game' AS game_format,
  'Specialty: [...] Cue Game' AS specialty_quote
FROM cue_population AS p
WHERE p.game_format_slug IS NULL
ORDER BY p.slug;

-- == 3 · HORSERACE GAME =====================================================

CREATE OR REPLACE VIEW hr_population AS
SELECT
  m.id   AS model_id,
  m.slug,
  m.name,
  m.manufacturer_name,
  m.year,
  s.ipdb_id,
  m.game_format_slug,
  EXISTS (SELECT 1 FROM px.ipdb.model_specialties AS o
          WHERE o.ipdb_id = s.ipdb_id AND o.specialty = 'One Ball Game') AS ipdb_also_one_ball,
  EXISTS (SELECT 1 FROM model_themes AS t
          WHERE t.model_id = m.id AND t.theme_slug = 'horse-racing') AS carries_theme
FROM px.ipdb.model_specialties AS s
JOIN models AS m ON m.ipdb_id = s.ipdb_id
WHERE s.specialty = 'Horserace Game';

-- What gen.py emits for 0327: the theme on every member that lacks it.
CREATE OR REPLACE VIEW hr_patch_rows AS
SELECT
  p.slug,
  p.name,
  p.ipdb_id,
  'horse-racing' AS theme,
  'Specialty: [...] Horserace Game' AS specialty_quote
FROM hr_population AS p
WHERE NOT p.carries_theme
ORDER BY p.slug;

-- == 4 · GATES ==============================================================

CREATE OR REPLACE VIEW cue_checks AS
  -- An empty population means the census moved, not that the work is done.
  SELECT 'specialty_absent_from_census' AS check_name, NULL::BIGINT AS model_id,
         v.specialty AS detail
  FROM (VALUES ('Cue Game'), ('Horserace Game')) AS v(specialty)
  WHERE NOT EXISTS (SELECT 1 FROM px.ipdb.model_specialties AS s WHERE s.specialty = v.specialty)
  UNION ALL
  -- A listing the census carries that no live model answers: the assertion has
  -- nowhere to land, and creating a record is a different campaign.
  SELECT 'listing_matches_no_model', NULL::BIGINT,
         s.specialty || ' ipdb:' || s.ipdb_id::VARCHAR
  FROM px.ipdb.model_specialties AS s
  WHERE s.specialty IN ('Cue Game', 'Horserace Game')
    AND NOT EXISTS (SELECT 1 FROM models AS m WHERE m.ipdb_id = s.ipdb_id)
  UNION ALL
  -- THE SINGLE-VALUED RULE, ASSERTED. A member holding a format is left alone only
  -- because IPDB also asserts Bagatelle on it, or because a human listed it in
  -- `_cue_held_back` with the format it holds. Anything else is a real
  -- disagreement with the source that a blanket assertion may not paper over.
  SELECT 'member_holds_unexplained_format', p.model_id,
         p.slug || ' holds ' || p.game_format_slug
  FROM cue_population AS p
  LEFT JOIN _cue_held_back AS h ON h.slug = p.slug
  WHERE p.game_format_slug IS NOT NULL
    AND p.game_format_slug <> 'cue-game'
    AND NOT (p.ipdb_also_bagatelle AND p.game_format_slug = 'bagatelle')
    AND h.holds IS DISTINCT FROM p.game_format_slug
  UNION ALL
  -- Drift guard on the literal relation: a held-back row must still name a
  -- member holding the format it was held back for.
  SELECT 'held_back_does_not_resolve', NULL::BIGINT, h.slug
  FROM _cue_held_back AS h
  WHERE NOT EXISTS (SELECT 1 FROM cue_population AS p
                    WHERE p.slug = h.slug AND p.game_format_slug = h.holds)
  UNION ALL
  -- The premise of landing Horserace Game as a theme: no member may be a machine
  -- the catalog calls something other than a one-ball. A member holding, say,
  -- `bingo-pinball` would be a heading meaning something this file has not read.
  SELECT 'horserace_member_holds_non_one_ball_format', p.model_id,
         p.slug || ' holds ' || p.game_format_slug
  FROM hr_population AS p
  WHERE p.game_format_slug IS NOT NULL AND p.game_format_slug <> 'one-ball'
  UNION ALL
  -- The theme must exist before anything can carry it.
  SELECT 'theme_vocabulary_absent', NULL::BIGINT, 'horse-racing'
  WHERE NOT EXISTS (SELECT 1 FROM themes AS t WHERE t.slug = 'horse-racing');
COMMENT ON VIEW cue_checks IS
  'Gates for the cue-game / horserace campaign — one row per failure; empty is a pass.';

-- `cue-game` rides `0302-new-vocab-terms`, which lands in the same rebuild as
-- 0326, so its absence cannot gate emission -- the apply engine refuses 0326
-- on its own if the format is missing. Reported here so the state is visible.
CREATE OR REPLACE VIEW cue_summary AS
  SELECT 'cue_population'             AS metric, count(*) AS n FROM cue_population
  UNION ALL SELECT 'cue_slot_empty',            count(*) FROM cue_population WHERE game_format_slug IS NULL
  UNION ALL SELECT 'cue_already_cue_game',      count(*) FROM cue_population WHERE game_format_slug = 'cue-game'
  UNION ALL SELECT 'cue_ipdb_also_bagatelle',   count(*) FROM cue_population WHERE ipdb_also_bagatelle AND game_format_slug = 'bagatelle'
  UNION ALL SELECT 'cue_held_back',             count(*) FROM cue_population WHERE held_back
  UNION ALL SELECT 'cue_patch_rows',            count(*) FROM cue_patch_rows
  UNION ALL SELECT 'cue_game_vocabulary_present', count(*) FROM game_formats WHERE slug = 'cue-game'
  UNION ALL SELECT 'hr_population',             count(*) FROM hr_population
  UNION ALL SELECT 'hr_ipdb_also_one_ball',     count(*) FROM hr_population WHERE ipdb_also_one_ball
  UNION ALL SELECT 'hr_catalog_one_ball',       count(*) FROM hr_population WHERE game_format_slug = 'one-ball'
  UNION ALL SELECT 'hr_already_themed',         count(*) FROM hr_population WHERE carries_theme
  UNION ALL SELECT 'hr_patch_rows',             count(*) FROM hr_patch_rows
  UNION ALL SELECT 'CHECK_FAILURES',            count(*) FROM cue_checks;
