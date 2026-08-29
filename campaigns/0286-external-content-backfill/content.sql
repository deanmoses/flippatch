-- Credits and tags for the models linked in 0281/0283 — the analysis behind
-- `0286-opdb-model-tags` and `0287-ipdb-model-credits`.
--
-- The companion to `0284-external-field-backfill`, same scope and same attribution
-- reasoning, for the two kinds of content that are not scalar fields: IPDB's credit
-- block and OPDB's tag vocabulary. Two patches again, because a patch carries one
-- attribution and these belong to their sources.
--
-- SCOPE IS THE MODELS THIS PASS LINKED, read from `patch_claims`. A model linked
-- earlier has already had its source content ingested; one still missing it was
-- skipped for a reason nobody recorded, and reopening that is how a deliberate
-- omission gets silently overwritten. Two IPDB-linked models with missing credits sit
-- just outside this line -- `venom-limited-edition` and `venom-premium` -- and stay
-- outside it deliberately.
--
-- CREDITS ARE CITED, TAGS ARE NOT. IPDB's credit block is the field's accepted
-- reference and its page is citable, so each credit rides the line that names it. OPDB
-- has no citable page (its machine URL takes a numeric database id the export does not
-- carry), so the tag rows carry a note instead, exactly as 0284 does.

.read ../flippatch/scripts/analysis/external_data_sources.sql
ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

CREATE OR REPLACE VIEW cb_scope AS
  SELECT DISTINCT field_name AS id_field, model_slug
  FROM patch_claims
  WHERE patch_number IN (281, 283) AND field_name IN ('opdb_id', 'ipdb_id');

-- ═══ IPDB CREDITS ═══════════════════════════════════════════════════════════
--
-- The quote is the page's own credit line ("Design by: Jack Danger"), which states
-- exactly one credit and nothing else -- one quote, one fact. `_IPDB_ROW_FIELDS` maps
-- each role to the label the rendered row prints, and the two roles in this scope are
-- the only ones needed; a third would fail `credit_role_label_unknown` below rather
-- than emit an unquotable credit.
CREATE OR REPLACE VIEW cb_credit_labels AS
  SELECT * FROM (VALUES ('design', 'Design by'), ('art', 'Art by')) AS t(role_slug, label);

CREATE OR REPLACE VIEW cb_credits AS
  SELECT c.model_slug, c.ipdb_id, c.role_slug, c.person_slug, c.ipdb_person_name,
         l.label || ': ' || c.ipdb_person_name AS quote
  FROM ipdb_credits_missing AS c
  INNER JOIN cb_scope AS s ON s.model_slug = c.model_slug AND s.id_field = 'ipdb_id'
  LEFT JOIN cb_credit_labels AS l USING (role_slug);

-- ═══ OPDB TAGS ══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW cb_tags AS
  SELECT v.model_slug, v.target_slug AS tag_slug
  FROM opdb_model_vocabulary_missing AS v
  INNER JOIN cb_scope AS s ON s.model_slug = v.model_slug AND s.id_field = 'opdb_id'
  WHERE v.target_entity_type = 'tag';

-- ═══ SUMMARY & CHECKS ═══════════════════════════════════════════════════════

CREATE OR REPLACE VIEW cb_summary AS
            SELECT 'credits' AS metric, count(*) AS value FROM cb_credits
  UNION ALL SELECT 'credit_models', count(DISTINCT model_slug) FROM cb_credits
  UNION ALL SELECT 'credit_' || role_slug, count(*) FROM cb_credits GROUP BY role_slug
  UNION ALL SELECT 'tags', count(*) FROM cb_tags
  UNION ALL SELECT 'tag_' || tag_slug, count(*) FROM cb_tags GROUP BY tag_slug;

CREATE OR REPLACE VIEW cb_checks AS
  -- ANCHOR: both populations non-empty, or a renamed upstream column emits an empty
  -- but perfectly well-formed patch.
            SELECT 'population_empty' AS check_name, s AS detail
            FROM (VALUES ('credits'), ('tags')) AS t(s)
            WHERE (s = 'credits' AND NOT EXISTS (SELECT 1 FROM cb_credits))
               OR (s = 'tags'    AND NOT EXISTS (SELECT 1 FROM cb_tags))

  -- A credit's person and role are FK targets that must already resolve; the layer
  -- reports an unmatched person separately (`ipdb-person-unmatched`) and such a row
  -- must never reach a patch as a silent NULL.
  UNION ALL SELECT 'credit_person_unresolved', model_slug || '/' || ipdb_person_name
            FROM cb_credits WHERE person_slug IS NULL
  UNION ALL SELECT 'credit_person_ambiguous', c.model_slug || '/' || c.ipdb_person_name
            FROM ipdb_credits_missing c
            INNER JOIN cb_scope s ON s.model_slug = c.model_slug AND s.id_field = 'ipdb_id'
            WHERE c.n_person_matches <> 1
  UNION ALL SELECT 'credit_person_missing_from_catalog', person_slug
            FROM cb_credits WHERE person_slug NOT IN (SELECT slug FROM people)
  UNION ALL SELECT 'credit_role_unresolved', role_slug
            FROM cb_credits WHERE role_slug NOT IN (SELECT slug FROM credit_roles)

  -- Every credit must be quotable, or its cite supports nothing. A role with no label
  -- mapping lands here rather than emitting a credit the verbatim gate cannot check.
  UNION ALL SELECT 'credit_role_label_unknown', role_slug
            FROM cb_credits WHERE quote IS NULL

  -- Never re-assert a member the model already carries: a relationship member that is
  -- already present is a no-op, and an entry whose only effect is a no-op is rejected.
  UNION ALL SELECT 'credit_already_present', c.model_slug || '/' || c.person_slug
            FROM cb_credits c
            INNER JOIN model_credits mc ON mc.model_slug = c.model_slug
                                       AND mc.person_slug = c.person_slug
                                       AND mc.role_slug = c.role_slug
  -- `model_tag_slugs` is one row per model holding a LIST of slugs, so membership is
  -- a list predicate rather than a join key.
  UNION ALL SELECT 'tag_already_present', t.model_slug || '/' || t.tag_slug
            FROM cb_tags t
            INNER JOIN models m ON m.slug = t.model_slug
            INNER JOIN model_tag_slugs mt ON mt.model_id = m.id
            WHERE list_contains(mt.tag_slugs, t.tag_slug)

  UNION ALL SELECT 'tag_unresolved', tag_slug
            FROM cb_tags WHERE tag_slug NOT IN (SELECT slug FROM tags)

  -- One row per (model, person, role) and per (model, tag), or the patch asserts a
  -- duplicate member, which ingest rejects.
  UNION ALL SELECT 'duplicate_credit', k FROM (
              SELECT model_slug || '/' || person_slug || '/' || role_slug AS k FROM cb_credits
            ) GROUP BY k HAVING count(*) > 1
  UNION ALL SELECT 'duplicate_tag', k FROM (
              SELECT model_slug || '/' || tag_slug AS k FROM cb_tags
            ) GROUP BY k HAVING count(*) > 1;
