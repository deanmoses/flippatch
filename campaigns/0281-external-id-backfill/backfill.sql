-- External ID backfill, 2023 and newer — the analysis behind `0281-external-id-backfill`.
--
-- WHAT THIS EMITS: one row per catalog model that should carry an external identifier
-- it does not yet hold. Three populations, deliberately kept apart because their
-- EVIDENCE differs and each row's note must say which kind it rests on:
--
--   opdb_named    the comparison layer offers it: OPDB's listing name, manufacturer and
--                 year all match the catalog model, and no rival candidate survives.
--   opdb_edition  the layer classifies the listing `absent` and is WRONG about it. The
--                 machine is in the catalog under a longer edition name — OPDB writes
--                 "Sonic the Hedgehog (Arcade)" where the catalog writes "(Arcade
--                 Edition)" — and `name_norm` only lowercases and strips punctuation,
--                 so no re-run will ever bridge that gap. These are a HUMAN judgment
--                 recorded in `bf_edition_pairs` below; the checks hold it honest.
--   ipdb          the layer offers it, and unlike OPDB the listing is citable, so these
--                 carry a real `ipdb:` cite with a verbatim quote instead of a bare note.
--
-- WHY 2023+. The cutoff is the campaign's whole scope decision. Older disagreements are
-- re-litigations of matches already adjudicated once, and several of them are entangled
-- with unresolved title-grouping splits (`ipdb_id_chain = 'titles_disagree'`), where
-- linking a model would silently take a side. Every row here is newer than the last
-- acquisition and none of them touch a contested grouping. The year band 2020-2022 is
-- empty, so 2023 is a natural seam rather than an arbitrary line.
--
-- WHY NO OPDB CITE. An `opdb:` cite resolves to a cached `opdb.org/machines/<id>` page,
-- and that URL takes a numeric database id the published export does not carry — the
-- Group-Model-Alias identifier is not addressable there. So the OPDB rows carry their
-- provenance in the note, which is what `note-required` asks for anyway. The IPDB rows
-- have no such problem and are cited properly.

.read ../flippatch/scripts/analysis/external_data_sources.sql

-- pinexplore's dumps raw: the comparison layer attaches `px` at BAKE time only, so a
-- session reading its finished tables has no handle on the source. The IPDB quote is
-- cut from those columns, so this campaign attaches it itself — the same alias the
-- layer uses, so the two can never end up with two handles on one file.
ATTACH IF NOT EXISTS '../pinexplore/explore.duckdb' AS px (READ_ONLY);

-- The scope line, in one place so `bf_checks` and the populations cannot drift apart.
CREATE OR REPLACE MACRO bf_earliest_year() AS 2023;

-- ═══ REFERENCE — human judgment, held honest by the checks ══════════════════
--
-- The edition-wording pairs. Each is a listing the layer calls `absent` that is in fact
-- the catalog model named beside it, under OPDB's shorter wording for the edition.
-- Approved row by row rather than inferred: `bf_checks` asserts the manufacturer and
-- year agree and that the layer still calls the listing absent, but NOTHING can machine-
-- verify that "(CE)" means "(Collector's Edition)" — that is the judgment being recorded.
CREATE OR REPLACE VIEW bf_edition_pairs AS
  SELECT * FROM (VALUES
    ('GvBPJ-M1rjr-AO7zb', 'sonic-the-hedgehog-arcade-edition'),
    ('GvBPJ-M1rjr-ARBkl', 'sonic-the-hedgehog-collectors-edition'),
    ('GvBPJ-M1rjr-A9Pzw', 'sonic-the-hedgehog-special-edition'),
    ('GBLzz-M4ok4-ARnwo', 'transformers-more-than-meets-the-eye-limited-edition'),
    ('Gwej3-MrRYv',       'the-3-musketeers'),
    ('Gj6PZ-Mb5z6-A1ZzW', 'galactic-tank-force-victory-edition'),
    ('GvBQX-M0ody-A1kee', 'houdini-100th-anniversary'),
    ('G4llj-M3dyz-A1Xy5', 'tales-of-the-arabian-nights-30th-anniversary-remake'),
    ('G4llj-M3dyz-ARWyv', 'tales-of-the-arabian-nights-legacy-edition-remake')
  ) AS t(opdb_id, model_slug);

