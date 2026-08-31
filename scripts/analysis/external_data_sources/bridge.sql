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
-- RESOLUTION RUNS COARSE TO FINE, AND THE WORKLIST IS THE ORDER. Identity is
-- resolved in stages -- manufacturers first (OPDB manufacturers, IPDB corporate
-- entities), then titles (OPDB groups), then models -- because each stage's ID links
-- are evidence the next stage matches on: a model candidate needs its maker resolved,
-- a group verdict reads its machines' links. ID matching at every stage precedes all
-- other work (field values, vocabulary, credits), which is the trailing `content`
-- stage. Not a strict DAG -- title verdicts read already-linked models, which works
-- because most models are ID-linked -- but the working order stands: author and apply
-- the manufacturer patch, re-run, then titles, re-run, then models. This is
-- STRUCTURAL, not advice: every finding carries `resolution_stage`, the worklist
-- orders stage-first, and working it top to bottom IS the process.
--
-- THE MAKER STAGE IS ONE STAGE WITH INTERNAL STRUCTURE, deliberately not split into
-- corporate-entity and manufacturer stages, because the dependency between the two
-- grains runs both ways. IDENTIFICATION runs at corporate-entity grain: IPDB speaks
-- only corporate entities, the manufacturer layer is the catalog's own grouping over
-- them, and an unresolved corporate entity degrades every IPDB model match -- the
-- maker leg of triangulation routes through `corporate_entities.manufacturer_slug`.
-- Record CREATION runs manufacturer-first inside the patch, because
-- `corporate_entities.manufacturer_id` is required. Those opposite arrows are why a
-- new maker is ONE adjudication and one patch -- identify the entity, decide its
-- grouping, create the manufacturer then the corporate entity referencing it -- and
-- splitting the stage would cut that unit of work in half across a boundary.
--
-- FINDINGS ARE NEVER SILENTLY ADJUDICATED. A classification may be excluded from a
-- findings INSERT only when the same situation is reported by another rule -- a
-- structural fact the exclusion comment must name -- never because a session judged
-- the class permanently fine. "The catalog is right about these" is a data-quality
-- adjudication; it belongs to Moses, and its instrument is the per-finding dismissal
-- below, dated and noted. A session that believes a whole class needs no findings
-- surfaces that belief as a proposal, not as a WHERE clause.
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
--
-- A MATERIALIZED relation keeps a `_source` VIEW as its definition witness, for the same
-- reason: DuckDB stores no defining SQL for a table, so a dump converted to a table
-- outright would drop out of this scan and retire the guard on the very relations that
-- read pinexplore. The witness is never read at runtime -- it exists to be scanned here
-- -- and `external_data_sources_checks` fails if one goes missing.
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
  WHERE (SELECT count(*) FROM px.opdb.models) = 0
  UNION ALL
  -- THE DEFINITION WITNESSES. Each materialized dump is `CREATE TABLE AS SELECT * FROM
  -- <name>_source`, and that `_source` view is the only thing keeping its pinexplore
  -- reads inside `external_data_sources_boundary_checks`, which can scan views alone.
  -- Fold a witness back into its table and the boundary guard goes quiet rather than
  -- loud -- so its absence is a hard failure here.
  SELECT 'materialized_dump_lost_its_definition_witness', t.name
  FROM (VALUES ('_eds_ipdb_dump'), ('_eds_opdb_dump')) AS t(name)
  WHERE NOT EXISTS (SELECT 1 FROM duckdb_views() AS v
                    WHERE v.database_name = current_database()
                      AND v.schema_name = 'main'
                      AND v.view_name = t.name || '_source');
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
  resolution_stage VARCHAR,  -- 'manufacturers' | 'titles' | 'models' | 'content' --
                             -- where the finding sits in the coarse-to-fine
                             -- resolution order (see the header); the worklist sorts
                             -- on it first
  severity         VARCHAR,  -- 'error' | 'warning'
  external_id      VARCHAR,  -- the source's own id; NULL where the finding is catalog-side
  entity_type      VARCHAR,  -- catalog entity type; NULL where no catalog record exists
  entity_public_id VARCHAR,  -- the catalog slug; NULL likewise
  discriminator    VARCHAR,  -- the fact's own key within the record -- which credit,
                             -- which field, which candidate set -- completing identity
                             -- where the record-level keys repeat, and lapsing a
                             -- dismissal when the substance changes; NULL where the
                             -- record-level keys already say everything
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

