-- Bingo-pinball candidate analysis for the game_format = bingo-pinball campaign.
--
-- Goal: find every catalog model whose game_format should be set to the new
-- `bingo-pinball` format, so the campaign can author the patches. This is the
-- "detect + vet the candidate list" step; patch authoring is downstream.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, the read-only
-- connection, etc.) is FLIPCOMMONS' shared foundation, reused VERBATIM via the
-- `.read` below — flippatch keeps no copy of it. See this dir's README.md.
--
-- HOW TO RUN. This must run with cwd = the flipcommons checkout, so that BOTH the
-- `.read scripts/analysis/catalog.sql` below AND the foundation's own relative
-- `ATTACH backend/db.sqlite3` resolve there. `make analyze` handles the cwd/path
-- resolution and delegates to flipcommons' shared runner (scripts/analysis/analysis),
-- which prints the analysis_context watermark + bingo_summary and gates on
-- bingo_checks. Do not run this file directly:
--
--     P=patches/authoring/0172-bingo-game-format/bingo.sql
--     make analyze FILE=$F PREFIX=bingo                          # summary, gated on checks
--     make analyze FILE=$F Q="FROM bingo_candidates ORDER BY maker, name;"   # ad-hoc query
--     make analyze FILE=$F CMD=ui                                # live GUI at localhost:4213
--
-- Nothing is persisted; every count is a live snapshot of the dev DB. Re-run as
-- the catalog changes. `bingo_summary` emits the headline numbers; `bingo_checks`
-- is empty when healthy.
--
-- THE SIGNAL. Bingo pinballs are the multi-card, in-line-scoring games (Bally,
-- United, SIRMO, Splin, Petaco/Recel …). FOUR detectors, because no one signal
-- suffices — each covers a blind spot of the others:
--   by_word   — the IPDB free text says "bingo". Precise on the makers' own
--               history, but LOW RECALL: ~half the real bingos never use the word,
--               and it drags in non-bingos whose notes merely MENTION bingo (poker
--               novelties, precursors, company names, legislation).
--   by_struct — the notable_features PROSE carries the hole grid (trap/gobble holes
--               18/20/21/24/25/28) PLUS a card count or Bally/United feature name
--               (Magic Squares/Screen/Line, Mystic Lines, in-line). The conjunct is
--               what keeps the noisier counts (18/20/21/24/28 include 1940s one-ball
--               payout & ticket games) from matching.
--   by_hole25 — the STRUCTURED gameplay-feature `trap-holes` = 25 (the 5x5 card),
--               near-definitive (173 models carry it; none holds a non-bingo
--               format). Catches modern machines whose prose lost the hole text.
--               Only 25 is safe bare — other counts ride by_struct's conjunct.
--   by_maker  — a model by a verified bingo-only manufacturer (SIRMO, Splin, and
--               the small European export houses in _bingo_maker). Catches the
--               modern electronic six-card machines with no hole prose and no
--               "bingo" word — invisible to the other three.
-- The candidate set is their UNION minus a hand-vetted exclusion list. All are
-- heuristics; every row still wants source review before it becomes a claim.

-- == 1 · FOUNDATION ==========================================================
.read scripts/analysis/catalog.sql

-- == 2 · REFERENCE ===========================================================
-- Hand-maintained vetting, keyed by model id — the human review of the raw
-- detector output, made reproducible. NOT derived from the DB. The `name`
-- columns are for readability only; the id is the key. bingo_checks flags any
-- entry here that has gone stale against the live detector output.

