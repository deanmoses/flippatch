-- The external data sources bridge: pinexplore's dumps, beside the live catalog.
--
-- `.read` this (or a per-source file that reads it) from a campaign analysis AFTER
-- flipcommons' foundation, to compare what an external source says against what the
-- catalog holds. Every per-source file in this directory reads it first, so a campaign
-- normally reaches for `ipdb.sql` rather than this.
--
-- SCOPE — pinexplore's `explore.duckdb`, and only its published marts: the bare
-- `ipdb.*` / `opdb.*` schemas, each holding that source parsed, merged and validated
-- into our vocabulary. Everything under `*_raw`, `*_stg` and `*_ref` is pinexplore's own
-- working material, free to be reshaped without notice, and reading it is what
-- `external_data_sources_boundary_checks` below fails on. Source TEXT for citing a claim is a
-- different concern and lives in `../evidence.sql`, over the web-scrape cache.
--
-- CATALOG DATES ARE ALWAYS KIND-QUALIFIED. The foundation's `models.year` / `models.month`
-- are coalesced display columns -- a project date fills in where no production date
-- exists -- so comparing either against a source asserts the wrong fact on every
-- project-dated machine. This layer reads `production_*` / `project_*` explicitly, and
-- IPDB's side carries `date_kind` beside every year it quotes. The one undifferentiated
-- date is OPDB's own, which has no kinds to tell.
--
-- SUMMARY METRICS NAME THEIR GRAIN (`_listings`, `_assignments`, `_values`, …), and
-- when a family's parts deliberately do not sum, the remainder gets a named metric --
-- an honest reader who notices a gap should find the explanation in the next row, not
-- in a query against a private view.
--
-- WHERE A WORDING FIX LIVES. A vocabulary value's spelling says which repo resolves it:
-- slug-shaped means pinexplore translated it, so a mapping decision updates pinexplore's
-- ref table; source display wording resolves through the catalog's aliases, so the fix
-- is an alias patch here.
--
-- FINDINGS ARE VIEWS, NEVER CHECKS. A comparison view returning rows is the normal,
-- healthy state -- that is the worklist a campaign is built to work down. The runner
-- fails nonzero on a row from ANY public `*_checks` view in the session, so a finding
-- placed in one would break every campaign that reads this layer. `*_checks` here holds
-- only this layer's own invariants: the attach resolved, a join preserved its grain, a
-- classification is exhaustive. Same line flipcommons' `audit.sql` draws between
-- `audit_findings` and `audit_checks`.
--
-- WHERE THE PATHS RESOLVE. Every path is relative to the FLIPCOMMONS checkout, because
-- that is where the analysis runner `cd`s before invoking DuckDB -- the same frame
-- `catalog.sql`'s own literal 'backend/db.analytics.duckdb' is in. `ATTACH` takes a
-- string LITERAL, so this cannot honour a `PINEXPLORE_DIR` override; the sibling layout
-- is assumed, as `evidence.sql` assumes it.
--
-- The alias is `px`, matching what campaigns 0268/0269/0277/0278 already attach, so this
-- layer and a campaign that attaches it directly cannot end up with two handles on one
-- file.

ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- The dump watermark, printed alongside `analysis_context` on every run.
--
-- One row per ingested artifact rather than one per source: IPDB alone arrives as two
-- Xantari snapshots that pinexplore merges, and "which snapshots went in" is the
-- question this answers. `observed_at` is the artifact's claim about its own currency --
-- for a Xantari snapshot, the `LastRefreshDateUtc` in its header -- and is NULL for an
-- export that carries no date, which is an honest absence rather than a missing value.
-- `acquired_on` is the other fact: when the file was manually downloaded, recorded by
-- hand in pinexplore's acquisition log and NULL where nobody recorded it.
--
-- pinexplore assembles this itself in `ingest.watermarks`; this view is a pass-through
-- so that a campaign gets the watermark from the same place it gets everything else.
--
-- It exists because a campaign's two inputs move at unrelated rates: the catalog changes
-- with every patch, the dumps change when someone drops in a new scrape. A result that
-- moved because a newer snapshot landed is indistinguishable from a broken query until
-- this row says otherwise.
CREATE OR REPLACE VIEW external_data_sources_context AS
  SELECT source, artifact_kind, artifact, observed_at, acquired_on, n_records
  FROM px.ingest.watermarks;
