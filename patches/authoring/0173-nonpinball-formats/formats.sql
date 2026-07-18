-- Non-pinball game_format candidate analysis — the sweep AFTER bingo (0172).
--
-- Goal: surface the catalog models that should carry a NON-pinball game_format
-- but don't yet, across every format IPDB keeps INSIDE the pinball family. This
-- is the "detect + vet the candidate list" step; vocab + patch authoring is
-- downstream (one campaign per format the review confirms is worth adding).
--
-- WHY THIS EXISTS. The original format sweep (0010) used one signal only: IPDB
-- notes that SELF-LABEL "not a pinball". High precision, but by construction it
-- can only find the formats IPDB itself disowns (slot, gun, video, shuffle …).
-- The formats IPDB CATALOGS AS PINBALL are invisible to it — bingo was the first
-- (its own 307-model campaign, 0172); rolldown, one-ball payout and the
-- poker/keno consoles still have no home. This probe hunts that blind spot.
--
-- PLAN-LOCAL LAYER. The generic catalog decode (the `models` view, the read-only
-- connection, etc.) is FLIPCOMMONS' shared foundation, reused VERBATIM via the
-- `.read` below — flippatch keeps no copy of it. See this dir's README.md.
--
-- HOW TO RUN. Must run with cwd = the flipcommons checkout, so BOTH the `.read`
-- below AND the foundation's relative `ATTACH backend/db.sqlite3` resolve there.
-- `make analyze` (in flippatch) handles the cwd/path resolution and delegates to
-- flipcommons' shared runner (scripts/analysis), which prints analysis_context +
-- format_summary and gates on format_checks. Do not run this file directly:
--
--     P=patches/authoring/0173-nonpinball-formats/formats.sql
--     make analyze PLAN=$P PREFIX=format                             # summary, gated on checks
--     make analyze PLAN=$P Q="FROM format_candidates ORDER BY proposed_format, maker, name;"
--     make analyze PLAN=$P Q="FROM format_review WHERE proposed_format='rolldown';"  # per-format queue
--     make analyze PLAN=$P Q="FROM format_excluded_review;"          # the false positives, auditable
--     make analyze PLAN=$P CMD=ui                                    # live GUI at localhost:4213
--
-- Nothing is persisted; every count is a live snapshot of the dev DB. The SQL is
-- the source of truth for the candidate list, re-derived on each run.
--
-- THE SIGNAL. One detector per candidate format, matched against the model's
-- free text (ipdb_notes + ipdb_notable_features + description). All are keyword
-- heuristics; every row still wants source review before it becomes a claim.
-- Three structural aids (from the foundation's decoded M2Ms) do most of the
-- precision work — none is proof on its own, each is a signal that outruns the text:
--   * pin_mech — a model carrying a structured pinball MECHANISM (flippers /
--     pop-bumpers / slingshots) is a pinball on its face. These matches are
--     almost always themed pinball (a bowling- or baseball-THEMED flipper game),
--     so pin_mech rows are held OUT of the candidate set and surfaced separately.
--     Caveat: pre-1947 pin games are flipperless too (the flipper arrived with
--     Gottlieb's 1947 Humpty Dumpty), so absence of pin_mech is NOT proof of
--     non-pinball for early games — it only removes the modern themed FPs.
--   * is_grid — the structured 25-trap-hole grid (the 5x5 bingo card): the
--     keyword-invisible bingo-family signal (see _grid_reuse).
--   * has_payout_reward — a Cash/Ticket Payout reward type (foundation `rewards`):
--     the keyword-invisible GAMBLING signal. Surfaces payout consoles (one-ball /
--     slot ancestors) whose notes are bare. Not auto-classified — payout spans
--     several formats — so it feeds a hand-worklist (format_review_payout), and
--     enriches every keyword candidate's row (reward_types) for at-a-glance vetting.
--   * game_format IS NULL — already-typed models are done; we hunt the untyped.
-- Other foundation views were evaluated as extra signals and are all inert on
-- this population, so none is used (checked, so a later pass need not re-derive it):
--   * relationship edges (model_edges/model_relationships), as a variant-cabinet-FP
--     aid — only 1/140 candidates carries any edge, 0 link to a typed model;
--   * title-mates (title_* / title_size), the same variant-cabinet idea via a shared
--     Title — every candidate is alone in its Title (title_size = 1);
--   * tags — the vocabulary (widebody / prototype / remake / home-use) is all
--     pinball-production attributes, nothing format- or genre-relevant.
-- Proposed formats split two ways:
--   NEW vocab this probe is scouting  : rolldown, one-ball, poker-console
--   EXISTING vocab to recall-extend   : slot-machine, gun-game, shuffle (bowler),
--                                       bagatelle, pitch-and-bat (baseball)
-- where the 0010 self-label sweep under-collected into the untyped pool.

-- == 1 · FOUNDATION ==========================================================
.read scripts/analysis/catalog.sql

-- == 2 · REFERENCE ===========================================================
-- Hand-maintained vetting, keyed by model id — the human review of the raw
-- detector output, made reproducible. NOT derived from the DB. The `name`
-- column is for readability only; the id is the key. format_checks flags any
-- entry here that has gone stale against the live detector output.

-- Confirmed FALSE POSITIVES: a detector fired but the model is NOT that format.
-- Seed set from the first sampling pass; grows as each format's queue is vetted.
CREATE OR REPLACE VIEW _format_excluded AS
  SELECT * FROM (VALUES
    (4422, 'Pool Alley', 'bowler detector: IPDB says "looks like a puck/ball bowler but it is neither" — a cue-stick pool game')
  ) AS t(id, name, reason);

-- Grid-reuse NON-bingos: the models carrying the structured 25-trap-hole grid
-- (the 5x5 bingo card) that the bingo campaign (0172) hand-vetted as NOT in-line
-- bingos and excluded. Their IPDB free text is bare ("Trap holes (25). Equipped
-- with Electropak.") — a keyword detector can't see them — so the grid IS the
-- signal, and the format below is carried over from 0172's exclusion reasoning.
-- This is the seed for the poker/keno-console format (and flags the "pin table"
-- novelties that may just be early flipperless pinball, an editorial call).
CREATE OR REPLACE VIEW _grid_reuse AS
  SELECT * FROM (VALUES
    (4395, 'Poker-eno',    'poker-console',      'Evans keno/poker payout console; 25-hole grid scored as poker, not in-line bingo'),
    (5845, 'Tango',        'poker-console',      'Evans payout console with an Electropak; not an in-line bingo'),
    -- Jolly Joker (3037) was here as the rolldown pilot anchor; shipped in the
    -- 0173-rolldown campaign, it is now typed rolldown and drops out of the
    -- untyped candidate pool. Retired so stale_grid_reuse stays green.
    (5317, 'Space Glider', 'pop-up-novelty',     'Williams pop-up-target novelty (15 shots per play), not a bingo'),
    (4569, 'Rallye',       'pin-table(review)',  'Magister: IPDB calls it a pin table (automobile art) — may be early flipperless pinball'),
    (3336, 'L''Hirondelle','pin-table(review)',  'IPDB calls it a pin table (bird/Eiffel-tower art, no cards) — may be early flipperless pinball')
  ) AS t(id, name, proposed_format, note);

-- == 3 · ANALYSIS ============================================================
-- detect -> assemble -> classify (see scripts/analysis/README.md). One detector
-- column per candidate format, their union minus exclusions, then review slices.

-- detect --
-- Per untyped model: the collapsed lower-case free text, the structured
-- pinball-mechanism flag, and one boolean per candidate format.
CREATE OR REPLACE VIEW _format_signal AS
  WITH base AS (
    SELECT
      m.id, m.name, m.manufacturer_name AS maker, m.year, m.label,
      m.ipdb_notes AS notes, m.ipdb_notable_features AS notable_features,
      lower(coalesce(m.ipdb_notes, '') || ' '
            || coalesce(m.ipdb_notable_features, '') || ' '
            || coalesce(m.description, '')) AS txt,
      -- A structured pinball mechanism => pinball on its face (see header). Read
      -- through the foundation's decoded model_gameplay_features (live features
      -- only) rather than the raw M2M — the promotion convention (README).
      EXISTS (SELECT 1 FROM model_gameplay_features f
               WHERE f.model_id = m.id
                 AND f.feature_slug IN ('flippers', 'pop-bumpers', 'slingshots')) AS pin_mech,
      -- Structured 5x5 bingo-card grid (the 25-count is the real signal, per the
      -- view's note). After 0172 the untyped holders are the grid-reuse non-bingos
      -- (see _grid_reuse) — keyword-invisible, grid-only.
      EXISTS (SELECT 1 FROM model_gameplay_features f
               WHERE f.model_id = m.id
                 AND f.feature_slug = 'trap-holes' AND f.count = 25) AS is_grid,
      -- Structured reward-type M2M (foundation `rewards` view). A cash/ticket
      -- PAYOUT reward is the gambling signal — a second structural aid, like the
      -- grid: it is keyword-invisible (these 1930s payout consoles carry bare
      -- notes) yet marks the one-ball / slot / poker-console genres the free text
      -- misses. NOT proof on its own — surfaced for vetting in format_review_payout,
      -- never auto-classified (payout spans several formats, and a stray reward on
      -- a modern pinball is a known data quirk). reward_types is shown inline in
      -- format_review so a keyword candidate's gambling status is visible at a glance.
      coalesce(rw.rewards, []::VARCHAR[]) AS reward_types,
      (list_contains(coalesce(rw.rewards, []::VARCHAR[]), 'Cash Payout')
        OR list_contains(coalesce(rw.rewards, []::VARCHAR[]), 'Ticket Payout')) AS has_payout_reward
    FROM models m
    LEFT JOIN rewards rw ON rw.id = m.id
    WHERE m.game_format_id IS NULL       -- already-typed models are done
  )
  SELECT
    id, name, maker, year, label, notes, notable_features, pin_mech, is_grid,
    reward_types, has_payout_reward,
    -- NEW-vocab candidates (no format exists yet) --
    -- rolldown: score by rolling balls DOWN into pockets (Skee-Ball kin), often
    -- mapped to poker hands. Solid/hyphen forms only — the bare "roll down" spaced
    -- form matches ordinary "the ball rolls down" prose (bagatelles, baseball).
    (txt LIKE '%rolldown%' OR txt LIKE '%roll-down%') AS is_rolldown,
    -- one-ball: the horse-race / odds payout one-ball gambling consoles, the
    -- pre-bingo ancestors. The gambling qualifier keeps ordinary "one ball play"
    -- pinball prose out.
    ((txt LIKE '%one-ball%' OR txt LIKE '%one ball%')
      AND (txt LIKE '%payout%' OR txt LIKE '%odds%' OR txt LIKE '%gambl%'
           OR txt LIKE '%horse%' OR txt LIKE '%ticket%' OR txt LIKE '%coins for%')) AS is_oneball,
    -- poker-console / trade-stimulator: the Evans Poker-eno / Tango world — a
    -- card/keno/dice game paid out at the counter, not an in-line bingo.
    ((txt LIKE '%poker%' OR txt LIKE '%keno%' OR txt LIKE '%dice%')
      AND (txt LIKE '%console%' OR txt LIKE '%payout%' OR txt LIKE '%stimulator%'
           OR txt LIKE '%counter game%' OR txt LIKE '%trade %' OR txt LIKE '%gambl%')) AS is_console,
    -- EXISTING-vocab recall extension --
    -- slot: reels + spin/payout. Excludes EM pinball SCORE reels explicitly.
    (txt LIKE '%slot machine%' OR txt LIKE '%one-armed%' OR txt LIKE '%fruit machine%'
      OR (txt LIKE '%reel%' AND txt NOT LIKE '%score reel%'
          AND (txt LIKE '%spin%' OR txt LIKE '%payout%' OR txt LIKE '%symbol%'
               OR txt LIKE '%jackpot%'))) AS is_slot,
    -- bowler => existing 'shuffle'. Named bowler/alley forms only (bare "bowl"
    -- matches Super-Bowl themes and "bowl of" prose).
    (txt LIKE '%shuffle alley%' OR txt LIKE '%puck bowler%' OR txt LIKE '%ball bowler%'
      OR txt LIKE '%big ball bowler%' OR txt LIKE '%bowling game%' OR txt LIKE '%bowling alley%') AS is_bowler,
    -- baseball => existing 'pitch-and-bat' (the adjacent vocab). Baseball noun
    -- plus a play-mechanic word, to drop merely baseball-THEMED games.
    (txt LIKE '%baseball%'
      AND (txt LIKE '%batter%' OR txt LIKE '%pitch%' OR txt LIKE '%innings%'
           OR txt LIKE '%home run%' OR txt LIKE '%diamond%')) AS is_baseball,
    -- gun => existing 'gun-game'.
    (txt LIKE '%gun game%' OR txt LIKE '%rifle%'
      OR (txt LIKE '%shoot%' AND txt LIKE '%target%' AND txt LIKE '%gun%')) AS is_gun,
    -- bagatelle => existing 'bagatelle' (pre-flipper plunger tables). Broad and
    -- era-ambiguous; kept last in priority.
    (txt LIKE '%bagatelle%') AS is_bagatelle
  FROM base;

-- assemble --
-- One row per candidate: matched >= 1 detector, NOT a vetted false positive, and
-- NOT already a pinball-on-its-face (pin_mech held out — see format_review_pinmech
-- for what that removed). `matched` lists every format that fired; `proposed_format`
-- is the most-specific single pick (priority: the specific gambling/console forms
-- before the broad slot/bagatelle catch-alls).
CREATE OR REPLACE VIEW format_candidates AS
  SELECT
    s.id, s.name, s.maker, s.year, s.label,
    -- grid-reuse rows carry a hand-vetted format; keyword rows fall to priority.
    coalesce(
      g.proposed_format,
      CASE WHEN s.is_rolldown  THEN 'rolldown' END,
      CASE WHEN s.is_oneball   THEN 'one-ball' END,
      CASE WHEN s.is_console   THEN 'poker-console' END,
      CASE WHEN s.is_bowler    THEN 'shuffle(bowler)' END,
      CASE WHEN s.is_baseball  THEN 'pitch-and-bat(baseball)' END,
      CASE WHEN s.is_gun       THEN 'gun-game' END,
      CASE WHEN s.is_slot      THEN 'slot-machine' END,
      CASE WHEN s.is_bagatelle THEN 'bagatelle' END,
      CASE WHEN s.is_grid      THEN 'grid-review' END      -- untyped 25-grid, not yet in _grid_reuse
    ) AS proposed_format,
    list_filter([
      CASE WHEN s.is_grid      THEN 'grid-25' END,
      CASE WHEN s.is_rolldown  THEN 'rolldown' END,
      CASE WHEN s.is_oneball   THEN 'one-ball' END,
      CASE WHEN s.is_console   THEN 'poker-console' END,
      CASE WHEN s.is_bowler    THEN 'shuffle(bowler)' END,
      CASE WHEN s.is_baseball  THEN 'pitch-and-bat(baseball)' END,
      CASE WHEN s.is_gun       THEN 'gun-game' END,
      CASE WHEN s.is_slot      THEN 'slot-machine' END,
      CASE WHEN s.is_bagatelle THEN 'bagatelle' END
    ], lambda x: x IS NOT NULL) AS matched,
    s.reward_types, s.notes, s.notable_features
  FROM _format_signal s
  LEFT JOIN _grid_reuse g ON g.id = s.id
  WHERE NOT s.pin_mech
    AND (s.is_rolldown OR s.is_oneball OR s.is_console OR s.is_slot
         OR s.is_bowler OR s.is_baseball OR s.is_gun OR s.is_bagatelle OR s.is_grid)
    AND s.id NOT IN (SELECT id FROM _format_excluded)
  ORDER BY proposed_format, s.maker NULLS LAST, s.name;

-- review --
-- The human-review queue, NEW-vocab formats first (they carry the campaign
-- decision), then the recall-extension formats. Multi-match rows (matched.len>1)
-- float up inside each format — they are the ambiguous boundary calls. Full note +
-- notable_features inline so no re-fetching is needed.
CREATE OR REPLACE VIEW format_review AS
  SELECT
    id, label, maker, year, proposed_format, matched,
    len(matched) AS n_match, reward_types, notes, notable_features
  FROM format_candidates
  ORDER BY
    array_position(['rolldown','one-ball','poker-console','pop-up-novelty',
                    'pin-table(review)','grid-review','shuffle(bowler)',
                    'pitch-and-bat(baseball)','gun-game','slot-machine','bagatelle'],
                   proposed_format),
    (len(matched) > 1) DESC, maker NULLS LAST, name;

-- What the pin_mech filter removed: matched a format detector but carries a
-- pinball mechanism (near-certainly themed pinball). Kept auditable, not silently
-- dropped — a genuine non-pinball hiding here would be a detector miss to fix.
CREATE OR REPLACE VIEW format_review_pinmech AS
  SELECT
    s.id, s.label, s.maker, s.year,
    list_filter([
      CASE WHEN s.is_rolldown  THEN 'rolldown' END,
      CASE WHEN s.is_oneball   THEN 'one-ball' END,
      CASE WHEN s.is_console   THEN 'poker-console' END,
      CASE WHEN s.is_bowler    THEN 'shuffle(bowler)' END,
      CASE WHEN s.is_baseball  THEN 'pitch-and-bat(baseball)' END,
      CASE WHEN s.is_gun       THEN 'gun-game' END,
      CASE WHEN s.is_slot      THEN 'slot-machine' END,
      CASE WHEN s.is_bagatelle THEN 'bagatelle' END
    ], lambda x: x IS NOT NULL) AS matched,
    s.notable_features
  FROM _format_signal s
  WHERE s.pin_mech
    AND (s.is_rolldown OR s.is_oneball OR s.is_console OR s.is_slot
         OR s.is_bowler OR s.is_baseball OR s.is_gun OR s.is_bagatelle)
  ORDER BY s.maker NULLS LAST, s.name;

-- Payout-reward recall gain: untyped models carrying a Cash/Ticket Payout reward
-- that NO keyword detector caught (not already a candidate). These are the
-- keyword-invisible gambling machines — 1930s-40s payout consoles (one-ball / slot
-- ancestors) whose notes are bare, findable only by the structured reward. A
-- hand-classification worklist for the payout campaigns, not auto-typed: payout
-- doesn't name a single format, and the odd modern pinball carries a stray payout
-- reward (a data quirk — vet on year + notes, e.g. the empty-noted 2026 Stern here).
CREATE OR REPLACE VIEW format_review_payout AS
  SELECT s.id, s.label, s.maker, s.year, s.reward_types, s.pin_mech,
         s.notes, s.notable_features
  FROM _format_signal s
  WHERE s.has_payout_reward
    AND s.id NOT IN (SELECT id FROM format_candidates)
  ORDER BY s.year NULLS FIRST, s.maker NULLS LAST, s.name;

-- The confirmed false positives, with the text that tripped the detector — so
-- the exclusion calls stay auditable, not buried in a VALUES list.
CREATE OR REPLACE VIEW format_excluded_review AS
  SELECT e.id, s.label, e.reason, s.pin_mech, s.notes, s.notable_features
  FROM _format_excluded e
  JOIN _format_signal s ON s.id = e.id
  ORDER BY s.name;

-- == 4 · SUMMARY & CHECKS ====================================================
-- The honest-prose tail. Headline numbers the write-up quotes come from
-- format_summary, never hand-counted; format_checks is empty when healthy.

CREATE OR REPLACE VIEW format_summary AS
            SELECT 'candidates'      AS metric, NULL AS proposed_format, count(*) AS value FROM format_candidates
  UNION ALL SELECT 'excluded_fp',        NULL, count(*) FROM _format_excluded
  UNION ALL SELECT 'held_out_pin_mech',  NULL, count(*) FROM format_review_pinmech
  UNION ALL SELECT 'payout_recall_gain', NULL, count(*) FROM format_review_payout
  UNION ALL SELECT 'multi_match',        NULL, count(*) FROM format_candidates WHERE len(matched) > 1
  UNION ALL SELECT 'by_format', proposed_format, count(*) FROM format_candidates GROUP BY proposed_format
  ORDER BY metric, value DESC;

CREATE OR REPLACE VIEW format_checks AS
  -- Every excluded id must still be a live detector hit (else the exclusion is
  -- stale — the row it removed no longer matches any detector).
            SELECT 'stale_exclusion' AS check, e.id, e.name AS detail
            FROM _format_excluded e
            WHERE NOT EXISTS (
              SELECT 1 FROM _format_signal s WHERE s.id = e.id
                AND (s.is_rolldown OR s.is_oneball OR s.is_console OR s.is_slot
                     OR s.is_bowler OR s.is_baseball OR s.is_gun OR s.is_bagatelle))
  -- No candidate may carry a pinball mechanism (the assemble step holds those out;
  -- a leak means the filter and the review slice disagree).
  UNION ALL SELECT 'pin_mech_in_candidates', c.id, c.label
            FROM format_candidates c JOIN _format_signal s ON s.id = c.id
            WHERE s.pin_mech
  -- Every _grid_reuse id must still be a live untyped 25-hole holder (else the
  -- carried-over bingo exclusion has gone stale — the grid or the row is gone).
  UNION ALL SELECT 'stale_grid_reuse', g.id, g.name
            FROM _grid_reuse g
            WHERE NOT EXISTS (SELECT 1 FROM _format_signal s WHERE s.id = g.id AND s.is_grid);