-- Confirmed FALSE POSITIVES: a detector fired but the model is NOT a bingo.
-- Every id here is a live `by_word` hit (a note that mentions bingo without the
-- game being one). Structural-only precursors — 1930s one-ball payouts and
-- lite-a-line games (Arlington, Over 18 Under, Bally Entry, Vee-A-Lite) — are
-- already excluded by the detector itself and so are absent here by design.
CREATE OR REPLACE VIEW _bingo_excluded AS
  SELECT * FROM (VALUES
    (173,  'Airways',                 'bagatelle; a reverse side is titled Bingo 36'),
    (334,  'Arrowhead',               'Keeney flipper pinball; bingo only in maker history'),
    (359,  'Atlas',                   'bagatelle boxed set (Atlas / Bingo 36 side)'),
    (473,  'Bally Derby',             'one-ball payout; note calls it the beginning of the bingo machines (precursor)'),
    (664,  'Big Broadcast',           'note names the Bingo Novelty Mfg Company, not the game type'),
    (776,  'Bing-A-Roll',             'roll-down payout, not a card bingo'),
    (785,  'Bingo Bango',             'Nasco flipper pinball conversion'),
    (790,  'Bingo Play Cards',        '1932 countertop card game'),
    (794,  'Bingo',                   'Gottlieb 1931 bagatelle merely named Bingo'),
    (1132, 'Carnival Pinball Game',   'generic nameless carnival games'),
    (1882, 'El Rancho',               'Keeney gambling upright disguised as a pinball; note only compares to bingos'),
    (2426, 'Gold Star',               'bagatelle boxed set (Atlas / Bingo 36 side)'),
    (2516, 'Grand Slam',              'Petaco flipper pinball (Gottlieb copy); bingo only in Franco-era context'),
    (2673, 'Hi Ball',                 'Tecnoplay pinball; bingo only as an unreleased conversion kit'),
    (2690, 'Hi-Hand',                 'Williams poker novelty; a bingo-style playfield, not a bingo'),
    (2754, 'Hit The Deck Play Cards', 'note names the Bingo Novelty Mfg Company'),
    (2864, 'Hullabaloo',              'replacement playfield; note merely lists bingo-named games'),
    (3027, 'Joker Wild',              'Bally poker novelty; a bingo-style playfield, not a bingo'),
    (3058, 'Juggle Ball',             'note names the Bingo Novelty Mfg Company'),
    (3843, 'Moon Shot',               'Bally flipper pinball (Gottlieb copy); bingo only in history'),
    (4134, 'Pamco Parlay Junior',     'one-ball payout precursor; note calls it the beginning of the bingo machines'),
    (4135, 'Pamco Parlay Senior',     'one-ball payout precursor; note calls it the beginning of the bingo machines'),
    (4136, 'Pamco Parlay',            'one-ball payout precursor; note calls it the beginning of the bingo machines'),
    (4973, 'Sevens',                  'Gottlieb whitewood pinball prototype; note says it played too much like a bingo'),
    (5132, 'SK-IL-RO',                'gambling pinball; note only compares its counter to bingo games'),
    (5166, 'Skill Race',              'Games Inc gambling pinball; bingo only in legislative context'),
    (5493, 'Stadium',                 'Como pinball; note is about Bally making bingos'),
    (5584, 'Startime',                'Keeney gambling pinball disguised as one; note compares to bingos'),
    (6012, 'The Pilot',               'note names the Bingo Novelty Mfg Company'),
    (6229, 'Touchdown',               'note: actually a 5-ball flipperless pin game (explicit denial)'),
    (6587, 'Watch My Line',           'Gottlieb; note: was not a Bingo in the traditional sense'),
    (4961, 'Serenade',                'United 1948 flipper pinball; note cross-references a different United bingo also named Serenade (caught structurally as serenade-5)'),
    -- Pre-1951 ancestors of the bingo (lite-a-line / card-lighting). Out of
    -- campaign scope: they predate the in-line bingo form (Bally Bright Lights,
    -- 1951), so they are not bingo-pinball. (Excluded per the campaign decision.)
    (787,  'Bingo-Cards',             'copy of PAMCO Lite-A-Line; a pre-bingo card-lighting game'),
    (3370, 'Line-O',                  '1936 number-lighting game with a backglass bingo card; precursor'),
    (4793, 'Roto Lite',               '1935 PAMCO lite-a-line; in-line scoring ancestor of the bingo'),
    -- Non-bingos with a 25-trap-hole grid the hole detector catches: a 5x5 hole
    -- field is near-definitive for bingo, but a few gambling/novelty games reuse
    -- the grid for a different game (keno, poker, pop-up novelty).
    (4395, 'Poker-eno',               'Evans keno/poker payout console; a 25-hole grid scored as poker, not in-line bingo'),
    (5845, 'Tango',                   'Evans payout console with an Electropak; not an in-line bingo'),
    (4569, 'Rallye',                  'Magister: note calls it a pin table (automobile-themed pinball), not a bingo'),
    (3037, 'Jolly Joker',             'Williams: note says rolldown play to score poker hands, not in-line bingo'),
    (5317, 'Space Glider',            'Williams pop-up-target novelty (15 shots per play), not a bingo'),
    (3336, 'L''Hirondelle',           'note calls it a pin table (bird/Eiffel-tower art, no cards/in-line); a 25-hole French novelty, not a bingo')
  ) AS t(id, name, reason);

