-- text.sql — mechanics for mining a declared vocabulary out of unstructured source text.
--
-- A PROVING GROUND, parked in this campaign rather than in `scripts/analysis/`.
-- Everything here is campaign-agnostic and carries no judgment — no notion of citations,
-- publications, locators or patches — but one consumer is not a pattern. It moves up a
-- level when a second campaign has copied from it and shown what the shared shape is.
--
-- It solves two problems every free-text campaign hits and both of which are easy to get
-- subtly wrong: WHERE a term occurs (every occurrence, exact position) and WHAT sentence
-- it sits in (verbatim, because a `cite.quote:` must survive `make verify-quotes`). The
-- reasons each is harder than it looks are at the macros below.
--
-- THE CONTRACT is fixed column names, because SQL macros cannot take a column as a
-- parameter. Callers pass two relations BY NAME:
--
--   src    — one row per document: `key` (any identifier) and `txt` (the source text)
--   vocab  — one row per term:     `term` (canonical name) and `term_re` (its regex)
--
-- A three-line adapter view over your real tables is the intended way to meet it:
--
--   CREATE OR REPLACE VIEW notes_src AS
--     SELECT slug AS key, ipdb_notes AS txt FROM models WHERE ipdb_notes IS NOT NULL;
--   CREATE OR REPLACE VIEW my_vocab_src AS
--     SELECT work AS term, alias_re AS term_re FROM pub_vocab;
--   SELECT * FROM mention_positions('notes_src', 'my_vocab_src');
--
-- Matching is whatever the caller's regexes say. This file imposes no case folding, no
-- word boundaries and no normalization — those are judgments and they belong upstream,
-- in the vocabulary, where the campaign can see and gate them.

-- ── Canonical whitespace ─────────────────────────────────────────────────────
-- Every whitespace run becomes ONE character: a space, or — if the run contained a blank
-- line — a newline. So after this, `\n` means "paragraph break" and nothing else, and no
-- whitespace run is ever longer than one character.
--
-- That second property is the point. Written against raw text the sentence regexes need
-- variable-length classes like `[ \r\n]+`, and a variable-length run can be consumed
-- PARTIALLY: `[.!?][ \r\n]+[^A-Z]` matched ".\r\n\r\nAs late as" by taking three of the
-- four whitespace characters and handing the fourth to `[^A-Z]`, so a paragraph break
-- read as "not a sentence end" and one quote ran 917 characters through three following
-- paragraphs. With runs guaranteed length 1 that is not a bug to guard against, it is
-- unrepresentable.
--
-- The blank line is kept — rather than flattening everything to spaces — because it is
-- the ONLY thing that bounds a colon-led list. "…were also used for this conversion:"
-- followed by one game per line has no sentence punctuation anywhere, so without the
-- paragraph break there is nothing to stop a quote at. 3008 of 3096 notes with newlines
-- contain one.
--
-- chr(1) is a safe sentinel: the corpus contains no control characters other than CR and
-- LF (verified — also no tabs), so it cannot collide with real text. It exists only to
-- protect the paragraph marker from the space-collapsing pass that follows it.
CREATE OR REPLACE MACRO text_norm(txt) AS
  replace(
    regexp_replace(
      regexp_replace(replace(txt, chr(13), ''),      -- CR never appears without LF
                     '[ \t]*\n[ \t]*\n[ \t\n]*', chr(1), 'g'),  -- blank line → sentinel
      '[ \t\n]+', ' ', 'g'),                          -- every other run → one space
    chr(1), chr(10));                                 -- sentinel → the paragraph newline

-- ── Sentence boundaries ──────────────────────────────────────────────────────
-- A sentence ends at [.!?] followed by whitespace and a CAPITAL letter, or at a
-- paragraph break regardless of punctuation. Both inputs are assumed canonical: pass
-- text through `text_norm` first, or the length-1 guarantee below does not hold.
--
-- The capital is the whole trick. Source prose is dense with abbreviations that end in a
-- period and are followed by a space — "Vol. 1", "p. 83", "No. 5" — and every one of
-- them sits directly against the locator a citation campaign is trying to capture. A
-- naive split on ". " truncates the quote immediately before the thing it exists to
-- show. Requiring a capital costs nothing and removes the entire class.
--
-- A bare `\n` is a boundary too, with no punctuation required: it is a paragraph break,
-- which ends a sentence whether or not the author punctuated it. That is what lets a
-- mention inside a colon-led list start its quote at the list, not paragraphs earlier.
--
-- The search window ends at `pos` INCLUSIVE, and the arithmetic carries the matching +1.
-- Ending it at pos-1 is the obvious form and it is wrong in the commonest case of all:
-- when the term begins its own sentence, the prefix stops on the boundary whitespace,
-- no capital is visible, the match fails, and the fallback runs the span back to
-- character 1 — quoting the entire document up to that point. It stays verbatim and
-- keeps the locator, so neither of the campaign's downstream assertions sees anything
-- wrong. Only a fixture catches it, which is why there is one.
CREATE OR REPLACE MACRO _sent_start(txt, pos) AS
  CASE WHEN regexp_extract(substr(txt, 1, pos),
                           '(?s)^.*(?:[.!?][ \n]|\n)([A-Z].*)$', 1) = '' THEN 1
       ELSE pos - len(regexp_extract(substr(txt, 1, pos),
                                     '(?s)^.*(?:[.!?][ \n]|\n)([A-Z].*)$', 1)) + 1
  END;