-- ═══ POPULATIONS ════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW bf_opdb_named AS
  SELECT
    u.unlinked_model_slug        AS model_slug,
    'opdb_named'                 AS evidence,
    'opdb_id'                    AS field_name,
    u.opdb_id                    AS value,
    u.opdb_name                  AS ext_name,
    u.opdb_manufacturer_name     AS note_maker,
    u.opdb_year                  AS ext_year,
    NULL                         AS cite_ref,
    NULL                         AS quote
  FROM opdb_models_unmatched AS u
  WHERE u.classification = 'catalog_holds_unlinked'
    AND u.opdb_year >= bf_earliest_year();

CREATE OR REPLACE VIEW bf_opdb_edition AS
  SELECT
    p.model_slug,
    'opdb_edition'               AS evidence,
    'opdb_id'                    AS field_name,
    u.opdb_id                    AS value,
    u.opdb_name                  AS ext_name,
    u.opdb_manufacturer_name     AS note_maker,
    u.opdb_year                  AS ext_year,
    NULL                         AS cite_ref,
    NULL                         AS quote
  FROM bf_edition_pairs AS p
  INNER JOIN opdb_models_unmatched AS u USING (opdb_id);

-- The IPDB quote, cut from the mart's own columns so it is verbatim by construction --
-- `quotes.sources` renders the same three fields, the title bare, the header line bare
-- and the corporate entity under a `Manufacturer:` label. Three spans joined in SOURCE
-- order (name, then header date, then manufacturer), which is the order the page prints
-- and the order `verify-quote-verbatim` requires. Together they are exactly the triangle
-- the identity rests on: name, year, maker.
CREATE OR REPLACE VIEW bf_ipdb AS
  SELECT
    u.unlinked_model_slug        AS model_slug,
    'ipdb'                       AS evidence,
    'ipdb_id'                    AS field_name,
    u.ipdb_id::VARCHAR           AS value,
    d.name                       AS ext_name,
    split_part(d.corporate_entity_text, ',', 1) AS note_maker,
    u.ipdb_date_year             AS ext_year,
    'ipdb:' || u.ipdb_id         AS cite_ref,
    d.name || ' [...] ' || d.additional_details
      || ' [...] Manufacturer: ' || d.corporate_entity_text AS quote
  FROM ipdb_models_unmatched AS u
  INNER JOIN px.ipdb.models AS d ON d.ipdb_id = u.ipdb_id
  WHERE u.classification = 'catalog_holds_unlinked'
    AND u.ipdb_date_year >= bf_earliest_year();

CREATE OR REPLACE VIEW bf_patch_rows AS
            SELECT * FROM bf_opdb_named
  UNION ALL SELECT * FROM bf_opdb_edition
  UNION ALL SELECT * FROM bf_ipdb;

-- ═══ SUMMARY & CHECKS ═══════════════════════════════════════════════════════

CREATE OR REPLACE VIEW bf_summary AS
            SELECT evidence AS metric, count(*) AS value FROM bf_patch_rows GROUP BY evidence
  UNION ALL SELECT 'rows_total', count(*) FROM bf_patch_rows
  UNION ALL SELECT 'earliest_year_in_scope', bf_earliest_year();

