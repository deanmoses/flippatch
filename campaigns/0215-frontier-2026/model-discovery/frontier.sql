-- Frontier sweep 2026 — reconcile externally-sourced candidates against the live catalog.
--
-- The candidate set does NOT come from the catalog: it is scraped from Pinside's
-- newest-first index and Kineticist's game index (both cached in the pinexplore web
-- cache, both already seeded citation roots). So the relation is a checked-in CSV
-- read here, and this file's whole job is the JOIN back to the catalog — which is
-- why it must run inside the foundation session and not in a database of its own.
--
--   make analyze FILE=../flippatch/campaigns/0215-frontier-2026/model-discovery/frontier.sql PREFIX=frontier
--
-- Re-run it after every edit to candidates.csv: the checks are what stop a stale or
-- mistyped candidate list from being emitted as a patch.
--
-- The catalog decode below is flipcommons' shared foundation, reused verbatim; cwd must
-- be the flipcommons checkout for it and the CSV's ../flippatch path to resolve.

.read scripts/analysis/catalog.sql

CREATE OR REPLACE TEMP VIEW _cand AS
SELECT
  corroboration, candidate_name, proposed_slug, maker_name, year, month, pinside_status, kind,
  nullif(franchise_slug, '')  AS franchise_slug,
  nullif(franchise_action,'') AS franchise_action,
  nullif(themes, '')            AS themes,
  nullif(inherited_themes, '')  AS inherited_themes,
  nullif(lineage_kind, '')    AS lineage_kind,
  nullif(lineage_target, '')  AS lineage_target,
  pinside_slug, note, title_slug_proposed, corporate_entity_slug,
  nullif(unreleased_lookalike_ack, '') AS unreleased_lookalike_ack,
  name_key(candidate_name)                   AS cand_key,
  name_key(name_strip_paren(candidate_name)) AS family_key,
  name_key(maker_name)                       AS maker_key
-- Dialect stated explicitly rather than sniffed: the themes column is a quoted,
-- comma-separated list, and the sniffer reads those inner commas as extra delimiters.
FROM read_csv('../flippatch/campaigns/0215-frontier-2026/model-discovery/candidates.csv', header = true,
              delim = ',', quote = '"', escape = '"',
              columns = {corroboration: 'VARCHAR', candidate_name: 'VARCHAR',
                         proposed_slug: 'VARCHAR',
                         maker_name: 'VARCHAR', year: 'INTEGER', month: 'INTEGER',
                         pinside_status: 'VARCHAR',
                         kind: 'VARCHAR', franchise_slug: 'VARCHAR',
                         franchise_action: 'VARCHAR', themes: 'VARCHAR',
                         inherited_themes: 'VARCHAR',
                         lineage_kind: 'VARCHAR', lineage_target: 'VARCHAR',
                         pinside_slug: 'VARCHAR', note: 'VARCHAR',
                         title_slug_proposed: 'VARCHAR',
                         corporate_entity_slug: 'VARCHAR',
                         unreleased_lookalike_ack: 'VARCHAR'});

-- One row per (candidate, proposed theme). Themes are authored as a comma-separated
-- list because that is what a human edits; this is the grain the vocabulary check needs.
CREATE OR REPLACE TEMP VIEW _cand_theme AS
SELECT candidate_name, trim(t.theme) AS theme_slug
FROM _cand, unnest(str_split(themes, ',')) AS t(theme)
WHERE themes IS NOT NULL AND trim(t.theme) <> '';

-- The subset of a candidate's themes carried over verbatim from an existing related
-- model. Sibling parity outranks the ancestor rule: an inherited theme is never pruned
-- for being implied, because pruning it would silently diverge the new row from the
-- rows it was copied from. Only themes derived fresh are subject to the DAG check.
CREATE OR REPLACE TEMP VIEW _cand_inherited AS
SELECT candidate_name, trim(t.theme) AS theme_slug
FROM _cand, unnest(str_split(inherited_themes, ',')) AS t(theme)
WHERE inherited_themes IS NOT NULL AND trim(t.theme) <> '';

-- Full ancestor closure of the theme DAG. theme_vocab.parents is one level, but
-- redundancy is transitive: robots -> science-fiction -> outer-space means proposing
-- robots alongside outer-space is just as redundant as proposing it alongside
-- science-fiction, and a one-level check would miss it.
CREATE OR REPLACE TEMP VIEW _theme_ancestor AS
WITH RECURSIVE anc(slug, ancestor) AS (
  SELECT v.slug, unnest(v.parents) FROM theme_vocab v WHERE len(v.parents) > 0
  UNION
  SELECT a.slug, unnest(v.parents)
  FROM anc a JOIN theme_vocab v ON v.slug = a.ancestor WHERE len(v.parents) > 0
)
SELECT * FROM anc;