-- A PARAGRAPH BREAK ends the tail, terminator or not, so the search string is truncated
-- at the first `\n` before the sentence scan runs. Source notes put lists under a colon —
-- "…announced 'now 4 more games' were also used for this conversion:" followed by one
-- game per line — and a list has no sentence punctuation at all, so without this the span
-- runs to the end of the document. Truncating is safe HERE and only here: `sentence_span`
-- has already passed its anchor, so a locator in a following paragraph is inside the span
-- before this ever applies.
--
-- After that truncation the string holds no newlines, so the sentence scan is a
-- space-only, single-character affair. On raw text this needed `[ \r\n]+` and a
-- `[^A-Z \r\n]` guard, because a variable-length run could be split — see `text_norm`.
CREATE OR REPLACE MACRO _sent_tail(txt, pos) AS
  len(regexp_extract(
        regexp_replace(substr(txt, pos), '(?s)\n.*$', ''),
        '(?s)^(?:[^.!?]|[.!?][^ ]|[.!?] [^A-Z])*[.!?]?'));

-- The verbatim span running from the start of the sentence containing `from_pos` through
-- the end of the sentence containing `thru_pos`. Pass the same position twice for "the
-- sentence containing this point".
--
-- TWO positions rather than one, because the thing worth quoting frequently straddles a
-- boundary: "…were in Cash Box, Oct-1-1960. On page 61, Paul Huebsch…" puts the date in
-- one sentence and the page in the next, and a quote carrying only the first is verbatim
-- and useless. The caller passes whatever it must not cut off.
--
-- The result is always a substring of `txt`, which is what makes it quotable. A campaign
-- should still assert that downstream — see `text_checks` for the shape of that test.
CREATE OR REPLACE MACRO sentence_span(txt, from_pos, thru_pos) AS
  substr(txt,
         _sent_start(txt, from_pos),
         (thru_pos - _sent_start(txt, from_pos) + 1) + _sent_tail(txt, thru_pos + 1));

-- ── Occurrences, with positions ──────────────────────────────────────────────
-- One row per (document, term, occurrence). Returns `txt` alongside so a caller can cut
-- windows and sentences without re-joining the source.
--
-- Position is reconstructed from the split rather than searched for: `str_split_regex`
-- gives the text BETWEEN hits and `regexp_extract_all` gives the hits, so hit i begins
-- after the first i gaps and the first i-1 hits. Exact, and it costs one pass.
--
-- The alternative — `instr(txt, hit)` — is what a first version does and it is wrong for
-- precisely the rows that matter: it finds the FIRST occurrence of that text, so every
-- repeat of a term gets the first one's position, and any preceding-context window built
-- from it describes the wrong sentence.
--
-- `pre` is the combined-alternation prefilter: test each document ONCE before fanning it
-- out across the whole vocabulary, so documents mentioning nothing pay one regex instead
-- of one per term. Built from the vocabulary itself, so there is no second source of
-- truth to drift.
CREATE OR REPLACE MACRO mention_positions(src, vocab) AS TABLE
WITH any_term AS (
  SELECT string_agg('(?:' || term_re || ')', '|') AS re FROM query_table(vocab)
),
pre AS (
  SELECT s.key, s.txt
  FROM query_table(src) s, any_term a
  WHERE s.txt IS NOT NULL AND regexp_matches(s.txt, a.re)
),
split AS (
  SELECT p.key, p.txt, v.term,
         regexp_extract_all(p.txt, v.term_re) AS hits,
         str_split_regex(p.txt, v.term_re)    AS gaps
  FROM pre p CROSS JOIN query_table(vocab) v
  WHERE regexp_matches(p.txt, v.term_re)
)
SELECT
  s.key, s.txt, s.term,
  i.i          AS occurrence,
  s.hits[i.i]  AS hit,
  CAST(1 + list_sum(list_transform(list_slice(s.gaps, 1, i.i), lambda x: len(x)))
         + coalesce(list_sum(list_transform(list_slice(s.hits, 1, i.i - 1),
                                            lambda x: len(x))), 0) AS BIGINT) AS pos