COMMENT ON VIEW external_data_sources_context IS
  'One row per ingested external-source artifact — source, kind, which artifact, the date it claims for itself, the recorded manual-download date, and its record count. Printed by every analysis run that reads this layer.';

-- WHAT THIS LAYER READS FROM PINEXPLORE, AND WHETHER IT SHOULD.
--
-- pinexplore publishes a mart per external source. Everything under it -- the raw reads
-- of the dump files, the staging that parses and corrects them, the hand-curated
-- reference lists -- is that repo's own working material, free to be reshaped whenever
-- the pipeline is. Reaching past the mart into those layers couples a campaign to
-- internals nobody promised to keep still.
--
-- Now a GATE, not a report. It was a `_context` view while pinexplore had no mart and
-- every read below the line was unavoidable; the mart exists, this layer reads only it,
-- and so the `_checks` suffix makes the runner fail on a row instead of printing one.
-- That suffix is the whole difference between a warning and a gate.
--
-- It reads view definitions, so a relation named only in an ad-hoc `query` -- or in an
-- INSERT feeding the findings table -- is invisible. That understates, which is the safe
-- direction, and it is why every source file reads `px` in its RULE VIEWS only and lets
-- the INSERT project from those: keeping the reads in views is what keeps them checked.
CREATE OR REPLACE VIEW external_data_sources_boundary_checks AS
  WITH reads AS (
    SELECT
      v.view_name,
      t.relation
    FROM duckdb_views() AS v,
         unnest(regexp_extract_all(
           v.sql, 'px\.[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?')) AS t(relation)
    WHERE v.database_name = current_database()
      AND v.schema_name = 'main'
  )
  SELECT
    relation,
    -- An ALLOWLIST, not a denylist. Naming the internal layers meant the rule was only
    -- as complete as the list of ways to be internal -- `px.checks.violations` is not a
    -- mart and matched none of them. Naming the publishable schemas instead fails
    -- closed: a schema pinexplore adds is off-limits until someone decides otherwise,
    -- which is the right default for another repo's working material.
    --
    -- `fandom` is deliberately absent: pinexplore publishes no fandom mart, and the
    -- plan rules the comparison out even if one appears -- Fandom was never ingested
    -- and comparing would only surface ids nobody intends to acquire. `web_cache` is
    -- absent too; source TEXT is `evidence.sql`'s concern, per the header above.
    CASE
      WHEN NOT regexp_matches(relation, '^px\.[A-Za-z_][A-Za-z0-9_]*\.')
        THEN 'unqualified -- names no schema, so no layer'
      WHEN NOT regexp_matches(relation, '^px\.(ipdb|opdb|glossary|ingest)\.')
        THEN 'not a published mart'
    END AS layer,
    list_sort(list(DISTINCT view_name)) AS read_by
  FROM reads
  GROUP BY ALL
  HAVING layer IS NOT NULL
  ORDER BY layer, relation;
COMMENT ON VIEW external_data_sources_boundary_checks IS
  'Empty when healthy — one row per pinexplore internal this layer reaches past the mart to read. A row means a campaign has coupled itself to another repo''s working material.';

-- Empty when healthy.
--
-- An unreachable pinexplore never reaches here: the ATTACH above fails first, loudly,
-- with the path in the message. What it cannot catch is a pinexplore whose build died
-- partway, leaving the file readable and the tables empty or absent -- which reads
-- downstream as "the dump agrees with the catalog perfectly" rather than as a fault.
CREATE OR REPLACE VIEW external_data_sources_checks AS
  SELECT 'dump_empty' AS check_name, 'px.ipdb.models has no rows' AS detail
  WHERE (SELECT count(*) FROM px.ipdb.models) = 0
  UNION ALL
  SELECT 'dump_empty', 'px.opdb.models has no rows'
  WHERE (SELECT count(*) FROM px.opdb.models) = 0;
COMMENT ON VIEW external_data_sources_checks IS
  'Empty when healthy — invariants of the bridge itself, not findings about the data. A row means the attached dump is unusable.';

