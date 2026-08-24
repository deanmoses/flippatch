-- IPDB against the catalog: which listings we hold, and which credits we are missing.
--
-- `.read` this from a campaign analysis after flipcommons' foundation:
--
--     .read ../flippatch/scripts/analysis/external_data_sources/ipdb.sql
--
-- It reads `bridge.sql` itself, so the attach, the watermark and the bridge's own
-- invariants come with it. Read that file first for the scope and the findings/checks
-- rule; the worklists below return rows on a healthy catalog.

.read ../flippatch/scripts/analysis/external_data_sources/bridge.sql

-- One row per IPDB model, as IPDB states it, decoded into catalog terms.
--
-- Reads pinexplore's MART. It is the only thing here that may be read: the staging and
-- reference layers under it are that repo's working material. The mart is also where
-- the corrections live -- records whose scraped manufacturer IPDB's own page denies
-- arrive with those fields already cleared, and IPDB's two ways of writing "no
-- manufacturer" (ids 0 and 328) arrive as NULL rather than as a company.
--
-- That last point is why the filters below are `IS NOT NULL` rather than a NOT IN
-- against a list of placeholder ids. A forgotten `IS NOT NULL` compares against NULL
-- and matches nothing; a forgotten NOT IN compares against a real corporate entity and
-- matches the wrong one.
--
-- Every `ipdb_` column is IPDB's assertion; the two slugs are that assertion decoded, not
-- the catalog's own answer -- `ipdb_corporate_entity_slug` is the corporate entity IPDB's
-- id points at, which is the thing the catalog's own value gets compared against below.
--
-- The decode joins on `ipdb_manufacturer_id`, the catalog's handle on an IPDB maker,
-- which resolves all but two of them and cannot multiply the grain: that column is unique
-- across live corporate entities, asserted in `ipdb_checks`.
CREATE OR REPLACE VIEW _eds_ipdb_dump AS
  SELECT
    im.ipdb_id,
    im.name                                                         AS ipdb_name,
    im.ipdb_corporate_entity_id,
    im.corporate_entity_text                                        AS ipdb_corporate_entity_text,
    EXTRACT(YEAR FROM TRY_CAST(im.date_of_manufacture AS DATE))::INT AS ipdb_year,
    im.carried_forward,
    im.duplicate_of_ipdb_id,
    corporate_entity.slug                                           AS ipdb_corporate_entity_slug,
    corporate_entity.manufacturer_slug                              AS ipdb_manufacturer_slug
  FROM px.ipdb.models AS im
  LEFT JOIN corporate_entities AS corporate_entity
    ON corporate_entity.ipdb_manufacturer_id = im.ipdb_corporate_entity_id;

-- Catalog models that answer to an unmatched listing's name and maker, counted by
-- whether they already carry an IPDB id.
--
-- Matched on `name_norm`, not `name_key`: `name_key` strips a trailing parenthetical, so
-- it folds "Foo Fighters (Pro)", "(Premium)" and "(Limited Edition)" onto one key and
-- would offer all three as candidates for each. The edition suffix is the identity here.
--
-- Aggregated rather than joined through, because a name and maker can answer to more
-- than one model and joining would emit the listing once per candidate. The two counts
-- are what expose that: a representative slug is projected for the common single-
-- candidate case, and `n_*_candidates > 1` says not to trust it.
CREATE OR REPLACE VIEW _eds_ipdb_candidates AS
  WITH unmatched AS (
    SELECT * FROM _eds_ipdb_dump AS d
    WHERE NOT EXISTS (SELECT 1 FROM models AS m WHERE m.ipdb_id = d.ipdb_id)
  )
  SELECT
    u.ipdb_id,
    count(*) FILTER (WHERE m.ipdb_id IS NULL)                        AS n_unlinked_candidates,
    count(*) FILTER (WHERE m.ipdb_id IS NOT NULL)                    AS n_linked_candidates,
    any_value(m.slug)    FILTER (WHERE m.ipdb_id IS NULL)            AS unlinked_model_slug,
    any_value(m.slug)    FILTER (WHERE m.ipdb_id IS NOT NULL)        AS linked_model_slug,
    any_value(m.ipdb_id) FILTER (WHERE m.ipdb_id IS NOT NULL)        AS linked_model_ipdb_id,
    any_value(m.year)    FILTER (WHERE m.ipdb_id IS NOT NULL)        AS linked_model_year
  FROM unmatched AS u
  INNER JOIN models AS m
    ON name_norm(m.name) = name_norm(u.ipdb_name)
   AND m.manufacturer_slug = u.ipdb_manufacturer_slug
  GROUP BY u.ipdb_id;

-- Catalog models answering to an unmatched listing's NAME, whatever their maker.
--
-- The weaker half of the pair above, and it exists because the stronger half needs a
-- maker on both sides. Where the listing has no resolved maker, `_eds_ipdb_candidates`
-- cannot match anything at all, and a count of zero there is "not looked for" rather
-- than "not there" -- the two read identically until this says otherwise.
--
-- A namesake is not a candidate. Machine names repeat freely across makers and decades
-- (eight live models are called Lady Luck), so this evidences the question rather than
-- answering it: a non-zero count means read the IPDB page before creating a record.
CREATE OR REPLACE VIEW _eds_ipdb_namesakes AS
  SELECT
    d.ipdb_id,
    count(*)                                    AS n_namesake_models,
    list_sort(list(m.slug))[:5]                 AS namesake_model_slugs
  FROM _eds_ipdb_dump AS d
  INNER JOIN models AS m ON name_norm(m.name) = name_norm(d.ipdb_name)
  WHERE NOT EXISTS (SELECT 1 FROM models AS x WHERE x.ipdb_id = d.ipdb_id)
  GROUP BY d.ipdb_id;

