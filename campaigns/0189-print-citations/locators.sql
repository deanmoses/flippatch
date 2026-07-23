-- locators.sql — the locator grammar: what a citation's date, page and volume look like
-- in IPDB's prose, and how to turn one into the parts a `sources:` node and a `cite:`
-- need.
--
-- READ ORDER. `.read` by `citations.sql`, which owns every `.read` in this campaign.
-- Depends on nothing but DuckDB itself: no catalog view, no corpus scan, no notion of
-- which publications exist. That independence is the point of the file — it is a PARSER,
-- and the mining that applies it lives next door.
--
-- WHY A RULES TABLE AND MACROS, not views. Views would have to be views OVER the
-- mentions, which would make the grammar depend on the corpus scan and put the
-- dependency backwards. As a declarative table plus pure functions it depends on
-- nothing, and — the real prize — every rule becomes testable against a literal. Each
-- fixture at the bottom corresponds to a bug this campaign actually shipped: a full
-- month name degrading to a bare year, a page list truncating to its first page, an
-- impossible date minting an issue that never existed.
--
-- THE THREE AXES ARE INDEPENDENT. A formulation is a tuple of shape names — (date, page,
-- volume) — rather than one bespoke regex per phrasing. Adding a phrasing is one row,
-- never an edit to an existing pattern, and an unhandled phrasing surfaces as a NULL
-- shape instead of being silently absorbed by a neighbour.

-- ── The rules ────────────────────────────────────────────────────────────────
-- axis, priority, name, regex. Lower prio wins when several match, so rules are ordered
-- most-specific-first WITHIN an axis and are otherwise independent.
--
-- MONTH NAMES ARE SPELLED OUT, not approximated by `[A-Z][a-z]{2,8}`. The loose form
-- matched any capitalised word before a year, so "Fall 1986" and "Machines 1931" parsed
-- as dates whose month lookup then returned NULL — degrading a real seasonal issue to a
-- bare year and inventing an issue out of a book title. A rule that matches the wrong
-- thing and then fails quietly downstream is worse than one that does not match.
--
-- Three dash-date rules exist because IPDB writes 'Aug-21-1954', 'June-17-1939' and
-- '08-31-1940'. The abbreviated pattern demands a dash after exactly three letters, so
-- without the second the full-month form degraded to 'bare-year'; without the third the
-- all-numeric form did the same, and five real dates became five fabricated year-level
-- issues. The 'monDD-yyyy' rule is a genuine IPDB typo ('Dec15-1945') — kept because a
-- rule table makes a typo cost one row instead of a special case.
CREATE OR REPLACE VIEW shape_rules AS
SELECT * FROM (VALUES
  -- ── DATE ──
  ('date',  10, 'mon-dd-yyyy',    '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-[0-9]{1,2}-[0-9]{4}'),
  ('date',  11, 'month-dd-yyyy',  '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]+-[0-9]{1,2}-[0-9]{4}'),
  ('date',  12, 'monDD-yyyy',     '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[0-9]{1,2}-[0-9]{4}'),
  ('date',  20, 'mm/dd/yyyy',     '[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}'),
  -- NO two-digit-year rule, and this is measured rather than an oversight. IPDB does
  -- write "BB 4/17/43 pg 67", but the mm/dd/yy form appears in 183 models and almost all
  -- of them are MANUFACTURE dates in ordinary prose — "only two sample games were made
  -- on 02/20/50". A rule for it would harvest those into citations wherever one happens
  -- to fall inside a publication window, and it would have to invent a century to do it.
  -- One recoverable row is not worth a detector that fabricates issue dates; that row
  -- drops as 'no parsable date', which is the safe failure. A fixture below pins it.
  ('date',  25, 'mm-dd-yyyy',     '[0-9]{1,2}-[0-9]{1,2}-(?:18|19|20)[0-9]{2}'),
  ('date',  30, 'month d, yyyy',  '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* [0-9]{1,2}, [0-9]{4}'),
  ('date',  40, 'mon-yyyy',       '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*-[0-9]{4}'),
  ('date',  50, 'month yyyy',     '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*,? (?:18|19|20)[0-9]{2}'),
  -- A seasonal issue is a real issue with a real address; the quarterlies (Coin Slot)
  -- date this way and nothing else can name them.
  ('date',  55, 'season yyyy',    '(?:Spring|Summer|Fall|Autumn|Winter),? (?:18|19|20)[0-9]{2}'),
  ('date',  60, 'bare-year',      '(?:18|19|20)[0-9]{2}'),
  -- ── PAGE ──
  ('page',   8, 'pp N, M',        'pp\.? ?[0-9]{1,4}(?:, ?[0-9]{1,4})+'),
  ('page',   9, 'pages N, M, O',  'pages [0-9]{1,4}(?:, [0-9]{1,4})+(?:,? and [0-9]{1,4})?'),
  ('page',  10, 'pages N and M',  'pages [0-9]{1,4} and [0-9]{1,4}'),
  ('page',  11, 'pages N-M',      'pages? [0-9]{1,4}[-–][0-9]{1,4}'),
  ('page',  12, 'pp N-M',         'pp\.? ?[0-9]{1,4}[-–][0-9]{1,4}'),
  ('page',  20, 'pages N',        'pages [0-9]{1,4}'),
  ('page',  21, 'page N',         'page [0-9]{1,4}'),
  ('page',  30, 'pp N',           'pp\.? ?[0-9]{1,4}'),
  ('page',  31, 'pN / p. N',      '\bp\.? ?[0-9]{1,4}'),
  ('page',  32, 'pg N',           '\bpgs?\.? ?[0-9]{1,4}'),
  -- ── VOLUME (books and numbered magazine issues) ──
  ('vol',   10, 'Volume N',       'Volume [0-9IVX]+'),
  ('vol',   20, 'Vol N',          'Vol\.? ?[0-9IVX]+')
) AS t(axis, prio, shape, re);