-- Ambiguous / edge cases KEPT as candidates but tagged for editorial review.
-- These are the boundary calls for the campaign to make, not clear yes/no:
--   one-ball   one-ball bingo-family games (SIRMO/Splin/Bally). Same cabinets and
--              cards as the multi-card bingos, sold as a one-ball mode/model.
--   word-bingo Bally letter variants (Crosswords/Spelling-Bee) — a bingo playfield
--              scoring words, marketed for locations that refused bingos.
--   hybrid     Williams "combination bingo machine and pinball" games.
-- (The pre-1951 lite-a-line precursors were reviewed and dropped — they sit in
-- _bingo_excluded, not here.)
CREATE OR REPLACE VIEW _bingo_bucket AS
  SELECT * FROM (VALUES
    (3029, 'one-ball',   'Jokers & Ladders One Ball — one-ball, small bingo-type playfield'),
    (4066, 'one-ball',   'One Ball Bonus Multiplier — one-ball, small bingo-type playfield'),
    (4067, 'one-ball',   'One Ball Circus — one-ball bingo, export to Spain'),
    (4068, 'one-ball',   'One Ball Conti — one-ball, small bingo-type playfield'),
    (4182, 'one-ball',   'Party Games — one-ball, small bingo-type playfield, TFT'),
    (4204, 'one-ball',   'Penalty One Ball — SIRMO one-ball bingo'),
    (4205, 'one-ball',   'Penalty Une Bille — SIRMO one-ball bingo (France)'),
    (4455, 'one-ball',   'President One Ball — six-card one-ball bingo'),
    (6316, 'one-ball',   'Triple Joker — one-ball, small bingo-type playfield'),
    (6481, 'one-ball',   'Up ''n Down One Ball — one-ball, small bingo-type playfield'),
    (1516, 'word-bingo', 'Crosswords — Bally letter bingo; for locations that refused traditional bingos'),
    (5394, 'word-bingo', 'Spelling-Bee — same game as Crosswords, letters not numbers'),
    (1723, 'hybrid',     'Disk Jockey — Williams combination bingo machine and pinball'),
    (2232, 'hybrid',     'Four Corners — Williams; combines elements of a bingo machine with flipper pinball')
  ) AS t(id, bucket, note);

-- Bingo-ONLY manufacturers: makers whose entire catalog is in-line bingo (the
-- obscure European export houses). For these, the maker itself is the signal — it
-- catches the modern electronic six-card machines whose notes never say "bingo"
-- and whose notable_features carry no hole-count prose. Membership was verified
-- per maker by inspecting every one of their models (all bingos, zero non-bingo
-- game_format); SIRMO + Splin are additionally vouched by the export analysis and
-- bingo references. Do NOT add a maker here on a NULL-format count alone — a
-- pinball maker like Recel/Playmatic also shows "0 non-bingo formats" simply
-- because game_format is sparsely populated.
CREATE OR REPLACE VIEW _bingo_maker AS
  SELECT * FROM (VALUES
    ('SIRMO Games S.A.'), ('Splin S.A.'), ('WIMI Games'), ('G.A.A.'), ('SG'), ('TSCC')
  ) AS t(maker);

-- == 3 · ANALYSIS ============================================================
-- detect -> assemble -> classify. A candidate hunt (see scripts/analysis/README.md):
-- the shape is the two detectors, their union minus exclusions, then the review
-- slices.