-- WORKLIST — IPDB listings with no catalog model, and what each one actually is.
--
-- "No model carries this IPDB id" is one condition covering five situations that want
-- five different responses, and reading them all as gaps overstates the work by roughly
-- half. `classification` separates them:
--
--   duplicate_listing       IPDB lists this model twice under two of its own maker
--                           records; the catalog links the other id. Nothing to do.
--                           Confirmed cases only, carried on the mart row itself;
--                           pinexplore's `ipdb_ref.duplicate_listings` records the
--                           reasoning and the two URLs it rests on.
--   catalog_holds_unlinked  The catalog has the machine and no IPDB id on it. A
--                           backfill: patch the id, do not create a record.
--   possible_duplicate      A catalog model of the same name and maker is already
--                           linked to a DIFFERENT IPDB id. Either an unrecorded
--                           duplicate listing, or two genuinely different machines.
--                           Needs both IPDB pages read before it can move.
--   maker_unresolved        No candidate search was possible: the listing has no maker
--                           to match on. NOT a statement that the catalog lacks the
--                           machine -- read `n_namesake_models` and the IPDB page.
--   absent                  A search ran on name and maker and found nothing. A
--                           candidate new record.
--
-- `maker_unresolved` exists because the candidate search needs a maker on BOTH sides
-- and silently matches nothing when it has one, which used to land these rows in
-- `absent` -- asserting the catalog lacks a machine nobody had looked for. IPDB 7067
-- "Long Shot" read that way while the catalog held two Long Shots.
--
-- Two causes, told apart by `ipdb_corporate_entity_text`. NULL means IPDB names no
-- maker at all, and only the page or another source can settle it. Non-NULL means IPDB
-- names one the catalog carries no id for, which `ipdb_corporate_entities_unmatched`
-- worklists -- acquire the id there and these rows classify themselves.
--
-- Precedence runs confirmed-first: a confirmed duplicate also matches the
-- `possible_duplicate` shape by construction, and the confirmation is the stronger
-- statement. `catalog_holds_unlinked` outranks `possible_duplicate` because an unlinked
-- model is the cheaper and likelier explanation; where both hold, the candidate counts
-- carry the ambiguity. `maker_unresolved` sits below both only for reading order -- a
-- row without a maker slug reaches neither branch anyway, since the join they rest on
-- cannot match on a NULL.
--
-- `carried_forward` is worth reading before acting on an `absent` row: it marks a record
-- the newest scrape missed, served from an older snapshot, so the listing may no longer
-- exist upstream at all.
CREATE OR REPLACE VIEW ipdb_models_unmatched AS
  SELECT
    d.ipdb_id,
    d.ipdb_name,
    d.ipdb_year,
    d.ipdb_corporate_entity_text,
    d.ipdb_manufacturer_slug,
    CASE
      WHEN d.duplicate_of_ipdb_id IS NOT NULL   THEN 'duplicate_listing'
      WHEN c.n_unlinked_candidates > 0          THEN 'catalog_holds_unlinked'
      WHEN c.n_linked_candidates > 0            THEN 'possible_duplicate'
      WHEN d.ipdb_manufacturer_slug IS NULL     THEN 'maker_unresolved'
      ELSE                                           'absent'
    END                                    AS classification,
    d.duplicate_of_ipdb_id,
    c.unlinked_model_slug,
    c.linked_model_slug,
    c.linked_model_ipdb_id,
    c.linked_model_year,
    coalesce(c.n_unlinked_candidates, 0)   AS n_unlinked_candidates,
    coalesce(c.n_linked_candidates, 0)     AS n_linked_candidates,
    -- Name-only evidence, carried on every row rather than only the unsearchable ones:
    -- a namesake under a DIFFERENT maker is worth seeing before creating a record, and
    -- an `absent` row with namesakes is the shape a mis-attributed listing takes.
    coalesce(n.n_namesake_models, 0)       AS n_namesake_models,
    n.namesake_model_slugs,
    d.carried_forward
  FROM _eds_ipdb_dump AS d
  LEFT JOIN _eds_ipdb_candidates AS c USING (ipdb_id)
  LEFT JOIN _eds_ipdb_namesakes  AS n USING (ipdb_id)
  WHERE NOT EXISTS (SELECT 1 FROM models AS m WHERE m.ipdb_id = d.ipdb_id);
COMMENT ON VIEW ipdb_models_unmatched IS
  'Worklist — one row per IPDB listing no live model carries the id of, classified as duplicate_listing / catalog_holds_unlinked / possible_duplicate / maker_unresolved / absent, with the candidate model where one was found and a namesake count where one was not. Rows are expected.';

-- WORKLIST — the other direction: a model carries an IPDB id the dump no longer holds.
--
-- Either the listing was deleted upstream and the catalog is citing a dead record, or a
-- scrape missed it. pinexplore tells them apart where it knows: a confirmed deletion is
-- in `ipdb.retracted_listings` with its evidence, and `retraction_reason` carries that
-- here. A NULL there is unexplained absence, which is a page to load rather than a fact.
--
-- That view is republished rather than folded into a column because it is the one fact
-- about the dump no column can carry: the row it describes is absent from `ipdb.models`
-- by construction.
CREATE OR REPLACE VIEW ipdb_ids_not_in_dump AS
  SELECT
    m.slug              AS model_slug,
    m.name              AS model_name,
    m.ipdb_id,
    m.year,
    m.manufacturer_slug,
    r.reason            AS retraction_reason,
    r.evidence_url      AS retraction_evidence_url,
    'https://www.ipdb.org/machine.cgi?id=' || m.ipdb_id AS ipdb_url
  FROM models AS m
  LEFT JOIN px.ipdb.retracted_listings AS r ON r.ipdb_id = m.ipdb_id
  WHERE m.ipdb_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM px.ipdb.models AS im WHERE im.ipdb_id = m.ipdb_id);
COMMENT ON VIEW ipdb_ids_not_in_dump IS
  'Worklist — one row per live model whose ipdb_id is absent from the merged dump, with pinexplore''s retraction evidence where the deletion is confirmed. Rows are expected.';

-- WORKLIST — models where IPDB's maker and the catalog's do not line up.
--
-- IPDB issues one id per CORPORATE ENTITY, not per manufacturer: `Bally` is ids 47, 48
-- and 214, one per incarnation. So this compares corporate entities, and carries the
-- manufacturer each rolls up to beside it -- a disagreement that survives the roll-up is
-- a different and larger claim than one that does not.
--
--   catalog_has_none       IPDB names a maker and the model carries no corporate
--                          entity. A backfill, provided IPDB's attribution is sound.
--   ipdb_entity_unmatched  IPDB's id is on no live corporate entity, so nothing was
--                          compared. Usually IPDB holding one company twice: the
--                          catalog links one of its ids and the models filed under the
--                          other land here. Resolve at the entity, not the model --
--                          `ipdb_corporate_entities_unmatched` is one row per company
--                          rather than one per machine attributed to it.
--   disagrees              Both resolve and differ. Structurally rare, because the
--                          catalog's corporate entities were largely seeded FROM these
--                          ids and read the same key back -- so a row is either a
--                          genuine correction or IPDB re-pointing an id, and is worth a
--                          look precisely because it should not happen.
--
-- Models IPDB names no maker for are absent entirely, which is not the same as agreement:
-- `models_without_corporate_entity` in the summary is the catalog-side total, and the
-- difference between the two is the population no external source can settle.
CREATE OR REPLACE VIEW ipdb_model_corporate_entity_mismatched AS
  SELECT
    d.ipdb_id,
    d.ipdb_name,
    m.slug                        AS model_slug,
    CASE
      WHEN m.corporate_entity_slug IS NULL        THEN 'catalog_has_none'
      WHEN d.ipdb_corporate_entity_slug IS NULL   THEN 'ipdb_entity_unmatched'
      ELSE                                             'disagrees'
    END                           AS classification,
    m.corporate_entity_slug,
    d.ipdb_corporate_entity_slug,
    d.ipdb_corporate_entity_text,
    m.manufacturer_slug,
    d.ipdb_manufacturer_slug,
    m.manufacturer_slug IS DISTINCT FROM d.ipdb_manufacturer_slug AS manufacturer_differs,
    'https://www.ipdb.org/machine.cgi?id=' || d.ipdb_id AS ipdb_url
  FROM _eds_ipdb_dump AS d
  INNER JOIN models AS m ON m.ipdb_id = d.ipdb_id
  -- No placeholder filter: the mart already says NULL where IPDB names no maker.
  WHERE d.ipdb_corporate_entity_id IS NOT NULL
    AND m.corporate_entity_slug IS DISTINCT FROM d.ipdb_corporate_entity_slug;
