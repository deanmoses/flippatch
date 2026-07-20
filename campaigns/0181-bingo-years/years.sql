-- Year fill for bingo machines, from bingo.cdyn.com's machine listing.
--
-- Goal: give the year-less bingo corpus a real `year`. The catalog carries ~224
-- bingo models with no year at all, and the gap is not cosmetic — a missing year
-- disables the single strongest signal for telling two same-named games apart. It
-- was a NULL year that let ../0177-exports/exports.sql tier Splin S.A.'s modern
-- six-card 'Acapulco' as a foreign build of Bally's 1961 'Acapulco'.
--
-- What this patch does and does NOT fix, on that worked example: cdyn does not list a
-- Splin 'Acapulco' at all, so that model stays year-less and the pair is NOT resolved
-- by a direct year comparison. What the patch does supply is the MAKER'S ERA — six
-- Splin models dated 1999-2003 — which places the maker 38 years after Bally's 1961
-- game. Dating a maker's other models is therefore worth as much here as dating the
-- model itself, and the follow-up in exports.sql is a maker-era fallback for
-- comparisons where one side has no year of its own.
--
-- SOURCE. bingo.cdyn.com's alpha-by-manufacturer listing, read from pinexplore's web
-- scrape cache (see extract_cdyn.py in this dir, which writes cdyn_machines.tsv).
-- It is the only source found that dates the late European bingo makers. Its Game
-- Number column, by contrast, is the literal string "unknown" for every maker except
-- Bally, so this campaign takes YEARS from it and nothing else.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode is FLIPCOMMONS' shared foundation,
-- reused VERBATIM via the `.read` below. Same pattern as ../0177-exports/exports.sql.
--
-- HOW TO RUN. cwd must be the flipcommons checkout; `make analyze` handles that:
--
--     P=campaigns/0181-bingo-years/years.sql
--     make analyze FILE=$F PREFIX=year                        # summary, gated on checks
--     make analyze FILE=$F Q="FROM year_patch_rows;"          # what gen.py emits
--     make analyze FILE=$F Q="FROM year_rejected;"            # what the gate held back
--     make analyze FILE=$F Q="FROM model_number_collisions;"  # foundation: maker+number clashes
--
-- STRUCTURE — the four sections every analysis file has (flipcommons'
-- scripts/analysis/README.md): 1 FOUNDATION, 2 REFERENCE, 3 ANALYSIS, 4 SUMMARY & CHECKS.

-- ── 1 · FOUNDATION ─────────────────────────────────────────────────────────
.read scripts/analysis/catalog.sql
-- flippatch's evidence bridge — pinexplore's web scrape cache as `ev`, so the source
-- text this campaign rests on is queryable next to the catalog rows it emits. That is
-- what lets the checks below verify each cite quote against the live cached page, and
-- notice when cdyn_machines.tsv has drifted from it. Both paths resolve from the
-- flipcommons root; see the header of evidence.sql.
.read ../flippatch/scripts/analysis/evidence.sql

-- ── 2 · REFERENCE ──────────────────────────────────────────────────────────

-- The source rows. Located via FLIPPATCH_DIR so this resolves wherever the two repos
-- sit; the fallback is the sibling layout the repo topology already assumes (the
-- foundation `.read` above relies on the same convention from the other direction).
CREATE OR REPLACE TABLE cdyn AS
  SELECT * FROM read_csv(
    COALESCE(NULLIF(getenv('FLIPPATCH_DIR'), ''), '../flippatch')
      || '/campaigns/0181-bingo-years/cdyn_machines.tsv',
    delim = '\t', header = true,
    columns = {'maker':'VARCHAR','game':'VARCHAR','number':'VARCHAR','type':'VARCHAR','year':'VARCHAR'});

