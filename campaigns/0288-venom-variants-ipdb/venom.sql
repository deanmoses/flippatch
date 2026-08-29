-- IPDB's testimony on the two Venom variants — the analysis behind
-- `0288-ipdb-venom-variants`.
--
-- WHY THESE TWO, OUTSIDE THE 2023+ SWEEP'S SCOPE RULE. Campaigns 0284/0286 fill source
-- content only for models THIS pass linked, on the principle that a model linked earlier
-- has either had its source content ingested already or was skipped for a reason nobody
-- recorded -- and reopening the latter silently overwrites a decision. These two were
-- checked individually against that rule and clear it:
--
--   * no patch has asserted or retracted any field this one writes -- their `ipdb_id`
--     comes from the seed baseline, and the patches that do touch them (0204's themes,
--     0206's limited-edition tag) decide other things entirely. Contrast `road-trip`,
--     whose production_month was deliberately retracted by 0233 and 0235 as a
--     world-debut date wrongly read as a manufacture date: that IS a decision about a
--     field here, and it is why road-trip is excluded;
--   * IPDB holds no claims on them at all, so nothing here supersedes or no-ops.
--
-- They are a gap, not a decision. `venom-pro` -- the same machine's third variant, which
-- 0281 linked and 0285/0287 filled -- is the shape this restores them to.
--
-- THE MONTH IS A DELIBERATE DISAGREEMENT. OPDB claims July for both and IPDB says
-- August. `opdb` outranks `ipdb`, so July keeps resolving and nothing a reader sees
-- changes; what changes is that IPDB's August is on the record instead of invisible.
-- That is the point of a source-attributed claim.

ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- ═══ REFERENCE — the two models, adjudicated by hand ═════════════════════════
--
-- An explicit pair rather than a derived population: the judgment being recorded is
-- "these two were checked against the scope rule and clear it", which no query can
-- make for itself. `venom_checks` holds the pair to the facts that justified it.
CREATE OR REPLACE VIEW venom_scope AS
  SELECT * FROM (VALUES
    ('venom-limited-edition', 7066),
    ('venom-premium',         7065)
  ) AS t(model_slug, ipdb_id);

CREATE OR REPLACE VIEW venom_rows AS
  WITH m AS (
    SELECT s.model_slug, im.*
    FROM venom_scope AS s
    INNER JOIN models AS mo ON mo.slug = s.model_slug AND mo.ipdb_id = s.ipdb_id
    INNER JOIN px.ipdb.models AS im ON im.ipdb_id = s.ipdb_id
  )
  -- Each field rides the line of the rendered row that states it, so one quote supports
  -- one fact. The header line states year and month together -- one statement, one
  -- changeset -- which is why the emitter groups by quote rather than by field.
            SELECT model_slug, ipdb_id, 'field' AS kind, 'production_year' AS name,
                   additional_details_date_year::VARCHAR AS value, true AS numeric_value,
                   additional_details AS quote, additional_details_date_kind AS date_kind
            FROM m WHERE additional_details_date_kind = 'manufacture'
  UNION ALL SELECT model_slug, ipdb_id, 'field', 'production_month',
                   additional_details_date_month::VARCHAR, true,
                   additional_details, additional_details_date_kind
            FROM m WHERE additional_details_date_kind = 'manufacture'
  UNION ALL SELECT model_slug, ipdb_id, 'field', 'player_count', players::VARCHAR, true,
                   'Players: ' || players::VARCHAR, NULL
            FROM m WHERE players IS NOT NULL
  UNION ALL SELECT model_slug, ipdb_id, 'field', 'technology_generation',
                   technology_generation_slug, false, 'Type: ' || type_text, NULL
            FROM m WHERE technology_generation_slug IS NOT NULL AND type_text IS NOT NULL
  -- A JSON STRING, not a number: the schema keeps the field a string so it can carry an
  -- approximate or ranged quantity later, and the whole seed uses the string form.
  UNION ALL SELECT model_slug, ipdb_id, 'field', 'production_quantity',
                   production_number::VARCHAR, false,
                   'Production: ' || production_number::VARCHAR, NULL
            FROM m WHERE production_number IS NOT NULL
  UNION ALL SELECT model_slug, ipdb_id, 'credit', 'design', 'brian-eddy', false,
                   'Design by: ' || design_by, NULL
            FROM m WHERE design_by IS NOT NULL
  UNION ALL SELECT model_slug, ipdb_id, 'credit', 'art', 'jeremy-packer', false,
                   'Art by: ' || art_by, NULL
            FROM m WHERE art_by IS NOT NULL;

-- ═══ SUMMARY & CHECKS ═══════════════════════════════════════════════════════

CREATE OR REPLACE VIEW venom_summary AS
            SELECT 'models' AS metric, count(DISTINCT model_slug) AS value FROM venom_rows
  UNION ALL SELECT kind || 's', count(*) FROM venom_rows GROUP BY kind
  UNION ALL SELECT 'rows_total', count(*) FROM venom_rows;

CREATE OR REPLACE VIEW venom_checks AS
            SELECT 'population_empty' AS check_name, '' AS detail
            WHERE NOT EXISTS (SELECT 1 FROM venom_rows)

  -- Both models must still resolve, with the ipdb_id the pair was adjudicated against.
  UNION ALL SELECT 'model_or_id_unresolved', s.model_slug
            FROM venom_scope s
            WHERE NOT EXISTS (SELECT 1 FROM models m
                              WHERE m.slug = s.model_slug AND m.ipdb_id = s.ipdb_id)

  -- THE JUSTIFICATION, ENFORCED — PER FIELD, not per model. What the exemption rests
  -- on is that no authored decision covers the facts being written here. A patch that
  -- touched some OTHER field is not such a decision: both models carry themes from
  -- 0204 and a limited-edition tag from 0206, and neither says anything about IPDB's
  -- dates, player count, hardware or credits. The test that matters is whether a patch
  -- has asserted or RETRACTED one of the very fields below -- which is exactly what
  -- disqualifies `road-trip`, whose production_month was retracted by 0233 and 0235 as
  -- a world-debut date misread as a manufacture date.
  UNION ALL SELECT 'field_touched_by_a_patch', p.model_slug || '/' || p.field_name
            FROM patch_claims p
            INNER JOIN venom_scope s USING (model_slug)
            WHERE p.field_name IN (SELECT CASE WHEN kind = 'credit' THEN 'credit' ELSE name END
                                   FROM venom_rows)
  UNION ALL SELECT 'field_has_a_retraction', r.model_slug || '/' || r.field_name
            FROM patch_retractions r
            INNER JOIN venom_scope s USING (model_slug)
            WHERE r.field_name IN (SELECT CASE WHEN kind = 'credit' THEN 'credit' ELSE name END
                                   FROM venom_rows)

  -- IPDB must hold no claim on the field, or this supersedes rather than fills.
  UNION ALL SELECT 'ipdb_already_claims_field', r.model_slug || '/' || r.name
            FROM venom_rows r
            INNER JOIN models m ON m.slug = r.model_slug
            INNER JOIN model_claims c ON c.model_id = m.id AND c.field_name = r.name
                                     AND c.ingest_source_slug = 'ipdb'
            WHERE r.kind = 'field'

  -- A project date in a production field asserts the wrong fact about the machine.
  UNION ALL SELECT 'date_kind_not_manufacture', model_slug || '/' || coalesce(date_kind, 'NULL')
            FROM venom_rows
            WHERE name IN ('production_year', 'production_month')
              AND date_kind IS DISTINCT FROM 'manufacture'

  -- FK targets must resolve, and the credit must not already be present.
  UNION ALL SELECT 'credit_person_unresolved', value
            FROM venom_rows WHERE kind = 'credit' AND value NOT IN (SELECT slug FROM people)
  UNION ALL SELECT 'credit_role_unresolved', name
            FROM venom_rows WHERE kind = 'credit' AND name NOT IN (SELECT slug FROM credit_roles)
  UNION ALL SELECT 'credit_already_present', r.model_slug || '/' || r.value
            FROM venom_rows r
            INNER JOIN model_credits mc ON mc.model_slug = r.model_slug
                                       AND mc.person_slug = r.value AND mc.role_slug = r.name
            WHERE r.kind = 'credit'
  UNION ALL SELECT 'technology_generation_unresolved', value
            FROM venom_rows WHERE name = 'technology_generation'
              AND value NOT IN (SELECT slug FROM technology_generations)

  -- The credit quote must name the person the credit asserts, or the cite supports a
  -- different fact than the claim. IPDB prints the name; the slug is our resolution of
  -- it, so this is the one place the two are checked against each other.
  UNION ALL SELECT 'credit_quote_person_mismatch', model_slug || '/' || value
            FROM venom_rows
            WHERE kind = 'credit'
              AND replace(lower(split_part(quote, ': ', 2)), ' ', '-') <> value

  UNION ALL SELECT 'quote_missing', model_slug || '/' || name
            FROM venom_rows WHERE quote IS NULL OR trim(quote) = ''
  UNION ALL SELECT 'duplicate_target', k
            FROM (SELECT model_slug || '/' || kind || '/' || name AS k FROM venom_rows)
            GROUP BY k HAVING count(*) > 1
  UNION ALL SELECT 'numeric_value_not_numeric', value
            FROM venom_rows WHERE numeric_value AND NOT regexp_matches(value, '^[0-9]+$');