COMMENT ON VIEW ipdb_model_corporate_entity_mismatched IS
  'Worklist — one row per model whose corporate entity differs from the one IPDB names, classified catalog_has_none / ipdb_entity_unmatched / disagrees, with the manufacturer each rolls up to. Rows are expected.';

-- WORKLIST — an IPDB corporate entity the catalog has no handle on.
--
-- Its id appears on no live corporate entity, so every model IPDB attributes to it
-- resolves to nothing and every comparison above is silent about them. Either the company
-- is genuinely absent from the catalog, or we hold it and never recorded the id -- which
-- `corporate_entities_missing_ipdb_id` is the other half of.
CREATE OR REPLACE VIEW ipdb_corporate_entities_unmatched AS
  SELECT
    i.ipdb_corporate_entity_id,
    i.corporate_entity_name        AS ipdb_corporate_entity_name,
    -- The mart's derived brand -- the trade name where IPDB states one, the company
    -- name otherwise. NOT the raw `trade_name`, which is '' on every entity IPDB gives
    -- no trade name, and that is most of them.
    i.manufacturer_name            AS ipdb_manufacturer_name,
    i.corporate_entity_text        AS ipdb_corporate_entity_text,
    (SELECT count(*) FROM _eds_ipdb_dump AS d
      WHERE d.ipdb_corporate_entity_id = i.ipdb_corporate_entity_id) AS n_ipdb_models,
    (SELECT list(e.name) FROM entity_names AS e
      WHERE e.entity_type = 'corporate-entity'
        AND name_norm(e.name) = name_norm(i.corporate_entity_name)) AS catalog_name_matches
  FROM px.ipdb.corporate_entities AS i
  WHERE NOT EXISTS (
    SELECT 1 FROM corporate_entities AS c
    WHERE c.ipdb_manufacturer_id = i.ipdb_corporate_entity_id
  );
COMMENT ON VIEW ipdb_corporate_entities_unmatched IS
  'Worklist — one row per IPDB corporate entity whose id no live corporate entity carries, with how many IPDB models depend on it and any catalog record answering to the same name.';

-- WORKLIST — a corporate entity we hold that IPDB now has a record for.
--
-- The catalog's makers do not all come from IPDB; recent boutique manufacturers were
-- researched here first. When IPDB catches up, the id becomes acquirable, and this is
-- where that shows. Empty means nothing to acquire today, not that the check is idle.
--
-- Name matching is the only route available: with no id on our side there is nothing to
-- join on. `n_ipdb_matches` above 1 means the name reaches several IPDB records and names
-- none of them in particular.
CREATE OR REPLACE VIEW corporate_entities_missing_ipdb_id AS
  SELECT
    c.slug                    AS corporate_entity_slug,
    c.name                    AS corporate_entity_name,
    c.manufacturer_slug,
    c.n_models,
    i.n_ipdb_matches,
    i.ipdb_corporate_entity_id,
    i.ipdb_corporate_entity_text
  FROM corporate_entities AS c
  INNER JOIN (
    SELECT
      name_norm(corporate_entity_name)  AS name_key,
      count(*)                          AS n_ipdb_matches,
      min(ipdb_corporate_entity_id)     AS ipdb_corporate_entity_id,
      any_value(corporate_entity_text)  AS ipdb_corporate_entity_text
    FROM px.ipdb.corporate_entities
    GROUP BY 1
  ) AS i ON i.name_key = name_norm(c.name)
  WHERE c.ipdb_manufacturer_id IS NULL;
COMMENT ON VIEW corporate_entities_missing_ipdb_id IS
  'Worklist — one row per live corporate entity with no IPDB id that IPDB now appears to hold a record for, matched by name. Empty when there is nothing to acquire.';

-- Every string that names a live person, folded once, so a credit can be resolved
-- without joining the whole name pool per row. `n_people` is the guard: one norm can
-- name two different people, and a credit resolved to an arbitrary one of them is worse
-- than one left unresolved.
CREATE OR REPLACE VIEW _eds_person_by_name AS
  SELECT name_norm(name) AS person_name_norm,
         count(DISTINCT entity_id) AS n_people,
         min(entity_id)            AS person_id
  FROM entity_names
  WHERE entity_type = 'person'
  GROUP BY 1;

-- IPDB's credits, landed on the catalog model and person they refer to.
--
-- `name_norm`, not `name_key`: `name_key` drops a trailing parenthetical, which on a
-- person is part of the name rather than a qualifier.
CREATE OR REPLACE VIEW _eds_ipdb_credits AS
  SELECT
    c.ipdb_id,
    m.id            AS model_id,
    m.slug          AS model_slug,
    c.role          AS ipdb_role,
    c.role_slug,
    c.person_name   AS ipdb_person_name,
    r.person_id,
    coalesce(r.n_people, 0) AS n_person_matches,
    p.slug          AS person_slug
  FROM px.ipdb.credits AS c
  INNER JOIN models AS m ON m.ipdb_id = c.ipdb_id
  LEFT JOIN _eds_person_by_name AS r ON r.person_name_norm = name_norm(c.person_name)
  LEFT JOIN people AS p ON p.id = r.person_id;