-- cdyn's maker heading -> the catalog's manufacturer name. Hand-maintained: the two
-- vocabularies are independent and neither is derivable from the other ("SPLIN
-- (formerly show games)" vs "Splin S.A."). A maker absent here simply contributes no
-- rows, which is the safe default — an unmapped maker cannot produce a wrong year,
-- only a missing one. `year_checks` reports makers left unmapped so the omission is
-- visible rather than silent.
CREATE OR REPLACE VIEW _maker_map AS
  SELECT * FROM (VALUES
    ('Bally',                        'Bally'),
    ('Sirmo',                        'SIRMO Games S.A.'),
    ('SPLIN (formerly show games)',  'Splin S.A.'),
    ('Wimi',                         'WIMI Games'),
    ('Show Games',                   'SG'),
    ('General Automated Amusements', 'G.A.A.'),
    ('United',                       'United'),
    ('Keeney',                       'Keeney'),
    ('Playmatic',                    'Playmatic'),
    ('Williams',                     'Williams'),
    ('Interflip',                    'Interflip')
  ) AS t(cdyn_maker, catalog_maker);

-- ── 3 · ANALYSIS ───────────────────────────────────────────────────────────
-- Shape: normalize -> match (two keys, one per maker class) -> gate -> emit.

-- Number keys, EXACT and LOOSE — and the distinction is load-bearing.
--
-- This stays ANALYSIS-LOCAL by design. The foundation's `model_number_collisions` makes
-- the point: a maker's suffix convention is a fact about THAT MAKER, not about the
-- column, so a shared stem macro would answer confidently for makers it was never
-- calibrated on. The rule below is calibrated on Bally and holds for Bally.
--
-- Bally's trailing letter is NOT a variant marker: #634 is 'Fun Way' and #634-A is
-- 'Lotta Fun', #652 is 'Fun Spot' and #652-A is "Barrel-O'-Fun" — different games
-- sharing a number stem. So the letter must not be normalized away when both sides
-- carry it. But the catalog's number is sometimes the stem where cdyn has the letter
-- (catalog records "Barrel O' Fun '61" as #670 while cdyn numbers it 670-A), so an
-- exact-only key would miss those.
--
-- The resolution: match on the EXACT number first, and fall back to the loose stem
-- only for a model no exact match resolved. The name-agreement gate below is what
-- makes the fallback safe — a loose match that lands on the wrong game
-- ("Barrel O' Fun '61" #670 -> cdyn's #670 'Fun Spot '61') disagrees on the name and
-- goes to review rather than emitting.
CREATE OR REPLACE MACRO _num_exact(s) AS NULLIF(upper(trim(COALESCE(s, ''))), '');
CREATE OR REPLACE MACRO _num_loose(s) AS
  NULLIF(upper(regexp_replace(COALESCE(s, ''), '-[A-Za-z]$', '')), '');

-- The models in scope: year-less, and belonging to a maker cdyn covers. Restricted to
-- year-less models on purpose — this campaign FILLS a gap, it does not adjudicate a
-- year the catalog already asserts. A cdyn/catalog year disagreement on a dated model
-- is a real question, but it is a different (and much more careful) patch.
CREATE OR REPLACE TABLE _target_models AS
  SELECT
    m.id, m.slug, m.name, m.label, m.manufacturer_name, m.game_format_slug,
    m.manufacturer_model_identifier AS model_number,
    name_key(m.name) AS nkey,
    _num_exact(m.manufacturer_model_identifier) AS numkey_exact,
    _num_loose(m.manufacturer_model_identifier) AS numkey_loose
  FROM models m
  WHERE m.year IS NULL
    AND m.manufacturer_name IN (SELECT catalog_maker FROM _maker_map);

-- The source rows, keyed, with the catalog maker resolved.
CREATE OR REPLACE TABLE _cdyn_keyed AS
  SELECT
    mm.catalog_maker AS maker, c.game, c.number, c.type, c.year,
    name_key(c.game) AS nkey,
    -- "unknown" is cdyn's literal null for this column; treat it as absent rather
    -- than letting it become a join key that matches every other unknown.
    CASE WHEN lower(c.number) = 'unknown' THEN NULL ELSE _num_exact(c.number) END AS numkey_exact,
    CASE WHEN lower(c.number) = 'unknown' THEN NULL ELSE _num_loose(c.number) END AS numkey_loose
  FROM cdyn c
  JOIN _maker_map mm ON mm.cdyn_maker = c.maker;

-- MATCH, on the strongest key each maker class offers.
--
-- by NUMBER (Bally, and the one Williams row) — the manufacturer's own game number,
-- already in the catalog from IPDB. This is the key that survives contact with the
-- data: matching Bally on NAME alone put the catalog's #535 'Broadway' onto cdyn's
-- #576 'Broadway' (cdyn lists both a 1951 #535 and a 1955 #576) and collapsed two
-- distinct 'Tahiti' records onto one row. The number is unambiguous where it exists.
--
-- by NAME (every European maker) — no number exists in any source for these, so the
-- name within a maker is all there is. That is acceptable only because each of these
-- makers has a small catalog and cdyn lists it in full, so the uniqueness requirement
-- below is a real constraint rather than a formality.
CREATE OR REPLACE TABLE _matched AS
  WITH by_number_exact AS (
    SELECT t.id, c.year, c.game AS cdyn_game, c.number AS cdyn_number, c.type AS cdyn_type,
           'number' AS matched_on, (t.nkey = c.nkey) AS name_agrees
    FROM _target_models t
    JOIN _cdyn_keyed c ON c.numkey_exact = t.numkey_exact AND c.maker = t.manufacturer_name
    WHERE t.numkey_exact IS NOT NULL
  ),
  -- The stem fallback, only for a model the exact key left unresolved.
  by_number_loose AS (
    SELECT t.id, c.year, c.game AS cdyn_game, c.number AS cdyn_number, c.type AS cdyn_type,
           'number-stem' AS matched_on, (t.nkey = c.nkey) AS name_agrees
    FROM _target_models t
    JOIN _cdyn_keyed c ON c.numkey_loose = t.numkey_loose AND c.maker = t.manufacturer_name
    WHERE t.numkey_loose IS NOT NULL
      AND t.id NOT IN (SELECT id FROM by_number_exact)
  ),
  by_name AS (
    SELECT t.id, c.year, c.game AS cdyn_game, c.number AS cdyn_number, c.type AS cdyn_type,
           'name' AS matched_on, TRUE AS name_agrees
    FROM _target_models t
    JOIN _cdyn_keyed c ON c.nkey = t.nkey AND c.maker = t.manufacturer_name
    -- Numbered makers are resolved above; falling back to the name for a model whose
    -- number failed to match would reintroduce exactly the Broadway and Tahiti
    -- mismatches the number key exists to prevent.
    WHERE t.numkey_exact IS NULL
  ),
  unioned AS (
    SELECT * FROM by_number_exact
    UNION ALL SELECT * FROM by_number_loose
    UNION ALL SELECT * FROM by_name
  )
  -- Ambiguity counted AFTER tier selection, so a model resolved exactly is not
  -- re-flagged by the looser key it never used.
  SELECT u.*,
         count(*) OVER (PARTITION BY u.id) AS n_source,
         count(*) OVER (PARTITION BY u.cdyn_game, u.cdyn_number) AS n_model
  FROM unioned u;

-- The same match, run over EVERY model of a mapped maker rather than only the
-- year-less ones. Nothing is emitted from this — it exists so the anchor checks can
-- test whether the two KEYS still resolve, independently of whether any model still
-- needs a year. The emitted set drains to zero once the patch is applied, which is
-- success, not breakage; only a probe that ignores the backlog can tell them apart.
CREATE OR REPLACE TABLE _match_probe AS
  SELECT m.slug, m.name, m.manufacturer_name, c.game AS cdyn_game, c.number AS cdyn_number,
         c.year AS cdyn_year,
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

-- GATE. A year is emitted only when the match is unambiguous in BOTH directions and
-- the value is a clean four-digit year. Everything else lands in `year_rejected` with
-- a reason, because a wrong year is worse than a missing one — it silently re-tiers
-- every same-name comparison that depends on it.
CREATE OR REPLACE TABLE _scored AS
  SELECT
    t.id, t.slug, t.label, t.name, t.manufacturer_name, t.model_number,
    m.year AS cdyn_year, m.cdyn_game, m.cdyn_number, m.cdyn_type, m.matched_on,
    m.name_agrees, m.n_source, m.n_model,
    TRY_CAST(m.year AS INTEGER) AS year_value,
    CASE
      -- one model matching several source rows: which year is unknowable
      WHEN m.n_source > 1                             THEN 'model matches several source rows'
      -- several models matching one source row: the two Tahitis on one cdyn line
      WHEN m.n_model > 1                              THEN 'source row matches several models'
      WHEN TRY_CAST(m.year AS INTEGER) IS NULL        THEN 'year not a number'
      WHEN TRY_CAST(m.year AS INTEGER) NOT BETWEEN 1900 AND 2100 THEN 'year out of range'
      -- Number matched but the names differ. Most are benign spelling variants
      -- ("The Twist"/"Twist", "Broadway"/"Broadway_51"), but #1017 is 'Golden Gate 75'
      -- here and 'Mystic Gate' there — a real question. The gate does not try to tell
      -- those apart; all of them go to review, since the number key is only worth
      -- trusting where the name corroborates it.
      WHEN NOT m.name_agrees                          THEN 'number matched, name differs'
    END AS reject_reason
  FROM _target_models t
  JOIN _matched m ON m.id = t.id;

-- emit ── the rows gen.py writes, one per model.
-- `quote` is the source's own table row, verbatim from the cached page: the game, its
-- number, its bingo type and the year, which is exactly the evidence the claim rests
-- on. `make verify-quotes` collapses whitespace on both sides, so the pipe-delimited
-- row verifies as a substring of the cached page text.
CREATE OR REPLACE TABLE year_patch_rows AS
  SELECT
    s.id, s.slug, s.label, s.manufacturer_name,
    s.year_value AS year,
    s.cdyn_type  AS bingo_type,
    s.matched_on,
    '| ' || s.cdyn_game || ' | ' || s.cdyn_number || ' | ' || s.cdyn_type
         || ' | ' || s.cdyn_year || ' |' AS quote
  FROM _scored s
  WHERE s.reject_reason IS NULL
  ORDER BY s.slug;

CREATE OR REPLACE VIEW year_rejected AS
  SELECT reject_reason, id, slug, label, model_number, cdyn_game, cdyn_number,
         cdyn_year, matched_on, n_source, n_model
  FROM _scored WHERE reject_reason IS NOT NULL
  ORDER BY reject_reason, label;

-- Two live models sharing one maker+number: use the foundation's
-- `model_number_collisions` directly. This plan kept its own copy until the
-- foundation absorbed it; the foundation's version is exact-number-only (no stem
-- match) and carries `n_titles`, which is the discriminator between a legitimate
-- within-Title split and a duplicate worth a look.

-- THE LIVE SOURCE PAGE, from the evidence bridge. `cdyn` above is the checked-in TSV
-- — an audit artifact frozen at extraction time; this is the page as currently cached.
-- Holding both lets the checks below answer the question a frozen artifact cannot:
-- does the evidence still say what the TSV says it said?
CREATE OR REPLACE VIEW _cdyn_page AS
  SELECT * FROM evidence_pages
  WHERE url = 'https://bingo.cdyn.com/machines/index.html';

-- The page's machine rows, parsed in SQL — the same shape extract_cdyn.py's parser
-- takes (a four-cell pipe row that is not the repeated header). Deliberately a COUNT
-- probe rather than a second extractor: parsing stays in extract_cdyn.py, and this
-- only needs enough structure to notice the page changed underneath the TSV.
CREATE OR REPLACE VIEW _cdyn_page_rows AS
  SELECT trim(line) AS line
  FROM (SELECT unnest(string_split(text, chr(10))) AS line FROM _cdyn_page)
  WHERE starts_with(trim(line), '|')
    -- New-style lambda deliberately: the deprecated `->` spelling emits a DuckDB
    -- warning on stderr, which the analysis runner's view discovery parses as output.
    AND len(list_filter(string_split(trim(trim(line), '|'), '|'), lambda x: trim(x) <> '')) = 4
    AND NOT starts_with(trim(line), '| Game Name');

-- ── 4 · SUMMARY & CHECKS ───────────────────────────────────────────────────

CREATE OR REPLACE VIEW year_summary AS
  SELECT 'yearless_in_scope' AS metric, count(*) AS value FROM _target_models
  UNION ALL SELECT 'yearless_bingo_total',
    (SELECT count(*) FROM models WHERE year IS NULL AND game_format_slug = 'bingo-pinball')
  UNION ALL SELECT 'matched',        (SELECT count(DISTINCT id) FROM _matched)
  UNION ALL SELECT 'matched_number', (SELECT count(DISTINCT id) FROM _matched WHERE matched_on = 'number')
  UNION ALL SELECT 'matched_name',   (SELECT count(DISTINCT id) FROM _matched WHERE matched_on = 'name')
  UNION ALL SELECT 'patch_rows',     (SELECT count(*) FROM year_patch_rows)
  UNION ALL SELECT 'patch_rows_number', (SELECT count(*) FROM year_patch_rows WHERE matched_on = 'number')
  UNION ALL SELECT 'patch_rows_name',   (SELECT count(*) FROM year_patch_rows WHERE matched_on = 'name')
  UNION ALL SELECT 'rejected',       (SELECT count(*) FROM year_rejected)
  UNION ALL SELECT 'source_rows',    (SELECT count(*) FROM cdyn)
  UNION ALL SELECT 'source_makers_unmapped',
    (SELECT count(DISTINCT maker) FROM cdyn WHERE maker NOT IN (SELECT cdyn_maker FROM _maker_map))
  UNION ALL SELECT 'number_collisions', (SELECT count(*) FROM model_number_collisions)
  UNION ALL SELECT 'source_page_rows_live', (SELECT count(*) FROM _cdyn_page_rows)
  ORDER BY metric;

-- Empty when healthy.
CREATE OR REPLACE VIEW year_checks AS
  -- Vocabulary: every mapped catalog maker must actually exist, or the map has a typo
  -- and silently contributes nothing.
  SELECT 'maker_map_unknown_catalog_maker' AS check, NULL::BIGINT AS id, mm.catalog_maker AS detail
  FROM _maker_map mm
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.manufacturer_name = mm.catalog_maker)
  UNION ALL
  SELECT 'maker_map_unknown_cdyn_maker', NULL::BIGINT, mm.cdyn_maker
  FROM _maker_map mm
  WHERE NOT EXISTS (SELECT 1 FROM cdyn c WHERE c.maker = mm.cdyn_maker)
  UNION ALL
  -- Structural: the emitted set and the rejected set must partition the matches, so a
  -- row can never be silently dropped between scoring and emission.
  SELECT 'scored_partition_broken', NULL::BIGINT, 'emitted + rejected != scored'
  WHERE (SELECT count(*) FROM _scored)
     <> (SELECT count(*) FROM year_patch_rows) + (SELECT count(*) FROM year_rejected)
  UNION ALL
  -- Correctness: this campaign only FILLS a null year. A row targeting a model that
  -- already has one would overwrite an existing catalog claim.
  SELECT 'row_targets_dated_model', r.id, r.label
  FROM year_patch_rows r JOIN models m ON m.id = r.id
  WHERE m.year IS NOT NULL
  UNION ALL
  -- Vocabulary: an emitted year must be a plausible four-digit year.
  SELECT 'year_out_of_range', r.id, r.year::VARCHAR
  FROM year_patch_rows r WHERE r.year NOT BETWEEN 1900 AND 2100
  UNION ALL
  -- Structural: one row per model, since gen.py writes one entry per row and a
  -- duplicated ref collides at apply.
  SELECT 'row_duplicated', r.id, r.slug FROM year_patch_rows r
  GROUP BY r.id, r.slug HAVING count(*) > 1
  UNION ALL
  -- Structural: every row must carry the quote its cite ships with.
  SELECT 'row_without_quote', r.id, r.label
  FROM year_patch_rows r WHERE r.quote IS NULL OR r.quote = ''
  UNION ALL
  -- Anchors: both KEYS still resolve a source row onto the right catalog model.
  --
  -- These deliberately probe `_match_probe` (every model of a mapped maker) rather
  -- than `year_patch_rows`. The emitted set legitimately drains to zero the moment
  -- the patch is applied — every model it targeted now HAS a year and drops out of
  -- scope — so anchoring on it cannot tell "the campaign finished" from "the join
  -- broke", and fired on a healthy run the first time this patch was ingested.
  -- The probe tests the machinery, which stays true regardless of the backlog.
  SELECT 'anchor_number_key_dark', NULL::BIGINT,
         'cdyn #669 no longer resolves to Bally Acapulco by manufacturer_model_identifier'
  WHERE NOT EXISTS (
    SELECT 1 FROM _match_probe WHERE matched_on = 'number' AND cdyn_number = '669'
      AND name_agrees AND slug = 'acapulco')
  UNION ALL
  SELECT 'anchor_name_key_dark', NULL::BIGINT,
         'cdyn no longer resolves Splin Montana V by name (the European-maker key)'
  WHERE NOT EXISTS (
    SELECT 1 FROM _match_probe WHERE matched_on = 'name' AND slug = 'montana-v')
  UNION ALL
  -- Guard: the two mismatches that motivated the number key must stay OUT. Both were
  -- observed emitting a wrong year while this gate was built: name-matching put
  -- catalog #535 'Broadway' on cdyn's 1955 #576 row, and collapsed both 'Tahiti'
  -- records onto one 1979 line.
  SELECT 'anchor_guard_regressed', r.id, r.slug || ' is emitting a year again'
  FROM year_patch_rows r
  WHERE r.slug IN ('broadway-2', 'tahiti-4', 'tahiti-7')
  UNION ALL
  SELECT 'anchor_guard_slug_stale', NULL::BIGINT, g.slug || ' is no longer a model slug'
  FROM (VALUES ('broadway-2'), ('tahiti-4'), ('tahiti-7'), ('acapulco-2')) AS g(slug)
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = g.slug)
  UNION ALL
  -- Evidence: the cited page must actually be in the cache. Every quote this campaign
  -- emits cites this one URL, so if it is absent `make verify-quotes` fails on all of
  -- them — better to learn that here, before generating a patch, than after.
  SELECT 'source_page_not_cached', NULL::BIGINT,
         'https://bingo.cdyn.com/machines/index.html is not in pinexplore''s web cache'
  WHERE NOT EXISTS (SELECT 1 FROM _cdyn_page)
  UNION ALL
  -- Evidence: every emitted quote must be verbatim in the cached page. This is the
  -- gate `make verify-quotes` applies, pulled forward to the point where the rows are
  -- built — the normalization is `evidence_norm`, the SQL twin of that tool's own. A
  -- row failing here would ship a quote a reviewer could not ctrl-F.
  SELECT 'quote_not_verbatim_in_source', r.id, r.quote
  FROM year_patch_rows r
  WHERE EXISTS (SELECT 1 FROM _cdyn_page)
    AND NOT EXISTS (
      SELECT 1 FROM _cdyn_page p
      WHERE contains(p.text_norm, evidence_norm(r.quote)))
  UNION ALL
  -- Drift: cdyn_machines.tsv is frozen at extraction time, and nothing else notices
  -- when the page moves underneath it. A count mismatch means the page changed and the
  -- TSV is stale — rerun extract_cdyn.py and diff it, which is what the artifact is
  -- for. A count is a weak equality test on purpose: it catches added/removed machines
  -- without re-implementing the parser here.
  SELECT 'tsv_stale_vs_cached_page', NULL::BIGINT,
         'TSV has ' || (SELECT count(*) FROM cdyn) || ' rows, cached page now parses '
           || (SELECT count(*) FROM _cdyn_page_rows) || ' — rerun extract_cdyn.py'
  WHERE EXISTS (SELECT 1 FROM _cdyn_page)
    AND (SELECT count(*) FROM cdyn) IS DISTINCT FROM (SELECT count(*) FROM _cdyn_page_rows);
