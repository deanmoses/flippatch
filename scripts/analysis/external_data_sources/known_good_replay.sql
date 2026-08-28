-- Does the matcher get right the answers we already know?
--
-- `.read` this from a campaign analysis after flipcommons' foundation:
--
--     .read ../flippatch/scripts/analysis/external_data_sources/known_good_replay.sql
--
-- It reads `ipdb.sql` and `opdb.sql` itself, so the attach, the watermark and both
-- ladders come with it.
--
-- THE IDEA. 8k catalog models already carry an IPDB or OPDB id. Those are the answer key.
-- This file covers up the answers: for every already-linked listing it asks the matcher
-- "which catalog model is this?", and compares the answer to what's already on record.
-- OPDB's "Carnival", 1971, Sega Enterprises should come back `carnival-2`, because that's
-- what `carnival-2` already links. Repeat eight thousand times and the question "is the
-- matcher broken?" stops being a matter of belief.
--
-- IT RUNS THE SHIPPING LADDER, NOT A COPY OF IT. A reimplementation here would drift
-- from the real one and then certify the drift -- so `_eds_opdb_model_resolution` and
-- `_eds_ipdb_candidates` are deliberately NOT scoped to unmatched listings (see the
-- comment at each), every consumer that wants only unmatched rows filters at its own
-- site, and this file reads the same views the worklists read. If the ladder changes,
-- this measures the change; that property is the reason for the unscoping and must
-- survive any future edit to either view.
--
-- WHAT IT DOES AND DOES NOT COVER. It exercises the NAME LADDER -- the heuristic part,
-- where a wrong answer is possible. The ipdb_id route above the ladder is an id rather
-- than a match and is scoped to unmatched listings, so it does not fire here at all;
-- neither do the manufacturer and title stages, which have no replay yet. The bar is the
-- one the worklist itself acts on: a unique candidate at the winning tier, the year
-- corroborated, and the maker leg uncontested. Anything short of that is not an answer
-- the layer would have offered, so it is not counted as one either.
--
-- THE ANSWER KEY IS NOT AXIOMATIC. A disagreement means the ladder and the recorded link
-- differ; which one is wrong is a question for a person. `medieval-madness-remake-royal-
-- edition` carries IPDB 6264 while IPDB's own name for 6264 is the Limited Edition --
-- a real editorial disagreement, not a matcher bug. So these are WORKLISTS, never
-- `*_checks`: a row here is something to read, and gating the runner on it would fail
-- every run over a question nobody has answered yet.
--
-- A DISAGREEMENT IS NOT AUTOMATICALLY A BAD LINK, which is why the counts split on
-- `would_link`. Most of them are answers the layer would have classified
-- `possible_duplicate` -- the candidate already carries someone else's id, so the
-- worklist says "read both pages" rather than "backfill this". Getting one of those
-- different costs a reader two page loads. The `would_link` half is the real measure:
-- an answer the layer would have handed over as a link, that the record contradicts.
--
-- ONE CAVEAT WORTH CARRYING. Some catalog names and years were themselves patched in
-- from these sources, so the agreement rate is flattered. It does not rescue the case
-- that matters -- choosing among same-named models is exactly where a derived name
-- gives no help -- but the headline number is an upper bound, not a guarantee.

.read ../flippatch/scripts/analysis/external_data_sources/ipdb.sql
.read ../flippatch/scripts/analysis/external_data_sources/opdb.sql