-- WORKLIST — a credit IPDB records that the catalog does not.
--
-- One direction only. The catalog's credits come from many sources and it holds
-- hundreds IPDB has no record of; asserting the two agree would fail on every
-- well-researched model and say nothing. What is actionable is the other side: IPDB
-- names someone the catalog does not credit.
--
-- `person_slug` NULL with `n_person_matches` 0 means the person is not in the catalog
-- either, so the row needs a person created before the credit can be added.
-- `n_person_matches` above 1 means the name is ambiguous and the row names no one in
-- particular -- resolve it by hand rather than by picking.
--
-- Reaches only listings the catalog already links, since a credit needs a model to hang
-- on. Credits on the `catalog_holds_unlinked` rows of `ipdb_models_unmatched` appear here
-- only once those ids are backfilled, so this count grows as that worklist shrinks.
CREATE OR REPLACE VIEW ipdb_credits_missing AS
  SELECT
    c.ipdb_id,
    c.model_slug,
    c.role_slug,
    c.ipdb_person_name,
    c.person_slug,
    c.n_person_matches,
    'https://www.ipdb.org/machine.cgi?id=' || c.ipdb_id AS ipdb_url
  FROM _eds_ipdb_credits AS c
  WHERE NOT EXISTS (
    SELECT 1 FROM model_credits AS mc
    WHERE mc.model_id  = c.model_id
      AND mc.role_slug = c.role_slug
      AND mc.person_id = c.person_id
  );
COMMENT ON VIEW ipdb_credits_missing IS
  'Worklist — one row per IPDB credit with no counterpart in the catalog, with the resolved person where the name matched one. Rows are expected.';

-- WORKLIST — a person IPDB credits who is not in the catalog at all.
--
-- The person-grain rollup of the unresolved half of `ipdb_credits_missing`: a new dump
-- brings new people, and creating the person comes before crediting them. Empty today.
CREATE OR REPLACE VIEW ipdb_people_unmatched AS
  SELECT
    ipdb_person_name,
    list_sort(list(DISTINCT role_slug))        AS role_slugs,
    count(DISTINCT ipdb_id)                    AS n_models,
    list_sort(list(DISTINCT ipdb_id))[:5]      AS sample_ipdb_ids
  FROM _eds_ipdb_credits
  WHERE n_person_matches = 0
  GROUP BY ipdb_person_name;
COMMENT ON VIEW ipdb_people_unmatched IS
  'Worklist — one row per person IPDB credits whose name matches no live catalog person, with the roles and machines they appear on.';

-- ═══ SPECIALTIES ═══════════════════════════════════════════════════════════
--
-- IPDB's Specialty field, which the Xantari dumps do not carry and the archive.org
-- pages do. It is the source of basic classification we have otherwise had to
-- synthesize: bingo, payout, widebody, flipperless.
--
-- pinexplore maps each IPDB specialty onto OUR vocabulary and publishes the rules whole
-- in `px.ipdb.specialties`, including the ones aimed at vocabulary we do not have. Its
-- reference file states the division of labour outright: "This build can check only that
-- spelling convention; flippatch must check whether the target exists." That check is
-- `specialty_target_not_in_catalog` below, and it is the reason this section exists at
-- all rather than the mapping being trusted end to end.
--
-- Coverage is archive-sourced and therefore partial -- 189 assignments over 151 models
-- today, against 6676 listings. A model with no row here has not been checked, not been
-- cleared.

-- One row per (IPDB model, specialty), landed on the catalog model and answered twice
-- over: does the target vocabulary EXIST, and does the model CARRY it.
--
-- `target_exists` is asked of every row except the `model-relationship` ones, whose
-- targets (`conversion`, `conversion_kit`, `retheme`) name a relationship type rather
-- than a record -- neither resolvable nor missing vocabulary, so they resolve
-- structurally. Pinexplore used to ship a flag pre-answering this; it no longer does,
-- and should not have: whether our catalog holds a value is ours to answer.
--
-- CARRIAGE IS `IS NOT DISTINCT FROM` ON THE TWO SINGLE-VALUED DIMS, not `=`. A model
-- with no game format at all yields NULL from `=`, and NULL is neither carried nor a
-- gap -- it silently drops out of both, which is precisely backwards: a model whose
-- game format is unset is the MOST actionable row IPDB's assertion produces. That
-- mistake cost 27 findings when this was first counted.
--
-- `model_edges` is outbound-only, which suits all three relationship specialties: IPDB
-- is saying THIS machine is a conversion, a kit, or a retheme of something else.
CREATE OR REPLACE VIEW _eds_ipdb_specialties AS
  SELECT
    s.ipdb_id,
    s.specialty,
    s.target_entity_type,
    s.target_value,
    s.archive_source_url,
    s.archive_capture_date,
    m.id   AS model_id,
    m.slug AS model_slug,
    m.name AS model_name,
    -- Resolved HERE, against the live catalog, because here is the only place it
    -- can be. Pinexplore used to ship a flag saying whether a target existed, and
    -- this read it rather than looking -- a claim about our database made by one
    -- that cannot see it, and stale the moment we added the vocabulary. The
    -- relationship types stay exempt: an edge type is neither a record that
    -- resolves nor vocabulary we lack.
    CASE
      WHEN s.target_entity_type = 'model-relationship' THEN true
      ELSE EXISTS (SELECT 1 FROM entity_subjects AS es
                   WHERE es.subject_type = s.target_entity_type
                     AND es.subject_public_id = s.target_value
                     AND is_live(es.subject_status))
    END AS target_exists,
    CASE s.target_entity_type
      WHEN 'reward-type'      THEN EXISTS (SELECT 1 FROM model_rewards AS r
                                     WHERE r.model_id = m.id AND r.reward_type_slug = s.target_value)
      WHEN 'tag'              THEN EXISTS (SELECT 1 FROM model_tags AS t
                                     WHERE t.model_id = m.id AND t.tag_slug = s.target_value)
      WHEN 'gameplay-feature' THEN EXISTS (SELECT 1 FROM model_gameplay_features AS g
                                     WHERE g.model_id = m.id AND g.feature_slug = s.target_value)
      WHEN 'game-format'      THEN m.game_format_slug IS NOT DISTINCT FROM s.target_value
      WHEN 'cabinet'          THEN m.cabinet_slug     IS NOT DISTINCT FROM s.target_value
      WHEN 'model-relationship' THEN EXISTS (SELECT 1 FROM model_edges AS e
                                     WHERE e.model_id = m.id
                                       AND e.relationship_type = s.target_value)
      -- No ELSE: a target_entity_type nobody wrote a branch for lands NULL, which
      -- `specialty_carriage_unhandled` fails on. An ELSE false would report every such
      -- row as a gap instead, which is a wrong answer rather than a loud one.
    END AS carried
  FROM px.ipdb.model_specialties AS s
  LEFT JOIN models AS m ON m.ipdb_id = s.ipdb_id;

