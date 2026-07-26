-- Export-candidate analysis for the 0177-exports campaign.
--
-- Goal: find every catalog model built for a foreign market, and decompose the
-- candidates into review buckets that are first-cut worklists for the data patches
-- setting `export_edition_of` and `ModelExportMarket`. This is the DISCOVERY layer;
-- per-row judgement and patch authoring are downstream (see this dir's README.md).
-- Flippatch owns this analysis — flipcommons' Exports.md, which specifies the two
-- catalog structures, links here rather than carrying a copy.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (models/countries/rewards/title_size
-- and the read-only connection) is FLIPCOMMONS' shared foundation, reused VERBATIM
-- via the `.read` below — flippatch keeps no copy. Same pattern as
-- ../0128-relationships/relationships.sql and ../0172-bingo-game-format/bingo.sql.
--
-- HOW TO RUN. cwd must be the flipcommons checkout so BOTH the `.read` below AND the
-- foundation's own `ATTACH backend/db.sqlite3` resolve there. `make analyze` handles
-- the cwd/path resolution and delegates to flipcommons' shared runner, which prints
-- the analysis_context watermark + export_summary and gates on export_checks. Do not
-- run this file directly:
--
--     P=campaigns/0177-exports/exports.sql
--     make analyze FILE=$F PREFIX=export                              # summary, gated on checks
--     make analyze FILE=$F Q="FROM export_twin_pairs;"                # deterministic export_edition_of
--     make analyze FILE=$F Q="FROM export_titlemate_review;"          # likely target sits in the same Title
--     make analyze FILE=$F Q="FROM export_orphan_review;"             # candidates still needing a target
--     make analyze FILE=$F Q="FROM export_namesake_review;"           # same name, separate Title
--     make analyze FILE=$F Q="FROM export_market_review;"             # the ModelExportMarket shape per candidate
--     make analyze FILE=$F CMD=ui                                     # live GUI at localhost:4213
--
-- Nothing is persisted; there is no build artifact. Counts are a snapshot of
-- current DB state — re-run as candidates get reviewed. `export_summary` emits
-- the headline numbers the README quotes; `export_checks` is empty when healthy.
--
-- The notes detectors are freetext heuristics: they over- and under-count and
-- every row needs source review before it becomes a claim (see README.md).
--
-- STRUCTURE — a analysis file has four sections (see flipcommons' scripts/analysis/README.md).
-- Three are the same in every analysis; only section 3 is shaped by the question:
--   1 · FOUNDATION       .read the shared decode layer
--   2 · REFERENCE        analysis-local hand-maintained lookups (often empty)
--   3 · ANALYSIS         the actual work — this file's shape is detect ->
--                        assemble -> enrich -> review; yours may differ
--   4 · SUMMARY & CHECKS the tail that keeps the prose honest — always keep it

-- ── 1 · FOUNDATION ─────────────────────────────────────────────────────────
.read scripts/analysis/catalog.sql

-- ── 2 · REFERENCE ──────────────────────────────────────────────────────────
-- Hand-maintained lookups specific to this analysis. Not derived from the DB.

-- Country ADJECTIVES — 'a German version', 'for the Italian market'. The one token kind
-- the catalog does not and should not carry: `country_aliases` holds alternate NAMES
-- for a country ("West Germany", "Holland", "England"), while an adjective is a parsing
-- strategy this analysis applies to prose. That is the same judgment/mechanic split the
-- foundation's own name macros are built on, so the two halves stay on their own sides.
--
-- This list USED to carry the alternate names too — 'USA', 'United States', 'UK',
-- 'Holland' — hand-copied, and wrong by omission: the catalog knows 11 country aliases
-- and this file knew 4. The seven it missed included 'England', which is why
-- 'Adventures of Rocky and Bullwinkle' ("the black cabinet games exported to England")
-- resolved no market at all. `country_aliases` now supplies that half.
--
-- Country NAMES are never hardcoded here — `countries` supplies them, so a country
-- rename can't silently desync the lookup.
CREATE OR REPLACE VIEW _country_adjective AS
  SELECT * FROM (VALUES
    ('Italian','Italy'), ('Spanish','Spain'), ('French','France'), ('German','Germany'),
    ('Portuguese','Portugal'), ('Japanese','Japan'), ('Brazilian','Brazil'),
    ('Belgian','Belgium'), ('British','United Kingdom'), ('American','United States of America')
  ) AS t(token, country_name);

-- token -> country slug, from three sources: the catalog's country names, the catalog's
-- registered aliases, and this analysis's adjectives. Checked to be collision-free —
-- `country_lookup_ambiguous` below fails the run if a token ever resolves two ways,
-- since every consumer joins on `token` and a duplicate would multiply rows silently.
CREATE OR REPLACE VIEW _country_lookup AS
  SELECT name AS token, slug FROM countries
  UNION ALL
  SELECT alias AS token, country_slug AS slug FROM country_aliases
  UNION ALL
  SELECT a.token, c.slug FROM _country_adjective a JOIN countries c ON c.name = a.country_name;

-- Region labels for the `target_market_label` case (flipcommons' Exports.md): a market
-- that is a multi-country region, not a catalog country. Unlike countries these have NO catalog
-- vocabulary to draw on (a region isn't a Location), so the canonical label is
-- hand-declared here — this IS the closed set `market_kind = 'region'` validates
-- against. `pattern` is a case-insensitive regex requiring EXPORT context around the
-- region word, because the bare word is mostly noise ("European football" theme, "a
-- European distributor", a collector "in Europe"). Keep patterns tight; a false region
-- hit invents a market. Only Europe recurs in the data today; the row shape is ready
-- for Scandinavia/Benelux/Latin America if they ever surface.
CREATE OR REPLACE VIEW _region_alias AS
  SELECT * FROM (VALUES
    ('Europe',   '(?i)(for (the )?european market|made for europe|export(ed)? to europe|shipped to europe)'),
    ('Far East', '(?i)(export(ed)? to (the )?far east|for the far east(ern)? market|made for the far east)')
  ) AS t(label, pattern);

-- ── 3 · ANALYSIS ───────────────────────────────────────────────────────────
-- This analysis hunts candidate export models, so its shape is:
--   detect   surface candidates from several independent signals (the _by_*,
--            _dest_* helpers below)
--   assemble union the signals into one row per candidate (export_candidates)
--   enrich   join in existing lineage edges (export_candidate_lineage)
--   review   slice the candidates into the human-review buckets (export_*_review,
--            export_name_family)
-- A different question wants a different shape — classify, aggregate, diff, etc.
-- Keep sections 1, 2 and 4; rebuild this one for your plan.

-- detect ──
-- Detector 1 (membership): any model whose notes carry export-edition phrasing.
-- Scope is *any model built for export*, so this is NOT gated on a named market
-- (the market is parsed separately below and may be empty). The one exclusion is
-- the "quantity produced for export: N" production statistic — a sales figure
-- nearly every Williams/Gottlieb game carries — which is blanked before matching
-- so it can't create a candidate on its own, yet a note that ALSO carries real
-- export phrasing (e.g. Yukon (Special)) is still kept.
-- NOTE: "for the <X> market" phrasing was REMOVED from membership — it was mostly
-- noise. The unbounded `%for the % market%` bridged unrelated text (4-IN-1's "sell ...
-- to the home market" became a hit), and even bounded it caught domestic markets. Of
-- the 42 candidates it uniquely supplied, only ~5 were genuine foreign-market exports.
-- Those hits are now PARKED in `export_market_phrase_review` for a separate, careful
-- pass, rather than polluting the candidate set. (`_market_tokens` below still parses
-- the phrase into a country for models that ARE candidates by other signals — fine.)
CREATE OR REPLACE VIEW _by_notes AS
  SELECT id FROM (
    SELECT id, regexp_replace(COALESCE(ipdb_notes, ''), '(?i)quantity produced for export', '', 'g') AS n
    FROM models
  )
  WHERE n ILIKE '%for export%'
     OR n ILIKE '%export to %'
     OR n ILIKE '%export edition%' OR n ILIKE '%export version%' OR n ILIKE '%export model%';

-- The _dest_* views below parse the destination MARKET from the notes/name. They
-- feed the `markets` column, not candidate membership — a by_notes candidate with
-- no parseable country simply has empty markets.

-- "export to <Country>[ and/then <Country>...]" — resolve each parsed token to a
-- country slug. Two shapes the naive single-token regex missed:
--   list      "export to Israel and Indonesia", "export to Brazil then Italy" — capture
--             the whole run (tokens chained by " and "/" then ") and split it, so the
--             tail country isn't dropped.
--   acronym   "export to the USA", "export to the UK" — the token charset allows
--             all-caps runs (USA/UK), resolved via `_country_lookup`.
-- The country charset deliberately over-captures (any capitalized run); a token that
-- isn't a country simply drops at the `_country_lookup` join. A leading "the " on a
-- list tail (". . . and the UK") is stripped before lookup.
-- A MACRO, not a view, because the emit layer re-runs this same parse on a NARROWER
-- span. Membership parses the whole note; the patch rows must parse the ONE cited
-- sentence, so that the quote a market claim ships with actually supports it. Two
-- copies of these regexes would drift, so there is exactly one definition and both
-- callers pass their own text.
-- Returns RAW tokens (a leading "the " stripped); a token that isn't a country simply
-- drops at the `_country_lookup` join, which is what lets the charsets over-capture.
CREATE OR REPLACE MACRO _market_tokens(txt) AS (
  list_transform(
    list_concat(
      -- Detector 1a: "export to <Country>[ and/then <Country>...]" — capture the whole
      -- run, then split it, so the tail country of a list isn't dropped.
      flatten(list_transform(
        regexp_extract_all(COALESCE(txt, ''),
          'export to (?:the )?([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*(?: (?:and|then) (?:the )?[A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*)*)',
          1),
        lambda run: string_split_regex(run, ' (?:and|then) ')
      )),
      list_concat(
        -- Detector 1b: "for the <Adjective|Country> market" (single-word token).
        regexp_extract_all(COALESCE(txt, ''), 'for the ([A-Z][a-z]+) market', 1),
        -- Detector 2b: a nationality ADJECTIVE sitting directly on "export" —
        -- "Italian export version". Requiring a CAPITALIZED token is what keeps this
        -- precise: it excludes the same-shaped non-markets ("add-a-ball export
        -- version", "4-player export version").
        regexp_extract_all(COALESCE(txt, ''), '([A-Z][a-z]+) export', 1)
      )
    ),
    lambda t: trim(regexp_replace(t, '^the ', ''))
  )
);

-- Detectors 1a/1b/2b over the FULL note — the membership-side caller of the macro.
-- Caveat on the adjective form: it could in principle name the maker's ORIGIN rather
-- than the destination ("Spanish export version" by a Spanish maker).
-- `market_is_maker_home` flags exactly that case for review; no model hits it today.
CREATE OR REPLACE VIEW _dest_freetext AS
  SELECT m.id, cl.slug AS dest
  FROM models m, UNNEST(_market_tokens(m.ipdb_notes)) AS d(token)
  JOIN _country_lookup cl ON cl.token = d.token;

-- Detector 2: trailing "(Country)" name suffix -> that country's slug.
CREATE OR REPLACE VIEW _dest_suffix AS
  SELECT m.id, c.slug AS dest
  FROM models m JOIN countries c ON m.name LIKE '%(' || c.name || ')';

-- Detector 3: OPDB feature flag containing "export" (today only "Export edition",
-- but the substring is insurance against other spellings). No market on its own.
CREATE OR REPLACE VIEW _by_opdb AS
  SELECT id FROM models
  WHERE len(list_filter(opdb_features, lambda f: lower(f) LIKE '%export%')) > 0;

-- Detector 4 (membership AND exclusion): the FORMULAIC TWIN sentence — the highest-
-- quality signal in the notes. Spanish-market makers ran paired brands, one domestic and
-- one export (Petaco/Recel, Recreativos Franco/Interflip), and IPDB writes BOTH sides:
--   domestic side: "Petaco is the name used for domestic games.
--                   The same company made an export version as Recel's 1980 'Black Magic'."
--   export side:   "Recel is the name used for export games.
--                   The same company made a domestic version as Petaco's 'Black Magic'."
-- Each model states its OWN role and NAMES its counterpart, so this needs no maker-level
-- inference and no maker lookup table: a model whose note says the TWIN is "domestic" is
-- itself the export, and vice versa. That makes it usable in both directions — it adds
-- export-side models as candidates and positively EXCLUDES the domestic side, which the
-- freetext detectors otherwise flag (a Petaco note says "export" only because it is
-- naming its Recel twin).
-- Shape notes: the qualifier floats around the keyword ("a 1-player domestic version",
-- "a domestic 4-player version", "a domestic SS version") and the article varies
-- (a/an/the), so both slots are optional word-runs. All 58 occurrences parse.
-- The independent "is the name used for <role> games" sentence is captured as
-- `declared_role` purely to cross-check the twin sentence; the two never disagree today,
-- and `export_checks` fails loudly if they ever do.
-- MATERIALIZED (a TABLE, not a view) — the one exception in this file. The regex below
-- is backtracking-heavy, and `_twin` is inlined into `export_candidates`, which
-- `export_summary` reference-expands ~20 times; as a view the parse re-runs on every one
-- of those and exhausts memory. A table computes it once at init. Nothing is persisted
-- (the database is :memory:), and like the views it stays non-TEMP so the DuckDB UI can
-- see it across connections.
CREATE OR REPLACE TABLE _twin AS
  WITH src AS (
    -- Cheap prefilter FIRST: the regex below is backtracking-heavy and this view is
    -- inlined into candidates, checks and the summary, so without this it re-scans all
    -- ~6.9k notes several times over and exhausts memory. Only these rows can match.
    SELECT id, ipdb_notes FROM models WHERE ipdb_notes ILIKE '%same company made%'
  ),
  p AS (
    SELECT id,
      regexp_extract(ipdb_notes, $$made (?:an?|the) (?:[A-Za-z0-9-]+ )*?(export|domestic) (?:[A-Za-z0-9-]+ )*?version as ([A-Z][A-Za-z. ]+?)'s (?:([0-9]{4}) )?'([^']+)'$$, 1) AS twin_kind,
      regexp_extract(ipdb_notes, $$made (?:an?|the) (?:[A-Za-z0-9-]+ )*?(export|domestic) (?:[A-Za-z0-9-]+ )*?version as ([A-Z][A-Za-z. ]+?)'s (?:([0-9]{4}) )?'([^']+)'$$, 2) AS twin_brand,
      regexp_extract(ipdb_notes, $$made (?:an?|the) (?:[A-Za-z0-9-]+ )*?(export|domestic) (?:[A-Za-z0-9-]+ )*?version as ([A-Z][A-Za-z. ]+?)'s (?:([0-9]{4}) )?'([^']+)'$$, 3) AS twin_year,
      regexp_extract(ipdb_notes, $$made (?:an?|the) (?:[A-Za-z0-9-]+ )*?(export|domestic) (?:[A-Za-z0-9-]+ )*?version as ([A-Z][A-Za-z. ]+?)'s (?:([0-9]{4}) )?'([^']+)'$$, 4) AS twin_name,
      regexp_extract(ipdb_notes, '(?i)is the name used for (export|domestic) games', 1) AS declared_role
    FROM src
  )
  SELECT
    id,
    -- this model's own role is the OPPOSITE of the twin it names
    CASE twin_kind WHEN 'domestic' THEN 'export' ELSE 'domestic' END AS role,
    twin_kind, twin_brand, NULLIF(twin_year, '') AS twin_year, twin_name,
    NULLIF(declared_role, '') AS declared_role
  FROM p
  WHERE twin_kind <> '';

-- Membership half of detector 4: the export side of a twin pair.
CREATE OR REPLACE VIEW _by_twin AS
  SELECT id FROM _twin WHERE role = 'export';

CREATE OR REPLACE VIEW _dest AS
  SELECT id, dest FROM _dest_freetext
  UNION SELECT id, dest FROM _dest_suffix;

-- Region detector: an export-context region phrase (see `_region_alias`) anywhere in
-- notes/notable-features. Feeds the `regions` column, NOT candidate membership — the
-- `market_kind = 'region'` case, i.e. a `target_market_label` with no country.
CREATE OR REPLACE VIEW _dest_region AS
  SELECT m.id, r.label AS region
  FROM models m
  JOIN _region_alias r
    ON regexp_matches(concat_ws(' | ', m.ipdb_notes, m.ipdb_notable_features), r.pattern);

-- assemble ──
-- One row per candidate model: which detectors fired, the parsed markets (country
-- slugs), and the maker-relative signal. "Export" is market-relative: a model built
-- for the SAME country its maker is based in is domestic, not export (README.md,
-- "Export is maker-relative"). market_is_maker_home flags those likely false
-- positives (e.g. Conquistador, a Portuguese maker's Portuguese-market game) for
-- review — it is a review signal, not an error, so it is NOT a check.
--   markets            : sorted country SLUGS parsed from the notes/name (may be empty)
--   regions            : sorted region LABELS parsed from the notes (the
--                        `target_market_label` case, e.g. ['Europe']); may be empty
--   market_kind        : how (if at all) the destination market is known —
--                        'country' if any country parsed, else 'region' if any region
--                        parsed, else 'unknown'. Mirrors the field the write path picks:
--                        country -> target_market_location, region -> target_market_label,
--                        unknown -> a ModelExportMarket row with neither, or no row at all.
--   maker_home_slug    : the maker's home country slug (model -> corporate_entity ->
--                        location), NULL when the maker has no located corporate entity
--   market_is_maker_home : a parsed market equals the maker's home country
-- MATERIALIZED (see the note on `_twin`). This is the hub of the file: five review views
-- build on it and `export_summary` reference-expands it ~30 times. As a view, every one
-- of those re-runs the whole detector stack (regex over ~6.9k notes, several times each)
-- and the summary exhausts memory. As a table it is computed once at init and every
-- consumer becomes a cheap scan. Still non-TEMP, so the UI sees it; nothing is persisted.
CREATE OR REPLACE TABLE export_candidates AS
  WITH ids AS (
    SELECT id FROM _by_notes
    UNION SELECT id FROM _dest_suffix
    UNION SELECT id FROM _by_opdb
    UNION SELECT id FROM _by_twin
  )
  SELECT
    m.id, m.name, m.manufacturer_name, m.opdb_id, m.label,
    EXISTS (SELECT 1 FROM _by_notes bn WHERE bn.id = m.id)          AS by_notes,
    EXISTS (SELECT 1 FROM _dest_suffix s WHERE s.id = m.id)         AS by_suffix,
    EXISTS (SELECT 1 FROM _by_opdb o WHERE o.id = m.id)             AS by_opdb,
    EXISTS (SELECT 1 FROM _by_twin t WHERE t.id = m.id)             AS by_twin,
    list_sort(list_distinct(
      COALESCE((SELECT list(d.dest) FROM _dest d WHERE d.id = m.id), []::VARCHAR[])
    )) AS markets,
    list_sort(list_distinct(
      COALESCE((SELECT list(dr.region) FROM _dest_region dr WHERE dr.id = m.id), []::VARCHAR[])
    )) AS regions,
    CASE
      WHEN EXISTS (SELECT 1 FROM _dest d WHERE d.id = m.id)        THEN 'country'
      WHEN EXISTS (SELECT 1 FROM _dest_region dr WHERE dr.id = m.id) THEN 'region'
      ELSE 'unknown'
    END AS market_kind,
    m.country_slug AS maker_home_slug,
    (SELECT name FROM countries WHERE slug = m.country_slug) AS maker_home_country,
    (m.country_slug IS NOT NULL
       AND EXISTS (SELECT 1 FROM _dest d WHERE d.id = m.id AND d.dest = m.country_slug)) AS market_is_maker_home,
    COALESCE((SELECT rewards FROM rewards rw WHERE rw.id = m.id), []::VARCHAR[]) AS rewards,
    m.ipdb_notes AS notes
  FROM models m
  WHERE m.id IN (SELECT id FROM ids)
    -- Positive exclusion: the twin sentence identifies this model as the DOMESTIC side,
    -- which outranks any freetext hit. A Petaco note says "export" only because it names
    -- its Recel twin; without this the domestic half of every pair is a false positive.
    AND m.id NOT IN (SELECT id FROM _twin WHERE role = 'domestic')
  ORDER BY m.name;

-- enrich ──
-- Candidate x lineage: does the model already carry a model->model edge?
--
-- The three facts read from TWO foundation views, and which one each uses is the
-- point rather than an implementation detail:
--   has_variant_of : a variant_of edge the model itself STATES. Directional on
--   rel_types        purpose — the direction IS the fact. A variant points at its
--                    base; the base is not a variant of the variant, so these read
--                    `model_edges` (outbound only).
--   has_edge       : "is this model connected to anything at all?" — a CONNECTEDNESS
--                    question, so it reads `model_edges_bidir`. An outbound-only test
--                    answers a confident false for a model whose relationship is
--                    stated from the other end, and the foundation counts 416 live
--                    models in exactly that position. This is not hypothetical here:
--                    while `has_edge` read `model_edges`, 30 of the 221 candidates
--                    were called edge-less despite carrying an inbound edge, and 24
--                    of them sat in `export_titlemate_review` asking a reviewer to
--                    find a relationship the catalog already recorded.
--   has_inbound_only : those rows, kept visible — a model whose only edge points at
--                    it. Worth a glance in its own right: it is often the ORIGINAL of
--                    an export, which is the reciprocal case this campaign mines.
-- MATERIALIZED for the same reason as `export_candidates` — the titlemate/orphan review
-- views and several summary rows all build on it.
CREATE OR REPLACE TABLE export_candidate_lineage AS
  SELECT
    c.id, c.name, c.label, c.by_notes, c.by_suffix, c.by_opdb, c.markets, c.rewards,
    EXISTS (SELECT 1 FROM model_edges e WHERE e.model_id = c.id AND e.relationship_type = 'variant_of') AS has_variant_of,
    COALESCE((
      SELECT list_sort(list_distinct(list(e.relationship_type)))
      FROM model_edges e WHERE e.model_id = c.id AND e.edge_source = 'relationship'
    ), []::VARCHAR[]) AS rel_types,
    EXISTS (SELECT 1 FROM model_edges_bidir e WHERE e.model_id = c.id) AS has_edge,
    (NOT EXISTS (SELECT 1 FROM model_edges e WHERE e.model_id = c.id)
       AND EXISTS (SELECT 1 FROM model_edges_bidir e WHERE e.model_id = c.id)) AS has_inbound_only,
    m.title_size,
    c.notes
  FROM export_candidates c
  JOIN models m ON m.id = c.id
  ORDER BY c.name;

-- review ──
-- Candidates that share a Title but carry no lineage edge. One row per
-- (candidate, title-mate) pair, to judge whether the candidate should be tied
-- to a mate — and, if so, how:
--   reward_differs : candidate and mate both have reward types, and they differ
--                    -> shape A, a reward-type variant_of the mate
--   same_maker     : same maker -> variant_of (family); different -> copy. Keyed
--                    on manufacturer_id — the user-facing maker brand. NOT
--                    corporate_entity_id (a single legal incarnation, which would
--                    split one brand's eras, e.g. Gottlieb, into "cross-maker"),
--                    and NOT the nullable IPDB trade-name text.
-- candidate_notes carries the FULL ipdb.notes free text for source review.
CREATE OR REPLACE VIEW export_titlemate_review AS
  SELECT
    c.id,
    c.label       AS candidate,
    c.rewards     AS candidate_rewards,
    c.markets,
    mate.label    AS titlemate,
    COALESCE((SELECT rewards FROM rewards rm WHERE rm.id = mate.id), []::VARCHAR[]) AS titlemate_rewards,
    (len(c.rewards) > 0
       AND len(COALESCE((SELECT rewards FROM rewards rm WHERE rm.id = mate.id), []::VARCHAR[])) > 0
       AND c.rewards <> COALESCE((SELECT rewards FROM rewards rm WHERE rm.id = mate.id), []::VARCHAR[])) AS reward_differs,
    (cm.manufacturer_id IS NOT NULL
       AND cm.manufacturer_id = mate.manufacturer_id) AS same_maker,
    c.notes       AS candidate_notes
  FROM export_candidate_lineage l
  JOIN export_candidates c ON c.id = l.id
  JOIN models cm            ON cm.id = c.id
  JOIN models mate          ON mate.title_id = cm.title_id AND mate.id <> c.id
  WHERE NOT l.has_edge AND l.title_size > 1
  ORDER BY c.name, mate.name;

-- Candidates with no lineage edge AND alone in their Title (no sibling in the
-- catalog). Probe whether ANY free text names an origin model. Free text scanned
-- = ipdb.notes + ipdb.notable_features + the description column (all the prose a
-- candidate carries).
--   quoted_names       : distinct 'Quoted Game Names' across that free text
--   quoted_in_catalog  : at least one of those names exists as a model today
--   relates_phrase     : free text uses a lineage phrase (copy/version/conversion
--                        of, similar to, same playfield as, made for export)
--   has_freetext       : any of the three sources is non-empty
-- Reading:
--   quoted_in_catalog            -> findable: author a copy (or variant) to it
--   quoted_names but not in cat. -> origin named but not yet a model: create it
--   has_freetext, no quoted name -> prose exists but names no model (shape C)
--   no freetext at all           -> genuine shape C: market fact, no lineage
-- freetext carries the FULL concatenated prose for source review.
CREATE OR REPLACE VIEW export_orphan_review AS
  WITH base AS (
    SELECT
      l.id, l.name AS candidate, l.label AS candidate_label, m.manufacturer_name AS candidate_maker,
      m.game_format_slug, l.markets, l.by_opdb,
      NULLIF(concat_ws(
        E'\n---\n',
        NULLIF(m.ipdb_notes, ''),
        NULLIF(m.ipdb_notable_features, ''),
        NULLIF(m.description, '')
      ), '') AS freetext
    FROM export_candidate_lineage l
    JOIN models m ON m.id = l.id
    WHERE NOT l.has_edge AND l.title_size <= 1
  ),
  scanned AS (
    SELECT
      b.*,
      -- Permissive quote class: IPDB mixes backtick/straight/curly quotes, e.g.
      -- Elite Guard's origin is written `Palace Guard' (backtick open). Surfaces
      -- some jargon too ('FunGame') — a review aid, verified against the note.
      list_distinct(regexp_extract_all(COALESCE(b.freetext, ''), '[`''‘“"]([A-Z][^`''’“”"]{1,40})[''’”"]', 1)) AS quoted_names,
      regexp_matches(COALESCE(b.freetext, ''),
        '(copy of|version of|conversion of|similar to|same (playfield )?(layout|design|game) as|made for export)') AS relates_phrase,
      (b.freetext IS NOT NULL) AS has_freetext
    FROM base b
  )
  SELECT
    s.*,
    EXISTS (
      SELECT 1 FROM models s2 WHERE list_contains(s.quoted_names, s2.name)
    ) AS quoted_in_catalog,
    CASE
      WHEN NOT s.has_freetext        THEN 'no freetext'
      WHEN len(s.quoted_names) = 0   THEN 'freetext, no origin named'
      ELSE 'origin named'
    END AS origin_lead
  FROM scanned s
  ORDER BY s.candidate;

-- Name-family regroup candidates for the alone-in-Title orphans. A candidate and
-- another model of the SAME MAKER (manufacturer_id — the brand, so a product line
-- spanning corporate eras still links) sit in separate singleton Titles but their
-- significant-name-token sets nest (one contains the other), e.g.
--   Palm Beach Club  <-  Palm Beach          Diamond Flipper Di Lusso <- Diamond Flipper
-- Token nesting (containment), not mere overlap, so 'Diamond Flipper' and
-- 'Golden Flipper' do NOT link (distinct games) while 'Circus' <- 'Super Circus'
-- does. relation reads from the MEMBER's side:
--   'member is base'      member's tokens ⊆ candidate's  (candidate adds a modifier)
--   'member extends'      candidate's tokens ⊆ member's  (member adds a modifier)
--   'same base'           identical token sets
-- Filter origin_lead='freetext, no origin named' for the shape-C set. Tiers: a
-- distinctive base theme (Palm Beach, Carrousel) is a strong regroup case; a
-- generic base (Flipper, Circus as a maker product line) is weaker — judge from
-- the note, this only narrows the field.
CREATE OR REPLACE VIEW export_name_family AS
  WITH toks AS (
    SELECT
      m.id, m.name, m.manufacturer_id AS mfr, m.title_id, m.title_size,
      list_sort(list_distinct(list_filter(
        string_split(lower(regexp_replace(m.name, '[^a-z0-9]+', ' ', 'g')), ' '),
        lambda t: length(t) >= 4 AND t NOT IN ('game', 'games', 'ball', 'balls', 'bingo')
      ))) AS tk
    FROM models m
  ),
  cand AS (
    SELECT o.id, o.candidate, o.candidate_label, o.origin_lead, o.markets
    FROM export_orphan_review o
  )
  SELECT
    c.candidate_label AS candidate, c.origin_lead, c.markets,
    ct.tk           AS candidate_tokens,
    (SELECT label FROM models WHERE id = n.id) AS family_member,
    n.tk            AS member_tokens,
    (n.title_id IS NOT NULL
       AND n.title_size = 1) AS member_alone_in_title,
    EXISTS (SELECT 1 FROM cand c2 WHERE c2.id = n.id) AS member_is_also_candidate,
    CASE
      WHEN ct.tk = n.tk                                       THEN 'same base'
      WHEN len(list_intersect(ct.tk, n.tk)) = len(n.tk)       THEN 'member is base'
      ELSE 'member extends'
    END AS relation
  FROM cand c
  JOIN toks ct ON ct.id = c.id
  JOIN toks n  ON n.mfr = ct.mfr AND n.id <> c.id
              AND len(ct.tk) > 0 AND len(n.tk) > 0
              AND (len(list_intersect(ct.tk, n.tk)) = len(n.tk)
                   OR len(list_intersect(ct.tk, n.tk)) = len(ct.tk))
  ORDER BY c.candidate, n.name;

-- NAMESAKES ACROSS TITLES — the SAME GAME NAME sitting in a DIFFERENT Title.
--
-- `export_name_family` above is same-maker and token-NESTING ('Palm Beach' <- 'Palm Beach
-- Club'). This view is the other half: an EXACT name match, across makers, in a separate
-- Title. It is the bucket the Acapulco case lives in — Splin S.A.'s Belgian bingo
-- 'Acapulco' ("made for export to France") sits in `acapulco-2` while Bally's 'Acapulco'
-- sits in `acapulco`, with no edge and no shared Title between them.
--
-- Two distinct actions come out of a row here, and they are NOT the same decision:
--   the EDGE   same maker -> `export_edition_of`; a DIFFERENT maker's build of the same
--              game is a `copy` (the 0128 campaign), never an export edition. That rule
--              is `patch_fk_cross_maker` in the checks below, and it is what makes this a
--              REVIEW view rather than an emit tier: most rows here want a `copy`.
--   the TITLE  a Title groups the same game, so two singleton Titles holding the same
--              game are a merge lead — move the model, then retire the empty Title.
-- `title_merge_lead` marks the second independently of the first.
--
-- Name normalization strips ONE trailing parenthetical, which is what lets the campaign's
-- own `(Country)` suffix models find their original ('On Beam (Italy)' -> 'On Beam') —
-- but it also collapses 'KISS (Limited Edition)' onto 'KISS', so `name_match` records
-- whether the match was exact or needed the strip, and the reviewer judges accordingly.
-- MAKER ERA — the year span a manufacturer's DATED models occupy, used as a fallback
-- when a model itself has no year.
--
-- This exists because dating the models did not, on its own, fix the case that
-- motivated the whole view. ../0181-bingo-years dated 109 bingos, but bingo.cdyn.com
-- lists no Splin 'Acapulco', so that model stayed year-less and the pair stayed
-- mis-tiered. What 0181 DID establish is Splin's era: six models dated 1999-2003.
-- Against Bally's 1961 'Acapulco' that is a 38-year separation — the same conclusion
-- a direct year comparison would have reached, from the maker instead of the model.
--
-- Requires at least 3 dated models, so one stray date cannot define an era. A maker
-- below that threshold yields no era and the pair simply keeps an unknown gap, which
-- is the honest answer rather than a guess.
CREATE OR REPLACE VIEW _maker_era AS
  SELECT id AS manufacturer_id,
         year_of_first_model AS era_start, year_of_last_model AS era_end, n_dated
  FROM manufacturers WHERE n_dated >= 3;

-- Distance in years between two [start, end] spans; 0 when they overlap.
CREATE OR REPLACE MACRO _span_gap(a_start, a_end, b_start, b_end) AS
  greatest(0, greatest(a_start - b_end, b_start - a_end));

-- ABBREVIATION GUARD — every sentence extractor in this file bounds a sentence with a
-- run of non-period characters (`[^.]*\.`), which breaks on the period inside a TITLE
-- ABBREVIATION. It shipped two truncated quotes: Recel's twin sentence for 'Mr. Doom'
-- and 'Mr. Evil' was cut at "as Petaco's 'Mr." — the game name severed mid-word, the
-- opening quote never closed.
--
-- `make verify-quotes` cannot catch this. A truncated span is still a verbatim
-- substring of the source, so it passes; only reading the quote reveals it.
--
-- The guard swaps the period for a sentinel before extraction and swaps it back after,
-- so the emitted quote stays byte-identical to the source. Scoped tightly: only these
-- titles, and only when a CAPITALIZED word follows, which is the mid-name shape. Not
-- guarded are 'Inc.', 'Co.', 'Ltd.', 'No.' and 'Mfg.' — those genuinely do end
-- sentences in this corpus ("...manufactured by Williams Electronics, Inc."), and
-- merging two sentences into one quote would be its own defect.
CREATE OR REPLACE MACRO _abbrev_guard(txt) AS
  regexp_replace(COALESCE(txt, ''), '\b(Mr|Mrs|Ms|Dr|St|Capt|Sgt)\.(\s+[A-Z])', '\1' || chr(1) || '\2', 'g');
CREATE OR REPLACE MACRO _abbrev_unguard(txt) AS replace(COALESCE(txt, ''), chr(1), '.');

-- The maker reference IPDB writes for another machine: "<Maker>'s <year> '<Name>'".
-- `'s?` because the possessive loses its s on a maker whose name ends in one —
-- "Gottlieb's 1968 'Big Jack'" but "Williams' 1971 'Jackpot'". Groups: 1 maker,
-- 2 year, 3 name. Defined here rather than beside the reciprocal parse because the
-- MERGE gate needs it too: resolving a quote's reference on name+maker+YEAR is the
-- only thing that separates same-named models, which is this view's whole population.
CREATE OR REPLACE MACRO _maker_ref_pat() AS
  '([A-Z][A-Za-z0-9.&-]*(?: [A-Z][A-Za-z0-9.&-]*)*)''s? (?:([0-9]{4}) )?''([^'']+)''';

-- BINGO SUB-GENRE — a second, independent discriminator for same-named bingos.
--
-- `game_format_slug` is 'bingo-pinball' for the whole corpus, so it cannot separate
-- two same-named bingos at all. The gameplay-feature vocabulary can: bingos divide
-- into a plain card game and several distinctive Bally mechanisms, and the markers are
-- near-mutually-exclusive in the data (115 models carry `bingo-cards` alone;
-- mystic-lines, magic-screen and magic-squares appear alone 14/14/11 times).
--
-- On the worked example this settles structurally what the maker era only inferred:
-- Bally's 'Acapulco' is [magic-squares] and Splin's is [bingo-cards] — disjoint, so
-- not the same game whatever their names say.
--
-- The closed marker set is declared rather than derived: most gameplay features
-- (trap-holes, flippers, rollover-buttons) are incidental hardware shared across
-- sub-genres, and treating those as identity would split games that ARE the same.
CREATE OR REPLACE VIEW _bingo_subgenre AS
  SELECT gf.model_id, list_sort(list_distinct(list(gf.feature_slug))) AS marks
  FROM model_gameplay_features gf
  WHERE gf.feature_slug IN
    ('bingo-cards', 'super-cards', 'magic-squares', 'magic-screen', 'mystic-lines', 'magic-lines')
  GROUP BY gf.model_id;

-- The tiering below is calibrated on the pair distribution, and the two axes that
-- actually separate signal from coincidence are YEAR GAP and GAME FORMAT:
--   'Bazaar' (Bally 1966) vs 'Bazaar' (ESCO 1937) — 29 years apart, unrelated games that
--   happen to share a generic noun. 39 of the cross-maker pairs are of exactly this kind.
-- A NULL year is NOT treated as a far gap: the entire modern European bingo cohort
-- (Splin, SIRMO, WIMI, TSCC, Fipermatic) carries no year at all, and that cohort is where
-- the real cross-maker builds are. Those rows lean on maker HOME COUNTRY instead — a
-- Belgian maker's same-named build of a US game is a foreign build, not a coincidence.
CREATE OR REPLACE VIEW export_namesake_review AS
  WITH cand AS (
    SELECT
      c.id, c.label AS candidate, c.markets, c.market_kind, c.notes,
      cm.name, cm.title_id, cm.title_slug, cm.title_size, cm.manufacturer_id,
      cm.manufacturer_name,
      cm.year, cm.country_slug AS maker_home, cm.game_format_slug,
      name_key(cm.name) AS key,
      EXISTS (SELECT 1 FROM model_edges_bidir e WHERE e.model_id = c.id) AS has_edge
    FROM export_candidates c
    JOIN models cm ON cm.id = c.id
  ),
  pairs AS (
    SELECT
      c.*,
      o.id AS namesake_id, o.label AS namesake, o.slug AS namesake_slug,
      o.title_slug AS namesake_title, o.manufacturer_id AS o_mfr,
      o.year AS namesake_year, o.country_slug AS namesake_maker_home,
      o.game_format_slug AS o_fmt,
      (c.name = o.name) AS exact_name,
      (c.manufacturer_id IS NOT NULL AND c.manufacturer_id = o.manufacturer_id) AS same_maker,
      (c.game_format_slug IS NOT DISTINCT FROM o.game_format_slug) AS same_game_format,
      COALESCE(cs.marks, []::VARCHAR[]) AS subgenre,
      COALESCE(os.marks, []::VARCHAR[]) AS namesake_subgenre,
      -- Only ever SEPARATES: both sides must carry markers and share none. An absent
      -- marker set is unknown, not different, so this can never merge two games.
      (cs.marks IS NOT NULL AND os.marks IS NOT NULL
         AND len(list_intersect(cs.marks, os.marks)) = 0) AS subgenre_differs,
      (c.game_format_slug IS NOT DISTINCT FROM o.game_format_slug
         AND NOT (cs.marks IS NOT NULL AND os.marks IS NOT NULL
                  AND len(list_intersect(cs.marks, os.marks)) = 0)) AS same_format,
      CASE WHEN c.year IS NOT NULL AND o.year IS NOT NULL
           THEN abs(c.year - o.year) END AS year_gap,
      -- The fallback gap: each side's own year when it has one, else its maker's era.
      -- NULL only when a side is undated AND its maker has too few dated models.
      _span_gap(
        COALESCE(c.year, ce.era_start), COALESCE(c.year, ce.era_end),
        COALESCE(o.year, oe.era_start), COALESCE(o.year, oe.era_end)
      ) AS era_gap,
      (c.year IS NULL OR o.year IS NULL) AS era_gap_uses_maker,
      -- The candidate's maker and the namesake's maker are based in different countries:
      -- the shape of a foreign licensed/unlicensed build (Splin/Bally, Fipermatic/Gottlieb).
      (c.country_slug_ok AND o.country_slug IS NOT NULL
         AND c.maker_home IS DISTINCT FROM o.country_slug) AS foreign_maker,
      (c.title_size = 1 AND o.title_size = 1) AS both_alone_in_title,
      EXISTS (SELECT 1 FROM export_candidates c2 WHERE c2.id = o.id) AS namesake_is_candidate,
      -- An edge ALREADY joining exactly this pair, in either direction — the row is
      -- settled and only the Title question (if any) is left.
      EXISTS (SELECT 1 FROM model_edges_bidir e
               WHERE e.model_id = c.id AND e.target_id = o.id) AS already_related
    FROM (SELECT *, (maker_home IS NOT NULL) AS country_slug_ok FROM cand) c
    JOIN models o
      ON name_key(o.name) = c.key
     AND o.id <> c.id
     AND o.title_id IS DISTINCT FROM c.title_id
    LEFT JOIN _maker_era ce ON ce.manufacturer_id = c.manufacturer_id
    LEFT JOIN _maker_era oe ON oe.manufacturer_id = o.manufacturer_id
    LEFT JOIN _bingo_subgenre cs ON cs.model_id = c.id
    LEFT JOIN _bingo_subgenre os ON os.model_id = o.id
  )
  SELECT
    p.id, p.candidate, p.markets, p.market_kind, p.title_slug,
    p.namesake_id, p.namesake, p.namesake_slug, p.namesake_title,
    CASE WHEN p.exact_name THEN 'exact' ELSE 'suffix-stripped' END AS name_match,
    p.same_maker, p.same_format, p.same_game_format, p.subgenre_differs,
    p.subgenre, p.namesake_subgenre,
    p.year_gap, p.era_gap, p.foreign_maker,
    -- Which measurement the tier below actually used, so a reviewer can weigh it:
    -- a model's own year is evidence, its maker's era is an inference from siblings.
    CASE WHEN p.year_gap IS NOT NULL THEN 'model years'
         WHEN p.era_gap IS NOT NULL  THEN 'maker era'
         ELSE 'unknown' END AS gap_basis,
    p.maker_home, p.namesake_maker_home,
    p.both_alone_in_title, p.namesake_is_candidate, p.has_edge, p.already_related,
    -- lead: what the pair is EVIDENCE FOR, before anyone reads a source. Ordered most
    -- to least actionable; every tier still wants the note read before it becomes a claim.
    CASE
      WHEN p.already_related                             THEN 'already related'
      -- Same maker, same format, contemporaneous: 'On Beam (Italy)' (Bally 1969) vs
      -- 'On Beam' (Bally 1969). This is the export_edition_of shape outright.
      WHEN p.same_maker AND p.same_format
           AND COALESCE(p.year_gap, p.era_gap, 0) <= 2    THEN 'export edition'
      WHEN p.same_maker AND p.same_format                 THEN 'same maker, check years'
      WHEN p.same_maker                                   THEN 'same maker, format differs'
      -- Cross-maker foreign build — the Splin/Bally and Fipermatic/Gottlieb shape. The
      -- honest edge is `copy` (0128), NOT export_edition_of.
      WHEN p.same_format AND p.foreign_maker
           AND COALESCE(p.year_gap, p.era_gap, 0) <= 15   THEN 'foreign build (copy)'
      WHEN p.same_format
           AND COALESCE(p.year_gap, p.era_gap, 0) <= 5    THEN 'cross-maker, contemporaneous'
      -- Ordered above the year arm deliberately: when both fire the verdict is the
      -- same, and a reviewer is better served by the structural reason (two disjoint
      -- bingo mechanisms) than by a gap inferred from the maker's era.
      WHEN p.subgenre_differs                             THEN 'likely coincidence (bingo sub-genre differs)'
      WHEN COALESCE(p.year_gap, p.era_gap) >= 16          THEN 'likely coincidence (years apart)'
      WHEN NOT p.same_format                              THEN 'likely coincidence (format differs)'
      ELSE 'needs a source read'
    END AS lead,
    -- A Title groups one game, so two SINGLETON Titles holding the same game are a merge
    -- lead: move the model into the surviving Title, then retire the emptied one. Held
    -- back from the coincidence tiers, where the shared name means nothing.
    (p.both_alone_in_title
       AND p.same_format
       AND COALESCE(p.year_gap, p.era_gap, 0) <= 15) AS title_merge_lead,
    p.notes AS candidate_notes
  FROM pairs p
  ORDER BY p.candidate, p.namesake;

-- ── TITLE MERGES: the emit layer ───────────────────────────────────────────
-- `export_namesake_review` is a worklist for a human. This is the gate between it
-- and a claim, and it is deliberately much narrower — a name match plus a plausible
-- era is a LEAD, and DataPatchAuthoring.md is explicit that a shared name or Title is
-- a lead to verify against the source, never evidence in itself.
--
-- The gate exists because this campaign already produced one wrong claim from exactly
-- this shape. Splin S.A.'s 'Acapulco' looked like a foreign build of Bally's, and
-- nothing in any source said so: bingo.cdyn.com dates Splin 1999-2003 against Bally's
-- 1961, and the two carry disjoint bingo mechanisms. An ungated emitter would have
-- authored that edge. So a row emits ONLY when the mover's own note names the target
-- in a lineage sentence, and everything else is auditable in `export_merge_blocked`.
--
-- A merge is TWO patches, never one: `delete:`'s referrer check reads live DB state,
-- so a model re-homed earlier in the SAME patch is not yet visible (DataPatches.md).
-- Patch A re-homes the model and reslugs the doomed Title; patch B deletes it.

-- Which side moves. The mover is the model that is the copy/export; the survivor owns
-- the Title. Direction is taken from the tier, never from the row order:
--   'export edition'       the candidate IS an export candidate by construction, so
--                          it moves onto the original's Title.
--   'foreign build (copy)' the foreign maker's build moves onto the original's Title;
--                          the original is the one whose maker is NOT foreign-built.
-- Where both models are export candidates the pair appears from both ends (Kicker /
-- Kicker (Italy)), so the older model — by its own year, else its maker's era start —
-- is taken as the survivor and the mirror row drops out.
-- MATERIALIZED, like `_twin` and `export_candidates` above: it sits under two review
-- views AND under `export_summary`, which reference-expands them, so as a view the
-- whole namesake stack re-runs on every expansion.
CREATE OR REPLACE TABLE _merge_pair AS
  SELECT
    n.*,
    m.slug AS mover_slug, m.name AS mover_name, m.ipdb_id AS mover_ipdb_id,
    m.manufacturer_slug AS mover_maker_slug, m.title_slug AS mover_title,
    t.slug AS survivor_slug, t.name AS survivor_name, t.title_slug AS survivor_title,
    -- the surviving Title's slug carries a numeric suffix -> the doomed Title has to
    -- free nothing, but the survivor keeps a less-readable slug; reported, not fixed.
    regexp_matches(t.title_slug, '-[0-9]+$') AS survivor_title_is_suffixed
  FROM export_namesake_review n
  JOIN models m ON m.id = n.id
  JOIN models t ON t.id = n.namesake_id
  WHERE n.title_merge_lead
    AND NOT n.already_related
    AND n.lead IN ('export edition', 'foreign build (copy)')
    -- drop the mirror: keep the row whose candidate is the YOUNGER of the pair
    AND COALESCE(m.year, 9999) >= COALESCE(t.year, 0);

-- The evidence: a sentence in the MOVER's own note that names the survivor AND carries
-- a lineage predicate. Both conditions matter — a note that merely mentions the other
-- game (a "same playfield as" aside, an unrelated cross-reference) is not a statement
-- that this model is a build of it. Normalized exactly as verify_quotes normalizes the
-- source side, so an extracted span stays a verbatim substring.
CREATE OR REPLACE TABLE _merge_evidence AS
  SELECT
    p.id,
    _abbrev_unguard(trim(regexp_extract(_abbrev_guard(nn.note_norm),
      '([^.]*(?:copy of|version of|conversion of|made for export|exported to)[^.]*\.)', 1))) AS sentence,
    nn.note_norm
  FROM _merge_pair p,
       LATERAL (SELECT regexp_replace(
         replace(replace(replace(replace(COALESCE(p.candidate_notes, ''), '“', '"'), '”', '"'),
                 '‘', ''''), '’', ''''),
         '\s+', ' ', 'g') AS note_norm) nn;

-- The rows a generator may write, one per merge, plus everything each patch needs.
-- Nothing here is inferred: `quote` is verbatim from the mover's note and names the
-- survivor, and a row without one does not appear.
-- Scored ONCE, materialized, and read by both the emit view and the blocked view —
-- so the gate has exactly one definition and the two can never drift apart.
--
-- The reference in the quote is RESOLVED on name + maker + YEAR, not merely searched
-- for by name. That is the whole gate, because this view's population is same-NAMED
-- models: a name-containment test passes against every one of them. It was not
-- hypothetical — with a name test, 'Hula-Hula (Italy)' cited "Chicago Coin's 1966
-- 'Hula-Hula'" and was matched to the 1965 model, and the 1966 'Hula-Hula' cited a
-- sentence naming ITSELF. Two of three emitted rows were wrong. Same discipline as
-- `_origin_ref` further down, and for the same reason.
CREATE OR REPLACE TABLE _merge_scored AS
  WITH parsed AS (
    SELECT
      p.*, e.sentence,
      NULLIF(regexp_extract(COALESCE(e.sentence, ''), _maker_ref_pat(), 1), '') AS ref_maker,
      NULLIF(regexp_extract(COALESCE(e.sentence, ''), _maker_ref_pat(), 2), '') AS ref_year,
      NULLIF(regexp_extract(COALESCE(e.sentence, ''), _maker_ref_pat(), 3), '') AS ref_name
    FROM _merge_pair p
    LEFT JOIN _merge_evidence e ON e.id = p.id
  ),
  resolved AS (
    SELECT
      q.*,
      -- exactly one live model matching name + maker (+ year when the quote gives one)
      (SELECT list(m.id) FROM models m
        WHERE m.name = q.ref_name
          AND m.manufacturer_name = q.ref_maker
          AND (q.ref_year IS NULL OR m.year IS NOT DISTINCT FROM TRY_CAST(q.ref_year AS BIGINT))
      ) AS ref_ids
    FROM parsed q
  )
  SELECT
    r.* EXCLUDE (ref_ids),
    CASE WHEN len(r.ref_ids) = 1 THEN r.ref_ids[1] END AS ref_model_id,
    CASE
      WHEN r.mover_ipdb_id IS NULL              THEN 'mover has no ipdb id to cite'
      WHEN COALESCE(r.sentence, '') = ''        THEN 'no lineage sentence in the mover''s note'
      WHEN length(r.sentence) NOT BETWEEN 20 AND 240 THEN 'sentence out of bounds'
      WHEN r.sentence LIKE '%' || chr(65533) || '%'  THEN 'mojibake'
      WHEN r.ref_name IS NULL                   THEN 'lineage sentence names no model'
      WHEN len(r.ref_ids) = 0                   THEN 'quoted reference resolves to no model'
      WHEN len(r.ref_ids) > 1                   THEN 'quoted reference is ambiguous'
      -- the source describes the mover in terms of ITSELF (an IPDB self-reference);
      -- it establishes nothing about any other model
      WHEN r.ref_ids[1] = r.id                  THEN 'quote is self-referential'
      -- the source names a real model, just not the one this pairing assumed. NOT an
      -- error in the source — a lead pointing somewhere else, which the blocked view
      -- surfaces so the true target can be picked up by hand.
      WHEN r.ref_ids[1] <> r.namesake_id        THEN 'quote names a different model'
    END AS blocked_reason
  FROM resolved r;

CREATE OR REPLACE VIEW export_merge_rows AS
  SELECT
    s.id, s.mover_slug, s.candidate AS mover, s.mover_ipdb_id, s.mover_title,
    s.namesake_id AS survivor_id, s.survivor_slug, s.namesake AS survivor, s.survivor_title,
    s.lead,
    -- PATCH A — re-home the model. The disambiguating slug takes the MAKER suffix
    -- (0140/0148's convention: big-valley-rmg, not big-valley-2), because a numeric
    -- suffix says only "another one" while the maker says which one.
    -- The maker suffix (0140/0148: big-valley-rmg) disambiguates a CROSS-MAKER copy —
    -- it names whose build this is. On a same-maker export edition the maker is the one
    -- thing the two models SHARE, so the suffix says nothing: 'hula-hula-chicago-coin'
    -- distinguishes it from no one, all three Hula-Hulas being Chicago Coin.
    -- So: rename only cross-maker, and otherwise keep the existing slug — which for
    -- these already carries the real disambiguator in the name (`hula-hula-italy`,
    -- `on-beam-italy`). NULL means "no slug change in the patch".
    -- name_NORM, not name_key: the trailing parenthetical IS the disambiguator, and
    -- stripping it collided 'Hula-Hula' with 'Hula-Hula (Italy)' onto one slug.
    CASE WHEN NOT s.same_maker
         THEN regexp_replace(name_norm(s.mover_name), ' ', '-', 'g') || '-' || s.mover_maker_slug
    END AS new_slug,
    -- A bare numeric slug survives a same-maker merge unchanged and stays unhelpful.
    -- Flagged, never auto-renamed: the right disambiguator (reward type, year, market)
    -- is a judgement the source has to support, not one to synthesise here.
    (s.same_maker AND regexp_matches(s.mover_slug, '-[0-9]+$')) AS slug_needs_review,
    s.survivor_title AS new_title,
    -- the edge: same maker -> an export edition; a different maker's build is a copy
    CASE WHEN s.same_maker THEN 'export_edition_of' ELSE 'copy' END AS edge_kind,
    s.sentence AS quote,
    -- PATCH B — retire the emptied Title. Reslugged to '-deleted' in patch A first, so
    -- the retired Title is legible as retired and cannot shadow a live slug.
    s.mover_title AS doomed_title,
    s.mover_title || '-deleted' AS doomed_title_new_slug,
    'Orphaned after its sole model ('
      || CASE WHEN NOT s.same_maker
              THEN regexp_replace(name_norm(s.mover_name), ' ', '-', 'g') || '-' || s.mover_maker_slug
              ELSE s.mover_slug END
      || ') was merged into the ' || s.survivor_title || ' title.' AS delete_note,
    s.survivor_title_is_suffixed,
    s.candidate_notes
  FROM _merge_scored s
  WHERE s.blocked_reason IS NULL
  ORDER BY s.mover_slug;

-- The merges the gate held back, with the reason — a real review queue. Most rows here
-- are not wrong, merely unsourced: the pair may well be the same game, and a human
-- reading the note (or finding a source) can promote it.
CREATE OR REPLACE VIEW export_merge_blocked AS
  SELECT blocked_reason, id, mover_slug, candidate AS mover, namesake AS survivor,
         (SELECT label FROM models m WHERE m.id = _merge_scored.ref_model_id) AS quote_names,
         lead, year_gap, era_gap, gap_basis, sentence, candidate_notes
  FROM _merge_scored WHERE blocked_reason IS NOT NULL
  ORDER BY blocked_reason, mover_slug;

-- Twin pairs, export side -> its named domestic counterpart. This is the most directly
-- actionable view in the file: each row is a ready-made `export_edition_of` edge
-- (export model IS the export edition of the domestic model), parsed deterministically
-- rather than guessed. `domestic_model_id IS NULL` means the note names a counterpart
-- that isn't in the catalog yet — create it, or reconcile the name.
-- Note the twin is NOT always the same title: Interflip's 'Dragon' pairs with
-- Recreativos Franco's 'Dragoon', and player counts can differ across the pair.
CREATE OR REPLACE VIEW export_twin_pairs AS
  SELECT
    t.id            AS export_model_id,
    m.label         AS export_model,
    t.twin_brand    AS domestic_brand,
    t.twin_name     AS domestic_name,
    t.twin_year     AS domestic_year,
    d.id            AS domestic_model_id,
    d.label         AS domestic_model,
    t.declared_role AS export_side_declared_role
  FROM _twin t
  JOIN models m ON m.id = t.id
  LEFT JOIN models d ON d.name = t.twin_name AND d.manufacturer_name = t.twin_brand
  WHERE t.role = 'export'
  ORDER BY m.label;

-- PARKED SET — "for the <X> market" phrasing, deliberately NOT candidates.
-- This phrasing was pulled out of `_by_notes` because it is mostly noise (see the note
-- there). These are the models it uniquely supplied: matched by the phrase, but claimed
-- by NO other detector, so removing the clause dropped them from `export_candidates`.
-- Kept here so the ~5 genuine ones aren't lost — a later pass triages this view and
-- promotes the real exports (by fixing their source data or adding a precise detector).
-- `lead` is the triage signal:
--   'foreign country'    a parsed market that is NOT the maker's home -> likely a real
--                        export (Vector/German market, Grande Domino/Italian market)
--   'maker-home country' parsed market == maker's home -> domestic, not export
--   'region'            an export-context region phrase resolved instead of a country
--   'no market'         the phrase matched but nothing resolved -> almost all noise
CREATE OR REPLACE VIEW export_market_phrase_review AS
  WITH matched AS (
    SELECT id FROM (
      SELECT id, regexp_replace(COALESCE(ipdb_notes, ''), '(?i)quantity produced for export', '', 'g') AS n
      FROM models
    ) WHERE n ILIKE '%for the % market%'
  ),
  claimed AS (
    SELECT id FROM _by_notes
    UNION SELECT id FROM _dest_suffix
    UNION SELECT id FROM _by_opdb
  )
  SELECT
    m.id,
    m.label,
    list_sort(list_distinct(
      COALESCE((SELECT list(d.dest) FROM _dest d WHERE d.id = m.id), []::VARCHAR[])
    )) AS parsed_market,
    m.country_slug AS maker_home_slug,
    CASE
      WHEN EXISTS (SELECT 1 FROM _dest d WHERE d.id = m.id
                     AND d.dest IS DISTINCT FROM m.country_slug)        THEN 'foreign country'
      WHEN EXISTS (SELECT 1 FROM _dest d WHERE d.id = m.id)             THEN 'maker-home country'
      WHEN EXISTS (SELECT 1 FROM _dest_region r WHERE r.id = m.id)      THEN 'region'
      ELSE 'no market'
    END AS lead,
    m.ipdb_notes AS notes
  FROM models m
  JOIN matched x ON x.id = m.id
  WHERE m.id NOT IN (SELECT id FROM claimed)
  ORDER BY lead, m.label;

-- Market review: one row per candidate focused on the DESTINATION market, to fill
-- the ModelExportMarket rows (flipcommons' Exports.md → the join table). `market_kind`
-- is the headline — 'country' rows map to `target_market_location`, 'region' to `target_market_label`,
-- 'unknown' to a row with neither (or no row at all). `n_markets` > 1 flags the rare
-- multi-country build (the join table's reason for being). `notes` carries the source
-- text so a reviewer can fill or correct a market the narrow parser missed — 'unknown'
-- does NOT mean the prose names no market, only that no detector resolved one.
CREATE OR REPLACE VIEW export_market_review AS
  SELECT
    c.id, c.label AS candidate, c.manufacturer_name,
    c.market_kind,
    c.markets,
    len(c.markets)      AS n_markets,
    c.regions,
    c.maker_home_country,
    c.market_is_maker_home,
    c.notes
  FROM export_candidates c
  ORDER BY c.market_kind, c.name;

-- emit ──
-- The PATCH-ROW layer: the subset of candidates safe to author WITHOUT a per-row
-- source read, shaped so `gen.py` is a pure emitter. Everything above is discovery;
-- this is the gate between discovery and a claim.
--
-- The review views above are worklists for a HUMAN. This layer is deliberately much
-- narrower, because `by_notes` membership is a keyword match and a keyword match is
-- not a claim. Sampling the bucket turns up three ways a note mentions export while
-- the model is NOT one: the note is about ANOTHER model's export ("Also produced as
-- a 4-player Williams' 1971 'Jackpot' made for export" — Jackpot is the export, not
-- Gold Rush), the note hedges ("likely for export", "It's possible that ... was only
-- a name change for export reasons"), or export is background prose about the
-- industry ("Bally's 50-cycle motor used for export games"). Same shape as
-- ../0128-relationships/relationships.sql's certain tier, and the same remedy:
-- score the DISQUALIFIERS explicitly and route the losers to an auditable rejected
-- view rather than dropping them silently.

-- The evidence spans, one per candidate. `note_norm` is the note put through exactly
-- the normalization scripts/quote_verify/verify_quotes.py applies to the SOURCE side
-- (the four smart quotes straightened, whitespace runs collapsed), so an extracted
-- span stays a verbatim substring of pinexplore's corpus. Backticks are deliberately
-- NOT straightened — IPDB writes `Title' and verify_quotes doesn't touch them either.
--   export_sentence : the single sentence carrying export phrasing, bounded by a run
--                     of non-period characters. The "quantity produced for export: N"
--                     production statistic is blanked first, exactly as in `_by_notes`,
--                     so a sales figure can't become the cited evidence.
--   twin_sentence   : the formulaic "The same company made a <role> version as
--                     <Brand>'s '<Name>'." sentence — the twin tier's quote.
-- Both are PROPOSALS until `make verify-quotes` proves them verbatim against
-- pinexplore's ipdb_machines corpus. Never ship an extracted quote that hasn't passed.
CREATE OR REPLACE VIEW _export_evidence AS
  SELECT
    c.id,
    _abbrev_unguard(trim(regexp_extract(
      regexp_replace(_abbrev_guard(nn.note_norm), '(?i)quantity produced for export', '', 'g'),
      '([^.]*(for export|export to |export edition|export version|export model)[^.]*\.)',
      1))) AS export_sentence,
    _abbrev_unguard(trim(regexp_extract(_abbrev_guard(nn.note_norm), '([^.]*same company made [^.]*\.)', 1))) AS twin_sentence,
    -- The independent "Recel is the name used for export games." sentence. The twin
    -- sentence names the counterpart (so it carries `export_edition_of`) but only
    -- IMPLIES this model's own role; this one states it outright, which is what the
    -- `- {}` "built for export" row actually rests on. Present on 27 of 30 twins;
    -- `export_checks` already guarantees the two never contradict each other.
    _abbrev_unguard(trim(regexp_extract(_abbrev_guard(nn.note_norm),
      '([^.]*is the name used for (export|domestic) games[^.]*\.)', 1))) AS role_sentence
  FROM export_candidates c,
       LATERAL (SELECT regexp_replace(
         replace(replace(replace(replace(COALESCE(c.notes, ''), '“', '"'), '”', '"'),
                 '‘', ''''), '’', ''''),
         '\s+', ' ', 'g') AS note_norm) nn;

-- Is the export sentence a SELF-claim — this model built for export — rather than a
-- mention of export in some other role? The whitelist is deliberately narrow: the
-- same wording carries opposite meanings depending on the subject ("This is the
-- export version of Big Ben" vs "Eclipse uses the same sound PROM as the export
-- version of Black Hole"), and no amount of blacklisting recovers a subject the
-- regex can't see. So green requires a MATCH here, not merely the absence of a
-- disqualifier — a sentence that doesn't state the model's own role goes to review.
-- The gate is an OPENER whitelist, not a keyword search, because in this corpus the
-- export phrase is a floating participle: "<something> made for export to Italy"
-- says nothing about WHICH noun was exported. Compare
--   "This is the add-a-ball version of Segasa's 1975 'Big Ben' made for export to Italy."
--   "The playfield layout was used again on Gottlieb's 1972 'Space Orbit' made for
--    export to Italy."
-- Identical tails; the first model IS the export and the second is not. Only the
-- SUBJECT separates them, so green requires the sentence to open with a subject that
-- refers to the model itself ("This", "Game", "A version of", "Made for export", a
-- quoted title). Anything else — a person, another game, a component — is not
-- rejected as false, it is routed to review, where a human can read the note.
CREATE OR REPLACE MACRO _is_self_export_claim(s) AS (
  -- Case-insensitivity is SCOPED (see the note on `(?i)` further down): a blanket
  -- (?i) would make `[A-Z]` match lowercase and quietly void the two alternatives
  -- that depend on capitalization to identify a proper name.
  regexp_matches(COALESCE(s, ''),
    '^(?i:'
    || 'this|it |game |made |built |produced |manufactured '        -- "This game was...", "Made for export to France."
    || '|same game|conversion of|version of|export (?:version|model|edition) of'
    || '|an? [a-z0-9 -]{0,25}(?:version|game|model|edition)'        -- "A special version of...", "An add-a-ball version of..."
    || '|the [a-z]+ (?:game|machine|model|version)'                 -- "The prototype game ... was built for export"
    || ')')
  -- "'Harmony' and Gottlieb's 1967 'Troubadour' are versions of ..." — a quoted
  -- PROPER NAME opener, so the capital is the whole point.
  OR regexp_matches(COALESCE(s, ''), '^''[A-Z]')
  -- "<Name> is the export version of ..." — likewise anchored on a proper name.
  OR regexp_matches(COALESCE(s, ''),
       '^[A-Z][A-Za-z0-9 .''-]{0,25}(?i: (?:is|was) (?:an?|the) )[A-Za-z0-9 -]{0,20}(?i:export)')
);

-- The scored shortlist: every candidate with its emission KIND and its
-- DISQUALIFIER. reject_reason IS NULL is green; anything else is auditable in
-- `export_patch_rejected`. Kind picks which EVIDENCE the claim cites:
--   twin   the formulaic twin sentence — the deterministic tier. It alone yields an
--          `export_edition_of` target, parsed rather than guessed.
--   notes  a self-claiming export sentence -> `cite: ipdb:<id>` carrying it verbatim.
--   suffix the model's NAME ends in "(Country)". The evidence is the catalog's own
--          data, so this cites nothing and reasons in a `note:` instead — the same
--          call ../0172-bingo-game-format/gen.py makes for its struct rows.
-- Order matters: twin outranks notes (it is parsed, and its sentence is the one that
-- also names the counterpart), and notes outranks suffix (a quote beats an inference
-- from a name). reject_reason applies to the NOTES tier only — the other two rest on
-- structured data, and a model whose note fails the gate can still emit on `suffix`.
--
-- `by_opdb` is DELIBERATELY NOT A TIER. All 34 of its models are Brazilian, Spanish,
-- Italian or Japanese makers' local builds (Taito do Brasil, Electromatic, LTD,
-- Rowamet, Maresa), and 7 already carry a `copy` edge. OPDB's "Export edition" flag
-- is written from the ORIGINAL DESIGN's point of view — a foreign-market build of a
-- US game — which is the inverse of our maker-relative definition: Taito do Brasil
-- building Sultan in Brazil for Brazil is DOMESTIC (README.md, "Export is
-- maker-relative"). Emitting `- {}` for those would assert "built for export" of
-- models that were not. They stay a review bucket; the ones that are real exports
-- want a per-row source read, and most want a `copy` edge from the 0128 campaign
-- instead. `export_opdb_review` below is that worklist.
CREATE OR REPLACE VIEW _export_scored AS
  WITH ev AS (
    SELECT
      c.id, c.label, c.by_notes, c.by_suffix, c.by_opdb, c.by_twin, c.notes,
      m.slug, m.ipdb_id, m.opdb_id,
      e.export_sentence, e.twin_sentence, e.role_sentence
    FROM export_candidates c
    JOIN models m ON m.id = c.id
    JOIN _export_evidence e ON e.id = c.id
  ),
  scored AS (
    SELECT
      ev.*,
      CASE
        WHEN NOT ev.by_notes                                   THEN NULL
        WHEN ev.export_sentence = ''                            THEN 'no sentence extracted'
        WHEN length(ev.export_sentence) NOT BETWEEN 20 AND 240  THEN 'sentence out of bounds'
        WHEN ev.export_sentence LIKE '%' || chr(65533) || '%'   THEN 'mojibake'
        -- The non-period sentence bound truncates on an abbreviation ("the 1991 USA
        -- game 'A." — the note said "A.G. Football"), yielding a span that is verbatim
        -- but reads as a different, mangled claim. Two tells: a span that starts
        -- mid-word/mid-quote, or one that ends on a single-letter abbreviation.
        WHEN regexp_matches(ev.export_sentence, '^[a-z]|^[A-Za-z0-9.-]+''[ ,]|[^A-Za-z][A-Z]\.$')
          THEN 'truncated sentence'
        -- The subject IS self-referential but the export clause hangs off ANOTHER
        -- game named later in the sentence — a relative clause ("a near copy of
        -- 'Lucky Card' WHICH WAS a game made for export to Italy") or a comparison
        -- ("the same ... AS THE VERSION made for export to Italy, 'Royal Pair'").
        -- The exported model is real and named; it just isn't this one.
        WHEN regexp_matches(ev.export_sentence,
               '(?i)which (was|is)[^.]{0,40}export|as the [a-z]+ made for export|used again on'
               -- "A NEW VERSION OF THIS GAME featuring 'a smaller cabinet designed for
               -- export' was to be in production" — the export is an announced variant.
               || '|a new version of this game|was to be in production')
          THEN 'export attaches elsewhere'
        -- The subject is a COMPONENT, not the machine — artwork/schematic prose that
        -- happens to name an export (../0128-relationships/relationships.sql makes the
        -- same call for component-copies).
        WHEN regexp_matches(ev.export_sentence,
               '(?i)^the (playfield|backglass|back glass|artwork|art ?work|cabinet|schematic|score ?card|layout|sound)')
          THEN 'component subject'
        -- the note is on the ORIGINAL, describing the model that WAS exported
        -- Three shapes, all "the export is some OTHER model":
        --   "Also produced as ... 'Jackpot' made for export"     (names the export)
        --   "A solid state version for export to Spain IS Bally's 'Wall Street
        --    Special (Spain)'"                                   (predicate names it)
        --   "'Dimension', ITS EXPORT VERSION 'Galaxie', and ..."  (possessive names it)
        WHEN regexp_matches(ev.export_sentence,
               '(?i)also (produced|made|released|manufactured|sold)'
               || '|for export( to [A-Za-z ]+?)? is '
               || '|its export (version|model|edition)')
          THEN 'reverse-direction'
        -- The source doesn't assert the export of THIS model: it hedges, negates, or
        -- likens the model to exports rather than calling it one ("While its apron is
        -- similar to add-a-ball games made for export to Italy, ... he has never seen
        -- this game there" — a note that DENIES the export).
        WHEN regexp_matches(ev.export_sentence,
               '(?i)probabl|possibl|apparentl|appears to|seems to|may (be|have)|might'
               || '|likely|perhaps|reportedly|believed|thought to be|said to be|presumabl'
               || '|we do(n''t| not) know|typically|known to|never|similar to|^while '
               || '|near[- ]?copy|would make|tells us')
          THEN 'hedged'
        -- The sentence NAMES a destination the catalog can't resolve — a country that
        -- isn't seeded as a Location yet ("Made for export to Israel and Indonesia").
        -- Emitting the `- {}` unknown-market row here would be a lie of a specific
        -- kind: it asserts the destination is UNKNOWN when the source states it. Hold
        -- the row until the country exists (then it re-greens with no code change).
        WHEN len(_market_tokens(ev.export_sentence)) > 0
             AND NOT EXISTS (SELECT 1 FROM UNNEST(_market_tokens(ev.export_sentence)) AS t(token)
                             JOIN _country_lookup cl ON cl.token = t.token)
          THEN 'market names an unseeded country'
        WHEN NOT _is_self_export_claim(ev.export_sentence)      THEN 'not a self-claim'
      END AS notes_reject
    FROM ev
  )
  SELECT
    s.*,
    CASE
      WHEN s.by_twin                              THEN 'twin'
      WHEN s.by_notes AND s.notes_reject IS NULL  THEN 'notes'
      WHEN s.by_suffix                            THEN 'suffix'
    END AS kind
  FROM scored s;

-- The ORIGIN the cited sentence names, for the notes tier — the second source of a
-- parsed `export_edition_of`.
--
-- This is NOT the title-mate inference DataPatchAuthoring.md warns off. The rule there
-- is "a title-mate is a LEAD to verify against the source, not evidence"; here the
-- source itself names the original inside the very sentence the claim cites ("A version
-- of Gottlieb's 1969 'Mini Pool' made for export to Italy"). Parsing it is the same move
-- the twin tier makes, and the quote that ships with the row states the relationship.
--
-- Gated three ways, because a wrong FK is a worse error than a missing one:
--   an ORIGIN PHRASE must introduce it — "version of" / "conversion of". "Same game as"
--     is deliberately EXCLUDED: it marks a SIBLING, not an original. Troubadour's note
--     says "Same game as Gottlieb's 1967 'Harmony'", but Harmony's own note shows both
--     are versions of 'Melody' — reading that as an origin would invert a peer relation.
--   "version of THIS ... game" is excluded — a self-reference, naming no other model
--     (Bronco's "A special version of this 4-player Model 396 game").
--   the reference must resolve to EXACTLY ONE live model, and never to itself.
-- Anything ambiguous simply yields no FK; the row still emits its market row.
CREATE OR REPLACE VIEW _origin_ref AS
  WITH src AS (
    SELECT s.id, s.export_sentence AS sent
    FROM _export_scored s
    WHERE s.kind = 'notes'
      AND regexp_matches(s.export_sentence, '(?i)(version|conversion) of')
      AND NOT regexp_matches(s.export_sentence, '(?i)(version|conversion) of th(is|e same)')
      AND NOT regexp_matches(s.export_sentence, '(?i)same game as')
  ),
  -- Form A, the dominant one: "<Maker>'s <year> '<Name>'". Structured enough to
  -- resolve on all three parts, which is what disambiguates same-named games
  -- (Chicago Coin's 'Gun Smoke' vs the candidate of the same name).
  maker_ref AS (
    SELECT
      src.id,
      regexp_extract_all(src.sent, '([A-Z][A-Za-z0-9.&-]*(?: [A-Z][A-Za-z0-9.&-]*)*)''s? (?:([0-9]{4}) )?''([^'']+)''', 0) AS hits,
      regexp_extract(src.sent, '([A-Z][A-Za-z0-9.&-]*(?: [A-Z][A-Za-z0-9.&-]*)*)''s? (?:([0-9]{4}) )?''([^'']+)''', 1) AS maker,
      NULLIF(regexp_extract(src.sent, '([A-Z][A-Za-z0-9.&-]*(?: [A-Z][A-Za-z0-9.&-]*)*)''s? (?:([0-9]{4}) )?''([^'']+)''', 2), '') AS yr,
      regexp_extract(src.sent, '([A-Z][A-Za-z0-9.&-]*(?: [A-Z][A-Za-z0-9.&-]*)*)''s? (?:([0-9]{4}) )?''([^'']+)''', 3) AS nm
    FROM src
  ),
  -- Form B, the fallback: a quoted or bare name with no maker — "a version of
  -- `Palace Guard'", "A version of Paul Bunyan made for export". Resolvable only by
  -- name, so it demands a globally unique match below.
  plain_ref AS (
    SELECT
      src.id,
      COALESCE(
        NULLIF(regexp_extract(src.sent, '(?i:(?:version|conversion) of )[`''"]([A-Z][^`''"]+)[''"]', 1), ''),
        NULLIF(regexp_extract(src.sent, '(?i:(?:version|conversion) of )([A-Z][A-Za-z0-9 -]+?)(?i: (?:made )?for export)', 1), '')
      ) AS nm
    FROM src
    WHERE src.id NOT IN (SELECT id FROM maker_ref WHERE len(hits) = 1)
  ),
  -- Form A resolution: name + maker, preferring an exact year match. Requires the
  -- sentence to carry exactly ONE maker reference, so a two-game sentence abstains.
  -- A single match is taken outright; several same-named games by one maker are
  -- disambiguated ONLY when the note's year picks exactly one of them. Otherwise the
  -- row abstains rather than guessing between them.
  resolved_maker AS (
    SELECT
      r.id,
      list(m.slug ORDER BY (m.year IS NOT DISTINCT FROM TRY_CAST(r.yr AS BIGINT)) DESC, m.slug) AS slugs,
      count(*) AS n,
      count(*) FILTER (WHERE m.year IS NOT DISTINCT FROM TRY_CAST(r.yr AS BIGINT)) AS n_year
    FROM maker_ref r
    JOIN models m ON m.name = r.nm AND m.manufacturer_name = r.maker AND m.id <> r.id
    WHERE len(r.hits) = 1
    GROUP BY r.id
    HAVING count(*) = 1
        OR count(*) FILTER (WHERE m.year IS NOT DISTINCT FROM TRY_CAST(r.yr AS BIGINT)) = 1
  ),
  -- Form B resolution: name alone, and only when it is unambiguous catalog-wide.
  resolved_plain AS (
    SELECT r.id, list(m.slug) AS slugs
    FROM plain_ref r
    JOIN models m ON m.name = r.nm AND m.id <> r.id
    WHERE r.nm IS NOT NULL
    GROUP BY r.id
    HAVING count(*) = 1
  )
  SELECT id, slugs[1] AS origin_slug, 'maker-ref' AS how FROM resolved_maker
  UNION ALL
  SELECT id, slugs[1], 'name-only' FROM resolved_plain;

-- RECIPROCAL NOTES — the export edge stated from the OTHER end.
--
-- IPDB frequently records an export on the ORIGINAL's record rather than the export's:
-- Paul Bunyan's note says "The Italian version is Gottlieb's 1968 'Big Jack'.". That is
-- a second, INDEPENDENT statement of an edge this campaign already claims from Big
-- Jack's own note — the strongest corroboration available without a human read — and
-- `cite:` takes a LIST, so it rides the SAME entry (one ChangeSet, two sources) rather
-- than a second entry. It has to: DataPatches.md requires entries targeting one record
-- to assert DISJOINT claim keys, so a second entry re-asserting `export_edition_of`
-- would be a hard error, not a duplicate.
--
-- The parse binds the model reference DIRECTLY to an export-designating predicate,
-- which is what keeps it honest in a corpus full of near-misses:
--   "The replay version of this game is Gottlieb's 1973 'High Hand' and the Italian
--    version is Gottlieb's 1973 'Top Hand'."
-- Both halves have the same shape; only the second is an export. A sentence-level
-- keyword match would bind 'High Hand'. Requiring "<export predicate> is/was <ref>"
-- with nothing between them takes 'Top Hand' and leaves 'High Hand' alone.
--
-- `source_is_origin` is the DIRECTION flag, and it is deliberately conservative.
-- Usually the note's own model is the original, but not always:
--   "The Add-a-ball version of this game is Gottlieb's 1977 'Team One' WHICH WAS
--    exported to Italy as Gottlieb's 1977 'Kicker'."
-- Kicker's original is Team One, not the model whose note this is. A relative clause
-- ("which was") or a second model reference before the predicate re-anchors the
-- subject, so those rows carry the export fact but NOT a usable origin.
-- A NOTE ON `(?i)`: a BLANKET (?i) also makes `[A-Z]` match lowercase, silently
-- disabling every capitalization requirement in the pattern. That is not academic — it
-- made the maker capture read "player Williams" out of "a 4-player Williams' 1971
-- 'Jackpot'". Capitalization is load-bearing here (it marks a proper name, and a
-- country), so case-insensitivity is SCOPED to the literal words with `(?i:...)` while
-- `[A-Z]` stays case-sensitive. The same rule applies in `_origin_ref` above.

-- (`_maker_ref_pat()` is defined near the top, with the shared macros.)

-- Form 1 — "<export-designating subject> is/was <ref>". The predicate must DESIGNATE an
-- export, and the ref must follow it IMMEDIATELY: that is what picks 'Top Hand' and
-- leaves 'High Hand' alone in "The replay version of this game is Gottlieb's 1973 'High
-- Hand' and the Italian version is Gottlieb's 1973 'Top Hand'."
CREATE OR REPLACE MACRO _recip_predicate_pat() AS
  '(?i:(?:italian|spanish|french|german|portuguese|japanese|brazilian|belgian|british|american)[a-z -]* (?:version|export|model|edition)'
  || '|(?:version|model|edition)[a-z -]{0,25} for export(?: to [a-z ]+?)?'
  || '|version made for export(?: to [a-z ]+?)?)(?i: is | was )' || _maker_ref_pat();

-- Form 2 — "exported to <Country> as <ref>".
CREATE OR REPLACE MACRO _recip_exported_as_pat() AS
  '(?i:export(?:ed)? to )[A-Za-z ]+?(?i: as )' || _maker_ref_pat();

-- Form 3 — "Also produced as ... <ref> ... made for export".
CREATE OR REPLACE MACRO _recip_also_pat() AS
  '(?i:also (?:produced|released|made|manufactured))[^.]{0,40}?' || _maker_ref_pat()
  || '[^.]{0,30}?(?i:for export)';

-- MATERIALIZED (a TABLE, not a view) — same reason as `_twin` and `export_candidates`.
-- The three parse forms run nine backtracking-heavy regexes per sentence over the whole
-- corpus, and `export_patch_rows` references this four times while `export_summary`
-- reference-expands THAT a dozen more. As a view the parse re-runs on every one of
-- those and the summary takes minutes; as a table it is computed once at init.
-- Nothing is persisted (the database is :memory:) and it stays non-TEMP so the UI
-- can see it across connections.
CREATE OR REPLACE TABLE _reciprocal AS
  WITH norm AS (
    SELECT
      m.id AS source_id, m.slug AS source_slug, m.name AS source_name, m.ipdb_id AS source_ipdb_id,
      regexp_replace(
        replace(replace(replace(replace(COALESCE(m.ipdb_notes, ''), '“', '"'), '”', '"'),
                '‘', ''''), '’', ''''),
        '\s+', ' ', 'g') AS n
    FROM models m
    WHERE m.ipdb_id IS NOT NULL
  ),
  sents AS (
    SELECT norm.* EXCLUDE (n), _abbrev_unguard(trim(sent)) AS sent
    FROM norm, UNNEST(regexp_extract_all(_abbrev_guard(norm.n), '[^.]*\.', 0)) AS d(sent)
    WHERE sent ILIKE '%export%'
       OR regexp_matches(sent,
            '(?i:(italian|spanish|french|german|portuguese|japanese|brazilian|belgian|british|american)[a-z -]* version)')
  ),
  picked AS (
    SELECT
      s.*,
      CASE
        WHEN regexp_extract(s.sent, _recip_predicate_pat(), 3) <> ''   THEN 'predicate'
        WHEN regexp_extract(s.sent, _recip_exported_as_pat(), 3) <> '' THEN 'exported-as'
        WHEN regexp_extract(s.sent, _recip_also_pat(), 3) <> ''        THEN 'also-produced'
      END AS form,
      COALESCE(
        NULLIF(regexp_extract(s.sent, _recip_predicate_pat(), 1), ''),
        NULLIF(regexp_extract(s.sent, _recip_exported_as_pat(), 1), ''),
        NULLIF(regexp_extract(s.sent, _recip_also_pat(), 1), '')) AS maker,
      COALESCE(
        NULLIF(regexp_extract(s.sent, _recip_predicate_pat(), 2), ''),
        NULLIF(regexp_extract(s.sent, _recip_exported_as_pat(), 2), ''),
        NULLIF(regexp_extract(s.sent, _recip_also_pat(), 2), '')) AS yr,
      COALESCE(
        NULLIF(regexp_extract(s.sent, _recip_predicate_pat(), 3), ''),
        NULLIF(regexp_extract(s.sent, _recip_exported_as_pat(), 3), ''),
        NULLIF(regexp_extract(s.sent, _recip_also_pat(), 3), '')) AS nm,
      -- DIRECTION, deliberately conservative. Usually the note's own model is the
      -- original, but a relative clause re-anchors the subject to a model named earlier
      -- in the sentence: "The Add-a-ball version of this game is Gottlieb's 1977 'Team
      -- One' WHICH WAS exported to Italy as Gottlieb's 1977 'Kicker'." Kicker's original
      -- is Team One, not the model whose note this is. Such rows carry the export FACT
      -- but no usable origin.
      NOT regexp_matches(s.sent, '(?i:which (was|is|were|are))') AS source_is_origin,
      -- The nationality adjective, when the predicate is one ("a single-player SPANISH
      -- version is ..."). Needed because such a phrase only designates an EXPORT when
      -- the nationality differs from the target maker's own home country.
      regexp_extract(s.sent,
        '((?i:italian|spanish|french|german|portuguese|japanese|brazilian|belgian|british|american))[a-z -]* (?:version|export|model|edition)(?i: is | was )',
        1) AS adj
    FROM sents s
    -- a hedged or second-hand sentence states no flat fact
    WHERE NOT regexp_matches(s.sent,
            '(?i:sometimes|may actually|might|perhaps|probabl|possibl|considered to be|according to)')
  )
  SELECT
    k.source_id, k.source_slug, k.source_name, k.source_ipdb_id,
    t.id AS target_id, t.slug AS target_slug, t.label AS target_label,
    k.sent AS quote, k.form,
    -- An export edition and its original are built by the SAME maker; a different
    -- maker's build of the same design is a `copy`, not an export
    -- (DataPatchAuthoring.md). So a cross-maker note may still evidence the export
    -- FACT, but it cannot establish the ORIGIN. This is what stops Gottlieb's Italian
    -- 'Texas Ranger' being recorded as an export edition of Maresa's Spanish 'Dakota'.
    (k.source_is_origin AND sm.manufacturer_id IS NOT DISTINCT FROM t.manufacturer_id
       AND sm.manufacturer_id IS NOT NULL) AS source_is_origin
  FROM picked k
  JOIN models t  ON t.name = k.nm AND t.manufacturer_name = k.maker AND t.id <> k.source_id
  JOIN models sm ON sm.id = k.source_id
  WHERE k.form IS NOT NULL
    -- EXPORT IS MAKER-RELATIVE. "A single-player Spanish version is Maresa's 1972
    -- 'Dakota'" describes a SPANISH maker's home-market build — domestic, not an
    -- export, however export-shaped the sentence looks (README.md).
    AND NOT EXISTS (
      SELECT 1 FROM _country_lookup cl
      WHERE lower(cl.token) = lower(k.adj) AND cl.slug = t.country_slug)
  -- the reference must land on exactly ONE model; the year disambiguates same-named
  -- games by one maker, and where it cannot, the row abstains entirely.
  QUALIFY count(*) OVER (PARTITION BY k.source_id, k.sent) = 1
       OR (t.year IS NOT DISTINCT FROM TRY_CAST(k.yr AS BIGINT)
           AND count(*) FILTER (WHERE t.year IS NOT DISTINCT FROM TRY_CAST(k.yr AS BIGINT))
                 OVER (PARTITION BY k.source_id, k.sent) = 1);

-- The origin a reciprocal note establishes, when it establishes one UNAMBIGUOUSLY.
-- Requires `source_is_origin` (no relative clause re-anchoring the subject) and exactly
-- ONE distinct claimed origin: two different models each naming the same export means
-- the catalog has a duplicate or the notes disagree, and either way the honest FK is
-- none. That is not hypothetical — 'Kicker (Italy)' is claimed by both Chicago Coin
-- 'Kicker' records, and 'Top Hand' by both 'Capt. Card' and 'High Hand'.
CREATE OR REPLACE VIEW _recip_origin AS
  SELECT target_id, any_value(source_slug) AS origin_slug
  FROM _reciprocal
  WHERE source_is_origin
  GROUP BY target_id
  HAVING count(DISTINCT source_slug) = 1;

-- The rows gen.py emits, one per model. Two independent facts ride each row
-- (flipcommons' DataPatchAuthoring.md → Export editions and markets):
--
--   export_edition_of  the domestic original's slug, ONLY where a source names one and
--                      it resolves uniquely: the twin sentence, a notes-tier "version
--                      of <Maker>'s <year> '<Name>'", or a reciprocal note from the
--                      original's own record. Never inferred from a shared Title —
--                      the titlemate/orphan buckets stay a human worklist.
--   market_*           the ModelExportMarket shape. Exactly ONE of the three, so the
--                      "a null-location row must be the model's only row" convention
--                      — which ingest does NOT enforce — holds by construction:
--                        market_countries  non-empty -> `target_market_location` rows
--                        market_label      non-null  -> one `target_market_label` row
--                        neither                     -> one `- {}` unknown-market row
--
-- The market is parsed from the CITED SPAN, not the whole note, so the evidence each
-- row ships with actually supports the market it claims — except on a `suffix` row,
-- where the name itself is the evidence and supplies the country directly. That is
-- why `_market_tokens` is a macro: this is its second caller.
--
-- `recip_cites` carries the corroborating reciprocal statements. They ride the SAME
-- entry as a second `cite:` (DataPatches.md: a cite list attaches every citation to
-- every claim), never a second entry — entries targeting one record must assert
-- disjoint claim keys, so a second entry re-asserting `export_edition_of` is an error.
-- MATERIALIZED for the same reason: five review/summary consumers build on it.
CREATE OR REPLACE TABLE export_patch_rows AS
  WITH parsed AS (
    SELECT
      s.id, s.slug, s.label, s.ipdb_id, s.opdb_id, s.kind,
      CASE s.kind WHEN 'twin' THEN s.twin_sentence WHEN 'notes' THEN s.export_sentence END AS quote,
      -- twin tier only: the second cited span, joined by gen.py with a ' [...] '
      -- omission marker (verify_quotes checks each span independently).
      CASE WHEN s.kind = 'twin' THEN NULLIF(s.role_sentence, '') END AS role_quote,
      (SELECT list(d.dest) FROM _dest_suffix d WHERE d.id = s.id) AS suffix_markets,
      COALESCE((
        SELECT list_sort(list_distinct(list(cl.slug)))
        FROM UNNEST(_market_tokens(
               CASE s.kind WHEN 'twin' THEN s.twin_sentence ELSE s.export_sentence END)) AS t(token)
        JOIN _country_lookup cl ON cl.token = t.token
      ), []::VARCHAR[]) AS quoted_markets,
      (SELECT r.label FROM _region_alias r
        WHERE regexp_matches(COALESCE(s.export_sentence, ''), r.pattern) LIMIT 1) AS quoted_label,
      COALESCE(
        (SELECT d.slug FROM export_twin_pairs p
           JOIN models d ON d.id = p.domestic_model_id
          WHERE p.export_model_id = s.id),
        (SELECT o.origin_slug FROM _origin_ref o WHERE o.id = s.id)
      ) AS export_edition_of,
      CASE
        WHEN (SELECT d.slug FROM export_twin_pairs p JOIN models d ON d.id = p.domestic_model_id
               WHERE p.export_model_id = s.id) IS NOT NULL THEN 'twin'
        ELSE (SELECT o.how FROM _origin_ref o WHERE o.id = s.id)
      END AS origin_how,
      s.notes
    FROM _export_scored s
    WHERE s.kind IS NOT NULL
  ),
  -- Models the campaign would otherwise MISS entirely: no usable note of their own,
  -- but the original's record names them as its export. 'Western' is the worked
  -- example — its own note only hedges ("would make 'Western' the last 2-player game
  -- made for export"), while Lariat's states it flat.
  recip_only AS (
    SELECT
      m.id, m.slug, m.label, m.ipdb_id, m.opdb_id, 'reciprocal' AS kind,
      NULL::VARCHAR AS quote, NULL::VARCHAR AS role_quote,
      NULL::VARCHAR[] AS suffix_markets,
      COALESCE((
        SELECT list_sort(list_distinct(list(cl.slug)))
        FROM _reciprocal r2, UNNEST(_market_tokens(r2.quote)) AS t(token)
        JOIN _country_lookup cl ON cl.token = t.token
        WHERE r2.target_id = m.id
      ), []::VARCHAR[]) AS quoted_markets,
      NULL::VARCHAR AS quoted_label,
      (SELECT ro.origin_slug FROM _recip_origin ro WHERE ro.target_id = m.id) AS export_edition_of,
      CASE WHEN (SELECT ro.origin_slug FROM _recip_origin ro WHERE ro.target_id = m.id) IS NOT NULL
           THEN 'reciprocal' END AS origin_how,
      m.ipdb_notes AS notes
    FROM models m
    WHERE m.id IN (SELECT target_id FROM _reciprocal)
      AND m.id NOT IN (SELECT id FROM parsed)
  ),
  unioned AS (SELECT * FROM parsed UNION ALL SELECT * FROM recip_only),
  -- The FK is resolved in its OWN step because `recip_cites` below has to filter on it,
  -- and a SELECT cannot reference a column it is computing.
  resolved AS (
    SELECT
      b.* EXCLUDE (export_edition_of, origin_how),
      -- A reciprocal note can also supply the origin a row's own source never named.
      -- That is how 'Jackpot' gets Gold Rush back: its own note says only "Same game as
      -- ... 'Gold Rush' but made for export", which `_origin_ref` refuses (a sibling
      -- phrasing), while Gold Rush's note states the export outright.
      COALESCE(b.export_edition_of,
               (SELECT ro.origin_slug FROM _recip_origin ro WHERE ro.target_id = b.id)) AS export_edition_of,
      COALESCE(
        b.origin_how,
        CASE WHEN EXISTS (SELECT 1 FROM _recip_origin ro WHERE ro.target_id = b.id)
             THEN 'reciprocal' END) AS origin_how
    FROM unioned b
  )
  SELECT
    b.id, b.slug, b.label, b.ipdb_id, b.opdb_id, b.kind, b.quote, b.role_quote,
    b.export_edition_of, b.origin_how,
    CASE WHEN b.kind = 'suffix' THEN list_sort(list_distinct(b.suffix_markets))
         ELSE b.quoted_markets END AS market_countries,
    CASE WHEN b.kind = 'suffix' THEN NULL
         WHEN len(b.quoted_markets) > 0 THEN NULL
         ELSE b.quoted_label END AS market_label,
    -- Corroborating statements from the OTHER end, as extra cites on this same entry.
    -- A reciprocal source is a different model, so its ipdb_id can never collide with
    -- this row's own cite (DataPatches.md rejects a duplicated ref+locator+quote).
    --
    -- The ORIGIN MUST BE IDENTIFIED, by the ref or by the quote. An entry-level cite
    -- rides EVERY claim the entry asserts (DataPatches.md), so a corroborating cite has
    -- to support the FK too — not merely mention this model. Two shapes qualify:
    --
    --   the ref IS the origin   the classic reciprocal. The sentence's subject is
    --                           implicit ("The Add-a-ball version for export to Italy
    --                           is ... 'High Seas'") and the record it sits on supplies
    --                           it, so ref + quote together state the edge.
    --   the quote NAMES it      a third model's record describing the whole family:
    --                           "The Add-a-ball version of this game is ... 'Ship Ahoy'
    --                           which was exported to Italy as ... 'High Seas'." Not a
    --                           reciprocal at all, but it states this exact edge
    --                           explicitly, so it is real corroboration.
    --
    -- What both exclude is a cite whose subject is implicit AND is someone else. 'Ten-Up'
    -- was citing Pin-Up's note, "The Add-a-ball version for export to Italy is Gottlieb's
    -- 1973 'Ten-Up'" — implicit subject PIN-UP, never naming King Pin. Read alone it
    -- asserts a different original than this row claims (King Pin and Ten-Up are both
    -- 1973; Pin-Up is 1975 and cannot be the original). Corroboration from the wrong end
    -- is contradiction.
    --
    -- The name test is deliberately weak — plain containment of the origin's name. It is
    -- only ever used to ADMIT evidence for an FK already established by the gates above,
    -- never to derive one, so it does not need the name+maker+year discipline `_origin_ref`
    -- carries.
    --
    -- Where the row asserts no FK the statement corroborates the export FACT alone, and
    -- any record stating it flatly is admissible.
    COALESCE((
      SELECT list({'ipdb_id': r.source_ipdb_id, 'quote': r.quote} ORDER BY r.source_ipdb_id, r.quote)
      FROM _reciprocal r
      WHERE r.target_id = b.id
        AND r.source_ipdb_id IS DISTINCT FROM b.ipdb_id
        AND (b.export_edition_of IS NULL
             OR r.source_id = (SELECT o.id FROM models o WHERE o.slug = b.export_edition_of)
             OR r.quote LIKE '%' || (SELECT o.name FROM models o WHERE o.slug = b.export_edition_of) || '%')
    ), []) AS recip_cites,
    b.notes
  FROM resolved b
  ORDER BY b.slug;

-- The disqualified notes rows, with the reason — auditable, and a real review queue
-- in its own right: a 'not a self-claim' or 'reverse-direction' row is very often a
-- GENUINE export fact, just not the one a naive read would have authored (the
-- reverse-direction rows in particular name the model that IS the export).
CREATE OR REPLACE VIEW export_patch_rejected AS
  SELECT
    s.notes_reject AS reject_reason, s.id, s.slug, s.label, s.ipdb_id,
    s.kind AS fell_back_to, s.export_sentence, s.notes
  FROM _export_scored s
  WHERE s.notes_reject IS NOT NULL
  ORDER BY s.notes_reject, s.label;

-- The OPDB-flagged models, held OUT of the patch rows (see the note on `_export_scored`).
-- This is a worklist, not a queue of claims: judge each against its maker's home
-- country before treating the flag as an export fact, and check the 0128 campaign's
-- `relationship_review` first — for most of these the honest edge is `copy`, not
-- `export_edition_of`.
--   maker_home       the maker's country. Equal to the plausible destination -> domestic.
--   rel_types        typed edges the model already carries ([copy] -> almost certainly
--                    a local licensed build, not an export)
--   also_by_notes    the note independently mentions export -> the stronger lead
CREATE OR REPLACE VIEW export_opdb_review AS
  SELECT
    c.id, c.label, c.manufacturer_name, c.maker_home_country AS maker_home,
    l.rel_types, l.has_variant_of,
    c.by_notes AS also_by_notes,
    (SELECT s.notes_reject FROM _export_scored s WHERE s.id = c.id) AS notes_reject,
    c.notes
  FROM export_candidates c
  JOIN export_candidate_lineage l ON l.id = c.id
  WHERE c.by_opdb
    AND NOT EXISTS (SELECT 1 FROM export_patch_rows r WHERE r.id = c.id)
  ORDER BY c.manufacturer_name, c.label;

-- ── NAME CLUSTERS: the catalog-wide grain ──────────────────────────────────
-- Everything above this line is rooted in `export_candidates` — a model is visible
-- only if a detector fired on its free text, its name suffix or an OPDB flag. That is
-- the right root for authoring a claim and the wrong one for ASKING A QUESTION about
-- the corpus, because a same-named pair where NEITHER side has usable prose is
-- structurally invisible to every view above: no detector fires, so no candidate, so no
-- namesake row. 'Cavalier' (Recel 1979) / 'Cavalier' (Petaco 1979) is only in
-- `export_namesake_review` because IPDB happened to write a twin sentence about it.
--
-- These views drop that root and cluster the WHOLE live catalog by name: 1,106 clusters
-- covering 3,087 models, 930 of them split across more than one Title. That is far too
-- many to read, which is what the tiering is for — `pair_state` retires the settled
-- pairs and `lead` sorts the rest by what the pair is evidence FOR.
--
-- Clustering is on `name_key` (one trailing parenthetical stripped), the same key the
-- namesake view uses, so 'On Beam (Italy)' lands with 'On Beam'. `name_match` records
-- whether a pair needed the strip, because the strip also collapses genuinely different
-- games: A. M. Amusement's 'Forward Pass (Junior)' and 'Forward Pass (Marvel)' are two
-- machines, not one. Where that distinction is load-bearing the view below uses
-- `name_norm` instead and says so.
--
-- PLACEHOLDER NAMES are excluded from the whole grain. 37 live models are named
-- 'Unknown', or 'Unknown ("Three Bell")' where a cabinet marking is all anyone has.
-- That is the ABSENCE of a name, and `name_key` — which strips the parenthetical —
-- collapses all 37 into a single cluster spanning 12 makers and 1889-1984, which then
-- produced 579 pairs of pure noise, more than every real lead in this file combined.
-- Two models being equally un-named is not a shared name.
CREATE OR REPLACE MACRO _is_real_name(nm) AS
  name_key(nm) <> '' AND NOT regexp_matches(name_norm(nm), '^unknown');

-- PAIRED BRANDS — two maker names that are one operation, derived rather than declared.
--
-- The Spanish makers ran paired brands, one domestic and one export: Recel/Petaco,
-- Interflip/Recreativos Franco. This campaign found those pairs only through IPDB's
-- formulaic twin sentence (`_by_twin`), and everything downstream of that discovery
-- then had to be told, tier by tier, that cross-maker does NOT mean `copy` here.
--
-- The catalog cannot answer it structurally, and `corporate_entity_slug` — the obvious
-- place to look — is the wrong LEVEL, not merely unpopulated. DomainModel.md declares
-- `Manufacturer ||--o{ CorporateEntity : incarnations`: a corporate entity is one legal
-- incarnation OF a maker, so it sits BELOW the brand and partitions it across eras.
-- Bally's 762 models split into three (Bally Manufacturing 1932-82, Bally Midway
-- 1983-88, Midway/WMS 1988-99); Gottlieb and Williams span four each.
--
-- So corporate entity divides one brand over time — it can never group two brands into
-- one operation, and no level above Manufacturer exists to do so. That is why the
-- paired-brand relationship has to be inferred from name-collision statistics here
-- rather than read off a foreign key.
--
-- What DOES separate a paired brand from two unrelated makers is the ratio of
-- CONTEMPORANEOUS shared names to shared names. Bally and Gottlieb share 64 model names
-- and exactly ONE of them within a year — generic nouns, independently reused over four
-- decades. Petaco and Recel share 30 and 22 are within a year, because they are the same
-- games shipped under two labels in the same season. The absolute count alone would rank
-- Bally/Gottlieb first; it is the ratio that inverts them.
--
-- `same_home` splits the two phenomena the ratio finds, and the split is the whole
-- payoff:
--   same home country   one operation, two labels -> `export_edition_of` (Recel/Petaco)
--   different home      a licensed or unlicensed foreign build -> `copy`, the 0128
--                       campaign's edge (Segasa/Williams, Bally/Bally Wulff, Maresa/
--                       Gottlieb). NEVER an export edition, per the maker-relative rule.
--
-- Purely derived — no maker names are hardcoded anywhere in this file. A pair that falls
-- below threshold silently disappears, which is exactly what the anchor checks below
-- exist to catch for the pairs this campaign depends on.
--
-- MATERIALIZED: read by two review views, the summary and the checks.
CREATE OR REPLACE TABLE _paired_brand AS
  WITH nm AS (
    SELECT id, name_key(name) AS k, manufacturer_id AS mfr, manufacturer_name AS mfr_name,
           year, country_slug AS home
    FROM models
    WHERE _is_real_name(name) AND manufacturer_id IS NOT NULL
  ),
  pairs AS (
    SELECT
      a.mfr AS a_id, a.mfr_name AS a_maker, a.home AS a_home,
      b.mfr AS b_id, b.mfr_name AS b_maker, b.home AS b_home,
      count(*) AS n_shared,
      -- Contemporaneous: both sides dated and within a year. Undated models are NOT
      -- counted as close — the modern European bingo cohort is entirely undated, and
      -- treating "unknown" as "same season" would manufacture pairs out of nothing.
      count(*) FILTER (
        WHERE a.year IS NOT NULL AND b.year IS NOT NULL AND abs(a.year - b.year) <= 1
      ) AS n_close,
      -- How much of the cohort is already worked, so a reviewer can see at a glance
      -- whether a pair is a finished job or an untouched one. Counted over the CLOSE
      -- pairs, not all shared names: `n_close - n_close_edged` is then a real remainder.
      -- (Counting over n_shared made it negative — Interflip/Recreativos Franco carries
      -- 4 edges of which only 3 are contemporaneous.)
      count(*) FILTER (
        WHERE a.year IS NOT NULL AND b.year IS NOT NULL AND abs(a.year - b.year) <= 1
          AND EXISTS (SELECT 1 FROM model_edges_bidir e
                       WHERE e.model_id = a.id AND e.target_id = b.id)
      ) AS n_close_edged,
      count(*) FILTER (
        WHERE EXISTS (SELECT 1 FROM model_edges_bidir e
                       WHERE e.model_id = a.id AND e.target_id = b.id)
      ) AS n_edged,
      -- WHAT the cohort's existing edges SAY. This is what stops `same_home` being read
      -- as "export edition", which it is not: Recel/Petaco is one Spanish operation
      -- selling a domestic and an export label, but Ace Novelty / Colonial Specialties
      -- (both USA, both 1932, five shared names) is a domestic rebadge with no export
      -- in it at all. Rather than guess, the cohort is calibrated on the edges a human
      -- has already authored inside it — so an unworked pair inherits the verdict its
      -- own cohort earned, and a cohort nobody has judged inherits nothing.
      count(*) FILTER (
        WHERE EXISTS (SELECT 1 FROM model_edges_bidir e
                       WHERE e.model_id = a.id AND e.target_id = b.id
                         AND e.relationship_type = 'export_edition_of')) AS n_export_edges,
      count(*) FILTER (
        WHERE EXISTS (SELECT 1 FROM model_edges_bidir e
                       WHERE e.model_id = a.id AND e.target_id = b.id
                         AND e.relationship_type = 'copy')) AS n_copy_edges
    FROM nm a
    JOIN nm b ON b.k = a.k AND b.mfr > a.mfr
    GROUP BY ALL
  )
  SELECT
    *,
    (a_home IS NOT DISTINCT FROM b_home AND a_home IS NOT NULL) AS same_home,
    round(n_close::DOUBLE / n_shared, 2) AS close_ratio,
    CASE WHEN a_home IS NOT DISTINCT FROM b_home AND a_home IS NOT NULL
         THEN 'same-home partner'     -- one market: export label, rebadge or duplicate
         ELSE 'cross-border partner'  -- a build across a border -> copy (0128)
    END AS partner_kind,
    -- The cohort's own verdict, or NULL when nobody has judged it yet. NULL is the
    -- honest answer and the lead tiers below treat it as one: an unjudged cohort gets a
    -- review lead, never an export claim.
    CASE WHEN n_export_edges > 0 AND n_export_edges >= n_copy_edges THEN 'export_edition_of'
         WHEN n_copy_edges > 0                                     THEN 'copy'
    END AS cohort_edge
  FROM pairs
  -- Both arms are needed. The count alone admits Bally/Genco (3 close of 28 shared);
  -- the ratio alone admits any maker pair that shares two names and both are dated the
  -- same year, which is coincidence at n=2.
  WHERE n_close >= 3 AND n_close::DOUBLE / n_shared >= 0.4;

-- The derived partner table, for reading. `n_unworked` is the worklist signal — the
-- contemporaneous same-named pairs inside one operation that carry no edge yet — and
-- `cohort_edge` says what the pairs someone already judged in that cohort turned out
-- to be. A cohort with n_unworked high and cohort_edge NULL has never been opened.
CREATE OR REPLACE VIEW export_paired_brands AS
  SELECT a_maker, b_maker, a_home, b_home, same_home, partner_kind, cohort_edge,
         n_shared, n_close, close_ratio, n_edged, n_export_edges, n_copy_edges,
         (n_close - n_close_edged) AS n_unworked
  FROM _paired_brand
  ORDER BY n_unworked DESC, n_close DESC;

-- One row per same-name CLUSTER — the orientation view. Read this to find a family
-- worth opening, then `export_cluster_pairs` for the decisions inside it.
--
-- `cluster_state` is the headline, and it keeps the campaign's two decisions apart
-- exactly as `export_namesake_review` does: an edge is a claim about what was copied,
-- a Title is an editorial placement, and a cluster can be finished on one axis and
-- untouched on the other. The 'edges complete, Titles split' state is the one that
-- looks done in a patch diff and is not.
CREATE OR REPLACE VIEW export_name_cluster AS
  WITH members AS (
    SELECT name_key(name) AS name_key, id, name, manufacturer_name, title_id, year
    FROM models WHERE _is_real_name(name)
  ),
  agg AS (
    SELECT
      name_key,
      count(*)                                  AS n_models,
      count(DISTINCT title_id)                  AS n_titles,
      count(DISTINCT manufacturer_name)         AS n_makers,
      min(year)                                 AS year_min,
      max(year)                                 AS year_max,
      list_sort(list_distinct(list(manufacturer_name))) AS makers
    FROM members GROUP BY name_key
  ),
  edges AS (
    SELECT a.name_key,
           count(*) AS n_pairs,
           count(*) FILTER (
             WHERE EXISTS (SELECT 1 FROM model_edges_bidir e
                            WHERE e.model_id = a.id AND e.target_id = b.id)) AS n_pairs_edged
    FROM members a JOIN members b ON b.name_key = a.name_key AND b.id > a.id
    GROUP BY a.name_key
  )
  SELECT
    g.name_key,
    (SELECT name FROM members WHERE name_key = g.name_key LIMIT 1) AS display_name,
    g.n_models, g.n_titles, g.n_makers, g.makers, g.year_min, g.year_max,
    e.n_pairs, e.n_pairs_edged,
    (e.n_pairs - e.n_pairs_edged) AS n_pairs_unedged,
    EXISTS (SELECT 1 FROM _paired_brand p
             WHERE list_contains(g.makers, p.a_maker) AND list_contains(g.makers, p.b_maker)
        ) AS has_paired_brand,
    CASE
      WHEN e.n_pairs_edged = e.n_pairs AND g.n_titles = 1 THEN 'settled'
      WHEN e.n_pairs_edged = e.n_pairs                    THEN 'edges complete, Titles split'
      WHEN e.n_pairs_edged > 0        AND g.n_titles = 1  THEN 'partly edged, one Title'
      WHEN e.n_pairs_edged > 0                            THEN 'partly edged, Titles split'
      WHEN g.n_titles = 1                                 THEN 'no edges, one Title'
      ELSE                                                     'untouched'
    END AS cluster_state
  FROM agg g JOIN edges e USING (name_key)
  WHERE g.n_models > 1
  ORDER BY has_paired_brand DESC, n_pairs_unedged DESC, g.n_models DESC;

-- The pair grain inside a cluster — 4,476 unordered pairs catalog-wide, one per
-- (model, same-named model). This is the worklist; filter it by `lead`.
--
-- `a` is the EARLIER side (its own year, else its maker's era start), because in a
-- lineage pair the older model is usually the original. That is an ordering convenience
-- for reading, NOT a claim: the direction of an `export_edition_of` still comes from a
-- source, never from which row sorted first.
--
-- The gap falls back to the maker's era when a model is undated, exactly as
-- `export_namesake_review` does, and `gap_basis` records which measurement was used —
-- a model's own year is evidence, its maker's era is an inference from its siblings.
CREATE OR REPLACE VIEW export_cluster_pairs AS
  -- GENERIC NAMES — a name so many unrelated makers reached for that sharing it says
  -- nothing. 'Baseball' is 19 models by 16 makers across 1931-1970; 'Circus' is 16 by
  -- 12 across 1932-1980. Measured, not listed: many makers AND a long span, which is
  -- what separates a shared noun from a shared game. Recel/Petaco's 'Cavalier' is two
  -- makers in one year and is untouched by this.
  WITH generic AS (
    SELECT name_key(name) AS name_key
    FROM models WHERE _is_real_name(name)
    GROUP BY 1
    HAVING count(DISTINCT manufacturer_id) >= 6 AND (max(year) - min(year)) >= 20
  ),
  mm AS (
    SELECT m.id, m.slug, m.name, m.label, m.title_id, m.title_slug, m.title_size,
           m.manufacturer_id, m.manufacturer_name, m.year, m.game_format_slug,
           m.country_slug AS maker_home, name_key(m.name) AS name_key,
           COALESCE(m.year, e.era_start) AS lo, COALESCE(m.year, e.era_end) AS hi
    FROM models m
    LEFT JOIN _maker_era e ON e.manufacturer_id = m.manufacturer_id
    WHERE _is_real_name(m.name)
  ),
  -- Orientation is decided on ids alone and the columns are joined back afterwards, so
  -- the pair is built once and every column below reads from a plain `mm` row.
  oriented AS (
    SELECT
      CASE WHEN x_first THEN xid ELSE yid END AS a_id,
      CASE WHEN x_first THEN yid ELSE xid END AS b_id
    FROM (
      SELECT x.id AS xid, y.id AS yid,
             (COALESCE(x.year, x.lo, 9999) <= COALESCE(y.year, y.lo, 9999)) AS x_first
      FROM mm x JOIN mm y ON y.name_key = x.name_key AND y.id > x.id
    )
  ),
  p AS (
    SELECT
      a.name_key,
      a.id AS a_id, a.slug AS a_slug, a.name AS a_name, a.label AS a_label,
      a.title_id AS a_title_id, a.title_slug AS a_title, a.title_size AS a_title_size,
      a.manufacturer_id AS a_mfr, a.manufacturer_name AS a_maker,
      a.maker_home AS a_maker_home, a.year AS a_year,
      a.game_format_slug AS a_fmt, a.lo AS a_lo, a.hi AS a_hi,
      b.id AS b_id, b.slug AS b_slug, b.name AS b_name, b.label AS b_label,
      b.title_id AS b_title_id, b.title_slug AS b_title, b.title_size AS b_title_size,
      b.manufacturer_id AS b_mfr, b.manufacturer_name AS b_maker,
      b.maker_home AS b_maker_home, b.year AS b_year,
      b.game_format_slug AS b_fmt, b.lo AS b_lo, b.hi AS b_hi,
      -- The edge joining exactly this pair, in either direction, as STATED. A pair can
      -- legitimately carry more than one type, so this is a list, not a scalar.
      (SELECT list_sort(list_distinct(list(e.relationship_type)))
         FROM model_edges_bidir e
        WHERE e.model_id = a.id AND e.target_id = b.id) AS edge_types,
      -- Only ever SEPARATES, per the note on `_bingo_subgenre`: both sides must carry
      -- markers and share none. An absent marker set is unknown, not different.
      (ca.marks IS NOT NULL AND cb.marks IS NOT NULL
         AND len(list_intersect(ca.marks, cb.marks)) = 0) AS subgenre_differs,
      (SELECT pb.partner_kind FROM _paired_brand pb
        WHERE (pb.a_id = a.manufacturer_id AND pb.b_id = b.manufacturer_id)
           OR (pb.a_id = b.manufacturer_id AND pb.b_id = a.manufacturer_id)) AS partner_kind,
      (SELECT pb.cohort_edge FROM _paired_brand pb
        WHERE (pb.a_id = a.manufacturer_id AND pb.b_id = b.manufacturer_id)
           OR (pb.a_id = b.manufacturer_id AND pb.b_id = a.manufacturer_id)) AS cohort_edge
    FROM oriented o
    JOIN mm a ON a.id = o.a_id
    JOIN mm b ON b.id = o.b_id
    LEFT JOIN _bingo_subgenre ca ON ca.model_id = a.id
    LEFT JOIN _bingo_subgenre cb ON cb.model_id = b.id
  ),
  scored AS (
    SELECT
      p.*,
      (p.a_mfr = p.b_mfr) AS same_maker,
      (p.a_fmt IS NOT DISTINCT FROM p.b_fmt AND NOT p.subgenre_differs) AS same_format,
      (p.a_title_id = p.b_title_id) AS same_title,
      (p.a_name = p.b_name) AS exact_name,
      CASE WHEN p.a_year IS NOT NULL AND p.b_year IS NOT NULL
           THEN abs(p.a_year - p.b_year) END AS year_gap,
      _span_gap(p.a_lo, p.a_hi, p.b_lo, p.b_hi) AS era_gap,
      (p.partner_kind = 'same-home partner') AS same_home_partner,
      (p.partner_kind = 'cross-border partner') AS foreign_partner,
      EXISTS (SELECT 1 FROM generic g WHERE g.name_key = p.name_key) AS generic_name,
      len(COALESCE(p.edge_types, [])) > 0 AS has_edge
    FROM p
  )
  SELECT
    s.name_key,
    s.a_slug, s.a_label AS a, s.a_title,
    s.b_slug, s.b_label AS b, s.b_title,
    CASE WHEN s.exact_name THEN 'exact' ELSE 'suffix-stripped' END AS name_match,
    s.same_maker, s.same_format, s.same_title, s.partner_kind, s.cohort_edge, s.generic_name,
    s.year_gap, s.era_gap,
    CASE WHEN s.year_gap IS NOT NULL THEN 'model years'
         WHEN s.era_gap IS NOT NULL  THEN 'maker era'
         ELSE 'unknown' END AS gap_basis,
    s.edge_types,
    -- pair_state — is there anything LEFT to do? This is the column that makes a
    -- catalog-wide view readable: it retires the ~1,900 pairs already joined and
    -- co-titled, leaving the two open shapes plus the unjudged remainder.
    CASE
      WHEN s.has_edge AND s.same_title       THEN 'settled'
      WHEN s.has_edge                        THEN 'title split'   -- edge done, Title not
      WHEN s.same_title                      THEN 'edge missing'  -- co-titled, unjoined
      ELSE                                        'open'
    END AS pair_state,
    -- lead — what the pair is EVIDENCE FOR, before anyone reads a source. Same contract
    -- as `export_namesake_review.lead`: every tier still wants the note read before it
    -- becomes a claim. The paired-brand tiers are the ones this view exists to add.
    CASE
      WHEN s.has_edge                                        THEN 'already related'
      -- Same maker, same name, same year, same Title, no edge: two records of one
      -- machine. Requires an EXACT name — the parenthetical strip collapses
      -- 'Forward Pass (Junior)' onto '(Marvel)', which are two different games.
      WHEN s.same_maker AND s.exact_name AND s.same_title
           AND s.a_year IS NOT DISTINCT FROM s.b_year        THEN 'duplicate record?'
      -- THE NEW TIERS. Two makers of one operation shipping the same game in the same
      -- season — the shape this campaign found only through IPDB's twin sentence, now
      -- reached from structure. What the pair IS comes from the cohort's own judged
      -- edges, never from `same_home` alone: Recel/Petaco is an export label
      -- (cohort_edge = export_edition_of), Ace Novelty / Colonial Specialties is a 1932
      -- domestic rebadge with no export in it. Direction still comes from a source.
      WHEN s.same_home_partner AND s.same_format
           AND COALESCE(s.year_gap, s.era_gap, 0) <= 2
           AND s.cohort_edge = 'export_edition_of'            THEN 'export edition (paired brand)'
      -- Same operation, same season, but nobody has judged this cohort yet — a real
      -- lead and explicitly NOT an export claim. Read a source before it becomes one.
      WHEN s.same_home_partner AND s.same_format
           AND COALESCE(s.year_gap, s.era_gap, 0) <= 2        THEN 'same-home partner, unjudged cohort'
      WHEN s.same_maker AND s.same_format
           AND COALESCE(s.year_gap, s.era_gap, 0) <= 2        THEN 'same maker, contemporaneous'
      -- A build across a border is a `copy` for 0128, never an export edition.
      WHEN s.foreign_partner AND s.same_format
           AND COALESCE(s.year_gap, s.era_gap, 0) <= 5        THEN 'foreign build (copy)'
      -- Below the tiers that carry a structural reason to connect the pair (one
      -- operation, one maker, one border crossing), a generic name is the ONLY thing
      -- left, and it is not evidence. Placed here, not higher, so it can never demote a
      -- partner or same-maker pair: 'Circus' is generic, but Recel's and Petaco's
      -- 'Cavalier' would be too if the tier order were wrong.
      WHEN s.generic_name                                    THEN 'likely coincidence (generic name)'
      WHEN s.same_format
           AND COALESCE(s.year_gap, s.era_gap, 0) <= 5       THEN 'cross-maker, contemporaneous'
      WHEN s.subgenre_differs                                THEN 'likely coincidence (bingo sub-genre differs)'
      WHEN COALESCE(s.year_gap, s.era_gap) >= 16             THEN 'likely coincidence (years apart)'
      WHEN NOT s.same_format                                 THEN 'likely coincidence (format differs)'
      ELSE                                                        'needs a source read'
    END AS lead,
    s.a_maker, s.b_maker, s.a_maker_home, s.b_maker_home,
    s.a_title_size, s.b_title_size, s.a_id, s.b_id
  FROM scored s
  ORDER BY s.name_key, s.a_slug;

-- THE MERGE BACKLOG — pairs this project has ALREADY joined with an edge and left
-- sitting in two Titles. README.md quoted this as a number; it is a worklist.
--
-- Nothing here needs research: the edge is the claim that the two are one game, so the
-- Title split is a placement the edge already decided. The work is the two-patch merge
-- (re-home + reslug, then delete the emptied Title) described above `_merge_pair`.
-- `both_alone_in_title` marks the simple case where the doomed Title holds only the
-- mover; where it does not, the other members need a decision of their own first.
CREATE OR REPLACE VIEW export_merge_backlog AS
  SELECT
    p.name_key, p.a, p.a_slug, p.a_title, p.b, p.b_slug, p.b_title,
    p.edge_types, p.a_maker, p.b_maker, p.partner_kind,
    (p.a_title_size = 1 AND p.b_title_size = 1) AS both_alone_in_title,
    p.a_title_size, p.b_title_size
  FROM export_cluster_pairs p
  WHERE p.pair_state = 'title split'
  ORDER BY list_contains(p.edge_types, 'export_edition_of') DESC, p.name_key;

-- DUPLICATE RECORDS — same maker, same EXACT name, same year, same Title, no edge.
--
-- Not an export finding, and deliberately kept as its own view rather than folded into
-- a lead: it is a data-quality signal that turned up while clustering, and it BLOCKS
-- export work when it lands on a target. 'Kicker (Italy)' cites "Chicago Coin's 1966
-- 'Kicker'" and abstains on its FK because the catalog holds two of those; that pair
-- is a row here. Same for Recel's two 1975 'Criterium 75' records.
--
-- `name_norm` matching, not `name_key`: the parenthetical is the DISAMBIGUATOR in this
-- population, and stripping it would report A. M. Amusement's 'Forward Pass (Junior)'
-- and 'Forward Pass (Marvel)' — two 1934 machines, correctly distinct — as duplicates.
CREATE OR REPLACE VIEW export_duplicate_smell AS
  SELECT
    a.slug AS a_slug, a.label AS a, b.slug AS b_slug, b.label AS b,
    a.manufacturer_name AS maker, a.year, a.title_slug AS title,
    a.ipdb_id AS a_ipdb_id, b.ipdb_id AS b_ipdb_id,
    (a.ipdb_id IS NOT DISTINCT FROM b.ipdb_id) AS same_ipdb_id,
    -- Blocks an export FK: a same-named target this campaign cannot resolve uniquely.
    EXISTS (SELECT 1 FROM export_candidates c WHERE c.id IN (a.id, b.id)) AS touches_a_candidate
  FROM models a
  JOIN models b
    ON name_norm(b.name) = name_norm(a.name)
   AND b.id > a.id
   AND b.manufacturer_id = a.manufacturer_id
   AND b.title_id = a.title_id
   AND b.year IS NOT DISTINCT FROM a.year
  WHERE _is_real_name(a.name)
    AND NOT EXISTS (SELECT 1 FROM model_edges_bidir e
                     WHERE e.model_id = a.id AND e.target_id = b.id)
  ORDER BY touches_a_candidate DESC, maker, a.name;

-- BARE NUMERIC SLUGS — a slug that admits the catalog could not tell two records apart.
--
-- `alaska-2` says only "the second thing called Alaska". It is a placeholder minted at
-- seed time because a name collided, and it survives long after the catalog learned WHY
-- the two differ. Where the reason is known the slug should carry it, and the catalog
-- already uses that convention: `hula-hula-italy`, `big-ben-segasa-italy`,
-- `harley-davidson-bally`. So a bare suffix is not cosmetic — it is unfinished
-- disambiguation, and this campaign is exactly the work that supplies the missing fact.
--
-- DETECTING it needs care, because a trailing number is often the NAME:
--   black-magic-4   'Black Magic 4'   the 4 IS the game -> legitimate, leave alone
--   black-magic-2   'Black Magic'     Petaco's build     -> bare placeholder
--   criterium-2000  'Criterium 2000'  legitimate         criterium-75-2  bare
-- The test is structural rather than a re-implementation of Django's slugify (which
-- differs on apostrophes and '&', so reconstructing the slug from the name mis-sorts
-- ~440 rows): the slug's trailing number must not also end the name. 1,489 live models
-- are bare placeholders; 159 trailing numbers are genuinely part of the name.
CREATE OR REPLACE TABLE _bare_slug AS
  SELECT
    m.id, m.slug, m.name, m.label, m.title_slug, m.year,
    m.manufacturer_id, m.manufacturer_name, m.manufacturer_slug, m.country_slug,
    regexp_replace(m.slug, '-[0-9]+$', '') AS base_slug
  FROM models m
  WHERE regexp_matches(m.slug, '-[0-9]+$')
    AND NOT regexp_matches(name_norm(m.name), regexp_extract(m.slug, '-([0-9]+)$', 1) || '$')
    -- ...and the trailing number must not be the model's own YEAR, which is a
    -- disambiguator ALREADY APPLIED rather than a placeholder. `big-ben-williams-1954`
    -- and `big-ben-williams-1975` are exactly the shape this view wants the catalog to
    -- reach; without this they were reported as deficits and proposed renames to the
    -- slugs they already hold.
    AND regexp_extract(m.slug, '-([0-9]+)$', 1) IS DISTINCT FROM m.year::VARCHAR;

-- What the slug SHOULD say, proposed from the fact that actually separates the record
-- from the others sharing its base. The order is the user-facing rule:
--   1. an export edition with ONE known destination  -> the country   (hula-hula-italy)
--   2. a sibling by a different maker                -> the maker     (harley-davidson-bally)
--   3. same maker, different year                    -> the year
--   4. nothing distinguishes them                    -> no proposal
--
-- THIS VIEW COMPOSES SLUGS; IT NEVER MINTS THEM. Every proposal is an existing slug
-- (`base_slug`, `manufacturer_slug`, a country slug) or an integer year, joined by a
-- hyphen — so the result is slug-safe by construction and idempotent under the real
-- slugifier. Turning free TEXT into a slug is a different operation and does not belong
-- in SQL: the catalog's slugs were minted client-side by standalone Python calling
-- Django's `slugify`, whose NFKD + ascii-ignore pass is Unicode-table-driven and has no
-- honest DuckDB equivalent.
--
-- That is not a theoretical boundary. A `name parenthetical` basis lived here briefly,
-- slugifying the trailing '(…)' with name_norm + replace(' ','-'), and it produced
-- 'target-machine-type-ターケットマシン-タイフ１' — non-ASCII, AND with the dakuten eaten by
-- strip_accents (ゲ->ケ, プ->フ), which is the exact misuse name_norm's own comment warns
-- against. It also emitted 'forward-pass-junior-junior', because the base slug already
-- carried the parenthetical. The raw parenthetical survives as `name_paren_raw`: it IS
-- a real distinguisher and often the best one, so a reviewer can mint 'alaska-em'
-- properly on the authoring side rather than have this file guess at it.
--
-- Tier 4 is the honest outcome, not a gap to paper over. Two records with the same name,
-- maker AND year are not two machines needing better slugs — they are the
-- `export_duplicate_smell` population, and the fix is a merge, not a rename.
--
-- A proposal is only offered when it actually WORKS: `proposal_resolves` requires that
-- no other sibling would land on the same slug, and `proposed_slug_free` that no live
-- model already holds it. Renaming `alaska-2` to a slug another model owns trades a
-- vague slug for a broken one.
CREATE OR REPLACE VIEW export_slug_deficit AS
  -- THE FAMILY: every live model whose slug is the base, or the base plus a numeric
  -- suffix. Membership is matched AGAINST the base, never by stripping digits off each
  -- candidate — 'criterium-80' strips to 'criterium', so a computed-base join silently
  -- dropped the very sibling that makes 'criterium-80-2' ambiguous.
  WITH fam AS (
    SELECT
      b.id AS bare_id, b.base_slug,
      s.id AS member_id, s.slug AS member_slug, s.name AS member_name,
      s.manufacturer_id AS member_mfr, s.year AS member_year
    FROM (SELECT DISTINCT base_slug, id FROM _bare_slug) b
    -- Written as EQUALITIES on a precomputed strip, not `regexp_matches(s.slug,
    -- '^' || b.base_slug || '-[0-9]+$')`. The two are exactly equivalent — a slug is
    -- base-plus-digits iff stripping its trailing digits yields the base — but the
    -- regex form builds a pattern per row pair and cost ~10M evaluations, taking the
    -- whole analysis past two minutes. The equality form hash-joins.
    JOIN (SELECT id, slug, name, manufacturer_id, year,
                 regexp_replace(slug, '-[0-9]+$', '') AS stripped
          FROM models) s
      ON s.slug = b.base_slug OR s.stripped = b.base_slug
  ),
  -- The destination country as the CATALOG holds it — `model_export_markets`, which
  -- 0177 has already written 104 rows into. Read from the applied catalog rather than
  -- re-derived from this file's own parse: the slug should reflect what the record
  -- says, and a candidate whose market row was rejected or corrected in review must not
  -- go on naming a slug from the parse that lost.
  --
  -- Exactly one COUNTRY is required. A model exported to two markets has no single
  -- country to be named after, and a free-text `target_label` region ('Europe') is not
  -- a slug component.
  mkt AS (
    SELECT model_id AS id, any_value(target_country_slug) AS country
    FROM model_export_markets
    WHERE target_country_slug IS NOT NULL
    GROUP BY model_id
    HAVING count(*) = 1
  ),
  scored AS (
    SELECT
      b.*,
      k.country AS export_country,
      -- The trailing parenthetical a human already wrote to tell these apart:
      -- 'Alaska (EM)', 'Fireball (Home Model)'. Carried RAW and never turned into a
      -- slug here — see the note above the view on why this analysis composes slugs
      -- but never mints them.
      NULLIF(regexp_extract(b.name, '\(([^)]+)\)$', 1), '') AS name_paren_raw,
      (SELECT count(*) FROM fam f WHERE f.bare_id = b.id AND f.member_id <> b.id) AS n_siblings,
      (SELECT list_sort(list(f.member_slug)) FROM fam f
        WHERE f.bare_id = b.id AND f.member_id <> b.id) AS sibling_slugs,
      -- UNIQUENESS, tested on the FACT rather than on the string a proposal would
      -- build. 'alaska-2' (Recreativos Franco) is uniquely identified by its maker;
      -- 'alaska-3' is NOT, because 'alaska' is Interflip too — so the maker basis has
      -- to decline there rather than mint a second alaska-interflip.
      NOT EXISTS (SELECT 1 FROM fam f WHERE f.bare_id = b.id AND f.member_id <> b.id
                    AND f.member_mfr IS NOT DISTINCT FROM b.manufacturer_id) AS maker_unique,
      NOT EXISTS (SELECT 1 FROM fam f WHERE f.bare_id = b.id AND f.member_id <> b.id
                    AND f.member_year IS NOT DISTINCT FROM b.year) AS year_unique,
      -- Nobody holds the clean base — so one of these records can simply take it, and
      -- the family may need no invented suffix at all.
      NOT EXISTS (SELECT 1 FROM models m2 WHERE m2.slug = b.base_slug) AS base_slug_free
    FROM _bare_slug b
    LEFT JOIN mkt k ON k.id = b.id
  ),
  -- The four candidate slugs, each NULL when its basis has nothing to say.
  cand AS (
    SELECT
      s.*,
      CASE WHEN s.export_country IS NOT NULL THEN s.base_slug || '-' || s.export_country END AS s_export,
      CASE WHEN s.maker_unique               THEN s.base_slug || '-' || s.manufacturer_slug END AS s_maker,
      CASE WHEN s.year_unique AND s.year IS NOT NULL
           THEN s.base_slug || '-' || s.year::VARCHAR END AS s_year
    FROM scored s
  ),
  -- Each candidate vetted against live slugs INDEPENDENTLY, so the preference order can
  -- FALL THROUGH instead of dead-ending. Gottlieb's 'Kicker' (kicker-2) exports to
  -- Italy, but Chicago Coin's 'Kicker (Italy)' already holds `kicker-italy`; the
  -- destination basis yields there and the maker basis supplies `kicker-gottlieb`.
  -- Dead-ending on the first choice lost 3 otherwise-actionable rows.
  vetted AS (
    SELECT
      c.*,
      (c.s_export IS NOT NULL AND NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = c.s_export)) AS f_export,
      (c.s_maker  IS NOT NULL AND NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = c.s_maker))  AS f_maker,
      (c.s_year   IS NOT NULL AND NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = c.s_year))   AS f_year
    FROM cand c
  ),
  proposed AS (
    SELECT
      v.*,
      CASE WHEN v.f_export THEN 'export destination'
           WHEN v.f_maker  THEN 'maker'
           WHEN v.f_year   THEN 'year' END AS proposal_basis,
      CASE WHEN v.f_export THEN v.s_export
           WHEN v.f_maker  THEN v.s_maker
           WHEN v.f_year   THEN v.s_year END AS proposed_slug
    FROM vetted v
  )
  SELECT
    p.id, p.slug, p.proposed_slug, p.proposal_basis,
    p.name, p.label, p.manufacturer_name, p.year, p.title_slug,
    p.base_slug, p.base_slug_free, p.n_siblings, p.sibling_slugs,
    p.maker_unique, p.year_unique, p.export_country, p.name_paren_raw,
    -- The proposal must not collide with a live model...
    (p.proposed_slug IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM models m2 WHERE m2.slug = p.proposed_slug)) AS proposed_slug_free,
    -- ...and must not be a slug a SIBLING would equally claim, which is what would
    -- happen for Recel's two 1975 'Criterium 75' records: same maker, so the maker
    -- suffix separates nothing and the real answer is a merge.
    (p.proposed_slug IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM proposed q
        WHERE q.base_slug = p.base_slug AND q.id <> p.id
          AND q.proposed_slug = p.proposed_slug)) AS proposal_resolves
  FROM proposed p
  ORDER BY p.proposal_basis IS NULL, p.base_slug, p.slug;

-- ── 4 · SUMMARY & CHECKS ───────────────────────────────────────────────────
-- The honest-prose tail. Every analysis file keeps these two views.

-- export_summary — the headline numbers README.md quotes, sourced from the views
-- rather than hand-counted. Regenerate the Summary section from this; if a number
-- in the prose and a number here disagree, the prose is stale.
--
-- Every figure here has a reproducible definition. The no-origin orphans' leaf
-- split is now genre-backed: Bingo Pinball and Slot Machine are counted from the
-- game_format FK (below). Only the residual — pinball/other with no origin named —
-- stays prose, since "why is this pinball origin-less" is a per-row source read.
CREATE OR REPLACE VIEW export_summary AS
  -- Detectors and candidate set.
  SELECT 'candidates'          AS metric, count(*)                        AS value FROM export_candidates
  UNION ALL SELECT 'by_notes',           count(*) FILTER (WHERE by_notes)  FROM export_candidates
  UNION ALL SELECT 'by_suffix',          count(*) FILTER (WHERE by_suffix) FROM export_candidates
  UNION ALL SELECT 'by_opdb',            count(*) FILTER (WHERE by_opdb)   FROM export_candidates
  UNION ALL SELECT 'by_twin',            count(*) FILTER (WHERE by_twin)   FROM export_candidates
  -- Twin pairs: deterministic export_edition_of edges, and the domestic halves the twin
  -- sentence positively excludes from the candidate set.
  UNION ALL SELECT 'twin_pairs',          (SELECT count(*) FROM export_twin_pairs)
  UNION ALL SELECT 'twin_pairs_resolved', (SELECT count(*) FROM export_twin_pairs WHERE domestic_model_id IS NOT NULL)
  UNION ALL SELECT 'twin_domestic_excluded', (SELECT count(*) FROM _twin WHERE role = 'domestic')
  UNION ALL SELECT 'opdb_notes_overlap', count(*) FILTER (WHERE by_opdb AND by_notes) FROM export_candidates
  -- Maker-relative: candidates whose parsed market IS the maker's home country
  -- (likely domestic, not export — a review signal, e.g. Conquistador, Univerx).
  UNION ALL SELECT 'market_is_maker_home', count(*) FILTER (WHERE market_is_maker_home) FROM export_candidates
  -- Destination market: how often is one known, and of what kind? (ModelExportMarket.)
  -- market_kind partitions the candidate set: country + region + unknown == candidates.
  UNION ALL SELECT 'market_country',   count(*) FILTER (WHERE market_kind = 'country') FROM export_candidates
  UNION ALL SELECT 'market_region',    count(*) FILTER (WHERE market_kind = 'region')  FROM export_candidates
  UNION ALL SELECT 'market_unknown',   count(*) FILTER (WHERE market_kind = 'unknown') FROM export_candidates
  -- Cardinality of the country markets: single vs the rare multi-country build that is
  -- the ModelExportMarket join table's whole reason for being.
  UNION ALL SELECT 'market_one_country',    count(*) FILTER (WHERE len(markets) = 1) FROM export_candidates
  UNION ALL SELECT 'market_multi_country',  count(*) FILTER (WHERE len(markets) > 1) FROM export_candidates
  -- Parked "for the <X> market" hits: dropped from membership as noise, held for a
  -- later pass. `_foreign` is the subset worth rescuing (a non-maker-home market).
  UNION ALL SELECT 'market_phrase_parked',
    (SELECT count(*) FROM export_market_phrase_review)
  UNION ALL SELECT 'market_phrase_parked_foreign',
    (SELECT count(*) FROM export_market_phrase_review WHERE lead = 'foreign country')
  -- Lineage: does the candidate already carry an edge?
  UNION ALL SELECT 'has_edge',           count(*) FILTER (WHERE has_edge)      FROM export_candidate_lineage
  UNION ALL SELECT 'has_inbound_only',   count(*) FILTER (WHERE has_inbound_only) FROM export_candidate_lineage
  UNION ALL SELECT 'no_edge',            count(*) FILTER (WHERE NOT has_edge)  FROM export_candidate_lineage
  UNION ALL SELECT 'no_edge_share_title', count(*) FILTER (WHERE NOT has_edge AND title_size > 1)  FROM export_candidate_lineage
  UNION ALL SELECT 'no_edge_alone',        count(*) FILTER (WHERE NOT has_edge AND title_size <= 1) FROM export_candidate_lineage
  -- Share-a-title candidates partitioned by reward-type signal: variant / copy /
  -- need-notes sum to no_edge_share_title. same_maker keys on manufacturer_id, so
  -- 'copy' is a cross-BRAND reward-differing mate; one qualifying mate is enough.
  UNION ALL SELECT 'share_title_variant_signal',
    (SELECT count(DISTINCT id) FROM export_titlemate_review WHERE reward_differs AND same_maker)
  UNION ALL SELECT 'share_title_copy_signal',
    (SELECT count(*) FROM (SELECT id FROM export_titlemate_review GROUP BY id
       HAVING bool_or(reward_differs AND NOT same_maker) AND NOT bool_or(reward_differs AND same_maker)))
  UNION ALL SELECT 'share_title_need_notes',
    (SELECT count(*) FROM (SELECT id FROM export_titlemate_review GROUP BY id
       HAVING NOT bool_or(reward_differs)))
  -- Alone-in-title orphans, by whether their free text leads anywhere.
  UNION ALL SELECT 'alone_origin_named',      count(*) FILTER (WHERE origin_lead = 'origin named')                              FROM export_orphan_review
  UNION ALL SELECT 'alone_origin_in_catalog', count(*) FILTER (WHERE quoted_in_catalog)                                        FROM export_orphan_review
  UNION ALL SELECT 'alone_no_origin',         count(*) FILTER (WHERE origin_lead IN ('freetext, no origin named','no freetext')) FROM export_orphan_review
  -- No-origin leaf split by genre: bingos and slots have no pinball analogue.
  -- Predicated on the stable game_format_slug, not the display name.
  UNION ALL SELECT 'alone_no_origin_bingo',   count(*) FILTER (WHERE origin_lead IN ('freetext, no origin named','no freetext') AND game_format_slug = 'bingo-pinball') FROM export_orphan_review
  UNION ALL SELECT 'alone_no_origin_slot',    count(*) FILTER (WHERE origin_lead IN ('freetext, no origin named','no freetext') AND game_format_slug = 'slot-machine')  FROM export_orphan_review
  -- residual: no-origin models that are neither bingo nor slot (pinball/other, per-row read).
  -- bingo + slot + other == alone_no_origin, so the leaf split is self-checking.
  UNION ALL SELECT 'alone_no_origin_other',    count(*) FILTER (WHERE origin_lead IN ('freetext, no origin named','no freetext') AND game_format_slug IS DISTINCT FROM 'bingo-pinball' AND game_format_slug IS DISTINCT FROM 'slot-machine') FROM export_orphan_review
  -- Name-family regroup: candidates with a same-maker singleton-Title sibling, and
  -- the shape-C (no-origin) subset of those.
  UNION ALL SELECT 'name_family_candidates',
    (SELECT count(DISTINCT candidate) FROM export_name_family)
  UNION ALL SELECT 'name_family_shape_c',
    (SELECT count(DISTINCT candidate) FROM export_name_family WHERE origin_lead = 'freetext, no origin named')
  -- Namesakes across Titles: the same game name in a SEPARATE Title. Two independent
  -- worklists come out of it — the EDGE (export edition vs the cross-maker `copy` the
  -- 0128 campaign owns) and the TITLE merge, which `title_merge_lead` counts separately.
  -- `namesake_merge_backlog` is the one worth watching: pairs this campaign has ALREADY
  -- joined with an edge but left sitting in two singleton Titles.
  UNION ALL SELECT 'namesake_pairs',      (SELECT count(*) FROM export_namesake_review)
  UNION ALL SELECT 'namesake_candidates', (SELECT count(DISTINCT id) FROM export_namesake_review)
  UNION ALL SELECT 'namesake_export_edition',
    (SELECT count(DISTINCT id) FROM export_namesake_review WHERE lead = 'export edition')
  UNION ALL SELECT 'namesake_foreign_build',
    (SELECT count(DISTINCT id) FROM export_namesake_review WHERE lead = 'foreign build (copy)')
  UNION ALL SELECT 'namesake_coincidence',
    (SELECT count(*) FROM export_namesake_review WHERE lead LIKE 'likely coincidence%')
  UNION ALL SELECT 'namesake_title_merge_leads',
    (SELECT count(DISTINCT id) FROM export_namesake_review WHERE title_merge_lead)
  -- The merge emit layer: what the gate would author, and what it held back.
  UNION ALL SELECT 'merge_rows',    (SELECT count(*) FROM export_merge_rows)
  UNION ALL SELECT 'merge_blocked', (SELECT count(*) FROM export_merge_blocked)
  UNION ALL SELECT 'namesake_merge_backlog',
    (SELECT count(*) FROM export_namesake_review WHERE title_merge_lead AND already_related)
  -- Emit layer: what gen.py actually writes, and what the gate held back. patch_rows
  -- + the rejected rows that fell through to no tier + opdb_review == candidates is
  -- NOT an identity (a rejected notes row can still emit on `suffix`), so the checks
  -- below assert the partitions that ARE exact rather than this being a sum.
  UNION ALL SELECT 'patch_rows',        (SELECT count(*) FROM export_patch_rows)
  UNION ALL SELECT 'patch_twin',        (SELECT count(*) FROM export_patch_rows WHERE kind = 'twin')
  UNION ALL SELECT 'patch_notes',       (SELECT count(*) FROM export_patch_rows WHERE kind = 'notes')
  UNION ALL SELECT 'patch_suffix',      (SELECT count(*) FROM export_patch_rows WHERE kind = 'suffix')
  UNION ALL SELECT 'patch_reciprocal',  (SELECT count(*) FROM export_patch_rows WHERE kind = 'reciprocal')
  -- Rows carrying a SECOND source: the original's own record corroborating the export.
  UNION ALL SELECT 'patch_rows_with_reciprocal_cite',
    (SELECT count(*) FROM export_patch_rows WHERE len(recip_cites) > 0)
  UNION ALL SELECT 'patch_reciprocal_statements', (SELECT count(*) FROM _reciprocal)
  -- The three ModelExportMarket shapes. Exactly one per row, by construction.
  UNION ALL SELECT 'patch_market_country', (SELECT count(*) FROM export_patch_rows WHERE len(market_countries) > 0)
  UNION ALL SELECT 'patch_market_label',   (SELECT count(*) FROM export_patch_rows WHERE market_label IS NOT NULL)
  UNION ALL SELECT 'patch_market_unknown', (SELECT count(*) FROM export_patch_rows
                                              WHERE len(market_countries) = 0 AND market_label IS NULL)
  UNION ALL SELECT 'patch_export_edition_of', (SELECT count(*) FROM export_patch_rows WHERE export_edition_of IS NOT NULL)
  UNION ALL SELECT 'patch_fk_twin',      (SELECT count(*) FROM export_patch_rows WHERE export_edition_of IS NOT NULL AND kind = 'twin')
  UNION ALL SELECT 'patch_fk_maker_ref', (SELECT count(*) FROM export_patch_rows WHERE origin_how = 'maker-ref')
  UNION ALL SELECT 'patch_fk_name_only', (SELECT count(*) FROM export_patch_rows WHERE origin_how = 'name-only')
  UNION ALL SELECT 'patch_fk_reciprocal', (SELECT count(*) FROM export_patch_rows WHERE origin_how = 'reciprocal')
  -- RECIPROCALLY CONFIRMED: the TARGET's own note names this candidate back ("The
  -- Italian version is Gottlieb's 1968 'Big Jack'."). That is a second, independent
  -- statement of the same edge, from the other end — the strongest evidence available
  -- short of a human read, and the reason to trust the parse. Reported, not enforced:
  -- a one-sided note is normal, so absence is not an error.
  UNION ALL SELECT 'patch_fk_reciprocal_confirmed',
    (SELECT count(*) FROM export_patch_rows r JOIN models t ON t.slug = r.export_edition_of
      WHERE r.export_edition_of IS NOT NULL
        AND COALESCE(t.ipdb_notes, '') LIKE '%''' || (SELECT name FROM models WHERE id = r.id) || '''%')
  -- Held back: the notes gate's rejects, and the OPDB flag bucket.
  UNION ALL SELECT 'patch_rejected',    (SELECT count(*) FROM export_patch_rejected)
  UNION ALL SELECT 'patch_opdb_review', (SELECT count(*) FROM export_opdb_review)
  -- NAME CLUSTERS — the catalog-wide grain, independent of detector membership.
  UNION ALL SELECT 'cluster_count',     (SELECT count(*) FROM export_name_cluster)
  UNION ALL SELECT 'cluster_models',    (SELECT sum(n_models) FROM export_name_cluster)
  UNION ALL SELECT 'cluster_settled',   (SELECT count(*) FROM export_name_cluster WHERE cluster_state = 'settled')
  UNION ALL SELECT 'cluster_untouched', (SELECT count(*) FROM export_name_cluster WHERE cluster_state = 'untouched')
  UNION ALL SELECT 'cluster_with_paired_brand', (SELECT count(*) FROM export_name_cluster WHERE has_paired_brand)
  -- Paired brands: how many maker pairs the ratio detector finds, and how much of what
  -- it finds is still unworked. `paired_brand_unworked` is the campaign-shaped number —
  -- contemporaneous same-named pairs inside one operation, carrying no edge.
  UNION ALL SELECT 'paired_brand_pairs',        (SELECT count(*) FROM _paired_brand)
  UNION ALL SELECT 'paired_brand_same_home',    (SELECT count(*) FROM _paired_brand WHERE same_home)
  UNION ALL SELECT 'paired_brand_foreign',      (SELECT count(*) FROM _paired_brand WHERE NOT same_home)
  -- Cohorts nobody has judged yet: the honest frontier of this detector.
  UNION ALL SELECT 'paired_brand_unjudged',     (SELECT count(*) FROM _paired_brand WHERE cohort_edge IS NULL)
  UNION ALL SELECT 'paired_brand_unworked',     (SELECT COALESCE(sum(n_close - n_close_edged), 0) FROM _paired_brand)
  -- The pair grain and what is left to decide on it.
  UNION ALL SELECT 'cluster_pairs',             (SELECT count(*) FROM export_cluster_pairs)
  UNION ALL SELECT 'cluster_pairs_settled',     (SELECT count(*) FROM export_cluster_pairs WHERE pair_state = 'settled')
  UNION ALL SELECT 'cluster_pairs_title_split', (SELECT count(*) FROM export_cluster_pairs WHERE pair_state = 'title split')
  UNION ALL SELECT 'cluster_pairs_edge_missing',(SELECT count(*) FROM export_cluster_pairs WHERE pair_state = 'edge missing')
  UNION ALL SELECT 'lead_export_edition_paired',(SELECT count(*) FROM export_cluster_pairs WHERE lead = 'export edition (paired brand)')
  UNION ALL SELECT 'lead_same_home_unjudged',   (SELECT count(*) FROM export_cluster_pairs WHERE lead = 'same-home partner, unjudged cohort')
  UNION ALL SELECT 'lead_foreign_build_copy',   (SELECT count(*) FROM export_cluster_pairs WHERE lead = 'foreign build (copy)')
  UNION ALL SELECT 'lead_duplicate_record',     (SELECT count(*) FROM export_cluster_pairs WHERE lead = 'duplicate record?')
  -- The finished-edge / unfinished-Title backlog, split by which edge was claimed.
  UNION ALL SELECT 'merge_backlog',             (SELECT count(*) FROM export_merge_backlog)
  UNION ALL SELECT 'merge_backlog_export',      (SELECT count(*) FROM export_merge_backlog WHERE list_contains(edge_types, 'export_edition_of'))
  UNION ALL SELECT 'merge_backlog_both_alone',  (SELECT count(*) FROM export_merge_backlog WHERE both_alone_in_title)
  UNION ALL SELECT 'duplicate_smell',           (SELECT count(*) FROM export_duplicate_smell)
  UNION ALL SELECT 'duplicate_smell_on_candidate', (SELECT count(*) FROM export_duplicate_smell WHERE touches_a_candidate)
  -- BARE NUMERIC SLUGS — unfinished disambiguation, and what the catalog now knows to
  -- finish it with. `slug_deficit_actionable` is the emit-ready number: a proposal that
  -- both resolves its family and collides with nothing live.
  UNION ALL SELECT 'slug_deficit',            (SELECT count(*) FROM export_slug_deficit)
  UNION ALL SELECT 'slug_deficit_by_export',  (SELECT count(*) FROM export_slug_deficit WHERE proposal_basis = 'export destination')
  UNION ALL SELECT 'slug_deficit_has_paren',  (SELECT count(*) FROM export_slug_deficit WHERE name_paren_raw IS NOT NULL)
  UNION ALL SELECT 'slug_deficit_by_maker',   (SELECT count(*) FROM export_slug_deficit WHERE proposal_basis = 'maker')
  UNION ALL SELECT 'slug_deficit_by_year',    (SELECT count(*) FROM export_slug_deficit WHERE proposal_basis = 'year')
  UNION ALL SELECT 'slug_deficit_no_basis',   (SELECT count(*) FROM export_slug_deficit WHERE proposal_basis IS NULL)
  UNION ALL SELECT 'slug_deficit_actionable', (SELECT count(*) FROM export_slug_deficit WHERE proposal_resolves AND proposed_slug_free)
  UNION ALL SELECT 'slug_deficit_base_free',  (SELECT count(*) FROM export_slug_deficit WHERE base_slug_free)
  ORDER BY metric;

-- export_checks — invariants that should always hold. Empty result = healthy; any
-- row is a problem to investigate. Query `FROM export_checks;` after each re-run.
-- Three check classes (see flipcommons' scripts/analysis/README.md):
--   Structural : joins preserve grain; the detector set covers the candidates
--   Vocabulary : parsed values belong to a closed set (markets are countries)
--   Anchors    : each heuristic still fires on a known example — the only class
--                that catches a whole detector going dark, which a row-level
--                invariant cannot see.
CREATE OR REPLACE VIEW export_checks AS
  -- Structural: every candidate appears exactly once in the lineage view.
  SELECT 'lineage_missing_candidate' AS check, c.id, c.name AS detail
  FROM export_candidates c
  WHERE NOT EXISTS (SELECT 1 FROM export_candidate_lineage l WHERE l.id = c.id)
  UNION ALL
  -- Structural: a suffix hit always parses a country, so its markets can't be empty.
  SELECT 'suffix_without_market', c.id, c.name
  FROM export_candidates c
  WHERE c.by_suffix AND len(c.markets) = 0
  UNION ALL
  -- Structural: no quote may end mid-name at a title abbreviation. `make verify-quotes`
  -- cannot see this — a truncated span is still a verbatim substring of the source, so
  -- it passes — which is exactly why it needs a check of its own.
  SELECT 'quote_truncated_at_abbreviation', r.id, r.slug || ': ' || q
  FROM export_patch_rows r,
       UNNEST([r.quote, r.role_quote] || list_transform(r.recip_cites, lambda c: c.quote)) AS t(q)
  WHERE q IS NOT NULL
    AND regexp_matches(q, '''(Mr|Mrs|Ms|Dr|St|Capt|Sgt)\.$')
  UNION ALL
  -- Structural: every corroborating cite must IDENTIFY the origin — the ref is the
  -- origin's record, or the quote names it. An entry-level cite rides EVERY claim the
  -- entry asserts, so a cite that does neither attaches to `export_edition_of` while
  -- supporting a different one — how 'Ten-Up' came to cite Pin-Up's note for a King
  -- Pin edge.
  SELECT 'recip_cite_origin_unidentified', r.id,
         r.slug || ' cites ipdb:' || c.ipdb_id || ', which neither IS nor names ' || r.export_edition_of
  FROM export_patch_rows r, UNNEST(r.recip_cites) AS t(c)
  WHERE r.export_edition_of IS NOT NULL
    AND c.ipdb_id IS DISTINCT FROM (SELECT o.ipdb_id FROM models o WHERE o.slug = r.export_edition_of)
    AND c.quote NOT LIKE '%' || (SELECT o.name FROM models o WHERE o.slug = r.export_edition_of) || '%'
  UNION ALL
  -- Structural: `_country_lookup` unions three sources (catalog names, catalog aliases,
  -- this file's adjectives) and every consumer joins it on `token`. A token resolving
  -- two ways would multiply rows in the market parse rather than error, so the
  -- collision-free property the union relies on is asserted rather than assumed.
  SELECT 'country_lookup_ambiguous', NULL::BIGINT,
         token || ' -> ' || string_agg(DISTINCT slug, ', ')
  FROM _country_lookup GROUP BY token HAVING count(DISTINCT slug) > 1
  UNION ALL
  -- Vocabulary: every parsed market slug must be a known country slug.
  SELECT 'market_not_a_country', c.id, mkt
  FROM export_candidates c, UNNEST(c.markets) AS t(mkt)
  WHERE mkt NOT IN (SELECT slug FROM countries)
  UNION ALL
  -- Vocabulary: every parsed region label must belong to the declared region set.
  SELECT 'region_not_declared', c.id, rgn
  FROM export_candidates c, UNNEST(c.regions) AS t(rgn)
  WHERE rgn NOT IN (SELECT label FROM _region_alias)
  UNION ALL
  -- Structural: market_kind must partition the candidates (country|region|unknown), and
  -- must agree with the parsed lists — a 'country' kind needs a country, 'region' a region.
  SELECT 'market_kind_disagrees', c.id, c.market_kind
  FROM export_candidates c
  WHERE c.market_kind NOT IN ('country','region','unknown')
     OR (c.market_kind = 'country' AND len(c.markets) = 0)
     OR (c.market_kind = 'region'  AND (len(c.regions) = 0 OR len(c.markets) > 0))
     OR (c.market_kind = 'unknown' AND (len(c.markets) > 0 OR len(c.regions) > 0))
  UNION ALL
  -- Anchor: the region detector still fires (Phantom Haus is "made for Europe").
  SELECT 'anchor_region_dark', NULL::BIGINT, 'the export-context region detector matched zero models'
  WHERE NOT EXISTS (SELECT 1 FROM export_candidates WHERE market_kind = 'region')
  UNION ALL
  -- Vocabulary: the maker-home slug backing market_is_maker_home must be a country
  -- slug — guards the maker-relative join against a non-country location root.
  SELECT 'maker_home_not_a_country', c.id, c.maker_home_slug
  FROM export_candidates c
  WHERE c.maker_home_slug IS NOT NULL AND c.maker_home_slug NOT IN (SELECT slug FROM countries)
  UNION ALL
  -- Structural: the four detectors must cover the candidate set with nothing left over.
  SELECT 'candidate_without_detector', c.id, c.name
  FROM export_candidates c
  WHERE NOT (c.by_notes OR c.by_suffix OR c.by_opdb OR c.by_twin)
  UNION ALL
  -- Vocabulary/agreement: the twin sentence and the independent "is the name used for
  -- <role> games" sentence must never disagree. This is the whole basis for trusting the
  -- twin parse as deterministic — two independent statements of the same fact. A row here
  -- means the boilerplate changed shape and the parse can no longer be trusted.
  SELECT 'twin_role_contradiction', t.id, t.role || ' vs declared ' || t.declared_role
  FROM _twin t
  WHERE t.declared_role IS NOT NULL AND t.declared_role <> t.role
  UNION ALL
  -- Structural: every "same company made ... version as" sentence must PARSE. Coverage,
  -- not correctness — a new phrasing variant (the qualifier already floats) would
  -- silently drop a pair otherwise.
  SELECT 'twin_sentence_unparsed', m.id, m.name
  FROM models m
  WHERE m.ipdb_notes ILIKE '%same company made%'
    AND NOT EXISTS (SELECT 1 FROM _twin t WHERE t.id = m.id)
  UNION ALL
  -- Structural: the twin roles are opposites, so a model can never be both.
  SELECT 'twin_both_roles', t.id, 'model is both export and domestic side'
  FROM _twin t GROUP BY t.id HAVING count(DISTINCT t.role) > 1
  UNION ALL
  -- Structural: no domestic-side twin may survive as a candidate — that exclusion is the
  -- point of the detector.
  SELECT 'domestic_twin_is_candidate', c.id, c.name
  FROM export_candidates c
  WHERE EXISTS (SELECT 1 FROM _twin t WHERE t.id = c.id AND t.role = 'domestic')
  UNION ALL
  -- Structural: the parked market-phrase set is by definition the rows NO detector
  -- claims, so it must be disjoint from the candidates. Overlap means the clause leaked
  -- back into membership.
  SELECT 'parked_phrase_is_candidate', p.id, p.label
  FROM export_market_phrase_review p
  WHERE EXISTS (SELECT 1 FROM export_candidates c WHERE c.id = p.id)
  UNION ALL
  -- Anchor: the (Country) suffix detector still catches the analysis's own example.
  SELECT 'anchor_suffix_dark', NULL::BIGINT, 'Big Ben (Italy) no longer hits by_suffix'
  WHERE NOT EXISTS (SELECT 1 FROM export_candidates WHERE by_suffix AND name = 'Big Ben (Italy)')
  UNION ALL
  -- Anchor: the ipdb.notes freetext detector still matches something.
  SELECT 'anchor_notes_dark', NULL::BIGINT, 'the ipdb.notes detector matched zero models'
  WHERE NOT EXISTS (SELECT 1 FROM export_candidates WHERE by_notes)
  UNION ALL
  -- Anchor: the opdb.features flag detector still matches something.
  SELECT 'anchor_opdb_dark', NULL::BIGINT, 'the opdb.features detector matched zero models'
  WHERE NOT EXISTS (SELECT 1 FROM export_candidates WHERE by_opdb)
  UNION ALL
  -- Vocabulary/anchor: the game_format slugs the summary counts by must still exist.
  -- A slug change would silently zero alone_no_origin_bingo / _slot with no error;
  -- only this check sees it go dark. Reads the foundation's game_formats vocabulary.
  SELECT 'game_format_vocab_dark', NULL::BIGINT, gf
  FROM (VALUES ('bingo-pinball'), ('slot-machine')) AS t(gf)
  WHERE gf NOT IN (SELECT slug FROM game_formats)
  UNION ALL
  -- Structural: the two no-edge buckets must partition no_edge. They rely on
  -- title_size being non-NULL — a null-title candidate falls out of BOTH (its
  -- title_size comparisons go NULL), and only this sum catches the silent drop.
  SELECT 'no_edge_partition_broken', NULL::BIGINT, 'share_title + alone != no_edge'
  WHERE (SELECT count(*) FROM export_candidate_lineage WHERE NOT has_edge)
     <> (SELECT count(*) FROM export_candidate_lineage WHERE NOT has_edge AND title_size > 1)
      + (SELECT count(*) FROM export_candidate_lineage WHERE NOT has_edge AND title_size <= 1)
  UNION ALL
  -- ── namesake layer ──
  -- Vocabulary: `lead` is a closed set, and the prose in README.md enumerates it. A new
  -- string here means a tier was added without the doc (or a CASE arm fell through).
  SELECT 'namesake_lead_unknown', n.id, n.lead
  FROM export_namesake_review n
  WHERE n.lead NOT IN ('already related', 'export edition', 'same maker, check years',
                       'same maker, format differs', 'foreign build (copy)',
                       'cross-maker, contemporaneous', 'likely coincidence (years apart)',
                       'likely coincidence (format differs)',
                       'likely coincidence (bingo sub-genre differs)', 'needs a source read')
  UNION ALL
  -- Structural: a shared NAME across two unrelated games is exactly what the coincidence
  -- tiers exist to mark, so proposing a Title MERGE on one is self-contradictory —
  -- and a merge is the most destructive action this analysis suggests.
  SELECT 'namesake_merge_on_coincidence', n.id, n.candidate || ' + ' || n.namesake
  FROM export_namesake_review n
  WHERE n.title_merge_lead AND n.lead LIKE 'likely coincidence%'
  UNION ALL
  -- Structural: this view is the CROSS-Title bucket; a same-Title pair belongs to
  -- `export_titlemate_review` and would be double-counted here.
  SELECT 'namesake_same_title_leaked', n.id, n.title_slug
  FROM export_namesake_review n
  WHERE n.title_slug IS NOT DISTINCT FROM n.namesake_title
  UNION ALL
  -- Structural: both `already_related` and `has_edge` read the foundation's
  -- BIDIRECTIONAL edge view, so a pair related in either direction must have a
  -- connected candidate. This check needed an inbound-edge escape hatch while
  -- has_edge was outbound-only; the two probes now agree by construction, and a row
  -- here means one of them drifted back to the directional view.
  SELECT 'namesake_related_without_edge', n.id, n.candidate
  FROM export_namesake_review n
  WHERE n.already_related AND NOT n.has_edge
  UNION ALL
  -- Anchor: the namesake detector still fires. It cannot drain to zero by review alone —
  -- the coincidence tiers (a generic name reused decades apart) are permanent — so an
  -- empty result means the name key or the Title join broke, not that the work is done.
  SELECT 'anchor_namesake_dark', NULL::BIGINT, 'the cross-Title namesake detector matched zero pairs'
  WHERE NOT EXISTS (SELECT 1 FROM export_namesake_review)
  UNION ALL
  -- ── merge emit layer ──
  -- Structural: `slug` is UNIQUE, so two merges must never propose the same new slug.
  -- Not hypothetical — building this, `name_key` stripped the parenthetical and sent
  -- BOTH 'Hula-Hula' and 'Hula-Hula (Italy)' (same maker, same destination Title) to
  -- `hula-hula-chicago-coin`. A soft-delete does not free a slug either, so a
  -- collision is a hard apply failure, not a warning.
  SELECT 'merge_new_slug_collision', NULL::BIGINT, r.new_slug
  FROM export_merge_rows r GROUP BY r.new_slug HAVING count(*) > 1
  UNION ALL
  -- ...and it must not collide with a slug some OTHER live model already holds.
  SELECT 'merge_new_slug_taken', r.id, r.new_slug
  FROM export_merge_rows r
  WHERE EXISTS (SELECT 1 FROM models m WHERE m.slug = r.new_slug AND m.id <> r.id)
  UNION ALL
  -- Structural: a model can only move INTO a different Title. A row whose source and
  -- destination Titles are equal would delete the Title it just moved the model into.
  SELECT 'merge_title_is_destination', r.id, r.doomed_title
  FROM export_merge_rows r WHERE r.doomed_title IS NOT DISTINCT FROM r.new_title
  UNION ALL
  -- Structural: one row per mover. Two rows moving one model into two Titles is a
  -- contradiction, and the second would silently win at apply.
  SELECT 'merge_mover_duplicated', r.id, r.mover_slug
  FROM export_merge_rows r GROUP BY r.id, r.mover_slug HAVING count(*) > 1
  UNION ALL
  -- Structural: a mover and its survivor must not be the same model.
  SELECT 'merge_self_pair', r.id, r.mover_slug
  FROM export_merge_rows r WHERE r.id = r.survivor_id
  UNION ALL
  -- Correctness: the quote is the row's whole evidence, so it must exist and name the
  -- survivor. This restates the gate as an invariant — if the two ever disagree, the
  -- gate has a hole.
  SELECT 'merge_quote_missing', r.id, r.mover_slug
  FROM export_merge_rows r WHERE r.quote IS NULL OR r.quote = ''
  UNION ALL
  -- Restated on the RESOLVED reference rather than a name search: every emitted row's
  -- quote must resolve, on name+maker+year, to exactly the survivor.
  SELECT 'merge_quote_resolves_elsewhere', r.id, r.mover_slug
  FROM _merge_scored r
  WHERE r.blocked_reason IS NULL AND r.ref_model_id IS DISTINCT FROM r.namesake_id
  UNION ALL
  -- Correctness: an `export_edition_of` edge requires a shared maker; a different
  -- maker's build is a `copy`. Same rule as `patch_fk_cross_maker`, restated for the
  -- merge layer, which is where a wrong edge would ride in on a Title decision.
  SELECT 'merge_edge_cross_maker', r.id, r.mover_slug || ' -> ' || r.survivor_slug
  FROM export_merge_rows r
  JOIN models m ON m.id = r.id
  JOIN models t ON t.id = r.survivor_id
  WHERE r.edge_kind = 'export_edition_of'
    AND m.manufacturer_id IS DISTINCT FROM t.manufacturer_id
  UNION ALL
  -- Guard: the pair that motivated the gate must never emit. Nothing sources a Splin
  -- -> Bally 'Acapulco' edge, and an ungated emitter would have authored one.
  SELECT 'merge_guard_regressed', r.id, r.mover_slug || ' is emitting a merge again'
  FROM export_merge_rows r WHERE r.mover_slug IN ('acapulco-2', 'circus-sirmo', 'dixieland-2')
  UNION ALL
  -- ── emit layer ──
  -- Structural: every patch row is a candidate, and appears exactly once (gen.py
  -- writes one claims: entry per row, and a duplicate ref would collide at apply).
  -- ...except a `reciprocal` row, which is DISCOVERED from the original's record
  -- rather than detected on its own, so it legitimately isn't a candidate.
  SELECT 'patch_row_not_a_candidate', r.id, r.label
  FROM export_patch_rows r
  WHERE r.kind <> 'reciprocal'
    AND NOT EXISTS (SELECT 1 FROM export_candidates c WHERE c.id = r.id)
  UNION ALL
  SELECT 'patch_row_duplicated', r.id, r.slug
  FROM export_patch_rows r GROUP BY r.id, r.slug HAVING count(*) > 1
  UNION ALL
  -- Structural: gen.py keys every entry on `model.<slug>`, so a null slug would emit
  -- a malformed ref rather than fail.
  SELECT 'patch_row_without_slug', r.id, r.label
  FROM export_patch_rows r WHERE r.slug IS NULL OR r.slug = ''
  UNION ALL
  -- Structural: the quote-bearing tiers must actually carry a quote AND the ipdb_id
  -- the cite is built from. A row citing ipdb: with no quote would ship an
  -- unverifiable claim; `make verify-quotes` can only check quotes that exist.
  SELECT 'patch_quote_tier_incomplete', r.id, r.label
  FROM export_patch_rows r
  WHERE r.kind IN ('twin', 'notes') AND (r.quote IS NULL OR r.quote = '' OR r.ipdb_id IS NULL)
  UNION ALL
  -- Structural: the `suffix` tier cites nothing, so it must carry its evidence — the
  -- country parsed off the model's own name — or it claims nothing at all.
  SELECT 'patch_suffix_without_market', r.id, r.label
  FROM export_patch_rows r
  WHERE r.kind = 'suffix' AND len(r.market_countries) = 0
  UNION ALL
  -- Structural: the market shapes must be MUTUALLY EXCLUSIVE. This is the check that
  -- protects the "a null-location row must be the model's only row" convention, which
  -- ingest does NOT enforce (DataPatches.md) — if it breaks, the patch applies an
  -- illegal mix silently.
  SELECT 'patch_market_shape_mixed', r.id, r.label
  FROM export_patch_rows r
  WHERE len(r.market_countries) > 0 AND r.market_label IS NOT NULL
  UNION ALL
  -- Vocabulary: every emitted market slug must be a country, since it becomes a
  -- `target_market_location` and flipcommons rejects a non-top-level location.
  SELECT 'patch_market_not_a_country', r.id, mkt
  FROM export_patch_rows r, UNNEST(r.market_countries) AS t(mkt)
  WHERE mkt NOT IN (SELECT slug FROM countries)
  UNION ALL
  -- Vocabulary: an emitted label must belong to the declared region set.
  SELECT 'patch_label_not_declared', r.id, r.market_label
  FROM export_patch_rows r
  WHERE r.market_label IS NOT NULL AND r.market_label NOT IN (SELECT label FROM _region_alias)
  UNION ALL
  -- Structural: `export_edition_of` must resolve to a real model and never self-point
  -- (flipcommons carries an anti-self CHECK; catching it here beats failing at apply).
  SELECT 'patch_fk_unresolved', r.id, r.export_edition_of
  FROM export_patch_rows r
  WHERE r.export_edition_of IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = r.export_edition_of)
  UNION ALL
  SELECT 'patch_fk_self_reference', r.id, r.slug
  FROM export_patch_rows r WHERE r.export_edition_of = r.slug
  UNION ALL
  -- Structural: every FK must carry the PROVENANCE of how it was parsed. A target
  -- without one was inferred, which this campaign does not do.
  SELECT 'patch_fk_without_provenance', r.id, r.label
  FROM export_patch_rows r
  WHERE r.export_edition_of IS NOT NULL AND r.origin_how IS NULL
  UNION ALL
  SELECT 'patch_fk_provenance_unknown', r.id, COALESCE(r.origin_how, '<null>')
  FROM export_patch_rows r
  WHERE r.origin_how IS NOT NULL
    AND r.origin_how NOT IN ('twin', 'maker-ref', 'name-only', 'reciprocal')
  UNION ALL
  -- Structural: a `suffix` row cites nothing of its own, so its only route to a target
  -- is a reciprocal note — which DOES bring a cite with it.
  SELECT 'patch_suffix_carries_unsourced_fk', r.id, r.label
  FROM export_patch_rows r
  WHERE r.kind = 'suffix' AND r.export_edition_of IS NOT NULL
    AND (r.origin_how IS DISTINCT FROM 'reciprocal' OR len(r.recip_cites) = 0)
  UNION ALL
  -- Correctness: an export edition and its original share a MAKER — a different
  -- maker's build is a `copy`, not an export. The TWIN tier is the deliberate
  -- exception, and the only one: its sentence says "the SAME COMPANY made ...", i.e.
  -- one company running two brands (Recel/Petaco, Interflip/Recreativos Franco).
  SELECT 'patch_fk_cross_maker', r.id, r.label || ' -> ' || r.export_edition_of
  FROM export_patch_rows r
  JOIN models m ON m.id = r.id
  JOIN models t ON t.slug = r.export_edition_of
  WHERE r.origin_how IS DISTINCT FROM 'twin'
    AND m.manufacturer_id IS DISTINCT FROM t.manufacturer_id
  UNION ALL
  -- Structural: a `reciprocal` row's ONLY evidence is the corroborating note, so it
  -- must have one, with a citable ipdb id.
  SELECT 'patch_reciprocal_without_cite', r.id, r.label
  FROM export_patch_rows r
  WHERE r.kind = 'reciprocal'
    AND (len(r.recip_cites) = 0
         OR EXISTS (SELECT 1 FROM UNNEST(r.recip_cites) AS t(c) WHERE c.ipdb_id IS NULL))
  UNION ALL
  -- Structural: every emitted row must carry SOME evidence — a quote to cite, a
  -- reciprocal note, or (suffix only) the name-derived market its note reasons from.
  SELECT 'patch_row_without_evidence', r.id, r.label
  FROM export_patch_rows r
  WHERE NOT (
    (r.kind IN ('twin', 'notes') AND r.quote IS NOT NULL AND r.ipdb_id IS NOT NULL)
    OR (r.kind = 'suffix' AND len(r.market_countries) > 0)
    OR len(r.recip_cites) > 0
  )
  UNION ALL
  -- Correctness: EXPORT IS MAKER-RELATIVE. A model built for the country its maker
  -- is based in is domestic, not an export (README.md; DataPatchAuthoring.md). A row
  -- claiming its maker's home country as a destination is a false claim, not a weak
  -- one — the one invariant here that guards meaning rather than shape.
  SELECT 'patch_market_is_maker_home', r.id, r.label || ' -> ' || mkt
  FROM export_patch_rows r
  JOIN models m ON m.id = r.id, UNNEST(r.market_countries) AS t(mkt)
  WHERE m.country_slug IS NOT NULL AND mkt = m.country_slug
  UNION ALL
  -- Structural: the twin tier's evidence is a role statement, not a destination, so
  -- every twin row must be an unknown-market `- {}`. A country appearing there would
  -- mean the twin sentence was parsed for a market it never stated.
  SELECT 'patch_twin_claims_a_market', r.id, r.label
  FROM export_patch_rows r
  WHERE r.kind = 'twin' AND (len(r.market_countries) > 0 OR r.market_label IS NOT NULL)
  UNION ALL
  -- Anchor: the notes gate still passes its worked example. A tightened regex that
  -- accidentally rejects everything would otherwise show up only as a smaller patch.
  SELECT 'anchor_notes_tier_dark', NULL::BIGINT, 'the notes tier emitted zero rows'
  WHERE NOT EXISTS (SELECT 1 FROM export_patch_rows WHERE kind = 'notes')
  UNION ALL
  SELECT 'anchor_big_ben_italy_missing', NULL::BIGINT,
         'Big Ben (Italy) no longer emits a notes row for italy'
  WHERE NOT EXISTS (
    SELECT 1 FROM export_patch_rows
    WHERE slug = 'big-ben-segasa-italy' AND kind = 'notes' AND list_contains(market_countries, 'italy'))
  UNION ALL
  -- Anchor: the twin tier still resolves its counterpart (the deterministic tier is
  -- the campaign's whole basis for authoring `export_edition_of` at all).
  SELECT 'anchor_twin_tier_dark', NULL::BIGINT, 'no twin row resolved an export_edition_of target'
  WHERE NOT EXISTS (SELECT 1 FROM export_patch_rows WHERE kind = 'twin' AND export_edition_of IS NOT NULL)
  UNION ALL
  -- Anchor: the FALSE-POSITIVE guards still bite. Every row below was OBSERVED
  -- emitting a wrong claim while this gate was being built; each must stay OUT of the
  -- patch. Without this a loosened regex silently re-admits a known-bad claim.
  SELECT 'anchor_guard_regressed', r.id, g.slug || ' is emitting again (' || g.why || ')'
  FROM (VALUES
    ('eclipse',       'names another model''s export version'),
    ('mini-cycle',    'export attaches to Space Orbit'),
    ('polo',          'export attaches to Space Orbit'),
    ('royal-cards',   'the export is Royal Pair'),
    ('sky-devils',    'the export is Sky Dive'),
    ('the-card',      'the export is Lucky Card'),
    ('m-79-ambush',   'the export is an announced new version'),
    ('dimension',     'its export version is Galaxie'),
    ('wall-street-2', 'the export is Wall Street Special (Spain)'),
    ('extra-inning',  'the note denies the export'),
    ('hyde-park',     'the export is Hyde Park (Italy)'),
    ('gold-rush-2',   'the export is Jackpot')
  ) AS g(slug, why)
  JOIN export_patch_rows r ON r.slug = g.slug
  UNION ALL
  -- Guard: a reciprocal statement must not resurrect a DOMESTIC build. Maresa is a
  -- Spanish maker, so "A single-player Spanish version is Maresa's 1972 'Dakota'"
  -- describes a home-market game; it must never become an export row.
  SELECT 'anchor_recip_domestic_regressed', r.id, r.label || ' is emitting again'
  FROM export_patch_rows r WHERE r.slug = 'dakota'
  UNION ALL
  -- ...and the guards are only meaningful while their slugs still resolve. A reslug
  -- would otherwise turn every guard above into a silent no-op.
  SELECT 'anchor_guard_slug_stale', NULL::BIGINT, g.slug || ' is no longer a model slug'
  FROM (VALUES
    ('eclipse'), ('mini-cycle'), ('polo'), ('royal-cards'), ('sky-devils'), ('the-card'),
    ('m-79-ambush'), ('dimension'), ('wall-street-2'), ('extra-inning'), ('hyde-park'),
    ('gold-rush-2'), ('big-ben-segasa-italy'), ('dakota'), ('lariat-2'), ('speakeasy-2')
  ) AS g(slug)
  WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = g.slug)
  UNION ALL
  -- ── name clusters ────────────────────────────────────────────────────────
  -- Anchor: the paired-brand detector still finds the pairs this campaign was BUILT on.
  -- Both were discovered through IPDB's twin sentence; the detector must reach them from
  -- structure alone, or its whole claim to generalize beyond that sentence is void.
  SELECT 'anchor_paired_brand_dark', NULL::BIGINT,
         a || ' / ' || b || ' is no longer detected as a paired brand'
  FROM (VALUES ('Recel', 'Petaco'), ('Interflip', 'Recreativos Franco')) AS g(a, b)
  WHERE NOT EXISTS (
    SELECT 1 FROM _paired_brand p
     WHERE (p.a_maker = g.a AND p.b_maker = g.b) OR (p.a_maker = g.b AND p.b_maker = g.a))
  UNION ALL
  -- Guard: the detector must NOT admit two unrelated makers who merely reused generic
  -- nouns for forty years. Bally and Gottlieb share 64 model names and one of them
  -- contemporaneously; if they appear here the ratio arm has stopped biting and every
  -- 'export edition (paired brand)' lead below is suspect.
  SELECT 'guard_paired_brand_overreach', NULL::BIGINT,
         p.a_maker || ' / ' || p.b_maker || ' admitted at close_ratio ' || p.close_ratio
  FROM _paired_brand p
  WHERE (p.a_maker, p.b_maker) IN (('Bally', 'Gottlieb'), ('Bally', 'Williams'),
                                   ('Gottlieb', 'Williams'), ('Bally', 'Genco'))
     OR (p.b_maker, p.a_maker) IN (('Bally', 'Gottlieb'), ('Bally', 'Williams'),
                                   ('Gottlieb', 'Williams'), ('Bally', 'Genco'))
  UNION ALL
  -- Structural: a paired-brand maker pair must always be same-home OR cross-border,
  -- never neither — `partner_kind` has to partition the table, since the two kinds mean
  -- opposite edges (export_edition_of vs copy).
  SELECT 'partner_kind_disagrees', NULL::BIGINT, p.a_maker || ' / ' || p.b_maker
  FROM _paired_brand p
  WHERE p.partner_kind NOT IN ('same-home partner', 'cross-border partner')
     OR (p.partner_kind = 'same-home partner') <> p.same_home
     OR p.cohort_edge IS NOT NULL AND p.cohort_edge NOT IN ('export_edition_of', 'copy')
  UNION ALL
  -- Anchor: the cohort calibration still reads Recel/Petaco as an EXPORT cohort. This
  -- is what licenses the 'export edition (paired brand)' tier; if it goes NULL or flips
  -- to 'copy', that tier empties and the detector has lost its one confirmed example.
  SELECT 'anchor_export_cohort_dark', NULL::BIGINT,
         'the Recel/Petaco cohort no longer calibrates as export_edition_of'
  WHERE NOT EXISTS (
    SELECT 1 FROM _paired_brand p
     WHERE p.a_maker IN ('Recel', 'Petaco') AND p.b_maker IN ('Recel', 'Petaco')
       AND p.cohort_edge = 'export_edition_of')
  UNION ALL
  -- Guard: the export tier may NEVER fire on a cohort no human has judged. That tier
  -- asserts the export shape from structure alone, and its only warrant is the cohort's
  -- own authored edges — a row here means an unjudged 1930s rebadge is being presented
  -- as an export lead.
  SELECT 'export_tier_on_unjudged_cohort', p.a_id, p.a_slug || ' / ' || p.b_slug
  FROM export_cluster_pairs p
  WHERE p.lead = 'export edition (paired brand)' AND p.cohort_edge IS DISTINCT FROM 'export_edition_of'
  UNION ALL
  -- Structural: `pair_state` must partition the pair grain — a pair is settled, or
  -- missing an edge, or missing a Title decision, or open. Nothing else.
  SELECT 'pair_state_unknown', p.a_id, p.a_slug || ' / ' || p.b_slug || ': ' || p.pair_state
  FROM export_cluster_pairs p
  WHERE p.pair_state NOT IN ('settled', 'title split', 'edge missing', 'open')
  UNION ALL
  -- Structural: the merge backlog is exactly the title-split pairs, so every row must
  -- carry an edge. A row without one means `pair_state` and the backlog have drifted.
  SELECT 'merge_backlog_without_edge', NULL::BIGINT, m.a_slug || ' / ' || m.b_slug
  FROM export_merge_backlog m
  WHERE len(COALESCE(m.edge_types, [])) = 0
  UNION ALL
  -- Anchor: the merge backlog still sees a worked example. Petaco's 'Criterium 75' and
  -- Recel's carry an `export_edition_of` edge and sit in two Titles — the
  -- finished-edge / unfinished-Title shape this view exists to surface. It succeeds
  -- 'Cavalier', whose merge is authored (the doomed Title holds a second model here,
  -- so this pair is not the simple case and outlives the singleton tranche).
  -- Expected to FIRE once that merge is authored; re-anchor or retire with it.
  SELECT 'anchor_merge_backlog_dark', NULL::BIGINT,
         'criterium-75-3 / criterium-75 no longer appears in export_merge_backlog'
  WHERE EXISTS (SELECT 1 FROM models WHERE slug = 'criterium-75-3')
    AND NOT EXISTS (SELECT 1 FROM export_merge_backlog
                     WHERE 'criterium-75-3' IN (a_slug, b_slug))
  UNION ALL
  -- ── bare numeric slugs ───────────────────────────────────────────────────
  -- Guard: a trailing number that is NOT a placeholder must never be called one. Two
  -- shapes qualify and both were observed being mis-detected while this view was built:
  -- the number is the game's NAME ('Black Magic 4', 'Criterium 2000'), or it is a year
  -- disambiguator ALREADY APPLIED ('big-ben-williams-1954'). Proposing a rename for
  -- either destroys information rather than adding it.
  SELECT 'slug_deficit_ate_a_real_name', b.id, b.slug || ' (' || b.name || ')'
  FROM _bare_slug b WHERE b.slug IN ('black-magic-4', 'criterium-2000',
                                    'big-ben-williams-1954', 'big-ben-daval-1936')
  UNION ALL
  -- Anchor: the detector still fires on the known placeholders. If it goes dark the
  -- whole view empties and reads as "nothing to fix".
  SELECT 'slug_deficit_dark', NULL::BIGINT, g.slug || ' is no longer detected as a bare slug'
  FROM (VALUES ('alaska-2'), ('cherokee-2'), ('criterium-80-2')) AS g(slug)
  WHERE EXISTS (SELECT 1 FROM models m WHERE m.slug = g.slug)
    AND NOT EXISTS (SELECT 1 FROM _bare_slug b WHERE b.slug = g.slug)
  UNION ALL
  -- Structural: a proposed slug must BE a slug — lowercase alphanumerics and single
  -- hyphens, nothing else. This is the guard that catches SQL trying to mint one out of
  -- free text: it fires on the non-ASCII 'target-machine-type-ターケットマシン-タイフ１' the
  -- withdrawn parenthetical basis produced, and on any future attempt to reintroduce it.
  SELECT 'proposed_slug_not_slug_safe', d.id, d.proposed_slug
  FROM export_slug_deficit d
  WHERE d.proposed_slug IS NOT NULL
    AND NOT regexp_matches(d.proposed_slug, '^[a-z0-9]+(-[a-z0-9]+)*$')
  UNION ALL
  -- Vocabulary: the proposal basis is a closed set.
  SELECT 'slug_proposal_basis_unknown', d.id, d.proposal_basis
  FROM export_slug_deficit d
  WHERE d.proposal_basis IS NOT NULL
    AND d.proposal_basis NOT IN ('export destination', 'maker', 'year')
  UNION ALL
  -- Structural: two records must never be proposed the same slug. The uniqueness test
  -- runs on the distinguishing FACT, so a collision here means that test is wrong —
  -- and a rename that collides is worse than the vague slug it replaces.
  SELECT 'slug_proposal_collision', min(d.id), d.proposed_slug
  FROM export_slug_deficit d
  WHERE d.proposed_slug IS NOT NULL AND d.proposal_resolves
  GROUP BY d.proposed_slug HAVING count(*) > 1
  UNION ALL
  -- Structural: a proposal must never re-mint a slug a live model already holds. This
  -- is what would have happened to 'alaska-3', whose maker (Interflip) is also
  -- 'alaska'\'s — caught only because uniqueness reads the family, not the bare rows.
  SELECT 'slug_proposal_taken', d.id, d.proposed_slug
  FROM export_slug_deficit d
  WHERE d.proposal_resolves AND NOT d.proposed_slug_free;
