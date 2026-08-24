-- OPDB against the catalog: which listings and groups we hold, and where the two disagree.
--
-- `.read` this from a campaign analysis after flipcommons' foundation:
--
--     .read ../flippatch/scripts/analysis/external_data_sources/opdb.sql
--
-- It reads `bridge.sql` itself, so the attach, the watermark and the bridge's own
-- invariants come with it. Read that file first for the scope and the findings/checks
-- rule; the worklists below return rows on a healthy catalog.
--
-- WHAT OPDB IS TO US, which shapes every rule here. The catalog's models and titles were
-- seeded from OPDB, so its ids are our densest external key: models join `opdb_id` at
-- machine-or-alias grain, titles join `opdb_id` at group grain, and THOSE ARE DIFFERENT
-- NAMESPACES -- a group id on a model matches nothing and reads as absence. OPDB also
-- publishes its own id changelog, which IPDB does not: an id that stops resolving is
-- usually explained (moved, with a successor; or deleted) rather than an unexplained hole.
-- What OPDB lacks is IPDB's depth -- no credits, no corporate entities (makers only at
-- brand grain), no free-text provenance -- so the maker comparison here is a sanity check
-- where IPDB's is a seeding-key audit, and there is no credits section at all.
--
-- THEMES ARE DELIBERATELY NOT COMPARED. `px.opdb.model_themes` exists, but its values are
-- OPDB's coarse keywords (movie, tv, music) and the catalog's theme system is richer and
-- has been re-curated since seeding; comparing would restate the IPDB-themes decision the
-- plan already made. The bucket stays published in pinexplore for ad-hoc looks.

.read ../flippatch/scripts/analysis/external_data_sources/bridge.sql

-- One row per OPDB model -- machine or alias, containers already excluded by the mart --
-- as OPDB states it, decoded into catalog terms.
--
-- Reads pinexplore's MART only; the staging and reference layers under it are that
-- repo's working material. The mart already speaks catalog language where the vocabulary
-- is small and closed (`technology_generation`, `display_type`, `cabinet`, the tag and
-- reward-type views), and stays in OPDB's wording where the catalog resolves through
-- aliases (gameplay features) -- `OpdbMappings.md` in pinexplore is the authority.
--
-- The decode joins on `opdb_manufacturer_id`, the catalog's handle on an OPDB maker.
-- OPDB models MANUFACTURERS, not corporate entities -- brand-grain trade names like
-- `Bally` -- so the slug lands on `manufacturers`, not `corporate_entities`, and every
-- maker comparison below is at that coarser grain. The join cannot multiply the grain:
-- the id is unique across manufacturers, asserted in `opdb_checks`.
CREATE OR REPLACE VIEW _eds_opdb_dump AS
  SELECT
    om.opdb_id,
    om.name                                    AS opdb_name,
    om.production_year                         AS opdb_year,
    om.opdb_manufacturer_id,
    om.manufacturer_name                       AS opdb_manufacturer_name,
    -- 'machine' rather than NULL, so the column reads as a classification instead of as
    -- an absence: NULL here means "not a variant of anything", which IS a statement.
    coalesce(om.variant_parent_relation, 'machine') AS opdb_relation,
    om.variant_of                              AS opdb_variant_of,
    om.title_opdb_id,
    om.ipdb_id                                 AS opdb_ipdb_id,
    om.player_count                            AS opdb_player_count,
    om.technology_generation                   AS opdb_technology_generation,
    om.display_type                            AS opdb_display_type,
    om.cabinet                                 AS opdb_cabinet,
    manufacturer.slug                          AS opdb_manufacturer_slug
  FROM px.opdb.models AS om
  LEFT JOIN manufacturers AS manufacturer
    ON manufacturer.opdb_manufacturer_id = om.opdb_manufacturer_id;

-- Catalog models that answer to an unmatched listing's name and maker, counted by
-- whether they already carry an OPDB id.
--
-- Matched on `name_norm`, not `name_key`: `name_key` strips a trailing parenthetical,
-- and on OPDB the parenthetical IS the identity -- the unmatched set is full of
-- "(Pro)" / "(Premium)" / "(LE)" edition rows whose base machine the catalog holds.
--
-- Aggregated rather than joined through, because a name and maker can answer to more
-- than one model and joining would emit the listing once per candidate.
CREATE OR REPLACE VIEW _eds_opdb_candidates AS
  WITH unmatched AS (
    SELECT * FROM _eds_opdb_dump AS d
    WHERE NOT EXISTS (SELECT 1 FROM models AS m WHERE m.opdb_id = d.opdb_id)
  )
  SELECT
    u.opdb_id,
    count(*) FILTER (WHERE m.opdb_id IS NULL)                 AS n_unlinked_candidates,
    count(*) FILTER (WHERE m.opdb_id IS NOT NULL)             AS n_linked_candidates,
    any_value(m.slug)    FILTER (WHERE m.opdb_id IS NULL)     AS unlinked_model_slug,
    any_value(m.slug)    FILTER (WHERE m.opdb_id IS NOT NULL) AS linked_model_slug,
    any_value(m.opdb_id) FILTER (WHERE m.opdb_id IS NOT NULL) AS linked_model_opdb_id,
    any_value(m.year)    FILTER (WHERE m.opdb_id IS NOT NULL) AS linked_model_year
  FROM unmatched AS u
  INNER JOIN models AS m
    ON name_norm(m.name) = name_norm(u.opdb_name)
   AND m.manufacturer_slug = u.opdb_manufacturer_slug
  GROUP BY u.opdb_id;

-- Catalog models answering to an unmatched listing's NAME, whatever their maker.
-- The evidence for the rows the candidate search could not run on -- see the IPDB twin
-- of this view for why a namesake is not a candidate.
CREATE OR REPLACE VIEW _eds_opdb_namesakes AS
  SELECT
    d.opdb_id,
    count(*)                    AS n_namesake_models,
    list_sort(list(m.slug))[:5] AS namesake_model_slugs
  FROM _eds_opdb_dump AS d
  INNER JOIN models AS m ON name_norm(m.name) = name_norm(d.opdb_name)
  WHERE NOT EXISTS (SELECT 1 FROM models AS x WHERE x.opdb_id = d.opdb_id)
  GROUP BY d.opdb_id;

