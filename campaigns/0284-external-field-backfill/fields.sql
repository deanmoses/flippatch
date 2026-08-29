-- External field values for the models linked in 0281/0283 — the analysis behind
-- `0284-opdb-model-fields` and `0285-ipdb-model-fields`.
--
-- WHAT THIS EMITS: every scalar field value IPDB and OPDB hold for the models whose
-- external id was written by patches 0281 and 0283, as claims attributed to the SOURCE
-- rather than to Flipcommons. Two patches, because a patch carries one attribution.
--
-- WHY ONLY THOSE MODELS. A model linked before this pass already had its external field
-- data ingested; one that is linked and still has no source claims is either newly
-- linked or was skipped for a reason nobody recorded, and reopening the latter is how a
-- deliberate omission gets silently overwritten. The scope is therefore the models THIS
-- pass linked, read from `patch_claims` rather than inferred from a date or a NULL.
--
-- WHY VALUES THAT AGREE ARE EMITTED TOO. The point of a source-attributed claim is to
-- record what the source says, not to change what a reader sees: `flipcommons-catalog`
-- outranks both sources, so an agreeing value is corroboration and a disagreeing one is
-- recorded dissent, neither of which moves the resolved value. This is safe against the
-- no-op rejection because `_diff_claims` compares WITHIN a source (it filters on
-- `actor_id`), and these sources hold no claims at all on these models — so every row
-- here is a new claim rather than a re-assertion.
--
-- IPDB DATES ARE KIND-QUALIFIED. Only a `manufacture` date says anything about
-- production; a project date is a different fact and must never land in
-- `production_year`/`production_month`. The rows below carry the kind and `fb_checks`
-- refuses anything else.

ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- The scope, in one place. Both patches and every check read it.
CREATE OR REPLACE VIEW fb_scope AS
  SELECT DISTINCT field_name AS id_field, model_slug
  FROM patch_claims
  WHERE patch_number IN (281, 283) AND field_name IN ('opdb_id', 'ipdb_id');

-- ═══ OPDB ═══════════════════════════════════════════════════════════════════
--
-- No cite: an `opdb:` cite resolves to a cached opdb.org machine page keyed by a
-- numeric database id the published export does not carry, so there is no page to
-- point at. The note carries the provenance and `note-required` is satisfied by it.
CREATE OR REPLACE VIEW fb_opdb_rows AS
  WITH m AS (
    SELECT mo.slug, mo.id, om.*
    FROM fb_scope AS s
    INNER JOIN models AS mo ON mo.slug = s.model_slug AND s.id_field = 'opdb_id'
    INNER JOIN px.opdb.models AS om ON om.opdb_id = mo.opdb_id
  )
            SELECT slug AS model_slug, 'production_year'  AS field_name, production_year::VARCHAR       AS value, true  AS numeric_value FROM m WHERE production_year IS NOT NULL
  UNION ALL SELECT slug, 'production_month',      production_month::VARCHAR,      true  FROM m WHERE production_month IS NOT NULL
  UNION ALL SELECT slug, 'player_count',          player_count::VARCHAR,          true  FROM m WHERE player_count IS NOT NULL
  UNION ALL SELECT slug, 'technology_generation', technology_generation,          false FROM m WHERE technology_generation IS NOT NULL
  UNION ALL SELECT slug, 'display_type',          display_type,                   false FROM m WHERE display_type IS NOT NULL;

-- ═══ IPDB ═══════════════════════════════════════════════════════════════════
--
-- Each field rides the line of the rendered row that states it, so a quote supports
-- exactly one fact and `verify-quote-verbatim` can check it independently. The header
-- line states the date and is the carrier for BOTH year and month -- one statement,
-- one changeset -- which is why `quote` is the grouping key the emitter uses rather
-- than the field name.
CREATE OR REPLACE VIEW fb_ipdb_rows AS
  WITH m AS (
    SELECT mo.slug, im.*
    FROM fb_scope AS s
    INNER JOIN models AS mo ON mo.slug = s.model_slug AND s.id_field = 'ipdb_id'
    INNER JOIN px.ipdb.models AS im ON im.ipdb_id = mo.ipdb_id
  )
            SELECT slug AS model_slug, ipdb_id, 'production_year' AS field_name,
                   additional_details_date_year::VARCHAR AS value, true AS numeric_value,
                   additional_details AS quote, additional_details_date_kind AS date_kind
            FROM m WHERE additional_details_date_kind = 'manufacture' AND additional_details_date_year IS NOT NULL
  UNION ALL SELECT slug, ipdb_id, 'production_month', additional_details_date_month::VARCHAR, true,
                   additional_details, additional_details_date_kind
            FROM m WHERE additional_details_date_kind = 'manufacture' AND additional_details_date_month IS NOT NULL
  UNION ALL SELECT slug, ipdb_id, 'player_count', players::VARCHAR, true,
                   'Players: ' || players::VARCHAR, NULL
            FROM m WHERE players IS NOT NULL
  UNION ALL SELECT slug, ipdb_id, 'technology_generation', technology_generation_slug, false,
                   'Type: ' || type_text, NULL
            FROM m WHERE technology_generation_slug IS NOT NULL AND type_text IS NOT NULL
  -- `production_quantity` is the one field here that is a JSON STRING rather than a
  -- number: the schema keeps it a string so it can eventually carry an approximate or
  -- ranged quantity, and the whole seed uses the string form. Hence `false`.
  UNION ALL SELECT slug, ipdb_id, 'production_quantity', production_number::VARCHAR, false,
                   'Production: ' || production_number::VARCHAR, NULL
            FROM m WHERE production_number IS NOT NULL;