FROM split s, unnest(range(1, len(s.hits) + 1)) AS i(i);

-- ── Self-test ────────────────────────────────────────────────────────────────
-- Empty when healthy, and DATA-INDEPENDENT on purpose: every case below is a literal, so
-- these assert the mechanics rather than the corpus and cannot be quieted by the data
-- changing underneath them. Macros are invisible to any column or row sweep, so a
-- hand-written smoke test is the only thing that can catch one breaking.
CREATE OR REPLACE VIEW text_checks AS
WITH fixtures(name, got, want) AS (VALUES
  -- text_norm: every run to one character, blank lines surviving as exactly one newline
  ('norm collapses CRLF to a space',
   text_norm('one' || chr(13) || chr(10) || 'two'), 'one two'),
  ('norm collapses a run of spaces',
   text_norm('one    two'), 'one two'),
  ('norm keeps a blank line as one newline',
   text_norm('one' || chr(13) || chr(10) || chr(13) || chr(10) || 'two'), 'one' || chr(10) || 'two'),
  ('norm collapses a long blank run to one newline',
   text_norm('one' || chr(10) || chr(10) || chr(10) || '   ' || chr(10) || 'two'), 'one' || chr(10) || 'two'),
  -- the sentence containing a point, with the previous sentence excluded
  ('sentence_span picks one sentence',
   sentence_span('Foo was a kit. The ad ran in March 1945. Later notes.', 16, 16),
   'The ad ran in March 1945.'),
  -- an abbreviation is not a sentence end: the span must reach past "Vol. 1"
  ('sentence_span survives Vol. and p.',
   sentence_span('See The Encyclopedia Vol. 1 p. 137 for this. Next one.', 5, 5),
   'See The Encyclopedia Vol. 1 p. 137 for this.'),
  -- a paragraph break bounds the start, and needs no punctuation to do it
  ('sentence_span stops at a paragraph break',
   sentence_span('Ends here' || chr(10) || 'Starts here. And on.', 12, 12),
   'Starts here.'),
  -- two positions spanning a boundary: the page sits in the following sentence
  ('sentence_span reaches a later sentence',
   sentence_span('It was in Cash Box, Oct-1-1960. On page 61, Paul spoke. Done.', 11, 40),
   'It was in Cash Box, Oct-1-1960. On page 61, Paul spoke.'),
  -- no preceding boundary at all: the span starts at character 1
  ('sentence_span handles a document start',
   sentence_span('Billboard 1945 p20. Next.', 1, 1),
   'Billboard 1945 p20.'),
  -- a paragraph break must END the span too, not just bound its start
  ('sentence_span stops AT a paragraph break',
   sentence_span('Ends here.' || chr(10) || 'And on.', 1, 1),
   'Ends here.'),
  -- a colon-led list has no sentence punctuation: the paragraph break is the only thing
  -- that can stop it, and without that rule one real quote ran to the end of its note
  ('sentence_span stops a colon-led list at the break',
   sentence_span('Ad in BB p82 named these: Mascot Mystic' || chr(10) || 'Later text.', 7, 12),
   'Ad in BB p82 named these: Mascot Mystic'),
  -- ...but a locator in the NEXT paragraph must still be reachable: the break stops the
  -- tail only after the anchor, never before it
  ('sentence_span crosses a break to reach the anchor',
   sentence_span('In Cash Box.' || chr(10) || 'On page 61 it ran. Then more.', 4, 20),
   'In Cash Box.' || chr(10) || 'On page 61 it ran.')
)
SELECT 'text_' || name AS check,
       'got [' || coalesce(got, '<null>') || '] want [' || want || ']' AS detail
FROM fixtures WHERE got IS DISTINCT FROM want

UNION ALL
-- Every occurrence is found, not just the first, and each carries its own position: the
-- two failure modes the position arithmetic exists to prevent.
SELECT 'text_mention_positions_repeats', detail FROM (
  WITH s(key, txt) AS (VALUES ('m1', 'A Billboard ad, then a second Billboard ad here.')),
       v(term, term_re) AS (VALUES ('Billboard', 'Billboard'))
  SELECT CASE
    WHEN count(*) <> 2 THEN 'expected 2 occurrences, got ' || count(*)
    WHEN count(DISTINCT pos) <> 2 THEN 'occurrences share a position — positions are not per-occurrence'
    WHEN min(pos) <> 3 OR max(pos) <> 31 THEN 'positions wrong: ' || string_agg(pos::VARCHAR, ',' ORDER BY pos)
  END AS detail
  FROM mention_positions('s', 'v')
) WHERE detail IS NOT NULL;