-- ═══ FINDINGS ══════════════════════════════════════════════════════════════
--
-- The single cross-source readout. Every per-source file projects its worklists down
-- into this one narrow shape, so "what does the external world disagree with us about"
-- is one query rather than one query per source per rule.
--
-- Modelled on flipcommons' `audit_findings` and deliberately NOT folded into it: an
-- audit finding is about a single record, while every finding here is about a PAIR --
-- an external listing and the catalog row it does or does not correspond to. Forcing
-- the pair into the audit's single-subject shape would cost that layer its own
-- self-checks, which is why this is a parallel structure rather than a contribution.
--
-- ASSEMBLED BY INSERT, NOT BY UNION. The audit unions because each of its rule views
-- already emits the five common columns itself; ours do not, and must not -- the wide
-- worklist IS the product a campaign works down, and `ipdb_models_unmatched` earns its
-- candidate slugs, counts and namesake lists. So a projection step exists here that the
-- audit does not need, and a positional `UNION ALL` is the worst place to put one: the
-- audit's own comment flags that a rule reordering its SELECT would swap `message` into
-- `severity` with no type error, and mitigates it with discipline alone. `INSERT ... BY
-- NAME` against a typed table removes that failure mode structurally -- names are
-- matched, not positions -- and keeps each rule's severity and wording next to the rule
-- instead of in a distant manifest.
--
-- Private, because the public spelling is the two views below: findings are only
-- meaningful after dismissals are applied.
CREATE TABLE IF NOT EXISTS _external_data_source_findings (
  source           VARCHAR,  -- 'ipdb', 'opdb' -- the external data source; or 'cross',
                             -- for a merge finding no single witness owns (fields.sql)
  rule             VARCHAR,  -- kebab-case, source-prefixed: 'ipdb-model-absent'
  severity         VARCHAR,  -- 'error' | 'warning'
  external_id      VARCHAR,  -- the source's own id; NULL where the finding is catalog-side
  entity_type      VARCHAR,  -- catalog entity type; NULL where no catalog record exists
  entity_public_id VARCHAR,  -- the catalog slug; NULL likewise
  message          VARCHAR,  -- deterministic one-liner; see the ordering rule below
  detail_view      VARCHAR   -- the wide worklist this was projected from
);
COMMENT ON TABLE _external_data_source_findings IS
  'Private accumulator — every source file INSERTs its projected findings here. Read external_data_source_findings instead, which applies dismissals.';

-- IF NOT EXISTS above, and a per-source DELETE in each source file, together make a
-- double `.read` harmless. It is not hypothetical: `ipdb.sql` and a future `opdb.sql`
-- both read this file, so a campaign reading both runs it twice. `CREATE OR REPLACE
-- TABLE` here would silently discard the first file's rows; `IF NOT EXISTS` without the
-- per-source DELETE would silently double them. Each source owns its own rows and
-- clears them before writing, so either order of reads converges on the same table.

-- ─── dismissals ────────────────────────────────────────────────────────────
--
-- A finding that is permanently, knowably wrong -- a quirk of the external source we
-- have already adjudicated and do not want to re-adjudicate every run.
--
-- AN INLINE VALUES LIST, NOT A FILE. It is how both repos already carry hand-curated
-- exception lists with their reasoning -- pinexplore's `ipdb_ref.retracted` (with
-- `reason` and `evidence_url`) and `ipdb_ref.specialty`, and the pattern flipcommons'
-- analysis README names under "Making manual judgment checkable". It keeps the
-- dismissal in the same file as the rule it dismisses, needs no parser, and has exactly
-- one escaping rule (double a single quote) rather than CSV's several. If this ever
-- outgrows a screenful the answer is a JSONL sidecar, because CSV fails SILENTLY on
-- prose containing commas and quotes -- which is precisely what `note` and `message`
-- are -- while `read_json` rejects malformed input outright.
--
-- IDENTITY INCLUDES THE MESSAGE, following the audit, whose `duplicate-name` rule states
-- it outright: identity is (rule, record, message). That is also why every aggregate
-- reaching a message below is ordered. A dismissal keyed without the message would stay
-- attached to a finding whose substance had changed underneath it -- a candidate count
-- moving 1 -> 3 is a different situation, and the old adjudication should lapse rather
-- than silently cover it.
--
-- THE BAR IS HIGH. The audit has no per-finding suppression anywhere in 900 lines; its
-- exemptions are whole categories excluded in the rule with a documented data-model
-- reason. A rule needing dismissals in bulk is a rule to fix, not to paper over.
--
-- Typed-empty rather than a VALUES list, because an empty VALUES list is a syntax error
-- and a dummy seed row would be a live trap. Add one by appending a UNION ALL line.
CREATE OR REPLACE VIEW _external_data_source_dismissals AS
  SELECT NULL::VARCHAR AS source,
         NULL::VARCHAR AS rule,
         NULL::VARCHAR AS external_id,
         NULL::VARCHAR AS entity_public_id,
         NULL::VARCHAR AS message,
         NULL::DATE    AS dismissed_on,
         NULL::VARCHAR AS note
  WHERE false
  -- Append dismissals here, newest last. Copy the finding's `message` VERBATIM from
  -- `external_data_source_findings`; a dismissal whose message has drifted matches
  -- nothing and is reported as stale by `external_data_source_findings_summary`.
  --
  -- UNION ALL SELECT 'ipdb', 'ipdb-model-absent', '7067', NULL,
  --   '<the exact message>', DATE '2026-08-22', 'Why this is permanently not a finding.'
  ;