CREATE OR REPLACE VIEW month_numbers AS
SELECT * FROM (VALUES
  ('Jan',1),('Feb',2),('Mar',3),('Apr',4),('May',5),('Jun',6),
  ('Jul',7),('Aug',8),('Sep',9),('Oct',10),('Nov',11),('Dec',12)
) AS t(mon3, mon_num);

-- ── Resolving a rule against a string ────────────────────────────────────────
-- The winning shape on one axis, and its matched text. NULL when nothing matches, which
-- is what a caller should treat as "this axis is absent" rather than coercing to a
-- catch-all.
CREATE OR REPLACE MACRO loc_shape(txt, ax) AS
  (SELECT r.shape FROM shape_rules r
    WHERE r.axis = ax AND regexp_matches(txt, r.re) ORDER BY r.prio LIMIT 1);

CREATE OR REPLACE MACRO loc_match(txt, ax) AS
  (SELECT regexp_extract(txt, r.re) FROM shape_rules r
    WHERE r.axis = ax AND regexp_matches(txt, r.re) ORDER BY r.prio LIMIT 1);

-- ── Decoding a matched date ──────────────────────────────────────────────────
-- Year is unambiguous in every shape: the only 4-digit run in the value.
CREATE OR REPLACE MACRO loc_year(shape, val) AS
  CAST(regexp_extract(val, '(?:18|19|20)[0-9]{2}') AS INTEGER);

-- Named month, every lettered shape: first three letters, looked up. Works for both
-- 'Aug' and 'August' because the lookup is on the 3-letter prefix.
CREATE OR REPLACE MACRO loc_month(shape, val) AS
  CASE shape
    WHEN 'mm/dd/yyyy'  THEN CAST(regexp_extract(val, '^([0-9]{1,2})/', 1) AS INTEGER)
    WHEN 'mm-dd-yyyy'  THEN CAST(regexp_extract(val, '^([0-9]{1,2})-', 1) AS INTEGER)
    WHEN 'bare-year'   THEN NULL
    WHEN 'season yyyy' THEN NULL
    ELSE (SELECT mon_num FROM month_numbers
           WHERE mon3 = substr(regexp_extract(val, '[A-Z][a-z]+'), 1, 3))
  END;

