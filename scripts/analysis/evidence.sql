-- Evidence bridge — the source text behind a claim, as SQL.
--
-- `.read` this from a campaign analysis AFTER flipcommons' foundation to get the
-- cached SOURCE TEXT alongside the decoded catalog, so a campaign can join the rows
-- it is about to emit against the evidence they rest on. Before this existed each
-- campaign invented its own bridge — a `sys.path.insert` into pinexplore's internals,
-- a hardcoded absolute path, or "run this one from the pinexplore repo root".
--
-- SCOPE — pinexplore's web-scrape cache, and nothing else. That cache is EVIDENCE:
-- raw source text, the same durable blob `make verify-quotes` checks quotes against.
-- pinexplore's `explore.duckdb` is deliberately NOT attached here — it is pinexplore's
-- derived cross-source model, and flipcommons' analysis README already routes
-- cross-source work there. The practical consequence, worth knowing before you reach
-- for this: it serves campaigns citing `https:` refs. Patches citing `ipdb:` (today the
-- bulk of the corpus by citation count) resolve their evidence through
-- `scripts/quote_verify`, not through this layer.
--
-- WHERE THE PATHS RESOLVE. This file lives in flippatch, but every path in it is
-- relative to the FLIPCOMMONS checkout, because that is where the analysis runner
-- `cd`s before invoking DuckDB. Same frame as `catalog.sql`'s own literal
-- 'backend/db.analytics.duckdb'. So the ATTACH below reads `../pinexplore/...` — do not
-- "fix" it to `../../pinexplore` on the reasoning that this file sits two levels down
-- in flippatch; it is not resolved from here. `ATTACH` takes a string LITERAL — no
-- expression, no `getenv()`, no `getvariable()` — so unlike the rest of flippatch's
-- tooling this cannot honour a `PINEXPLORE_DIR` override. The sibling layout is
-- assumed, exactly as the foundation assumes it from the other direction.
--
-- WHY THERE IS NO FULL-TEXT-SEARCH VIEW. The cache carries an FTS5 index
-- (`pages_fts`), and it is tempting to expose it. It does not survive the trip:
-- DuckDB has no `MATCH` operator, the FTS virtual table read through a sqlite ATTACH
-- hands back every column as `BLOB`, and the one route that does work —
-- `sqlite_query('ev', '… MATCH …')` — refuses lateral column parameters, so it can
-- never be joined to a catalog row. That join is the entire point. The corpus is ~315
-- pages / ~2 MB of text, where a brute-force scan of the typed `text` column below
-- costs tens of milliseconds and supports arbitrary correlated joins, regex and
-- offset windows. So: no index, full scans, and everything joinable.
--
-- USAGE, from a campaign analysis file:
--
--     .read scripts/analysis/catalog.sql
--     .read ../flippatch/scripts/analysis/evidence.sql
--
-- `evidence_checks` and `evidence_context` are discovered by the runner, so a
-- consumer inherits this layer's invariants and its staleness watermark without
-- folding them into its own views. See flipcommons' scripts/analysis/README.md.

INSTALL sqlite;
LOAD sqlite;
ATTACH IF NOT EXISTS '../pinexplore/ingest_sources/web/cache.sqlite' AS ev (TYPE sqlite, READ_ONLY);