CREATE OR REPLACE VIEW bf_checks AS
  -- ANCHOR. Each population is non-empty. A renamed layer column or a re-baked layer
  -- that reclassifies everything would otherwise zero a whole branch silently, and a
  -- patch generated from nothing is still perfectly well-formed YAML.
            SELECT 'population_empty' AS check_name, e AS detail
            FROM (VALUES ('opdb_named'), ('opdb_edition'), ('ipdb')) AS t(e)
            WHERE NOT EXISTS (SELECT 1 FROM bf_patch_rows r WHERE r.evidence = e)

  -- Every hand-approved pair still resolves. A stale slug or a retired OPDB id would
  -- otherwise drop out of the INNER JOIN and shrink the patch with no error.
  UNION ALL SELECT 'edition_pair_unresolved', p.opdb_id
            FROM bf_edition_pairs p
            WHERE NOT EXISTS (SELECT 1 FROM bf_opdb_edition e WHERE e.value = p.opdb_id)

  -- The judgment is "same machine, different wording", so the two legs a machine CAN be
  -- checked on must hold. Name is deliberately not checked -- differing is the premise.
  UNION ALL SELECT 'edition_pair_maker_disagrees', e.value
            FROM bf_opdb_edition e
            INNER JOIN models m ON m.slug = e.model_slug
            INNER JOIN opdb_models_unmatched u ON u.opdb_id = e.value
            WHERE m.manufacturer_slug IS DISTINCT FROM u.opdb_manufacturer_slug
  UNION ALL SELECT 'edition_pair_year_disagrees', e.value
            FROM bf_opdb_edition e
            INNER JOIN models m ON m.slug = e.model_slug
            WHERE m.production_year IS DISTINCT FROM e.ext_year

  -- The override stays an override. If the layer starts offering one of these itself,
  -- the hand-curated pair is redundant and should be retired rather than double-emitted.
  UNION ALL SELECT 'edition_pair_no_longer_absent', u.opdb_id
            FROM bf_edition_pairs p
            INNER JOIN opdb_models_unmatched u USING (opdb_id)
            WHERE u.classification <> 'absent'

  -- Never overwrite. Every target must be a model that holds no id in this field yet.
  UNION ALL SELECT 'target_already_holds_an_id', r.model_slug
            FROM bf_patch_rows r
            INNER JOIN models m ON m.slug = r.model_slug
            WHERE (r.field_name = 'opdb_id' AND m.opdb_id IS NOT NULL)
               OR (r.field_name = 'ipdb_id' AND m.ipdb_id IS NOT NULL)
  UNION ALL SELECT 'target_model_missing', r.model_slug
            FROM bf_patch_rows r
            WHERE NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = r.model_slug)

  -- Identifiers are unique per field, so a value another live model already carries
  -- would be a duplicate link, not a backfill.
  UNION ALL SELECT 'value_already_live', r.value
            FROM bf_patch_rows r
            WHERE EXISTS (SELECT 1 FROM models m WHERE m.opdb_id = r.value)
               OR EXISTS (SELECT 1 FROM models m WHERE m.ipdb_id::VARCHAR = r.value)

  -- One row per model per field, or the patch asserts a field twice on one entry.
  UNION ALL SELECT 'duplicate_target', target
            FROM (SELECT model_slug || '/' || field_name AS target FROM bf_patch_rows)
            GROUP BY target HAVING count(*) > 1

  -- The quote must carry all three spans, or the evidence is not the triangle the note
  -- claims. A NULL component would silently concatenate to a short string.
  UNION ALL SELECT 'ipdb_quote_incomplete', model_slug
            FROM bf_ipdb
            WHERE quote IS NULL OR ext_name IS NULL OR note_maker IS NULL
               OR length(quote) - length(replace(quote, '[...]', '')) <> 10

  -- Every row must be able to fill its note template.
  UNION ALL SELECT 'note_field_missing', model_slug
            FROM bf_patch_rows
            WHERE ext_name IS NULL OR note_maker IS NULL OR ext_year IS NULL

  -- The emitter narrows an ipdb_id back to a JSON integer, because that is how every
  -- ipdb_id already in the catalog is stored and a claim's value is compared as JSON.
  -- The union above widens both id kinds to VARCHAR to stack them, so this asserts the
  -- narrowing is always possible rather than letting the generator raise on a surprise.
  UNION ALL SELECT 'ipdb_id_not_numeric', value
            FROM bf_patch_rows
            WHERE field_name = 'ipdb_id' AND NOT regexp_matches(value, '^[0-9]+$');