CREATE OR REPLACE MACRO loc_day(shape, val) AS
  CASE shape
    WHEN 'mon-dd-yyyy'   THEN CAST(regexp_extract(val, '-([0-9]{1,2})-', 1) AS INTEGER)
    WHEN 'month-dd-yyyy' THEN CAST(regexp_extract(val, '-([0-9]{1,2})-', 1) AS INTEGER)
    WHEN 'monDD-yyyy'    THEN CAST(regexp_extract(val, '([0-9]{1,2})-', 1) AS INTEGER)
    WHEN 'mm/dd/yyyy'    THEN CAST(regexp_extract(val, '^[0-9]{1,2}/([0-9]{1,2})/', 1) AS INTEGER)
    WHEN 'mm-dd-yyyy'    THEN CAST(regexp_extract(val, '^[0-9]{1,2}-([0-9]{1,2})-', 1) AS INTEGER)
    WHEN 'month d, yyyy' THEN CAST(regexp_extract(val, ' ([0-9]{1,2}),', 1) AS INTEGER)
    ELSE NULL
  END;

CREATE OR REPLACE MACRO loc_season(shape, val) AS
  CASE shape WHEN 'season yyyy'
    THEN lower(regexp_extract(val, '(Spring|Summer|Fall|Autumn|Winter)', 1))
    ELSE NULL END;

-- ── Issue identity ───────────────────────────────────────────────────────────
-- The slug is an ADDRESS, not data: ISO date when dated, year-month when the day is
-- unknown, `year-season` for a seasonal. The y/m/d values carry the date for sort and
-- display, and nothing parses the slug back.
--
-- VALIDITY IS PART OF IDENTITY. IPDB contains real date typos ("Jun-39-1962"), and a
-- date that isn't a date cannot name an issue — so an invalid one yields NULL and the
-- caller drops the row with a reason, rather than minting a source node for an issue
-- that never existed. TRY_CAST does the calendar properly, so Feb 30 fails too, not just
-- day > 31.
--
-- A BARE YEAR IS NOT AN ISSUE, and yields NULL. Billboard published weekly; "Billboard
-- 1940" addresses no object a reader could check, and emitting it minted `sources:`
-- nodes for issues that never existed. Every such row in the corpus turned out to be a
-- parse failure with the real date sitting in the same sentence — which is what the
-- mm-dd-yyyy and month-name rules above now catch — so this drops nothing real.
CREATE OR REPLACE MACRO loc_issue_slug(y, m, d, season) AS
  CASE
    WHEN y IS NULL                   THEN NULL
    WHEN y NOT BETWEEN 1880 AND 2030 THEN NULL
    WHEN season IS NOT NULL          THEN printf('%04d-%s', y, season)
    WHEN m IS NULL                   THEN NULL
    WHEN m NOT BETWEEN 1 AND 12      THEN NULL
    WHEN d IS NULL                   THEN printf('%04d-%02d', y, m)
    WHEN TRY_CAST(printf('%04d-%02d-%02d', y, m, d) AS DATE) IS NULL THEN NULL
    ELSE printf('%04d-%02d-%02d', y, m, d)
  END;

-- ── Page locator ─────────────────────────────────────────────────────────────
-- The convention: lowercase 'p.', a space, the number(s). Locators dedup by EXACT TEXT,
-- so normalizing here is what stops 'p83' and 'p. 83' minting two CitationInstances for
-- one page.
--
-- SEPARATE pages, not a range: "pages 78 and 83" is p. 78 and p. 83, and "pp 132, 161"
-- is two of them. Folding either to '78-83' would silently claim the pages between them
-- as evidence. Every number in the match is kept — reading the list off the matched text
-- rather than re-parsing its punctuation is what stops a new list form from truncating
-- to its first page, which is exactly how "pp 132, 161" once became "p. 132".
CREATE OR REPLACE MACRO loc_page(shape, val) AS
  CASE
    WHEN shape IS NULL THEN NULL
    WHEN shape IN ('pages N and M', 'pages N, M, O', 'pp N, M')
      THEN 'pp. ' || array_to_string(regexp_extract_all(val, '[0-9]{1,4}'), ', ')
    WHEN shape IN ('pages N-M', 'pp N-M')
      THEN 'pp. ' || array_to_string(regexp_extract_all(val, '[0-9]{1,4}'), '-')
    ELSE 'p. ' || regexp_extract(val, '([0-9]{1,4})', 1)
  END;