-- detect --
-- Per-model free text, the model's structured trap/gobble-hole count, and the
-- FOUR detector flags. No single signal suffices, so a candidate is their union
-- (minus the vetted false positives).
CREATE OR REPLACE VIEW _bingo_signal AS
  WITH t AS (
    SELECT
      m.id, m.name, m.manufacturer_name AS maker, m.year, m.label,
      m.ipdb_notes AS notes,
      m.ipdb_notable_features AS notable_features,
      m.description,
      -- The model's structured trap/gobble-hole gameplay-feature count (the 5x5 =
      -- 25-hole bingo card grid, materialized as a real member with a count) —
      -- from the foundation's model_gameplay_features view, not a raw fc join.
      (SELECT f.feature_slug FROM model_gameplay_features f
        WHERE f.model_id = m.id AND f.feature_slug IN ('trap-holes', 'gobble-holes')
        ORDER BY f.count DESC NULLS LAST LIMIT 1) AS hole_feature,
      (SELECT max(f.count) FROM model_gameplay_features f
        WHERE f.model_id = m.id AND f.feature_slug IN ('trap-holes', 'gobble-holes')) AS hole_count
    FROM models m
  )
  SELECT
    id, name, maker, year, label, notes, notable_features, hole_feature, hole_count,
    -- by_word: the free text anywhere says "bingo".
    (lower(coalesce(notes, ''))            LIKE '%bingo%'
       OR lower(coalesce(notable_features, '')) LIKE '%bingo%'
       OR lower(coalesce(description, ''))      LIKE '%bingo%') AS by_word,
    -- by_struct: a bingo hole grid IN THE PROSE plus a card count or a Bally/United
    -- feature name. The count-before-cards form (`six cards`, `1 regular card`)
    -- keeps stray "score card" / "instruction card" prose from matching. This
    -- carries counts 18/20/21/24/28 the raw structured signal below can't (only 25
    -- is precise as a bare count — see by_hole25).
    (regexp_matches(lower(coalesce(notable_features, '')),
        '(trap holes|gobble holes) \((18|20|21|24|25|28)\)')
     AND (
        regexp_matches(lower(coalesce(notable_features, '')),
          '(one|two|three|four|five|six|seven|eight|nine|ten|[0-9]+)[ -]?([a-z]+ )?cards?')
        OR regexp_matches(lower(coalesce(notable_features, '')),
          '(magic|mystic) (squares|screen|lines?|card|numbers?)')
        OR lower(coalesce(notable_features, '')) LIKE '%magic-numbers%'
        OR lower(coalesce(notable_features, '')) LIKE '%wheel card%'
        OR lower(coalesce(notable_features, '')) LIKE '%in-line%'
     )) AS by_struct,
    -- by_hole25: a structured 25-trap-hole grid — the 5x5 bingo card, near-definitive
    -- (173 models carry it; none holds a non-bingo game_format). No card/feature
    -- conjunct needed at 25; it catches modern machines whose prose lost the hole
    -- text. Only 25 is safe bare: 18/20/21/24/28 structured counts are dominated by
    -- 1940s one-ball payout games, ticket games and precursors, so those must ride
    -- by_struct's card/feature conjunct instead.
    (hole_feature = 'trap-holes' AND hole_count = 25) AS by_hole25,
    -- by_maker: a model by a verified bingo-only manufacturer (see _bingo_maker).
    (maker IN (SELECT maker FROM _bingo_maker)) AS by_maker
  FROM t;

-- assemble --
-- One row per candidate: the union of the detectors, minus the vetted false
-- positives, tagged with its review bucket (default 'core').
--
-- A fifth signal, by_lineage, rides on top of the other four: a model with a
-- model_edge (conversion / variant / copy / retheme) whose target is itself a
-- core bingo. This catches converted bingos that describe themselves only via
-- their donor — e.g. Bally 'Bamboo', a repainted 'Orient' — carrying no bingo
-- word, no hole-count prose, no bingo-only maker. It keys on the CORE detector
-- set, NOT the applied game_format, so it reproduces without 0172 applied. It is
-- genre-preserving for these relationship types, but review each: a conversion
-- CAN change a game's type (the precision check found zero doing so today).
CREATE OR REPLACE VIEW bingo_candidates AS
  WITH core AS (
    SELECT s.* FROM _bingo_signal s
    WHERE (s.by_word OR s.by_struct OR s.by_hole25 OR s.by_maker)
      AND s.id NOT IN (SELECT id FROM _bingo_excluded)
  ),
  lineage_ids AS (
    SELECT DISTINCT e.model_id AS id
    FROM model_edges e
    WHERE e.target_id IN (SELECT id FROM core)
      AND e.model_id NOT IN (SELECT id FROM core)
      AND e.model_id NOT IN (SELECT id FROM _bingo_excluded)
  )
  SELECT
    s.id, s.name, s.maker, s.year, s.label,
    s.by_word, s.by_struct, s.by_hole25, s.by_maker,
    (s.id IN (SELECT id FROM lineage_ids)) AS by_lineage,
    s.hole_feature, s.hole_count,
    coalesce(b.bucket, 'core') AS bucket,
    s.notes, s.notable_features
  FROM _bingo_signal s
  LEFT JOIN _bingo_bucket b ON b.id = s.id
  WHERE s.id IN (SELECT id FROM core) OR s.id IN (SELECT id FROM lineage_ids)
  ORDER BY s.maker NULLS LAST, s.name;