-- Does the catalog know this maker at all? A missing maker is not a blocker, it is a
-- prerequisite: the corporate entity AND manufacturer (and a website root, for a URL
-- cite) have to be created in the same patch or an earlier one.
CREATE OR REPLACE TEMP VIEW _maker AS
SELECT c.candidate_name, m.id AS manufacturer_id, m.slug AS manufacturer_slug
FROM _cand c
LEFT JOIN manufacturers m ON name_key(m.name) = c.maker_key;

-- Exact hit: already in the catalog under a matching name AND maker.
--
-- Matched on name_norm, NOT name_key: name_key is name_norm(name_strip_paren(...)), so
-- it deliberately collapses an edition onto its family — which is what _family wants and
-- exactly what identity must not do. Using it here made every one of the four 2023
-- Galactic Tank Force rows an "exact" match for the Victory Edition.
CREATE OR REPLACE TEMP VIEW _exact AS
SELECT c.candidate_name,
       min(m.id)                                         AS model_id,
       string_agg(DISTINCT m.slug, ', ' ORDER BY m.slug) AS model_slug
FROM _cand c
JOIN models m ON name_norm(m.name) = name_norm(c.candidate_name)
             AND name_key(m.manufacturer_name) = c.maker_key
GROUP BY c.candidate_name;

-- Family hit: same maker, same title once a trailing parenthetical is dropped. This is
-- how an edition lands next to its siblings rather than being minted as an unrelated
-- model.
CREATE OR REPLACE TEMP VIEW _family AS
SELECT c.candidate_name, count(*) AS n_family,
       string_agg(DISTINCT m.slug, ', ' ORDER BY m.slug) AS family_slugs
FROM _cand c
JOIN models m ON name_key(name_strip_paren(m.name)) = c.family_key
             AND name_key(m.manufacturer_name) = c.maker_key
WHERE NOT EXISTS (SELECT 1 FROM _exact e WHERE e.candidate_name = c.candidate_name)
GROUP BY c.candidate_name;

-- Same-maker models that are UNRELEASED and share a significant word with the candidate.
-- This is the trap that renamed the never-built Popadiuk/Andrews Houdini "Master Mystery"
-- (IPDB 6469) into American Pinball's 2026 anniversary edition: two different machines,
-- one maker, one shared word. Similarity is a REVIEW trigger, never a merge signal, so
-- every pair must be acknowledged by slug in the CSV before the patch can emit.
CREATE OR REPLACE TEMP VIEW _lookalike AS
SELECT DISTINCT c.candidate_name, m.slug AS unreleased_slug, m.name AS unreleased_name
FROM _cand c
JOIN models m ON name_key(m.manufacturer_name) = c.maker_key
             AND m.production_status_slug = 'unreleased'
JOIN (SELECT candidate_name, unnest(str_split(name_norm(candidate_name), ' ')) AS w FROM _cand) t
  ON t.candidate_name = c.candidate_name
WHERE length(t.w) >= 4
  AND list_contains(str_split(name_norm(m.name), ' '), t.w);

-- Does a Title already exist for this machine? Every model must land in the correct
-- Title, so this resolves the family name against titles and reports the themes its
-- sibling models carry — what a new edition should be copying.
CREATE OR REPLACE TEMP VIEW _title AS
SELECT c.candidate_name, t.slug AS title_slug,
       (SELECT string_agg(DISTINCT th.theme_slug, ', ' ORDER BY th.theme_slug)
          FROM models sm JOIN model_themes th ON th.model_id = sm.id
         WHERE sm.title_id = t.id) AS sibling_themes
FROM _cand c
JOIN titles t ON name_key(t.name) = c.family_key;