-- The OPDB replay, one row per already-linked listing the ladder answered confidently.
-- `agrees` is the verdict; the disagreements are the point, and the columns beside them
-- are the evidence for reading one.
-- MATERIALIZED: the summary and the checks between them scan this nine times.
CREATE OR REPLACE TABLE _eds_opdb_replay AS
  SELECT
    d.opdb_id,
    d.opdb_name,
    d.opdb_year,
    d.opdb_manufacturer_slug,
    truth.slug                                              AS recorded_model_slug,
    coalesce(r.unlinked_model_slug, r.linked_model_slug)    AS ladder_model_slug,
    r.match_basis,
    r.resolved_year_verdict,
    mc.contested_rival_models,
    -- WOULD THE LAYER HAVE CALLED THIS A LINK? Only if nothing else is sitting on the
    -- candidate. A candidate already carrying a DIFFERENT id is `possible_duplicate` in
    -- the worklist -- read both pages -- so a wrong answer there costs a reader two page
    -- loads, not a bad link. Under replay the truth model necessarily carries this very
    -- listing's id, and that self-occupancy is not somebody else's claim, so it counts
    -- as free. This split is the whole point of the two disagreement metrics: the
    -- `would_link` count is the one that must stay at zero.
    (r.unlinked_model_slug IS NOT NULL
     OR r.linked_model_opdb_id = d.opdb_id)                           AS would_link,
    coalesce(r.unlinked_model_slug, r.linked_model_slug) = truth.slug AS agrees
  FROM _eds_opdb_dump AS d
  INNER JOIN models AS truth ON truth.opdb_id = d.opdb_id
  INNER JOIN _eds_opdb_model_resolution AS r ON r.opdb_id = d.opdb_id
  LEFT JOIN _eds_opdb_maker_contested AS mc ON mc.opdb_id = d.opdb_id
  -- The live confident bar, mirrored: unique candidate, year corroborated, maker leg
  -- uncontested. Kept in step with `opdb_models_unmatched`'s confident classes by
  -- `known_good_replay_checks` below.
  WHERE r.n_candidates = 1
    AND r.resolved_year_verdict = 'corroborated'
    AND mc.opdb_id IS NULL;

CREATE OR REPLACE VIEW opdb_known_good_replay AS
  SELECT * EXCLUDE (agrees) FROM _eds_opdb_replay
  WHERE NOT agrees ORDER BY would_link DESC, opdb_id;
COMMENT ON VIEW opdb_known_good_replay IS
  'Worklist — one row per already-linked OPDB listing where replaying the name ladder lands on a different model than the link on record, would_link first: true means the layer would have offered it as a backfill and is the serious kind, false means it would have gone to possible_duplicate for a human anyway. Empty is the healthy state; a row is an adjudication, not necessarily a bug.';

-- The IPDB replay. One tier rather than three -- name and maker, no grouping concept --
-- so there is no `match_basis` to report.
-- MATERIALIZED: see the OPDB twin.
CREATE OR REPLACE TABLE _eds_ipdb_replay AS
  SELECT
    d.ipdb_id,
    d.ipdb_name,
    d.ipdb_date_year,
    d.ipdb_manufacturer_slug,
    truth.slug                                              AS recorded_model_slug,
    coalesce(c.unlinked_model_slug, c.linked_model_slug)    AS ladder_model_slug,
    c.resolved_year_verdict,
    -- See the OPDB twin: a candidate spoken for by another id is `possible_duplicate`,
    -- not a link instruction.
    (c.unlinked_model_slug IS NOT NULL
     OR c.linked_model_ipdb_id = d.ipdb_id)                           AS would_link,
    coalesce(c.unlinked_model_slug, c.linked_model_slug) = truth.slug AS agrees
  FROM _eds_ipdb_dump AS d
  INNER JOIN models AS truth ON truth.ipdb_id = d.ipdb_id
  INNER JOIN _eds_ipdb_candidates AS c ON c.ipdb_id = d.ipdb_id
  WHERE c.n_candidates = 1
    AND c.resolved_year_verdict = 'corroborated';

CREATE OR REPLACE VIEW ipdb_known_good_replay AS
  SELECT * EXCLUDE (agrees) FROM _eds_ipdb_replay
  WHERE NOT agrees ORDER BY would_link DESC, ipdb_id;
COMMENT ON VIEW ipdb_known_good_replay IS
  'Worklist — one row per already-linked IPDB listing where replaying the name ladder lands on a different model than the link on record, would_link first: true means the layer would have offered it as a backfill and is the serious kind, false means it would have gone to possible_duplicate for a human anyway. Empty is the healthy state; a row is an adjudication, not necessarily a bug.';