-- Every finding with its dismissal state. The auditable spelling: what was dismissed,
-- when and why is visible here rather than vanishing from the record.
--
-- `IS NOT DISTINCT FROM` on the two nullable key columns, not `=`: `external_id` is NULL
-- on catalog-side findings and `entity_public_id` is NULL wherever no catalog record
-- exists, and `NULL = NULL` is unknown, so `=` would make exactly those findings
-- undismissable.
CREATE OR REPLACE VIEW external_data_source_findings_all AS
  SELECT f.*,
         d.dismissed_on,
         d.note AS dismissal_note,
         d.dismissed_on IS NOT NULL AS dismissed
  FROM _external_data_source_findings AS f
  LEFT JOIN _external_data_source_dismissals AS d
    ON  d.source = f.source
    AND d.rule   = f.rule
    AND d.external_id      IS NOT DISTINCT FROM f.external_id
    AND d.entity_public_id IS NOT DISTINCT FROM f.entity_public_id
    AND d.message = f.message;
COMMENT ON VIEW external_data_source_findings_all IS
  'Every external-source finding INCLUDING dismissed ones, each carrying its dismissal date and note. The auditable spelling; external_data_source_findings is the worklist.';

-- The dismissal record, browsable. `is_stale` marks an adjudication no longer matching
-- any finding -- someone fixed it, so the row can be pruned when convenient.
CREATE OR REPLACE VIEW external_data_source_dismissals AS
  SELECT d.*,
         NOT EXISTS (
           SELECT 1 FROM external_data_source_findings_all AS f
           WHERE f.source = d.source AND f.rule = d.rule
             AND f.external_id      IS NOT DISTINCT FROM d.external_id
             AND f.entity_public_id IS NOT DISTINCT FROM d.entity_public_id
             AND f.message = d.message) AS is_stale
  FROM _external_data_source_dismissals AS d;
COMMENT ON VIEW external_data_source_dismissals IS
  'Every dismissal with its date, note and is_stale flag. Stale means no finding matches any more — someone fixed it; prune when convenient.';

-- THE WORKLIST. Rows are the normal, healthy state -- this is what a campaign is built
-- to work down, which is why it is a view and never a `*_checks` view. The runner fails
-- nonzero on a row from any public `*_checks` view in the session, so a standing backlog
-- placed in one would break every campaign that reads this layer.
CREATE OR REPLACE VIEW external_data_source_findings AS
  SELECT * EXCLUDE (dismissed, dismissed_on, dismissal_note)
  FROM external_data_source_findings_all
  WHERE NOT dismissed
  ORDER BY CASE severity WHEN 'error' THEN 0 ELSE 1 END, source, rule, external_id;
COMMENT ON VIEW external_data_source_findings IS
  'Worklist — one row per live disagreement between an external data source and the catalog, errors first: source, rule, severity, the external id and catalog record it is about, a message, and the wide view to read next. Rows are expected.';

-- The headline readout, per rule.
--
-- Counted from the findings table rather than per rule VIEW, which is the one place this
-- layer departs from the audit's shape and does so knowingly. The audit counts per view
-- so a rule finding nothing keeps a row at zero -- a detector going dark otherwise looks
-- exactly like a clean catalog. Here a rule contributes no row when it finds nothing, so
-- that signal is carried instead by `<prefix>_summary` in each source file, which does
-- count per view. Reading both is how you tell "no findings" from "no detector".
--
-- The stale-dismissal rows ride along deliberately, and deliberately NOT in `*_checks`:
-- a dismissal goes stale when someone FIXES the finding, which is a success, and gating
-- the build on it would punish exactly the outcome the layer exists to produce.
CREATE OR REPLACE VIEW external_data_source_findings_summary AS
            SELECT source, rule, severity, count(*) AS n, false AS is_stale_dismissal
            FROM external_data_source_findings_all
            WHERE NOT dismissed
            GROUP BY ALL
  UNION ALL SELECT source, rule, 'dismissed', count(*), false
            FROM external_data_source_findings_all
            WHERE dismissed
            GROUP BY ALL
  UNION ALL SELECT source, rule, 'STALE DISMISSAL', count(*), true
            FROM external_data_source_dismissals
            WHERE is_stale
            GROUP BY ALL
  ORDER BY is_stale_dismissal DESC, severity, source, rule;