CREATE OR REPLACE VIEW frontier_review AS
SELECT
  c.corroboration,
  c.candidate_name,
  c.proposed_slug,
  c.maker_name,
  c.year,
  c.month,
  -- Pinside's wording maps onto the catalog vocabulary; anything else stays NULL rather
  -- than being guessed at. A tier-3 row has no Pinside page and so no status.
  CASE c.pinside_status
    WHEN 'In production'      THEN 'produced'
    WHEN 'Production planned' THEN 'announced'
  END                                             AS proposed_production_status,
  c.kind,
  CASE
    -- kind='update' is a hand-identified rename of a row whose current name cannot
    -- match by string (Houdini "Master Mystery" -> Houdini 100th Anniversary), so it
    -- is declared in the CSV rather than resolved here, and anchored in the checks.
    WHEN c.kind = 'update'           THEN 'update_existing_row'
    WHEN e.model_id IS NOT NULL      THEN 'already_present'
    WHEN f.n_family IS NOT NULL      THEN 'new_edition_of_existing_family'
    WHEN mk.manufacturer_id IS NULL  THEN 'new_model_new_maker'
    ELSE                                  'new_model'
  END                                             AS resolution,
  mk.manufacturer_slug,
  CASE WHEN mk.manufacturer_id IS NULL THEN 'CREATE corporate entity + manufacturer' END
                                                  AS maker_action,
  coalesce(t.title_slug, c.title_slug_proposed) AS title_slug,
  EXISTS (SELECT 1 FROM titles ti
           WHERE ti.slug = coalesce(t.title_slug, c.title_slug_proposed)) AS title_exists,
  CASE WHEN t.title_slug IS NULL THEN 'CREATE title' END AS title_action,
  c.corporate_entity_slug,
  c.franchise_slug,
  c.franchise_action,
  c.themes,
  c.inherited_themes,
  t.sibling_themes,
  c.lineage_kind,
  c.lineage_target,
  e.model_slug                                    AS existing_model_slug,
  f.family_slugs,
  c.pinside_slug,
  c.note
FROM _cand c
LEFT JOIN _exact  e  ON e.candidate_name  = c.candidate_name
LEFT JOIN _family f  ON f.candidate_name  = c.candidate_name
LEFT JOIN _maker  mk ON mk.candidate_name = c.candidate_name
LEFT JOIN _title  t  ON t.candidate_name  = c.candidate_name;

CREATE OR REPLACE VIEW frontier_summary AS
SELECT resolution, count(*) AS n,
       count(*) FILTER (WHERE maker_action IS NOT NULL)     AS needs_maker,
       count(*) FILTER (WHERE title_action IS NOT NULL)     AS needs_title,
       count(*) FILTER (WHERE franchise_action = 'create')  AS needs_franchise,
       count(*) FILTER (WHERE lineage_kind IS NOT NULL)     AS has_lineage,
       count(*) FILTER (WHERE themes IS NULL)               AS themes_blank
FROM frontier_review GROUP BY resolution ORDER BY n DESC;

-- The emission surface: what a generator may read. Every candidate is in scope — kits,
-- one-offs, homebrews and prototypes are catalog machines like any other. A row whose
-- only source is Kineticist carries that as a column rather than being dropped.
CREATE OR REPLACE VIEW frontier_patch_rows AS
SELECT * FROM frontier_review ORDER BY maker_name, candidate_name;

CREATE OR REPLACE VIEW frontier_checks AS
  -- Staleness: a candidate that already exists means the sweep has been overtaken by a
  -- patch. Emitting it would duplicate a live model.
  SELECT 'already_present' AS check_name, candidate_name AS subject,
         coalesce(existing_model_slug, '') AS detail
  FROM frontier_review WHERE resolution = 'already_present'
UNION ALL
  -- Vocabulary: every proposed theme must be a real theme slug. A typo here is
  -- invisible downstream — it emits well-formed YAML naming a theme that does not exist.
  SELECT 'theme_not_in_vocab', ct.candidate_name, ct.theme_slug
  FROM _cand_theme ct
  WHERE NOT EXISTS (SELECT 1 FROM theme_vocab v WHERE v.slug = ct.theme_slug)
UNION ALL
  -- Redundant ancestor: never carry the general term when a more specific descendant is
  -- already proposed — the DAG derives it. music alongside hard-rock, sports alongside
  -- fishing, outer-space alongside science-fiction. Transitive, via the closure above.
  SELECT 'theme_redundant_ancestor', ct.candidate_name,
         ct.theme_slug || ' is implied by ' || sp.theme_slug
  FROM _cand_theme ct
  JOIN _cand_theme sp ON sp.candidate_name = ct.candidate_name
  JOIN _theme_ancestor a ON a.slug = sp.theme_slug AND a.ancestor = ct.theme_slug
  WHERE NOT EXISTS (SELECT 1 FROM _cand_inherited i
                     WHERE i.candidate_name = ct.candidate_name
                       AND i.theme_slug = ct.theme_slug)
UNION ALL
  -- A franchise declared 'existing' must actually exist...
  SELECT 'franchise_existing_missing', candidate_name, franchise_slug
  FROM frontier_review
  WHERE franchise_action = 'existing'
    AND NOT EXISTS (SELECT 1 FROM franchises f WHERE f.slug = frontier_review.franchise_slug)
