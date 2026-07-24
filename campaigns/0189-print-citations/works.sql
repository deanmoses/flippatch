-- works.sql — WHICH print works does IPDB's free text name, and can the catalog address
-- them yet?
--
-- READ ORDER. `.read` by `citations.sql`, which owns every `.read` in this campaign.
-- Depends on the foundation (`models` for the corpus, `citation_sources` for what is
-- seeded) and on nothing else here.
--
-- THIS IS TEXT MINING, with no counterpart in the analytics foundation. The foundation
-- exposes what citation source roots the catalog HAS — seeded, structured, already ours.
-- This file asks which works IPDB's prose NAMES, whether or not we hold them. The two
-- meet only at `citation_seeded`, a join, and it is the smallest thing here.
--
-- Three jobs:
--   1. THE VOCABULARY — the aliases a work is written under, declared.
--   2. IS IT COMPLETE — an open-ended survey answering what the vocabulary cannot ask
--      about itself, and the only check in the campaign that can catch the analysis
--      being INCOMPLETE rather than broken.
--   3. WHAT WE HOLD — resolution against the seeded roots, and the book edition map.

-- ═══ 1. THE VOCABULARY ═══════════════════════════════════════════════════════
-- One row per (canonical work, alias regex). Aliases are the surface spellings IPDB
-- actually uses: "The Billboard" was the magazine's name until 1961 and both forms
-- appear, and "Encylopedia" is a real misspelling in the corpus, not a typo here.
--
-- Matching is CASE-SENSITIVE throughout. 'RePlay' the magazine vs 'replay' the
-- gameplay noun is exactly the distinction a case-insensitive match destroys, and
-- pinball prose is full of the noun.
--
-- Some aliases are ordinary English capitalised ('Coin Slot', 'Loose Change', 'Pinball
-- Machines') and will occasionally match prose rather than a title. They are left in:
-- every one is low-volume, and a collision is caught by the ambiguity gate or by having
-- no seeded root to resolve to — measured, when the page requirement was removed and not
-- one prose collision came through with it. A mention also only becomes a patch edit
-- after `citations.sql` matches it to an entry's own quote, which collisions do not
-- survive.
CREATE OR REPLACE VIEW pub_vocab AS
SELECT * FROM (VALUES
  -- ── trade press: the print originals behind most IPDB dating ──
  -- 'BB' is IPDB's trade shorthand for Billboard, and it is confirmed rather than
  -- guessed: `tally-roll` carries both "The first Billboard ad ... is dated 07/06/1946
  -- p161" and "(Per BB 07/06/1946, pp 132, 161)" — same date, and the BB form is the one
  -- that gives both pages. The digit is part of the alias on purpose: bare 'BB' is far
  -- too short to be safe on its own, and every real use is followed by a date.
  -- 'Billboard' is also an ordinary English noun, and the corpus uses it that way:
  -- "Billboard at this new plant at 3401 N. California Avenue. A sign posted on the
  -- property in 2022…" is a physical sign at a factory. Nothing here excludes it, and
  -- nothing needs to: a sign has no issue date beside it, so it cannot resolve an issue
  -- and cannot become a citation. The identity requirement is the guard, not the alias.
  ('Billboard',                 'periodical', '(?:The )?Billboard|\bBB [0-9]'),
  ('Cash Box',                  'periodical', '(?:The )?Cash Box'),
  ('Automatic Age',             'periodical', 'Automatic Age'),
  ('Coin Machine Digest',       'periodical', 'Coin Machine Digest'),
  ('Coin Machine Journal',      'periodical', '(?:The )?Coin Machine Journal'),
  ('Automatic World',           'periodical', 'Automatic World'),
  ('Coin Machine Review',       'periodical', 'Coin Machine Review'),
  ('Vending Times',             'periodical', 'Vending Times'),
  ('Amusement Business',        'periodical', 'Amusement Business'),
  ('Automatic Merchandiser',    'periodical', 'Automatic Merchandiser'),
  ('Loose Change',              'periodical', 'Loose Change'),
  ('Play Meter',                'periodical', 'Play ?Meter'),
  -- Case-sensitivity protects 'RePlay' the magazine from 'replay' the gameplay noun,
  -- and it also rejected 'Replay Magazine' — the correct title, differently cased. The
  -- alias carries both spellings, but the second REQUIRES the word "magazine": a bare
  -- `\bReplay\b` was tried and produced 90 mentions of which 5 were genuine, because
  -- "Replay and Regular (Novelty Play) models" and "Replay version is Williams' 1966
  -- 'Full House'" are the capitalised gameplay noun. They all landed in the drop pile,
  -- so nothing downstream broke — which is precisely why it would have gone unnoticed.
  ('RePlay',                    'periodical', 'RePlay|Replay [Mm]agazine'),
  ('Coin Slot',                 'periodical', '(?:The )?Coin Slot'),
  ('GameRoom Magazine',         'periodical', 'Game ?Room(?: [Mm]agazine)?'),
  ('PinGame Journal',           'periodical', 'PinGame Journal'),
  ('Pinball Trader Newsletter', 'periodical', 'Pinball Trader'),
  ('Pinhead Classified',        'periodical', 'Pinhead Classified'),
  ('Coin Drop International',   'periodical', 'Coin Drop International'),
  ('Canadian Coin Box',         'periodical', 'Canadian Coin Box'),
  ('Coin-Op Newsletter',        'periodical', 'Coin-?Op Newsletter'),
  ('Pinball Magazine',          'periodical', 'Pinball Magazine'),
  -- ── books ──
  -- 'EOP' is IPDB's own abbreviation for the Encyclopedia.
  ('The Encyclopedia of Pinball',    'book', '(?:The )?Ency[cl]+opedia of Pinball|\bEOP\b'),
  ('The Pinball Compendium',         'book', '(?:The )?Pinball Compendium'),
  ('Pinball Machines',               'book', 'Pinball Machines'),
  -- Lawton's bingo book — seeded (0041) as its full title "Bally Bingo Pinball Machines",
  -- which is the work label here so citation_seeded resolves it; the alias stays IPDB's
  -- shorthand "Bingo Pinball Machines". A deliberate collision: that alias CONTAINS
  -- Bueschel's "Pinball Machines", and RE2 has no lookbehind to exclude the longer title
  -- from the shorter alias. Declaring it as its own work is what makes the overlap visible —
  -- "Jeffrey Lawton's book Bingo Pinball Machines on page 62" now matches two works and
  -- is dropped as ambiguous, instead of being silently attributed to Bueschel and
  -- emitting the wrong ISBN the moment a Pinball Machines edition is mapped.
  ('Bally Bingo Pinball Machines',   'book', 'Bingo Pinball Machines'),
  ('The Complete Pinball Book',      'book', '(?:The )?Complete Pinball Book'),
  ('Pinball Snapshots',              'book', 'Pinball Snapshots'),
  ('Pinball Memories',               'book', 'Pinball Memories'),
  ('Pinball Perspectives',           'book', 'Pinball Perspectives'),
  ('Pinball One',                    'book', 'Pinball One'),
  ('Pinball Wizardry',               'book', 'Pinball Wizardry'),
  ('Tilt: The Pinball Book',         'book', 'Tilt: The Pinball Book'),
  ('Pinball Reference Guide',        'book', 'Pinball Reference Guide')
) AS t(work, work_type, alias_re);

-- ── The open-ended survey ────────────────────────────────────────────────────
-- Everything downstream of this campaign is conditioned on `pub_vocab`. A work missing
-- from those rows is not under-counted, it is INVISIBLE: it raises no drop reason, fails
-- no check, and moves no floor. The detector floor guards against a detector going dark,
-- but it is measured inside the vocabulary, so it cannot tell "the corpus is this size"
-- from "we are only looking at part of it". `Bingo Pinball Machines` was found by
-- accident — it happened to collide with an alias we already had — and that is not a
-- search strategy.
--
-- So these frames look for what a citation LOOKS LIKE, with no vocabulary at all.
-- Declared as a table for the same reason `shape_rules` is: adding a frame is one row,
-- and a frame can be tested against a literal.
--
-- TWO frames, because neither finds the other's hits. `locator` needs an adjacent page
-- or date and finds "Game Machine, Feb-15-1977"; `magazine` needs the word itself and
-- finds "issue of Bally-Who", which carries no locator at all. A third frame is one row
-- here plus a fixture, and that is the intended way to widen coverage — never by
-- loosening an existing one, which is how a coverage check stops covering.
CREATE OR REPLACE VIEW candidate_frames AS
SELECT * FROM (VALUES
  ('locator',
   '(?:[A-Z][A-Za-z''&-]+ ){0,3}[A-Z][A-Za-z''&-]+,? (?:dated |of |issue |magazine )?' ||
   '(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[- ][0-9]{1,2}[,-] ?[0-9]{4}' ||
   '|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}|pages? [0-9]{1,4}|pp?\.? ?[0-9]{1,4})'),
  ('magazine',
   '(?:[A-Z][A-Za-z''&-]+ ){0,3}[A-Z][A-Za-z''&-]+ [Mm]agazine' ||
   '|issue of (?:[A-Z][A-Za-z''&-]+ ){0,3}[A-Z][A-Za-z''&-]+')
) AS t(frame, frame_re);

-- Strip a frame match down to the bare name: drop a trailing locator, a trailing
-- "magazine", a leading "issue of". Frame-agnostic on purpose — one macro for every
-- frame means a new frame needs no new stripping rule, and it is testable in isolation.
CREATE OR REPLACE MACRO candidate_phrase(matched) AS
  trim(regexp_replace(regexp_replace(regexp_replace(matched,
    ',? (?:dated |of |issue |magazine )?(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[- ][0-9]{1,2}[,-] ?[0-9]{4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}|pages? [0-9]{1,4}|pp?\.? ?[0-9]{1,4})$', ''),
    ' [Mm]agazine$', ''), '^issue of ', ''));

-- The normalized corpus, materialized once and shared with `citations.sql`. `text_norm`
-- is three regex passes over every note; as a view it re-ran per reference.
CREATE OR REPLACE TABLE pub_notes_src AS
  SELECT slug AS key, text_norm(ipdb_notes) AS txt FROM models WHERE ipdb_notes IS NOT NULL;

CREATE OR REPLACE VIEW candidate_frames_src AS
  SELECT frame AS term, frame_re AS term_re FROM candidate_frames;

-- Frames are located through `mention_positions` rather than `regexp_extract_all` for the
-- same reason the mentions are: it returns an exact position per occurrence, so `ctx`
-- below is the text around THIS match. Reaching for `instr(txt, matched)` instead would
-- find the first occurrence of that text and hand every repeat the wrong context.
CREATE OR REPLACE TABLE pub_candidates AS
SELECT
  p.key                       AS slug,
  p.term                      AS frame,
  p.hit                       AS matched,
  candidate_phrase(p.hit)     AS phrase,
  -- Enough either side to hold a locator: the date usually PRECEDES the name ("the
  -- January 1953 issue of Bally-Who") while a page usually follows it.
  substr(p.txt, greatest(1, p.pos - 60),
         least(60, p.pos - 1) + CAST(len(p.hit) + 90 AS BIGINT)) AS ctx
FROM mention_positions('pub_notes_src', 'candidate_frames_src') p;

-- The standing verdicts. One row per phrase pattern somebody has already looked at, so
-- the gate reports only what is NEW. Recording a decision here is the way to quiet it —
-- never by loosening the frames, which is how a coverage check stops covering.
--
-- `needs-root` is a real backlog, not a dismissal: each is a work the corpus cites and
-- the catalog cannot address, and it becomes citable the moment a root is declared for
-- it in `0041-citation-sources.yaml`. They are listed here rather than added to
-- `pub_vocab` on purpose — a work in the vocabulary with no seeded root produces
-- mentions that can only ever drop, which is noise wearing the costume of progress.
CREATE OR REPLACE VIEW vocab_review AS
SELECT * FROM (VALUES
  -- ── not publications: what the frames pick up that is not a citation at all ──
  ('^(?:Granted|Filed|Patented|Issued|Renewed|Applied)$', 'not-a-publication', 'patent record language'),
  ('^(?:On|The|From|Our|Per|Present|This|That|In|At|By|An?|And|But|It|Its|He|His|They)$',
                                                          'not-a-publication', 'sentence-leading prose word'),
  ('^(?:Manufacture Date|Project Date|Production Log|Log|Parts List|Parts Manual|The Parts Manual|Service Bulletin|Schematic|ORIGINAL)$',
                                                          'not-a-publication', 'manufacturer document or date label'),
  ('^PDF$',                                               'not-a-publication', 'file format, from "PDF pages 32"'),
  ('^(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day$',        'not-a-publication', 'weekday before a date'),
  ('^Pinball$',                                           'not-a-publication', 'truncation of "…of Pinball page N" — the lowercase "of" breaks the capitalised run'),
  ('^Doolittle Raid$',                                    'not-a-publication', 'historical event with a date'),
  ('^(?:Part [IVX]+|[IVX]+ Coin Machines)$',              'not-a-publication', 'Cash Box section name, e.g. "part III Coin Machines"'),
  ('''s$',                                                'not-a-publication', 'possessive — "issue of Stern''s", "issue of Bally''s": the publication name follows and is not captured'),
  ('^(?:The )?(?:Japanese|German(?:-language)?|Italian|French|Spanish|Dutch|British|American|European|trade|the)$',
                                                          'not-a-publication', 'adjective before the word magazine — "The Italian magazine <name>" names the language, not the title'),
  ('^Jimmy Johnson''s Western Companies$',                'not-a-publication', 'a company'),
  -- ── out of scope: real publications, but not print sources this campaign cites ──
  ('^(?:Heavy Metal|MAD|Esquire|Playboy|Life|Time)$',     'out-of-scope', 'consumer magazine named as theme material, not as a dating source'),
  -- ── needs-root: cited by the corpus, not addressable by the catalog ──
  ('^(?:The )?Game Machine$',        'needs-root', 'Japanese coin-op trade magazine — "according to Game Machine, Feb-15-1977"'),
  ('^Bally-Who',                     'needs-root', 'Bally house organ — verify it is a periodical before seeding'),
  ('^Spinning Reels$',               'needs-root', 'periodical named in "issue of Spinning Reels" — verify'),
  ('^Automat$',                      'needs-root', 'German coin-op trade magazine'),
  ('^Bally Midway Monitor$',         'needs-root', 'Bally/Midway house organ — verify it is a periodical'),
  ('^Amusement Review$',             'needs-root', 'trade magazine — verify'),
  ('^Atchison Daily Globe$',         'needs-root', 'newspaper; would be the first newspaper root'),
  ('^Marketplace (?:Newsletter|Pictorial History)$', 'needs-root', 'verify: newsletter vs book'),
  ('^The Game$',                     'needs-root', 'from "The Game Magazine" — verify; may be a mis-set "The Game Machine"'),
  ('^Pinball Wizard$',               'needs-root', 'verify: distinct from the seeded book "Pinball Wizardry"'),
  -- Read in context, these two are not what the phrase suggested:
  ('^Silver Ball$',                  'not-a-publication', 'tail of the BOOK title "Pinball, Lure of the Silver Ball" — the frame cuts at the comma'),
  ('^Ballyhoo$',                     'not-a-publication', 'the 1930s humour magazine the GAME was named after, not a source: "the Ballyhoo magazine which caused Ray Moloney to name the game"'),
  ('^Replay$',                       'not-a-publication', 'the gameplay noun capitalised; RePlay the magazine is in pub_vocab and needs the word "magazine" to match'),
  -- Found by this view's own second pass, once the first round of verdicts quieted the
  -- noise. The European trade press is a whole seam the vocabulary never had: the
  -- catalog is full of Italian, German and Spanish makers, and their dating evidence is
  -- in their own trade papers, not Billboard.
  ('^AUTOMATENMARKT$',               'needs-root', 'German coin-op trade magazine'),
  ('^Automatico Espa',               'needs-root', 'Automático Español, Spanish coin-op trade magazine (phrase truncates at the accent)'),
  ('^Euroslot$',                     'needs-root', 'European coin-op trade magazine'),
  ('^Novomatic$',                    'needs-root', 'Novomatic house organ — verify it is a periodical'),
  ('^Marketplace$',                  'needs-root', 'verify against the Marketplace Newsletter entry above'),
  ('^The Gaffney Ledger$',           'needs-root', 'newspaper, as with the Atchison Daily Globe'),
  -- ── remaining noise the frames pick up ──
  ('^(?:Flying|OUI)$',               'out-of-scope', 'consumer magazine named as theme material'),
  ('^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-?$',
                                     'not-a-publication', 'month token from "issue of Feb-15-1977"')
) AS t(phrase_re, verdict, note);

-- Uncovered and unreviewed — empty when the vocabulary is complete as far as anyone has
-- looked. Coverage is tested against the FULL match, not the trimmed phrase, so an alias
-- whose regex includes its locator (Billboard's `BB [0-9]`) still counts as covered.

CREATE OR REPLACE VIEW citation_vocab_gaps AS
SELECT c.phrase, count(*) AS n, count(DISTINCT c.slug) AS models,
       string_agg(DISTINCT c.frame, '/') AS frames, any_value(c.matched) AS example
FROM pub_candidates c
WHERE NOT EXISTS (SELECT 1 FROM pub_vocab v  WHERE regexp_matches(c.matched, v.alias_re))
  AND NOT EXISTS (SELECT 1 FROM vocab_review r WHERE regexp_matches(c.phrase, r.phrase_re))
GROUP BY c.phrase ORDER BY n DESC, c.phrase;

-- The actionable half of the review: works we know we cannot cite yet, with how much
-- each is worth. Seed a root for one and its mentions become emittable.
-- RANK BY `citable`, NOT BY `observed`. A mention is only worth a root if the surrounding
-- text identifies an ISSUE — for a magazine that means a parsable date. `citable` applies
-- the real locator grammar from `locators.sql` to the text around each mention, so it
-- answers "would seeding this root produce a citation" rather than "is this work talked
-- about". `with_page` rides along as detail, not as a requirement: a page is a
-- convenience, and a monthly house organ has no unit finer than its issue.
CREATE OR REPLACE VIEW citation_vocab_backlog AS
SELECT r.phrase_re, r.note,
       count(c.phrase)                                        AS observed,
       count(DISTINCT c.slug)                                 AS models,
       count(*) FILTER (WHERE loc_shape(c.ctx, 'page') IS NOT NULL) AS with_page,
       count(*) FILTER (WHERE loc_shape(c.ctx, 'date') IS NOT NULL) AS citable,
       any_value(c.matched)                                   AS example
FROM vocab_review r
LEFT JOIN pub_candidates c ON regexp_matches(c.phrase, r.phrase_re)
WHERE r.verdict = 'needs-root'
GROUP BY r.phrase_re, r.note ORDER BY citable DESC, observed DESC;

-- ── 4b. The book edition ─────────────────────────────────────────────────────
-- An `isbn:` cite must name ONE edition, and ingest rejects an ISBN that lands on a
-- record with editions under it. That makes book resolution a lookup, not an inference,
-- and the mapping is declared here where the checks can see it.
--
-- Three shapes of book in the seeded shelf:
--   * single edition   — the root itself carries the ISBN. Nothing to disambiguate.
--   * volumes          — the Encyclopedia. IPDB's prose names the volume ("Vol 1",
--                        "Volume 2") and each volume is its own seeded record. Note the
--                        catalog names Vol. 2 "Vol. 2: Contact to Bumper 1934–1936",
--                        which does NOT start with the work title — a name-prefix match
--                        cannot find it, which is why the ISBN is written out here.
--   * editions         — Pinball Machines, The Complete Pinball Book, and the Compendium's
--                        "1982 to the Present" all have revised editions below a root
--                        that carries no ISBN of its own. IPDB never says which printing,
--                        so these are genuinely unresolvable: the row carries a NULL isbn
--                        and drops with a reason rather than guessing a printing.
CREATE OR REPLACE VIEW book_editions AS
SELECT * FROM (VALUES
  ('The Encyclopedia of Pinball', 'Vol(?:ume)?\.? ?1\b',                  '9781889933009', 'Vol. 1'),
  ('The Encyclopedia of Pinball', 'Vol(?:ume)?\.? ?2\b',                  '9781889933023', 'Vol. 2'),
  ('The Pinball Compendium',      '1930s[-–—]1960s',                      '9780764315275', '1930s–1960s'),
  ('The Pinball Compendium',      '1970[-–—]1981',                        '9780764320743', '1970–1981'),
  ('The Pinball Compendium',      'Electro[- ]?[Mm]echanical',            '9780764330285', 'Electro-Mechanical Era'),
  ('The Pinball Compendium',      '1982[-– ]?(?:to )?(?:the )?[Pp]resent', NULL,           '1982 to the Present (edition unknown)')
) AS t(work, edition_re, edition_isbn, edition_label);

-- ═══ 5. WHAT IS SEEDED ═══════════════════════════════════════════════════════
-- Resolve the vocabulary against the catalog's citation sources.
--
-- The match is a PREFIX match, not an equality: the catalog names its books with their
-- subtitles ("Pinball Snapshots: Air Aces to Xenon") while IPDB's prose names the short
-- title, so an exact join reports half the seeded book shelf as missing and would send
-- an author to create duplicate roots for works already there.
--
-- Every attribute is co-drawn from ONE row, via a single `argMin` over a STRUCT — not
-- three independent `argMin`s. The independent form was still wrong: `arg_min(arg, val)`
-- ignores rows whose VALUE argument is NULL, independently per call, so `argMin(name, id)`
-- and `argMin(isbn, id)` could resolve to different roots. "The Pinball Compendium" showed
-- the name of the 1982 volume (the min-id root) beside the ISBN of the 1930s–1960s one,
-- because the 1982 root carries a NULL isbn and the isbn call skipped it. A struct is a
-- non-NULL value as long as its row exists, so all three fields come from the same min-id
-- root — genuinely consistent, which is what the old comment only claimed. `n_roots > 1`
-- still flags that the row is one of several; downstream trusts `root_isbn` only at
-- `n_roots = 1`, so a NULL isbn on a multi-root min row is correct, not a regression.
--
-- Reads citation_sources (filtered to roots) rather than citation_roots, because the
-- authored `slug` — the left half of a `<root>:<issue>` cite — lives only on the former.
CREATE OR REPLACE VIEW citation_seeded AS
WITH agg AS (
  SELECT
    v.work,
    v.work_type,
    count(DISTINCT r.citation_source_id) AS n_roots,
    argMin({'name': r.citation_source_name, 'slug': r.slug, 'isbn': r.isbn},
           r.citation_source_id)         AS root
  FROM pub_vocab v
  LEFT JOIN citation_sources r
    ON r.is_root
    AND r.citation_source_type = v.work_type
    AND (r.citation_source_name = v.work
         OR starts_with(r.citation_source_name, v.work || ':')
         OR starts_with(r.citation_source_name, v.work || ','))
  GROUP BY v.work, v.work_type
)
SELECT work, work_type, n_roots,
  root.name AS seeded_as,
  root.slug AS root_slug,
  root.isbn AS root_isbn
FROM agg;

-- ── Self-test ────────────────────────────────────────────────────────────────
-- Empty when healthy. The first group is data-independent; the last two read the corpus
-- because that is what they are for.
CREATE OR REPLACE VIEW works_checks AS
WITH cases(name, got, want) AS (VALUES
  ('phrase strips a trailing date', candidate_phrase('Game Machine, Feb-15-1977'), 'Game Machine'),
  ('phrase strips a trailing page', candidate_phrase('Silver Ball, page 121'), 'Silver Ball'),
  ('phrase strips a trailing magazine', candidate_phrase('AUTOMATENMARKT magazine'), 'AUTOMATENMARKT'),
  ('phrase strips a leading issue-of', candidate_phrase('issue of Bally-Who'), 'Bally-Who'),
  ('phrase leaves a bare name alone', candidate_phrase('Euroslot'), 'Euroslot')
)
SELECT 'works_' || name AS check,
       'got [' || coalesce(got, '<null>') || '] want [' || want || ']' AS detail
FROM cases WHERE got IS DISTINCT FROM want

UNION ALL
-- A citation-shaped phrase the vocabulary does not cover and nobody has ruled on. This
-- is the only check in the campaign that can catch the analysis being INCOMPLETE rather
-- than broken; every other one is measured inside the vocabulary and cannot see past it.
-- Threshold 3 keeps the long tail of one-off prose out of the gate — `citation_vocab_gaps`
-- lists everything down to a single occurrence and is worth sweeping by eye now and then.
-- Quiet it by recording a verdict in `vocab_review`, never by narrowing a frame.
SELECT 'works_vocab_gap_unreviewed',
  'uncovered phrase "' || phrase || '" appears ' || n || ' times, e.g. "' || example || '"'
FROM citation_vocab_gaps WHERE n >= 3

UNION ALL
-- An ISBN declared in book_editions that no seeded citation source carries. The mapping
-- is hand-written, so a typo here mints a cite that fails at dry-run rather than in this
-- analysis, where it is cheap to see.
SELECT 'works_book_edition_isbn_unseeded',
  work || ' → ' || edition_label || ' declares ISBN ' || edition_isbn || ' which is not seeded'
FROM book_editions b
WHERE b.edition_isbn IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM citation_sources c WHERE c.isbn = b.edition_isbn);
