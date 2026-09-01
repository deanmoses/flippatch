-- IPDB's three relationship specialties -- `Converted Game`, `Conversion Kit`,
-- `Re-themed Game` -- worked into ModelRelationship edges: the research campaign the
-- 0297 census deferred ("a relationship edge needs a target and a `license_status`,
-- and IPDB's one word supplies neither").
--
-- ANALYSIS-LOCAL LAYER over the external data source comparison layer, whose
-- `ipdb_model_relationships_missing` view IS the worklist -- live, so an authored and
-- applied edge drops out of scope on the next run. Nothing here is a snapshot to
-- reconcile, and nothing here re-derives a counterpart: that view's header records,
-- case by case, why no SQL rule can (jaws, handicap-5, broadway-5...). This file only
-- ROUTES the work.
--
-- HOW TO RUN. cwd must be the flipcommons checkout; `make analyze` handles that:
--
--     F=campaigns/0299-ipdb-relationship-lineage/lineage.sql
--     make analyze FILE=$F PREFIX=lineage                    # summary, gated on checks
--     make analyze FILE=$F Q="FROM lineage_sweep_candidates;"  # the sweep feed
--     make analyze FILE=$F Q="FROM lineage_parked_0128;"       # the hand-pass worklist
--
--
-- == HOW THE SCOPE IS CUT ===================================================
--
-- Scope is the `no_edge` class only. The other two classes are DEFERRED, per the
-- regroup that opened this campaign:
--
--   `other_type_edge` (14)    -- the model already carries outbound lineage of another
--                                type; whether that is the same relationship mistyped
--                                or a second relationship is an adjudication question,
--                                not a research gap, and wants its own pass.
--   `edge_points_inward` (3)  -- connected from the far end; same question reversed.
--
-- Within `no_edge`, models campaign 0128's sweep ALREADY JUDGED are routed to a hand
-- pass instead of re-judging ("don't re-adjudicate anything from 0128"): their
-- standing verdicts in that campaign's results.json were parked in doubt buckets and
-- never worked, so the AI half is done and only the human half is outstanding.
-- `lineage_parked_0128` carries those verdicts; `lineage_sweep_candidates` carries
-- everything 0128 never judged. The two partition scope exactly, and the checks
-- assert it.
--
-- Being on 0128's CANDIDATE list without a result row is not adjudication -- that
-- file is regenerated live and proves nothing about what a run judged -- so such
-- models stay in the sweep feed.
--
-- Two scope models (`cadillac-2` ipdb:4795, `sky-chief-2` ipdb:3256) have no IPDB
-- note at all: the specialty census asserts the relationship and no prose names a
-- donor. They stay in the feed -- the judge sees whatever `ipdb:` free text resolves
-- (at least the Specialty line) and lands them in review rather than green.

.read ../flippatch/scripts/analysis/external_data_sources.sql

-- == 1 · SCOPE ==============================================================

-- The `no_edge` slice of the layer's live worklist, at its model+edge grain (a model
-- IPDB marks both a kit and a converted game is two rows here, one candidate below).
CREATE OR REPLACE VIEW lineage_scope AS
  SELECT * FROM ipdb_model_relationships_missing
  WHERE classification = 'no_edge';

-- == 2 · THE 0128 RECORD ====================================================

-- Campaign 0128's sweep results, the point-in-time record of what its run judged.
-- A FROZEN INPUT on the same footing as any recorded adjudication -- the judgments
-- were made and stand; this campaign reuses them rather than re-buying them. The
-- fields carried are the ones the hand pass adjudicates from.
CREATE OR REPLACE VIEW _lineage_0128_rows AS
  SELECT
    CAST(r.ipdb_id AS BIGINT) AS ipdb_id,
    r.model_slug,
    r.disposition,
    r.verdict,
    r.relationship_type,
    r.license_status,
    r.target_title,
    r.target_maker,
    r.target_year,
    r.target_label,
    r.resolved_slug,
    r.resolution_how,
    r.quote,
    r.quote_verified
  FROM (SELECT unnest(rows) AS r
        FROM read_json_auto('../flippatch/campaigns/0128-relationships/sweep/results.json'));

-- == 3 · THE TWO ROUTES =====================================================