-- ─── the rule registry ─────────────────────────────────────────────────────
--
-- One row per (worklist, classification): THE home of the rule vocabulary. Everything
-- a rule states about itself -- its stage, severity and detail view, or the reason its
-- class deliberately produces no finding -- lives here and nowhere else. The findings
-- INSERTs join this on the class they project and inherit those columns, so a new
-- class is a registry row plus a message branch, not four sites edited in lockstep;
-- `classification` is NULL for a worklist that is a single rule whole.
--
-- EXCLUSIONS ARE ROWS, NEVER WHERE CLAUSES. The header's rule -- findings are never
-- silently adjudicated -- becomes structural here: a class that produces no finding
-- carries `excluded_because`, plus `covered_by_rule` when the same situation is
-- reported under another name (verified live by `registry_covered_by_unregistered`),
-- and the per-file classification checks fail on any emitted class the registry has
-- never heard of. A WHERE clause can no longer quietly retire a class -- which also
-- closes a live near-miss: the old opdb INSERT's CASE had no `maker_contested`
-- branch, so a row of that class would have inserted a NULL rule and message and
-- relied on `finding_null_required` to notice; under the registry join the class
-- simply routes to its own rule.
CREATE OR REPLACE VIEW _eds_rule_registry AS
  SELECT * FROM (VALUES
    -- source | detail_view | classification | rule | resolution_stage | severity | covered_by_rule | excluded_because
    -- ── ipdb: the unmatched worklist ──
    ('ipdb', 'ipdb_models_unmatched', 'catalog_holds_unlinked', 'ipdb-model-unlinked',            'models', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_models_unmatched', 'possible_duplicate',     'ipdb-model-possible-duplicate',  'models', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_models_unmatched', 'multiple_candidates',    'ipdb-model-multiple-candidates', 'models', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_models_unmatched', 'year_unverified',        'ipdb-model-year-unverified',     'models', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_models_unmatched', 'year_conflict',          'ipdb-model-year-conflict',       'models', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_models_unmatched', 'maker_unresolved',       'ipdb-model-maker-unresolved',    'models', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_models_unmatched', 'absent',                 'ipdb-model-absent',              'models', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_models_unmatched', 'duplicate_listing',      NULL, NULL, NULL, NULL,
     'a confirmed IPDB-side double entry whose twin the catalog links; the confirmation lives on the mart row, and there is nothing to do'),
    -- ── ipdb: dead ids (classes derived in the INSERT from retraction_reason) ──
    ('ipdb', 'ipdb_ids_not_in_dump', 'retracted',   'ipdb-id-retracted',   'models', 'error',   NULL, NULL),
    ('ipdb', 'ipdb_ids_not_in_dump', 'unexplained', 'ipdb-id-not-in-dump', 'models', 'warning', NULL, NULL),
    -- ── ipdb: makers ──
    ('ipdb', 'ipdb_model_corporate_entity_mismatched', 'disagrees',             'ipdb-corporate-entity-disagrees',  'manufacturers', 'error',   NULL, NULL),
    ('ipdb', 'ipdb_model_corporate_entity_mismatched', 'catalog_has_none',      'ipdb-corporate-entity-missing',    'manufacturers', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_model_corporate_entity_mismatched', 'ipdb_entity_unmatched', 'ipdb-corporate-entity-unresolved', 'manufacturers', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_corporate_entities_unmatched', NULL, 'ipdb-corporate-entity-unknown',        'manufacturers', 'warning', NULL, NULL),
    ('ipdb', 'corporate_entities_missing_ipdb_id', NULL, 'ipdb-corporate-entity-id-acquirable', 'manufacturers', 'warning', NULL, NULL),
    -- ── ipdb: credits (classes derived in the INSERT from n_person_matches) ──
    ('ipdb', 'ipdb_credits_missing', 'person_resolved',  'ipdb-credit-missing',          'content', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_credits_missing', 'person_ambiguous', 'ipdb-credit-person-ambiguous', 'content', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_credits_missing', 'person_unmatched', NULL, NULL, NULL, 'ipdb-person-unmatched',
     'the person does not exist yet, and creating them comes first; reported once at person grain rather than once per credit'),
    ('ipdb', 'ipdb_people_unmatched',           NULL, 'ipdb-person-unmatched',            'content', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_model_specialties_missing',  'vocabulary',   'ipdb-specialty-missing',        'content', 'warning', NULL, NULL),
    -- The three relationship specialties are reported at model+edge grain instead. Every
    -- other specialty row hands an author `target_slug` -- the record the patch asserts;
    -- a relationship row cannot, because its target names an edge TYPE and an edge needs
    -- a COUNTERPART the specialty census never states. So the same fact under this rule
    -- would be a worklist row nobody can act on; the detail view it points at splits the
    -- work by what the catalog already holds instead.
    ('ipdb', 'ipdb_model_specialties_missing',  'relationship', NULL, NULL, NULL, 'ipdb-relationship-missing',
     'the target is a relationship type, not a record: reported at model+edge grain by ipdb_model_relationships_missing, which splits the work by the edges the catalog already holds'),
    ('ipdb', 'ipdb_specialty_vocabulary_absent', NULL, 'ipdb-specialty-vocabulary-absent', 'content', 'warning', NULL, NULL),
    -- ── ipdb: relationship edges (classes derived in the INSERT from the edges the
    -- catalog already holds). All three are warnings: a source asserting an edge we do
    -- not hold is not the catalog being demonstrably wrong, which is the bar for `error`.
    --
    -- THE LATTER TWO ARE NAMED FOR WHAT THE CATALOG HOLDS, not for a verdict on it.
    -- IPDB's Specialty names no counterpart, so nothing can test whether an edge already
    -- on the model is this same relationship mistyped or a second relationship to another
    -- machine — and `DomainModel.md` allows both. A rule called `-type-disagrees` would
    -- assert the first and send an author to change a sound edge; see the class prose in
    -- `ipdb.sql` for the live case (`jaws`) that settles it.
    ('ipdb', 'ipdb_model_relationships_missing', 'no_edge',            'ipdb-relationship-missing',      'content', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_model_relationships_missing', 'other_type_edge',    'ipdb-relationship-other-edges',  'content', 'warning', NULL, NULL),
    ('ipdb', 'ipdb_model_relationships_missing', 'edge_points_inward', 'ipdb-relationship-inbound-only', 'content', 'warning', NULL, NULL),
    -- ── opdb: the unmatched worklist ──
    ('opdb', 'opdb_models_unmatched', 'catalog_holds_unlinked', 'opdb-model-unlinked',            'models', 'warning', NULL, NULL),
    ('opdb', 'opdb_models_unmatched', 'possible_duplicate',     'opdb-model-possible-duplicate',  'models', 'warning', NULL, NULL),
    ('opdb', 'opdb_models_unmatched', 'maker_contested',        'opdb-model-maker-contested',     'models', 'warning', NULL, NULL),
    ('opdb', 'opdb_models_unmatched', 'multiple_candidates',    'opdb-model-multiple-candidates', 'models', 'warning', NULL, NULL),
    ('opdb', 'opdb_models_unmatched', 'year_unverified',        'opdb-model-year-unverified',     'models', 'warning', NULL, NULL),
    ('opdb', 'opdb_models_unmatched', 'year_conflict',          'opdb-model-year-conflict',       'models', 'warning', NULL, NULL),
    ('opdb', 'opdb_models_unmatched', 'maker_unresolved',       'opdb-model-maker-unresolved',    'models', 'warning', NULL, NULL),
    ('opdb', 'opdb_models_unmatched', 'absent',                 'opdb-model-absent',              'models', 'warning', NULL, NULL),
    ('opdb', 'opdb_models_unmatched', 'moved_successor',        NULL, NULL, NULL, 'opdb-id-moved',
     'the repoint is reported on the model citing the stale id; a second finding on the successor would restate it'),
    -- ── opdb: titles ──
    ('opdb', 'opdb_titles_unmatched', 'catalog_holds_unlinked', 'opdb-title-unlinked',            'titles', 'warning', NULL, NULL),
    ('opdb', 'opdb_titles_unmatched', 'possible_duplicate',     'opdb-title-possible-duplicate',  'titles', 'warning', NULL, NULL),
    ('opdb', 'opdb_titles_unmatched', 'multiple_candidates',    'opdb-title-multiple-candidates', 'titles', 'warning', NULL, NULL),
    ('opdb', 'opdb_titles_unmatched', 'year_unverified',        'opdb-title-year-unverified',     'titles', 'warning', NULL, NULL),
    ('opdb', 'opdb_titles_unmatched', 'year_conflict',          'opdb-title-year-conflict',       'titles', 'warning', NULL, NULL),
    ('opdb', 'opdb_titles_unmatched', 'absent',                 'opdb-title-absent',              'titles', 'warning', NULL, NULL),
    ('opdb', 'opdb_titles_unmatched', 'split_across_titles',    NULL, NULL, NULL, 'opdb-title-split-across-titles',
     'reported at split grain, which also reaches the matched groups this worklist cannot see'),
    ('opdb', 'opdb_title_splits',    NULL, 'opdb-title-split-across-titles', 'titles', 'warning', NULL, NULL),
    ('opdb', 'opdb_title_ids_stale', NULL, 'opdb-title-id-not-in-dump',      'titles', 'warning', NULL, NULL),
    -- ── opdb: stale ids ──
    ('opdb', 'opdb_ids_stale', 'moved',       'opdb-id-moved',       'models', 'error',   NULL, NULL),
    ('opdb', 'opdb_ids_stale', 'deleted',     'opdb-id-deleted',     'models', 'error',   NULL, NULL),
    ('opdb', 'opdb_ids_stale', 'container',   'opdb-id-container',   'models', 'error',   NULL, NULL),
    ('opdb', 'opdb_ids_stale', 'unexplained', 'opdb-id-not-in-dump', 'models', 'warning', NULL, NULL),
    -- ── opdb: makers ──
    ('opdb', 'opdb_model_manufacturer_mismatched', 'catalog_has_none', 'opdb-manufacturer-missing', 'manufacturers', 'warning', NULL, NULL),
    ('opdb', 'opdb_model_manufacturer_mismatched', 'excepted',       NULL, NULL, NULL, NULL,
     'an adjudicated pairing; the reason rides the worklist row'),
    ('opdb', 'opdb_model_manufacturer_mismatched', 'opdb_unmatched', NULL, NULL, NULL, 'opdb-manufacturer-unknown',
     'resolving the manufacturer resolves every model filed under it; reported once at decision grain'),
    ('opdb', 'opdb_model_manufacturer_mismatched', 'disagrees',      NULL, NULL, NULL, 'opdb-manufacturer-disagrees',
     'reported once at pair grain; the model-grain rows stay as the patch material'),
    ('opdb', 'opdb_manufacturer_pairs_disagreeing', NULL, 'opdb-manufacturer-disagrees',      'manufacturers', 'warning', NULL, NULL),
    ('opdb', 'opdb_manufacturers_unmatched',        NULL, 'opdb-manufacturer-unknown',        'manufacturers', 'warning', NULL, NULL),
    ('opdb', 'manufacturers_missing_opdb_id',       NULL, 'opdb-manufacturer-id-acquirable',  'manufacturers', 'warning', NULL, NULL),
    -- ── opdb: the IPDB cross-reference ──
    ('opdb', 'opdb_ipdb_id_crosscheck', 'disagrees',  'opdb-ipdb-id-disagrees',  'models', 'error',   NULL, NULL),
    ('opdb', 'opdb_ipdb_id_crosscheck', 'acquirable', 'opdb-ipdb-id-acquirable', 'models', 'warning', NULL, NULL),
    -- ── opdb: vocabulary ──
    ('opdb', 'opdb_model_vocabulary_missing', NULL, 'opdb-vocabulary-missing', 'content', 'warning', NULL, NULL),
    ('opdb', 'opdb_vocabulary_absent',        NULL, 'opdb-vocabulary-absent',  'content', 'warning', NULL, NULL),
    -- ── cross: the field merge (classes are the merge's `shape`; the excluded shapes
    --    never reach the unsupported worklist, and registering them is what lets
    --    fields_checks prove the shape vocabulary complete instead of trusting the CASE) ──
    ('cross', 'model_fields_unsupported', 'backfill',     'cross-field-unsupported', 'content', 'warning', NULL, NULL),
    ('cross', 'model_fields_unsupported', 'outvoted',     'cross-field-unsupported', 'content', 'warning', NULL, NULL),
    ('cross', 'model_fields_unsupported', 'lone_witness', 'cross-field-unsupported', 'content', 'warning', NULL, NULL),
    ('cross', 'model_fields_unsupported', 'scatter',      'cross-field-unsupported', 'content', 'warning', NULL, NULL),
    ('cross', 'model_fields_unsupported', 'contested',    NULL, NULL, NULL, NULL,
     'a standoff a witness already backs the catalog on; browsable in model_fields_contested, never work'),
    ('cross', 'model_fields_unsupported', 'supported',    NULL, NULL, NULL, NULL,
     'the catalog agrees with a witness; nothing to report')
  ) AS t(source, detail_view, classification, rule, resolution_stage, severity,
         covered_by_rule, excluded_because);

-- ─── adjudications ─────────────────────────────────────────────────────────
--
-- THE ONE PLACE A HUMAN JUDGMENT ABOUT A FINDING IS RECORDED. Three scopes, one
-- relation; what separates them is not their shape but their EFFECT:
--
--   finding           dismisses ONE finding -- a quirk of the external source already
--                     adjudicated, not to be re-adjudicated every run. Keys on the
--                     finding's identity; touches nothing else.
--   maker-pair        adjudicates an (OPDB maker, catalog manufacturer) FILING POLICY
--                     -- OPDB filing games under a parent or successor company. It
--                     reaches into computation, not just reporting: it clears the
--                     `excepted` class on every model filed that way and feeds the
--                     ladder's contested-maker guard (identity.sql), which a
--                     finding-scope dismissal would leave armed.
--   vocabulary-value  settles an absent vocabulary value as permanently not ours to
--                     mint: the value leaves `opdb_vocabulary_absent` itself, with
--                     the reason kept browsable.
--
-- Pick the NARROWEST scope that carries the decision: one finding gets 'finding'; a
-- judgment about the pairing or the value gets its scope, because the wider scopes
-- survive changes (another model filed that way, another machine gaining the value)
-- that would rightly lapse a finding-scope dismissal.
--
-- AN INLINE VALUES LIST, NOT A FILE. It is how both repos already carry hand-curated
-- exception lists with their reasoning -- pinexplore's `ipdb_ref.retracted` (with
-- `reason` and `evidence_url`) and `ipdb_ref.specialty`, and the pattern flipcommons'
-- analysis README names under "Making manual judgment checkable". It keeps the
-- adjudication beside the machinery it feeds, needs no parser, and has exactly one
-- escaping rule (double a single quote) rather than CSV's several. If this ever
-- outgrows a couple of screenfuls the answer is a JSONL sidecar, because CSV fails
-- SILENTLY on prose containing commas and quotes -- which is precisely what `note`
-- is -- while `read_json` rejects malformed input outright.
--
-- THE BAR IS HIGH. The audit has no per-finding suppression anywhere in 900 lines; its
-- exemptions are whole categories excluded in the rule with a documented data-model
-- reason. A rule needing dismissals in bulk is a rule to fix, not to paper over.
--
-- EVERY ROW CARRIES ITS REASON in `note` (checked), and new rows carry
-- `adjudicated_on`; the maker-pair rows inherited from pinexplore's deleted
-- `opdb_ref.manufacturer_exceptions` predate the dating discipline and are honestly
-- undated (the research behind each is recoverable there via
-- `git log -S opdb_ref.manufacturer_exceptions -p`). Staleness is computed per scope
-- and REPORTED, never gated -- a stale row means someone fixed the situation, which
-- is a success; browse `external_data_source_adjudications` (opdb.sql) and prune when
-- convenient.
--
-- Each scope's block writes only its own key columns; the projection stamps the rest
-- NULL, and `adjudication_scope_keys_mismatched` holds every row to its scope's shape.
CREATE OR REPLACE VIEW _eds_adjudications AS
  -- ── scope 'finding' ──
  --
  -- IDENTITY IS (source, rule, external_id, entity_public_id, discriminator): the
  -- record-level keys plus the fact's own key within the record. The discriminator
  -- does the job the rendered message once did without making a sentence load-bearing:
  -- a dismissal keyed on record alone would stay attached to a finding whose substance
  -- had changed underneath it -- a candidate set growing from one model to three is a
  -- different situation, and the old adjudication should lapse rather than silently
  -- cover it -- so each rule's INSERT chooses the discriminator carrying exactly that
  -- substance, and a dismissal copies it VERBATIM (often NULL) from
  -- `external_data_source_findings`. One whose discriminator has drifted matches
  -- nothing and is reported as stale.
  --
  -- Typed-empty rather than a VALUES list, because an empty VALUES list is a syntax
  -- error and a dummy seed row would be a live trap. Add one by appending a UNION ALL:
  --
  -- UNION ALL SELECT 'finding', 'ipdb', 'ipdb-model-absent', '7067', NULL, NULL,
  --   NULL::INT, NULL, NULL, NULL, DATE '2026-08-22', 'Why this is permanently not a finding.'
  SELECT 'finding'      AS scope,
         NULL::VARCHAR  AS source,
         NULL::VARCHAR  AS rule,
         NULL::VARCHAR  AS external_id,
         NULL::VARCHAR  AS entity_public_id,
         NULL::VARCHAR  AS discriminator,
         NULL::INT      AS opdb_manufacturer_id,
         NULL::VARCHAR  AS manufacturer_slug,
         NULL::VARCHAR  AS target_entity_type,
         NULL::VARCHAR  AS target_value,
         NULL::DATE     AS adjudicated_on,
         NULL::VARCHAR  AS note
  WHERE false

  UNION ALL
  -- OPDB files HEXA Pinball's Louis Vuitton as an ALIAS of machine GV8j1-M0oZe
  -- ('-A1r2W'), i.e. the same machine rethemed, and so groups it with Space Hunt.
  -- Flipcommons holds the two as separate titles. Adjudicated in favour of the
  -- catalog: the split stands, and both models already carry their correct OPDB ids,
  -- so nothing about the link is in question -- only the grouping, which is a
  -- difference of editorial policy rather than a defect on either side.
  SELECT 'finding', 'opdb', 'opdb-title-split-across-titles', 'GV8j1', 'space-hunt',
         'louis-vuitton, space-hunt', NULL::INT, NULL, NULL, NULL,
         DATE '2026-08-29',
         'OPDB groups the Louis Vuitton retheme with Space Hunt as one machine; Flipcommons holds them as separate titles'

  UNION ALL
  -- Road Trip is unreleased. OPDB dates it February 2025 — its world debut at Pinball
  -- at the Beach — while Ramps' own statement is "Expected Late 2026", so the two sides
  -- are dating different events rather than disagreeing about one. Both month claims
  -- were deliberately retracted (0233-ramps-pinball called the resolved February 2026 "a
  -- chimera"; 0235-road-trip-month-opdb-retract dropped OPDB's), and the year carries
  -- the same debut date. The comparison reads the dump against the catalog and cannot
  -- see those retractions, so without these two rows the settled question returns on
  -- every run. The discriminator carries OPDB's value, so a changed dump lapses them.
  SELECT 'finding', 'cross', 'cross-field-unsupported', NULL, 'road-trip',
         'production_year: - / 2025', NULL::INT, NULL, NULL, NULL,
         DATE '2026-08-29',
         'OPDB dates this machine to its February 2025 world debut rather than to manufacture; the machine is unreleased'

  UNION ALL
  SELECT 'finding', 'cross', 'cross-field-unsupported', NULL, 'road-trip',
         'production_month: - / 2', NULL::INT, NULL, NULL, NULL,
         DATE '2026-08-29',
         'OPDB month is the February 2025 world debut, not a manufacture month; no month is assertable while the machine is unreleased'

  UNION ALL
  -- ── scope 'maker-pair' ──
  --
  -- Keyed on the PAIR -- this OPDB maker id against this catalog manufacturer -- so
  -- one row clears every model filed that way at once. One slug was updated at
  -- inheritance: the row written as `mecatronics-aka-taito-brazil-a-division-of-taito`
  -- had already rotted against the catalog's rename to `mecatronics`, exactly the
  -- failure `exception_slug_unresolved` (identity_checks) now makes loud.
  SELECT 'maker-pair', 'opdb', NULL, NULL, NULL, NULL,
         t.opdb_manufacturer_id, t.manufacturer_slug, NULL, NULL, NULL, t.reason
  FROM (VALUES
    (15, 'sonic',                'OPDB uses parent name Segasa for Sonic-branded games'),
    -- Geiger-Automatenbau GmbH = A.H. Geiger Co. = the Komplett Flipper brand.
    (50, 'komplett-flipper',     'OPDB uses Geiger for Komplett Flipper brand'),
    (50, 'professional-pinball', 'OPDB misattributes to Geiger; IPDB says Professional Pinball'),
    (95, 'the-pinball-company',  'Collaboration: designed by TPC, manufactured by Spooky'),
    (40, 'briarwood',            'OPDB uses parent Brunswick for Briarwood division games'),
    (14, 'bally',                'OPDB uses Midway for Bally-branded game'),
    (2,  'alben',                'OPDB uses Gottlieb for Alben-manufactured game'),
    (20, 'bell-coin-matics',     'OPDB uses Bell Games for Bell Coin Matics game'),
    (3,  'chicago-gaming',       'OPDB uses Chicago Coin for Chicago Gaming game'),
    (4,  'sentinel',             'OPDB uses Cic Play for Sentinel game'),
    -- LAI = Leisure & Allied Industries, Australian.
    (49, 'lai',                  'OPDB uses Allied Leisure for LAI game'),
    (90, 'jocmatic-sa',          'OPDB uses Joctronic for Jocmatic game'),
    (73, 'mecatronics',          'OPDB uses Taito for Brazilian division')
  ) AS t(opdb_manufacturer_id, manufacturer_slug, reason)

  UNION ALL
  -- ── scope 'vocabulary-value' ──
  --
  -- A decision about the VALUE, wherever it appears. The edition tags are deliberately
  -- NOT here -- OpdbMappings.md calls them signals to CONSIDER, an open decision that
  -- belongs on the worklist.
  SELECT 'vocabulary-value', 'opdb', NULL, NULL, NULL, NULL, NULL, NULL,
         t.target_entity_type, t.target_value, NULL, t.reason
  FROM (VALUES
    ('tag', 'licensed',
     'OpdbMappings.md rules out minting a tag: the signal feeds licensed-relationship research, not tag vocabulary.')
  ) AS t(target_entity_type, target_value, reason);

-- The finding scope under its historical name, for every consumer below: the columns
-- a dismissal keys on, plus its date and note.
CREATE OR REPLACE VIEW _external_data_source_dismissals AS
  SELECT source, rule, external_id, entity_public_id, discriminator,
         adjudicated_on AS dismissed_on, note
  FROM _eds_adjudications
  WHERE scope = 'finding';

-- Every finding with its dismissal state. The auditable spelling: what was dismissed,
-- when and why is visible here rather than vanishing from the record.
--
-- `IS NOT DISTINCT FROM` on the three nullable key columns, not `=`: `external_id` is
-- NULL on catalog-side findings, `entity_public_id` is NULL wherever no catalog record
-- exists, `discriminator` is NULL wherever the record-level keys suffice, and
-- `NULL = NULL` is unknown, so `=` would make exactly those findings undismissable.
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
    AND d.discriminator    IS NOT DISTINCT FROM f.discriminator;
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
             AND f.discriminator    IS NOT DISTINCT FROM d.discriminator) AS is_stale
  FROM _external_data_source_dismissals AS d;
COMMENT ON VIEW external_data_source_dismissals IS
  'Every dismissal with its date, note and is_stale flag. Stale means no finding matches any more — someone fixed it; prune when convenient.';

-- THE WORKLIST. Rows are the normal, healthy state -- this is what a campaign is built
-- to work down, which is why it is a view and never a `*_checks` view. The runner fails
-- nonzero on a row from any public `*_checks` view in the session, so a standing backlog
-- placed in one would break every campaign that reads this layer.
-- ORDERED BY RESOLUTION STAGE FIRST, severity second: a manufacturer warning
-- precedes a model error, because fixing the maker's id changes what every later
-- stage matches. Working the list top to bottom is the resolution process; filter on
-- `resolution_stage` to hold the current stage until it is empty.
--
-- THE SOURCE SORT IS LOAD-BEARING, not cosmetic: the identity doc rules "match IPDB
-- before OPDB" -- IPDB's names match the catalog's, and every IPDB link extends the
-- ipdb_id route's reach on the OPDB side -- and `'ipdb' < 'opdb'` happens to satisfy
-- it alphabetically. A source added later, or an innocent reorder, must keep the
-- doc's order deliberate here.
CREATE OR REPLACE VIEW external_data_source_findings AS
  SELECT * EXCLUDE (dismissed, dismissed_on, dismissal_note)
  FROM external_data_source_findings_all
  WHERE NOT dismissed
  ORDER BY CASE resolution_stage WHEN 'manufacturers' THEN 0 WHEN 'titles' THEN 1
                                 WHEN 'models' THEN 2 ELSE 3 END,
           CASE severity WHEN 'error' THEN 0 ELSE 1 END, source, rule, external_id;
COMMENT ON VIEW external_data_source_findings IS
  'Worklist — one row per live disagreement between an external data source and the catalog, ordered by resolution_stage (manufacturers, then titles, then models, then content) and errors-first within a stage: work it top to bottom, holding each stage until it is empty. Rows are expected.';

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
  SELECT * FROM (
              SELECT resolution_stage, source, rule, severity, count(*) AS n,
                     false AS is_stale_dismissal
              FROM external_data_source_findings_all
              WHERE NOT dismissed
              GROUP BY ALL
    UNION ALL SELECT resolution_stage, source, rule, 'dismissed', count(*), false
              FROM external_data_source_findings_all
              WHERE dismissed
              GROUP BY ALL
    UNION ALL SELECT NULL, source, rule, 'STALE DISMISSAL', count(*), true
              FROM external_data_source_dismissals
              WHERE is_stale
              GROUP BY ALL
  )
  ORDER BY is_stale_dismissal DESC,
           CASE resolution_stage WHEN 'manufacturers' THEN 0 WHEN 'titles' THEN 1
                                 WHEN 'models' THEN 2 ELSE 3 END,
           severity, source, rule;
COMMENT ON VIEW external_data_source_findings_summary IS
  'One row per (stage, source, rule, severity) with its count, in resolution-stage order, plus dismissed tallies and any STALE DISMISSAL that no longer matches a finding. Stale is reported, never gated — it means someone fixed the finding.';

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
                       ('resolution_stage', f.resolution_stage),
                       ('severity', f.severity), ('message', f.message),
                       ('detail_view', f.detail_view)) AS v(col, val)
  WHERE v.val IS NULL

  UNION ALL
  -- Findings inherit rule, stage, severity and detail_view by joining the registry,
  -- so AGREEMENT WITH THE REGISTRY is the one invariant -- it subsumes the old
  -- findings-grain closed-set checks (the vocabularies are closed at the registry, in
  -- the registry_* checks below) and the unregistered-rule check (a rule the registry
  -- lacks matches no row here either). A row means an INSERT hand-wrote a literal
  -- beside the registry, which is exactly the fork this makes loud.
  SELECT 'finding_registry_mismatch',
         f.source || ' / ' || f.rule || ' -> ' || f.resolution_stage || ' / '
           || f.severity || ' / ' || f.detail_view
  FROM (SELECT DISTINCT source, rule, resolution_stage, severity, detail_view
        FROM _external_data_source_findings) AS f
  WHERE NOT EXISTS (
    SELECT 1 FROM _eds_rule_registry AS r
    WHERE r.source = f.source AND r.rule = f.rule
      AND r.resolution_stage = f.resolution_stage
      AND r.severity = f.severity
      AND r.detail_view = f.detail_view)

  UNION ALL
  -- A finding names a catalog record by entity type, and the vocabulary is closed. A
  -- typo'd type makes the record unresolvable by every consumer without erroring.
  SELECT 'unknown_entity_type', rule || ' -> ' || entity_type
  FROM _external_data_source_findings
  WHERE entity_type IS NOT NULL
    AND entity_type NOT IN (SELECT entity_type FROM entity_registry)

  UNION ALL
  -- Identity is (source, rule, external_id, entity_public_id, discriminator), which is
  -- what a dismissal keys on. A repeat means either two rules collided on one identity,
  -- a source file was inserted twice, or a rule that emits several facts per record
  -- forgot to discriminate them — and in every case a single dismissal would silently
  -- suppress only one of the copies.
  SELECT 'duplicate_finding_identity',
         source || ' / ' || rule || ' / ' || coalesce(external_id, '-')
           || ' / ' || coalesce(discriminator, '-')
  FROM _external_data_source_findings
  GROUP BY source, rule, external_id, entity_public_id, discriminator
  HAVING count(*) > 1

  UNION ALL
  -- `detail_view` is the reader's route from the narrow finding to the wide worklist it
  -- came from. Checked at REGISTRY grain, so a rule whose worklist is currently empty
  -- still validates: a renamed or deleted view would leave its findings pointing at
  -- nothing, and nothing else would notice.
  SELECT 'detail_view_missing', missing_view
  FROM (
    SELECT DISTINCT r.detail_view AS missing_view
    FROM _eds_rule_registry AS r
    WHERE NOT EXISTS (
        SELECT 1 FROM duckdb_views() AS v
        WHERE v.database_name = current_database()
          AND v.schema_name = 'main'
          AND v.view_name = r.detail_view)
  )

  UNION ALL
  -- A dismissal is an adjudication of one specific finding, so its rule must be one the
  -- registry knows. Catches a rule renamed out from under a dismissal, which would
  -- otherwise read as "nothing to dismiss" — silently reviving a settled finding.
  -- Against the REGISTRY, not the findings table: a rule whose last finding was fixed
  -- still validates its dismissal, which then simply reads as stale.
  SELECT 'dismissal_unknown_rule', d.source || ' -> ' || d.rule
  FROM _external_data_source_dismissals AS d
  WHERE NOT EXISTS (SELECT 1 FROM _eds_rule_registry AS r
                    WHERE r.source = d.source AND r.rule = d.rule)

  UNION ALL
  -- ─── invariants of the registry itself ───
  -- The join key: two rows answering one (worklist, class) would double every finding
  -- projected through them.
  SELECT 'registry_key_duplicate',
         detail_view || ' / ' || coalesce(classification, '-')
  FROM _eds_rule_registry
  GROUP BY detail_view, classification HAVING count(*) > 1

  UNION ALL
  -- A rule is one thing: one worklist, one stage, one severity, one source — however
  -- many classes project into it (the field shapes do). A rule spanning two answers
  -- to any of those is two rules wearing one name.
  SELECT 'registry_rule_inconsistent', rule
  FROM _eds_rule_registry
  WHERE rule IS NOT NULL
  GROUP BY rule
  HAVING count(DISTINCT source || '/' || detail_view || '/' || resolution_stage || '/' || severity) > 1

  UNION ALL
  -- A row either emits (rule filled, its columns with it) or is excluded with its
  -- reason on record — never both, never neither. This is the "never silently
  -- adjudicated" rule made structural.
  SELECT 'registry_rule_xor_excluded',
         detail_view || ' / ' || coalesce(classification, '-')
  FROM _eds_rule_registry
  WHERE (rule IS NULL) = (excluded_because IS NULL)
     OR (rule IS NOT NULL AND (resolution_stage IS NULL OR severity IS NULL))

  UNION ALL
  -- The stage and severity vocabularies, closed at their one source: findings inherit
  -- these columns from the registry, so guarding them here guards every finding.
  SELECT 'registry_stage_unknown', rule || ' -> ' || resolution_stage
  FROM _eds_rule_registry
  WHERE rule IS NOT NULL
    AND resolution_stage NOT IN ('manufacturers', 'titles', 'models', 'content')

  UNION ALL
  SELECT 'registry_severity_unknown', rule || ' -> ' || severity
  FROM _eds_rule_registry
  WHERE rule IS NOT NULL AND severity NOT IN ('error', 'warning')

  UNION ALL
  -- An excluded class claiming coverage must name a rule that exists — otherwise the
  -- claim is the silent adjudication it exists to prevent.
  SELECT 'registry_covered_by_unregistered',
         detail_view || ' / ' || coalesce(classification, '-') || ' -> ' || covered_by_rule
  FROM _eds_rule_registry AS x
  WHERE covered_by_rule IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM _eds_rule_registry AS r WHERE r.rule = x.covered_by_rule)

  UNION ALL
  -- ─── invariants of the adjudications relation ───
  -- The scope vocabulary is closed: every consumer projects one scope by literal
  -- string, so a row under an unknown scope would be invisible to all of them.
  SELECT 'adjudication_scope_unknown', scope
  FROM _eds_adjudications
  WHERE scope NOT IN ('finding', 'maker-pair', 'vocabulary-value')

  UNION ALL
  -- Every row holds its scope's shape: its own keys filled, the other scopes' keys
  -- NULL. A finding row missing its rule matches nothing; a pair row carrying
  -- vocabulary keys is two adjudications fused into one unreadable row.
  SELECT 'adjudication_scope_keys_mismatched',
         scope || ': ' || coalesce(note, '<no note>')
  FROM _eds_adjudications
  WHERE CASE scope
          WHEN 'finding' THEN
            NOT (source IS NOT NULL AND rule IS NOT NULL
                 AND opdb_manufacturer_id IS NULL AND manufacturer_slug IS NULL
                 AND target_entity_type IS NULL AND target_value IS NULL)
          WHEN 'maker-pair' THEN
            NOT (source IS NOT NULL
                 AND opdb_manufacturer_id IS NOT NULL AND manufacturer_slug IS NOT NULL
                 AND rule IS NULL AND external_id IS NULL AND entity_public_id IS NULL
                 AND discriminator IS NULL
                 AND target_entity_type IS NULL AND target_value IS NULL)
          WHEN 'vocabulary-value' THEN
            NOT (source IS NOT NULL
                 AND target_entity_type IS NOT NULL AND target_value IS NOT NULL
                 AND rule IS NULL AND external_id IS NULL AND entity_public_id IS NULL
                 AND discriminator IS NULL
                 AND opdb_manufacturer_id IS NULL AND manufacturer_slug IS NULL)
          ELSE false  -- an unknown scope is already reported above
        END

  UNION ALL
  -- An adjudication without its reason is an assertion of authority, not a record of
  -- judgment.
  SELECT 'adjudication_note_required',
         scope || ' / ' || coalesce(rule, manufacturer_slug, target_value, '-')
  FROM _eds_adjudications
  WHERE note IS NULL;
COMMENT ON VIEW external_data_source_findings_checks IS
  'Empty when healthy — invariants of the findings layer, its rule registry and the adjudications: no NULL in a required column, every finding agreeing with the registry on stage/severity/detail_view, one row per finding identity, one registry row per (worklist, class), every rule one thing, every exclusion reasoned, every detail_view resolvable, every dismissal naming a registered rule, every adjudication in its scope''s shape with its reason.';