-- The headline: how many answers the replay produced and how many it got different.
-- Source-labelled so these land beside each source's own metrics in the run summary.
CREATE OR REPLACE VIEW known_good_replay_summary AS
              SELECT 'opdb' AS source, 'replay_answers' AS metric, count(*) AS value FROM _eds_opdb_replay
    UNION ALL SELECT 'opdb', 'replay_answers_would_link', count(*) FROM _eds_opdb_replay WHERE would_link
    UNION ALL SELECT 'opdb', 'replay_answers_' || match_basis, count(*) FROM _eds_opdb_replay GROUP BY match_basis
    -- The two that matter, and they are deliberately not one number: a disagreement the
    -- layer would have PUBLISHED as a link is the failure this whole file exists to
    -- detect, and it must stay at zero. The rest would have reached a human regardless.
    UNION ALL SELECT 'opdb', 'REPLAY_DISAGREEMENTS_would_link', count(*) FROM _eds_opdb_replay WHERE NOT agrees AND would_link
    UNION ALL SELECT 'opdb', 'replay_disagreements_to_human', count(*) FROM _eds_opdb_replay WHERE NOT agrees AND NOT would_link
    UNION ALL SELECT 'ipdb', 'replay_answers', count(*) FROM _eds_ipdb_replay
    UNION ALL SELECT 'ipdb', 'replay_answers_would_link', count(*) FROM _eds_ipdb_replay WHERE would_link
    UNION ALL SELECT 'ipdb', 'REPLAY_DISAGREEMENTS_would_link', count(*) FROM _eds_ipdb_replay WHERE NOT agrees AND would_link
    UNION ALL SELECT 'ipdb', 'replay_disagreements_to_human', count(*) FROM _eds_ipdb_replay WHERE NOT agrees AND NOT would_link;
COMMENT ON VIEW known_good_replay_summary IS
  'How many links the replay re-derived confidently and how many came back different, per source — the OPDB half broken out by the tier that decided.';

-- Empty when healthy. Invariants of the replay itself, never findings about the data.
CREATE OR REPLACE VIEW known_good_replay_checks AS
  -- THE CHECK THIS FILE EXISTS FOR. A replay that answers nothing scores a flawless
  -- zero-out-of-zero, and a broken join looks exactly like a perfect matcher -- the
  -- precise false confidence the file was written to prevent. Both ladders answer
  -- thousands of already-linked listings, so a collapse to nothing is a wiring fault.
  SELECT 'replay_produced_no_answers' AS check_name,
         'opdb' AS detail
  WHERE (SELECT count(*) FROM _eds_opdb_replay) = 0

  UNION ALL
  SELECT 'replay_produced_no_answers', 'ipdb'
  WHERE (SELECT count(*) FROM _eds_ipdb_replay) = 0

  UNION ALL
  -- One row per listing, or every count above is quietly multiplied.
  SELECT 'opdb_replay_not_one_row_per_listing', opdb_id
  FROM _eds_opdb_replay GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  SELECT 'ipdb_replay_not_one_row_per_listing', ipdb_id::VARCHAR
  FROM _eds_ipdb_replay GROUP BY ipdb_id HAVING count(*) > 1

  UNION ALL
  -- THE LADDER MUST STAY UNSCOPED, or this file silently tests nothing: scoping either
  -- candidate view back to unmatched listings would empty the replay. The check above
  -- catches a total collapse; this one catches the specific regression, by asserting the
  -- ladder still reasons about listings that ARE linked.
  SELECT 'opdb_ladder_rescoped_to_unmatched', 'no linked listing reaches the resolution'
  WHERE NOT EXISTS (
    SELECT 1 FROM _eds_opdb_model_resolution AS r
    INNER JOIN models AS m ON m.opdb_id = r.opdb_id)

  UNION ALL
  SELECT 'ipdb_ladder_rescoped_to_unmatched', 'no linked listing reaches the candidates'
  WHERE NOT EXISTS (
    SELECT 1 FROM _eds_ipdb_candidates AS c
    INNER JOIN models AS m ON m.ipdb_id = c.ipdb_id);
COMMENT ON VIEW known_good_replay_checks IS
  'Empty when healthy — the replay actually ran, holds one row per listing, and both ladders are still unscoped enough to reach already-linked listings. A row means the replay is measuring nothing, which reads identically to a perfect score.';
