-- citations.sql — the citation instances themselves: every print reference IPDB's free
-- text carries, and which of our own patch entries could carry it.
--
-- THE ENTRY POINT for this campaign, and the only file here that `.read`s anything. Run:
--   make analyze FILE=campaigns/0189-print-citations/citations.sql PREFIX=citation
--   make analyze FILE=campaigns/0189-print-citations/citations.sql Q="FROM citation_candidates;"
--
-- THE CAMPAIGN IN FOUR FILES. Each answers a question the others do not, carries its own
-- `*_checks`, and can be edited without opening the rest — which is the point, since a
-- session tuning instance extraction has no business reading the book edition map.
--
--   text.sql       vocabulary-agnostic mechanics: where a term occurs, what sentence it
--                  sits in. No notion of citations at all.
--   works.sql      WHICH works IPDB names, whether the vocabulary is complete, and what
--                  the catalog can address today.
--   locators.sql   the locator grammar: date, page and volume patterns, and the pure
--                  functions that decode one. A parser; it never touches the corpus.
--   citations.sql  this file. Applies all three to the corpus and answers the campaign.
--
-- Leaf files own no `.read` of their own — nesting them would re-execute the expensive
-- `CREATE TABLE`s below. Each declares its dependencies in its header instead, so the
-- load order here is the contract: mechanics, then grammar, then vocabulary, then this.
-- Grammar precedes vocabulary because `works.sql` asks the locator rules whether a work
-- it cannot yet cite would actually yield a citation if it could; `locators.sql` depends
-- on nothing, so it is free to go first.
--
-- WHAT THIS FILE ANSWERS. IPDB's Notes are secondary: again and again they say where
-- THEY read a fact — "Victory Game's ad in Billboard 09/29/1945 p83". Billboard is the
-- original authority. This file finds those references, resolves each into a citable
-- `<root>:<issue>` or `isbn:`, and lands them on the grain a rewrite is decided at.
--
-- THAT LAST STEP IS THE ONE THAT SIZES THE CAMPAIGN, and it is not "this model has a
-- print mention". A patch entry quotes one passage; the print reference may sit in a
-- different sentence of the same note, supporting nothing the entry claims. Read section 5.

.read scripts/analysis/catalog.sql
.read ../flippatch/campaigns/0189-print-citations/text.sql
.read ../flippatch/campaigns/0189-print-citations/locators.sql
.read ../flippatch/campaigns/0189-print-citations/works.sql

-- ═══ 1. THE MENTIONS ═════════════════════════════════════════════════════════
-- One row per (model, work, OCCURRENCE) — every occurrence, including repeats. Finding
-- them, and the reason repeats are hard, is `text.sql`'s job; this is the adapter and
-- the windows cut around each hit. A TABLE because everything below re-reads it.
-- `text_norm` here is the single normalization point: every position, window, snippet
-- and quote below is measured against canonical text, so nothing downstream has to think
-- about CR, tabs or multi-character whitespace runs. The quote stays verifiable because
-- `verify_quotes.normalize` collapses whitespace on both sides before comparing.
-- `pub_notes_src`, the normalized corpus, is defined in `works.sql` — the first file to
-- need it — and both files read it.
CREATE OR REPLACE VIEW pub_vocab_src AS
  SELECT work AS term, alias_re AS term_re FROM pub_vocab;

CREATE OR REPLACE TABLE pub_mentions AS
SELECT
  p.key            AS slug,
  m.ipdb_id,
  p.term           AS work,
  v.work_type,
  p.occurrence,
  p.pos,
  p.txt            AS notes,
  -- The alias plus the 90 chars after it: long enough to hold any date+page tail IPDB
  -- writes, short enough that the next sentence's numbers cannot leak in and fake a
  -- locator. Windows may overlap; that is the point, and it is what the positional
  -- finder buys.
  --
  -- 70 was too tight, and the way it failed is instructive: "The first Billboard ad from
  -- the manufacturer for this rolldown game is dated 07/06/1946 p161" cuts at the "p",
  -- so the page rule saw a bare letter and matched nothing — the row dropped as "no
  -- page" while the page sat three characters past the edge. A truncated window does not
  -- announce itself; it just quietly produces a smaller corpus. The clause gate below is
  -- what makes the wider window safe.
  substr(p.txt, p.pos, CAST(len(p.hit) + 90 AS BIGINT))          AS snip,
  -- The 90 chars preceding, for the framing hint only. Kept OUT of the locator window
  -- deliberately: widening the shape window backwards would let the previous sentence's
  -- numbers pose as this citation's locator.
  substr(p.txt, greatest(1, p.pos - 90), least(90, p.pos - 1))   AS lead
FROM mention_positions('pub_notes_src', 'pub_vocab_src') p
JOIN pub_vocab v ON v.work = p.term
JOIN models m    ON m.slug = p.key;

