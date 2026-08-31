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
  UNION ALL SELECT 'patch_rows_pending', count(*) FROM lineage_patch_rows;

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
  GROUP BY ipdb_id HAVING count(*) > 1;
