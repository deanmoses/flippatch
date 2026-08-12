-- Document publisher roots (patch 0227) — verify the hand-reviewed publisher →
-- manufacturer mapping against the live catalog.
--
-- The mapping does NOT come from the catalog: it was derived from IPDB filename
-- prefixes in pinexplore's explore.duckdb and reviewed by hand (see README.md for
-- the derivation and the judgement calls). This file's whole job is the join back
-- to the catalog: every mapped slug must be a live manufacturer, and the emitted
-- root takes the manufacturer's live name — so a renamed manufacturer never
-- drifts the root, and a mistyped slug fails the gate instead of minting a
-- publisher nothing can cite.
--
--   make analyze FILE=../flippatch/campaigns/0227-document-publisher-roots/roots.sql PREFIX=roots
--
-- The catalog decode below is flipcommons' shared foundation, reused verbatim; cwd
-- must be the flipcommons checkout for it and the CSV's ../flippatch path to resolve.

.read scripts/analysis/catalog.sql

CREATE OR REPLACE TEMP VIEW _mapping AS
SELECT manufacturer_slug, ipdb_prefixes, ipdb_docs, note
FROM read_csv('../flippatch/campaigns/0227-document-publisher-roots/publishers.csv',
              header = true, delim = ',', quote = '"', escape = '"',
              columns = {manufacturer_slug: 'VARCHAR', ipdb_prefixes: 'VARCHAR',
                         ipdb_docs: 'INTEGER', note: 'VARCHAR'});

-- One emitted root per mapping row. The slug is the reviewed judgement; the name
-- is read live from the catalog. ipdb_docs rides along only to order the patch
-- (and the README table) by trove weight — it is point-in-time evidence, not data.
CREATE OR REPLACE VIEW roots_patch_rows AS
SELECT m.manufacturer_slug, mf.name AS manufacturer_name, m.ipdb_docs
FROM _mapping m
JOIN manufacturers mf ON mf.slug = m.manufacturer_slug;

CREATE OR REPLACE VIEW roots_summary AS
SELECT
  (SELECT count(*) FROM _mapping)         AS mapped_publishers,
  (SELECT count(*) FROM roots_patch_rows) AS resolved_roots,
  -- Distinct by prefix set, not summed over rows: the two Stern roots share the
  -- 'Stern' prefix and its 692 documents (the corpus splits by era only when
  -- documents are seeded), so a row-wise sum would double-count them.
  (SELECT sum(ipdb_docs)
   FROM (SELECT DISTINCT ipdb_prefixes, ipdb_docs FROM _mapping)) AS ipdb_docs_covered;

CREATE OR REPLACE VIEW roots_checks AS
  -- A mapped slug that is not a live manufacturer: a typo, or a catalog rename
  -- that outran this campaign. Either way the root must not be emitted.
  SELECT 'manufacturer_missing' AS check_name, manufacturer_slug AS subject,
         coalesce(ipdb_prefixes, '') AS detail
  FROM _mapping m
  WHERE NOT EXISTS (SELECT 1 FROM manufacturers mf WHERE mf.slug = m.manufacturer_slug)
UNION ALL
  -- The slug is the root's identity, so two rows mapping to it would emit one
  -- root twice with divergent notes.
  SELECT 'duplicate_mapping', manufacturer_slug, count(*)::VARCHAR
  FROM _mapping GROUP BY manufacturer_slug HAVING count(*) > 1;