-- WORKLIST — IPDB asserts a classification the catalog has the vocabulary for and the
-- model does not carry.
--
-- The actionable payload: each row is a patch waiting to be written, with the archived
-- page that evidences it. `archive_source_url` and `archive_capture_date` ride along
-- because the claim rests on a capture that is typically years old -- worth knowing
-- before asserting it against a catalog that has moved since.
--
-- Listings with no catalog model are excluded rather than reported: that is already a
-- finding under `ipdb-model-*`, and reporting it twice under two names is the overlap
-- the audit holds its rules apart to avoid.
CREATE OR REPLACE VIEW ipdb_model_specialties_missing AS
  SELECT
    ipdb_id,
    model_slug,
    model_name,
    specialty,
    target_entity_type,
    target_value,
    archive_source_url,
    archive_capture_date,
    'https://www.ipdb.org/machine.cgi?id=' || ipdb_id AS ipdb_url
  FROM _eds_ipdb_specialties
  WHERE model_slug IS NOT NULL
    AND target_exists
    AND NOT carried;
COMMENT ON VIEW ipdb_model_specialties_missing IS
  'Worklist — one row per IPDB specialty the catalog has vocabulary for but the model does not carry, with the archived page and capture date behind it. Rows are expected.';

-- WORKLIST — an IPDB specialty aimed at vocabulary the catalog does not have.
--
-- SPECIALTY GRAIN, not model grain, and that is the whole point. These are the rules
-- pinexplore deliberately left pointing at IPDB's own wording because no catalog term
-- answers them, and each is ONE decision -- add the tag, split the payout type, work out
-- what "Not A Pinball" should be -- not one decision per machine. Reported per model,
-- 49 rows would restate 5 questions.
--
-- Two shapes sit here together. Some are vocabulary we may simply want (`Flipperless`,
-- `WWII Contract`). Others are IPDB headings coarser than ours that no new term would
-- fix: `Payout Machine` spans our `cash-payout` and `merchant-paid`, and `Table
-- Top/Counter Game` spans `tabletop` and `countertop`. Those need the models read, not a
-- slug minted -- pinexplore's reference file says which is which.
CREATE OR REPLACE VIEW ipdb_specialty_vocabulary_absent AS
  SELECT
    specialty,
    target_entity_type,
    target_value              AS ipdb_wording,
    count(*)                  AS n_models,
    -- Ordered: this reaches a finding message, whose identity depends on it rendering
    -- the same way every run.
    list_sort(list(DISTINCT model_slug) FILTER (model_slug IS NOT NULL))[:5] AS sample_model_slugs
  FROM _eds_ipdb_specialties
  WHERE NOT target_exists
  GROUP BY ALL;
COMMENT ON VIEW ipdb_specialty_vocabulary_absent IS
  'Worklist — one row per IPDB specialty naming catalog vocabulary that does not exist, with how many models carry it and a sample. One row is one decision, not one per machine.';

-- ═══ FINDINGS ══════════════════════════════════════════════════════════════
--
-- The worklists above projected down into `_external_data_source_findings`. See
-- `bridge.sql` for why this is an INSERT rather than a UNION, and for the identity and
-- dismissal rules. Each block is self-contained: rule name, severity and wording sit
-- together, and a new rule is added by copying one block rather than by editing a
-- distant manifest.
--
-- SEVERITY. The bar for `error` is the doc's: OUR DATA IS CURRENTLY WRONG. A gap is not
-- an error -- a listing we have not linked, a credit we have not recorded and a maker we
-- hold no id for are all things the catalog does not YET say, and the catalog being
-- incomplete is its normal condition. What earns `error` is the catalog making a
-- positive claim the source contradicts: a dead IPDB id still cited, or two live records
-- that resolve and disagree.
--
-- MESSAGES ARE DETERMINISTIC AND SHORT. Every nullable argument is coalesced, because
-- `format()` propagates NULL and one NULL blanks the entire message -- the failure
-- `finding_null_required` exists to catch. They stay one line and carry no prose the
-- wide view already holds: `ipdb_ids_not_in_dump.retraction_reason` is a paragraph, and
-- the finding's job is to point at it, not to reproduce it.
--
-- Counts go through the foundation's `plural()` rather than "1 model(s)", since these
-- messages are read one per line by a human working the list.

-- Idempotent under a double `.read` -- see the note beside the table in `bridge.sql`.
DELETE FROM _external_data_source_findings WHERE source = 'ipdb';

-- ─── unmatched listings ────────────────────────────────────────────────────
-- `duplicate_listing` is excluded, not downgraded: it is a confirmed IPDB-side double
-- entry whose twin the catalog already links, so there is nothing to do and a finding
-- would be permanent noise. It stays visible in `ipdb_models_unmatched`.
--
-- One rule per classification rather than one rule for the view, because the classes ask
-- for different actions and a dismissal keys on the rule. Four warnings: each is
-- something the catalog does not yet say, never something it says wrongly.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  CASE classification
    WHEN 'catalog_holds_unlinked' THEN 'ipdb-model-unlinked'
    WHEN 'possible_duplicate'     THEN 'ipdb-model-possible-duplicate'
    WHEN 'maker_unresolved'       THEN 'ipdb-model-maker-unresolved'
    WHEN 'absent'                 THEN 'ipdb-model-absent'
  END AS rule,
  'warning' AS severity,
  ipdb_id::VARCHAR AS external_id,
  -- Only the unlinked class names a catalog record with any confidence. `absent` names
  -- none by definition, and the other two point at candidates the wide view carries with
  -- the counts that qualify them.
  CASE WHEN classification = 'catalog_holds_unlinked' AND unlinked_model_slug IS NOT NULL
       THEN 'model' END AS entity_type,
  CASE WHEN classification = 'catalog_holds_unlinked' THEN unlinked_model_slug END AS entity_public_id,
  CASE classification
    WHEN 'catalog_holds_unlinked' THEN
      format('IPDB {} "{}" matches unlinked catalog model {}; backfill the ipdb_id',
             ipdb_id, coalesce(ipdb_name, '?'), coalesce(unlinked_model_slug, '?'))
    WHEN 'possible_duplicate' THEN
      format('IPDB {} "{}" matches catalog model {}, which already links IPDB {}; read both pages',
             ipdb_id, coalesce(ipdb_name, '?'), coalesce(linked_model_slug, '?'),
             coalesce(linked_model_ipdb_id::VARCHAR, '?'))
    -- Two causes, and they read as different sentences because they ARE different
    -- situations: IPDB naming nobody can only be settled by the page, while IPDB naming
    -- a maker we hold no id for is settled at the entity, in
    -- `ipdb-corporate-entity-unknown`. A single coalesced wording collapsed them into
    -- "names maker nothing that resolves to no catalog corporate entity".
    WHEN 'maker_unresolved' THEN
      CASE WHEN ipdb_corporate_entity_text IS NULL THEN
        format('IPDB {} "{}" names no maker at all, so no candidate search ran; {}',
               ipdb_id, coalesce(ipdb_name, '?'),
               plural(n_namesake_models, 'catalog namesake', 'catalog namesakes'))
      ELSE
        format('IPDB {} "{}" names maker "{}", whose id no live corporate entity carries, so no candidate search ran; {}',
               ipdb_id, coalesce(ipdb_name, '?'), ipdb_corporate_entity_text,
               plural(n_namesake_models, 'catalog namesake', 'catalog namesakes'))
      END
    WHEN 'absent' THEN
      format('IPDB {} "{}" ({}) has no catalog model and none matches its name and maker; {} under other makers',
             ipdb_id, coalesce(ipdb_name, '?'), coalesce(ipdb_year::VARCHAR, 'undated'),
             plural(n_namesake_models, 'namesake', 'namesakes'))
  END AS message,
  'ipdb_models_unmatched' AS detail_view