UNION ALL
  -- ...and one declared 'create' must not, or the patch would collide with a live row.
  SELECT 'franchise_create_already_exists', candidate_name, franchise_slug
  FROM frontier_review
  WHERE franchise_action = 'create'
    AND EXISTS (SELECT 1 FROM franchises f WHERE f.slug = frontier_review.franchise_slug)
UNION ALL
  -- Every franchise row must declare which it is.
  SELECT 'franchise_action_invalid', candidate_name, coalesce(franchise_action, '<null>')
  FROM frontier_review
  WHERE franchise_action IS NULL OR franchise_action NOT IN ('existing', 'create', 'none')
UNION ALL
  SELECT 'franchise_slug_without_action', candidate_name, coalesce(franchise_slug, '')
  FROM frontier_review
  WHERE (franchise_slug IS NULL) <> (franchise_action = 'none')
UNION ALL
  -- A lineage target must resolve to something real — a Title or a model. 'unresolved'
  -- is a deliberate parking value: it names the suspected target while recording that
  -- the relationship is NOT yet established, and must never be emitted as a claim.
  SELECT 'lineage_target_unresolved', candidate_name, coalesce(lineage_target, '<null>')
  FROM frontier_review
  WHERE lineage_kind IS NOT NULL AND lineage_kind <> 'unresolved'
    AND NOT EXISTS (SELECT 1 FROM titles t WHERE t.slug = frontier_review.lineage_target)
    AND NOT EXISTS (SELECT 1 FROM models m WHERE m.slug = frontier_review.lineage_target)
UNION ALL
  SELECT 'lineage_kind_invalid', candidate_name, lineage_kind
  FROM frontier_review
  WHERE lineage_kind IS NOT NULL
    AND lineage_kind NOT IN ('remake_of', 'variant_of', 'kit_of', 'unresolved')
UNION ALL
  -- The Houdini row is an UPDATE, not a create. Its target is identified by hand (the
  -- names don't match), so anchor on the target still being there and still unreleased:
  -- if a patch has already renamed it, this candidate must be re-read before use.
  SELECT 'houdini_update_target_missing', 'Houdini 100th Anniversary',
         'no unreleased American Pinball Houdini row'
  WHERE NOT EXISTS (
    SELECT 1 FROM models
    WHERE name_key(manufacturer_name) = name_key('American Pinball')
      AND lower(name) LIKE '%houdini%' AND production_status_slug = 'unreleased')
UNION ALL
  -- A candidate declared a variant must actually find its family, else the edition
  -- would be minted as a standalone model.
  SELECT 'variant_without_family', candidate_name, maker_name
  FROM frontier_review WHERE kind = 'variant' AND family_slugs IS NULL
UNION ALL
  -- Anchor: the GTF family is what 'variant' resolves against. If it goes dark the
  -- variant check above silently stops meaning anything.
  SELECT 'gtf_family_dark', 'Galactic Tank Force', 'no American Pinball GTF rows'
  WHERE NOT EXISTS (
    SELECT 1 FROM models
    WHERE name_key(manufacturer_name) = name_key('American Pinball')
      AND lower(name) LIKE 'galactic tank force%')
UNION ALL
  -- A proposed slug must BE a slug: lowercase alphanumerics and single hyphens.
  SELECT 'slug_not_slug_safe', candidate_name, coalesce(proposed_slug, '<null>')
  FROM frontier_review
  WHERE proposed_slug IS NULL
     OR NOT regexp_matches(proposed_slug, '^[a-z0-9]+(-[a-z0-9]+)*$')
UNION ALL
  -- ...and must be free. Includes the update row: renaming houdini-master-mystery to
  -- houdini-100th-anniversary must not land on a slug some other live model holds.
  SELECT 'slug_taken', candidate_name, proposed_slug
  FROM frontier_review
  WHERE EXISTS (SELECT 1 FROM models m WHERE m.slug = frontier_review.proposed_slug)
UNION ALL
  -- Two candidates must never propose the same slug.
  SELECT 'slug_collision', min(candidate_name), proposed_slug
  FROM frontier_review WHERE proposed_slug IS NOT NULL
  GROUP BY proposed_slug HAVING count(*) > 1
UNION ALL
  -- An inherited theme must be one the row actually proposes, else the exemption is
  -- silently shielding a theme that is not there.
  SELECT 'inherited_theme_not_proposed', i.candidate_name, i.theme_slug
  FROM _cand_inherited i
  WHERE NOT EXISTS (SELECT 1 FROM _cand_theme ct
                     WHERE ct.candidate_name = i.candidate_name AND ct.theme_slug = i.theme_slug)
UNION ALL
  SELECT 'corroboration_invalid', candidate_name, coalesce(corroboration, '<null>')
  FROM frontier_review WHERE corroboration NOT IN ('both', 'kineticist');