-- ═══ 2. APPLYING THE GRAMMAR ═════════════════════════════════════════════════
-- Resolve each window against the locator rules from `locators.sql`, and decide whether
-- the row is ambiguous. A TABLE because `loc_shape`/`loc_match` are correlated
-- subqueries: materializing runs them once per mention. Resolving the rules a second way
-- for speed was tried and reverted — it bought 1.6s and cost a duplicate resolution
-- strategy plus a check to police it.
CREATE OR REPLACE TABLE pub_mention_shapes AS
WITH shaped AS (
  SELECT m.*,
    coalesce(loc_shape(m.snip, 'date'), 'none') AS date_shape,
    loc_match(m.snip, 'date')                   AS date_value,
    coalesce(loc_shape(m.snip, 'page'), 'none') AS page_shape,
    loc_match(m.snip, 'page')                   AS page_value,
    coalesce(loc_shape(m.snip, 'vol'),  'none') AS vol_shape,
    loc_match(m.snip, 'vol')                    AS vol_value
  FROM pub_mentions m
)
SELECT s.*,
  -- FALSE-POSITIVE GATE. IPDB often names two publications in one breath ("...in
  -- Billboard or Cash Box, Mar-31-1956, page 45"). When a second work is named in the
  -- window, the date and page we parsed may belong to that one, not this.
  --
  -- But only if it is named BEFORE them. A work mentioned after the locator cannot own
  -- it — "Encyclopedia of Pinball Vol 1 page 77 … later reported in Billboard" is not
  -- ambiguous about whose page 77 that is, and the position-blind form dropped rows like
  -- it purely for having a neighbour. That mattered more once the window widened: the
  -- extra 20 characters bought back real locators and would otherwise have spent them
  -- on false ambiguity.
  --
  -- With no locator parsed at all there is nothing to be positioned against, so any
  -- second work in the window still condemns the row.
  CASE
    WHEN s.date_value IS NULL AND s.page_value IS NULL THEN EXISTS (
      SELECT 1 FROM pub_vocab v2
      WHERE v2.work <> s.work AND regexp_matches(s.snip, v2.alias_re))
    ELSE EXISTS (
      SELECT 1 FROM pub_vocab v2
      WHERE v2.work <> s.work
        AND regexp_matches(s.snip, v2.alias_re)
        AND instr(s.snip, regexp_extract(s.snip, v2.alias_re)) <
            least(coalesce(nullif(instr(s.snip, s.date_value), 0), 1000000),
                  coalesce(nullif(instr(s.snip, s.page_value), 0), 1000000)))
  END AS ambiguous
FROM shaped s;

-- ═══ 3. IDENTITY ═════════════════════════════════════════════════════════════
-- A periodical mention resolves to an ISSUE; a book mention resolves to an EDITION. They
-- are different resolutions and an earlier build ran both through the issue path, which
-- was this campaign's worst bug: it required a parsed date of every book row, so 23
-- perfectly citable book mentions were dropped for "no parsable date" (a book has no
-- issue date), while the 9 that survived carried an `issue_slug` parsed out of prose
-- ABOUT THE GAME — "The Encyclopedia of Pinball page 22, on March 6, 1934 the Gee-Bee
-- Manufacturing Company changed…" became issue 1934-03-06. Neither half of that is
-- recoverable by tuning; the axis was wrong. The book half lives in `works.sql`.
CREATE OR REPLACE VIEW mention_issue AS
SELECT s.*,
  loc_year(s.date_shape,   s.date_value) AS iss_year,
  loc_month(s.date_shape,  s.date_value) AS iss_month,
  loc_day(s.date_shape,    s.date_value) AS iss_day,
  loc_season(s.date_shape, s.date_value) AS iss_season
FROM pub_mention_shapes s;

CREATE OR REPLACE VIEW mention_issue_slug AS
SELECT *,
  loc_issue_slug(iss_year, iss_month, iss_day, iss_season) AS issue_slug,
  loc_page(nullif(page_shape, 'none'), page_value)         AS page_locator,
  -- THE CLAUSE GATE, and it is a MAGAZINE test only.
  --
  -- Date and page are matched independently anywhere in the window, so nothing so far
  -- requires them to describe the same citation. They usually sit together; when they
  -- are far apart the window has spanned a clause boundary and the pairing is a guess —
  -- "Billboard every week starting Apr-16-1966. The ad dated May-21-1966 page 60" pairs
  -- page 60 with the April date, which is wrong.
  --
  -- A BOOK is exempt: its citation is an ISBN and a page, and the date parsed near the
  -- mention is prose about the game, never part of the reference. Applying the test to
  -- books anyway dropped 8 sound Encyclopedia citations.
  CASE WHEN work_type <> 'periodical' THEN false
       WHEN date_shape = 'none' OR page_shape = 'none' THEN false
       WHEN instr(snip, date_value) = 0 OR instr(snip, page_value) = 0 THEN false
       ELSE abs(instr(snip, page_value) - instr(snip, date_value)) > 25
  END AS date_page_split
FROM mention_issue;

-- ═══ 4. RESOLUTION — one predicate, one place ════════════════════════════════
-- Every mention gets a `cite_ref` (what a patch would write), a `locator`, and either
-- `emittable` or a `drop_reason`. The earlier build repeated the emittable predicate in
-- four views and the gate; they agreed by luck, not construction. Here they cannot
-- disagree because there is one of them.
--
-- Materialized for the same reason section 2 is: everything below re-reads this grain.
CREATE OR REPLACE TABLE mention_resolved AS
WITH resolved AS (
  SELECT
    s.*,
    sd.n_roots, sd.seeded_as, sd.root_slug, sd.root_isbn,
    be.edition_isbn, be.edition_label,
    -- A MATCHED EDITION ALWAYS WINS, and `root_isbn` is only trusted for a work with a
    -- single seeded root. The reverse precedence was a real bug: `citation_seeded` picks
    -- `root_isbn` with argMin, which is arbitrary among a work's roots, so every one of
    -- the 26 Pinball Compendium citations emitted the 1930s–1960s ISBN — including the
    -- ones whose text says "1970-1981" and "1982 to Present". A wrong ISBN is a citation
    -- to the wrong book, and nothing downstream can tell.
    --
    -- A matched edition with a NULL isbn is a deliberate "known, but not citable" (the
    -- Compendium's 1982 volume has printings below it), so it must NOT fall through to
    -- the root — hence a CASE on `edition_label` rather than coalesce on `edition_isbn`.
    CASE WHEN s.work_type <> 'book'        THEN NULL
         WHEN be.edition_label IS NOT NULL THEN be.edition_isbn
         WHEN sd.n_roots = 1               THEN sd.root_isbn
    END                                                                 AS book_isbn,
    -- Whether this work has ANY edition mapping at all. It separates two very different
    -- book failures that otherwise read the same: "IPDB didn't say which volume" (normal,
    -- the work is citable when it does say) from "nothing could ever resolve this work"
    -- (a shelf gap — the root carries no ISBN and no mapping covers it).
    EXISTS (SELECT 1 FROM book_editions b2 WHERE b2.work = s.work)       AS work_has_editions
  FROM mention_issue_slug s
  JOIN citation_seeded sd USING (work, work_type)
  LEFT JOIN LATERAL (
    SELECT b.edition_isbn, b.edition_label FROM book_editions b
    WHERE b.work = s.work AND regexp_matches(s.snip, b.edition_re) LIMIT 1) be ON true
),
-- The quote, cite_ref and locator are built here; the drop ladder is computed in the OUTER
-- select below so it can read `sentence` — the date-in-quote rung needs the built quote.
built AS (
SELECT * EXCLUDE (notes),
  -- THE QUOTE. Built here, not with the windows, because it needs the parsed locator:
  -- IPDB splits a citation across sentences often enough to matter ("…were in Cash Box,
  -- Oct-1-1960. On page 61, Paul Huebsch…"), so the span must reach past the mention's
  -- own sentence to whichever one holds the page. `snip` cannot serve as a quote at all —
  -- it starts mid-sentence and is cut at 90 chars.
  sentence_span(
    notes,
    pos,
    CASE WHEN page_value IS NOT NULL AND instr(snip, page_value) > 0
         THEN pos + instr(snip, page_value) + len(page_value) - 2
         ELSE pos END
  ) AS sentence,
  CASE WHEN work_type = 'periodical' AND root_slug IS NOT NULL AND issue_slug IS NOT NULL
         THEN root_slug || ':' || issue_slug
       WHEN work_type = 'book' AND book_isbn IS NOT NULL
         THEN 'isbn:' || book_isbn
  END AS cite_ref,
  -- Books carry the volume in the locator: "Vol. 2, p. 107" is the convention, and the
  -- volume is what the ISBN already encodes for the Encyclopedia — but a reader of the
  -- patch still needs it, and a work cited by a root ISBN with volumes inside it (the
  -- Compendium's own volumes are separate roots) has nowhere else to put it.
  CASE WHEN page_locator IS NULL THEN NULL
       WHEN work_type = 'book' AND vol_value IS NOT NULL
         THEN regexp_replace(vol_value, '^Vol(?:ume)?\.? ?', 'Vol. ') || ', ' || page_locator
       ELSE page_locator END AS locator
  FROM resolved
)
-- ONE drop ladder, most-specific first. NULL means emittable.
SELECT *,
  CASE
    WHEN ambiguous                                     THEN 'two works in window'
    WHEN seeded_as IS NULL                             THEN 'work has no seeded root'
    -- NO PAGE REQUIREMENT. Citability is "can we name the source", not "can we name a
    -- page". An earlier build required a page and it was wrong twice over: a monthly
    -- house organ has no finer unit than its issue ("the January 1953 issue of
    -- Bally-Who, a monthly newsletter from Bally"), and a book cited by ISBN already
    -- names its volume, so a page is a convenience rather than an identity. The catalog
    -- agrees — 3453 of its 3459 citation instances carry an empty locator.
    --
    -- It cost ~300 sound citations, most of them books. A comment in `pub_vocab` also
    -- claimed the page requirement was what caught prose collisions; it was not. Every
    -- mention it was holding back resolves to a real work, because a collision fails
    -- either the ambiguity gate or the seeded-root check long before reaching here.
    WHEN work_type = 'book' AND book_isbn IS NULL AND edition_label IS NOT NULL
                                                       THEN 'book edition not citable: ' || edition_label
    WHEN work_type = 'book' AND book_isbn IS NULL AND work_has_editions
                                                       THEN 'book volume not named in the mention'
    WHEN work_type = 'book' AND book_isbn IS NULL      THEN 'book has no citable edition seeded'
    WHEN work_type = 'periodical' AND root_slug IS NULL  THEN 'periodical root has no slug'
    -- A BARE YEAR IS USUALLY NOT THIS PUBLICATION'S YEAR AT ALL. `bare-year` is the
    -- catch-all date rule and it matches any 4-digit year anywhere in the window, so it
    -- routinely harvests one out of adjacent prose about something else entirely:
    -- "Billboard ads. The playfield has been retrofitted with Wico's 1948 'Whirlwind
    -- Play Booster'" yields 1948, which is another game's year in the next sentence.
    -- Read a sample before treating this pile as near-misses — most are misparses, not
    -- citations lacking a month. `bare-year` can never produce an emittable row (a year
    -- alone names no issue), so its only job is telling this reason from 'no parsable
    -- date'.
    WHEN work_type = 'periodical' AND issue_slug IS NULL AND date_shape = 'bare-year'
                                                       THEN 'bare year only, no issue date'
    WHEN work_type = 'periodical' AND issue_slug IS NULL AND date_shape <> 'none'
                                                       THEN 'impossible date in source'
    WHEN work_type = 'periodical' AND issue_slug IS NULL THEN 'no parsable date'
    WHEN date_page_split                               THEN 'date and page in different clauses'
    -- The date that minted the issue must survive into the quote a reader checks, or the
    -- cite addresses an issue its own evidence cannot support. The forward-only window can
    -- pair a mention with a date from a NEIGHBOURING clause (a movie release date a
    -- paragraph away), and `sentence_span` reaches only through the page — so a page-less
    -- periodical row can resolve to an issue whose date sits outside the extracted sentence.
    -- Drop rather than emit it; recovering these is the positional-binding rewrite, not a
    -- window tweak. The `sentence_missing_date` gate check is the twin of this rung.
    WHEN work_type = 'periodical' AND date_value IS NOT NULL AND NOT contains(sentence, date_value)
                                                       THEN 'issue date not in extractable quote'
  END AS drop_reason
FROM built;

-- ── THE FRAMING — what does the print source actually attest? ───────────────
-- A cite attaches to EVERY claim its entry asserts, so before adding one you must know
-- what the print source supports. IPDB frames these attributions several ways and only
-- some assert the fact:
--
--   asserts  — "Cash Box, page 85, states 'Made for the British Market'"
--   release  — "Billboard ... announced this game as a new release"
--   earliest — "The earliest mention we have found ... is in Billboard 09/29/1945 p83"
--              Both attest EXISTENCE BY A DATE and nothing more.
--   image    — "The Automatic Age ad of September 1933, page 54, shows an NRA logo"
--
-- READ THIS BEFORE TRUSTING IT. A triage hint over the drop pile and the orphans, and
-- nothing more: it reads verbs in a window that crosses a sentence boundary 45% of the
-- time, so a neighbouring sentence routinely decides the class. It is NOT what makes a
-- citation safe to attach — section 5 is.
CREATE OR REPLACE VIEW mention_framing AS
SELECT *,
  CASE
    WHEN regexp_matches(lead || ' ' || snip, '(?i)earliest (mention|ad|advertisement)|first (mention|ad)\b')
      THEN 'earliest'
    -- Verb stems carry an explicit inflection group rather than a trailing \b: a stem
    -- like 'announc' is never followed by a word boundary, so 'announc\b' can match
    -- nothing at all while looking perfectly reasonable.
    WHEN regexp_matches(lead || ' ' || snip,
         '(?i)\b(?:stat|indicat)(?:e|es|ed|ing)\b|\b(?:says|said|reports?|reported|noted|quoted)\b|according to')
      THEN 'asserts'
    WHEN regexp_matches(lead || ' ' || snip,
         '(?i)\b(?:announc|introduc|advertis|releas)(?:e|es|ed|ing)\b|\b(?:listed|lists|listing)\b')
      THEN 'release'
    WHEN regexp_matches(lead || ' ' || snip,
         '(?i)\b(?:show|shows|showed|shown|showing|pictur(?:e|es|ed|ing)|image[sd]?|photo)\b')
      THEN 'image'
    ELSE 'unclassified'
  END AS framing
FROM mention_resolved;

-- ═══ 5. THE REWRITE GRAIN — which patch entry could carry this? ══════════════
-- The campaign's actual worklist, and the view to read first.
--
-- A citation attaches to every claim in its patch ENTRY, and the entry's evidence is the
-- quote it already recorded. So a print reference may be added to an entry only when
-- that reference is inside THAT ENTRY'S OWN QUOTE. "The model is mentioned in a patch"
-- is a different and much weaker predicate: it admits ~100 models where this admits ~20
-- entries, because a patch entry quoting a feature phrase has nothing to do with a
-- Billboard reference three sentences away in the same note.
--
-- The containment test is per-part rather than on the whole snippet because patch quotes
-- elide with `[...]`: the entry that motivated this campaign quotes a relationship
-- sentence and a citation sentence with the middle cut out, so the reference is present
-- in pieces and absent as a contiguous span.
--
-- Built on `patch_entry_cites`, which is already one row per (entry, citation instance),
-- so the entry grain is inherited rather than re-derived. That matters here: 74 entries
-- in the corpus carry more than one distinct citation instance, and an aggregate that
-- reached for the quote with `any_value` could report a different quote than the one
-- that actually satisfied the containment test below. One row per (entry, evidence,
-- reference) keeps the licensing quote attached to the reference it licenses.
-- The campaign's scope, declared once. Production has ingested through
-- `0038-model-game-formats`; a patch at or below it is already applied there and its file
-- can never be re-ingested, so an entry inside one cannot carry a new citation no matter
-- what its quote says. This campaign is a moment in time and states its own cutoff — the
-- number is not derivable from this repo or the dev DB, and nothing outside this file
-- holds it.
CREATE OR REPLACE VIEW citation_scope AS SELECT 38 AS last_ingested_on_prod;

CREATE OR REPLACE VIEW citation_candidates AS
SELECT
  pe.patch_id,
  pe.patch_number,
  pe.changeset_id,
  pe.subject_type,
  pe.subject_id,
  pe.model_slug,
  m.ipdb_id,
  pe.fields            AS claim_fields,
  pe.n_claims_cited    AS n_claims,
  m.work,
  m.work_type,
  m.cite_ref           AS print_ref,
  m.locator            AS print_locator,
  m.framing            AS framing_hint,
  pe.quote             AS patch_quote,
  m.sentence           AS ipdb_sentence
FROM patch_entry_cites pe
JOIN mention_framing m
  ON m.slug = pe.model_slug
 AND m.drop_reason IS NULL
WHERE pe.patch_number > (SELECT last_ingested_on_prod FROM citation_scope)
  -- The stable handle on the citing work, NOT `citation_source_type = 'web'`: the type is
  -- a shape rather than an identity, so that proxy also admits every other web-rooted
  -- work and leans on the containment tests below to stay honest.
  AND pe.root_identifier_key = 'ipdb'
  -- the print reference, in pieces, inside the entry's own recorded quote
  AND contains(pe.quote, regexp_extract(m.snip, '^[^ ]+(?: [^ ]+)?'))
  AND (m.date_value IS NULL OR contains(pe.quote, m.date_value))
  AND (m.page_value IS NULL OR contains(pe.quote, m.page_value))
ORDER BY pe.patch_id, pe.model_slug;

-- EVERY emittable citation in the corpus, ONE ROW PER CITATION — not per mention. A note
-- can reach the same issue and page from two sentences ("...(Cash Box, Oct-15-1949, page
-- 20)." and "An article in Cash Box, Oct-15-1949, page 20, states..."), and a generator
-- reading the mention grain would emit that cite twice. The shortest sentence wins because
-- it is the tightest quote for the same fact; `n_sentences` says when there was a choice,
-- so an author can look for a better one. Defined HERE, ahead of `citation_orphans`, because
-- the orphan population is literally this set minus what a patch entry already carries — one
-- dedup, in one place, so the two views cannot drift to different grains.
CREATE OR REPLACE VIEW citation_rows AS
SELECT
  slug AS model_slug, ipdb_id, work, work_type, cite_ref, locator,
  argMin(framing,  length(sentence))          AS framing,
  argMin(date_shape, length(sentence))        AS date_shape,
  argMin(page_shape, length(sentence))        AS page_shape,
  argMin(sentence, length(sentence))          AS sentence,
  count(*)                                    AS n_sentences
FROM mention_framing
WHERE drop_reason IS NULL
GROUP BY slug, ipdb_id, work, work_type, cite_ref, locator
ORDER BY work, cite_ref, model_slug;

-- The orphan population: an emittable print reference that NO rewritable patch entry
-- carries. Not this campaign — a rewrite needs an entry to rewrite — but a large, real
-- backlog of print-attributed facts nothing has claimed yet. See the README's Follow-ups.
--
-- Anti-joined at CITATION grain (model + cite_ref + null-safe locator), NOT model grain.
-- The model-grain form was wrong twice over: a model carrying one candidate lost EVERY
-- other reference on it from the backlog (invisible in both views), and reading the mention
-- grain re-duplicated cites `citation_rows` had already folded. Building on `citation_rows`
-- and subtracting the exact (model, cite_ref, locator) triples a candidate carries fixes
-- both — and the `emittable_partitioned` check now guarantees the two views tile.
CREATE OR REPLACE VIEW citation_orphans AS
SELECT r.model_slug, r.ipdb_id, r.work, r.work_type, r.cite_ref, r.locator,
       r.framing, r.sentence
FROM citation_rows r
WHERE NOT EXISTS (
  SELECT 1 FROM citation_candidates c
  WHERE c.model_slug = r.model_slug
    AND c.print_ref = r.cite_ref
    AND c.print_locator IS NOT DISTINCT FROM r.locator)
ORDER BY r.work, r.cite_ref, r.model_slug;

-- ═══ 6. ANSWERS ══════════════════════════════════════════════════════════════

-- A. The works, with how much each is worth and whether it is citable today.
--    A book row with `root_isbn` NULL is not citable by the work: its ISBNs live on
--    edition records below the root, and an `isbn:` cite must name one edition. Check
--    `book_editions` for a mapping; where none exists (Pinball Machines, The Complete
--    Pinball Book) the work is simply uncitable until someone declares one, which is a
--    standing state of the seeded shelf and so is reported here and in the drop pile
--    rather than failed by the gate.
CREATE OR REPLACE VIEW citation_summary AS
SELECT
  sd.work, sd.work_type, sd.seeded_as, sd.root_slug, sd.root_isbn, sd.n_roots,
  count(s.slug)                                        AS mentions,
  count(DISTINCT s.slug)                               AS models,
  -- count(s.slug), NOT count(*): over the LEFT JOIN a zero-mention work yields one
  -- synthetic all-NULL row whose `drop_reason IS NULL` is vacuously true, and count(*)
  -- would score it as an emittable citation. Counting the non-NULL slug drops the phantom.
  count(s.slug) FILTER (WHERE s.drop_reason IS NULL)   AS emittable
FROM citation_seeded sd
LEFT JOIN mention_resolved s ON s.work = sd.work
GROUP BY ALL
ORDER BY mentions DESC, sd.work;

-- B. The formulations, as (date, page) pairs with a real example of each.
CREATE OR REPLACE VIEW citation_shapes AS
SELECT date_shape, page_shape, count(*) AS n, count(DISTINCT work) AS works,
       any_value(snip) AS example
FROM mention_resolved GROUP BY ALL ORDER BY n DESC;

-- C. The distinct ISSUES the emittable mentions need — one row per `sources:` node.
--    Magazines only: a book edition is cited by `isbn:` and is already seeded, so it
--    needs no node. `name` is the human label the node requires; `n_models` is how many
--    models rest on that issue.
CREATE OR REPLACE VIEW citation_issues AS
SELECT
  root_slug                                    AS parent,
  issue_slug                                   AS slug,
  work                                         AS periodical,
  CASE WHEN iss_season IS NOT NULL
         THEN upper(iss_season[1]) || iss_season[2:] || ' ' || CAST(iss_year AS VARCHAR)
       WHEN iss_day IS NOT NULL
         THEN strftime(make_date(iss_year, iss_month, iss_day), '%B %-d, %Y')
       WHEN iss_month IS NOT NULL
         THEN strftime(make_date(iss_year, iss_month, 1), '%B %Y')
       ELSE CAST(iss_year AS VARCHAR) END      AS name,
  any_value(iss_year)                          AS year,
  any_value(iss_month)                         AS month,
  any_value(iss_day)                           AS day,
  count(DISTINCT slug)                         AS n_models
FROM mention_resolved
WHERE drop_reason IS NULL AND work_type = 'periodical'
GROUP BY root_slug, issue_slug, work, iss_season, iss_year, iss_month, iss_day
ORDER BY root_slug, issue_slug;

-- D. citation_rows — every emittable citation, one row per cite. Defined up in section 5,
--    ahead of `citation_orphans`, which is built on it (orphans = rows − carried cites).

-- E. The DROP PILE, and why. Nothing here is emittable; the reason is the point.
--    'two works in window' is the interesting one — a second publication in the window
--    means the parsed date may belong to the other work, and many of these are
--    recoverable by a human read.
CREATE OR REPLACE VIEW citation_dropped AS
SELECT drop_reason AS reason, work, count(*) AS n, any_value(snip) AS example
FROM mention_resolved
WHERE drop_reason IS NOT NULL
GROUP BY ALL ORDER BY n DESC;

-- F. Per-axis rule usage: which patterns earn their place. A zero means the rule is dead
--    vocabulary or shadowed by a higher-priority sibling ('pp N' is shadowed by 'pp N-M'
--    and legitimately never fires alone).
CREATE OR REPLACE VIEW citation_rules AS
WITH fired AS (
  SELECT 'date' AS axis, date_shape AS shape FROM mention_resolved
  UNION ALL SELECT 'page', page_shape FROM mention_resolved
  UNION ALL SELECT 'vol',  vol_shape  FROM mention_resolved
)
SELECT r.axis, r.prio, r.shape, count(f.shape) AS n
FROM shape_rules r
LEFT JOIN fired f ON f.axis = r.axis AND f.shape = r.shape
GROUP BY ALL ORDER BY r.axis, r.prio;

-- G. How the emittable rows split by what their source attests. Scoping only — see the
--    warning on `mention_framing`.
CREATE OR REPLACE VIEW citation_framing AS
SELECT framing, count(*) AS n, count(DISTINCT model_slug) AS models,
       any_value(sentence) AS example
FROM citation_rows GROUP BY framing ORDER BY n DESC;

-- H. THE `sources:` NODES THE WORKLIST NEEDS — the candidate-scoped slice of
--    `citation_issues`. `citation_issues` is corpus-wide: every emittable periodical issue,
--    overwhelmingly ones only orphans rest on — far more than the handful the rewrite
--    worklist cites (compare `count(*)` of the two). Declare from THIS, not from
--    `citation_issues`, or you over-seed `0041` by an order of magnitude.
--
--    `source_type` and the y/m/d are the `sources:` node fields; `already_seeded` says which
--    issues are declared already — never re-declare one, the cite form does not create — and
--    `seeded_name` surfaces a name/date conflict against what is already there. `earliest_patch`
--    is the lowest-numbered candidate patch resting on the issue: the node must be declared
--    there or earlier, and `0041-citation-sources.yaml` is the usual home. Books are absent
--    by design — an `isbn:` cite names an already-seeded edition and needs no node.
CREATE OR REPLACE VIEW citation_candidate_sources AS
SELECT
  i.parent, i.slug, i.periodical,
  'periodical'                       AS source_type,
  i.name, i.year, i.month, i.day,
  count(DISTINCT c.model_slug)       AS n_models,
  min(c.patch_number)                AS earliest_patch_number,
  argMin(c.patch_id, c.patch_number) AS earliest_patch,
  EXISTS (SELECT 1 FROM citation_sources s
          WHERE s.root_citation_source_slug = i.parent AND s.slug = i.slug) AS already_seeded,
  (SELECT any_value(s.citation_source_name) FROM citation_sources s
   WHERE s.root_citation_source_slug = i.parent AND s.slug = i.slug)        AS seeded_name
FROM citation_candidates c
JOIN citation_issues i
  ON i.parent = split_part(c.print_ref, ':', 1)
 AND i.slug   = split_part(c.print_ref, ':', 2)
WHERE c.work_type = 'periodical'
GROUP BY i.parent, i.slug, i.periodical, i.name, i.year, i.month, i.day
ORDER BY i.parent, i.slug;

-- I. THE WORKLIST, MINUS WHAT A RE-INGEST HAS ALREADY APPLIED. `citation_candidates` keys
--    off the entry's IPDB cite, and that cite SURVIVES the rewrite — so once a rewritten
--    patch is re-ingested the candidate reappears though it is done, and the reset/re-ingest
--    tuning loop keeps re-suggesting finished work. This subtracts any entry already carrying
--    the EXACT print cite this campaign would add.
--
--    Matched by identity, not by root. The completed cite's source is reached by joining
--    `patch_entry_cites.citation_source_id` to `citation_sources` — which does carry the
--    child `slug` and the `isbn`, so the match is exact:
--      * periodical — the child issue source's root slug + issue slug equal the two halves
--        of `print_ref`, and the locator agrees. Root-only would wrongly retire a Billboard
--        candidate the moment the entry cited ANY other Billboard issue.
--      * book — `citation_sources.isbn` equals `print_ref`'s isbn half, locator agreeing.
--        A book's identifier_key is EMPTY (the ISBN lives in the `isbn` column), so the
--        earlier `root_identifier_key = 'isbn'` test never fired and every completed book
--        rewrite stayed pending forever.
--    Identical to `citation_candidates` until the first rewrite lands; that is the point.
CREATE OR REPLACE VIEW citation_pending_candidates AS
SELECT c.*
FROM citation_candidates c
WHERE NOT EXISTS (
  SELECT 1
  FROM patch_entry_cites done
  JOIN citation_sources src ON src.citation_source_id = done.citation_source_id
  WHERE done.changeset_id = c.changeset_id
    AND done.subject_type = c.subject_type
    AND done.subject_id   = c.subject_id
    AND done.locator IS NOT DISTINCT FROM c.print_locator
    AND ( (c.work_type = 'periodical'
             AND src.root_citation_source_slug = split_part(c.print_ref, ':', 1)
             AND src.slug                      = split_part(c.print_ref, ':', 2))
       OR (c.work_type = 'book'
             AND src.isbn = split_part(c.print_ref, ':', 2)) ))
ORDER BY c.patch_id, c.model_slug;

-- ═══ 7. THE GATE ═════════════════════════════════════════════════════════════
-- What must hold for this analysis to be trustworthy. These are detector-health checks,
-- not data-quality opinions: each fails when the MACHINERY has broken, which is the
-- failure mode that otherwise produces perfectly well-formed nonsense.
CREATE OR REPLACE VIEW citation_checks AS
-- A work the corpus cites with a full locator, but which has no seeded root, cannot be
-- cited at all. Declare its root before emitting.
SELECT
  'work_needs_root' AS check_name,
  true              AS failed,
  work || ' has ' || n || ' locator-bearing mention(s) but no seeded root' AS detail
FROM (SELECT work, count(*) AS n FROM mention_resolved
      WHERE drop_reason = 'work has no seeded root'
        AND (date_shape <> 'none' OR page_locator IS NOT NULL)
      GROUP BY work)

UNION ALL
-- A periodical root with no slug cannot be addressed by the `<root>:<issue>` cite form.
SELECT 'periodical_root_needs_slug', true,
  work || ' is seeded as ' || seeded_as || ' but carries no slug'
FROM citation_summary
WHERE work_type = 'periodical' AND mentions > 0 AND seeded_as IS NOT NULL AND root_slug IS NULL

UNION ALL
-- A book citation on a multi-root work that named no edition. It cannot be right: with
-- several seeded roots there is no such thing as "the work's ISBN", so anything emitted
-- here is one volume's identifier standing in for another's.
SELECT 'book_multiroot_without_edition', true,
  work || ': ' || count(*) || ' citation(s) resolved on a work with ' || any_value(n_roots)
       || ' roots but no edition match'
FROM mention_resolved
WHERE drop_reason IS NULL AND work_type = 'book' AND n_roots > 1 AND edition_label IS NULL
GROUP BY work

UNION ALL
-- A shape fired but extracted nothing: the rule's regex and its extract disagree.
SELECT 'empty_extraction', true,
  work || ': ' || date_shape || '/' || page_shape || ' matched but extracted empty'
FROM mention_resolved
WHERE (date_shape <> 'none' AND coalesce(date_value, '') = '')
   OR (page_shape <> 'none' AND coalesce(page_value, '') = '')

UNION ALL
-- A quote that is not verbatim. `sentence` is a positional span of the NORMALIZED note,
-- so it is tested against the same — which is exactly what `make verify-quotes` does,
-- since `verify_quotes.normalize` collapses whitespace on both sides before comparing.
-- Testing against raw text instead would fail every quote that crossed a whitespace run,
-- and would be asserting something the real gate does not.
SELECT 'sentence_not_verbatim', true,
  slug || '/' || work || ': extracted sentence is not a substring of its note'
FROM mention_resolved r
WHERE NOT EXISTS (
  SELECT 1 FROM pub_notes_src n WHERE n.key = r.slug AND contains(n.txt, r.sentence))

UNION ALL
-- A quote that does not contain the reference it exists to show. The sentence is what a
-- reader checks the citation against; one that stops before the page number is verbatim
-- and useless.
SELECT 'sentence_missing_locator', true,
  slug || '/' || work || ': sentence omits the parsed page "' || page_value || '"'
FROM mention_resolved
WHERE drop_reason IS NULL AND page_value IS NOT NULL AND NOT contains(sentence, page_value)

UNION ALL
-- CROSS-VIEW PARTITION. Every emittable citation must be reachable as EITHER a rewrite
-- candidate or an orphan, and the two must not overlap. The bug this pins: an earlier
-- `citation_orphans` anti-joined at MODEL grain, so a second reference on a model that
-- already had one candidate vanished from both populations — neither in the worklist nor
-- in the follow-up backlog. Keyed on (model, cite_ref, locator), the grain `citation_rows`
-- dedups to. Detector-health, not opinion: it fails only when the views stop tiling.
SELECT 'emittable_partitioned', true,
  count(*) || ' emittable citation(s) in neither citation_candidates nor citation_orphans'
FROM citation_rows r
WHERE NOT EXISTS (
        SELECT 1 FROM citation_candidates c
        WHERE c.model_slug = r.model_slug AND c.print_ref = r.cite_ref
          AND c.print_locator IS NOT DISTINCT FROM r.locator)
  AND NOT EXISTS (
        SELECT 1 FROM citation_orphans o
        WHERE o.model_slug = r.model_slug AND o.cite_ref = r.cite_ref
          AND o.locator IS NOT DISTINCT FROM r.locator)
HAVING count(*) > 0

UNION ALL
-- `citation_orphans` must be ONE ROW per (model, cite_ref, locator): a generator reads it
-- straight, so a duplicate is a double-emitted cite. The earlier view read the MENTION
-- grain and reproduced the exact multi-sentence duplication `citation_rows` exists to fold.
SELECT 'orphans_duplicated', true,
  count(*) || ' duplicate (model, cite_ref, locator) group(s) in citation_orphans'
FROM (SELECT 1 FROM citation_orphans
      GROUP BY model_slug, cite_ref, locator HAVING count(*) > 1)
HAVING count(*) > 0

UNION ALL
-- A work cannot have more emittable citations than it has mentions. `emittable > mentions`
-- means the count is tallying a phantom: `count(*) FILTER (drop_reason IS NULL)` over the
-- LEFT JOIN scores the synthetic all-NULL row of a zero-mention work as emittable.
SELECT 'summary_emittable_exceeds_mentions', true,
  work || ': emittable ' || emittable || ' > mentions ' || mentions
FROM citation_summary WHERE emittable > mentions

UNION ALL
-- The date twin of `sentence_missing_locator`. An emittable periodical cite mints its issue
-- from a parsed date; if that date is not in the quote a reader checks, the quote cannot
-- support the issue it addresses. This is how a forward window that reached a NEIGHBOURING
-- clause's date (a movie release date in the next paragraph) minted a plausible wrong issue
-- that verbatim-verified anyway, because the old gate checked only the page.
SELECT 'sentence_missing_date', true,
  slug || '/' || work || ': quote omits the parsed issue date "' || date_value || '"'
FROM mention_resolved
WHERE drop_reason IS NULL AND work_type = 'periodical'
  AND date_value IS NOT NULL AND NOT contains(sentence, date_value)

UNION ALL
-- THE DETECTOR FLOOR, on the grain the campaign acts on. A silently-broken alias regex
-- leaves every other view looking healthy, just smaller. The corpus is static, so this
-- count only moves when the machinery does. 23 candidates at authoring time against a
-- database in sync with disk; a floor of 15 absorbs vocabulary tuning without absorbing
-- a dark detector. If this fires, check `patch_context.files_never_ingested` first — an
-- un-ingested patch file lowers it for a reason that has nothing to do with detection.
SELECT 'candidate_floor', true,
  'only ' || count(*) || ' rewrite candidates (expected >= 15) — a detector may be dark'
FROM citation_candidates
HAVING count(*) < 15

UNION ALL
-- The corpus-wide floor, guarding the follow-up campaigns that read `citation_rows` and
-- `citation_orphans` rather than the rewrite grain.
SELECT 'emittable_floor', true,
  'only ' || count(*) || ' emittable mentions (expected >= 700) — a detector may be dark'
FROM mention_resolved
WHERE drop_reason IS NULL
HAVING count(*) < 700;
