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
-- `model_edges`, so "what's already done" is a column (has_rel_edge), not a snapshot
-- that goes stale. The AI sweep (vetting) and the authoring recipe are unchanged;
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
--     P=campaigns/0128-relationships/relationships.sql
--     make analyze FILE=$F PREFIX=relationships                       # summary, gated on checks
--     make analyze FILE=$F Q="FROM relationship_review LIMIT 40;"     # the actionable queue
--     make analyze FILE=$F Q="FROM relationship_edged_audit;"         # possible wrong existing edges
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

-- == 3 · ANALYSIS ============================================================
-- A candidate hunt: detect -> assemble+enrich -> review. Membership is the union of
-- the two phrase detectors; enrichment reads existing edges from the foundation's
-- `model_edges` (the "already done" signal) and resolves the quoted target guess.

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
    id, ipdb_id, slug, name, maker, maker_slug, year, label, notes, notable_features,
    -- by_copy: reproduces another maker's design (copy / bootleg / licensed build).
    regexp_matches(txt,
      '(a )?copy of|copied from|clone of|bootleg|unauthori[sz]ed (copy|version|reproduction)'
      || '|knock[- ]?off|under licen[cs]e|built under licen|licen[cs]ed (build|copy|version|reproduction) of'
      || '|reproduction of') AS by_copy,
    -- by_conv: reuses another machine's hardware (conversion / kit / repaint / retheme).
    regexp_matches(txt,
      'conversion of|conversion kit|converted (game )?(for|from)|conversion for'
      || '|re-?theme|repaint of|reworked from') AS by_conv,
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
    -- under-cited claim. Generic seeded titles ("Pinball Machines", "Pinball!") are
    -- NOT matched — the phrase is ubiquitous in notes and would match everything.
    regexp_matches(txt,
      'encyclopedia of pinball|pinball compendium|complete pinball book'
      || '|bingo pinball machines|\bbook\b') AS mentions_book_source,
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
CREATE OR REPLACE VIEW _quoted_resolved AS
  WITH q AS (
    SELECT s.id AS model_id, regexp_replace(lower(qn), '[^a-z0-9]', '', 'g') AS qkey
    FROM _rel_signal s, UNNEST(s.quoted_names) AS u(qn)
    WHERE (s.by_copy OR s.by_conv) AND length(qn) > 1
  )
  SELECT DISTINCT q.model_id, m.slug AS target_slug, m.label AS target_label
  FROM q
  JOIN models m ON regexp_replace(lower(m.name), '[^a-z0-9]', '', 'g') = q.qkey
              AND m.id <> q.model_id;

-- assemble + enrich --
-- One row per candidate (union of the two detectors), joined to its existing edge
-- state and its resolved target guess. All edge facts read from the foundation's
-- `model_edges` — the unified "every edge out of a model" view — so a candidate that
-- already carries a typed relationship is flagged has_rel_edge (the campaign's "done"
-- signal), and a pre-existing lineage FK (variant_of/remake_of) is surfaced too.
CREATE OR REPLACE VIEW relationship_candidates AS
  SELECT
    s.id, s.ipdb_id, s.slug, s.name, s.maker, s.year, s.label,
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
    -- a pre-existing structured lineage FK (a variant/remake), for context.
    EXISTS (SELECT 1 FROM model_lineage l WHERE l.model_id = s.id) AS has_lineage_fk,
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
CREATE OR REPLACE VIEW relationship_edged_audit AS
  SELECT
    c.id, c.ipdb_id, c.label, c.maker,
    c.rel_types, c.rel_targets, c.target_guess,
    -- a recorded held-back verdict on an ALREADY-edged model is the loudest signal
    -- here: someone judged this undecidable, yet an edge exists. Verify which.
    c.open_question, c.maker_question,
    c.notes
  FROM relationship_candidates c
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
CREATE OR REPLACE VIEW _rel_quote AS
  SELECT
    s.id,
    trim(regexp_extract(nn.note_norm,
      '([^.]*(copy of|clone of|conversion of|conversion kit for|converted game for'
      || '|converted from|repaint of|under licen|unauthori[sz]ed)[^.]*\.)', 1)) AS lineage_sentence,
    nn.note_norm
  FROM _rel_signal s,
       LATERAL (SELECT regexp_replace(
         replace(replace(replace(replace(coalesce(s.notes, ''), '“', '"'), '”', '"'), '‘', ''''), '’', ''''),
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
      WHEN regexp_matches(q.lineage_sentence, '(?i)conversion of|converted (game )?(for|from)') THEN 'conversion'
      WHEN regexp_matches(q.lineage_sentence, '(?i)repaint of')                THEN 'retheme'
      ELSE 'copy'
    END AS relationship_type,
    CASE
      WHEN regexp_matches(q.lineage_sentence, '(?i)unauthori[sz]ed|unlicensed|bootleg') THEN 'unlicensed'
      WHEN regexp_matches(q.lineage_sentence, '(?i)under licen|built under licen')      THEN 'licensed'
      ELSE 'unknown'
    END AS license_status,
    q.lineage_sentence AS quote,
    CASE
      WHEN regexp_matches(q.lineage_sentence,
             '(?i)(backglass|artwork|art work|playfield|cabinet|layout|score ?card)[^.]{0,60}(copy|copied)')
        THEN 'component-copy'
      WHEN regexp_matches(q.lineage_sentence,
             '(?i)near[- ]?copy|probabl|possibl|apparentl|appears to|seems to|may be|might be'
             || '|likely|reportedly|believed|thought to be|said to be')
        THEN 'hedged'
      WHEN regexp_matches(q.lineage_sentence, '(?i)also (produced|made|released|manufactured)')
        THEN 'reverse-direction'
      WHEN c.mentions_book_source
        THEN 'book-source'
      WHEN q.lineage_sentence LIKE '%' || chr(65533) || '%'
        THEN 'mojibake'
    END AS reject_reason,
    c.notes
  FROM relationship_candidates c
  JOIN _rel_quote q ON q.id = c.id
  JOIN models t     ON t.slug = c.target_guess[1]
  WHERE NOT c.has_rel_edge
    AND c.open_question IS NULL
    AND len(c.target_guess) = 1
    AND q.lineage_sentence <> ''
    AND length(q.lineage_sentence) BETWEEN 20 AND 220
    -- the target's name must survive inside the extracted sentence
    AND regexp_replace(lower(q.lineage_sentence), '[^a-z0-9]', '', 'g')
        LIKE '%' || regexp_replace(lower(t.name), '[^a-z0-9]', '', 'g') || '%'
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
CREATE OR REPLACE VIEW relationship_sweep_candidates AS
  SELECT c.ipdb_id, c.slug, c.target_guess AS hint
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
  -- Structural: every recorded open question must still name a live model. A stale
  -- entry (ipdb no longer in the catalog) means the judgement has lost its subject.
  UNION ALL SELECT 'stale_open_question', q.ipdb_id, q.slug
            FROM _rel_open_question q
            WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.ipdb_id = q.ipdb_id)
  -- Vocabulary: every maker-level question must name a real Manufacturer slug.
  UNION ALL SELECT 'stale_maker_question', NULL::BIGINT, mq.manufacturer_slug
            FROM _rel_maker_question mq
            WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.manufacturer_slug = mq.manufacturer_slug);
