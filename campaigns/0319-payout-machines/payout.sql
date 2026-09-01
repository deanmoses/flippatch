-- IPDB's `Payout Machine` specialty, landed on a new reward type of its own.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, liveness
-- filtering, the NULL-spelling regularization) is FLIPCOMMONS' shared foundation;
-- the runner loads it under this file automatically, so nothing is `.read` here.
--
-- WHY THE COMPARISON LAYER IS NOT READ. Same reason as 0307's `counter_games.sql`:
-- the rows are PER MODEL for a specialty whose target does not resolve, and the
-- layer publishes that grain only through `_eds_ipdb_specialties`, an internal
-- view the baked shim does not carry. Every model here already holds an `ipdb_id`,
-- so the link is a join, not a match. The census is attached directly.
--
-- HOW TO RUN. cwd must be the flipcommons checkout, so that this file's ATTACH
-- resolves. `make analyze` handles that:
--
--     F=campaigns/0319-payout-machines/payout.sql
--     make analyze FILE=$F PREFIX=payout                 # summary, gated on checks
--     make analyze FILE=$F Q="FROM payout_patch_rows;"   # what gen.py emits for 0320
--     make analyze FILE=$F Q="FROM payout_vocabulary;"   # what gen.py emits for 0319
--     make analyze FILE=$F Q="FROM payout_checks;"       # the gates, one row per failure
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
--
-- == WHY A NEW TERM AND NOT ONE OF THE THREE WE HAVE ========================
--
-- The layer's worklist note reads this heading as spanning `cash-payout` and
-- `merchant-paid`, needing per-model research to split. Reading the population
-- says the split is not there to be made, and that the heading is not a parent of
-- our three specific terms at all.
--
-- IPDB DEFINES IT BY WHO DISPENSES, NOT BY WHAT. Its glossary: "These machines
-- have the ability to dispense an award to players who achieved a goal ... The
-- awards have taken many forms (free games, tickets, candy, merchandise, etc.),
-- but the most popular was probably coins." The discriminator is that THE MACHINE
-- PAYS. What it pays is explicitly open.
--
-- SO THE THREE TERMS SIT WRONG UNDER IT, and the catalog's own memberships say so:
--
--   * `merchant-paid` is the definitional OPPOSITE -- "the machine identifies a
--     winner but pays nothing itself". 2 of our 16 carry the heading, both prize-
--     display counter games IPDB filed loosely.
--   * `ticket-payout` has its own IPDB heading, `Redemption Game`, where 31 of our
--     32 live. IPDB treats ticket and payout as SIBLINGS. 1 overlaps.
--   * `cash-payout` is the one real subset: 7 of our 8.
--
-- AND THE RESIDUE CANNOT BE SORTED. 238 of the 434 IPDB notes say nothing about
-- the reward beyond the flag, and there is no second source: 1 of the 434 carries
-- an OPDB id. Where the notes DO speak, they usually describe a factory ORDERING
-- OPTION rather than the machine's reward -- `zipper`, "Ticket, cash, or check
-- models were available"; `preakness`, "Payout version sold for $149.50. Ticket
-- version sold for $159.50." One listing covers every configuration.
--
-- That last shape needs no new vocabulary -- `reward_type` is many-to-many and the
-- catalog already answers it by attaching several (`bally-bonus` holds cash-payout
-- + free-play + ticket-payout). What is left over is not variance but IGNORANCE of
-- which form applied, and `payout` is the claim IPDB actually makes and we can
-- actually check: the machine dispensed the award.
--
--
-- == WHY ALL 434 AND NOT ONLY THE EMPTY SLOTS ===============================
--
-- 0307 emitted only models with an empty cabinet, because `cabinet` is a scalar
-- and a second value would overwrite. `reward_type` is a RELATIONSHIP: asserting a
-- member adds it, and the resolver unions `exists=true` across sources. So the 23
-- members that already carry a reward type keep it and gain `payout` beside it,
-- which is the true statement about a machine known to pay cash AND known to be a
-- payout machine. Nothing is superseded and `cash-payout` is left alone.

ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- One row per live catalog model IPDB marks `Payout Machine`, with the reward
-- types the catalog holds for it today.
CREATE OR REPLACE VIEW payout_population AS
  SELECT
    s.ipdb_id,
    m.id   AS model_id,
    m.slug,
    m.name,
    m.year,
    m.manufacturer_name,
    (SELECT list_sort(list(r.reward_type_slug))
     FROM model_rewards AS r WHERE r.model_id = m.id) AS current_rewards
  FROM px.ipdb.model_specialties AS s
  JOIN models AS m ON m.ipdb_id = s.ipdb_id
  WHERE s.specialty = 'Payout Machine';
COMMENT ON VIEW payout_population IS
  'Every live model IPDB marks Payout Machine, with the reward types the catalog holds today.';

-- WHAT 0319 EMITS -- the vocabulary move: `payout` created at display order 4, and
-- the four terms that follow it shifted down one so the general term seats ahead
-- of the specific ones it generalizes.
--
-- Literal because it is a vocabulary decision, not a derivation. `expected_order`
-- is the value the shift assumes each record holds TODAY, and `payout_checks`
-- asserts it rather than trusting it -- a shift computed against a stale ordering
-- silently produces the wrong one.
CREATE OR REPLACE VIEW payout_vocabulary AS
  SELECT * FROM (VALUES
    ('payout',        NULL, 4),
    ('cash-payout',      4, 5),
    ('ticket-payout',    5, 6),
    ('merchant-paid',    6, 7),
    ('free-play',        7, 8)
  ) AS t(slug, expected_order, new_order);