COMMENT ON VIEW external_data_source_findings_summary IS
  'One row per (source, rule, severity) with its count, plus dismissed tallies and any STALE DISMISSAL that no longer matches a finding. Stale is reported, never gated — it means someone fixed the finding.';

-- Empty when healthy. Invariants of the findings LAYER, never findings about the data.
CREATE OR REPLACE VIEW external_data_source_findings_checks AS
  -- format() propagates NULL, so one NULL argument blanks the WHOLE message and the
  -- finding renders as an empty line — broken-looking rather than wrong-looking. Needs
  -- its own branch because NULL slips every other test: `NULL NOT IN (…)` is unknown,
  -- not true. Straight from the audit's `finding_null_required`, for the same reason.
  SELECT 'finding_null_required' AS check_name,
         rule || ' -> ' || col   AS detail
  FROM _external_data_source_findings AS f,
       LATERAL (VALUES ('source', f.source), ('rule', f.rule),
                       ('severity', f.severity), ('message', f.message),
                       ('detail_view', f.detail_view)) AS v(col, val)
  WHERE v.val IS NULL

  UNION ALL
  -- Severity is computed per finding, so a CASE that loses its ELSE returns something
  -- nothing downstream knows how to rank or colour.
  SELECT 'unknown_severity', rule || ' -> ' || severity
  FROM _external_data_source_findings
  WHERE severity NOT IN ('error', 'warning')

  UNION ALL
  -- A finding names a catalog record by entity type, and the vocabulary is closed. A
  -- typo'd type makes the record unresolvable by every consumer without erroring.
  SELECT 'unknown_entity_type', rule || ' -> ' || entity_type
  FROM _external_data_source_findings
  WHERE entity_type IS NOT NULL
    AND entity_type NOT IN (SELECT entity_type FROM entity_registry)

  UNION ALL
  -- Identity is (source, rule, external_id, entity_public_id, message), which is what a
  -- dismissal keys on. A repeat means either two rules collided on one identity or a
  -- source file was inserted twice — and in the second case a single dismissal would
  -- silently only suppress one of the copies.
  SELECT 'duplicate_finding_identity',
         source || ' / ' || rule || ' / ' || coalesce(external_id, '-')
  FROM _external_data_source_findings
  GROUP BY source, rule, external_id, entity_public_id, message
  HAVING count(*) > 1

  UNION ALL
  -- `detail_view` is the reader's route from the narrow finding to the wide worklist it
  -- came from. A renamed or deleted view leaves the finding pointing at nothing, which
  -- no other check would notice.
  SELECT 'detail_view_missing', missing_view
  FROM (
    SELECT DISTINCT f.detail_view AS missing_view
    FROM _external_data_source_findings AS f
    WHERE f.detail_view IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM duckdb_views() AS v
        WHERE v.database_name = current_database()
          AND v.schema_name = 'main'
          AND v.view_name = f.detail_view)
  )

  UNION ALL
  -- A dismissal is an adjudication of one specific finding, so its rule must be one a
  -- source file actually emits. Catches a rule renamed out from under a dismissal, which
  -- would otherwise read as "nothing to dismiss" — silently reviving a settled finding.
  SELECT 'dismissal_unknown_rule', d.source || ' -> ' || d.rule
  FROM _external_data_source_dismissals AS d
  WHERE NOT EXISTS (SELECT 1 FROM _external_data_source_findings AS f
                    WHERE f.source = d.source AND f.rule = d.rule);
COMMENT ON VIEW external_data_source_findings_checks IS
  'Empty when healthy — invariants of the findings layer: no NULL in a required column, closed severity and entity-type vocabularies, one row per identity, every detail_view resolvable, every dismissal naming a live rule.';