-- WORKLIST — OPDB listings with no catalog model, and what each one actually is.
--
-- The classification is the IPDB one, minus `duplicate_listing` (OPDB records its own
-- duplicates as moved ids, which land in `opdb_ids_stale` instead):
--
--   catalog_holds_unlinked  The catalog has the machine and no OPDB id on it. A
--                           backfill: patch the id, do not create a record.
--   possible_duplicate      A catalog model of the same name and maker is already
--                           linked to a DIFFERENT OPDB id. Read both OPDB pages.
--   maker_unresolved        No candidate search was possible: the listing has no maker
--                           to match on. NOT a statement that the catalog lacks the
--                           machine -- read `n_namesake_models` and the OPDB page.
--   absent                  A search ran on name and maker and found nothing. A
--                           candidate new record.
--
-- Two columns qualify what an `absent` row would take to create, because OPDB's alias
-- rows are full Models to us (see `OpdbMappings.md`): `opdb_relation` says whether this
-- is a standalone machine or an edition of something, and where it is an edition,
-- `parent_model_slug` is the catalog model to hang `variant_of` on -- filled only when
-- OPDB itself is sure of the parent (its `variant_of` is NULL under a virtual
-- container). `linked_title_slug` is the catalog title already carrying the listing's
-- group, which is where the new model files.
CREATE OR REPLACE VIEW opdb_models_unmatched AS
  SELECT
    d.opdb_id,
    d.opdb_name,
    d.opdb_year,
    d.opdb_manufacturer_name,
    d.opdb_manufacturer_slug,
    d.opdb_relation,
    CASE
      WHEN c.n_unlinked_candidates > 0        THEN 'catalog_holds_unlinked'
      WHEN c.n_linked_candidates > 0          THEN 'possible_duplicate'
      WHEN d.opdb_manufacturer_slug IS NULL   THEN 'maker_unresolved'
      ELSE                                         'absent'
    END                                  AS classification,
    parent.slug                          AS parent_model_slug,
    linked_title.slug                    AS linked_title_slug,
    c.unlinked_model_slug,
    c.linked_model_slug,
    c.linked_model_opdb_id,
    c.linked_model_year,
    coalesce(c.n_unlinked_candidates, 0) AS n_unlinked_candidates,
    coalesce(c.n_linked_candidates, 0)   AS n_linked_candidates,
    coalesce(n.n_namesake_models, 0)     AS n_namesake_models,
    n.namesake_model_slugs
  FROM _eds_opdb_dump AS d
  LEFT JOIN _eds_opdb_candidates AS c USING (opdb_id)
  LEFT JOIN _eds_opdb_namesakes  AS n USING (opdb_id)
  LEFT JOIN models AS parent       ON parent.opdb_id = d.opdb_variant_of
  LEFT JOIN titles AS linked_title ON linked_title.opdb_id = d.title_opdb_id
  WHERE NOT EXISTS (SELECT 1 FROM models AS m WHERE m.opdb_id = d.opdb_id);
COMMENT ON VIEW opdb_models_unmatched IS
  'Worklist — one row per OPDB listing no live model carries the id of, classified catalog_holds_unlinked / possible_duplicate / maker_unresolved / absent, with the machine-or-edition relation, the catalog parent and title where OPDB names them, and candidate or namesake evidence. Rows are expected.';

-- WORKLIST — the other direction: a model carries an OPDB id the dump no longer serves.
--
-- OPDB explains most of its own absences, which IPDB cannot: `px.opdb.model_ids` holds
-- every id ever issued with where it is now. So an id that stops resolving classifies
-- itself:
--
--   moved        OPDB re-issued the id; `current_opdb_id` is the successor. The catalog
--                is citing a superseded id -- repoint it. `current_id_model_slug` is
--                filled when ANOTHER model already links the successor, which turns a
--                repoint into a possible merge and is worth knowing before patching.
--   deleted      OPDB withdrew the record. The catalog is citing a dead id; decide
--                whether the machine keeps a record without one.
--   container    The id resolves, but to one of OPDB's non-physical group containers --
--                a thing the catalog deliberately has no record kind for. A Model citing
--                one is mislinked.
--   unexplained  Absent from the changelog entirely: either a parse gap or an id that
--                never existed. The one class the dump cannot settle.
CREATE OR REPLACE VIEW opdb_ids_stale AS
  SELECT
    m.slug                  AS model_slug,
    m.name                  AS model_name,
    m.opdb_id,
    m.year,
    m.manufacturer_slug,
    CASE
      WHEN i.status = 'moved'                    THEN 'moved'
      WHEN i.status = 'deleted'                  THEN 'deleted'
      WHEN i.status = 'current' AND NOT i.is_model THEN 'container'
      ELSE                                            'unexplained'
    END                     AS classification,
    i.current_opdb_id,
    successor.slug          AS current_id_model_slug,
    i.retired_at
  FROM models AS m
  LEFT JOIN px.opdb.model_ids AS i ON i.opdb_id = m.opdb_id
  LEFT JOIN models AS successor    ON successor.opdb_id = i.current_opdb_id
  WHERE m.opdb_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM px.opdb.models AS om WHERE om.opdb_id = m.opdb_id);
COMMENT ON VIEW opdb_ids_stale IS
  'Worklist — one row per live model whose opdb_id is absent from the published dump, classified moved / deleted / container / unexplained via OPDB''s own id changelog, with the successor id and any model already linking it. Rows are expected.';

-- WORKLIST — OPDB machine groups with no catalog title, name-matched for candidates.
--
-- Group ids are their own namespace (`titles.opdb_id`, never `models.opdb_id`), and a
-- group has no maker, so the candidate search is name-only -- weaker than the model
-- search above, which the counts qualify. A group usually goes unmatched for the same
-- reason its machines do: a release newer than the catalog's last OPDB acquisition.
CREATE OR REPLACE VIEW opdb_titles_unmatched AS
  SELECT
    ot.opdb_id,
    ot.name        AS opdb_title_name,
    ot.year        AS opdb_year,
    ot.n_models    AS n_opdb_models,
    CASE
      WHEN c.n_unlinked_candidates > 0 THEN 'catalog_holds_unlinked'
      WHEN c.n_linked_candidates > 0   THEN 'possible_duplicate'
      ELSE                                  'absent'
    END            AS classification,
    c.unlinked_title_slug,
    c.linked_title_slug,
    c.linked_title_opdb_id,
    coalesce(c.n_unlinked_candidates, 0) AS n_unlinked_candidates,
    coalesce(c.n_linked_candidates, 0)   AS n_linked_candidates
  FROM px.opdb.titles AS ot
  LEFT JOIN (
    SELECT
      ot2.opdb_id,
      count(*) FILTER (WHERE t.opdb_id IS NULL)                 AS n_unlinked_candidates,
      count(*) FILTER (WHERE t.opdb_id IS NOT NULL)             AS n_linked_candidates,
      any_value(t.slug)    FILTER (WHERE t.opdb_id IS NULL)     AS unlinked_title_slug,
      any_value(t.slug)    FILTER (WHERE t.opdb_id IS NOT NULL) AS linked_title_slug,
      any_value(t.opdb_id) FILTER (WHERE t.opdb_id IS NOT NULL) AS linked_title_opdb_id
    FROM px.opdb.titles AS ot2
    INNER JOIN titles AS t ON name_norm(t.name) = name_norm(ot2.name)
    WHERE NOT EXISTS (SELECT 1 FROM titles AS x WHERE x.opdb_id = ot2.opdb_id)
    GROUP BY ot2.opdb_id
  ) AS c USING (opdb_id)
  WHERE NOT EXISTS (SELECT 1 FROM titles AS t WHERE t.opdb_id = ot.opdb_id);
COMMENT ON VIEW opdb_titles_unmatched IS
  'Worklist — one row per OPDB machine group no live title carries the id of, classified catalog_holds_unlinked / possible_duplicate / absent on a name-only search. Rows are expected.';

-- WORKLIST — a title citing a group id the dump no longer serves.
--
-- Thinner than the model twin because the changelog is machine-grain only: a vanished
-- group id has no moved/deleted verdict to inherit, so every row is unexplained until
-- someone reads OPDB. In practice these travel with `opdb_ids_stale`'s moved rows --
-- when OPDB merges machines into a new group, the old group dies with them.
CREATE OR REPLACE VIEW opdb_title_ids_stale AS
  SELECT
    t.slug    AS title_slug,
    t.name    AS title_name,
    t.opdb_id,
    t.n_models
  FROM titles AS t
  WHERE t.opdb_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM px.opdb.titles AS ot WHERE ot.opdb_id = t.opdb_id);