COMMENT ON VIEW payout_vocabulary IS
  'What 0319 emits — payout at display order 4 and the four terms it displaces, each with the order it must currently hold. expected_order NULL is the record being created.';

-- WHAT 0320 EMITS -- one `reward_type: [payout]` assertion per member, cited to
-- its own listing's Specialty row.
--
-- The quote names ONE specialty and leans on the `[...]` ellipsis to absorb
-- whatever precedes it, which is what `scripts/quotes/sources.py` prescribes: the
-- census records WHICH specialties a machine carries, not the order the page
-- prints them, so a quote asserting two are adjacent would assert something the
-- store cannot back.
CREATE OR REPLACE VIEW payout_patch_rows AS
  SELECT
    ipdb_id,
    slug,
    name,
    year,
    'payout'                          AS reward_type,
    'ipdb:' || ipdb_id                AS cite_ref,
    'Specialty: [...] Payout Machine' AS quote
  FROM payout_population;
COMMENT ON VIEW payout_patch_rows IS
  'What 0320 emits — one payout reward-type assertion per Payout Machine member, cited to its own Specialty row.';

CREATE OR REPLACE VIEW payout_checks AS
  -- The specialty must still be in the census. An empty population means the
  -- census moved under us, not that the work is done.
  SELECT 'specialty_absent_from_census' AS check_name,
         NULL::BIGINT AS id,
         'payout_population is empty' AS detail
  WHERE NOT EXISTS (SELECT 1 FROM payout_population)
  UNION ALL
  -- A listing with no live catalog model would be dropped by the join without a
  -- word. It is already a finding under `ipdb-model-*`; what this catches is the
  -- population shrinking for a reason nobody noticed.
  SELECT 'listing_matches_no_live_model', s.ipdb_id, s.ipdb_id::VARCHAR
  FROM px.ipdb.model_specialties AS s
  WHERE s.specialty = 'Payout Machine'
    AND NOT EXISTS (SELECT 1 FROM models AS m WHERE m.ipdb_id = s.ipdb_id)
  UNION ALL
  -- Two listings resolving to one model would emit the same entry ref twice in
  -- one patch. The layer guards the IPDB side of this; the catalog side is ours.
  SELECT 'model_claimed_by_two_listings', model_id,
         slug || ' <- ' || array_to_string(list_sort(list(ipdb_id))::VARCHAR[], ', ')
  FROM payout_population GROUP BY model_id, slug HAVING count(*) > 1
  UNION ALL
  -- Re-asserting a member the source already holds diffs to nothing, and a no-op
  -- diff under a provenance-bearing entry is a hard error at apply.
  SELECT 'member_already_holds_payout', p.model_id, p.slug
  FROM payout_population AS p
  WHERE list_contains(p.current_rewards, 'payout')
  UNION ALL
  -- 0319 CREATES the record, so the slug must be free. A live `payout` means
  -- somebody minted it already and this campaign is asserting onto a term it did
  -- not define.
  SELECT 'payout_slug_already_live', id, slug
  FROM reward_types WHERE slug = 'payout'
  UNION ALL
  -- THE PREMISE OF THE SHIFT, ASSERTED. Each displaced term must still hold the
  -- order the literal relation says it does; otherwise the new ordering is
  -- computed against a vocabulary that has moved.
  SELECT 'display_order_not_as_expected', r.id,
         v.slug || ' expected ' || v.expected_order::VARCHAR
           || ', holds ' || coalesce(r.display_order::VARCHAR, 'NULL')
  FROM payout_vocabulary AS v
  JOIN reward_types AS r ON r.slug = v.slug
  WHERE v.expected_order IS NOT NULL
    AND r.display_order IS DISTINCT FROM v.expected_order
  UNION ALL
  -- Drift guard on the other end of the same relation: a displaced slug that no
  -- longer names a live reward type is a claim that will not resolve.
  SELECT 'displaced_term_does_not_resolve', NULL::BIGINT, v.slug
  FROM payout_vocabulary AS v
  WHERE v.expected_order IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM reward_types AS r WHERE r.slug = v.slug)
  UNION ALL
  -- The new order must be a clean permutation: no term left sharing a slot with
  -- another once the shift lands.
  SELECT 'new_display_order_collides', NULL::BIGINT,
         'order ' || o::VARCHAR || ' claimed by ' || array_to_string(list_sort(list(slug)), ', ')
  FROM (
    SELECT v.slug, v.new_order AS o FROM payout_vocabulary AS v
    UNION ALL
    SELECT r.slug, r.display_order FROM reward_types AS r
    WHERE r.slug NOT IN (SELECT slug FROM payout_vocabulary)
  ) GROUP BY o HAVING count(*) > 1;
COMMENT ON VIEW payout_checks IS
  'Gates for the payout-machine campaign — one row per failure; empty is a pass.';

-- Summary, printed by `make analyze FILE=… PREFIX=payout`.
CREATE OR REPLACE VIEW payout_summary AS
  SELECT 'population'                AS metric, count(*) AS n FROM payout_population
  UNION ALL
  SELECT 'already_holds_a_reward',   count(*) FROM payout_population
    WHERE len(current_rewards) > 0
  UNION ALL
  SELECT 'already_holds_cash_payout', count(*) FROM payout_population
    WHERE list_contains(current_rewards, 'cash-payout')
  UNION ALL
  SELECT 'emitted_payout',           count(*) FROM payout_patch_rows
  UNION ALL
  SELECT 'vocabulary_rows',          count(*) FROM payout_vocabulary
  UNION ALL
  SELECT 'CHECK_FAILURES',           count(*) FROM payout_checks;
