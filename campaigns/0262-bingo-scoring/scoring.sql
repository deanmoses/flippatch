-- Scoring-method attachments for the bingo corpus, from bingo.cdyn.com's per-machine
-- Features blocks.
--
-- Goal: give `in-line-scoring`, `section-scoring` and `next-game-award` the model
-- attachments they have never had. The three records were created in ../../patches/
-- 0244-bingo-feature-vocab.yaml and described in 0260-bingo-scoring-descriptions.yaml,
-- and between them they carry ZERO carriers against 311 bingo-pinball models — so the
-- vocabulary exists, the prose exists, and no machine points at either. That is what
-- forced 0260's descriptions to name Carnival Queen and Border Beauty as bare prose
-- mentions no link could carry.
--
-- WHAT IS BEING CLASSIFIED. How a bingo machine decides a win: lining lit numbers up
-- on the card (in-line), or collecting them inside a colored area regardless of
-- adjacency (section). The two coexist — a magic screen game pays lines in the home
-- position and sections as the screen slides — so this is not a partition, and a
-- machine may carry both. `next-game-award` is the third: something won in this game
-- that switches a feature on in the NEXT one.
--
-- SOURCE. bingo.cdyn.com's per-machine pages, whose `Game Parameters` table ends in a
-- `Features` cell drawn from the site's own vocabulary (defined on machines/
-- features.html). Read from pinexplore's web scrape cache; see extract_cdyn_features.py
-- in this dir, which writes cdyn_features.tsv.
--
-- WHY NOT THE ALPHA LISTING. ../0181-bingo-years/cdyn_machines.tsv already parses
-- cdyn's index page, and its `Game Type` column (three-card, magic screen, mystic
-- lines) correlates with scoring method but does not state it: mystic-line games score
-- sections only, magic-screen games score both, and the early card games score lines —
-- but the type name is a marketing label, and reading a scoring method out of it is
-- inference. The per-machine Features cell states the method in the source's own
-- words, per machine, which is what a cite needs.
--
-- HOW TO RUN. cwd must be the flipcommons checkout; `make analyze` handles that:
--
--     F=campaigns/0262-bingo-scoring/scoring.sql
--     make analyze FILE=$F PREFIX=scoring                        # summary, gated on checks
--     make analyze FILE=$F Q="FROM scoring_patch_rows;"          # what gen.py emits
--     make analyze FILE=$F Q="FROM scoring_rejected;"            # what the gate held back
--     make analyze FILE=$F Q="FROM scoring_unmatched_source;"    # cdyn pages no model claimed
--
-- STRUCTURE — the four sections every analysis file has (flipcommons'
-- scripts/analysis/README.md): 1 FOUNDATION, 2 REFERENCE, 3 ANALYSIS, 4 SUMMARY & CHECKS.