COMMENT ON VIEW opdb_title_ids_stale IS
  'Worklist — one row per live title whose group opdb_id is absent from the dump. The id changelog is machine-grain, so these carry no verdict; read OPDB. Rows are expected.';

-- Maker pairings adjudicated as permanent, researched disagreements -- OPDB filing a
-- game under a parent or successor company where the catalog names the brand on the
-- machine. Inherited verbatim from pinexplore's deleted `opdb_ref.manufacturer_exceptions`
-- (recoverable there via `git log -S opdb_ref.manufacturer_exceptions -p`), which is
-- also where the research behind each row lives; one slug updated: the row written as
-- `mecatronics-aka-taito-brazil-a-division-of-taito` had already rotted against the
-- catalog's rename to `mecatronics`, exactly the failure the `exception_slug_unresolved`
-- check below now makes loud.
--
-- An exception is keyed on the PAIR -- this OPDB maker id against this catalog
-- manufacturer -- so it clears every model filed that way at once, which is why these
-- are not dismissals: a dismissal adjudicates one finding, and these adjudicate a
-- filing policy that surfaces on dozens.
CREATE OR REPLACE VIEW _eds_opdb_manufacturer_exceptions AS
  SELECT * FROM (VALUES
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
  ) AS t(opdb_manufacturer_id, manufacturer_slug, reason);

-- WORKLIST — models where OPDB's maker and the catalog's do not line up.
--
-- Manufacturer grain on BOTH sides -- OPDB has no corporate entities -- so this is the
-- sanity check `OpdbMappings.md` calls it, not the seeding-key audit the IPDB twin is.
-- That grain also sets the severity floor: OPDB routinely files a game under a parent
-- or successor company (the exceptions view above is thirteen researched cases of
-- exactly that), so a disagreement here defaults to "OPDB is coarser", not "the catalog
-- is wrong", and nothing in this view reaches `error`.
--
--   excepted            An adjudicated pairing; `exception_reason` carries the why.
--                       Kept visible here, excluded from findings.
--   catalog_has_none    The model carries no manufacturer at all; OPDB names one.
--   opdb_unmatched      OPDB's maker id is on no catalog manufacturer, so nothing was
--                       compared. Resolve at the manufacturer, in
--                       `opdb_manufacturers_unmatched` -- one row per company there
--                       rather than one per machine filed under it.
--   disagrees           Both resolve and differ, and nobody has adjudicated the pair.
CREATE OR REPLACE VIEW opdb_model_manufacturer_mismatched AS
  SELECT
    d.opdb_id,
    d.opdb_name,
    m.slug                     AS model_slug,
    CASE
      WHEN ex.reason IS NOT NULL              THEN 'excepted'
      WHEN m.manufacturer_slug IS NULL        THEN 'catalog_has_none'
      WHEN d.opdb_manufacturer_slug IS NULL   THEN 'opdb_unmatched'
      ELSE                                         'disagrees'
    END                        AS classification,
    m.manufacturer_slug,
    d.opdb_manufacturer_slug,
    d.opdb_manufacturer_name,
    d.opdb_manufacturer_id,
    ex.reason                  AS exception_reason
  FROM _eds_opdb_dump AS d
  INNER JOIN models AS m ON m.opdb_id = d.opdb_id
  LEFT JOIN _eds_opdb_manufacturer_exceptions AS ex
    ON  ex.opdb_manufacturer_id = d.opdb_manufacturer_id
    AND ex.manufacturer_slug    = m.manufacturer_slug
  WHERE d.opdb_manufacturer_id IS NOT NULL
    AND m.manufacturer_slug IS DISTINCT FROM d.opdb_manufacturer_slug;
COMMENT ON VIEW opdb_model_manufacturer_mismatched IS
  'Worklist — one row per model whose manufacturer differs from the one OPDB names, classified excepted / catalog_has_none / opdb_unmatched / disagrees, with the adjudication reason on excepted rows. Rows are expected.';

-- The exceptions, browsable, with `is_stale` marking a pairing no model exercises any
-- more -- OPDB refiled the game or the catalog moved; prune when convenient.
CREATE OR REPLACE VIEW opdb_manufacturer_exceptions AS
  SELECT ex.*,
         NOT EXISTS (SELECT 1 FROM opdb_model_manufacturer_mismatched AS w
                     WHERE w.classification = 'excepted'
                       AND w.opdb_manufacturer_id = ex.opdb_manufacturer_id
                       AND w.manufacturer_slug = ex.manufacturer_slug) AS is_stale
  FROM _eds_opdb_manufacturer_exceptions AS ex;
COMMENT ON VIEW opdb_manufacturer_exceptions IS
  'Every adjudicated maker pairing with its reason and is_stale flag. Stale means no model pair exercises it any more; prune when convenient.';

-- DECISION GRAIN, which is the whole point: the disagreements arrive in filing-policy
-- clumps (28 of the first 30 were one Taito pair), and the adjudication -- fine, so
-- except it; or wrong, so patch the models -- happens once per pair. The model-grain
-- rows stay above as the patch material. IPDB's twin stays per-model deliberately:
-- there a disagreement is a seeding-key anomaly, individually suspicious.
CREATE OR REPLACE VIEW opdb_manufacturer_pairs_disagreeing AS
  SELECT
    manufacturer_slug,
    opdb_manufacturer_slug,
    opdb_manufacturer_id,
    count(*)                                    AS n_models,
    -- Ordered: this reaches a finding message, whose identity depends on it rendering
    -- the same way every run.
    list_sort(list(DISTINCT model_slug))[:5]    AS sample_model_slugs
  FROM opdb_model_manufacturer_mismatched
  WHERE classification = 'disagrees'
  GROUP BY ALL;
COMMENT ON VIEW opdb_manufacturer_pairs_disagreeing IS
  'Worklist — one row per unadjudicated (catalog manufacturer, OPDB manufacturer) pairing that disagrees, with how many models file that way. One row is one adjudication.';

-- WORKLIST — an OPDB manufacturer the catalog has no handle on.
--
-- Grouped by id because pinexplore's `opdb.manufacturers` warns that one id can carry
-- conflicting names upstream; the list shows every spelling seen.
CREATE OR REPLACE VIEW opdb_manufacturers_unmatched AS
  SELECT
    pm.opdb_manufacturer_id,
    list_sort(list(DISTINCT pm.name))       AS opdb_names,
    (SELECT count(*) FROM _eds_opdb_dump AS d
      WHERE d.opdb_manufacturer_id = pm.opdb_manufacturer_id) AS n_opdb_models,
    (SELECT list_sort(list(DISTINCT e.public_id)) FROM entity_names AS e
      WHERE e.entity_type = 'manufacturer'
        AND name_norm(e.name) IN (SELECT name_norm(x.name) FROM px.opdb.manufacturers AS x
                                  WHERE x.opdb_manufacturer_id = pm.opdb_manufacturer_id))
                                            AS catalog_name_matches
  FROM px.opdb.manufacturers AS pm
  WHERE NOT EXISTS (
    SELECT 1 FROM manufacturers AS f
    WHERE f.opdb_manufacturer_id = pm.opdb_manufacturer_id
  )
  GROUP BY pm.opdb_manufacturer_id;
COMMENT ON VIEW opdb_manufacturers_unmatched IS
  'Worklist — one row per OPDB manufacturer id no live manufacturer carries, with every upstream spelling, how many OPDB models depend on it, and any catalog manufacturer answering to the same name.';

