-- Model-to-model relationship candidate analysis for the 0128-relationships campaign.
--
-- Goal: find every catalog model that SHOULD carry a `ModelRelationship` edge
-- (copy / conversion / conversion_kit / retheme) but doesn't yet, so the campaign
-- can author the patches — and surface already-edged models whose note may not
-- support the edge, for the "wrong existing value" check. This is the DISCOVERY
-- layer; per-note judgement is the AI corpus sweep, and patch authoring is
-- downstream (see this dir's README.md and sweep/SESSION-BRIEF.md).
--
-- WHY THIS EXISTS. The campaign's original candidate set was a one-time regex mine
-- over IPDB Notes, frozen into Worklist.md and reconciled against the DB by bespoke
-- status scripts. This plan replaces that frozen discovery layer with a REPRODUCIBLE
-- query over the LIVE catalog: it reads existing edges straight from the foundation's
-- `model_relationships`, so "what's already done" is a column (has_rel_edge), not a
-- snapshot that goes stale. Note it is `model_relationships`, NOT the unified
-- `model_edges`: this campaign authors TYPED edges, and folding in the lineage FKs
-- would count a `variant_of` as a discharged copy edge. The inbound direction comes
-- from `model_edges_bidir` as a separate, explicitly non-"done" signal. The AI sweep (vetting) and the authoring recipe are unchanged;
-- only the feed into them changes — `relationship_sweep_candidates` is the new
-- candidates.jsonl source, replacing the Worklist read in emit_candidates.py.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (models, model_edges, the read-only
-- connection) is FLIPCOMMONS' shared foundation, reused VERBATIM via the `.read`
-- below — flippatch keeps no copy. Same pattern as ../0172-bingo-game-format/bingo.sql.
--
-- HOW TO RUN. cwd must be the flipcommons checkout so BOTH the `.read` below AND the
-- foundation's own `ATTACH backend/db.sqlite3` resolve there. `make analyze` handles
-- the cwd/path resolution and delegates to flipcommons' shared runner, which prints
-- the analysis_context watermark + relationships_summary and gates on
-- relationships_checks. Do not run this file directly:
--
--     F=campaigns/0128-relationships/relationships.sql
--     make analyze FILE=$F PREFIX=relationships                       # summary, gated on checks
--     make analyze FILE=$F CMD=describe ARGS=$F                       # the view reference
--     make analyze FILE=$F Q="FROM relationship_review LIMIT 40;"     # the actionable queue
--     make analyze FILE=$F Q="FROM relationship_edged_audit;"         # possible wrong existing edges
--     make analyze FILE=$F Q="FROM relationship_uncited_edges;"       # edges with no evidence
--     make analyze FILE=$F Q="FROM relationship_sweep_candidates;" ARGS=--format json   # the sweep feed
--     make analyze FILE=$F CMD=ui                                     # live GUI at localhost:4213
--
-- Nothing is persisted; every count is a live snapshot. Re-run as the catalog moves.
--
-- THE SIGNAL. A model that reproduces or is built on another design describes it in
-- free text. TWO membership detectors (a candidate is their union), because copy and
-- conversion language are distinct vocabularies:
--   by_copy — the free text says the game reproduces another: "copy of", "clone of",
--             "bootleg", "under licen(c/s)e", "licensed build of". Covers copy /
--             licensed-build lineage (the Worklist's `licensed` + `bootleg` buckets).
--   by_conv — the free text says the game reuses another machine's hardware:
--             "conversion of", "conversion kit for", "converted game for", "repaint
--             of", "re-theme". Covers conversion / conversion_kit / retheme.
-- The type/license SPLIT (copy vs conversion vs kit; licensed vs unlicensed) is NOT
-- decided here — that is the sweep's per-note judgement. Detection only needs to find
-- the model and surface the note. Both detectors over-count (a note that MENTIONS a
-- conversion kit isn't always a lineage claim — Big Chief's "Extra Ball Conversion
-- Kit"); every row still wants source review before it becomes a claim.
--
-- THE TARGET GUESS. A quoted 'Game Name' in the free text that resolves to a live
-- model is surfaced as a best-effort `target_guess` — the same role the Worklist's
-- old guesses played: it rides into the sweep as an audited-not-inherited hint, never
-- authority (names aren't unique across makers, and the first quoted title isn't
-- always the origin). The sweep re-derives the target and diffs the guess.

-- == 1 · FOUNDATION ==========================================================
.read scripts/analysis/catalog.sql

-- == 2 · REFERENCE ===========================================================
-- Hand-maintained lookups specific to this analysis. Not derived from the DB.
-- (The detector phrase-sets live inline in _rel_signal below, next to the columns
-- they test, exactly as exports.sql keeps its detector regexes inline.)
--
-- The campaign's HUMAN JUDGEMENT lives here — the open decisions that were recorded
-- as ⚠ callouts in the retired Worklist.md. A query can re-derive candidates but not
-- a reviewer's held-back verdict, so those are encoded as lookups and flowed through
-- the review views and checks, per scripts/analysis/README.md → "Making manual
-- judgment checkable". relationships_checks flags any entry that has gone stale.

-- Per-model open decisions: rows deliberately HELD BACK from an earlier patch
-- because the note doesn't determine a single target. Keyed on the stable ipdb
-- number. `relationship_open_questions` shows each against its CURRENT edge state —
-- read it before authoring one of these, and note that a held-back row that now
-- carries an edge means someone resolved it (or authored past the hold): verify
-- which, don't assume.
CREATE OR REPLACE VIEW _rel_open_question AS
  SELECT * FROM (VALUES
    (3967, 'cosmic-princess', 'held-back-0127',
     'Note says "manufactured in Australia by LAI under license from Stern Electronics", but the only "Cosmic Princess" in IPDB/the catalog IS this LAI record — there is no seeded Stern original to point at. The machine-mined guess of magic-2 was judged a MIS-RESOLUTION. Decide whether to create the Stern original first, or treat this as the primary record and carry no copy edge.'),
    (5424, 'high-ace-2', 'held-back-0127',
     'Note names TWO Williams originals — "Same design as Williams'' 1973 ''Dealer''s Choice''. Same design and coloring as Williams'' 1974 ''Lucky Ace''." Pick the one it actually reproduces (dealers-choice-2 vs lucky-ace), or establish that both edges are correct.'),
    (4979, 'star-flite', 'held-back-0127',
     'Note names "the 2-player Williams'' 1974 ''Super-Flite'' and the 4-player Williams'' 1974 ''Strato-Flite''" (super-flite vs strato-flite). Pick one, or reconsider how a two-original export build should be linked.')
  ) AS t(ipdb_id, slug, kind, question);

-- Maker-level open questions: whether a maker's copying was AUTHORIZED, which the
-- per-model IPDB note never establishes (it establishes only the copy). These bear
-- on `license_status` across the maker's whole catalog, including already-authored
-- edges. Keyed on the Manufacturer slug. Compare with MAKER_AUTHORIZATION in
-- emit_candidates.py, which attaches the resolving sources as sweep evidence.
CREATE OR REPLACE VIEW _rel_maker_question AS
  SELECT * FROM (VALUES
    ('petaco',
     'Notes say only "a copy of Gottlieb''s …" (-> unlicensed), but secondary accounts have Petaco/Recel (founder Juan Paredes) importing and adapting Gottliebs then building their own copies NOT under licence, with VIFICO as the actually-licensed Spanish Gottlieb builder: https://www.flippers.be/recel.html , https://www.flippers.be/vifico.html . Leads, not proof. Also: recel and petaco exist as separate corporate-entity slugs — work out how they relate.'),
    ('fipermatic',
     'The mine defaulted to unlicensed on "a copy of", but every note also says "Gottlieb Made in Brazil" — IPDB describes Gottlieb shipping unassembled components to the Manaus free-trade zone for local assembly, which could be SANCTIONED (-> licensed). The note never says "licence", so it cannot support licensed on its own. Find a source that establishes or denies authorization. (zarza-2 copies Bally''s Xenon, not Gottlieb — the "Gottlieb Made in Brazil" framing may not apply; check separately.)')
  ) AS t(manufacturer_slug, question);

-- Book titles too generic to hunt for as free text. `citation_roots` is the authority
-- on WHICH books the catalog knows (see _rel_book_phrase below), but a handful of the
-- seeded titles are ordinary English that would match half the corpus — a note saying
-- "the pinball machines of the era" is not citing Pinball Machines. Excluded here
-- rather than by a length rule so each exclusion is a decision on the record;
-- `unlisted_generic_book` fails if one names a work that is no longer seeded.
CREATE OR REPLACE VIEW _rel_generic_book AS
  SELECT * FROM (VALUES
    ('Pinball!'),
    ('Pinball Machines'),
    ('Pinball Wizardry'),
    ('Your Pinball Machine'),
    -- stem is "Tilt", a pinball term before it is a book.
    ('Tilt: The Pinball Book')
  ) AS t(root_citation_source_name);

-- Relationship edges asserting AUTHORIZATION (licensed / unlicensed) with no external
-- evidence attached. The campaign's standing rule is that a note establishes the COPY,
-- not the AUTHORIZATION, so an uncited licensed/unlicensed claim is a discipline
-- violation — but these four predate the rule (all from 0124-bally-wulff-models, a
-- maker the README treats as done), so they are a BACKLOG, not a live invariant.
-- Recording them here lets `uncited_licensed_edge` gate every NEW one without gating
-- the run on the old ones, and `stale_uncited_licensed` fires when one is finally
-- cited or removed so this list can't quietly outlive its subjects.
CREATE OR REPLACE VIEW _rel_uncited_licensed_known AS
  SELECT * FROM (VALUES
    ('party-animal-bally-wulff', 'party-animal'),
    ('super-sport',              'hardbody'),
    ('supersonic-bally-wulff',   'supersonic'),
    ('karate-fight',             'black-belt')
  ) AS t(slug, target_slug);

-- == 3 · ANALYSIS ============================================================
-- A candidate hunt: detect -> assemble+enrich -> review. Membership is the union of
-- the two phrase detectors; enrichment reads existing edges from the foundation's
-- `model_edges` (the "already done" signal) and resolves the quoted target guess.

-- _rel_book_phrase — the free-text phrase that names each seeded book, derived from
-- `citation_roots` rather than hand-listed. The old detector hardcoded four titles and
-- silently missed the other fifteen the catalog has seeded, so a note attributing to
-- Pinball Snapshots sailed into the certain tier under-cited — the exact failure the
-- book hold-out exists to prevent. Deriving it means a newly seeded book is covered
-- the day it lands, and `unmatched_book_title` fails if one is neither matchable nor
-- explicitly excepted.
--
-- The phrase is the title's stem before any colon — a note writes "the Pinball
-- Compendium", not "The Pinball Compendium: 1982 to the Present" — except where that
-- stem is itself generic ("Pinball: A Quest for Mastery" stems to "Pinball"), where
-- the full title is used instead.
CREATE OR REPLACE VIEW _rel_book_phrase AS
  SELECT
    r.root_citation_source_name AS title,
    lower(CASE
      WHEN lower(trim(split_part(r.root_citation_source_name, ':', 1))) IN ('pinball', 'tilt')
        THEN r.root_citation_source_name
      ELSE trim(split_part(r.root_citation_source_name, ':', 1))
    END) AS phrase
  FROM citation_roots r
  WHERE r.citation_source_type = 'book'
    AND r.root_citation_source_name NOT IN (SELECT root_citation_source_name FROM _rel_generic_book);

-- THE PHRASEBOOK. Defined once here and shared by the membership detectors and the
-- quote extractor, because those two MUST agree. A phrase that fires the detector but
-- is unknown to the extractor produces a candidate with no quote, which drops out of
-- the certain tier carrying `no-quote-extracted` and nothing a reviewer can act on.
-- That drift is not hypothetical — the extractor previously read a narrower set of
-- FIELDS than the detectors for exactly this reason, and silently lost rows. Sharing
-- one definition makes the agreement structural instead of a thing to remember, and
-- `phrase_not_extractable` below checks it on every run.
--
-- Adding a phrase is cheap; adding one WITHOUT an anchor is how a phrase silently
-- stops matching later. Every phrase here has an anchor in relationships_checks.
--
-- Why these particular additions: the original phrasebook was written from the notes
-- that say "copy of" outright, and IPDB says the same thing many other ways. A
-- same-name/short-year-gap sweep (see relationship_namesake_review) surfaced 24
-- foreign builds of US designs the detectors had never seen, and reading their notes
-- produced this list — "Identical to Bally game of same name" (Bell Games' Flash
-- Gordon), "a customized version of Williams' 1986 'PIN-BOT'" (Unidesa), "An
-- adaptation of Williams' 1972 'Granada'" (Zaccaria). Roughly 140 models carry one of
-- these and were invisible to the campaign before.
CREATE OR REPLACE MACRO _copy_phrase_re() AS
  '(a )?copy of|copied from|clone of|bootleg|unauthori[sz]ed (copy|version|reproduction)'
  || '|knock[- ]?off|under licen[cs]e|built under licen'
  || '|licen[cs]ed (build|copy|version|reproduction) of|reproduction of'
  -- the vocabulary the namesake sweep surfaced
  || '|identical to|customi[sz]ed version of|a modification of'
  || '|an adaptation of|adapted from|same design as';

CREATE OR REPLACE MACRO _conv_phrase_re() AS
  'conversion of|conversion kit|converted (game )?(for|from)|conversion for'
  || '|re-?theme|repaint of|reworked from';

-- detect --
-- Per-model free text and the two membership flags. `txt` concatenates the three
-- prose fields the product doesn't model (ipdb_notes / ipdb_notable_features /
-- description) so a phrase in any of them fires the detector. quoted_names collects
-- distinct 'Quoted Titles' for the target guess (the permissive quote class handles
-- IPDB's mixed backtick/straight/curly quotes, per exports.sql).
CREATE OR REPLACE VIEW _rel_signal AS
  WITH t AS (
    SELECT
      m.id, m.ipdb_id, m.slug, m.name, m.manufacturer_name AS maker,
      m.manufacturer_slug AS maker_slug, m.year, m.label,
      m.ipdb_notes AS notes, m.ipdb_notable_features AS notable_features, m.description,
      lower(concat_ws(' | ',
        coalesce(m.ipdb_notes, ''), coalesce(m.ipdb_notable_features, ''), coalesce(m.description, '')
      )) AS txt
    FROM models m
  )
  SELECT
    id, ipdb_id, slug, name, maker, maker_slug, year, label,
    -- All three prose fields are projected, not just notes: the detectors below read
    -- the concatenation, so anything downstream that re-reads a narrower set (the
    -- quote extractor did) silently drops the rows detected via the other two.
    notes, notable_features, description,
    -- by_copy: reproduces another maker's design (copy / bootleg / licensed build).
    regexp_matches(txt, _copy_phrase_re()) AS by_copy,
    -- by_conv: reuses another machine's hardware (conversion / kit / repaint / retheme).
    regexp_matches(txt, _conv_phrase_re()) AS by_conv,
    -- mentions_book_source: the note attributes to a BOOK (the Encyclopedia of
    -- Pinball, the Pinball Compendium, Lawton's Bingo Pinball Machines, …). Such a
    -- note wants TWO citations — the ipdb: cite carrying the quote, plus a cite to
    -- the book that is the original authority — but `cite:`'s ref grammar has only
    -- two forms, `scheme:identifier` (no book scheme is registered) and an http(s)
    -- URL nesting under a seeded WEBSITE root. A book has neither, so the upstream
    -- citation is not expressible today even though the books ARE seeded as
    -- CitationSources. Until flipcommons grows a book ref form, these are held out
    -- of the certain tier so nobody authors a half-attributed claim at speed.
    -- Deliberately OVER-inclusive (a bare "book" counts): this is a filter-out, so
    -- a false positive costs a row a human read, while a false negative ships an
    -- under-cited claim. Two arms: the generic catch-all, plus every SEEDED book
    -- title (derived — see _rel_book_phrase). Generic seeded titles ("Pinball
    -- Machines", "Pinball!") are excepted in _rel_generic_book, since the phrase is
    -- ubiquitous in notes and would match everything.
    (regexp_matches(txt, 'bingo pinball machines|\bbook\b')
     OR EXISTS (SELECT 1 FROM _rel_book_phrase b WHERE txt LIKE '%' || b.phrase || '%')
    ) AS mentions_book_source,
    -- quoted titles anywhere in the prose, for the target guess (review aid only).
    list_distinct(regexp_extract_all(
      concat_ws(' ', coalesce(notes, ''), coalesce(notable_features, ''), coalesce(description, '')),
      '[`''‘“"]([A-Z][^`''’“”"]{1,40})[''’”"]', 1)) AS quoted_names
  FROM t;

-- _quoted_resolved — one row per (candidate, resolved target model). A quoted name
-- resolves to any LIVE model whose name matches after normalizing away case and
-- punctuation (IPDB writes `Star Trek' where the catalog has "Star Trek"). Self is
-- excluded. Names aren't unique across makers, so a quote can resolve to several
-- models — all are kept; the sweep adjudicates. Private: read via target_guess.
-- _title_key — the join key for matching a QUOTED TITLE against a catalog name. It is
-- the foundation's `name_norm()` with the separators then squeezed out, and it needs
-- to be both halves:
--
--   name_norm() alone is accent-correct but SEPARATOR-SIGNIFICANT (it collapses
--   punctuation runs to a space), so IPDB's 'Quick Silver' / 'Knock-Out' / 'Sun Beam'
--   stop matching the catalog's Quicksilver / Knockout / Sunbeam. Real losses: those
--   three plus others showed up the moment the macro was swapped in bare.
--
--   The local `[^a-z0-9]` class this replaced squeezed separators correctly but treats
--   every non-ASCII letter as punctuation, so `Competición Penalty` keys as
--   `competicinpenalty` while a note's unaccented `Competicion Penalty` keys as
--   `competicionpenalty` — they never meet. That is the Spanish-maker cohort this
--   campaign is built around. It also DELETES rather than collapsing, so a wholly
--   accented quote keys to '' and would match every other empty key.
--
-- Composing them keeps the separator-insensitivity and adds the accent folding. The
-- accent cohort has no live instance today (the two anchors below pin both halves),
-- so that half is latent correctness; the separator half is load-bearing right now.
--
-- One deliberate PRECISION gain comes with it: the old ASCII class deleted non-Latin
-- script outright, so `Baseball (ベースボール)` keyed as plain `baseball` and resolved
-- as a target guess for every quoted 'Baseball'. Folding keeps the script, so the two
-- key apart and that false guess is gone. Note this is `name_norm`, NOT the
-- foundation's `name_key` — `name_key` strips a trailing parenthetical, which would
-- re-merge exactly this pair, and the campaign treats `Dragon (EM)` / `Dragon` as
-- genuinely different models (README -> Names).
CREATE OR REPLACE MACRO _title_key(s) AS replace(name_norm(s), ' ', '');

CREATE OR REPLACE VIEW _quoted_resolved AS
  WITH q AS (
    SELECT s.id AS model_id, _title_key(qn) AS qkey
    FROM _rel_signal s, UNNEST(s.quoted_names) AS u(qn)
    WHERE (s.by_copy OR s.by_conv) AND length(qn) > 1
  )
  SELECT DISTINCT q.model_id, m.slug AS target_slug, m.label AS target_label
  FROM q
  JOIN models m ON _title_key(m.name) = q.qkey
              AND m.id <> q.model_id
  WHERE q.qkey <> '';

-- assemble + enrich --
-- One row per candidate (union of the two detectors), joined to its existing edge
-- state and its resolved target guess. All edge facts read from the foundation's
-- `model_edges` — the unified "every edge out of a model" view — so a candidate that
-- already carries a typed relationship is flagged has_rel_edge (the campaign's "done"
-- signal), and a pre-existing lineage FK (variant_of/remake_of) is surfaced too.
CREATE OR REPLACE VIEW relationship_candidates AS
  SELECT
    s.id, s.ipdb_id, s.slug, s.name, s.maker, s.maker_slug, s.year, s.label,
    s.by_copy, s.by_conv,
    s.mentions_book_source,
    -- already-authored typed relationship edge(s): the "done" signal.
    EXISTS (SELECT 1 FROM model_relationships r WHERE r.model_id = s.id) AS has_rel_edge,
    COALESCE((
      SELECT list_sort(list_distinct(list(r.relationship_type)))
      FROM model_relationships r WHERE r.model_id = s.id
    ), []::VARCHAR[]) AS rel_types,
    COALESCE((
      SELECT list_sort(list_distinct(list(coalesce(r.target_slug, r.target_label))))
      FROM model_relationships r WHERE r.model_id = s.id
    ), []::VARCHAR[]) AS rel_targets,
    -- a pre-existing structured lineage FK, WITH its kind. The three are not
    -- interchangeable for this campaign: an export_edition_of to the quoted origin is
    -- a different review from a variant_of, and DomainModel.md is explicit that an
    -- export edition is deliberately not a ModelRelationship type (an unauthorized
    -- "export" is a copy, not an export). Collapsing them to a boolean threw that away.
    COALESCE((
      SELECT list_sort(list_distinct(list(l.edge_kind)))
      FROM model_lineage l WHERE l.model_id = s.id
    ), []::VARCHAR[]) AS lineage_kinds,
    EXISTS (SELECT 1 FROM model_lineage l WHERE l.model_id = s.id) AS has_lineage_fk,
    -- INBOUND edges: something else already points AT this model. `model_edges` and
    -- `model_relationships` are outbound-only, so a model whose lineage is recorded
    -- from the far end reads as edge-less here and never leaves the queue. That is
    -- also exactly the reverse-direction case ("Also produced in Germany by …"): the
    -- work may already be done, just stated on the other model. Read as a hint, not a
    -- done signal — has_rel_edge stays outbound, because the campaign's job is to make
    -- a model state its OWN origin.
    EXISTS (
      SELECT 1 FROM model_edges_bidir b
      WHERE b.model_id = s.id AND b.direction = 'in'
    ) AS has_inbound_edge,
    -- best-effort resolved target guess(es) from the quoted titles (hint, not truth).
    COALESCE((
      SELECT list_sort(list_distinct(list(qr.target_slug)))
      FROM _quoted_resolved qr WHERE qr.model_id = s.id
    ), []::VARCHAR[]) AS target_guess,
    -- The campaign's recorded human judgement, carried ON THE ROW so it surfaces
    -- wherever the row is reviewed rather than in a view you must remember to open.
    -- NULL for the vast majority; a held-back verdict or a maker-level license
    -- question when one was recorded (see section 2).
    oq.question   AS open_question,
    mq.question   AS maker_question,
    s.notes, s.notable_features
  FROM _rel_signal s
  LEFT JOIN _rel_open_question  oq ON oq.ipdb_id = s.ipdb_id
  LEFT JOIN _rel_maker_question mq ON mq.manufacturer_slug = s.maker_slug
  WHERE s.by_copy OR s.by_conv;

-- namesake pairing --
-- relationship_namesake_review — pairs of models sharing a name across makers and
-- countries, a few years apart, with no edge between them. This is the campaign's
-- only STRUCTURAL detector: it reads no prose at all, so it sees the derivative
-- whose note never confesses the relationship — the blind spot `edged_models_missed`
-- measures.
--
-- ⚠ It is a RESEARCH queue, NOT an authoring queue, and the distinction is not
-- negotiable. Every edge this campaign writes carries a `cite:` with a verbatim
-- quote; "same name, three years apart, different country" is an INFERENCE and
-- yields no quote, so nothing here can be authored from this view alone. Its job is
-- to point at models worth reading — and, most valuably, to expose phrasings the
-- phrasebook is missing (`text_detector_found_it = false` is that signal).
--
-- The year window is empirically derived, not guessed. Measured against the
-- campaign's own hand-authored edges, cross-country namesake pairs are already
-- linked 27% of the time at a 1-3 year gap, 4% at 4-8, and ZERO beyond 9 years —
-- a name match at a 40-year remove is coincidence (there are four unrelated
-- "Coney Island"s). `namesake_window_drifted` re-checks that shape every run, so
-- the window stops being right the moment the data says otherwise.
CREATE OR REPLACE VIEW relationship_namesake_review AS
  SELECT
    a.id AS model_id,
    a.slug,
    a.label,
    a.manufacturer_slug AS maker,
    a.country_slug      AS country,
    a.year,
    b.slug              AS namesake_slug,
    b.manufacturer_slug AS namesake_maker,
    b.country_slug      AS namesake_country,
    b.year              AS namesake_year,
    a.year - b.year     AS year_gap,
    -- FALSE is the interesting case: a derivative the phrasebook cannot see. Each
    -- one is either a missing phrase or a genuine coincidence; reading a handful is
    -- how the phrasebook grows.
    EXISTS (SELECT 1 FROM relationship_candidates c WHERE c.id = a.id) AS text_detector_found_it
  FROM models a
  JOIN models b
    ON _title_key(a.name) = _title_key(b.name)
   AND b.manufacturer_slug <> a.manufacturer_slug
   AND b.year < a.year
  WHERE _title_key(a.name) <> ''
    AND a.country_slug IS NOT NULL AND b.country_slug IS NOT NULL
    AND a.country_slug <> b.country_slug
    AND a.year - b.year BETWEEN 1 AND 3
    AND NOT EXISTS (
      SELECT 1 FROM model_edges_bidir e
      WHERE e.model_id = a.id AND e.target_id = b.id)
  ORDER BY text_detector_found_it, a.country_slug, a.manufacturer_slug, a.slug;

-- provenance --
-- _rel_edge_claim — one row per (live model, relationship claim): WHO asserted each
-- edge, in which patch, and whether external evidence was attached. This is the
-- attribution JOIN the foundation prescribes — provenance is never a column on a
-- grain view — and it is what turns "this edge looks wrong" into "this edge was
-- asserted by X in patch Y citing nothing".
--
-- Read via `model_claims`, NOT `claims`: the latter is deliberately not live-filtered,
-- and this campaign works over live models only.
--
-- Two traps the foundation documents and this view preserves rather than papering
-- over: `rank IS NULL` means the claim is INELIGIBLE (inactive, or a suppressed
-- actor), which is a different thing from ranking last; and `member_exists = false`
-- is a TOMBSTONE — an actor asserting the edge is ABSENT — which the resolved
-- `model_relationships` view cannot show at all. Both are surfaced, not filtered.
CREATE OR REPLACE VIEW _rel_edge_claim AS
  SELECT
    c.model_id,
    c.claim_id,
    c.ref_id AS target_id,
    c.rank,
    c.member_exists,
    c.ingest_source_slug,
    c.patch_id,
    c.changeset_action,
    c.created_at,
    json_extract_string(c.value, '$.relationship_type') AS claimed_type,
    json_extract_string(c.value, '$.license_status')    AS claimed_license,
    EXISTS (SELECT 1 FROM claim_citations cc WHERE cc.claim_id = c.claim_id) AS cited
  FROM model_claims c
  WHERE c.field_name = 'model_relationship';

-- _rel_edge_provenance — the per-MODEL rollup of the above, so it can ride on a
-- review row without breaking its one-row-per-model grain. Counting stays here;
-- drill into _rel_edge_claim for the per-edge detail.
CREATE OR REPLACE VIEW _rel_edge_provenance AS
  SELECT
    model_id,
    list_sort(list_distinct(list(ingest_source_slug)))             AS edge_sources,
    list_sort(list_distinct(list(patch_id)))                       AS edge_patches,
    count(*) FILTER (WHERE NOT cited)                              AS n_uncited,
    count(*) FILTER (WHERE NOT member_exists)                      AS n_tombstoned,
    count(*) FILTER (WHERE rank IS NULL)                           AS n_ineligible,
    -- an edge hand-edited in the admin rather than authored as a data patch
    count(*) FILTER (WHERE patch_id IS NULL)                       AS n_interactive,
    -- two eligible sources disagreeing about authorization on the same model: the
    -- exact "wrong existing value" the audit exists to surface.
    count(DISTINCT claimed_license) FILTER (WHERE rank IS NOT NULL) > 1
                                                                   AS license_disagreement
  FROM _rel_edge_claim
  GROUP BY model_id;

-- relationship_uncited_edges — live relationship edges carrying NO external evidence.
-- The campaign has an elaborate apparatus for citing the edges it AUTHORS and had
-- none for finding the edges already in the catalog that were never cited; this is
-- that queue. Authorization claims sort first: an uncited licensed/unlicensed edge
-- asserts something no source was ever recorded for.
--
-- "Uncited", never "unsourced" — the foundation is explicit that an absent citation
-- means no EXTERNAL EVIDENCE was recorded, not that the claim is unattributed. Every
-- row here has an ingest source; what it lacks is a citation.
CREATE OR REPLACE VIEW relationship_uncited_edges AS
  SELECT
    m.slug,
    m.label,
    m.manufacturer_name AS maker,
    t.slug AS target_slug,
    ec.claimed_type,
    ec.claimed_license,
    ec.ingest_source_slug,
    ec.patch_id,
    ec.created_at
  FROM _rel_edge_claim ec
  JOIN models m      ON m.id = ec.model_id
  LEFT JOIN models t ON t.id = ec.target_id
  WHERE NOT ec.cited
    AND ec.rank = 1
    AND ec.member_exists
  ORDER BY ec.claimed_license = 'unknown', m.manufacturer_name NULLS LAST, m.label;

-- review --
-- The actionable queue: candidates with lineage language but NO typed edge yet.
-- Rows carrying a recorded open question float to the very top (a prior reviewer
-- already looked and held back — read that before re-deciding), then rows with a
-- resolved target guess (author-ready); guess-less rows need a source read to name
-- the origin. Full note text inline so no re-fetch is needed.
CREATE OR REPLACE VIEW relationship_review AS
  SELECT
    id, ipdb_id, label, maker,
    CASE WHEN by_copy AND by_conv THEN 'copy+conv'
         WHEN by_copy             THEN 'copy'
         ELSE 'conv' END AS signal,
    (len(target_guess) > 0) AS has_guess,
    target_guess,
    has_lineage_fk,
    open_question, maker_question,
    lineage_kinds, has_inbound_edge,
    notes, notable_features
  FROM relationship_candidates
  WHERE NOT has_rel_edge
  ORDER BY (open_question IS NOT NULL) DESC,
           (maker_question IS NOT NULL) DESC,
           (len(target_guess) > 0) DESC, maker NULLS LAST, label;

-- Possible wrong EXISTING edges: a model whose existing edge resolves to a catalog
-- model, but NONE of its resolved-slug targets appears among the note's quoted
-- origins. That's the sweep's specialty (a set-but-unsupported / conflict candidate)
-- pre-surfaced by SQL — a review aid, not a verdict: the note may name the origin
-- unquoted, or the first quoted title may not be the true donor. Restricted to edges
-- with a RESOLVED target (target_slug): a label-only edge (target_label, an unnamed or
-- plural donor like "unknown Bally donor machines") has no slug to compare and would
-- false-flag every time, so it is excluded by the has-a-resolved-target requirement.
--
-- PROVENANCE rides on every row. Judging a suspect edge from the resolved catalog
-- alone means judging it blind: an edge this campaign authored in 0127 citing a
-- verbatim IPDB quote and a hand-edit with no evidence at all look identical once
-- resolved. `edge_sources` / `edge_patches` name who asserted it, `n_uncited` says
-- whether anything backs it, `license_disagreement` catches two eligible sources
-- contradicting each other on authorization, and `n_tombstoned` / `n_ineligible`
-- surface the two states the resolved view structurally cannot show.
CREATE OR REPLACE VIEW relationship_edged_audit AS
  SELECT
    c.id, c.ipdb_id, c.label, c.maker,
    c.rel_types, c.rel_targets, c.target_guess,
    p.edge_sources, p.edge_patches,
    p.n_uncited, p.n_interactive, p.n_tombstoned, p.n_ineligible,
    p.license_disagreement,
    -- a recorded held-back verdict on an ALREADY-edged model is the loudest signal
    -- here: someone judged this undecidable, yet an edge exists. Verify which.
    c.open_question, c.maker_question,
    c.notes
  FROM relationship_candidates c
  LEFT JOIN _rel_edge_provenance p ON p.model_id = c.id
  WHERE c.has_rel_edge
    AND len(c.target_guess) > 0
    -- at least one existing edge resolves to a catalog model (not a bare label)
    AND EXISTS (
      SELECT 1 FROM model_relationships r
      WHERE r.model_id = c.id AND r.target_slug IS NOT NULL
    )
    -- ...yet none of those resolved targets is a quoted origin in the note
    AND NOT EXISTS (
      SELECT 1 FROM model_relationships r
      JOIN _quoted_resolved qr ON qr.model_id = c.id AND qr.target_slug = r.target_slug
      WHERE r.model_id = c.id AND r.target_slug IS NOT NULL
    )
  ORDER BY (c.open_question IS NOT NULL) DESC, c.maker NULLS LAST, c.label;

-- The campaign's recorded open decisions against their CURRENT catalog state. Read
-- this before authoring any of these models: a held-back row that now carries an
-- edge means the question was resolved OR authored past — `edged`/`rel_targets` say
-- which, `question` says what the hold was about. Maker-level questions are listed
-- with the count of that maker's edges they bear on.
CREATE OR REPLACE VIEW relationship_open_questions AS
  SELECT
    'model' AS scope, q.slug AS subject, q.kind, m.label,
    EXISTS (SELECT 1 FROM model_relationships r WHERE r.model_id = m.id) AS edged,
    COALESCE((
      SELECT list_sort(list_distinct(list(coalesce(r.target_slug, r.target_label))))
      FROM model_relationships r WHERE r.model_id = m.id
    ), []::VARCHAR[]) AS rel_targets,
    q.question
  FROM _rel_open_question q
  LEFT JOIN models m ON m.ipdb_id = q.ipdb_id
  UNION ALL
  SELECT
    'maker', mq.manufacturer_slug, 'license-status', NULL,
    EXISTS (SELECT 1 FROM models m2 JOIN model_relationships r ON r.model_id = m2.id
             WHERE m2.manufacturer_slug = mq.manufacturer_slug),
    COALESCE((
      SELECT list_sort(list_distinct(list(r.license_status)))
      FROM models m2 JOIN model_relationships r ON r.model_id = m2.id
      WHERE m2.manufacturer_slug = mq.manufacturer_slug
    ), []::VARCHAR[]),
    mq.question
  FROM _rel_maker_question mq
  ORDER BY scope, subject;

-- quote --
-- A first-cut VERBATIM cite quote, extracted from the note rather than hand-typed.
--
-- `note_norm` is the note put through exactly the normalization
-- scripts/quote_verify/verify_quotes.py applies to the SOURCE side: the four smart
-- quotes straightened and whitespace runs collapsed (the quote itself must already
-- be in that form). Backticks are deliberately NOT straightened — IPDB writes
-- `Title' and verify_quotes doesn't touch them either, so straightening here would
-- break the match. Pinexplore's ipdb_machines corpus (what verify_quotes actually
-- checks against) and the catalog's ipdb.notes come from the same IPDB pull, so an
-- exact substring of one is an exact substring of the other.
--
-- `lineage_sentence` is the single sentence carrying the lineage claim: a run of
-- non-period characters spanning a lineage phrase, up to its terminating period. The
-- non-period run is what bounds it to ONE sentence; the cost is that an abbreviation
-- inside the sentence (A.M.I.) truncates it, which the green tier below catches by
-- requiring the target's name to survive inside the extracted span.
--
-- This is a PROPOSAL, not a verified quote: `make verify-quotes` is the independent
-- gate that proves each one verbatim against pinexplore's corpus. Never ship an
-- extracted quote that hasn't passed it.
-- The extractor reads NOTABLE FEATURES then NOTES, joined by a newline — exactly the
-- slice and the order `ipdb_notes_text()` in scripts/quote_verify/verify_quotes.py
-- builds for an `ipdb:` ref, so an extracted span is a substring of the very text the
-- gate will check it against. `description` is deliberately NOT read even though the
-- detectors fire on it: it is flipcommons-authored prose, not IPDB's, so a span taken
-- from it could never verify under an `ipdb:` cite. A candidate detected only there
-- is disqualified explicitly (see the `description-only` reject reason) rather than
-- falling out of the tier through an empty quote.
--
-- The regex is CASE-INSENSITIVE. A large share of this corpus opens the note with the
-- phrase — "Copy of Williams' 1974 'Strato-Flite'." — and a case-sensitive class
-- silently extracts nothing from every one of them (anchor_quote_sentence_initial).
CREATE OR REPLACE VIEW _rel_quote AS
  SELECT
    s.id,
    trim(regexp_extract(nn.note_norm,
      '(?i)([^.]*(' || _copy_phrase_re() || '|' || _conv_phrase_re() || ')[^.]*\.)', 1)) AS lineage_sentence,
    nn.note_norm
  FROM _rel_signal s,
       LATERAL (SELECT regexp_replace(
         replace(replace(replace(replace(
           concat_ws(chr(10), nullif(s.notable_features, ''), nullif(s.notes, '')),
           '“', '"'), '”', '"'), '‘', ''''), '’', ''''),
         '\s+', ' ', 'g') AS note_norm) nn;

-- The CERTAIN tier: rows safe to author with minimal per-row reading.
--
-- Every condition below removes a way the row could be wrong:
--   not already edged        — there is something to author
--   no recorded open question — no prior reviewer held this back
--   exactly ONE resolved target — no "which Star Trek?" ambiguity
--   a lineage sentence extracted, and SHORT — one clean claim, not a paragraph
--   the target's NAME appears inside that sentence — ties the quote to the target,
--        and incidentally proves the sentence wasn't truncated by an abbreviation
--
-- relationship_type is read off the phrase. license_status follows the campaign's
-- standing discipline (README + TOOL-NOTES DEFECT 11): a note establishes the COPY,
-- not the AUTHORIZATION, so the default is `unknown` and `licensed`/`unlicensed` are
-- claimed ONLY when the sentence says so in words the quote itself carries.
-- Still spot-check a sample against the full note before authoring — this is a
-- high-confidence queue, not an oracle.
-- _green_scored — the certain-tier shortlist with its DISQUALIFIERS computed. A row
-- with reject_reason IS NULL is green; anything else is routed to
-- relationship_green_rejected so the exclusion stays auditable instead of silent.
-- The three reasons are all false-positive classes observed in the real output:
--   component-copy  the note says a COMPONENT is a copy ("the backglass is a near
--                   copy of", "the playfield layout is a copy of"), not the machine.
--                   This is TOOL-NOTES DEFECT 7 — artwork reuse misjudged as a
--                   machine copy. Structural components (playfield/layout/cabinet)
--                   are often real lineage, but "often" is not "certain": they go to
--                   review for a human call, not into the author-blind queue.
--   hedged          the note HEDGES the claim — "a near copy of", "probably a copy
--                   of", "appears to be". The relationship may well be real, but a
--                   hedged source cannot support a flat catalog assertion, and the
--                   quote would visibly undercut the claim it is cited for. These
--                   need a corroborating source, not a faster author path.
--   book-source     the note attributes to a BOOK, so the claim wants a second cite
--                   to that book alongside the ipdb: one — which `cite:` cannot
--                   express today (no book ref form; see mentions_book_source).
--                   Held out until flipcommons supports it, rather than shipping a
--                   claim cited only to the proximate source.
--   reverse-direction  the note is on the ORIGINAL, describing who copied IT ("Also
--                   produced in Germany by Bally Wulff under license from Bally
--                   Midway"). The edge belongs on the OTHER model, pointing back;
--                   authoring it here inverts the lineage.
--   mojibake        the extracted span carries a U+FFFD replacement character. It
--                   would still verify (pinexplore's corpus has the same damage from
--                   the same IPDB pull), but shipping a visible `?` in a public quote
--                   is a human call — usually the `[...]` omission marker instead.
CREATE OR REPLACE VIEW _green_scored AS
  SELECT
    c.id, c.ipdb_id, c.slug, c.label, c.maker,
    c.target_guess[1] AS target_machine,
    CASE
      WHEN regexp_matches(q.lineage_sentence, '(?i)conversion kit')            THEN 'conversion_kit'
      -- "conversion FOR X" is IPDB's 1940s phrasing and means the same as
      -- "conversion OF X". It was in the membership detector but not here, so three
      -- plainly-stated conversions were typed `copy` by the ELSE branch.
      WHEN regexp_matches(q.lineage_sentence,
             '(?i)conversion of|conversion for|converted (game )?(for|from)') THEN 'conversion'
      WHEN regexp_matches(q.lineage_sentence, '(?i)repaint of')                THEN 'retheme'
      ELSE 'copy'
    END AS relationship_type,
    CASE
      WHEN regexp_matches(q.lineage_sentence, '(?i)unauthori[sz]ed|unlicensed|bootleg') THEN 'unlicensed'
      -- "a licensed version of X" says so as plainly as "under licence" does. Checked
      -- after the unlicensed branch so "unlicensed version of" can never reach it.
      WHEN regexp_matches(q.lineage_sentence,
             '(?i)under licen|built under licen|licen[cs]ed (build|copy|version|reproduction) of')
        THEN 'licensed'
      ELSE 'unknown'
    END AS license_status,
    q.lineage_sentence AS quote,
    CASE
      -- component-copy: the note says a COMPONENT resembles another game, not the
      -- machine. The asset noun must PRECEDE the verb — an asset noun after it is
      -- normal in a genuine copy ("a copy of 'Vulcan' except the backglass depicts
      -- a woman"). The verb list tracks the phrasebook: the new phrasings are far
      -- MORE prone to this than "copy of" was, because "the backglass is identical
      -- to X" is one of IPDB's most common sentences. Filtering ~60% of the
      -- "identical to" hits, all of them genuine component talk.
      -- NEGATED: the sentence says the games are NOT alike. "very similar but not
      -- identical to X" contains the phrase "identical to" and asserts its opposite,
      -- so a naive phrase match reads the note exactly backwards. Checked FIRST —
      -- ahead of every other reason — because a negated sentence is not weak
      -- evidence for the claim, it is evidence against it.
      WHEN regexp_matches(q.lineage_sentence,
             '(?i)not identical|not a copy|not a conversion|isn''t|is not (a |an )?(copy|conversion)')
        THEN 'negated'
      WHEN regexp_matches(q.lineage_sentence,
             '(?i)(backglass|artwork|art work|playfield|cabinet|layout|score ?card|plastics'
             || '|glass|flipper|backdrop|advert|\bad\b)'
             -- verb forms too, not just nouns: "Playfield adapted from X" is a
             -- component claim and `adaptation` alone does not match `adapted`.
             || '[^.]{0,60}(copy|copied|identical|version|modification|adaptation|adapted|design)')
        THEN 'component-copy'
      WHEN regexp_matches(q.lineage_sentence,
             '(?i)near[- ]?copy|near(ly)?[- ]identical|almost identical|probabl|possibl|apparentl'
             -- the new phrasings attract their own hedges: IPDB writes "appears
             -- identical to" and "looks identical to" as readily as "appears to be".
             || '|appears (to|identical)|looks identical|very similar|seems to|may be|might be'
             || '|likely|reportedly|believed|thought to be|said to be')
        THEN 'hedged'
      -- reverse-direction: the prose test, plus the STRUCTURAL one. A model that is
      -- already the target of somebody's edge is very likely the original being
      -- described, not a derivative to author — the prose heuristic alone misses
      -- every reverse note that doesn't use the "also produced" formula.
      WHEN regexp_matches(q.lineage_sentence, '(?i)also (produced|made|released|manufactured)')
        OR c.has_inbound_edge
        THEN 'reverse-direction'
      -- RECIPROCAL: the model this row points at points straight back. At most one
      -- direction can be true — X cannot be a copy of Y while Y is a copy of X — so
      -- neither is author-ready until someone establishes which came first.
      --
      -- Ordered AFTER reverse-direction deliberately. A reverse-direction note ("Also
      -- produced in Germany by …") often ALSO satisfies this test, and of the two
      -- labels reverse-direction is the actionable one: it tells the reviewer the edge
      -- belongs on the other model, pointing back. Putting this branch first relabelled
      -- all three genuine reverse rows as reciprocal and sent the reviewer hunting for
      -- a mutual pair that was not there.
      WHEN EXISTS (
             SELECT 1 FROM _quoted_resolved qr
             JOIN models m2 ON m2.id = qr.model_id
             WHERE m2.slug = c.target_guess[1] AND qr.target_slug = c.slug)
        THEN 'reciprocal-pair'
      WHEN c.mentions_book_source
        THEN 'book-source'
      WHEN q.lineage_sentence LIKE '%' || chr(65533) || '%'
        THEN 'mojibake'
      WHEN q.lineage_sentence = ''
        THEN 'no-quote-extracted'
    END AS reject_reason,
    c.notes
  FROM relationship_candidates c
  JOIN _rel_quote q ON q.id = c.id
  JOIN models t     ON t.slug = c.target_guess[1]
  WHERE NOT c.has_rel_edge
    AND c.open_question IS NULL
    AND len(c.target_guess) = 1
    -- A row with NO extracted quote stays in the shortlist so it can carry the
    -- `no-quote-extracted` reject reason. Filtering it here instead would drop it from
    -- relationship_green AND relationship_green_rejected, which is the silent
    -- exclusion the rejected view exists to prevent. The quote-quality gates below
    -- therefore apply only once there IS a quote to judge.
    AND (q.lineage_sentence = '' OR (
          length(q.lineage_sentence) BETWEEN 20 AND 220
          -- the target's name must survive inside the extracted sentence, keyed the
          -- same way the resolver keyed it so the two can't drift apart
          AND _title_key(q.lineage_sentence) LIKE '%' || _title_key(t.name) || '%'))
  ORDER BY c.maker NULLS LAST, c.label;

-- The certain tier itself: shortlist minus the disqualified. These are the rows
-- safe to author with a spot-check rather than a per-row source read.
CREATE OR REPLACE VIEW relationship_green AS
  SELECT * EXCLUDE (reject_reason)
  FROM _green_scored WHERE reject_reason IS NULL
  ORDER BY maker NULLS LAST, label;

-- The disqualified rows, with the reason — auditable, and a real review queue in
-- its own right (a component-copy or reverse-direction row is usually a GENUINE
-- relationship, just not the one the naive read would have authored).
CREATE OR REPLACE VIEW relationship_green_rejected AS
  SELECT reject_reason, id, ipdb_id, label, maker,
         target_machine, relationship_type, quote, notes
  FROM _green_scored WHERE reject_reason IS NOT NULL
  ORDER BY reject_reason, maker NULLS LAST, label;

-- feed --
-- The AI-corpus-sweep candidate feed: one row per not-yet-edged candidate, keyed on
-- the stable ipdb number, with the resolved target guess as `hint`. This REPLACES the
-- Worklist read in emit_candidates.py — dump it as JSON (`Q=... ARGS=--format json`)
-- and adapt to the sweep's {ipdb_id, hint} contract. Only ipdb-keyed rows: the sweep
-- resolves and judges an IPDB note, so a candidate with no ipdb_id can't ride it (a
-- handful surface in relationship_review for hand authoring instead).
-- `maker_slug` rides along so the emitter can key its maker-level evidence off the
-- foundation's live-filtered `models.manufacturer_slug` instead of re-walking
-- machinemodel -> corporateentity -> manufacturer over raw SQLite, which is neither
-- live-filtered nor gated by this analysis's checks.
CREATE OR REPLACE VIEW relationship_sweep_candidates AS
  SELECT c.ipdb_id, c.slug, c.maker_slug, c.target_guess AS hint
  FROM relationship_candidates c
  WHERE NOT c.has_rel_edge AND c.ipdb_id IS NOT NULL
  ORDER BY c.ipdb_id;

-- == 4 · SUMMARY & CHECKS ====================================================
-- The honest-prose tail. Numbers any write-up quotes come from relationships_summary,
-- never hand-counted; relationships_checks is empty when healthy.

-- The acceptance question this trial answers: (1) do the detectors REPRODUCE the
-- already-authored edges (coverage_* below — recall vs the campaign's own ground
-- truth; the residual is edges authored from sources the IPDB-note detector can't
-- see, e.g. web-cache), and (2) how big is the NOT-edged tail vs the frozen
-- Worklist's belief that 56 remain (not_edged below).
CREATE OR REPLACE VIEW relationships_summary AS
            SELECT 'candidates'        AS metric, count(*) AS value FROM relationship_candidates
  UNION ALL SELECT 'by_copy',          count(*) FILTER (WHERE by_copy)            FROM relationship_candidates
  UNION ALL SELECT 'by_conv',          count(*) FILTER (WHERE by_conv)            FROM relationship_candidates
  UNION ALL SELECT 'by_both',          count(*) FILTER (WHERE by_copy AND by_conv) FROM relationship_candidates
  -- edged vs not: the not-edged set is the actionable remaining work.
  UNION ALL SELECT 'edged',            count(*) FILTER (WHERE has_rel_edge)       FROM relationship_candidates
  UNION ALL SELECT 'not_edged',        count(*) FILTER (WHERE NOT has_rel_edge)   FROM relationship_candidates
  UNION ALL SELECT 'not_edged_with_guess',
    count(*) FILTER (WHERE NOT has_rel_edge AND len(target_guess) > 0)            FROM relationship_candidates
  UNION ALL SELECT 'not_edged_no_guess',
    count(*) FILTER (WHERE NOT has_rel_edge AND len(target_guess) = 0)            FROM relationship_candidates
  UNION ALL SELECT 'not_edged_no_ipdb',
    count(*) FILTER (WHERE NOT has_rel_edge AND ipdb_id IS NULL)                  FROM relationship_candidates
  -- Coverage: of every model that ALREADY carries a typed edge, how many does the
  -- detector union catch? The residual = edges the note-phrase detector can't
  -- reproduce (authored from web/other sources). This is the recall check.
  UNION ALL SELECT 'edged_models_total',
    (SELECT count(DISTINCT model_id) FROM model_relationships)
  UNION ALL SELECT 'edged_models_covered',
    (SELECT count(*) FROM (
       SELECT DISTINCT model_id FROM model_relationships
       INTERSECT SELECT id FROM relationship_candidates))
  UNION ALL SELECT 'edged_models_missed',
    (SELECT count(*) FROM (
       SELECT DISTINCT model_id FROM model_relationships
       EXCEPT SELECT id FROM relationship_candidates))
  UNION ALL SELECT 'edged_audit_flagged', count(*)                               FROM relationship_edged_audit
  -- Recorded human judgement carried on candidate rows (see section 2).
  UNION ALL SELECT 'open_question_rows',  count(*) FILTER (WHERE open_question IS NOT NULL)  FROM relationship_candidates
  UNION ALL SELECT 'maker_question_rows', count(*) FILTER (WHERE maker_question IS NOT NULL) FROM relationship_candidates
  -- The certain tier: not-edged rows with one unambiguous target and an extracted quote.
  UNION ALL SELECT 'green',            count(*)                                   FROM relationship_green
  UNION ALL SELECT 'green_copy',       count(*) FILTER (WHERE relationship_type = 'copy')           FROM relationship_green
  UNION ALL SELECT 'green_conversion', count(*) FILTER (WHERE relationship_type = 'conversion')     FROM relationship_green
  UNION ALL SELECT 'green_conv_kit',   count(*) FILTER (WHERE relationship_type = 'conversion_kit') FROM relationship_green
  UNION ALL SELECT 'green_retheme',    count(*) FILTER (WHERE relationship_type = 'retheme')        FROM relationship_green
  UNION ALL SELECT 'green_licensed',   count(*) FILTER (WHERE license_status = 'licensed')          FROM relationship_green
  UNION ALL SELECT 'green_unlicensed', count(*) FILTER (WHERE license_status = 'unlicensed')        FROM relationship_green
  -- Disqualified from the certain tier (still real candidates — see the rejected view).
  UNION ALL SELECT 'green_rejected',           count(*)                                        FROM relationship_green_rejected
  UNION ALL SELECT 'green_rej_component',      count(*) FILTER (WHERE reject_reason = 'component-copy')    FROM relationship_green_rejected
  UNION ALL SELECT 'green_rej_hedged',         count(*) FILTER (WHERE reject_reason = 'hedged')            FROM relationship_green_rejected
  UNION ALL SELECT 'green_rej_reverse',        count(*) FILTER (WHERE reject_reason = 'reverse-direction') FROM relationship_green_rejected
  UNION ALL SELECT 'green_rej_book',           count(*) FILTER (WHERE reject_reason = 'book-source')       FROM relationship_green_rejected
  -- Candidates whose note attributes to a book (blocked on a book cite form upstream).
  UNION ALL SELECT 'book_source_candidates',   count(*) FILTER (WHERE mentions_book_source)                FROM relationship_candidates
  UNION ALL SELECT 'green_rej_mojibake',       count(*) FILTER (WHERE reject_reason = 'mojibake')          FROM relationship_green_rejected
  -- No ipdb-citable quote could be extracted — almost always a candidate detected
  -- only via `description`, which no `ipdb:` cite can verify against.
  UNION ALL SELECT 'green_rej_no_quote',        count(*) FILTER (WHERE reject_reason = 'no-quote-extracted') FROM relationship_green_rejected
  UNION ALL SELECT 'green_rej_negated',         count(*) FILTER (WHERE reject_reason = 'negated')            FROM relationship_green_rejected
  UNION ALL SELECT 'green_rej_reciprocal',      count(*) FILTER (WHERE reject_reason = 'reciprocal-pair')    FROM relationship_green_rejected
  -- The structural (prose-free) queue, and the share of it the phrasebook cannot see.
  -- A rising `namesake_unseen_by_text` is the signal that the phrasebook has another
  -- gap worth reading for.
  UNION ALL SELECT 'namesake_pairs',            count(*)                                        FROM relationship_namesake_review
  UNION ALL SELECT 'namesake_unseen_by_text',   count(*) FILTER (WHERE NOT text_detector_found_it) FROM relationship_namesake_review
  -- Provenance of the edges already in the catalog.
  UNION ALL SELECT 'uncited_edges',             count(*)                                       FROM relationship_uncited_edges
  UNION ALL SELECT 'uncited_licensed_edges',    count(*) FILTER (WHERE claimed_license <> 'unknown') FROM relationship_uncited_edges
  UNION ALL SELECT 'edges_interactive',         count(*) FILTER (WHERE patch_id IS NULL)        FROM relationship_uncited_edges
  UNION ALL SELECT 'edged_audit_license_disagreement', count(*) FILTER (WHERE license_disagreement) FROM relationship_edged_audit
  -- Candidates already pointed AT by another model's edge (the reverse-direction set).
  UNION ALL SELECT 'not_edged_inbound_only',    count(*) FILTER (WHERE has_inbound_edge)        FROM relationship_review
  -- The BOOK-CITE BLOCKER, upstream side. These move when flipcommons grows a book
  -- ref form; until then the campaign's book-attributed rows stay held out. Reported
  -- from citation_roots so nobody has to remember to re-check by hand.
  UNION ALL SELECT 'book_roots_seeded',         count(*)                       FROM citation_roots WHERE citation_source_type = 'book'
  UNION ALL SELECT 'book_roots_matchable',      count(*)                       FROM _rel_book_phrase
  UNION ALL SELECT 'book_root_cited_claims',    coalesce(sum(n_cited_claims), 0) FROM citation_roots WHERE citation_source_type = 'book'
  ORDER BY metric;

-- relationships_checks — invariants that should always hold. Empty = healthy; any
-- row is a problem to investigate. Three classes (scripts/analysis/README.md):
--   Structural : every candidate fires >=1 detector; the sweep feed keys on ipdb.
--   Vocabulary : every resolved target guess is a live model slug.
--   Anchors    : each detector still fires on a known example — the only class that
--                catches a WHOLE detector going dark (a rotted regex, a renamed
--                foundation column), which a row-level invariant can't see.
CREATE OR REPLACE VIEW relationships_checks AS
  -- Structural: every candidate is caught by at least one detector.
            SELECT 'candidate_without_detector' AS check, c.id, c.label AS detail
            FROM relationship_candidates c
            WHERE NOT (c.by_copy OR c.by_conv)
  -- Vocabulary: every resolved target guess must be a live model slug.
  UNION ALL SELECT 'guess_not_a_model', c.id, g
            FROM relationship_candidates c, UNNEST(c.target_guess) AS t(g)
            WHERE g NOT IN (SELECT slug FROM models)
  -- Structural: a sweep-feed row must carry a non-null ipdb_id (its whole key).
  UNION ALL SELECT 'sweep_feed_without_ipdb', f.slug::VARCHAR, NULL
            FROM relationship_sweep_candidates f
            WHERE f.ipdb_id IS NULL
  -- Anchor: the copy detector still fires on Maresa's Spin Out
  -- ("This is a copy of Gottlieb's 1975 'Spin Out'.").
  UNION ALL SELECT 'anchor_copy_dark', NULL::BIGINT, 'spin-out-maresa no longer hits by_copy'
            WHERE NOT EXISTS (SELECT 1 FROM _rel_signal WHERE slug = 'spin-out-maresa' AND by_copy)
  -- Anchor: the conversion detector still fires on Bamboo
  -- ("This is a conversion of Bally's 1967 'Orient'.").
  UNION ALL SELECT 'anchor_conv_dark', NULL::BIGINT, 'bamboo no longer hits by_conv'
            WHERE NOT EXISTS (SELECT 1 FROM _rel_signal WHERE slug = 'bamboo' AND by_conv)
  -- Anchor: the quoted-origin resolver still resolves a known target (Only Star's
  -- note quotes Gottlieb's 'Star Trek', which is a live model).
  UNION ALL SELECT 'anchor_guess_dark', NULL::BIGINT, 'the quoted-origin resolver matched zero targets'
            WHERE NOT EXISTS (SELECT 1 FROM _quoted_resolved)
  -- Anchor: _title_key must stay separator-insensitive. IPDB writes 'Sun Beam' where
  -- the catalog has Sunbeam, and a key that collapses punctuation to a space instead
  -- of squeezing it loses every such pair silently (bare name_norm() did exactly
  -- that). Both spellings must key alike.
  UNION ALL SELECT 'title_key_separator_significant', NULL::BIGINT,
                   'Sun Beam / Sunbeam no longer key alike'
            WHERE _title_key('Sun Beam') <> _title_key('Sunbeam')
  -- Anchor: _title_key must stay accent-folding, the half with no live instance to
  -- catch it. A local ASCII class keys these apart and would silently lose the
  -- Spanish-maker cohort the moment one enters the corpus.
  UNION ALL SELECT 'title_key_accent_significant', NULL::BIGINT,
                   'Competicion / Competición no longer key alike'
            WHERE _title_key('Competicion Penalty') <> _title_key('Competición Penalty')
  -- Discipline: no NEW uncited authorization claim. A licensed/unlicensed edge
  -- asserts something a bare "copy of" note cannot establish, so it must carry
  -- evidence. The four pre-rule rows are held in _rel_uncited_licensed_known so this
  -- gates regressions without gating the backlog.
  UNION ALL SELECT 'uncited_licensed_edge', NULL::BIGINT, u.slug || ' -> ' || coalesce(u.target_slug, '?')
            FROM relationship_uncited_edges u
            WHERE u.claimed_license <> 'unknown'
              AND NOT EXISTS (
                SELECT 1 FROM _rel_uncited_licensed_known k
                WHERE k.slug = u.slug AND k.target_slug IS NOT DISTINCT FROM u.target_slug)
  -- Staleness: a recorded backlog row that has since been cited, retracted or
  -- reslugged. The exception list must not outlive the rows it excuses.
  UNION ALL SELECT 'stale_uncited_licensed', NULL::BIGINT, k.slug || ' -> ' || k.target_slug
            FROM _rel_uncited_licensed_known k
            WHERE NOT EXISTS (
              SELECT 1 FROM relationship_uncited_edges u
              WHERE u.slug = k.slug AND u.target_slug IS NOT DISTINCT FROM k.target_slug
                AND u.claimed_license <> 'unknown')
  -- Vocabulary: every generic-book exception must still name a seeded book, or the
  -- exception is silently excusing nothing.
  UNION ALL SELECT 'unlisted_generic_book', NULL::BIGINT, g.root_citation_source_name
            FROM _rel_generic_book g
            WHERE NOT EXISTS (
              SELECT 1 FROM citation_roots r
              WHERE r.citation_source_type = 'book'
                AND r.root_citation_source_name = g.root_citation_source_name)
  -- Coverage: every seeded book is either matchable as free text or explicitly
  -- excepted. This is what makes the derived list self-maintaining — a newly seeded
  -- book cannot go undetected without someone deciding, on the record, that it is
  -- too generic to hunt for.
  UNION ALL SELECT 'unmatched_book_title', NULL::BIGINT, r.root_citation_source_name
            FROM citation_roots r
            WHERE r.citation_source_type = 'book'
              AND r.root_citation_source_name NOT IN (SELECT root_citation_source_name FROM _rel_generic_book)
              AND r.root_citation_source_name NOT IN (SELECT title FROM _rel_book_phrase)
  -- Structural: the extractor must know every phrase the detectors know. A phrase in
  -- either detector that the extractor cannot find leaves a candidate with no quote,
  -- which is the silent-drop shape this file has already been bitten by twice. Tested
  -- by construction — both read the same macros — so this fires only if someone
  -- inlines a phrase into one side.
  UNION ALL SELECT 'phrase_not_extractable', NULL::BIGINT, 'detector and extractor phrasebooks differ'
            WHERE NOT regexp_matches('probe copy of probe',
                        '(?i)([^.]*(' || _copy_phrase_re() || '|' || _conv_phrase_re() || ')[^.]*)')
  -- Anchors: each phrasebook entry still matches a real note. One per phrase added by
  -- the namesake sweep, pinned to the specimen that motivated it — these are new
  -- vocabulary with no track record, so a rot here would go unnoticed longest.
  UNION ALL SELECT 'anchor_phrase_' || p.name, NULL::BIGINT, p.name || ' matched no live model'
            FROM (VALUES
                   ('identical_to',      'identical to'),
                   ('customized_version','customi[sz]ed version of'),
                   ('modification_of',   'a modification of'),
                   ('adaptation_of',     'an adaptation of|adapted from'),
                   ('same_design_as',    'same design as')
                 ) AS p(name, re)
            WHERE NOT EXISTS (
              SELECT 1 FROM _rel_signal s
              WHERE regexp_matches(lower(concat_ws(' ', coalesce(s.notes, ''),
                                                        coalesce(s.notable_features, ''),
                                                        coalesce(s.description, ''))), p.re))
  -- Calibration: the namesake window must keep tracking reality. If cross-country
  -- namesake pairs at a 1-3 year gap ever stop being meaningfully more linked than
  -- distant ones, the window is no longer evidence of anything and the view is
  -- selling noise as a lead. Compares the near band against the 16+ band.
  UNION ALL SELECT 'namesake_window_drifted', NULL::BIGINT,
                   'near-gap namesake pairs are no better linked than distant ones'
            FROM (
              SELECT
                avg(CASE WHEN gap BETWEEN 1 AND 3 THEN linked::INT END) AS near,
                avg(CASE WHEN gap >= 16          THEN linked::INT END) AS far
              FROM (
                SELECT a.year - b.year AS gap,
                       EXISTS (SELECT 1 FROM model_edges_bidir e
                               WHERE e.model_id = a.id AND e.target_id = b.id) AS linked
                FROM models a JOIN models b
                  ON _title_key(a.name) = _title_key(b.name)
                 AND b.manufacturer_slug <> a.manufacturer_slug AND b.year < a.year
                WHERE _title_key(a.name) <> ''
                  AND a.country_slug IS NOT NULL AND b.country_slug IS NOT NULL
                  AND a.country_slug <> b.country_slug)
            ) w
            WHERE w.near IS NULL OR w.near <= coalesce(w.far, 0)
  -- Anchor: the DERIVED book-title arm still matches real prose. The `\bbook\b`
  -- catch-all masks it in the headline count, so a broken derivation (an empty
  -- citation_roots read, a stem rule that over-trims) would look like no change at
  -- all while silently reverting to the old four-title coverage.
  UNION ALL SELECT 'anchor_book_title_dark', NULL::BIGINT,
                   'no seeded book title matched any model prose'
            WHERE NOT EXISTS (
              SELECT 1 FROM models m, _rel_book_phrase b
              WHERE lower(concat_ws(' ', coalesce(m.ipdb_notes, ''),
                                         coalesce(m.ipdb_notable_features, ''),
                                         coalesce(m.description, '')))
                    LIKE '%' || b.phrase || '%')
  -- Anchor: the inbound-edge lens still sees something. model_edges_bidir going dark
  -- (a renamed direction value, a dropped view) would silently turn every
  -- reverse-direction structural test into a confident false.
  UNION ALL SELECT 'anchor_inbound_dark', NULL::BIGINT, 'model_edges_bidir returned no inbound rows'
            WHERE NOT EXISTS (SELECT 1 FROM model_edges_bidir WHERE direction = 'in')
  -- Structural: every recorded open question must still name a live model. A stale
  -- entry (ipdb no longer in the catalog) means the judgement has lost its subject.
  UNION ALL SELECT 'stale_open_question', q.ipdb_id, q.slug
            FROM _rel_open_question q
            WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.ipdb_id = q.ipdb_id)
  -- Vocabulary: every maker-level question must name a real Manufacturer slug.
  -- Tested against `manufacturers`, NOT against models-that-exist: the foundation is
  -- explicit that a maker with n_models = 0 is normal (the catalog carries makers it
  -- has no models for yet), so reaching through `models` would fail a legitimately
  -- seeded maker and gate the whole run on it.
  UNION ALL SELECT 'stale_maker_question', NULL::BIGINT, mq.manufacturer_slug
            FROM _rel_maker_question mq
            WHERE NOT EXISTS (SELECT 1 FROM manufacturers mf WHERE mf.slug = mq.manufacturer_slug)
  -- Anchor: the quote extractor still reaches a SENTENCE-INITIAL lineage phrase.
  -- IPDB writes a large share of this corpus as "Copy of Williams' 1974
  -- 'Strato-Flite'." — the phrase capitalized because it opens the note. The two
  -- anchors above both sit mid-sentence ("This is a copy of…"), so a case-sensitive
  -- extractor passes them while silently extracting nothing here, and the row leaves
  -- the certain tier through the `lineage_sentence <> ''` filter with no reject
  -- reason to show for it.
  UNION ALL SELECT 'anchor_quote_sentence_initial', NULL::BIGINT,
                   'astro-flite: sentence-initial lineage phrase extracted nothing'
            WHERE NOT EXISTS (
              SELECT 1 FROM _rel_quote WHERE id = (SELECT id FROM models WHERE slug = 'astro-flite')
                AND lineage_sentence <> '')
  -- Structural: the quote extractor must read the WHOLE ipdb-citable prose slice.
  -- An `ipdb:` cite verifies against Notable Features + Notes (verify_quotes.py's
  -- ipdb_notes_text), so the extractor must read both; reading only `notes` left every
  -- candidate whose lineage prose lives in Notable Features with no quote, dropping it
  -- from relationship_green AND relationship_green_rejected alike — the silent
  -- exclusion the rejected view exists to prevent.
  --
  -- `description` is deliberately NOT in scope here: the detectors read it, but it is
  -- flipcommons-authored prose that no `ipdb:` cite can verify against, so a
  -- description-only candidate legitimately yields no quote and is surfaced through
  -- the `no-quote-extracted` reject reason rather than this check.
  UNION ALL SELECT 'quote_field_narrower_than_detector', c.id, c.slug
            FROM relationship_candidates c
            JOIN _rel_signal s ON s.id = c.id
            JOIN _rel_quote  q ON q.id = c.id
            WHERE q.lineage_sentence = ''
              AND regexp_matches(
                    lower(coalesce(s.notable_features, '')),
                    'copy of|clone of|conversion of|conversion kit for|converted game for'
                    || '|converted from|repaint of|under licen|unauthori[sz]ed');

-- == 5 · VIEW REFERENCE ======================================================
-- One line per public view, read by `make analyze CMD=describe ARGS=<this file>`.
-- The reasoning a one-liner cannot hold sits in the comment blocks above, next to the
-- SELECT it explains; these exist so the view index can never drift from what the
-- session actually defines. Private `_underscore` helpers are excluded by the runner
-- and carry no comment.
COMMENT ON VIEW relationship_candidates IS
  'One row per model whose free text says it reproduces or is built on another design — the union of the by_copy and by_conv detectors, enriched with existing edge state, the resolved target guess and any recorded human judgement. The campaign''s universe; most consumers want relationship_review or relationship_green.';
COMMENT ON VIEW relationship_review IS
  'THE ACTIONABLE QUEUE: candidates with lineage language and no outbound typed edge yet. A model drops out the moment its edge is applied, so this IS the remaining work. Rows carrying a recorded open question sort first, then rows with a resolved target guess.';
COMMENT ON VIEW relationship_green IS
  'The CERTAIN tier: not-edged rows with exactly one resolved target, no open question and a verbatim quote extracted from the note itself. Author-ready with a spot-check rather than a per-row source read — but the quote is a PROPOSAL until make verify-quotes passes it.';
COMMENT ON VIEW relationship_green_rejected IS
  'Rows disqualified from the certain tier, each with its reject_reason. NOT a discard pile: most are genuine relationships that just are not the one a naive read would author (a component copy, a hedged note, a reverse-direction note, a book-attributed claim).';
COMMENT ON VIEW relationship_edged_audit IS
  'Possible WRONG EXISTING edges: an already-edged model none of whose resolved edge targets appears among its note''s quoted origins, carrying the provenance of those edges (who asserted them, in which patch, whether anything was cited, whether two sources disagree on authorization). A review aid, not a verdict.';
COMMENT ON VIEW relationship_uncited_edges IS
  'Live relationship edges carrying NO external evidence — the catalog-side counterpart to the campaign''s citation discipline. Authorization claims (licensed/unlicensed) sort first: those assert something no source was ever recorded for. Uncited, NOT unsourced — every row still has an ingest source.';
COMMENT ON VIEW relationship_open_questions IS
  'The campaign''s recorded human judgement — per-model rows held back from an earlier patch, and maker-level licensed-vs-unlicensed questions — each shown against its CURRENT edge state. A held-back row that now carries an edge means the question was resolved OR authored past; verify which.';
COMMENT ON VIEW relationship_sweep_candidates IS
  'The AI-corpus-sweep feed: one row per not-yet-edged candidate keyed on the stable ipdb number, with the resolved target guess as an audited-not-inherited hint and the maker slug for evidence attachment. Read by emit_candidates.py through the checks gate.';
COMMENT ON VIEW relationships_summary IS
  'Every headline number this campaign publishes — candidate counts, edged vs not_edged coverage, the certain tier and its reject classes, edge provenance, and the upstream book-cite blocker. Published prose quotes this view, never a hand count.';
COMMENT ON VIEW relationships_checks IS
  'The invariant gate: empty means healthy, any row fails the run. Structural (grain and coverage), Vocabulary (closed sets and non-stale reference entries) and Anchors (a known example still triggers each detector — the only class that catches a whole detector going dark).';