FROM ipdb_models_unmatched
WHERE classification <> 'duplicate_listing';

-- ─── dead ids ──────────────────────────────────────────────────────────────
-- The one place the catalog is positively wrong rather than incomplete, and so the one
-- rule here that reaches `error` -- but only where the deletion is CONFIRMED. An
-- unexplained absence is as likely to be a crawl that missed a page as a real deletion,
-- and calling that an error would assert something the dump cannot support.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  CASE WHEN retraction_reason IS NOT NULL THEN 'ipdb-id-retracted'
       ELSE 'ipdb-id-not-in-dump' END AS rule,
  CASE WHEN retraction_reason IS NOT NULL THEN 'error' ELSE 'warning' END AS severity,
  ipdb_id::VARCHAR AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  CASE WHEN retraction_reason IS NOT NULL
    THEN format('{} cites IPDB {}, a listing IPDB has deleted; see retraction_reason', model_slug, ipdb_id)
    ELSE format('{} cites IPDB {}, absent from the merged dump with no recorded retraction; load the page', model_slug, ipdb_id)
  END AS message,
  'ipdb_ids_not_in_dump' AS detail_view
FROM ipdb_ids_not_in_dump;

-- ─── maker disagreement ────────────────────────────────────────────────────
-- `disagrees` is an error: both sides resolve to a live corporate entity and name
-- different ones, so one of them is wrong. The doc calls this structurally rare -- the
-- catalog's entities were largely seeded FROM these ids -- which is exactly why a row
-- deserves the stronger severity: it should not happen.
--
-- The other two classes are gaps. `manufacturer_differs` rides in the message because a
-- disagreement surviving the roll-up to manufacturer is a materially larger claim than
-- two incarnations of one company being confused.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  CASE classification
    WHEN 'disagrees'             THEN 'ipdb-corporate-entity-disagrees'
    WHEN 'catalog_has_none'      THEN 'ipdb-corporate-entity-missing'
    WHEN 'ipdb_entity_unmatched' THEN 'ipdb-corporate-entity-unresolved'
  END AS rule,
  CASE WHEN classification = 'disagrees' THEN 'error' ELSE 'warning' END AS severity,
  ipdb_id::VARCHAR AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  CASE classification
    WHEN 'disagrees' THEN
      format('{} is attributed to {} but IPDB names {}{}',
             model_slug, coalesce(corporate_entity_slug, '?'),
             coalesce(ipdb_corporate_entity_slug, '?'),
             CASE WHEN manufacturer_differs THEN ' — and the manufacturers differ too' ELSE '' END)
    WHEN 'catalog_has_none' THEN
      format('{} carries no corporate entity; IPDB names {}',
             model_slug, coalesce(ipdb_corporate_entity_slug, coalesce(ipdb_corporate_entity_text, '?')))
    WHEN 'ipdb_entity_unmatched' THEN
      format('{}: IPDB names maker "{}", whose id no live corporate entity carries; resolve at the entity',
             model_slug, coalesce(ipdb_corporate_entity_text, '?'))
  END AS message,
  'ipdb_model_corporate_entity_mismatched' AS detail_view
FROM ipdb_model_corporate_entity_mismatched;

-- ─── corporate entities ────────────────────────────────────────────────────
-- Entity grain, not model grain: one company the catalog holds no id for silently
-- unresolves every model IPDB files under it, and fixing it once fixes them all.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  'ipdb-corporate-entity-unknown' AS rule,
  'warning' AS severity,
  ipdb_corporate_entity_id::VARCHAR AS external_id,
  NULL::VARCHAR AS entity_type,     -- no catalog record: that is the finding
  NULL::VARCHAR AS entity_public_id,
  format('IPDB corporate entity {} "{}" is on no live catalog record; {} depend{} on it{}',
         ipdb_corporate_entity_id, coalesce(ipdb_corporate_entity_name, '?'),
         plural(n_ipdb_models, 'IPDB model', 'IPDB models'),
         CASE WHEN n_ipdb_models = 1 THEN 's' ELSE '' END,
         -- Ordered, because identity includes the message and an unordered aggregate
         -- would render the same finding differently between runs.
         CASE WHEN len(catalog_name_matches) > 0
              THEN ' — catalog names matching: ' || array_to_string(list_sort(catalog_name_matches), ', ')
              ELSE '' END) AS message,
  'ipdb_corporate_entities_unmatched' AS detail_view
FROM ipdb_corporate_entities_unmatched;

INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  'ipdb-corporate-entity-id-acquirable' AS rule,
  'warning' AS severity,
  ipdb_corporate_entity_id::VARCHAR AS external_id,
  'corporate-entity' AS entity_type,
  corporate_entity_slug AS entity_public_id,
  format('{} carries no IPDB id; IPDB appears to hold {} matching by name, e.g. {}',
         corporate_entity_slug, plural(n_ipdb_matches, 'record', 'records'),
         ipdb_corporate_entity_id) AS message,
  'corporate_entities_missing_ipdb_id' AS detail_view
FROM corporate_entities_missing_ipdb_id;

-- ─── credits ───────────────────────────────────────────────────────────────
-- Three rules over one view, split so they cannot overlap -- the audit holds its rules
-- to exact boundaries for the same reason, so that one defect is never reported twice
-- under two names. The split is on how far person resolution got, which is also what
-- decides the next action:
--
--   exactly one match  the credit can be added as it stands
--   several matches    the name reaches several people and names none of them
--   no match           the person does not exist yet, and creating them comes first --
--                      reported at PERSON grain below, not once per credit
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  CASE WHEN n_person_matches = 1 THEN 'ipdb-credit-missing'
       ELSE 'ipdb-credit-person-ambiguous' END AS rule,
  'warning' AS severity,
  ipdb_id::VARCHAR AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  CASE WHEN n_person_matches = 1
    THEN format('{} is not credited to {} as {}, which IPDB records',
                model_slug, coalesce(ipdb_person_name, '?'), coalesce(role_slug, '?'))
    ELSE format('{}: IPDB credits "{}" as {}, a name matching {} catalog people; resolve by hand',
                model_slug, coalesce(ipdb_person_name, '?'), coalesce(role_slug, '?'), n_person_matches)
  END AS message,
  'ipdb_credits_missing' AS detail_view