-- ── Self-test ────────────────────────────────────────────────────────────────
-- Empty when healthy, and DATA-INDEPENDENT: every case is a literal, so these assert the
-- grammar rather than the corpus. Each one corresponds to a bug this campaign shipped —
-- if a fixture ever looks arbitrary, read the rule comment above it before deleting it.
CREATE OR REPLACE VIEW locator_checks AS
WITH cases(name, got, want) AS (VALUES
  -- a full month name must not degrade to a bare year
  ('shape full month name', loc_shape('in Billboard June-17-1939 p20', 'date'), 'month-dd-yyyy'),
  ('shape abbreviated month', loc_shape('in Billboard Aug-21-1954 p78', 'date'), 'mon-dd-yyyy'),
  -- an all-numeric dash date, likewise
  ('shape numeric dash date', loc_shape('Billboard article dated 08-31-1940 page 122', 'date'), 'mm-dd-yyyy'),
  -- a season is a real issue address, not a bare year
  ('shape seasonal issue', loc_shape('The Coin Slot, Fall 1986, page 40', 'date'), 'season yyyy'),
  -- a capitalised non-month before a year must NOT parse as a date
  ('shape rejects non-month word', loc_shape('Pinball Machines 1931 and later', 'date'), 'bare-year'),
  -- the deliberately unsupported two-digit year: no date at all, which is the safe drop
  ('shape rejects two-digit year', loc_shape('(BB 4/17/43 pg 67)', 'date'), NULL),
  -- page lists are lists, not ranges
  ('page comma list', loc_page(loc_shape('BB 07/06/1946, pp 132, 161', 'page'),
                               loc_match('BB 07/06/1946, pp 132, 161', 'page')), 'pp. 132, 161'),
  ('page and-list', loc_page('pages N and M', 'pages 78 and 83'), 'pp. 78, 83'),
  ('page range stays a range', loc_page('pages N-M', 'pages 78-83'), 'pp. 78-83'),
  ('page normalizes p83', loc_page('pN / p. N', 'p83'), 'p. 83'),
  ('page pg form', loc_page(loc_shape('pg 67', 'page'), loc_match('pg 67', 'page')), 'p. 67'),
  -- month/day decoding across shapes
  ('decode month from mm-dd-yyyy', CAST(loc_month('mm-dd-yyyy', '08-31-1940') AS VARCHAR), '8'),
  ('decode day from mon-dd-yyyy', CAST(loc_day('mon-dd-yyyy', 'Aug-21-1954') AS VARCHAR), '21'),
  ('decode month from full name', CAST(loc_month('month yyyy', 'September 1935') AS VARCHAR), '9'),
  ('decode season', loc_season('season yyyy', 'Fall 1986'), 'fall'),
  -- issue identity: validity is part of it
  ('slug full date', loc_issue_slug(1945, 9, 29, NULL), '1945-09-29'),
  ('slug year-month', loc_issue_slug(1932, 6, NULL, NULL), '1932-06'),
  ('slug seasonal', loc_issue_slug(1986, NULL, NULL, 'fall'), '1986-fall'),
  ('slug rejects impossible day', loc_issue_slug(1962, 6, 39, NULL), NULL),
  ('slug rejects Feb 30', loc_issue_slug(1934, 2, 30, NULL), NULL),
  ('slug rejects a bare year', loc_issue_slug(1940, NULL, NULL, NULL), NULL),
  ('slug rejects an absurd year', loc_issue_slug(1234, 5, 6, NULL), NULL)
)
SELECT 'locator_' || name AS check,
       'got [' || coalesce(got, '<null>') || '] want [' || coalesce(want, '<null>') || ']' AS detail
FROM cases WHERE got IS DISTINCT FROM want;