-- WORKLIST — a manufacturer we hold that OPDB now has a record for.
--
-- Name matching is the only route: with no id on our side there is nothing to join on.
CREATE OR REPLACE VIEW manufacturers_missing_opdb_id AS
  SELECT
    f.slug          AS manufacturer_slug,
    f.name          AS manufacturer_name,
    f.n_models,
    i.n_opdb_matches,
    i.opdb_manufacturer_id,
    i.opdb_name
  FROM manufacturers AS f
  INNER JOIN (
    SELECT
      name_norm(name)              AS name_key,
      count(DISTINCT opdb_manufacturer_id) AS n_opdb_matches,
      min(opdb_manufacturer_id)    AS opdb_manufacturer_id,
      any_value(name)              AS opdb_name
    FROM px.opdb.manufacturers
    GROUP BY 1
  ) AS i ON i.name_key = name_norm(f.name)
  WHERE f.opdb_manufacturer_id IS NULL;
COMMENT ON VIEW manufacturers_missing_opdb_id IS
  'Worklist — one row per live manufacturer with no OPDB id that OPDB now appears to hold a record for, matched by name. Empty when there is nothing to acquire.';

-- WORKLIST — OPDB's cross-reference into IPDB, checked against ours.
--
-- OPDB carries an `ipdb_id` on many machines, which makes it a second witness on a link
-- the catalog already asserts -- the one comparison here where both sides claim the
-- same fact and a difference means somebody is simply wrong.
--
--   disagrees   Both sides name an IPDB id and they differ. One of the three records
--               (our model, our ipdb_id, or OPDB's cross-reference) is mislinked.
--   acquirable  We have no ipdb_id; OPDB names one. `ipdb_id_in_ipdb_dump` says whether
--               that id resolves in the merged IPDB dump -- backfilling a dead id would
--               only feed `ipdb_ids_not_in_dump`.
CREATE OR REPLACE VIEW opdb_ipdb_id_crosscheck AS
  SELECT
    d.opdb_id,
    m.slug          AS model_slug,
    CASE WHEN m.ipdb_id IS NULL THEN 'acquirable' ELSE 'disagrees' END AS classification,
    m.ipdb_id,
    d.opdb_ipdb_id,
    EXISTS (SELECT 1 FROM px.ipdb.models AS im
            WHERE im.ipdb_id = d.opdb_ipdb_id) AS ipdb_id_in_ipdb_dump
  FROM _eds_opdb_dump AS d
  INNER JOIN models AS m ON m.opdb_id = d.opdb_id
  WHERE d.opdb_ipdb_id IS NOT NULL
    AND m.ipdb_id IS DISTINCT FROM d.opdb_ipdb_id;
COMMENT ON VIEW opdb_ipdb_id_crosscheck IS
  'Worklist — one row per model where OPDB''s ipdb_id cross-reference and the catalog''s ipdb_id differ or ours is missing, with whether OPDB''s id resolves in the IPDB dump. Rows are expected.';

-- WORKLIST — single-valued fields where both sides state a value and the values differ.
--
-- Both-set only, deliberately: a probe found ZERO models linked to OPDB with a NULL
-- year, player count, technology generation or display type, so a backfill class would
-- be dead code today -- and if the catalog ever grows such a gap, `absent` rows in the
-- unmatched worklist are where new-model data arrives, not here.
--
-- Names are deliberately NOT compared: 135 models differ under `name_norm` and nearly
-- all of it is styling convention (subtitle punctuation, edition spelling), a worklist
-- with no action. The unmatched views compare names where a name is all there is.
--
-- One row per (model, field) rather than the old wide `compare_models_opdb` shape,
-- because a finding needs one disagreement, not five booleans.
CREATE OR REPLACE VIEW opdb_model_fields_disagreeing AS
  WITH j AS (
    SELECT m.slug AS model_slug, d.opdb_id, v.*
    FROM _eds_opdb_dump AS d
    INNER JOIN models AS m ON m.opdb_id = d.opdb_id,
    LATERAL (VALUES
      ('year',                  m.year::VARCHAR,                  d.opdb_year::VARCHAR),
      ('player_count',          m.player_count::VARCHAR,          d.opdb_player_count::VARCHAR),
      ('technology_generation', m.technology_generation_slug,     d.opdb_technology_generation),
      ('display_type',          m.display_type_slug,              d.opdb_display_type)
    ) AS v(field, catalog_value, opdb_value)
  )
  SELECT model_slug, opdb_id, field, catalog_value, opdb_value
  FROM j
  WHERE catalog_value IS NOT NULL
    AND opdb_value IS NOT NULL
    AND catalog_value <> opdb_value;
COMMENT ON VIEW opdb_model_fields_disagreeing IS
  'Worklist — one row per (model, field) where the catalog and OPDB both state a single-valued fact and the values differ: year, player_count, technology_generation, display_type. Rows are expected.';

-- ═══ VOCABULARY ════════════════════════════════════════════════════════════
--
-- OPDB's classification signals -- tags, reward types, gameplay features, the cabinet
-- scalar, relationship edges, series -- checked for carriage on the catalog model, the
-- same two questions the IPDB specialties section asks: does the target vocabulary
-- EXIST, and does the model CARRY it.
--
-- The values arrive under the division of labour `OpdbMappings.md` sets: small closed
-- vocabularies pre-translated to catalog slugs, alias-bearing ones (gameplay features)
-- in OPDB's own wording for this side to resolve. EVERY value is slugified either way,
-- so a slug-shaped value that does not resolve is NOT the contract violation it is for
-- IPDB -- `pro-edition` is slug-shaped and known-absent by design. There is no
-- spelling-scoped resolution gate here; an unresolved value is a decision waiting in
-- `opdb_vocabulary_absent`, and when a decision maps one (`payout-machine` ==
-- `cash-payout`), the mapping goes back INTO pinexplore rather than living here.

-- One row per (OPDB model, asserted value), landed on the catalog model.
--
-- The per-entity mart views union into one shape so the resolution lookup and the
-- carriage CASE are written once. `model-relationship` targets name an edge type
-- rather than a record, so they resolve structurally -- same exemption as IPDB's.
CREATE OR REPLACE VIEW _eds_opdb_vocabulary AS
  SELECT
    r.opdb_id,
    r.target_entity_type,
    r.target_value,
    r.target_slug,
    r.model_id,
    r.model_slug,
    CASE WHEN r.target_entity_type = 'model-relationship' THEN true
         ELSE r.target_slug IS NOT NULL END AS target_exists,
    CASE r.target_entity_type
      WHEN 'tag'              THEN EXISTS (SELECT 1 FROM model_tags AS tg
                                     WHERE tg.model_id = r.model_id AND tg.tag_slug = r.target_slug)
      WHEN 'reward-type'      THEN EXISTS (SELECT 1 FROM model_rewards AS rw
                                     WHERE rw.model_id = r.model_id AND rw.reward_type_slug = r.target_slug)
      WHEN 'gameplay-feature' THEN EXISTS (SELECT 1 FROM model_gameplay_features AS g
                                     WHERE g.model_id = r.model_id AND g.feature_slug = r.target_slug)
      -- Single-valued dims: `target_slug IS NOT NULL` guards the IS NOT DISTINCT FROM,
      -- for the reason spelled out on the IPDB twin -- unguarded, a model with no
      -- cabinet at all would read as carrying every unresolved cabinet value.
      WHEN 'cabinet'          THEN r.target_slug IS NOT NULL
                                     AND m_cabinet_slug IS NOT DISTINCT FROM r.target_slug
      -- Series hangs off the TITLE in the catalog (`OpdbMappings.md` leaves the view at
      -- OPDB's model grain for exactly this reason), so carriage is asked of the
      -- model's title.
      WHEN 'series'           THEN r.target_slug IS NOT NULL
                                     AND m_series_slug IS NOT DISTINCT FROM r.target_slug
      -- Structural: an edge type is not a record and never resolves through target_slug.
      WHEN 'model-relationship' THEN EXISTS (SELECT 1 FROM model_edges AS e
                                     WHERE e.model_id = r.model_id
                                       AND e.relationship_type = r.target_value)
      -- No ELSE: an unhandled target_entity_type lands NULL, which
      -- `vocabulary_carriage_unhandled` fails on -- loud rather than wrong.
    END AS carried
  FROM (
    SELECT
      s.*,
      m.id   AS model_id,
      m.slug AS model_slug,
      m.cabinet_slug AS m_cabinet_slug,
      t.series_slug  AS m_series_slug,
      -- THE CATALOG RECORD THE VALUE DENOTES, or NULL if none does: exact public_id
      -- first, then name, then alias -- the same three-way lookup, with the same
      -- determinism rule, as the IPDB specialties section.
      (SELECT es.subject_public_id
       FROM entity_subjects AS es
       WHERE es.subject_type = s.target_entity_type
         AND is_live(es.subject_status)
         AND (es.subject_public_id = s.target_value
              OR lower(es.subject_name) = lower(s.target_value)
              OR EXISTS (SELECT 1 FROM entity_aliases AS ea
                         WHERE ea.entity_type = es.subject_type
                           AND ea.entity_id = es.subject_id
                           AND lower(ea.alias) = lower(s.target_value)))
       ORDER BY CASE WHEN es.subject_public_id = s.target_value THEN 0
                     WHEN lower(es.subject_name) = lower(s.target_value) THEN 1
                     ELSE 2 END,
                es.subject_public_id
       LIMIT 1) AS target_slug
    FROM (
                SELECT opdb_id, 'tag'              AS target_entity_type, tag              AS target_value FROM px.opdb.model_tags
      UNION ALL SELECT opdb_id, 'reward-type',                            reward_type                      FROM px.opdb.model_reward_types
      UNION ALL SELECT opdb_id, 'gameplay-feature',                       gameplay_feature                 FROM px.opdb.model_gameplay_features
      UNION ALL SELECT opdb_id, 'series',                                 series                           FROM px.opdb.model_series
      UNION ALL SELECT opdb_id, 'model-relationship',                     relationship_type                FROM px.opdb.model_relationships
      UNION ALL SELECT opdb_id, 'cabinet',                                cabinet                          FROM px.opdb.models WHERE cabinet IS NOT NULL
    ) AS s
    LEFT JOIN models AS m ON m.opdb_id = s.opdb_id
    LEFT JOIN titles AS t ON t.id = m.title_id
  ) AS r;

-- WORKLIST — OPDB asserts a classification the catalog has the vocabulary for and the
-- model does not carry. Each row is a patch waiting to be written.
--
-- Listings with no catalog model are excluded rather than reported: that is already a
-- finding under `opdb-model-*`, and one defect gets one name.
CREATE OR REPLACE VIEW opdb_model_vocabulary_missing AS
  SELECT
    opdb_id,
    model_slug,
    target_entity_type,
    target_value,
    target_slug
  FROM _eds_opdb_vocabulary
  WHERE model_slug IS NOT NULL
    AND target_exists
    AND NOT carried;
COMMENT ON VIEW opdb_model_vocabulary_missing IS
  'Worklist — one row per OPDB-asserted value the catalog has vocabulary for but the model (or its title, for series) does not carry. Rows are expected.';

-- Absent-vocabulary values adjudicated as PERMANENTLY not ours to mint. A settled value
-- leaves the worklist below but stays browsable here with its reason; `is_stale` marks
-- one no absent value exercises any more -- the vocabulary was created after all, or the
-- value left the dump -- and stale is reported, never gated.
--
-- NOT dismissals, deliberately: a dismissal keys on the message, whose count lapses it
-- whenever another model gains the value, and "we will never mint this" is a decision
-- about the VALUE. The edition tags are absent here on purpose -- OpdbMappings.md calls
-- them signals to CONSIDER, an open decision that belongs on the worklist.
CREATE OR REPLACE VIEW opdb_vocabulary_settled AS
  SELECT
    s.*,
    NOT EXISTS (SELECT 1 FROM _eds_opdb_vocabulary AS v
                WHERE NOT v.target_exists
                  AND v.target_entity_type = s.target_entity_type
                  AND v.target_value = s.target_value) AS is_stale
  FROM (VALUES
    ('tag', 'licensed',
     'OpdbMappings.md rules out minting a tag: the signal feeds licensed-relationship research, not tag vocabulary.')
  ) AS s(target_entity_type, target_value, reason);
COMMENT ON VIEW opdb_vocabulary_settled IS
  'Absent-vocabulary values adjudicated as permanently not ours to mint, with the reason and an is_stale flag. Settled values leave opdb_vocabulary_absent.';

-- WORKLIST — an OPDB value aimed at vocabulary the catalog does not have, settled
-- values excluded.
--
-- VALUE GRAIN: one row is one decision, not one per machine.
CREATE OR REPLACE VIEW opdb_vocabulary_absent AS
  SELECT
    target_entity_type,
    target_value,
    count(*)     AS n_models,
    -- Ordered: this reaches a finding message, whose identity depends on it rendering
    -- the same way every run.
    list_sort(list(DISTINCT model_slug) FILTER (model_slug IS NOT NULL))[:5] AS sample_model_slugs
  FROM _eds_opdb_vocabulary AS v
  WHERE NOT target_exists
    AND NOT EXISTS (SELECT 1 FROM opdb_vocabulary_settled AS st
                    WHERE st.target_entity_type = v.target_entity_type
                      AND st.target_value = v.target_value)
  GROUP BY ALL;
COMMENT ON VIEW opdb_vocabulary_absent IS
  'Worklist — one row per unsettled OPDB value naming catalog vocabulary that does not exist, with how many models carry it and a sample. One row is one decision, not one per machine.';

-- ═══ FINDINGS ══════════════════════════════════════════════════════════════
--
-- The worklists projected down into `_external_data_source_findings`; `bridge.sql`
-- holds the identity, dismissal and INSERT-not-UNION rules, and the IPDB file the
-- severity reasoning this follows: `error` means the catalog makes a positive claim
-- the source contradicts, and a gap is never an error.

-- Idempotent under a double `.read` -- see the note beside the table in `bridge.sql`.
DELETE FROM _external_data_source_findings WHERE source = 'opdb';

-- ─── unmatched listings and groups ─────────────────────────────────────────
-- Four warnings, one per classification, because the classes ask for different actions
-- and a dismissal keys on the rule.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  CASE classification
    WHEN 'catalog_holds_unlinked' THEN 'opdb-model-unlinked'
    WHEN 'possible_duplicate'     THEN 'opdb-model-possible-duplicate'
    WHEN 'maker_unresolved'       THEN 'opdb-model-maker-unresolved'
    WHEN 'absent'                 THEN 'opdb-model-absent'
  END AS rule,
  'warning' AS severity,
  opdb_id AS external_id,
  CASE WHEN classification = 'catalog_holds_unlinked' AND unlinked_model_slug IS NOT NULL
       THEN 'model' END AS entity_type,
  CASE WHEN classification = 'catalog_holds_unlinked' THEN unlinked_model_slug END AS entity_public_id,
  CASE classification
    WHEN 'catalog_holds_unlinked' THEN
      format('OPDB {} "{}" matches unlinked catalog model {}; backfill the opdb_id',
             opdb_id, coalesce(opdb_name, '?'), coalesce(unlinked_model_slug, '?'))
    WHEN 'possible_duplicate' THEN
      format('OPDB {} "{}" matches catalog model {}, which already links OPDB {}; read both pages',
             opdb_id, coalesce(opdb_name, '?'), coalesce(linked_model_slug, '?'),
             coalesce(linked_model_opdb_id, '?'))
    WHEN 'maker_unresolved' THEN
      CASE WHEN opdb_manufacturer_name IS NULL THEN
        format('OPDB {} "{}" names no maker at all, so no candidate search ran; {}',
               opdb_id, coalesce(opdb_name, '?'),
               plural(n_namesake_models, 'catalog namesake', 'catalog namesakes'))
      ELSE
        format('OPDB {} "{}" names maker "{}", whose id no live manufacturer carries, so no candidate search ran; {}',
               opdb_id, coalesce(opdb_name, '?'), opdb_manufacturer_name,
               plural(n_namesake_models, 'catalog namesake', 'catalog namesakes'))
      END
    WHEN 'absent' THEN
      -- The relation qualifies what creating the record involves: an edition with a
      -- resolved parent is a smaller job than a standalone machine.
      format('OPDB {} "{}" ({}, {}) has no catalog model and none matches its name and maker{}{}',
             opdb_id, coalesce(opdb_name, '?'), coalesce(opdb_year::VARCHAR, 'undated'),
             opdb_relation,
             CASE WHEN parent_model_slug IS NOT NULL
                  THEN '; catalog parent ' || parent_model_slug ELSE '' END,
             CASE WHEN linked_title_slug IS NOT NULL
                  THEN '; files under title ' || linked_title_slug ELSE '' END)
  END AS message,
  'opdb_models_unmatched' AS detail_view
FROM opdb_models_unmatched;

INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  CASE classification
    WHEN 'catalog_holds_unlinked' THEN 'opdb-title-unlinked'
    WHEN 'possible_duplicate'     THEN 'opdb-title-possible-duplicate'
    WHEN 'absent'                 THEN 'opdb-title-absent'
  END AS rule,
  'warning' AS severity,
  opdb_id AS external_id,
  CASE WHEN classification = 'catalog_holds_unlinked' AND unlinked_title_slug IS NOT NULL
       THEN 'title' END AS entity_type,
  CASE WHEN classification = 'catalog_holds_unlinked' THEN unlinked_title_slug END AS entity_public_id,
  CASE classification
    WHEN 'catalog_holds_unlinked' THEN
      format('OPDB group {} "{}" matches unlinked catalog title {}; backfill the opdb_id',
             opdb_id, coalesce(opdb_title_name, '?'), coalesce(unlinked_title_slug, '?'))
    WHEN 'possible_duplicate' THEN
      format('OPDB group {} "{}" matches catalog title {}, which already links OPDB group {}; read both',
             opdb_id, coalesce(opdb_title_name, '?'), coalesce(linked_title_slug, '?'),
             coalesce(linked_title_opdb_id, '?'))
    WHEN 'absent' THEN
      format('OPDB group {} "{}" ({}, {}) has no catalog title and none matches its name',
             opdb_id, coalesce(opdb_title_name, '?'), coalesce(opdb_year::VARCHAR, 'undated'),
             plural(n_opdb_models, 'OPDB model', 'OPDB models'))
  END AS message,
  'opdb_titles_unmatched' AS detail_view
FROM opdb_titles_unmatched;

-- ─── stale ids ─────────────────────────────────────────────────────────────
-- Three of the four classes are errors -- the changelog CONFIRMS the catalog is citing
-- something dead, superseded, or of the wrong kind -- and the unexplained class stays a
-- warning for the same reason IPDB's unexplained absences do: the dump cannot support
-- the stronger claim.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  CASE classification
    WHEN 'moved'       THEN 'opdb-id-moved'
    WHEN 'deleted'     THEN 'opdb-id-deleted'
    WHEN 'container'   THEN 'opdb-id-container'
    WHEN 'unexplained' THEN 'opdb-id-not-in-dump'
  END AS rule,
  CASE WHEN classification = 'unexplained' THEN 'warning' ELSE 'error' END AS severity,
  opdb_id AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  CASE classification
    WHEN 'moved' THEN
      format('{} cites OPDB {}, which OPDB moved to {}{}',
             model_slug, opdb_id, coalesce(current_opdb_id, '?'),
             CASE WHEN current_id_model_slug IS NOT NULL
                  THEN ' — already linked by ' || current_id_model_slug || '; possible merge'
                  ELSE '; repoint the opdb_id' END)
    WHEN 'deleted' THEN
      format('{} cites OPDB {}, a listing OPDB has deleted', model_slug, opdb_id)
    WHEN 'container' THEN
      format('{} cites OPDB {}, a non-physical group container, not a machine', model_slug, opdb_id)
    WHEN 'unexplained' THEN
      format('{} cites OPDB {}, absent from both the dump and the id changelog; read OPDB', model_slug, opdb_id)
  END AS message,
  'opdb_ids_stale' AS detail_view
FROM opdb_ids_stale;

INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'opdb-title-id-not-in-dump' AS rule,
  'warning' AS severity,
  opdb_id AS external_id,
  'title' AS entity_type,
  title_slug AS entity_public_id,
  format('{} cites OPDB group {}, absent from the dump; the changelog is machine-grain, so read OPDB',
         title_slug, opdb_id) AS message,
  'opdb_title_ids_stale' AS detail_view
FROM opdb_title_ids_stale;

-- ─── maker disagreement ────────────────────────────────────────────────────
-- All warnings -- the brand-grain sanity check never supports `error`. Two classes
-- produce no finding at all: `excepted` is an adjudicated pairing, and
-- `opdb_unmatched` is already reported at its decision grain by
-- `opdb-manufacturer-unknown` -- resolving the manufacturer resolves every model filed
-- under it, and reporting each model besides restates one defect under two names.
--
-- `disagrees` is PAIR grain: one finding per pairing, however many models file that
-- way. A pairing adjudicated as fine goes in the EXCEPTIONS list, not a dismissal --
-- the message carries the count, so a dismissal would lapse whenever a model was added,
-- which is wrong for a decision about the pairing itself.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'opdb-manufacturer-disagrees' AS rule,
  'warning' AS severity,
  opdb_manufacturer_id::VARCHAR AS external_id,
  'manufacturer' AS entity_type,
  manufacturer_slug AS entity_public_id,
  format('{} disagrees with OPDB''s {} on {}: {}{} — OPDB files under parent companies; adjudicate, then except or patch',
         coalesce(manufacturer_slug, '?'), coalesce(opdb_manufacturer_slug, '?'),
         plural(n_models, 'model', 'models'),
         CASE WHEN n_models > 5 THEN 'e.g. ' ELSE '' END,
         array_to_string(sample_model_slugs, ', ')) AS message,
  'opdb_manufacturer_pairs_disagreeing' AS detail_view
FROM opdb_manufacturer_pairs_disagreeing;

INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'opdb-manufacturer-missing' AS rule,
  'warning' AS severity,
  opdb_id AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  format('{} carries no manufacturer; OPDB names {}',
         model_slug, coalesce(opdb_manufacturer_slug, coalesce(opdb_manufacturer_name, '?'))) AS message,
  'opdb_model_manufacturer_mismatched' AS detail_view
FROM opdb_model_manufacturer_mismatched
WHERE classification = 'catalog_has_none';

-- ─── manufacturers ─────────────────────────────────────────────────────────
-- The NOT EXISTS is deduplication: where the id-acquirable rule below fired for this
-- id, both rules describe the same missing link from opposite ends, and the acquirable
-- side survives because it names a catalog record. Guarded on the acquirable rule
-- ACTUALLY FIRING, not on `catalog_name_matches` -- that list resolves through aliases
-- and ignores already-linked manufacturers, so a name match alone does not promise the
-- other finding exists. The wide view keeps every row either way.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'opdb-manufacturer-unknown' AS rule,
  'warning' AS severity,
  opdb_manufacturer_id::VARCHAR AS external_id,
  NULL::VARCHAR AS entity_type,     -- no catalog record: that is the finding
  NULL::VARCHAR AS entity_public_id,
  format('OPDB manufacturer {} "{}" is on no live catalog manufacturer; {} depend{} on it{}',
         opdb_manufacturer_id, array_to_string(opdb_names, '" / "'),
         plural(n_opdb_models, 'OPDB model', 'OPDB models'),
         CASE WHEN n_opdb_models = 1 THEN 's' ELSE '' END,
         CASE WHEN len(catalog_name_matches) > 0
              THEN ' — catalog names matching: ' || array_to_string(catalog_name_matches, ', ')
              ELSE '' END) AS message,
  'opdb_manufacturers_unmatched' AS detail_view
FROM opdb_manufacturers_unmatched AS u
WHERE NOT EXISTS (SELECT 1 FROM manufacturers_missing_opdb_id AS a
                  WHERE a.opdb_manufacturer_id = u.opdb_manufacturer_id);

INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'opdb-manufacturer-id-acquirable' AS rule,
  'warning' AS severity,
  opdb_manufacturer_id::VARCHAR AS external_id,
  'manufacturer' AS entity_type,
  manufacturer_slug AS entity_public_id,
  -- "e.g." only when the id is actually an example: with one match it IS the record.
  CASE WHEN n_opdb_matches = 1
    THEN format('{} carries no OPDB id; OPDB record {} matches it by name',
                manufacturer_slug, opdb_manufacturer_id)
    ELSE format('{} carries no OPDB id; {} match it by name, e.g. record {}',
                manufacturer_slug, plural(n_opdb_matches, 'OPDB record', 'OPDB records'),
                opdb_manufacturer_id)
  END AS message,
  'manufacturers_missing_opdb_id' AS detail_view
FROM manufacturers_missing_opdb_id;

-- ─── the IPDB cross-reference ──────────────────────────────────────────────
-- `disagrees` is the one OPDB rule outside the stale ids that reaches `error`: both
-- sides assert the same link and one of them is wrong.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  CASE classification WHEN 'disagrees' THEN 'opdb-ipdb-id-disagrees'
                      ELSE 'opdb-ipdb-id-acquirable' END AS rule,
  CASE classification WHEN 'disagrees' THEN 'error' ELSE 'warning' END AS severity,
  opdb_id AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  CASE classification
    WHEN 'disagrees' THEN
      format('{} carries ipdb_id {} but OPDB cross-references IPDB {}; one link is wrong',
             model_slug, coalesce(ipdb_id::VARCHAR, '?'), coalesce(opdb_ipdb_id::VARCHAR, '?'))
    ELSE
      format('{} carries no ipdb_id; OPDB cross-references IPDB {}, which {} in the merged IPDB dump',
             model_slug, coalesce(opdb_ipdb_id::VARCHAR, '?'),
             CASE WHEN ipdb_id_in_ipdb_dump THEN 'resolves' ELSE 'does NOT resolve' END)
  END AS message,
  'opdb_ipdb_id_crosscheck' AS detail_view
FROM opdb_ipdb_id_crosscheck;

-- ─── field disagreements ───────────────────────────────────────────────────
-- Warnings: both sides state a value and differ, and nothing says which is wrong --
-- the catalog's values are researched past OPDB on exactly these fields.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'opdb-field-disagrees' AS rule,
  'warning' AS severity,
  opdb_id AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  format('{}: {} is {} here but {} on OPDB',
         model_slug, field, catalog_value, opdb_value) AS message,
  'opdb_model_fields_disagreeing' AS detail_view
FROM opdb_model_fields_disagreeing;

-- ─── vocabulary ────────────────────────────────────────────────────────────
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'opdb-vocabulary-missing' AS rule,
  'warning' AS severity,
  opdb_id AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  format('{} does not carry {} {}, which OPDB asserts',
         model_slug, target_entity_type, coalesce(target_slug, target_value)) AS message,
  'opdb_model_vocabulary_missing' AS detail_view
FROM opdb_model_vocabulary_missing;

-- Value grain: one row is one vocabulary decision.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'opdb-vocabulary-absent' AS rule,
  'warning' AS severity,
  NULL::VARCHAR AS external_id,
  NULL::VARCHAR AS entity_type,
  NULL::VARCHAR AS entity_public_id,
  format('OPDB asserts {} "{}", which the catalog does not have; {} affected: {}{}',
         target_entity_type, target_value,
         plural(n_models, 'model', 'models'),
         CASE WHEN n_models > 5 THEN 'e.g. ' ELSE '' END,
         array_to_string(sample_model_slugs, ', ')) AS message,
  'opdb_vocabulary_absent' AS detail_view
FROM opdb_vocabulary_absent;

-- ═══ SUMMARY & CHECKS ══════════════════════════════════════════════════════

CREATE OR REPLACE VIEW opdb_summary AS
  SELECT 'unmatched_' || classification AS metric, count(*) AS value
  FROM opdb_models_unmatched GROUP BY classification
  UNION ALL SELECT 'unmatched_titles_' || classification, count(*)
    FROM opdb_titles_unmatched GROUP BY classification
  UNION ALL SELECT 'ids_stale_' || classification, count(*)
    FROM opdb_ids_stale GROUP BY classification
  UNION ALL SELECT 'title_ids_stale', count(*) FROM opdb_title_ids_stale
  UNION ALL SELECT 'manufacturer_' || classification, count(*)
    FROM opdb_model_manufacturer_mismatched GROUP BY classification
  UNION ALL SELECT 'manufacturer_pairs_disagreeing', count(*) FROM opdb_manufacturer_pairs_disagreeing
  UNION ALL SELECT 'opdb_manufacturers_unmatched', count(*) FROM opdb_manufacturers_unmatched
  UNION ALL SELECT 'manufacturers_missing_opdb_id', count(*) FROM manufacturers_missing_opdb_id
  UNION ALL SELECT 'manufacturer_exceptions_stale', count(*)
    FROM opdb_manufacturer_exceptions WHERE is_stale
  UNION ALL SELECT 'ipdb_crosscheck_' || classification, count(*)
    FROM opdb_ipdb_id_crosscheck GROUP BY classification
  UNION ALL SELECT 'fields_disagreeing', count(*) FROM opdb_model_fields_disagreeing
  UNION ALL SELECT 'vocabulary_missing', count(*) FROM opdb_model_vocabulary_missing
  UNION ALL SELECT 'vocabulary_absent_values', count(*) FROM opdb_vocabulary_absent
  UNION ALL SELECT 'vocabulary_settled_stale', count(*)
    FROM opdb_vocabulary_settled WHERE is_stale
  UNION ALL SELECT 'dump_models', count(*) FROM px.opdb.models
  UNION ALL SELECT 'dump_titles', count(*) FROM px.opdb.titles
  UNION ALL SELECT 'catalog_models_with_opdb_id', count(*) FROM models WHERE opdb_id IS NOT NULL
  UNION ALL SELECT 'catalog_titles_with_opdb_id', count(*) FROM titles WHERE opdb_id IS NOT NULL
  UNION ALL SELECT 'FINDINGS errors', count(*)
    FROM external_data_source_findings WHERE source = 'opdb' AND severity = 'error'
  UNION ALL SELECT 'FINDINGS warnings', count(*)
    FROM external_data_source_findings WHERE source = 'opdb' AND severity = 'warning'
  UNION ALL SELECT 'FINDINGS dismissed', count(*)
    FROM external_data_source_findings_all WHERE source = 'opdb' AND dismissed
  ORDER BY metric;
COMMENT ON VIEW opdb_summary IS
  'Headline counts for the OPDB comparison — the unmatched sets by classification, the stale ids, the maker and field disagreements, and the totals both sides are measured against.';

-- Empty when healthy. Invariants of this layer, never findings about the data.
CREATE OR REPLACE VIEW opdb_checks AS
  -- The catalog-side decode key of `_eds_opdb_dump`. Not unique by construction, and a
  -- second row would multiply every count taken off the dump.
  SELECT 'manufacturer_opdb_id_not_unique' AS check_name,
         opdb_manufacturer_id::VARCHAR AS detail
  FROM manufacturers
  WHERE opdb_manufacturer_id IS NOT NULL
  GROUP BY opdb_manufacturer_id HAVING count(*) > 1

  UNION ALL
  -- Both join keys this file rests on. Every comparison assumes one catalog record per
  -- external id; a duplicate would double-count silently everywhere at once.
  SELECT 'model_opdb_id_not_unique', opdb_id
  FROM models WHERE opdb_id IS NOT NULL
  GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  SELECT 'title_opdb_id_not_unique', opdb_id
  FROM titles WHERE opdb_id IS NOT NULL
  GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  -- The aggregations hold the worklists at one row per listing; if one ever stops, the
  -- classification silently double-counts.
  SELECT 'unmatched_not_one_row_per_listing', opdb_id
  FROM opdb_models_unmatched GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  SELECT 'unmatched_titles_not_one_row_per_group', opdb_id
  FROM opdb_titles_unmatched GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  SELECT 'namesakes_not_one_row_per_listing', opdb_id
  FROM _eds_opdb_namesakes GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  -- Closed classification sets: a CASE that grew a branch the consumers of these views
  -- do not know how to answer.
  SELECT 'classification_unknown', classification
  FROM opdb_models_unmatched
  WHERE classification NOT IN
    ('catalog_holds_unlinked', 'possible_duplicate', 'maker_unresolved', 'absent')

  UNION ALL
  SELECT 'title_classification_unknown', classification
  FROM opdb_titles_unmatched
  WHERE classification NOT IN ('catalog_holds_unlinked', 'possible_duplicate', 'absent')

  UNION ALL
  SELECT 'stale_classification_unknown', classification
  FROM opdb_ids_stale
  WHERE classification NOT IN ('moved', 'deleted', 'container', 'unexplained')

  UNION ALL
  SELECT 'manufacturer_classification_unknown', classification
  FROM opdb_model_manufacturer_mismatched
  WHERE classification NOT IN ('excepted', 'catalog_has_none', 'opdb_unmatched', 'disagrees')

  UNION ALL
  -- `absent` asserts the catalog lacks a machine, which is only true if a search ran,
  -- and a search needs a maker on both sides. The same regression guard as IPDB's.
  SELECT 'absent_without_maker_search', opdb_id
  FROM opdb_models_unmatched
  WHERE classification = 'absent' AND opdb_manufacturer_slug IS NULL

  UNION ALL
  -- The stale-id join to the changelog is a lookup and must not fan the worklist out.
  SELECT 'stale_not_one_row_per_model', model_slug
  FROM opdb_ids_stale GROUP BY model_slug, opdb_id HAVING count(*) > 1

  UNION ALL
  -- THE CHECK THE EXCEPTIONS LIST DEMANDED AT BIRTH: its predecessor carried a slug the
  -- catalog had renamed, and the exception silently stopped matching. A slug on no live
  -- manufacturer cannot except anything.
  SELECT 'exception_slug_unresolved', ex.manufacturer_slug
  FROM _eds_opdb_manufacturer_exceptions AS ex
  WHERE NOT EXISTS (SELECT 1 FROM manufacturers AS f WHERE f.slug = ex.manufacturer_slug)

  UNION ALL
  -- The corporate-mismatch view is one row per model; the decode must stay a lookup.
  SELECT 'manufacturer_mismatch_not_one_row_per_model', opdb_id
  FROM opdb_model_manufacturer_mismatched GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  -- The crosscheck classification is closed.
  SELECT 'crosscheck_classification_unknown', classification
  FROM opdb_ipdb_id_crosscheck
  WHERE classification NOT IN ('disagrees', 'acquirable')

  UNION ALL
  -- The fields LATERAL names a closed set; a field added there without a message and
  -- probe behind it should announce itself.
  SELECT 'field_unknown', field
  FROM opdb_model_fields_disagreeing
  WHERE field NOT IN ('year', 'player_count', 'technology_generation', 'display_type')

  UNION ALL
  -- The carriage CASE has no ELSE; this turns an unhandled target_entity_type into a
  -- loud failure instead of a silent gap report.
  SELECT 'vocabulary_carriage_unhandled', target_entity_type
  FROM _eds_opdb_vocabulary
  WHERE model_slug IS NOT NULL AND carried IS NULL
  GROUP BY ALL

  UNION ALL
  -- The vocabulary union is one row per (listing, entity type, value); the model join
  -- is a lookup and must not fan it out.
  SELECT 'vocabulary_not_one_row_per_assertion',
         opdb_id || ' / ' || target_entity_type || ' / ' || target_value
  FROM _eds_opdb_vocabulary
  GROUP BY opdb_id, target_entity_type, target_value HAVING count(*) > 1

  UNION ALL
  -- The anchor for the vocabulary section: pinexplore publishing NO assertions at all
  -- reads exactly like a catalog that already carries everything.
  -- Worded without naming the attach alias: the boundary check regex-scans view SQL
  -- and cannot tell an identifier from prose.
  SELECT 'vocabulary_assertions_missing', 'every pinexplore OPDB model vocabulary view is empty'
  WHERE (SELECT count(*) FROM _eds_opdb_vocabulary) = 0;
COMMENT ON VIEW opdb_checks IS
  'Empty when healthy — grain, closed-classification and join-key anchors for the OPDB comparison, plus the exception-slug resolution the inherited manufacturer exceptions demanded.';