FROM ipdb_credits_missing
WHERE n_person_matches >= 1;

INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  'ipdb-person-unmatched' AS rule,
  'warning' AS severity,
  NULL::VARCHAR AS external_id,     -- person grain: no single IPDB id owns this
  NULL::VARCHAR AS entity_type,     -- no catalog record: that is the finding
  NULL::VARCHAR AS entity_public_id,
  format('IPDB credits "{}" on {} as {}, matching no live catalog person',
         ipdb_person_name, plural(n_models, 'model', 'models'),
         -- Already sorted by the view; spelled again here so the message's determinism
         -- does not depend on a detail of a view someone may later change.
         array_to_string(list_sort(role_slugs), ', ')) AS message,
  'ipdb_people_unmatched' AS detail_view
FROM ipdb_people_unmatched;

-- ─── specialties ───────────────────────────────────────────────────────────
-- Warnings, both. IPDB asserting a classification we lack is the catalog being
-- incomplete, not wrong -- and the archive captures behind these are typically years
-- old, which is the wrong footing for an error.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  'ipdb-specialty-missing' AS rule,
  'warning' AS severity,
  ipdb_id::VARCHAR AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  format('{} does not carry {} {}, which IPDB lists as specialty "{}" (captured {})',
         model_slug, target_entity_type, target_value, specialty,
         coalesce(archive_capture_date::VARCHAR, 'undated')) AS message,
  'ipdb_model_specialties_missing' AS detail_view
FROM ipdb_model_specialties_missing;

-- Specialty grain: one row is one vocabulary decision. `external_id` is NULL because no
-- single IPDB listing owns the question, and `entity_type` is NULL because the record
-- whose absence is the finding cannot be named.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'ipdb' AS source,
  'ipdb-specialty-vocabulary-absent' AS rule,
  'warning' AS severity,
  NULL::VARCHAR AS external_id,
  NULL::VARCHAR AS entity_type,
  NULL::VARCHAR AS entity_public_id,
  -- "e.g." only when the sample is actually a sample: the list caps at 5, so at or
  -- below that it IS the population and hedging it would understate what is known.
  format('IPDB specialty "{}" maps to {} "{}", which the catalog does not have; {} affected: {}{}',
         specialty, target_entity_type, ipdb_wording,
         plural(n_models, 'model', 'models'),
         CASE WHEN n_models > 5 THEN 'e.g. ' ELSE '' END,
         array_to_string(sample_model_slugs, ', ')) AS message,
  'ipdb_specialty_vocabulary_absent' AS detail_view
FROM ipdb_specialty_vocabulary_absent;

-- ═══ SUMMARY & CHECKS ══════════════════════════════════════════════════════

CREATE OR REPLACE VIEW ipdb_summary AS
  SELECT 'unmatched_' || classification AS metric, count(*) AS value
  FROM ipdb_models_unmatched GROUP BY classification
  UNION ALL SELECT 'catalog_ids_not_in_dump', count(*) FROM ipdb_ids_not_in_dump
  UNION ALL SELECT 'corporate_entity_' || classification, count(*)
    FROM ipdb_model_corporate_entity_mismatched GROUP BY classification
  UNION ALL SELECT 'ipdb_corporate_entities_unmatched', count(*) FROM ipdb_corporate_entities_unmatched
  UNION ALL SELECT 'corporate_entities_missing_ipdb_id', count(*) FROM corporate_entities_missing_ipdb_id
  UNION ALL SELECT 'models_without_corporate_entity', count(*) FROM models WHERE corporate_entity_slug IS NULL
  UNION ALL SELECT 'credits_missing', count(*) FROM ipdb_credits_missing
  UNION ALL SELECT 'people_unmatched', count(*) FROM ipdb_people_unmatched
  UNION ALL SELECT 'dump_models', count(*) FROM px.ipdb.models
  UNION ALL SELECT 'dump_credits', count(*) FROM px.ipdb.credits
  UNION ALL SELECT 'catalog_models_with_ipdb_id', count(*) FROM models WHERE ipdb_id IS NOT NULL
  UNION ALL SELECT 'specialty_assignments', count(*) FROM px.ipdb.model_specialties
  UNION ALL SELECT 'specialty_models_covered', count(DISTINCT ipdb_id) FROM px.ipdb.model_specialties
  UNION ALL SELECT 'specialty_carried', count(*) FROM _eds_ipdb_specialties WHERE carried
  UNION ALL SELECT 'specialty_missing', count(*) FROM ipdb_model_specialties_missing
  UNION ALL SELECT 'specialty_vocabulary_absent', count(*) FROM ipdb_specialty_vocabulary_absent
  -- The findings rollup, so `run` shows the headline without a second query. Counted off
  -- the live worklist, so a dismissal is reflected here too.
  UNION ALL SELECT 'FINDINGS errors', count(*)
    FROM external_data_source_findings WHERE source = 'ipdb' AND severity = 'error'
  UNION ALL SELECT 'FINDINGS warnings', count(*)
    FROM external_data_source_findings WHERE source = 'ipdb' AND severity = 'warning'
  UNION ALL SELECT 'FINDINGS dismissed', count(*)
    FROM external_data_source_findings_all WHERE source = 'ipdb' AND dismissed
  ORDER BY metric;
COMMENT ON VIEW ipdb_summary IS
  'Headline counts for the IPDB comparison — the unmatched set by classification, the credit gap, and the totals both sides are measured against.';