-- The normalization `make verify-quotes` applies to the SOURCE side before testing a
-- quote as a substring — smart quotes straightened, whitespace runs collapsed. It
-- mirrors `scripts/quote_verify/verify_quotes.py::normalize`; the two must agree, or a
-- campaign's own pre-flight and the real gate will disagree about the same quote.
--
-- Admitted as a shared macro on flipcommons' EDITING.md rule — a mechanic, not a
-- judgment. It encodes no threshold and no per-source convention; it is the definition
-- of "verbatim" this repo already enforces in Python, expressed once more in SQL.
-- Text extraction hard-wraps prose that renders as spaces, which is why the whitespace
-- clause is not cosmetic.
CREATE OR REPLACE MACRO evidence_norm(s) AS
  regexp_replace(
    replace(replace(replace(replace(COALESCE(s, ''), '“', '"'), '”', '"'), '‘', ''''), '’', ''''),
    '\s+', ' ', 'g');

-- Every quotable cached page, typed.
--
-- Reads `ev.pages` directly rather than the FTS table so `text` arrives as a real
-- VARCHAR (see the header). Blank-text pages are filtered OUT: a handful of
-- JS-rendered sites cache with `http_status = 200` and no extracted text at all, and
-- they are not evidence — nothing can be quoted from them. That is a normal state of
-- the cache, not a fault, so it is reported by `evidence_context` rather than failed
-- by `evidence_checks`.
--
-- One caveat that bites URL lookups: `pages.url` is the NORMALIZED url (pinexplore's
-- `web_cache.normalize_url` runs on the way in), while a patch's `cite.ref` is written
-- by hand. They agree for most refs and can differ on trailing slashes and case. Join
-- on `evidence_norm`-free equality when you control both sides; when matching against
-- patch text, expect to normalize.
CREATE OR REPLACE VIEW evidence_pages AS
  SELECT
    url,
    title,
    text,
    evidence_norm(text) AS text_norm,
    length(text)        AS n_chars,
    http_status,
    content_type,
    first_fetched_at,
    last_fetched_at,
    last_updated,
    content_sha
  FROM ev.pages
  WHERE text IS NOT NULL AND trim(text) <> '';
COMMENT ON VIEW evidence_pages IS
  'One row per quotable cached page — url, title, raw text plus text_norm (the verbatim-gate normalization), size, fetch stamps and content_sha. Blank-text pages are excluded; join to this to test a claim against its source.';

-- The evidence watermark, printed alongside `analysis_context` on every run.
--
-- It exists because the two inputs to a campaign drift at completely different rates:
-- the catalog moves with every patch and interactive edit, while the cache moves when
-- someone re-fetches a page. A result that changed because a source page was refetched
-- looks exactly like a broken query until this row tells you otherwise.
CREATE OR REPLACE VIEW evidence_context AS
  SELECT
    (SELECT count(*) FROM ev.pages)                                   AS cached_pages,
    (SELECT count(*) FROM evidence_pages)                             AS quotable_pages,
    (SELECT count(*) FROM ev.pages
       WHERE text IS NULL OR trim(text) = '')                         AS blank_text_pages,
    (SELECT min(last_fetched_at) FROM ev.pages)                       AS oldest_fetch,
    (SELECT max(last_fetched_at) FROM ev.pages)                       AS newest_fetch;
COMMENT ON VIEW evidence_context IS
  'One row — the evidence watermark: cached page count, how many are quotable, how many cached blank, and the oldest/newest fetch stamps. Printed by every analysis run that reads this layer.';

-- Empty when healthy.
--
-- Deliberately short. Two things this layer CANNOT usefully check, and does not
-- pretend to: an unreachable cache never reaches here at all (the ATTACH above fails
-- first, loudly, with the path in the message), and a blank-text page is a normal
-- cache state reported by `evidence_context`, not a fault — an invariant that fires on
-- healthy data is worse than no invariant, because it trains a reader to skip the gate.
CREATE OR REPLACE VIEW evidence_checks AS
  -- An empty cache attaches cleanly and then silently starves every consumer: each
  -- join to `evidence_pages` returns nothing, which reads identically to "this
  -- campaign has no evidence" rather than "the cache was never pulled".
  SELECT 'evidence_cache_empty' AS check, NULL::VARCHAR AS detail
  WHERE (SELECT count(*) FROM ev.pages) = 0
  UNION ALL
  -- Every page cached blank would mean text extraction is broken wholesale rather than
  -- failing on the few JS-rendered outliers it normally does.
  SELECT 'evidence_all_pages_blank', NULL::VARCHAR
  WHERE (SELECT count(*) FROM ev.pages) > 0
    AND (SELECT count(*) FROM evidence_pages) = 0;
COMMENT ON VIEW evidence_checks IS
  'Empty when healthy — invariants over the attached web-scrape cache: the cache is non-empty, and not every page cached blank. Discovered and gated by the analysis runner.';