-- ═══ SUMMARY & CHECKS ═══════════════════════════════════════════════════════

CREATE OR REPLACE VIEW fb_summary AS
            SELECT 'opdb_models' AS metric, count(DISTINCT model_slug) AS value FROM fb_opdb_rows
  UNION ALL SELECT 'opdb_claims', count(*) FROM fb_opdb_rows
  UNION ALL SELECT 'opdb_' || field_name, count(*) FROM fb_opdb_rows GROUP BY field_name
  UNION ALL SELECT 'ipdb_models', count(DISTINCT model_slug) FROM fb_ipdb_rows
  UNION ALL SELECT 'ipdb_claims', count(*) FROM fb_ipdb_rows
  UNION ALL SELECT 'ipdb_' || field_name, count(*) FROM fb_ipdb_rows GROUP BY field_name;

CREATE OR REPLACE VIEW fb_checks AS
  -- ANCHOR. Both populations non-empty: a renamed mart column would otherwise zero a
  -- whole branch silently and emit a well-formed patch containing nothing.
            SELECT 'population_empty' AS check_name, s AS detail
            FROM (VALUES ('opdb'), ('ipdb')) AS t(s)
            WHERE (s = 'opdb' AND NOT EXISTS (SELECT 1 FROM fb_opdb_rows))
               OR (s = 'ipdb' AND NOT EXISTS (SELECT 1 FROM fb_ipdb_rows))

  -- THE NO-OP GUARD. These patches are attributed to the source, and `_diff_claims`
  -- compares within a source — so a field the source ALREADY claims on this model
  -- would either be a silent no-op or an unintended supersede. Neither belongs in a
  -- backfill, and either means the scope has drifted off "models this pass linked".
  UNION ALL SELECT 'opdb_already_claims_field', r.model_slug || '/' || r.field_name
            FROM fb_opdb_rows r
            INNER JOIN models m ON m.slug = r.model_slug
            INNER JOIN model_claims c ON c.model_id = m.id AND c.field_name = r.field_name
                                     AND c.ingest_source_slug = 'opdb'
  UNION ALL SELECT 'ipdb_already_claims_field', r.model_slug || '/' || r.field_name
            FROM fb_ipdb_rows r
            INNER JOIN models m ON m.slug = r.model_slug
            INNER JOIN model_claims c ON c.model_id = m.id AND c.field_name = r.field_name
                                     AND c.ingest_source_slug = 'ipdb'

  -- Vocabulary values are FK targets: a value that is not a catalog slug fails at apply,
  -- and failing here instead costs a second rather than a snapshot round trip.
  UNION ALL SELECT 'technology_generation_unresolved', value
            FROM (SELECT value FROM fb_opdb_rows WHERE field_name = 'technology_generation'
                  UNION SELECT value FROM fb_ipdb_rows WHERE field_name = 'technology_generation')
            WHERE value NOT IN (SELECT slug FROM technology_generations)
  UNION ALL SELECT 'display_type_unresolved', value
            FROM fb_opdb_rows WHERE field_name = 'display_type'
              AND value NOT IN (SELECT slug FROM display_types)

  -- OPDB DEFAULTS A YEAR-ONLY MANUFACTURE DATE TO JANUARY 1, so a January from OPDB
  -- carries no month information — the defect patches 0055/0277/0278 exist to undo.
  -- None of this scope's months are January; if that ever changes the run stops here
  -- rather than importing a default as a fact.
  UNION ALL SELECT 'opdb_month_is_january', model_slug
            FROM fb_opdb_rows WHERE field_name = 'production_month' AND value = '1'

  -- A project date in a production field asserts the wrong fact about the machine.
  UNION ALL SELECT 'ipdb_date_kind_not_manufacture', model_slug || '/' || coalesce(date_kind, 'NULL')
            FROM fb_ipdb_rows
            WHERE field_name IN ('production_year', 'production_month')
              AND date_kind IS DISTINCT FROM 'manufacture'

  -- Every IPDB row must carry the line its quote is cut from, or the cite supports
  -- nothing and the verbatim gate has nothing to check.
  UNION ALL SELECT 'ipdb_quote_missing', model_slug || '/' || field_name
            FROM fb_ipdb_rows WHERE quote IS NULL OR trim(quote) = ''

  -- One row per model per field, or a patch entry asserts the same field twice.
  UNION ALL SELECT 'duplicate_target', target
            FROM (SELECT model_slug || '/' || field_name AS target FROM fb_opdb_rows
                  UNION ALL SELECT model_slug || '/' || field_name FROM fb_ipdb_rows)
            GROUP BY target HAVING count(*) > 1

  -- Numeric values are narrowed back to JSON integers by the emitter; a claim's value
  -- is compared as JSON, so a string "4" would never equal the 4 held elsewhere.
  UNION ALL SELECT 'numeric_value_not_numeric', value
            FROM (SELECT value, numeric_value FROM fb_opdb_rows
                  UNION ALL SELECT value, numeric_value FROM fb_ipdb_rows)
            WHERE numeric_value AND NOT regexp_matches(value, '^[0-9]+$');