-- Empty when healthy. Invariants of this layer, never findings about the data.
CREATE OR REPLACE VIEW ipdb_checks AS
  -- The catalog-side join key of `_eds_ipdb_dump`. Not unique by construction, and a
  -- second row would multiply every count taken off the dump.
  SELECT 'corporate_entity_ipdb_id_not_unique' AS check_name,
         ipdb_manufacturer_id::VARCHAR AS detail
  FROM corporate_entities
  WHERE ipdb_manufacturer_id IS NOT NULL
  GROUP BY ipdb_manufacturer_id HAVING count(*) > 1

  UNION ALL
  -- The aggregation in `_eds_ipdb_candidates` is what holds the worklist at one row per
  -- listing; if it ever stops, the classification silently double-counts.
  SELECT 'unmatched_not_one_row_per_listing', ipdb_id::VARCHAR
  FROM ipdb_models_unmatched GROUP BY ipdb_id HAVING count(*) > 1

  UNION ALL
  -- A classification outside the closed set means the CASE grew a branch the consumers
  -- of this view do not know how to answer.
  SELECT 'classification_unknown', classification
  FROM ipdb_models_unmatched
  WHERE classification NOT IN
    ('duplicate_listing', 'catalog_holds_unlinked', 'possible_duplicate',
     'maker_unresolved', 'absent')

  UNION ALL
  -- `absent` is the one classification that ASSERTS something about the catalog rather
  -- than reporting what was found, and it is only true if a search ran. A search needs a
  -- maker on both sides, so a row reaching `absent` without one is the classification
  -- claiming a machine is missing that nobody looked for. That is exactly the bug
  -- `maker_unresolved` was added for, and this is its regression guard.
  SELECT 'absent_without_maker_search', u.ipdb_id::VARCHAR
  FROM ipdb_models_unmatched AS u
  WHERE u.classification = 'absent'
    AND u.ipdb_manufacturer_slug IS NULL

  UNION ALL
  -- The namesake join is a per-listing aggregate and must not fan the worklist out.
  SELECT 'namesakes_not_one_row_per_listing', ipdb_id::VARCHAR
  FROM _eds_ipdb_namesakes GROUP BY ipdb_id HAVING count(*) > 1

  UNION ALL
  -- The CASE precedence. A confirmed duplicate also matches the `possible_duplicate`
  -- shape by construction, so a branch reordered above it would silently demote these
  -- and they would read as work to do. There is no join left to break -- the fact is a
  -- column on the mart row -- so this tests the ordering alone.
  SELECT 'confirmed_duplicate_misclassified', u.ipdb_id::VARCHAR
  FROM ipdb_models_unmatched AS u
  WHERE u.duplicate_of_ipdb_id IS NOT NULL
    AND u.classification <> 'duplicate_listing'

  UNION ALL
  -- The pairing points at the listing the catalog is expected to hold instead. If that
  -- one is missing too, the row is no longer explaining anything away.
  SELECT 'duplicate_target_not_in_catalog', d.duplicate_of_ipdb_id::VARCHAR
  FROM _eds_ipdb_dump AS d
  WHERE d.duplicate_of_ipdb_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM models AS m WHERE m.ipdb_id = d.duplicate_of_ipdb_id)

  UNION ALL
  -- A credit role that names nothing in the catalog's vocabulary matches no catalog
  -- credit either, so every credit carrying it reports as missing forever. Catches both
  -- a dump field pinexplore has not mapped and a role the catalog has renamed.
  SELECT 'credit_role_not_in_vocabulary', detail
  FROM (
    SELECT DISTINCT coalesce(c.role_slug, '<unmapped ' || c.ipdb_role || '>') AS detail
    FROM _eds_ipdb_credits AS c
    WHERE c.role_slug IS NULL
       OR NOT EXISTS (SELECT 1 FROM credit_roles AS cr WHERE cr.slug = c.role_slug)
  )

  UNION ALL
  -- The corporate-entity worklist is one row per model, so the decode in
  -- `_eds_ipdb_dump` must stay a lookup rather than becoming a fan-out.
  SELECT 'corporate_entity_mismatch_not_one_row_per_model', ipdb_id::VARCHAR
  FROM ipdb_model_corporate_entity_mismatched GROUP BY ipdb_id HAVING count(*) > 1

  UNION ALL
  -- A classification outside the closed set.
  SELECT 'corporate_entity_classification_unknown', classification
  FROM ipdb_model_corporate_entity_mismatched
  WHERE classification NOT IN ('catalog_has_none', 'ipdb_entity_unmatched', 'disagrees')

  UNION ALL
  -- Person resolution is a lookup, so it must leave the credit grain alone.
  SELECT 'credits_not_one_row_per_dump_credit',
         (SELECT count(*) FROM px.ipdb.credits)::VARCHAR || ' dump credits -> '
           || (SELECT count(*) FROM _eds_ipdb_credits)::VARCHAR || ' resolved'
  WHERE (SELECT count(*) FROM _eds_ipdb_credits)
      > (SELECT count(*) FROM px.ipdb.credits)

  UNION ALL
  -- THE CHECK PINEXPLORE DELEGATES: whether a public_id exists is a question only the
  -- catalog answers. A mapping naming a slug we have since re-slugged would otherwise
  -- report every model carrying that specialty as a permanent gap, or drop it from the
  -- worklist entirely, with nothing else here noticing.
  --
  -- SCOPED BY SPELLING, which is the convention pinexplore writes these in: a
  -- slug-shaped target is one it expects to resolve, and IPDB's display wording --
  -- `Payout Machine`, `Not A Pinball` -- marks vocabulary the catalog is known not to
  -- have yet. Those belong to `specialty_vocabulary_absent` below, and firing on them
  -- here would report the entire backlog as a fault every run. The test is on the
  -- string, so it stays answerable here.
  SELECT 'specialty_target_not_in_catalog',
         specialty || ' -> ' || target_entity_type || '.' || target_value
  FROM _eds_ipdb_specialties
  WHERE regexp_full_match(target_value, '[a-z0-9][a-z0-9_-]*') AND NOT target_exists
  GROUP BY ALL

  UNION ALL
  -- The carriage CASE has no ELSE, so a target_entity_type nobody wrote a branch for
  -- lands NULL rather than being silently reported as a gap. This is what turns that
  -- into a loud failure. It fires the day pinexplore maps a specialty onto an entity
  -- type this file has never seen.
  SELECT 'specialty_carriage_unhandled', target_entity_type
  FROM _eds_ipdb_specialties
  WHERE model_slug IS NOT NULL AND carried IS NULL
  GROUP BY ALL

  UNION ALL
  -- The specialty worklist is one row per (listing, specialty); the join to `models` is
  -- a lookup and must not fan it out.
  SELECT 'specialty_not_one_row_per_assignment',
         ipdb_id::VARCHAR || ' / ' || specialty
  FROM _eds_ipdb_specialties
  GROUP BY ipdb_id, specialty HAVING count(*) > 1

  UNION ALL
  -- A closed vocabulary, and the anchor for the whole section: if pinexplore's rule
  -- table were emptied or the join silently produced nothing, every specialty view
  -- would go quiet and read exactly like a catalog that already carries everything.
  SELECT 'specialty_rules_missing', 'px.ipdb.specialties is empty'
  WHERE (SELECT count(*) FROM px.ipdb.specialties) = 0;
COMMENT ON VIEW ipdb_checks IS
  'Empty when healthy — grain, closed vocabulary and duplicate-list anchors for the IPDB comparison, plus the specialty-target resolution pinexplore delegates here.';