-- review --
-- The human-review queue. Flagged buckets and word-only rows float to the top
-- (they need reading); the structural core sinks (a hole grid + cards is a bingo
-- on its face). Full note + notable_features inline so no re-fetching is needed.
CREATE OR REPLACE VIEW bingo_review AS
  SELECT
    id, label, maker, year, bucket,
    -- which signals fired, strongest-evidence first
    CASE WHEN by_struct OR by_hole25 THEN 'hole-grid'
         WHEN by_word                THEN 'word'
         WHEN by_maker               THEN 'maker-only'
         WHEN by_lineage             THEN 'lineage-only'
         ELSE '?' END AS confidence,
    by_word, by_struct, by_hole25, by_maker, by_lineage, hole_count,
    notes, notable_features
  FROM bingo_candidates
  ORDER BY (bucket = 'core'), bucket,
           (by_lineage AND NOT by_word AND NOT by_struct AND NOT by_hole25 AND NOT by_maker) DESC,
           (by_maker AND NOT by_word AND NOT by_struct AND NOT by_hole25) DESC,
           maker NULLS LAST, name;

-- Generator feed — one row per candidate with everything gen.py needs to emit
-- the patch entry, so detection + vetting stay single-sourced in this file:
--   kind        'struct' → note-only, reasoning from the model's own hole-grid
--                          gameplay data (no cite; the evidence IS catalog data).
--               'word'   → cite the verbatim "bingo" statement from IPDB free text.
--               'maker'  → note-only, reasoning from the bingo-only manufacturer
--                          (a modern six-card machine with no hole prose, no cite).
--               'lineage'→ note-only, reasoning from the catalog edge to a bingo
--                          (a converted bingo with no signal of its own, no cite).
--   hole_count  the model's structured trap/gobble-hole count (struct rows; drives
--               the note); hole_feature names which.
--   maker       the manufacturer (drives the maker-row note); ipdb_id the word cite.
--   lineage_via the donor bingo + relationship, for the lineage-row note.
CREATE OR REPLACE VIEW bingo_patch_rows AS
  SELECT
    mm.slug,
    mm.ipdb_id,
    CASE WHEN c.by_struct OR c.by_hole25 THEN 'struct'
         WHEN c.by_word                  THEN 'word'
         WHEN c.by_maker                 THEN 'maker'
         ELSE 'lineage' END AS kind,
    c.bucket,
    c.maker,
    c.hole_feature,
    c.hole_count,
    -- clean phrase for the lineage note: 'conversion of Orient', 'variant of X',
    -- 'conversion kit of X' — strip the '_of' suffix and underscores so the type
    -- reads naturally before the appended ' of <target>'.
    (SELECT replace(replace(e.relationship_type, '_of', ''), '_', ' ') || ' of ' || t.name
       FROM model_edges e JOIN bingo_candidates t ON t.id = e.target_id
      WHERE e.model_id = c.id ORDER BY t.name LIMIT 1) AS lineage_via,
    c.notes,
    c.notable_features
  FROM bingo_candidates c
  JOIN models mm ON mm.id = c.id
  ORDER BY mm.slug;

-- The confirmed false positives, with the text that tripped the detector — so
-- the exclusion calls stay auditable, not buried in a VALUES list.
CREATE OR REPLACE VIEW bingo_excluded_review AS
  SELECT e.id, s.label, e.reason, s.by_word, s.by_struct, s.notes, s.notable_features
  FROM _bingo_excluded e
  JOIN _bingo_signal s ON s.id = e.id
  ORDER BY s.name;

-- == 4 · SUMMARY & CHECKS ====================================================
-- The honest-prose tail. Numbers the write-up quotes come from bingo_summary,
-- never hand-counted; bingo_checks is empty when the data is healthy.