-- The sweep feed: scope models with no standing 0128 verdict, one row per MODEL
-- (the sweep judges a model's whole relationship set in one call). No `hint` column
-- on purpose: 0128's target guesses live in its regenerable candidate file, not in
-- any adjudicated record, and the sweep's own resolution plus gates carry the audit.
CREATE OR REPLACE VIEW lineage_sweep_candidates AS
  SELECT DISTINCT s.ipdb_id, s.model_slug, s.model_name
  FROM lineage_scope AS s
  WHERE NOT EXISTS (SELECT 1 FROM _lineage_0128_rows AS j WHERE j.ipdb_id = s.ipdb_id);

-- The hand-pass worklist: scope models 0128 judged, at the grain of its result rows
-- (a note naming two donors is two rows). `specialty_asserts` is what IPDB's census
-- claims; the `judged_*` columns are what 0128's judge read out of the note. The
-- hand pass vets each against the full note (`make show-source ARGS="ipdb:<id>"`)
-- and authors or dismisses -- never re-judges.
CREATE OR REPLACE VIEW lineage_parked_0128 AS
  SELECT
    s.ipdb_id,
    s.model_slug,
    s.specialty_asserts,
    j.disposition,
    j.verdict,
    j.relationship_type AS judged_type,
    j.license_status    AS judged_license,
    j.target_title,
    j.target_maker,
    j.target_year,
    j.target_label,
    j.resolved_slug,
    j.resolution_how,
    j.quote,
    j.quote_verified,
    'https://www.ipdb.org/machine.cgi?id=' || s.ipdb_id AS ipdb_url
  FROM (SELECT ipdb_id, model_slug,
               list_sort(list(relationship_type)) AS specialty_asserts
        FROM lineage_scope GROUP BY ipdb_id, model_slug) AS s
  INNER JOIN _lineage_0128_rows AS j USING (ipdb_id);

-- == 4 · THE HAND-PASS ADJUDICATIONS ========================================

-- HUMAN JUDGMENT over the parked verdicts, made checkable -- one row per edge the
-- patch asserts, written after vetting each 0128 verdict against the FULL note
-- (`make show-source`). Every `quote` here passed `--check` verbatim before being
-- recorded. `why` is the adjudication note, kept beside the decision rather than in
-- a review document nothing gates on.
--
-- The recurring calls, so the table reads without the notes open:
--
--   TYPE follows the note's own wording where it and the census heading diverge
--   (`conversion of` vs the `Conversion Kit` specialty on the four Italian
--   conversions): the prose is per-machine evidence, the heading is a census grain.
--   The divergence is deliberate and lands those models in the deferred
--   `other_type_edge` class, where the mistyped-or-second-edge question belongs.
--
--   LICENSE is `unknown` on every row: an IPDB note establishes the conversion,
--   never the authorization (0128's standing rule).
--
--   HOMONYM DONORS resolve by feasibility: a 1970 Dama EM kit cannot target a 1937
--   or 1949 flipperless `Bazaar` or a 1976 `Rancho`, leaving exactly the 1966
--   machines; bare IPDB names mean the non-`(Italy)` listing (the Western note
--   demonstrates the convention by spelling out "or perhaps also ... 'Subway
--   (Italy)'" when it means both -- that hedged second donor stays unauthored).
--
--   AN either/or OR UNIDENTIFIED DONOR becomes a `target_label` in the note's own
--   words, never a guessed machine (the coal-town disjunction, the six unknowns).
CREATE OR REPLACE TABLE _lineage_adjudications (
  ipdb_id         BIGINT,
  model_slug      VARCHAR,
  relationship_type VARCHAR,
  target_machine  VARCHAR,
  target_label    VARCHAR,
  license_status  VARCHAR,
  quote           VARCHAR,
  why             VARCHAR
);
INSERT INTO _lineage_adjudications VALUES
  (3471, 'top-pin', 'conversion_kit', NULL, 'some Bally game', 'unknown',
   'furthering an idea that Top Pin is a conversion kit of some Bally game',
   'donor hedged in the note; the kit itself is the specialty''s own assertion'),
  (4066, 'western-2', 'conversion', 'subway-2', NULL, 'unknown',
   'The undated magazine ad shown here indicates that this game is a conversion of Gottlieb''s 1966 ''Subway''',
   'bare name = the non-Italy listing; "perhaps also Subway (Italy)" is hedged and stays unauthored'),
  (4072, 'summer-time-4', 'conversion', 'hit-a-card', NULL, 'unknown',
   'this game is a conversion of both Gottlieb''s 1967 ''Hit-A-Card'' and Gottlieb''s 1967 ''Solitaire''',
   'and-joined donors: two edges, one quote'),
  (4072, 'summer-time-4', 'conversion', 'solitaire', NULL, 'unknown',
   'this game is a conversion of both Gottlieb''s 1967 ''Hit-A-Card'' and Gottlieb''s 1967 ''Solitaire''',
   'and-joined donors: two edges, one quote'),
  (4397, 'bookmakers', 'conversion_kit', 'bazaar-2', NULL, 'unknown',
   'Conversion kit for Bazaar',
   'feasibility pick: Bally 1966, against a 1937 and a 1949 flipperless machine'),
  (4400, 'hippy', 'conversion_kit', 'ice-show', NULL, 'unknown',
   'Conversion kit for Ice Show',
   'bare name = the non-Italy listing, per the Western note''s convention'),
  (4403, 'road', 'conversion_kit', 'rancho-2', NULL, 'unknown',
   'Conversion kit for Rancho',
   'feasibility pick: Gottlieb 1966, against a 1948 one-ball and a 1976 machine'),
  (4812, 'lucky-double', 'conversion', 'gold-cup', NULL, 'unknown',
   'The backglass in each instance is a conversion of Bally''s 1948 ''Gold Cup'' probably renamed to remove this game from a no-operate list.',
   'the one firmly named donor; the note''s playfield/cabinet hedges stay in the note'),
  (4853, 'single-coin-2', 'conversion', 'barrel-o-fun', NULL, 'unknown',
   'This game is a conversion of Bally''s 1960 ''Barrel O’ Fun''',
   'firm; 0128''s quote-unverified was the curly apostrophe, which now verifies'),
  (4990, 'top-hand-4', 'conversion', 'top-hand-2', NULL, 'unknown',
   'This is a conversion of Gottlieb''s 1973 ''Top Hand''.',
   '0128''s one green fill, finally authored'),
  (5002, 'kiss-2', 'conversion', 'space-orbit', NULL, 'unknown',
   'A source indicates that this is a conversion of Gottlieb''s 1972 ''Space Orbit''.',
   'source-attributed but unrebutted, and the specialty affirms the relationship'),
  (5033, 'southside-johnny-and-the-asbury-jukes', 'conversion', 'star-trek-bally', NULL, 'unknown',
   'this game is a conversion of Bally''s 1979 ''Star Trek''',
   'firm; the note''s second image confirms an unchanged Star Trek playfield and cabinet'),
  (5098, 'coal-town', 'conversion', NULL, 'Bally''s 1948 ''Citation'' or Bally''s 1948 ''Lexington''', 'unknown',
   'This is a backglass conversion of either Bally''s 1948 ''Citation'' or Bally''s 1948 ''Lexington'', depending on if its cabinet has the payout mechanism in it.',
   'either/or is one unknown donor, not two: a label, never both edges'),
  (5115, 'tanforan', 'conversion', 'champion-4', NULL, 'unknown',
   'This game has no payout mechanism and is a conversion of Bally''s 1949 ''Champion''.',
   'firm; the Citation front door is a parts note, not a second donor'),
  (5150, 'tommy', 'conversion', NULL, 'a Stoner game, possibly Stoner''s 1938 ''Chubbie''', 'unknown',
   'This looks like a conversion of a Stoner game, possibly Stoner''s 1938 ''Chubbie''.',
   'hedged donor -- and IPDB itself holds two identical Stoner 1938 Chubbie listings'),
  (5379, 'last-round', 'conversion_kit', NULL, 'a Gottlieb game', 'unknown',
   'This was described to us as a conversion kit for a Gottlieb game.',
   'the header''s own example of a correct label edge'),
  (5738, 's-joao', 'conversion', 'carnival-3', NULL, 'unknown',
   'It has been reported that this 4-player "S. João" is a conversion of the 2-player Playmatic''s 1977 ''Carnival''.',
   'reported, unconfirmed by IPDB -- but the specialty affirms it and the Irmacor import-conversion pattern is established (0143)'),
  (6238, 'handicap-5', 'conversion', NULL, 'an unknown game', 'unknown',
   'This is a conversion of an unknown game.',
   'the note''s own firm words; the Williams attribution sits behind "if we correctly understand the French text" and stays in the note'),
  (6329, 'having-fun', 'conversion', NULL, 'an unknown Bally bingo game', 'unknown',
   'Conversion of an unknown Bally bingo game.',
   'firm label, verbatim'),
  (6743, 'hold-your-horses', 'conversion', NULL, 'an unidentified Bally horserace game', 'unknown',
   'we list this unique and apparently amalgamated non-payout game as a Converted Game done by an unknown company or person(s)',
   'IPDB''s considered conclusion on the amalgam; the Victory Special serial tag stays a note-level fact'),
  (6752, 'moderne', 'conversion', NULL, 'an unknown game', 'unknown',
   'Conversion of an unknown game.',
   'firm label, verbatim');

-- What gen.py emits: adjudicated edges the catalog does not yet carry. The
-- already-carried filter is what keeps this view (and the checks below) correct on
-- BOTH sides of the apply: before it, every row is pending; after it, the view
-- reads back empty and nothing fires.
CREATE OR REPLACE VIEW lineage_patch_rows AS
  SELECT a.*
  FROM _lineage_adjudications AS a
  INNER JOIN models AS m ON m.slug = a.model_slug
  WHERE NOT EXISTS (SELECT 1 FROM model_edges AS e
                    WHERE e.model_id = m.id
                      AND e.relationship_type = a.relationship_type
                      AND (a.target_machine IS NOT DISTINCT FROM e.target_slug
                           OR (a.target_label IS NOT NULL AND e.target_label IS NOT NULL)));


-- == 4b · THE SWEEP FILLS, VETTED ===========================================

-- Models held back from the fill patch for the escalation pass: their evidence is
-- multi-part (donor lists split across fill and escalated rows, hedged members,
-- unresolvable titles) and authoring only the greened fragment would state less
-- than the note does while looking complete.
CREATE OR REPLACE TABLE _lineage_fill_deferrals (ipdb_id BIGINT, model_slug VARCHAR, why VARCHAR);
INSERT INTO _lineage_fill_deferrals VALUES
  (876,  'flat-top',                  'donor list split across a label fill and two uncertain rows; wants machine edges authored as one unit'),
  (1418, 'laura',                     'the ad names 14 donors, two hedged between makers; a self-referential label understates it'),
  (2236, 'soft-ball-queens',          'same shape as laura: 12 named donors incl. an unknown Crystal and a conversion-of-a-conversion'),
  (6000, 'cherry-reel-football-board','the ad list mixes resolvable donors with unknowns and maker hedges; label wording needs the donors checked');

-- THE VETTED FILL EDGES -- the sweep''s green tier after the human pass, one row per
-- edge the fill patch asserts. Most rows are the judge''s answer verbatim; the vet
-- corrections, each argued from the full note:
--
--   GLICKMAN COHORT (10 models, one note template): "was a converted game for X",
--   then kit-only from June 1943. An edge''s identity is its machine target -- the
--   apply engine rejects a second member to the same target, whatever the type --
--   so each model carries ONE `conversion` edge to its donor (the note''s primary
--   fact; the kit phase stays a note-level fact), replacing the judge''s
--   inconsistent mix of label-vs-machine kit rows.
--
--   FRISCO is harmonized with OPPORTUNITY: the same flat ten-donor Gottlieb list,
--   authored the same way -- ten machine conversion edges, not one label.
--
--   MULTI-MEMBER ENTRIES carry the full list span as the one entry-level quote
--   (opportunity, frisco, best-bet), because a patch entry has a single cite and a
--   fragment naming one donor cannot support ten members.
--
--   LABEL REWORDS keep the note''s own words and drop editorial parentheticals
--   (mystic-star, silver-runway, beat-aces). double-feature-5 is retyped
--   conversion: "were used for this converted game" names a game, not a kit.
--   mandalay''s quote carries IPDB''s own revision sentence, which is where the
--   donor is named.
--
--   VICTORY GAMES kit typings (play-ball-6, sink-the-japs) were verified against
--   the full notes -- both say "this conversion kit" explicitly -- so the loose
--   first-sentence "conversion of" stays a kit.
--
-- License is `unknown` on every row (the fill gate asserts any other value against
-- the quote, and no note here establishes authorization); the checks pin that
-- against results.json rather than assuming it.
CREATE OR REPLACE TABLE _lineage_fill_edges (
  ipdb_id         BIGINT,
  model_slug      VARCHAR,
  relationship_type VARCHAR,
  target_machine  VARCHAR,
  target_label    VARCHAR,
  quote           VARCHAR
);
INSERT INTO _lineage_fill_edges VALUES
  (4909, '1776', 'conversion', 'show-boat-3', NULL, 'This game was modified from a Chicago Coin 1941 ''Show Boat'' for use in the 1948 motion picture titled "The Time of Your Life".'),
  (6003, '1942-bowling-alley', 'conversion', 'bowling-alley', NULL, '''1942 Bowling Alley'' is a converted game for Gottlieb''s 1939 ''Bowling Alley''.'),
  (5705, '45-derby', 'conversion', '41-derby', NULL, 'Wartime conversion of Bally''s 1941 ''41-Derby'' with new paint and new playfield.'),
  (3840, 'all-out', 'conversion', 'cross-line', NULL, '`All Out'' was a conversion of Bally''s `Cross Line'' of 1941'),
  (3857, 'archery', 'conversion', 'cadillac', NULL, '''Archery'' was a converted game for Genco''s 1940 ''Cadillac''.'),
  (811, 'arlington-2', 'conversion', 'fairmont', NULL, 'World War II conversion from Bally''s `Fairmont''.'),
  (3876, 'arrow', 'conversion', 'cadillac', NULL, '‘Arrow’ was a conversion of Genco''s 1940 ''Cadillac''.'),
  (5056, 'baseball-12', 'conversion_kit', NULL, 'existing machines', 'Game was advertised in May, 1932 as a 15-inch by 30-inch conversion playfield delivered a little long on three sides for trimming by operator to fit existing machines.'),
  (4895, 'beat-aces', 'conversion_kit', NULL, 'Exhibit''s Lightning, Electro, Golden Gate, and Drop Kick', 'This was a replacement playfield for the following games made by Exhibit Manufacturing: Lightning, Electro, Golden Gate, and Drop Kick.'),
  (5592, 'best-bet', 'conversion', 'club-trophy', NULL, 'this is a conversion of these games: Bally''s 1942 ''Longacres'' possibly Bally''s 1941 ''41-Derby'' Bally''s 1941 ''Club Trophy'' Whirlaway (either Victory Sales'' 1943 ''Whirlaway'' or Roy McGinnis'' 1943 ''Whirlaway'') Roy McGinnis'' 1944 ''Dust Whirls'' Bally''s 1946 ''Victory Special'' Pimlico (either Bally''s 1941 ''Pimlico'' or Victory Sales'' 1946 ''Pimlico'') Victory Sales'' 1946 ''Thorobreds'''),
  (5592, 'best-bet', 'conversion', 'dust-whirls', NULL, 'this is a conversion of these games: Bally''s 1942 ''Longacres'' possibly Bally''s 1941 ''41-Derby'' Bally''s 1941 ''Club Trophy'' Whirlaway (either Victory Sales'' 1943 ''Whirlaway'' or Roy McGinnis'' 1943 ''Whirlaway'') Roy McGinnis'' 1944 ''Dust Whirls'' Bally''s 1946 ''Victory Special'' Pimlico (either Bally''s 1941 ''Pimlico'' or Victory Sales'' 1946 ''Pimlico'') Victory Sales'' 1946 ''Thorobreds'''),
  (5592, 'best-bet', 'conversion', 'longacres-2', NULL, 'this is a conversion of these games: Bally''s 1942 ''Longacres'' possibly Bally''s 1941 ''41-Derby'' Bally''s 1941 ''Club Trophy'' Whirlaway (either Victory Sales'' 1943 ''Whirlaway'' or Roy McGinnis'' 1943 ''Whirlaway'') Roy McGinnis'' 1944 ''Dust Whirls'' Bally''s 1946 ''Victory Special'' Pimlico (either Bally''s 1941 ''Pimlico'' or Victory Sales'' 1946 ''Pimlico'') Victory Sales'' 1946 ''Thorobreds'''),
  (5592, 'best-bet', 'conversion', 'victory-special', NULL, 'this is a conversion of these games: Bally''s 1942 ''Longacres'' possibly Bally''s 1941 ''41-Derby'' Bally''s 1941 ''Club Trophy'' Whirlaway (either Victory Sales'' 1943 ''Whirlaway'' or Roy McGinnis'' 1943 ''Whirlaway'') Roy McGinnis'' 1944 ''Dust Whirls'' Bally''s 1946 ''Victory Special'' Pimlico (either Bally''s 1941 ''Pimlico'' or Victory Sales'' 1946 ''Pimlico'') Victory Sales'' 1946 ''Thorobreds'''),
  (3875, 'big-three-2', 'conversion', '1-2-3', NULL, 'A conversion of Mills'' 1940 ''"1 2 3"'''),
  (3846, 'bombardier-2', 'conversion', 'formation', NULL, '`Bombardier'' was a conversion of Genco''s `Formation'''),
  (5563, 'broadway-5', 'conversion_kit', NULL, 'unspecified games', 'This is a conversion kit for unspecified games.'),
  (4857, 'cherry-picker', 'conversion', 'sea-island', NULL, 'This game was created in 1963 by R. P. Hilleirich and derived from a Bally 1959 ''Sea Island'' but with an overpainted playfield and backglass.'),
  (3858, 'combat-2', 'conversion', 'leader', NULL, '''Combat'' was a converted game for Exhibit''s 1940 ''Leader''.'),
  (6103, 'combination-recreation-board', 'conversion_kit', NULL, 'billiard tables', 'This board is placed at one end of a billiard table surface to convert it to a carombolette table.'),
  (4527, 'daily-races-2', 'conversion', 'jockey-club-3', NULL, 'This game was a conversion of Bally''s 1941 Jockey Club.'),
  (6723, 'dark-shadow-conversion-kit', 'conversion_kit', 'dolly-parton', NULL, 'The example pictured here used Bally''s 1979 ''Dolly Parton'' as a source game.'),
  (714, 'double-feature-5', 'conversion', NULL, 'Bally games', 'One ad pictured here indicates only Bally games were used for this converted game.'),
  (3859, 'easy-pickin', 'conversion', 'oboy', NULL, 'Easy Pickin'' was a converted game for Chicago Coin''s 1939 ''O''Boy''.'),
  (3853, 'falling-suns', 'conversion', 'ten-spot', NULL, '`Falling Suns'' was a conversion of Genco''s `Ten Spot'''),
  (5727, 'figure-8-3', 'conversion_kit', NULL, 'a variety of unspecified games', 'The manufacturer indicated this game was sold as a replacement playfield for a variety of unspecified games while also sold as a complete game in a cabinet advertised as 31 inches long and 16 inches wide.'),
  (845, 'film-cavalcade', 'conversion', 'manhattan', NULL, '''Film Cavalcade'' is a flipper conversion of the flipperless United''s 1948 ''Manhattan''.'),
  (3854, 'flying-tigers', 'conversion', 'play-ball', NULL, '`Flying Tigers` was a conversion of Bally''s `Play Ball'''),
  (956, 'frisco', 'conversion', 'a-b-c-bowler', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'belle-hop', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'horoscope', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'miami-beach', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'paradise-3', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'school-days', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'sea-hawk', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'spot-pool', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'the-champ', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (956, 'frisco', 'conversion', 'the-new-champ', NULL, '''Frisco'' is a World War II conversion of the following games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1941 ''The New Champ'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''A-B-C Bowler'''),
  (4791, 'high-boy', 'conversion', 'metro-2', NULL, '`Hi-Boy'' was a conversion of Genco''s `Metro'' of 1940'),
  (1505, 'madame-butterfly', 'conversion', 'singapore', NULL, '''Madam Butterfly'' was a conversion of United''s 1947 flipperless game Singapore.'),
  (3384, 'mandalay', 'conversion_kit', 'trade-winds', NULL, 'We previously listed ''Mandalay'' as a converted game for Genco''s 1948 ''Trade Winds'' but a Billboard ad shown here identifies Mandalay as Schneller''s first conversion kit'),
  (4813, 'movie', 'conversion', 'pinball-champ', NULL, 'The playfield is that of ''Pinball Champ'' by Zaccaria.'),
  (3375, 'mystic-star', 'conversion_kit', NULL, 'machines using a Bally -35 MPU board set', 'A conversion kit, was shipped as a complete game, less circuit boards. Uses a Bally -35 MPU board set.'),
  (3862, 'nine-bells', 'conversion', 'mr-chips', NULL, '''Nine Bells'' was a converted game for Genco''s 1939 ''Mr. Chips''.'),
  (4792, 'nite-club', 'conversion', 'formation', NULL, '`Nite Club'' was a conversion of Genco''s `Formation'' of 1940'),
  (1723, 'opportunity', 'conversion', 'a-b-c-bowler', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'belle-hop', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'horoscope', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'miami-beach', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'paradise-3', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'school-days', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'sea-hawk', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'spot-pool', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'the-champ', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (1723, 'opportunity', 'conversion', 'the-new-champ', NULL, '''Opportunity'' is a conversion of these games:  Gottlieb''s 1940 ''The Champ'' Gottlieb''s 1940 ''Paradise'' Gottlieb''s 1941 ''Sea Hawk'' Gottlieb''s 1941 ''Horoscope'' Gottlieb''s 1941 ''School Days'' Gottlieb''s 1941 ''Belle Hop'' Gottlieb''s 1941 ''A-B-C Bowler'' Gottlieb''s 1941 ''Miami Beach'' Gottlieb''s 1941 ''Spot Pool'' Gottlieb''s 1941 ''The New Champ'''),
  (3865, 'peacherino', 'conversion', 'jolly', NULL, '''Peacherino'' was a converted game for Chicago Coin''s 1940 ''Jolly''.'),
  (1790, 'pin-up-girl', 'conversion', 'silver-skates-2', NULL, 'World War II conversion of Bally''s ''Silver Skates''.'),
  (3298, 'play-ball-6', 'conversion_kit', 'the-champ', NULL, '''Play Ball'' was a conversion of Gottlieb''s 1940 ''The Champ'' and Gottlieb''s 1941 ''The New Champ''.'),
  (3298, 'play-ball-6', 'conversion_kit', 'the-new-champ', NULL, '''Play Ball'' was a conversion of Gottlieb''s 1940 ''The Champ'' and Gottlieb''s 1941 ''The New Champ''.'),
  (1840, 'pokette', 'conversion_kit', 'ballyhoo-3', NULL, 'This is a replacement playfield for Bally''s 1932 ''Ballyhoo'' to be installed by the operator.'),
  (3847, 'production', 'conversion', 'blondie-2', NULL, '`Production'' was a conversion of Genco''s `Blondie''.'),
  (3866, 'red-heads-of-1942', 'conversion', 'blondie-2', NULL, '''Red Heads of 1942'' was a converted game for Genco''s 1940 ''Blondie''.'),
  (7037, 'retro-spa', 'conversion', 'future-spa', NULL, 'A narrow-body adaptation of the widebody game Bally''s 1979 ''Future Spa''.'),
  (3828, 'sailorettes', 'conversion', 'commodore', NULL, 'Sailorettes'' was a converted game for Chicago Coin''s 1939 ''Commodore''.'),
  (4530, 'sea-fair', 'retheme', 'big-show-2', NULL, 'This is a custom version of Bally''s 1956 ''Big Show'' and named for use during the annual Sea Fair festival held in Seattle, Washington.'),
  (4794, 'sea-power', 'conversion', 'four-roses', NULL, '`Sea Power'' was a conversion of Genco''s `Four Roses'' of 1940.'),
  (3337, 'shangrila', 'conversion', 'mr-chips', NULL, '''Shangri-La'' is a conversion of Genco''s 1939 ''Mr. Chips''.'),
  (3247, 'silver-runway', 'conversion_kit', NULL, 'other manufacturer''s games', 'This is a conversion playfield, meant to fit other manufacturer''s games.'),
  (3829, 'sink-the-japs', 'conversion_kit', 'seven-up', NULL, '''Sink the Japs'' was a conversion of Genco''s 1941 ''Seven Up''.'),
  (3867, 'sixty-grand', 'conversion', 'big-town', NULL, '''Sixty Grand'' was a converted game for Genco''s 1940 ''Big Town''.'),
  (3855, 'sky-rider-2', 'conversion', 'pan-american', NULL, '`Sky Rider'' was a conversion of Bally''s `Pan American'''),
  (3838, 'torpedo-patrol', 'conversion', 'formation', NULL, '`Torpedo Patrol'' was a conversion of Genco''s `Formation'''),
  (5284, 'treasure', 'conversion', 'skipper-2', NULL, 'Conversion of Bally''s 1937 ''Skipper''.'),
  (3870, 'triple-play-3', 'conversion', 'home-run-1940', NULL, '''Triple Play'' was a converted game for Chicago Coin''s 1940 ''Home Run 1940''.');

-- What gen_fills.py emits: vetted fill edges the catalog does not yet carry, on the
-- same both-sides-of-the-apply footing as lineage_patch_rows.
CREATE OR REPLACE VIEW lineage_fill_patch_rows AS
  SELECT a.*
  FROM _lineage_fill_edges AS a
  INNER JOIN models AS m ON m.slug = a.model_slug
  WHERE NOT EXISTS (SELECT 1 FROM model_edges AS e
                    WHERE e.model_id = m.id
                      AND e.relationship_type = a.relationship_type
                      AND (a.target_machine IS NOT DISTINCT FROM e.target_slug
                           OR (a.target_label IS NOT NULL AND e.target_label IS NOT NULL)));


-- == 4c · THE ESCALATIONS, ADJUDICATED ======================================

-- HUMAN JUDGMENT over the sweep's 98 review rows, one decision per model, each made
-- from the FULL note. The recurring calls, extending the rules sections 4 and 4b
-- established:
--
--   AND-LISTS become machine edges, one per named donor (all-american-derby,
--   challenger-5, eagle-squadron, invasion, whirlaway-2, the Williams and Munves
--   donor lists...). OR-LISTS become one label in the note''s words (derby-king-2''s
--   "any of these three", sportsman-3, war-admiral, whirlaway) -- the coal-town
--   rule: an either/or is one unknown donor, never several asserted ones.
--
--   MAKER-TOKEN GATE ARTIFACTS are authored on their resolved targets: the verify
--   call read "Exhibit''s" against the catalog''s `esco` slug and balked
--   (american-beauty, jeep, spot-cha, sweethearts, de-icer-2''s "Success Game''s"
--   against Success Manufacturing''s "Red White & Blue"). The resolutions were
--   correct all along.
--
--   CATALOG TWINS -- two live listings a note''s wording cannot split (Lucky,
--   Fleet, Thistledowns, the two Sports models, the two Bally Turf Kings) -- take
--   a label naming the machine, not a coin-flip slug.
--
--   AN UNSEEDED DONOR takes a label carrying its name (Keeney''s ''Clover'',
--   Stoner''s ''Turf Champ''), per the campaign''s no-creation policy.
--
--   IPDB''S OWN REASONED "likely X" identifications are authored as machine edges
--   with the hedge riding in the quote (picture-parade, hit-the-deck-play-cards);
--   bare "may be" speculation is not (the Colonial 1932 listings take
--   "an unidentified game").
--
--   MIXED LISTS use the machine edges for firm members plus the model''s one label
--   slot for the hedged or unresolvable remainder (flat-top, laura,
--   soft-ball-queens, big-top, race-king, war-admiral-2, black-jack-4,
--   cherry-reel-football-board).
CREATE OR REPLACE TABLE _lineage_escalation_edges (
  ipdb_id         BIGINT,
  model_slug      VARCHAR,
  relationship_type VARCHAR,
  target_machine  VARCHAR,
  target_label    VARCHAR,
  quote           VARCHAR
);
INSERT INTO _lineage_escalation_edges VALUES
  (5385, 'a-circus', 'conversion', NULL, 'an unidentified game', 'This is listed as a conversion game in the Encyclopedia of Pinball Vol 1, but no mention of what game it converted.'),
  (5389, 'a-circus-2', 'conversion_kit', NULL, 'any machine', 'The ad shown here indicates "Our boards are made to fit any machine - can be installed in 15 minutes."'),
  (5418, 'all-american-derby', 'conversion', 'sport-event', NULL, 'A conversion of the free play versions of Bally''s 1940 ''Sport Special'' and Bally''s 1940 ''Sport Event''.'),
  (5418, 'all-american-derby', 'conversion', 'sport-special', NULL, 'A conversion of the free play versions of Bally''s 1940 ''Sport Special'' and Bally''s 1940 ''Sport Event''.'),
  (2872, 'american-beauty', 'conversion', 'attention', NULL, '`American Beauty'' was a conversion of Exhibit''s ''Attention'' of 1940'),
  (5451, 'american-beauty-4', 'conversion', 'attention-2', NULL, 'A conversion of Bally''s 1940 ''Attention'' and Bally''s 1940 ''Mascot''.'),
  (5451, 'american-beauty-4', 'conversion', 'mascot', NULL, 'A conversion of Bally''s 1940 ''Attention'' and Bally''s 1940 ''Mascot''.'),
  (191, 'baseball-6', 'conversion', NULL, 'an unknown game', 'World War II conversion'),
  (5061, 'beatem', 'conversion', NULL, 'Chicago Coin''s 1939 ''Lucky''', '''Beatem'' was a conversion of Chicago Coin''s 1939 ''Lucky''.'),
  (5592, 'best-bet', 'conversion', 'thorobreds', NULL, 'Victory Sales'' 1946 ''Thorobreds'''),
  (284, 'big-top', 'conversion', NULL, 'Keeney''s ''Clover''', 'advertised this game as a new revamp (conversion) of these games:  Keeney''s 1941 ''Twin Six'' Keeney''s ''Clover'' Keeney''s 1941 ''Sky Ray'''),
  (284, 'big-top', 'conversion', 'sky-ray', NULL, 'advertised this game as a new revamp (conversion) of these games:  Keeney''s 1941 ''Twin Six'' Keeney''s ''Clover'' Keeney''s 1941 ''Sky Ray'''),
  (284, 'big-top', 'conversion', 'twin-six', NULL, 'advertised this game as a new revamp (conversion) of these games:  Keeney''s 1941 ''Twin Six'' Keeney''s ''Clover'' Keeney''s 1941 ''Sky Ray'''),
  (4843, 'black-jack-4', 'conversion_kit', NULL, 'similar size machines', 'The ad states the playfield can be used to convert  Allswell''s 1932 ''Oh Yeah!'' Bally''s 1932 ''Ballyhoo'' Buckley Manufacturing Company''s 1932 ''Favorite'' Pierce Tool''s 1932 ''Hoop-Er-Doo'' and similar size machines.'),
  (4843, 'black-jack-4', 'conversion_kit', 'ballyhoo-3', NULL, 'The ad states the playfield can be used to convert  Allswell''s 1932 ''Oh Yeah!'' Bally''s 1932 ''Ballyhoo'' Buckley Manufacturing Company''s 1932 ''Favorite'' Pierce Tool''s 1932 ''Hoop-Er-Doo'' and similar size machines.'),
  (4843, 'black-jack-4', 'conversion_kit', 'favorite-2', NULL, 'The ad states the playfield can be used to convert  Allswell''s 1932 ''Oh Yeah!'' Bally''s 1932 ''Ballyhoo'' Buckley Manufacturing Company''s 1932 ''Favorite'' Pierce Tool''s 1932 ''Hoop-Er-Doo'' and similar size machines.'),
  (4843, 'black-jack-4', 'conversion_kit', 'hoop-er-doo', NULL, 'The ad states the playfield can be used to convert  Allswell''s 1932 ''Oh Yeah!'' Bally''s 1932 ''Ballyhoo'' Buckley Manufacturing Company''s 1932 ''Favorite'' Pierce Tool''s 1932 ''Hoop-Er-Doo'' and similar size machines.'),
  (4843, 'black-jack-4', 'conversion_kit', 'oh-yeah', NULL, 'The ad states the playfield can be used to convert  Allswell''s 1932 ''Oh Yeah!'' Bally''s 1932 ''Ballyhoo'' Buckley Manufacturing Company''s 1932 ''Favorite'' Pierce Tool''s 1932 ''Hoop-Er-Doo'' and similar size machines.'),
  (6981, 'bug-a-boo', 'conversion_kit', 'the-hunter-2', NULL, 'that flyer shown here was an offer from the manufacturer to sell Bug-A-Boo as an otherwise unadvertised conversion backglass for their game, ''The Hunter'', at a separate price'),
  (3884, 'challenger-5', 'conversion', 'blue-ribbon-3', NULL, '''Challenger'' was a conversion of Bally''s 1938 ''Sport Page'' and Bally''s 1939 ''Blue Ribbon''.'),
  (3884, 'challenger-5', 'conversion', 'sport-page', NULL, '''Challenger'' was a conversion of Bally''s 1938 ''Sport Page'' and Bally''s 1939 ''Blue Ribbon''.'),
  (6000, 'cherry-reel-football-board', 'conversion_kit', NULL, 'Lucky Star, Ballyhoo, Etzel and The Wizzard', 'This two-page ad advertises the replacement playfield to fit in the following games:  • Lucky Star Manufacturing Company''s 1932 ''Lucky Star'' • Ballyhoo (not sure whether Bally or Rock-ola) • Lucky Strike Manufacturing Company''s 1932 ''Lucky Strike'' (maybe also their Marble and Steel Ball versions) • Royal Novelty Company''s 1931 ''Jostle'' • Etzel (unknown) • The Wizzard (unknown, might be Eagle Sheet Metal Manufacturing Co.''s 1932 ''Wizard Ball Game'')'),
  (6000, 'cherry-reel-football-board', 'conversion_kit', 'jostle', NULL, 'This two-page ad advertises the replacement playfield to fit in the following games:  • Lucky Star Manufacturing Company''s 1932 ''Lucky Star'' • Ballyhoo (not sure whether Bally or Rock-ola) • Lucky Strike Manufacturing Company''s 1932 ''Lucky Strike'' (maybe also their Marble and Steel Ball versions) • Royal Novelty Company''s 1931 ''Jostle'' • Etzel (unknown) • The Wizzard (unknown, might be Eagle Sheet Metal Manufacturing Co.''s 1932 ''Wizard Ball Game'')'),
  (6000, 'cherry-reel-football-board', 'conversion_kit', 'lucky-strike-5', NULL, 'This two-page ad advertises the replacement playfield to fit in the following games:  • Lucky Star Manufacturing Company''s 1932 ''Lucky Star'' • Ballyhoo (not sure whether Bally or Rock-ola) • Lucky Strike Manufacturing Company''s 1932 ''Lucky Strike'' (maybe also their Marble and Steel Ball versions) • Royal Novelty Company''s 1931 ''Jostle'' • Etzel (unknown) • The Wizzard (unknown, might be Eagle Sheet Metal Manufacturing Co.''s 1932 ''Wizard Ball Game'')'),
  (3023, 'classic-2', 'conversion_kit', NULL, 'any machine', 'The ad shown here indicates "Our boards are made to fit any machine - can be installed in 15 minutes."'),
  (5384, 'classic-3', 'conversion', NULL, 'an unidentified game', 'This is listed as a conversion game in the Encyclopedia of Pinball Vol 1, but no mention of what game it converted.'),
  (3842, 'commander-2', 'conversion', NULL, 'Bally''s ''Fleet''', '`Commander'' was a conversion of Bally''s `Fleet'''),
  (4790, 'de-icer-2', 'conversion', 'red-white-blue', NULL, '`De-Icer'' was a conversion of Success Game''s `Red White Blue'' of 1941.'),
  (669, 'derby-king-2', 'conversion', NULL, 'any of Bally''s 1940 ''Sport King'', Bally''s 1940 ''Long Shot'' or Bally''s 1941 ''Kentucky''', '''Derby King'' is a conversion of any of these three games: Bally''s 1940 ''Sport King'' Bally''s 1940 ''Long Shot'' Bally''s 1941 ''Kentucky'''),
  (3834, 'eagle-squadron', 'conversion', 'big-league', NULL, '''Eagle Squadron'' was a conversion of Genco''s 1940 ''Big League'' and Genco''s 1940 ''Big Town''.'),
  (3834, 'eagle-squadron', 'conversion', 'big-town', NULL, '''Eagle Squadron'' was a conversion of Genco''s 1940 ''Big League'' and Genco''s 1940 ''Big Town''.'),
  (3833, 'fast-track', 'conversion', 'blue-ribbon-3', NULL, '''Fast Track'' was a conversion of Bally''s 1938 ''Sport Page'' and Bally''s 1939 ''Blue Ribbon''.'),
  (3833, 'fast-track', 'conversion', 'sport-page', NULL, '''Fast Track'' was a conversion of Bally''s 1938 ''Sport Page'' and Bally''s 1939 ''Blue Ribbon''.'),
  (876, 'flat-top', 'conversion', NULL, 'Bally''s 1940 ''Attention'' (or maybe Exhibit''s)', 'it was a conversion of this game: Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'')  Then, a pictureless manufacturer ad in BB 04/21/1945 p76 announced the following games were also used for this conversion: Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Silver Skates''  Finally, a pictureless manufacturer ad in BB 06/16/1945 p82 announced "now 4 more games" were also used for this conversion: Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Pan-American'' Bally''s ''Crystal'''),
  (876, 'flat-top', 'conversion', 'air-force', NULL, 'it was a conversion of this game: Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'')  Then, a pictureless manufacturer ad in BB 04/21/1945 p76 announced the following games were also used for this conversion: Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Silver Skates''  Finally, a pictureless manufacturer ad in BB 06/16/1945 p82 announced "now 4 more games" were also used for this conversion: Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Pan-American'' Bally''s ''Crystal'''),
  (876, 'flat-top', 'conversion', 'crystal', NULL, 'it was a conversion of this game: Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'')  Then, a pictureless manufacturer ad in BB 04/21/1945 p76 announced the following games were also used for this conversion: Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Silver Skates''  Finally, a pictureless manufacturer ad in BB 06/16/1945 p82 announced "now 4 more games" were also used for this conversion: Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Pan-American'' Bally''s ''Crystal'''),
  (876, 'flat-top', 'conversion', 'mascot', NULL, 'it was a conversion of this game: Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'')  Then, a pictureless manufacturer ad in BB 04/21/1945 p76 announced the following games were also used for this conversion: Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Silver Skates''  Finally, a pictureless manufacturer ad in BB 06/16/1945 p82 announced "now 4 more games" were also used for this conversion: Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Pan-American'' Bally''s ''Crystal'''),
  (876, 'flat-top', 'conversion', 'mystic-3', NULL, 'it was a conversion of this game: Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'')  Then, a pictureless manufacturer ad in BB 04/21/1945 p76 announced the following games were also used for this conversion: Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Silver Skates''  Finally, a pictureless manufacturer ad in BB 06/16/1945 p82 announced "now 4 more games" were also used for this conversion: Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Pan-American'' Bally''s ''Crystal'''),
  (876, 'flat-top', 'conversion', 'pan-american', NULL, 'it was a conversion of this game: Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'')  Then, a pictureless manufacturer ad in BB 04/21/1945 p76 announced the following games were also used for this conversion: Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Silver Skates''  Finally, a pictureless manufacturer ad in BB 06/16/1945 p82 announced "now 4 more games" were also used for this conversion: Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Pan-American'' Bally''s ''Crystal'''),
  (876, 'flat-top', 'conversion', 'pursuit', NULL, 'it was a conversion of this game: Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'')  Then, a pictureless manufacturer ad in BB 04/21/1945 p76 announced the following games were also used for this conversion: Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Silver Skates''  Finally, a pictureless manufacturer ad in BB 06/16/1945 p82 announced "now 4 more games" were also used for this conversion: Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Pan-American'' Bally''s ''Crystal'''),
  (876, 'flat-top', 'conversion', 'silver-skates-2', NULL, 'it was a conversion of this game: Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'')  Then, a pictureless manufacturer ad in BB 04/21/1945 p76 announced the following games were also used for this conversion: Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Silver Skates''  Finally, a pictureless manufacturer ad in BB 06/16/1945 p82 announced "now 4 more games" were also used for this conversion: Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Pan-American'' Bally''s ''Crystal'''),
  (6302, 'gateway', 'conversion', NULL, 'an unidentified game', 'The Encyclopedia of Pinball Vol 2 lists Gateway as a converted game but the source game is not identified.'),
  (6729, 'high-stepper', 'conversion', 'bally-entry', NULL, 'A conversion of Bally''s 1947 ''Bally Entry'' and Bally''s 1947 ''Special Entry''.'),
  (6729, 'high-stepper', 'conversion', 'special-entry', NULL, 'A conversion of Bally''s 1947 ''Bally Entry'' and Bally''s 1947 ''Special Entry''.'),
  (4923, 'hit-the-deck-play-cards', 'conversion', 'bingo-play-cards', NULL, 'Per the  Encyclopedia of Pinball Vol 1, this is a converted game, likely that of Bingo Novelty Manufacturing Company''s 1932 ''Bingo Play Cards''.'),
  (5065, 'home-run-44', 'conversion', NULL, 'a game called ''Home Run''', '''Home Run ‘44'' was a conversion of a game called ''Home Run''.'),
  (6807, 'hullabaloo', 'conversion_kit', NULL, 'Baffle Ball, Bingo and six other early-1930s games', 'This was advertised as a replacement playfield for the following games:  Baffle Ball (possibly any of several) Bingo (possibly any of several) Bingo Planet (likely ''Planet Ball'') Golden Comet Hit the Deck (likely ''Hit The Deck Play Cards'') Lucky Strike Joy Game (likely this one: ''The Joy Game'') Play Boy (likely this one: ''Play-Boy'') Spot-A-Ball (likely ''Spot A Ball'')'),
  (1269, 'invasion', 'conversion', 'seven-up', NULL, '''Invasion'' was a conversion of Genco''s 1941 ''Seven Up'' and Genco''s 1941 ''Sluggers''.'),
  (1269, 'invasion', 'conversion', 'sluggers', NULL, '''Invasion'' was a conversion of Genco''s 1941 ''Seven Up'' and Genco''s 1941 ''Sluggers''.'),
  (3843, 'jeep', 'conversion', 'duplex', NULL, '`Jeep'' was a conversion of Exhibit''s `Duplex'''),
  (5387, 'jiggilo-2', 'conversion', NULL, 'an unidentified game', 'This is listed as a conversion game in the Encyclopedia of Pinball Vol 1, but no mention of what game it converted.'),
  (5390, 'jiggilo-3', 'conversion_kit', NULL, 'an unidentified game', 'it''s possible that this December 1932 conversion kit was Ace''s initial response to the injunction, to address their "Who''s Goofy" games that they had sold prior to the injunction'),
  (1384, 'kismet', 'conversion', NULL, 'an unknown game', 'World War II conversion.'),
  (1401, 'lariat', 'conversion', 'nevada-2', NULL, '`Lariat'' is a conversion of United''s `Nevada''.'),
  (1418, 'laura', 'conversion_kit', NULL, 'Bally''s 1940 ''Attention'' (or maybe Exhibit''s)', 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'air-force', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'broadcast', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'cross-line', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'crystal', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'flicker-2', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'mascot', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'mystic-3', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'pan-american', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'play-ball', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'pursuit', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'silver-skates-2', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'speed-ball', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1418, 'laura', 'conversion_kit', 'trailways', NULL, 'According to a magazine ad pictured here, the following games could be converted to become ''Laura'':  Bally''s 1940 ''Attention'' (or maybe Exhibit''s 1940 ''Attention'') Bally''s 1940 ''Mascot'' Bally''s 1941 ''Air Force'' Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Cross-Line'' Bally''s 1941 ''Flicker'' Bally''s 1941 ''Mystic'' (or, less likely, Pacific Manufacturing Corporation''s 1937 ''Mystic'') Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Play Ball'' Bally''s 1941 ''Pursuit'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Speed Ball'' Bally''s 1941 ''Trailways'' Bally''s ''Crystal'''),
  (1706, 'old-hilltop', 'conversion', 'winner-5', NULL, 'General Vending Sales Corporation, a distributor, converted Universal Industries'' 1950 ''Winner'' into ''Old Hilltop''.'),
  (1766, 'pastime-2', 'conversion', NULL, 'Stoner''s ''Turf Champ''', '`Pastime'' was a conversion of Stoner''s `Turf Champ'''),
  (4773, 'picture-parade', 'conversion', 'lady-robin-hood', NULL, 'Schneller''s 1949 and 1950 ads indicate this game is a conversion of ''Robin Hood'' but this is likely a reference to the recent Gottlieb''s 1948 ''Lady Robin Hood'''),
  (5299, 'poko-lite', 'conversion', 'bumper', NULL, 'Conversion of Bally''s 1936 ''Bumper'' and Bally''s 1937 ''Skipper''.'),
  (5299, 'poko-lite', 'conversion', 'skipper-2', NULL, 'Conversion of Bally''s 1936 ''Bumper'' and Bally''s 1937 ''Skipper''.'),
  (6256, 'profit-sharer', 'conversion_kit', NULL, 'non-payout pinball machines', 'is a "Jack Pot Attachment" for the front of the pinball cabinet to convert non-payout pinball machines to payout.'),
  (3832, 'race-king', 'conversion', NULL, 'Bally''s 1938 ''Thistledowns''', '''Race King'' was a conversion of these games: Bally''s 1938 ''Seabiscuit'' Bally''s 1938 ''Thistledowns'''),
  (3832, 'race-king', 'conversion', 'seabiscuit', NULL, '''Race King'' was a conversion of these games: Bally''s 1938 ''Seabiscuit'' Bally''s 1938 ''Thistledowns'''),
  (6943, 'rocket-buster', 'conversion', NULL, 'an unidentified gun game', 'Conversion of another gun game that we have not yet identified.'),
  (6823, 'scout', 'conversion_kit', 'harmony', NULL, 'a kit made in 1970-1972 for Gottlieb''s 1967 ''Harmony'' and Gottlieb''s 1967 ''Troubadour'''),
  (6823, 'scout', 'conversion_kit', 'troubadour', NULL, 'a kit made in 1970-1972 for Gottlieb''s 1967 ''Harmony'' and Gottlieb''s 1967 ''Troubadour'''),
  (2236, 'soft-ball-queens', 'conversion', NULL, 'Crystal (unknown game)', 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'attention-2', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'broadcast', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'charm', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'cross-line', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'flicker-2', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'marines-at-play-1st-edition', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'mascot', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'mystic-3', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'pan-american', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'silver-skates-2', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (2236, 'soft-ball-queens', 'conversion', 'vacation', NULL, 'Munves advertised that the following games could be used for this conversion, which included replacing the playfield: Bally''s 1941 ''Broadcast'' Bally''s 1941 ''Pan-American'' Bally''s 1941 ''Mystic'' Bally''s 1941 ''Silver Skates'' Bally''s 1941 ''Cross-Line'' Bally''s 1940 ''Vacation'' Crystal (unknown game) Westerhaus Amusement Co.''s 1944 ''Marines At Play (1st Edition)'' (itself a conversion) Bally''s 1940 ''Attention'' Bally''s 1940 ''Charm'' Bally''s 1940 ''Mascot'' Bally''s 1941 ''Flicker'''),
  (5256, 'space-duel', 'conversion', NULL, 'an unidentified game', 'The Pinball Collectors Resource - Millenium Edition lists this game as a conversion.'),
  (2308, 'sportsman-3', 'conversion', NULL, 'Bally''s ''Blue Grass'', ''Dark Horse'', ''Sport Special'', or ''Sport Event''', '`Sportsman'' was a conversion of Bally''s `Blue Grass'', `Dark Horse'', `Sport Special'', or `Sport Event'''),
  (2319, 'spot-cha', 'conversion', 'attention', NULL, 'World War II conversion of Exhibit''s ''Attention''.'),
  (3868, 'starlight', 'conversion', 'triumph-model-1', NULL, '''Starlight'' was a converted game for Bally''s 1940 ''Triumph (Model 1)''.'),
  (3750, 'strip-tease', 'conversion', NULL, 'Chicago Coin''s 1939 ''Sports'' (Model 69 and/or Model 70)', '''Strip Tease'' was a wartime conversion of Chicago Coin''s 1939 ''Sports'' (Model 69) and/or Chicago Coin''s 1939 ''Sports'' (Model 70).'),
  (6349, 'super-wall-street', 'conversion_kit', 'bali', NULL, 'Reportedly, this is a backglass issued by Bally for converting Bally''s 1974 ''Bali'' to a new game name.'),
  (5074, 'swat-king', 'conversion', NULL, 'a game called ''Play Ball''', '''Swat King'' was a conversion of a game called ''Play Ball''.'),
  (3869, 'sweethearts', 'conversion', 'stars-2', NULL, '''Sweethearts'' was a converted game for Exhibit''s 1941 ''Stars''.'),
  (5662, 'triumph', 'conversion', NULL, 'one or more other games', 'The ad indicates this game is a conversion of one or more other games.'),
  (4037, 'turf-course', 'conversion_kit', NULL, 'a Bally ''Turf King''', 'Probably a conversion backglass for a Bally''s `Turf King".'),
  (3851, 'war-admiral', 'conversion', NULL, 'Bally''s ''Grand Stand'', ''Grand National'' or ''Pace Maker''', '`War Admiral'' was a conversion of Bally''s `Grand Stand'', `Grand National'' or `Pace Maker''.'),
  (4052, 'war-admiral-2', 'conversion', NULL, 'Bally''s 1938 and/or 1939 ''Pace Maker''', 'War Admiral'' was a conversion of these games: Bally''s 1938 ''Grandstand'' Bally''s 1938 ''Pace Maker'' and/or Bally''s 1939 ''Pace Maker'' Bally''s 1939 ''Grand National'''),
  (4052, 'war-admiral-2', 'conversion', 'grand-national', NULL, 'War Admiral'' was a conversion of these games: Bally''s 1938 ''Grandstand'' Bally''s 1938 ''Pace Maker'' and/or Bally''s 1939 ''Pace Maker'' Bally''s 1939 ''Grand National'''),
  (4052, 'war-admiral-2', 'conversion', 'grandstand-2', NULL, 'War Admiral'' was a conversion of these games: Bally''s 1938 ''Grandstand'' Bally''s 1938 ''Pace Maker'' and/or Bally''s 1939 ''Pace Maker'' Bally''s 1939 ''Grand National'''),
  (4997, 'wer-zahlt-die-runde', 'conversion', 'clipper-2', NULL, 'This game was a conversion for T.H. Bergmann & Co.''s 1957 ''Turf'' and T.H. Bergmann & Co.''s 1954 ''Clipper'', two of the more successful games from that manufacturer.'),
  (4997, 'wer-zahlt-die-runde', 'conversion', 'turf', NULL, 'This game was a conversion for T.H. Bergmann & Co.''s 1957 ''Turf'' and T.H. Bergmann & Co.''s 1954 ''Clipper'', two of the more successful games from that manufacturer.'),
  (3547, 'whirlaway', 'conversion', NULL, 'Bally''s ''Blue Grass'', ''Dark Horse'', or ''Sport Special''', '`Whirlaway'' was a conversion of Bally''s `Blue Grass'', `Dark Horse'', or `Sport Special''.'),
  (3848, 'whirlaway-2', 'conversion', 'blue-grass', NULL, '''Whirlaway'' was a conversion of these 1-player games:  Bally''s 1940 ''Sport Event'' Bally''s 1940 ''Sport Special'' Bally''s 1940 ''Record Time'' Bally''s 1940 ''Dark Horse'' Bally''s 1941 ''Blue Grass'''),
  (3848, 'whirlaway-2', 'conversion', 'dark-horse', NULL, '''Whirlaway'' was a conversion of these 1-player games:  Bally''s 1940 ''Sport Event'' Bally''s 1940 ''Sport Special'' Bally''s 1940 ''Record Time'' Bally''s 1940 ''Dark Horse'' Bally''s 1941 ''Blue Grass'''),
  (3848, 'whirlaway-2', 'conversion', 'record-time', NULL, '''Whirlaway'' was a conversion of these 1-player games:  Bally''s 1940 ''Sport Event'' Bally''s 1940 ''Sport Special'' Bally''s 1940 ''Record Time'' Bally''s 1940 ''Dark Horse'' Bally''s 1941 ''Blue Grass'''),
  (3848, 'whirlaway-2', 'conversion', 'sport-event', NULL, '''Whirlaway'' was a conversion of these 1-player games:  Bally''s 1940 ''Sport Event'' Bally''s 1940 ''Sport Special'' Bally''s 1940 ''Record Time'' Bally''s 1940 ''Dark Horse'' Bally''s 1941 ''Blue Grass'''),
  (3848, 'whirlaway-2', 'conversion', 'sport-special', NULL, '''Whirlaway'' was a conversion of these 1-player games:  Bally''s 1940 ''Sport Event'' Bally''s 1940 ''Sport Special'' Bally''s 1940 ''Record Time'' Bally''s 1940 ''Dark Horse'' Bally''s 1941 ''Blue Grass'''),
  (5386, 'whos-goofy-2', 'conversion', NULL, 'an unidentified game', 'This is listed as a conversion game in the Encyclopedia of Pinball Vol 1, but no mention of what game it converted.');

-- Escalated rows adjudicated to NO edge, with the reason on the record. A model
-- listed only here stays in the live worklist (its finding remains an expected
-- row) -- dismissal from this campaign is not adjudication in the layer''s
-- permanent sense.
CREATE OR REPLACE TABLE _lineage_escalation_dismissals (ipdb_id BIGINT, model_slug VARCHAR, why VARCHAR);
INSERT INTO _lineage_escalation_dismissals VALUES
  (5592, 'best-bet', 'hedged and either/or list members (possibly 41-Derby; a Whirlaway; a Pimlico) stay note-level beside the five firm edges'),
  (3858, 'combat-2', 'the escalated gate row duplicates the edge authored in 0300 (Exhibit = esco; the maker token tripped the verify call)'),
  (3869, 'sweethearts', 'kit row collapsed into the conversion edge: edge identity is the machine target, one edge per donor'),
  (5390, 'jiggilo-3', 'the copy row''s subject is Ace''s 1933 ''Jiggilo'', not this December 1932 kit listing'),
  (4795, 'cadillac-2', 'no IPDB prose at all; the census assertion stays a live worklist row until a source names a donor'),
  (3256, 'sky-chief-2', 'no IPDB prose at all; the census assertion stays a live worklist row until a source names a donor');

-- What gen_escalations.py emits, on the same both-sides-of-the-apply footing as
-- the other two patch_rows views.
CREATE OR REPLACE VIEW lineage_escalation_patch_rows AS
  SELECT a.*
  FROM _lineage_escalation_edges AS a
  INNER JOIN models AS m ON m.slug = a.model_slug
  WHERE NOT EXISTS (SELECT 1 FROM model_edges AS e
                    WHERE e.model_id = m.id
                      AND e.relationship_type = a.relationship_type
                      AND (a.target_machine IS NOT DISTINCT FROM e.target_slug
                           OR (a.target_label IS NOT NULL AND e.target_label IS NOT NULL)));

-- == 5 · SUMMARY & CHECKS ===================================================


CREATE OR REPLACE VIEW lineage_summary AS
  SELECT 'scope_rows' AS metric, count(*) AS value FROM lineage_scope
  UNION ALL SELECT 'scope_models', count(DISTINCT ipdb_id) FROM lineage_scope
  UNION ALL SELECT 'sweep_candidates', count(*) FROM lineage_sweep_candidates
  UNION ALL SELECT 'parked_0128_models', count(DISTINCT ipdb_id) FROM lineage_parked_0128
  UNION ALL SELECT 'parked_0128_rows', count(*) FROM lineage_parked_0128
  UNION ALL SELECT 'deferred_other_type_edge', count(*)
    FROM ipdb_model_relationships_missing WHERE classification = 'other_type_edge'
  UNION ALL SELECT 'deferred_edge_points_inward', count(*)
    FROM ipdb_model_relationships_missing WHERE classification = 'edge_points_inward'
  UNION ALL SELECT 'adjudicated_edges', count(*) FROM _lineage_adjudications
  UNION ALL SELECT 'adjudicated_models', count(DISTINCT ipdb_id) FROM _lineage_adjudications
  UNION ALL SELECT 'patch_rows_pending', count(*) FROM lineage_patch_rows
  UNION ALL SELECT 'fill_edges', count(*) FROM _lineage_fill_edges
  UNION ALL SELECT 'fill_models', count(DISTINCT ipdb_id) FROM _lineage_fill_edges
  UNION ALL SELECT 'fill_deferrals', count(*) FROM _lineage_fill_deferrals
  UNION ALL SELECT 'fill_patch_rows_pending', count(*) FROM lineage_fill_patch_rows
  UNION ALL SELECT 'escalation_edges', count(*) FROM _lineage_escalation_edges
  UNION ALL SELECT 'escalation_models', count(DISTINCT ipdb_id) FROM _lineage_escalation_edges
  UNION ALL SELECT 'escalation_dismissals', count(*) FROM _lineage_escalation_dismissals
  UNION ALL SELECT 'escalation_patch_rows_pending', count(*) FROM lineage_escalation_patch_rows;

CREATE OR REPLACE VIEW lineage_checks AS
  -- THE ROUTING PARTITION: every scope model goes to exactly one of the two routes.
  -- A model in neither is work silently dropped; a model in both is 0128's record
  -- being re-adjudicated by the sweep -- each the one thing its route exists to
  -- prevent.
  SELECT 'scope_model_unrouted' AS check_name, s.ipdb_id AS id, s.model_slug AS detail
  FROM (SELECT DISTINCT ipdb_id, model_slug FROM lineage_scope) AS s
  WHERE NOT EXISTS (SELECT 1 FROM lineage_sweep_candidates c WHERE c.ipdb_id = s.ipdb_id)
    AND NOT EXISTS (SELECT 1 FROM lineage_parked_0128 p WHERE p.ipdb_id = s.ipdb_id)
  UNION ALL
  SELECT 'candidate_also_parked', c.ipdb_id, c.model_slug
  FROM lineage_sweep_candidates AS c
  WHERE EXISTS (SELECT 1 FROM lineage_parked_0128 p WHERE p.ipdb_id = c.ipdb_id)
  UNION ALL
  -- FEED GRAIN: one candidate row per model, asserted rather than trusted to
  -- DISTINCT -- the next join added upstream is what this waits for.
  SELECT 'candidate_not_one_row_per_model', ipdb_id, count(*)::VARCHAR
  FROM lineage_sweep_candidates GROUP BY ipdb_id HAVING count(*) > 1
  UNION ALL
  -- DETECTOR GONE DARK: the exclusion contract rests on 0128's results file. If it
  -- moves or empties, the cut silently widens to "sweep everything" -- well-formed,
  -- paid for, and wrong.
  SELECT 'results_0128_unreadable', NULL::BIGINT,
         'campaigns/0128-relationships/sweep/results.json read back empty'
  FROM (SELECT count(*) AS n FROM _lineage_0128_rows) WHERE n = 0
  UNION ALL
  -- THE ADJUDICATION LEDGER, both directions, on both sides of the apply. A parked
  -- model with no adjudication is hand-pass work silently dropped. An adjudication
  -- is orphaned only when its model is neither still parked NOR carrying an
  -- adjudicated edge -- the state a wrong slug, a renamed model, or a reverted
  -- apply leaves behind. (Post-apply, parked empties and the carried test takes
  -- over, so neither side fires on healthy state.)
  SELECT 'parked_model_unadjudicated', p.ipdb_id, p.model_slug
  FROM (SELECT DISTINCT ipdb_id, model_slug FROM lineage_parked_0128) AS p
  WHERE NOT EXISTS (SELECT 1 FROM _lineage_adjudications a WHERE a.ipdb_id = p.ipdb_id)
  UNION ALL
  SELECT 'adjudication_orphaned', a.ipdb_id, a.model_slug
  FROM _lineage_adjudications AS a
  WHERE NOT EXISTS (SELECT 1 FROM lineage_parked_0128 p WHERE p.ipdb_id = a.ipdb_id)
    AND NOT EXISTS (SELECT 1 FROM models m JOIN model_edges e ON e.model_id = m.id
                    WHERE m.slug = a.model_slug
                      AND e.relationship_type = a.relationship_type)
  UNION ALL
  -- STRUCTURE the apply engine would reject anyway, caught where the fix is:
  -- exactly one target key, a machine target that resolves, a license always given.
  SELECT 'adjudication_target_xor_broken', ipdb_id, model_slug
  FROM _lineage_adjudications
  WHERE (target_machine IS NULL) = (target_label IS NULL)
  UNION ALL
  SELECT 'adjudication_target_unresolved', a.ipdb_id, a.target_machine
  FROM _lineage_adjudications AS a
  WHERE a.target_machine IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = a.target_machine)
  UNION ALL
  SELECT 'adjudication_model_unresolved', a.ipdb_id, a.model_slug
  FROM _lineage_adjudications AS a
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = a.model_slug)
  UNION ALL
  SELECT 'adjudication_license_invalid', ipdb_id, coalesce(license_status, 'NULL')
  FROM _lineage_adjudications
  WHERE license_status IS NULL
     OR license_status NOT IN ('licensed', 'unlicensed', 'unknown')
  UNION ALL
  -- ONE LABEL SLOT PER MODEL is the apply engine's identity rule; two label rows
  -- for one model would silently reword each other.
  SELECT 'adjudication_two_labels_one_model', ipdb_id, count(*)::VARCHAR
  FROM _lineage_adjudications WHERE target_label IS NOT NULL
  GROUP BY ipdb_id HAVING count(*) > 1
  UNION ALL
  -- THE FILL LEDGER, mirroring the adjudication ledger above. Every fill model in
  -- results.json is either vetted into the edge table or named in the deferrals
  -- with a reason -- a model in neither is green work silently dropped, in both is
  -- contradictory. The orphan test carries the same both-sides-of-the-apply shape.
  SELECT 'fill_model_unaccounted', f.ipdb_id, f.model_slug
  FROM (SELECT DISTINCT CAST(r.ipdb_id AS BIGINT) AS ipdb_id, r.model_slug
        FROM (SELECT unnest(rows) AS r
              FROM read_json_auto('../flippatch/campaigns/0299-ipdb-relationship-lineage/sweep/results.json'))
        WHERE r.disposition = 'fill') AS f
  WHERE NOT EXISTS (SELECT 1 FROM _lineage_fill_edges e WHERE e.ipdb_id = f.ipdb_id)
    AND NOT EXISTS (SELECT 1 FROM _lineage_fill_deferrals d WHERE d.ipdb_id = f.ipdb_id)
  UNION ALL
  SELECT 'fill_model_both_vetted_and_deferred', e.ipdb_id, e.model_slug
  FROM _lineage_fill_edges AS e
  WHERE EXISTS (SELECT 1 FROM _lineage_fill_deferrals d WHERE d.ipdb_id = e.ipdb_id)
  UNION ALL
  SELECT 'fill_edge_orphaned', e.ipdb_id, e.model_slug
  FROM (SELECT DISTINCT ipdb_id, model_slug FROM _lineage_fill_edges) AS e
  WHERE NOT EXISTS (
      SELECT 1 FROM (SELECT unnest(rows) AS r
                     FROM read_json_auto('../flippatch/campaigns/0299-ipdb-relationship-lineage/sweep/results.json'))
      WHERE r.disposition = 'fill' AND CAST(r.ipdb_id AS BIGINT) = e.ipdb_id)
  UNION ALL
  SELECT 'fill_target_xor_broken', ipdb_id, model_slug
  FROM _lineage_fill_edges
  WHERE (target_machine IS NULL) = (target_label IS NULL)
  UNION ALL
  SELECT 'fill_target_unresolved', e.ipdb_id, e.target_machine
  FROM _lineage_fill_edges AS e
  WHERE e.target_machine IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = e.target_machine)
  UNION ALL
  SELECT 'fill_model_unresolved', e.ipdb_id, e.model_slug
  FROM _lineage_fill_edges AS e
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = e.model_slug)
  UNION ALL
  SELECT 'fill_two_labels_one_model', ipdb_id, count(*)::VARCHAR
  FROM _lineage_fill_edges WHERE target_label IS NOT NULL
  GROUP BY ipdb_id HAVING count(*) > 1
  UNION ALL
  -- The edge table has no license column because gen_fills.py hardcodes `unknown`;
  -- this pins the assumption to the record instead of leaving it implicit. A fill
  -- judged licensed/unlicensed would need the column added, and this check is how
  -- that day announces itself.
  SELECT 'fill_license_not_unknown', CAST(r.ipdb_id AS BIGINT), r.license_status
  FROM (SELECT unnest(rows) AS r
        FROM read_json_auto('../flippatch/campaigns/0299-ipdb-relationship-lineage/sweep/results.json'))
  WHERE r.disposition = 'fill' AND r.license_status <> 'unknown'
  UNION ALL
  -- One quote per patch entry: rows of one model must agree on it, because the
  -- entry-level cite is single and gen_fills.py errors rather than choosing.
  SELECT 'fill_entry_quote_disagrees', ipdb_id, count(DISTINCT quote)::VARCHAR
  FROM _lineage_fill_edges GROUP BY ipdb_id HAVING count(DISTINCT quote) > 1
  UNION ALL
  -- THE ESCALATION LEDGER: every model with a review-tier row in results.json is
  -- either adjudicated into edges or dismissed with a reason -- in neither is
  -- review work silently dropped. (A model may be in both: some of its rows
  -- authored, others dismissed.) The structural checks mirror the fill ones.
  SELECT 'escalated_model_unaccounted', e.ipdb_id, e.model_slug
  FROM (SELECT DISTINCT CAST(r.ipdb_id AS BIGINT) AS ipdb_id, r.model_slug
        FROM (SELECT unnest(rows) AS r
              FROM read_json_auto('../flippatch/campaigns/0299-ipdb-relationship-lineage/sweep/results.json'))
        WHERE r.disposition NOT IN ('fill', 'agrees', 'no-claim')) AS e
  WHERE NOT EXISTS (SELECT 1 FROM _lineage_escalation_edges a WHERE a.ipdb_id = e.ipdb_id)
    AND NOT EXISTS (SELECT 1 FROM _lineage_escalation_dismissals d WHERE d.ipdb_id = e.ipdb_id)
  UNION ALL
  SELECT 'escalation_edge_orphaned', a.ipdb_id, a.model_slug
  FROM (SELECT DISTINCT ipdb_id, model_slug FROM _lineage_escalation_edges) AS a
  WHERE NOT EXISTS (
      SELECT 1 FROM (SELECT unnest(rows) AS r
                     FROM read_json_auto('../flippatch/campaigns/0299-ipdb-relationship-lineage/sweep/results.json'))
      WHERE CAST(r.ipdb_id AS BIGINT) = a.ipdb_id)
  UNION ALL
  SELECT 'escalation_target_xor_broken', ipdb_id, model_slug
  FROM _lineage_escalation_edges
  WHERE (target_machine IS NULL) = (target_label IS NULL)
  UNION ALL
  SELECT 'escalation_target_unresolved', a.ipdb_id, a.target_machine
  FROM _lineage_escalation_edges AS a
  WHERE a.target_machine IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = a.target_machine)
  UNION ALL
  SELECT 'escalation_model_unresolved', a.ipdb_id, a.model_slug
  FROM _lineage_escalation_edges AS a
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = a.model_slug)
  UNION ALL
  SELECT 'escalation_two_labels_one_model', ipdb_id, count(*)::VARCHAR
  FROM _lineage_escalation_edges WHERE target_label IS NOT NULL
  GROUP BY ipdb_id HAVING count(*) > 1
  UNION ALL
  SELECT 'escalation_entry_quote_disagrees', ipdb_id, count(DISTINCT quote)::VARCHAR
  FROM _lineage_escalation_edges GROUP BY ipdb_id HAVING count(DISTINCT quote) > 1
  UNION ALL
  -- An escalation edge duplicating a fill or hand-pass edge would author the same
  -- claim twice across patches in one campaign.
  SELECT 'escalation_edge_duplicates_earlier_patch', a.ipdb_id, a.model_slug
  FROM _lineage_escalation_edges AS a
  WHERE EXISTS (SELECT 1 FROM _lineage_fill_edges f
                WHERE f.ipdb_id = a.ipdb_id AND f.relationship_type = a.relationship_type
                  AND f.target_machine IS NOT DISTINCT FROM a.target_machine
                  AND (a.target_machine IS NOT NULL OR f.target_label IS NOT NULL))
     OR EXISTS (SELECT 1 FROM _lineage_adjudications j
                WHERE j.ipdb_id = a.ipdb_id AND j.relationship_type = a.relationship_type
                  AND j.target_machine IS NOT DISTINCT FROM a.target_machine
                  AND (a.target_machine IS NOT NULL OR j.target_label IS NOT NULL));