-- ── 1 · FOUNDATION ─────────────────────────────────────────────────────────
-- The catalog foundation is already in the session — the runner attaches it before
-- reading this file, so there is no `.read` of it here. (../0181-bingo-years/years.sql
-- still carries one, from before the foundation moved to scripts/analysis/sql/; that
-- line now fails outright rather than reading as a no-op.)
--
-- flippatch's evidence bridge — pinexplore's web scrape cache as `ev`. Every row this
-- campaign emits cites a DIFFERENT page (the machine's own), so the quote check below
-- joins per row rather than testing one page; that is the whole reason the bridge is
-- worth reading here.
.read ../flippatch/scripts/analysis/evidence.sql

-- ── 2 · REFERENCE ──────────────────────────────────────────────────────────

-- The source rows, one per cdyn machine page carrying a Features cell.
CREATE OR REPLACE TABLE cdyn AS
  SELECT * FROM read_csv(
    COALESCE(NULLIF(getenv('FLIPPATCH_DIR'), ''), '../flippatch')
      || '/campaigns/0262-bingo-scoring/cdyn_features.tsv',
    delim = '\t', header = true, quote = '',
    columns = {'url':'VARCHAR','maker_dir':'VARCHAR','maker':'VARCHAR','game':'VARCHAR',
               'number':'VARCHAR','year':'VARCHAR','game_type':'VARCHAR',
               'features_row':'VARCHAR','features':'VARCHAR'});

-- cdyn's URL directory -> the catalog's manufacturer name. Hand-maintained, and keyed
-- on the DIRECTORY rather than the page's display maker because the directory is the
-- stable half of the URL this campaign cites. A maker absent here contributes no rows,
-- which is the safe default — an unmapped maker cannot produce a wrong attachment,
-- only a missing one. `scoring_checks` reports both halves so a typo cannot go quiet,
-- and `scoring_summary` counts the source makers left unmapped.
CREATE OR REPLACE VIEW _maker_map AS
  SELECT * FROM (VALUES
    ('bally',              'Bally'),
    ('sirmo',              'SIRMO Games S.A.'),
    ('united',             'United'),
    ('splin',              'Splin S.A.'),
    ('wimi',               'WIMI Games'),
    ('sg',                 'SG'),
    ('gaa',                'G.A.A.'),
    ('keeney',             'Keeney'),
    ('playmatic',          'Playmatic'),
    ('williams',           'Williams'),
    ('interflip',          'Interflip'),
    ('recreativos_franco', 'Recreativos Franco'),
    -- One machine, and the catalog spells the maker as its full corporate mouthful.
    ('universal',          'Universal Industries, Inc. (Chicago) A subsidiary of United Manufacturing Co.')
  ) AS t(maker_dir, catalog_maker);
-- STILL UNMAPPED: cdyn's `helco` (one machine, "New Five"), which the catalog does not
-- carry at all — a missing MODEL, recorded in ../0239-descriptions/gaps.jsonl rather
-- than papered over with a map entry pointing at nothing.

-- cdyn's per-machine feature term -> the catalog's gameplay-feature slug.
--
-- Two of these are direct synonyms. The rest are the NEXT GAME AWARD family, and they
-- are here because cdyn's own features.html defines the parent by enumerating them:
-- "next game award [...] See: - ballyhole - red letter game - ok game - futurity game
-- - sunny circles". A machine listing only an instance therefore evidences the parent
-- through that page, which is why `_ngw_via_instance` rows below ship a SECOND cite to
-- features.html — the machine page alone does not contain the words.
--
-- DELIBERATELY ABSENT: United's `lite-a-name`, which 0260's description glosses as the
-- same idea. features.html describes it as a progressive award "like Bally's futurity"
-- but does NOT list it under next game award, and the difference is real — lite-a-name
-- pays an in-line score on completion rather than setting up the next game. Attaching
-- it would be our inference, not the source's claim. It stays a gaps.jsonl row.
CREATE OR REPLACE VIEW _feature_map AS
  SELECT * FROM (VALUES
    ('in-line scoring',  'in-line-scoring',  'direct'),
    ('section scoring',  'section-scoring',  'direct'),
    ('next game award',  'next-game-award',  'direct'),
    ('ballyhole',        'next-game-award',  'instance'),
    ('red letter game',  'next-game-award',  'instance'),
    ('OK game',          'next-game-award',  'instance'),
    ('futurity',         'next-game-award',  'instance'),
    ('sunny circles',    'next-game-award',  'instance')
  ) AS t(cdyn_term, feature_slug, evidence_kind);

-- ── 3 · ANALYSIS ───────────────────────────────────────────────────────────
-- Shape: normalize -> match (two keys, one per maker class) -> gate -> emit.

-- Number keys, EXACT and LOOSE. Lifted from ../0181-bingo-years/years.sql, where the
-- distinction was calibrated: Bally's trailing letter is NOT a variant marker (#634 is
-- 'Fun Way' and #634-A is 'Lotta Fun'), so it must not be normalized away when both
-- sides carry it — but the catalog sometimes holds the stem where cdyn has the letter,
-- so exact-only would miss those. Exact first, stem as fallback, name agreement gating
-- the fallback. Analysis-local on purpose: the convention is a fact about Bally.
CREATE OR REPLACE MACRO _num_exact(s) AS NULLIF(upper(trim(COALESCE(s, ''))), '');
CREATE OR REPLACE MACRO _num_loose(s) AS
  NULLIF(upper(regexp_replace(COALESCE(s, ''), '-[A-Za-z]$', '')), '');

-- The models in scope: every live model of a maker cdyn covers whose game format is
-- bingo-pinball OR UNSET. Unlike 0181 this is not restricted to models missing the
-- field — a gameplay-feature attachment is a membership, not a scalar, so re-asserting
-- one the catalog already holds is a no-op rather than an overwrite. The emitted set is
-- filtered against existing attachments at the end instead, so the patch stays a diff.
--
-- WHY UNSET FORMAT IS IN SCOPE. Restricting to `game_format_slug = 'bingo-pinball'` was
-- the first cut, and it silently lost real bingos: cdyn's Bally #1025 'Bali', #634 'Fun
-- Way', #912 'Hole In One' and #913 'Stock Market' are all in the catalog, under the
-- right maker and the right number, with NO game format recorded at all. They dropped
-- out of scope and surfaced in `scoring_unmatched_source` looking like missing MODELS,
-- which they are not. A model whose format is unset is a model the catalog has not
-- classified, not a model the catalog says is something else — so it is in scope, while
-- a model carrying a DIFFERENT format is not.
--
-- That widening is only safe because of the gate below: Bally alone has 592
-- format-unset models, so the weak key (name) reaching into them needs corroboration
-- the strong key (the maker's own game number) does not.
CREATE OR REPLACE TABLE _target_models AS
  SELECT
    m.id, m.slug, m.name, m.label, m.manufacturer_name, m.year,
    m.game_format_slug IS NOT NULL AS format_known,
    m.manufacturer_model_identifier AS model_number,
    name_key(m.name) AS nkey,
    _num_exact(m.manufacturer_model_identifier) AS numkey_exact,
    _num_loose(m.manufacturer_model_identifier) AS numkey_loose
  FROM models m
  WHERE (m.game_format_slug = 'bingo-pinball' OR m.game_format_slug IS NULL)
    AND m.manufacturer_name IN (SELECT catalog_maker FROM _maker_map);

-- The source pages, keyed, with the catalog maker resolved.
CREATE OR REPLACE TABLE _cdyn_keyed AS
  SELECT
    mm.catalog_maker AS maker, c.url, c.game, c.number, c.year, c.game_type,
    c.features_row, c.features,
    name_key(c.game) AS nkey,
    TRY_CAST(c.year AS INTEGER) AS year_value,
    -- "unknown" is cdyn's literal null for this column; treat it as absent rather than
    -- letting it become a join key that matches every other unknown.
    CASE WHEN lower(c.number) IN ('unknown', '') THEN NULL ELSE _num_exact(c.number) END AS numkey_exact,
    CASE WHEN lower(c.number) IN ('unknown', '') THEN NULL ELSE _num_loose(c.number) END AS numkey_loose
  FROM cdyn c
  JOIN _maker_map mm ON mm.maker_dir = c.maker_dir;

-- MATCH, on the strongest key each maker class offers — the number where the maker
-- numbers its games (Bally, Williams), the name within the maker everywhere else.
CREATE OR REPLACE TABLE _matched AS
  WITH by_number_exact AS (
    SELECT t.id, c.url, 'number' AS matched_on, (t.nkey = c.nkey) AS name_agrees
    FROM _target_models t
    JOIN _cdyn_keyed c ON c.numkey_exact = t.numkey_exact AND c.maker = t.manufacturer_name
    WHERE t.numkey_exact IS NOT NULL
  ),
  by_number_loose AS (
    SELECT t.id, c.url, 'number-stem' AS matched_on, (t.nkey = c.nkey) AS name_agrees
    FROM _target_models t
    JOIN _cdyn_keyed c ON c.numkey_loose = t.numkey_loose AND c.maker = t.manufacturer_name
    WHERE t.numkey_loose IS NOT NULL
      AND t.id NOT IN (SELECT id FROM by_number_exact)
  ),
  by_name AS (
    SELECT t.id, c.url, 'name' AS matched_on, TRUE AS name_agrees
    FROM _target_models t
    JOIN _cdyn_keyed c ON c.nkey = t.nkey AND c.maker = t.manufacturer_name
    WHERE t.id NOT IN (SELECT id FROM by_number_exact)
      AND t.id NOT IN (SELECT id FROM by_number_loose)
      AND (
        -- The model has no number: the name within the maker is all there is.
        t.numkey_exact IS NULL
        -- Or the model has one and the SOURCE PAGE does not, so there is no number to
        -- match and none to contradict. Universal's '5 Star' is the case: the catalog
        -- numbers it 541, cdyn's page records the number as "unknown", and requiring a
        -- number match would strand it forever. This is NOT the Broadway/Tahiti hazard
        -- 0181 built the number key against — that was two NUMBERED cdyn rows sharing a
        -- name, where the number was the discriminator and the name key threw it away.
        -- Here there is no second number to prefer. The gate demands the year agree.
        OR c.numkey_exact IS NULL
      )
  ),
  unioned AS (
    SELECT * FROM by_number_exact
    UNION ALL SELECT * FROM by_number_loose
    UNION ALL SELECT * FROM by_name
  ),
  -- Both sides' years, for the tie-break below.
  dated AS (
    SELECT u.*, t.year AS catalog_year, c.year_value AS cdyn_year,
           (t.year IS NOT NULL AND c.year_value IS NOT NULL AND t.year = c.year_value) AS year_agrees
    FROM unioned u
    JOIN _target_models t ON t.id = u.id
    JOIN _cdyn_keyed c ON c.url = u.url
  ),
  -- YEAR TIE-BREAK. United reused its game names across eras — a 1940s one-ball and a
  -- 1950s bingo both called Havana, Hawaii, Mexico, Nevada, Rio, Singapore, South Seas,
  -- Tropicana, Serenade, Show Boat, Brazil, Manhattan — and neither carries a game
  -- number, so the name key lands on both and the ambiguity gate rejected all of them.
  -- But cdyn's page states the year, and exactly ONE of the two catalog models matches
  -- it. That is not a coin flip: it is a second agreeing fact, the same standard the
  -- number key is held to when the name has to corroborate it.
  --
  -- Applied only where it DECIDES: a group with one year-agreeing candidate keeps that
  -- candidate and drops the rest. A group where two candidates agree (United's Rodeo, one
  -- 1-card and one 3-card model of the same 1953 game) or where none does (Sirmo's two
  -- Golden Gates, both year-less) is left whole, so it still fails the ambiguity gate
  -- below and lands in `scoring_rejected` for a human.
  decided AS (
    SELECT d.*,
           count(*) FILTER (WHERE d.year_agrees) OVER (PARTITION BY d.url) AS url_year_hits,
           count(*) FILTER (WHERE d.year_agrees) OVER (PARTITION BY d.id) AS id_year_hits,
           count(*) OVER (PARTITION BY d.url) AS url_candidates,
           count(*) OVER (PARTITION BY d.id) AS id_candidates
    FROM dated d
  ),
  resolved AS (
    SELECT * FROM decided
    WHERE (url_candidates = 1 OR url_year_hits <> 1 OR year_agrees)
      AND (id_candidates = 1 OR id_year_hits <> 1 OR year_agrees)
  )
  -- Ambiguity counted AFTER tier selection and the tie-break, so a model resolved
  -- exactly is not re-flagged by the looser key it never used, and a pairing the year
  -- decided is not re-flagged by the candidate it displaced.
  SELECT r.id, r.url, r.matched_on, r.name_agrees, r.year_agrees,
         count(*) OVER (PARTITION BY r.id) AS n_source,
         count(*) OVER (PARTITION BY r.url) AS n_model
  FROM resolved r;

-- GATE. An attachment is emitted only when the model/page pairing is unambiguous in
-- BOTH directions, the names agree where a number did the matching, and the two sides
-- agree about the year where both state one. The year test is the corroborating check
-- this campaign can afford that 0181 could not: 0181 FILLED null years from this same
-- site, so most bingo models now carry a year, and a pairing that disagrees about it
-- is pairing two different machines.
CREATE OR REPLACE TABLE _scored AS
  SELECT
    t.id, t.slug, t.label, t.name, t.manufacturer_name, t.model_number, t.year AS catalog_year,
    t.format_known,
    c.url, c.game AS cdyn_game, c.number AS cdyn_number, c.game_type AS cdyn_type,
    c.year_value AS cdyn_year, c.features_row, c.features,
    m.matched_on, m.name_agrees, m.year_agrees, m.n_source, m.n_model,
    CASE
      WHEN m.n_source > 1 THEN 'model matches several source pages'
      WHEN m.n_model > 1  THEN 'source page matches several models'
      WHEN NOT m.name_agrees THEN 'number matched, name differs'
      WHEN t.year IS NOT NULL AND c.year_value IS NOT NULL AND t.year <> c.year_value
        THEN 'year disagrees'
      -- The corroboration the widened scope needs. A NAME match onto a model the catalog
      -- has not classified is the one combination with nothing else holding it down:
      -- United and Keeney built shuffle alleys and flipper games under the same roof,
      -- and a same-named non-bingo game of the right maker would take the attachment
      -- silently. Requiring both sides to state the same year makes the pairing rest on
      -- two agreeing facts instead of one. A number match needs no such crutch — the
      -- maker's own game number already agreed, and the name agreed with it.
      WHEN m.matched_on = 'name' AND NOT t.format_known
           AND (t.year IS NULL OR c.year_value IS NULL)
        THEN 'name match onto unclassified model, year unconfirmed'
      -- Same corroboration, for the other weak case: a model the catalog NUMBERS,
      -- matched by name because the source page states no number. The catalog thought
      -- the number worth recording, so a pairing that cannot use it earns its keep with
      -- the year instead.
      WHEN m.matched_on = 'name' AND t.numkey_exact IS NOT NULL
           AND (t.year IS NULL OR c.year_value IS NULL)
        THEN 'numbered model matched by name only, year unconfirmed'
    END AS reject_reason
  FROM _target_models t
  JOIN _matched m ON m.id = t.id
  JOIN _cdyn_keyed c ON c.url = m.url;

-- The same match run over every bingo model of a mapped maker, regardless of whether it
-- still needs an attachment. Nothing is emitted from it — it exists so the anchor checks
-- can test whether the KEYS still resolve once the emitted set has drained to zero,
-- which is success rather than breakage and indistinguishable from a broken join
-- without a probe that ignores the backlog.
CREATE OR REPLACE TABLE _match_probe AS
  SELECT m.slug, m.name, m.manufacturer_name, c.url, c.game AS cdyn_game, c.number AS cdyn_number,
         CASE WHEN c.numkey_exact IS NOT NULL AND c.numkey_exact = _num_exact(m.manufacturer_model_identifier)
              THEN 'number' ELSE 'name' END AS matched_on,
         (name_key(m.name) = c.nkey) AS name_agrees
  FROM models m
  JOIN _cdyn_keyed c
    ON c.maker = m.manufacturer_name
   AND (
     (c.numkey_exact IS NOT NULL AND c.numkey_exact = _num_exact(m.manufacturer_model_identifier))
     OR c.nkey = name_key(m.name)
   );

-- The gated pairs, exploded to one row per (model, cdyn feature term). A machine listing
-- several terms of one family (ballyhole AND OK game) collapses to one attachment below.
CREATE OR REPLACE TABLE _claims AS
  SELECT s.*, f.cdyn_term, f.feature_slug, f.evidence_kind
  FROM _scored s
  JOIN _feature_map f
    ON list_contains(string_split(s.features, '|'), f.cdyn_term)
  WHERE s.reject_reason IS NULL;

-- emit ── one row per (model, feature), already filtered against what the catalog holds,
-- so the patch is a diff rather than a re-assertion of 100 memberships it already has.
--
-- `quote` is the machine's own Features row, verbatim from the cached page: cdyn's
-- complete feature reading of that machine, which is the evidence the claim rests on
-- and is what a reviewer can ctrl-F on the cited page. `verify-quote-verbatim` collapses
-- whitespace on both sides, so the pipe-delimited row verifies as a substring.
--
-- `needs_family_cite` marks a next-game-award row evidenced ONLY by an instance term:
-- gen.py gives those a second cite to features.html, which is the page that says the
-- instance IS a next game award. A machine listing the parent term directly needs no
-- such crutch.
CREATE OR REPLACE TABLE scoring_patch_rows AS
  SELECT
    c.id, c.slug, c.label, c.manufacturer_name, c.url, c.feature_slug,
    c.features_row AS quote,
    any_value(c.matched_on) AS matched_on,
    string_agg(DISTINCT c.cdyn_term, ', ' ORDER BY c.cdyn_term) AS cdyn_terms,
    bool_and(c.evidence_kind = 'instance') AS needs_family_cite
  FROM _claims c
  WHERE NOT EXISTS (
    SELECT 1 FROM model_gameplay_features mgf
    WHERE mgf.model_id = c.id AND mgf.feature_slug = c.feature_slug)
  GROUP BY c.id, c.slug, c.label, c.manufacturer_name, c.url, c.feature_slug, c.features_row
  ORDER BY c.slug, c.feature_slug;

CREATE OR REPLACE VIEW scoring_rejected AS
  SELECT reject_reason, id, slug, label, model_number, catalog_year,
         cdyn_game, cdyn_number, cdyn_year, url, matched_on, n_source, n_model
  FROM _scored WHERE reject_reason IS NOT NULL
  ORDER BY reject_reason, label;

-- cdyn pages no catalog model claimed — the campaign's blind spot, and the place a
-- missing MODEL record shows up rather than a missing attachment.
CREATE OR REPLACE VIEW scoring_unmatched_source AS
  SELECT c.maker, c.game, c.number, c.year, c.game_type, c.url
  FROM _cdyn_keyed c
  WHERE NOT EXISTS (SELECT 1 FROM _matched m WHERE m.url = c.url)
  ORDER BY c.maker, c.game;

-- ── 4 · SUMMARY & CHECKS ───────────────────────────────────────────────────

CREATE OR REPLACE VIEW scoring_summary AS
  SELECT 'bingo_models_total' AS metric,
    (SELECT count(*) FROM models WHERE game_format_slug = 'bingo-pinball') AS value
  UNION ALL SELECT 'models_in_scope',   (SELECT count(*) FROM _target_models)
  UNION ALL SELECT 'models_in_scope_format_unset',
    (SELECT count(*) FROM _target_models WHERE NOT format_known)
  -- Emitted rows landing on a model the catalog has not classified. Every one of these
  -- is also a missing `game_format` the catalog should carry — bycatch for gaps.jsonl,
  -- not something this patch asserts.
  UNION ALL SELECT 'patch_rows_format_unset',
    (SELECT count(*) FROM scoring_patch_rows r JOIN models m ON m.id = r.id
     WHERE m.game_format_slug IS NULL)
  UNION ALL SELECT 'source_pages',      (SELECT count(*) FROM cdyn)
  UNION ALL SELECT 'source_pages_mapped', (SELECT count(*) FROM _cdyn_keyed)
  UNION ALL SELECT 'source_makers_unmapped',
    (SELECT count(DISTINCT maker_dir) FROM cdyn WHERE maker_dir NOT IN (SELECT maker_dir FROM _maker_map))
  UNION ALL SELECT 'matched_models',    (SELECT count(DISTINCT id) FROM _matched)
  UNION ALL SELECT 'gated_models',      (SELECT count(*) FROM _scored WHERE reject_reason IS NULL)
  -- Name matches whose year corroborates them. Not all of these needed the tie-break,
  -- but it is the population the tie-break draws from and the one to watch if the year
  -- key ever drifts.
  UNION ALL SELECT 'gated_name_matches_year_confirmed',
    (SELECT count(*) FROM _scored WHERE reject_reason IS NULL AND year_agrees AND matched_on = 'name')
  UNION ALL SELECT 'rejected',          (SELECT count(*) FROM scoring_rejected)
  UNION ALL SELECT 'unmatched_source_pages', (SELECT count(*) FROM scoring_unmatched_source)
  UNION ALL SELECT 'patch_rows',        (SELECT count(*) FROM scoring_patch_rows)
  UNION ALL SELECT 'patch_rows_in_line',  (SELECT count(*) FROM scoring_patch_rows WHERE feature_slug = 'in-line-scoring')
  UNION ALL SELECT 'patch_rows_section',  (SELECT count(*) FROM scoring_patch_rows WHERE feature_slug = 'section-scoring')
  UNION ALL SELECT 'patch_rows_next_game', (SELECT count(*) FROM scoring_patch_rows WHERE feature_slug = 'next-game-award')
  UNION ALL SELECT 'patch_rows_family_cite', (SELECT count(*) FROM scoring_patch_rows WHERE needs_family_cite)
  UNION ALL SELECT 'already_attached',
    (SELECT count(*) FROM _claims c WHERE EXISTS (
       SELECT 1 FROM model_gameplay_features mgf
       WHERE mgf.model_id = c.id AND mgf.feature_slug = c.feature_slug))
  ORDER BY metric;

-- The features.html page, which is what a `needs_family_cite` row's second cite points
-- at and what `_feature_map`'s instance rows rest on.
CREATE OR REPLACE VIEW _features_page AS
  SELECT * FROM evidence_pages WHERE url = 'https://bingo.cdyn.com/machines/features.html';

-- Empty when healthy.
CREATE OR REPLACE VIEW scoring_checks AS
  -- Vocabulary: every mapped catalog maker must exist, or the map has a typo and
  -- silently contributes nothing.
  SELECT 'maker_map_unknown_catalog_maker' AS check, NULL::BIGINT AS id, mm.catalog_maker AS detail
  FROM _maker_map mm
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.manufacturer_name = mm.catalog_maker)
  UNION ALL
  SELECT 'maker_map_unknown_cdyn_dir', NULL::BIGINT, mm.maker_dir
  FROM _maker_map mm
  WHERE NOT EXISTS (SELECT 1 FROM cdyn c WHERE c.maker_dir = mm.maker_dir)
  UNION ALL
  -- Vocabulary: every feature this campaign attaches must be a live catalog record.
  SELECT 'feature_slug_unknown', NULL::BIGINT, f.feature_slug
  FROM (SELECT DISTINCT feature_slug FROM _feature_map) f
  WHERE NOT EXISTS (SELECT 1 FROM gameplay_features g WHERE g.slug = f.feature_slug)
  UNION ALL
  -- Vocabulary: every cdyn term in the map must still appear on some machine page. A
  -- renamed term would zero its detector with no error — the failure mode the analysis
  -- README calls out as invisible.
  SELECT 'feature_term_dark', NULL::BIGINT, f.cdyn_term
  FROM _feature_map f
  WHERE NOT EXISTS (
    SELECT 1 FROM cdyn c WHERE list_contains(string_split(c.features, '|'), f.cdyn_term))
  UNION ALL
  -- Structural: the gated set and the rejected set must partition the matches, so a row
  -- can never be silently dropped between scoring and emission.
  SELECT 'scored_partition_broken', NULL::BIGINT, 'gated + rejected != scored'
  WHERE (SELECT count(*) FROM _scored)
     <> (SELECT count(*) FROM _scored WHERE reject_reason IS NULL) + (SELECT count(*) FROM scoring_rejected)
  UNION ALL
  -- Structural: one row per (model, feature) — gen.py groups by model, and a duplicated
  -- pair would emit the same member twice.
  SELECT 'row_duplicated', r.id, r.slug || ' / ' || r.feature_slug FROM scoring_patch_rows r
  GROUP BY r.id, r.slug, r.feature_slug HAVING count(*) > 1
  UNION ALL
  -- Correctness: never emit an attachment the catalog already holds.
  SELECT 'row_already_attached', r.id, r.slug || ' / ' || r.feature_slug
  FROM scoring_patch_rows r
  WHERE EXISTS (SELECT 1 FROM model_gameplay_features mgf
                WHERE mgf.model_id = r.id AND mgf.feature_slug = r.feature_slug)
  UNION ALL
  -- Correctness: a target is either a bingo-format model or one the catalog has not
  -- classified. A model carrying a DIFFERENT format is the catalog saying this is not a
  -- bingo, and no match strength overrides that.
  SELECT 'row_targets_other_format', r.id, r.label || ' is ' || m.game_format_slug
  FROM scoring_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.game_format_slug IS NOT NULL AND m.game_format_slug <> 'bingo-pinball'
  UNION ALL
  -- Structural: every row must carry the quote its cite ships with.
  SELECT 'row_without_quote', r.id, r.label
  FROM scoring_patch_rows r WHERE r.quote IS NULL OR r.quote = ''
  UNION ALL
  -- Anchors: both KEYS still resolve a source page onto the right catalog model. These
  -- probe `_match_probe` rather than the emitted set, which legitimately drains to zero
  -- once the patch is applied.
  SELECT 'anchor_number_key_dark', NULL::BIGINT,
         'cdyn #615 no longer resolves to Bally Carnival Queen by manufacturer_model_identifier'
  WHERE NOT EXISTS (
    SELECT 1 FROM _match_probe WHERE matched_on = 'number' AND cdyn_number = '615'
      AND name_agrees AND slug = 'carnival-queen')
  UNION ALL
  SELECT 'anchor_name_key_dark', NULL::BIGINT,
         'cdyn no longer resolves a Sirmo machine by name (the European-maker key)'
  WHERE NOT EXISTS (
    SELECT 1 FROM _match_probe WHERE matched_on = 'name' AND manufacturer_name = 'SIRMO Games S.A.')
  UNION ALL
  -- Anchor: the signal itself. Carnival Queen is the machine that introduced section
  -- scoring and carries both methods; if its page stops reading as both, the Features
  -- parser or the page layout has moved.
  SELECT 'anchor_signal_dark', NULL::BIGINT,
         'Carnival Queen no longer reads as carrying BOTH scoring methods'
  WHERE (SELECT count(*) FROM _claims c
         WHERE c.slug = 'carnival-queen'
           AND c.feature_slug IN ('in-line-scoring', 'section-scoring')) <> 2
  UNION ALL
  -- Evidence: the family page must be cached, since every `needs_family_cite` row cites
  -- it and would fail `make verify-quote-verbatim` if it were absent.
  SELECT 'features_page_not_cached', NULL::BIGINT,
         'https://bingo.cdyn.com/machines/features.html is not in pinexplore''s web cache'
  WHERE (SELECT count(*) FROM scoring_patch_rows WHERE needs_family_cite) > 0
    AND NOT EXISTS (SELECT 1 FROM _features_page)
  UNION ALL
  -- Evidence: every emitted quote must be verbatim in ITS OWN cited page, under the
  -- normalization `make verify-quote-verbatim` applies. Pulled forward to where the rows
  -- are built, because a quote a reviewer cannot ctrl-F is worse than no quote.
  SELECT 'quote_not_verbatim_in_source', r.id, r.url
  FROM scoring_patch_rows r
  WHERE NOT EXISTS (
    SELECT 1 FROM evidence_pages p
    WHERE p.url = r.url AND contains(p.text_norm, evidence_norm(r.quote)))
  UNION ALL
  -- Drift: cdyn_features.tsv is frozen at extraction time and nothing else notices when
  -- a page moves underneath it. A row whose cited page is no longer cached, or whose
  -- Features cell no longer matches the TSV, means the extract is stale — rerun
  -- extract_cdyn_features.py and diff it, which is what the artifact is for.
  SELECT 'tsv_page_not_cached', NULL::BIGINT, c.url
  FROM cdyn c
  WHERE NOT EXISTS (SELECT 1 FROM evidence_pages p WHERE p.url = c.url);