CREATE OR REPLACE VIEW bingo_summary AS
            SELECT 'signal_total'       AS metric, count(*) AS value FROM _bingo_signal WHERE by_word OR by_struct OR by_hole25 OR by_maker
  UNION ALL SELECT 'by_word',           count(*)                     FROM _bingo_signal WHERE by_word
  UNION ALL SELECT 'by_struct',         count(*)                     FROM _bingo_signal WHERE by_struct
  UNION ALL SELECT 'by_hole25',         count(*)                     FROM _bingo_signal WHERE by_hole25
  UNION ALL SELECT 'by_maker',          count(*)                     FROM _bingo_signal WHERE by_maker
  UNION ALL SELECT 'by_lineage',        count(*)                     FROM bingo_candidates WHERE by_lineage
  UNION ALL SELECT 'excluded',          count(*)                     FROM _bingo_excluded
  UNION ALL SELECT 'candidates',        count(*)                     FROM bingo_candidates
  UNION ALL SELECT 'candidates_core',   count(*)                     FROM bingo_candidates WHERE bucket = 'core'
  UNION ALL SELECT 'candidates_flagged',count(*)                     FROM bingo_candidates WHERE bucket <> 'core'
  UNION ALL SELECT 'kind_struct',       count(*)                     FROM bingo_patch_rows WHERE kind = 'struct'
  UNION ALL SELECT 'kind_word',         count(*)                     FROM bingo_patch_rows WHERE kind = 'word'
  UNION ALL SELECT 'kind_maker',        count(*)                     FROM bingo_patch_rows WHERE kind = 'maker'
  UNION ALL SELECT 'kind_lineage',      count(*)                     FROM bingo_patch_rows WHERE kind = 'lineage'
  ORDER BY metric;

CREATE OR REPLACE VIEW bingo_checks AS
  -- Every excluded id must still be a live detector hit (else the exclusion is
  -- stale — the row it removed no longer exists).
            SELECT 'stale_exclusion' AS check, e.id, e.name AS detail
            FROM _bingo_excluded e
            WHERE NOT EXISTS (SELECT 1 FROM _bingo_signal s WHERE s.id = e.id AND (s.by_word OR s.by_struct OR s.by_hole25 OR s.by_maker))
  -- Every bucketed id must be a live candidate (not excluded, still detected).
  UNION ALL SELECT 'stale_bucket', b.id, b.bucket
            FROM _bingo_bucket b
            WHERE NOT EXISTS (SELECT 1 FROM bingo_candidates c WHERE c.id = b.id)
  -- No id may be both excluded and bucketed.
  UNION ALL SELECT 'excluded_and_bucketed', b.id, b.bucket
            FROM _bingo_bucket b JOIN _bingo_excluded e ON e.id = b.id
  -- A candidate that ALREADY carries a non-bingo game_format is a conflict to
  -- resolve before the patch sets bingo-pinball.
  UNION ALL SELECT 'existing_nonbingo_format', c.id, m.game_format_slug
            FROM bingo_candidates c
            JOIN models m ON m.id = c.id
            WHERE m.game_format_slug IS NOT NULL AND m.game_format_slug <> 'bingo-pinball'
  -- ANCHORS: a known example must still fire each detector. This is the only class
  -- that catches a whole detector going DARK — a renamed foundation column (the
  -- session that renamed model->models / notes->ipdb_notes would have silently
  -- zeroed a detector) or a rotted regex. A row-level invariant can't see the set
  -- silently shrink; these can. One anchor per detector.
  UNION ALL SELECT 'anchor_word_dark',    1378, 'Coney Island'  WHERE NOT EXISTS (SELECT 1 FROM _bingo_signal WHERE id = 1378 AND by_word)
  UNION ALL SELECT 'anchor_struct_dark',   102, 'Acapulco'      WHERE NOT EXISTS (SELECT 1 FROM _bingo_signal WHERE id = 102  AND by_struct)
  UNION ALL SELECT 'anchor_hole25_dark',   102, 'Acapulco'      WHERE NOT EXISTS (SELECT 1 FROM _bingo_signal WHERE id = 102  AND by_hole25)
  UNION ALL SELECT 'anchor_maker_dark',   4204, 'Penalty One Ball' WHERE NOT EXISTS (SELECT 1 FROM _bingo_signal WHERE id = 4204 AND by_maker)
  UNION ALL SELECT 'anchor_lineage_dark',  492, 'Bamboo'        WHERE NOT EXISTS (SELECT 1 FROM bingo_candidates WHERE id = 492 AND by_lineage);
