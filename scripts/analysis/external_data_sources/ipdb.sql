-- IPDB against the catalog: which listings we hold, and which credits we are missing.
--
-- `.read` this from a campaign analysis after flipcommons' foundation:
--
--     .read ../flippatch/scripts/analysis/external_data_sources/ipdb.sql
--
-- It reads `assertions.sql` itself — which reads `identity.sql` (the decode of
-- IPDB's dump, the model-matching ladder and the known-good replay, run once for
-- both sources), which reads `bridge.sql` — so the attach, the watermark and every
-- shared invariant come with it. This file holds what is IPDB's alone: the worklist
-- in IPDB's terms, corporate entities (IPDB's maker grain), credits, specialties,
-- and their findings. The worklists below return rows on a healthy catalog.

.read ../flippatch/scripts/analysis/external_data_sources/assertions.sql

-- WORKLIST — IPDB listings with no catalog model, and what each one actually is.
--
-- The classification is `identity.sql`'s (`_eds_models_unmatched`; the mechanics — tiers,
-- the verdict discipline, the year triangle — are documented there). "No model
-- carries this IPDB id" is one condition covering several situations that want
-- different responses, and reading them all as gaps overstates the work by roughly
-- half. The classes as they read on this side:
--
--   duplicate_listing       IPDB lists this model twice under two of its own maker
--                           records; the catalog links the other id. Nothing to do.
--                           Confirmed cases only, carried on the mart row itself;
--                           pinexplore's `ipdb_ref.duplicate_listings` records the
--                           reasoning and the two URLs it rests on.
--   catalog_holds_unlinked  The search resolved UNIQUELY to a model with no IPDB id
--                           AND the year corroborates. A backfill: patch the id, do
--                           not create a record.
--   possible_duplicate      The search resolved uniquely, year corroborated, to a
--                           model already linked to a DIFFERENT IPDB id. Either an
--                           unrecorded duplicate listing, or two genuinely different
--                           machines. Needs both IPDB pages read before it can move.
--   year_unverified         Exactly one model answers, but the year triangle CANNOT
--                           CLOSE -- the listing or the catalog model is undated --
--                           so the match is unproven and linking it would be a guess
--                           (the identity doc's NEVER-GUESS rule). Find the year,
--                           date the undated side, then link.
--   multiple_candidates     MORE than one model answers the name and maker, so the
--                           search answers plurally: `candidate_model_slugs` lists
--                           them. Adjudicate before patching; no arbitrary candidate
--                           is ever presented as the answer.
--   year_conflict           Every name-and-maker match is refuted by the year
--                           triangle: more than a year from the catalog's dates.
--                           Either a wrong year on one side or a different era's
--                           machine -- `year_refuted_models` lists them with their
--                           years. Read the pages; do not create a record blind.
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
-- `carried_forward` is worth reading before acting on an `absent` row: it marks a record
-- the newest scrape missed, served from an older snapshot, so the listing may no longer
-- exist upstream at all.
CREATE OR REPLACE VIEW ipdb_models_unmatched AS
  SELECT
    d.ipdb_id,
    d.ipdb_name,
    d.ipdb_date_year,
    d.ipdb_date_kind,
    d.ipdb_corporate_entity_text,
    d.ipdb_manufacturer_slug,
    u.classification,
    d.duplicate_of_ipdb_id,
    u.unlinked_model_slug,
    u.linked_model_slug,
    u.linked_model_external_id::BIGINT AS linked_model_ipdb_id,
    u.linked_model_production_year,
    u.resolved_year_verdict,
    u.n_candidates,
    u.candidate_model_slugs,
    u.n_year_refuted,
    u.year_refuted_models,
    -- Name-only evidence, carried on every row rather than only the unsearchable ones:
    -- a namesake under a DIFFERENT maker is worth seeing before creating a record, and
    -- an `absent` row with namesakes is the shape a mis-attributed listing takes.
    u.n_namesake_models,
    u.namesake_model_slugs,
    d.carried_forward
  FROM _eds_models_unmatched AS u
  INNER JOIN _eds_ipdb_dump AS d ON d.ipdb_id::VARCHAR = u.external_id
  WHERE u.source = 'ipdb';
COMMENT ON VIEW ipdb_models_unmatched IS
  'Worklist — one row per IPDB listing no live model carries the id of, classified as duplicate_listing / catalog_holds_unlinked / possible_duplicate / multiple_candidates / year_unverified / year_conflict / maker_unresolved / absent, with the resolved model where exactly one answered, the sorted candidate list where several did, the year-refuted list where the triangle disagreed, and a namesake count where no search could run. Rows are expected.';

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
    m.production_year,
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
      -- `first` ordered by the id `min` picked, so the published pair names ONE IPDB
      -- record -- deterministically and NULLs included, for the reasons on the
      -- identity resolution.
      min(ipdb_corporate_entity_id)     AS ipdb_corporate_entity_id,
      first(corporate_entity_text ORDER BY ipdb_corporate_entity_id) AS ipdb_corporate_entity_text
    FROM px.ipdb.corporate_entities
    GROUP BY 1
  ) AS i ON i.name_key = name_norm(c.name)
  WHERE c.ipdb_manufacturer_id IS NULL;
COMMENT ON VIEW corporate_entities_missing_ipdb_id IS
  'Worklist — one row per live corporate entity with no IPDB id that IPDB now appears to hold a record for, matched by name. Empty when there is nothing to acquire.';

-- Every string that names a live person, folded once, so a credit can be resolved
-- without joining the whole name pool per row. One norm can name two different people,
-- and a credit resolved to an arbitrary one of them is worse than one left unresolved
-- -- so `person_id` fills ONLY when the name names exactly one person (the verdict
-- discipline of the model-matching ladder), and an ambiguous name resolves nobody:
-- its credits stay in the missing worklist carrying `n_people` as the explanation.
CREATE OR REPLACE VIEW _eds_person_by_name AS
  SELECT name_norm(name) AS person_name_norm,
         count(DISTINCT entity_id) AS n_people,
         CASE WHEN count(DISTINCT entity_id) = 1
              THEN min(entity_id) END AS person_id
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
  FROM px.ipdb.model_credits AS c
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
-- pinexplore buckets each IPDB specialty onto one of OUR entity types and publishes the
-- rules whole in `px.ipdb.specialties`, including the ones aimed at vocabulary we do not
-- have. Its reference file states the division of labour outright: `target_value` "IS
-- NEVER A CLAIM ABOUT THE CATALOG ... pinexplore reads no catalog and cannot know
-- whether a value resolves; flippatch answers that beside the live records."
--
-- SO BOTH HALVES OF THE ANSWER ARE OURS. `target_slug` resolves the wording onto a
-- record, through our aliases where the vocabulary has them, and
-- `specialty_target_not_in_catalog` below fails when a value that ought to resolve does
-- not. That is the reason this section exists at all rather than the mapping being
-- trusted end to end.
--
-- Its converse is `specialty_vocabulary_absent`, a worklist rather than a gate: a target
-- pinexplore spells in IPDB's own wording -- `Payout Machine`, `Not A Pinball` -- is one
-- nobody has catalog vocabulary for yet, and is a decision waiting rather than a fault.
--
-- Coverage is archive-sourced and therefore partial: only a small fraction of IPDB
-- listings have a cached page to read a Specialty off. A model with no row here has not
-- been checked, not been cleared -- and `specialty_listings_covered` in the summary is how
-- many have, which is the number to read rather than one written down here.

-- One row per (IPDB model, specialty): IPDB's slice of the unified assertion layer
-- (`assertions.sql` — the resolution lookup, the carriage CASE and their reasoning
-- live there, once for both sources), in the columns this file's worklists and
-- partition checks read. Pinexplore used to ship a flag pre-answering existence; it
-- no longer does, and should not have: whether our catalog holds a value is ours to
-- answer, and `target_slug` / `target_exists` are that answer.
CREATE OR REPLACE VIEW _eds_ipdb_specialties AS
  SELECT
    external_id::BIGINT AS ipdb_id,
    assertion_label     AS specialty,
    target_entity_type,
    target_value,
    target_slug,
    source_url,
    observed_on,
    model_id,
    model_slug,
    model_name,
    target_exists,
    carried
  FROM _eds_external_assertions
  WHERE source = 'ipdb';

-- WORKLIST — IPDB asserts a classification the catalog has the vocabulary for and the
-- model does not carry.
--
-- The actionable payload: each row is a patch waiting to be written, with the search
-- that evidences it. `source_url` is the advanced-search listing the assignment was
-- read from -- per specialty, not per model -- and `observed_on` is the one date the
-- whole census was taken. Unlike the archive captures this replaced, the evidence is
-- a current read rather than one typically years old.
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
    -- `target_slug` is what a patch asserts -- the resolved catalog record, NULL only on
    -- the structural model-relationship rows. `target_value` is IPDB's wording, kept for
    -- tracing back to the source; writing IT into a patch fails to resolve or mints a
    -- duplicate term.
    target_slug,
    target_value,
    source_url,
    observed_on,
    'https://www.ipdb.org/machine.cgi?id=' || ipdb_id AS ipdb_url
  FROM _eds_ipdb_specialties
  WHERE model_slug IS NOT NULL
    AND target_exists
    AND NOT carried;
COMMENT ON VIEW ipdb_model_specialties_missing IS
  'Worklist — one row per IPDB specialty the catalog has vocabulary for but the model does not carry: target_slug is the record a patch asserts, with the advanced search it was read from and the census date behind it. Rows are expected.';

-- WORKLIST — an IPDB specialty aimed at vocabulary the catalog does not have.
--
-- SPECIALTY GRAIN, not model grain, and that is the whole point. Each row is ONE
-- decision -- add the tag, split the payout type, work out what "Not A Pinball" should
-- be -- not one decision per machine, and reported per model it would restate the same
-- handful of questions dozens of times over.
--
-- THREE SHAPES SIT HERE TOGETHER.
--
-- Some are IPDB headings coarser than ours that no new term would fix: `Payout Machine`
-- spans our `cash-payout` and `merchant-paid`, `Table Top/Counter Game` spans `tabletop`
-- and `countertop`. Those need the models read, not a slug minted.
--
-- Some are vocabulary we may simply want and do not have, which pinexplore spells in
-- IPDB's own wording so it reads at a glance as work outstanding.
--
-- And some are vocabulary we DO have under another name, where the alias is what is
-- missing rather than the term: `Mechanical Backbox Animation` against our
-- `mechanical-backbox-animations`. `target_slug` resolves through our aliases, so a row
-- landing here is partly a question about whether we have the concept and partly one
-- about whether we have taught it the source's phrasing.
--
-- A target pinexplore spells as a SLUG is making the opposite claim -- that it expects
-- to resolve -- so it fails `specialty_target_not_in_catalog` instead of waiting here.
CREATE OR REPLACE VIEW ipdb_specialty_vocabulary_absent AS
  SELECT
    specialty,
    target_entity_type,
    target_value              AS ipdb_wording,
    count(*)                  AS n_models,
    -- Ordered: this reaches a finding message, kept deterministic so two runs render
    -- the same finding identically.
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
-- dismissal rules. Each INSERT joins the RULE REGISTRY (`_eds_rule_registry`, in
-- `bridge.sql`) on the class it projects and inherits rule name, stage, severity and
-- detail view from there — the registry is the vocabulary's one home, and an excluded
-- class is a registry row with its reason, never a WHERE clause here. What stays in
-- each block is what is irreducibly the rule's own: the identity expressions
-- (external id, catalog record, discriminator) and the message wording.
--
-- SEVERITY (recorded per class in the registry). The bar for `error` is the doc's: OUR
-- DATA IS CURRENTLY WRONG. A gap is not an error -- a listing we have not linked, a
-- credit we have not recorded and a maker we hold no id for are all things the catalog
-- does not YET say, and the catalog being incomplete is its normal condition. What
-- earns `error` is the catalog making a positive claim the source contradicts: a dead
-- IPDB id still cited, or two live records that resolve and disagree.
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
-- One rule per classification rather than one rule for the view, because the classes
-- ask for different actions and a dismissal keys on the rule. `duplicate_listing`
-- produces no finding — the registry row carries why — and stays visible in the wide
-- view.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  ipdb_id::VARCHAR AS external_id,
  -- Only the unlinked class names a catalog record with any confidence. `absent` names
  -- none by definition, and the other two point at candidates the wide view carries with
  -- the counts that qualify them.
  CASE WHEN w.classification = 'catalog_holds_unlinked' AND unlinked_model_slug IS NOT NULL
       THEN 'model' END AS entity_type,
  CASE WHEN w.classification = 'catalog_holds_unlinked' THEN unlinked_model_slug END AS entity_public_id,
  -- The identity-completing substance, per class: the answer or candidate set whose
  -- change should lapse a dismissal. NULL where the listing id says everything.
  CASE w.classification
    WHEN 'possible_duplicate'  THEN linked_model_slug
    WHEN 'multiple_candidates' THEN array_to_string(candidate_model_slugs, ', ')
    WHEN 'year_unverified'     THEN coalesce(unlinked_model_slug, linked_model_slug)
    WHEN 'year_conflict'       THEN array_to_string(year_refuted_models, ', ')
  END AS discriminator,
  CASE w.classification
    WHEN 'catalog_holds_unlinked' THEN
      format('IPDB {} "{}" matches unlinked catalog model {}; backfill the ipdb_id',
             ipdb_id, coalesce(ipdb_name, '?'), coalesce(unlinked_model_slug, '?'))
    WHEN 'possible_duplicate' THEN
      format('IPDB {} "{}" matches catalog model {}, which already links IPDB {}; read both pages',
             ipdb_id, coalesce(ipdb_name, '?'), coalesce(linked_model_slug, '?'),
             coalesce(linked_model_ipdb_id::VARCHAR, '?'))
    WHEN 'multiple_candidates' THEN
      -- The plural answer, listed and never picked from. The list is sorted at the
      -- source and capped at 5; `n_candidates` is the true count.
      format('IPDB {} "{}" matches {} by name and maker ({}); adjudicate before patching',
             ipdb_id, coalesce(ipdb_name, '?'),
             plural(n_candidates, 'catalog model', 'catalog models'),
             array_to_string(candidate_model_slugs, ', '))
    WHEN 'year_unverified' THEN
      format('IPDB {} "{}" ({}) matches {}{} by name and maker, but {}, so the match is unproven; find the year, date the undated side, then link',
             ipdb_id, coalesce(ipdb_name, '?'),
             coalesce(ipdb_date_year::VARCHAR, 'undated'),
             coalesce(unlinked_model_slug, linked_model_slug),
             coalesce(' (links IPDB ' || linked_model_ipdb_id::VARCHAR || ')', ''),
             CASE WHEN ipdb_date_year IS NULL THEN 'the IPDB listing states no year'
                  ELSE 'the catalog model is undated' END)
    WHEN 'year_conflict' THEN
      format('IPDB {} "{}" ({}) matches {} by name and maker but more than a year off ({}); read the pages -- a wrong year on one side, or a different era''s machine',
             ipdb_id, coalesce(ipdb_name, '?'),
             coalesce(ipdb_date_year::VARCHAR, 'undated'),
             plural(n_year_refuted, 'catalog model', 'catalog models'),
             array_to_string(year_refuted_models, ', '))
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
      -- The kind qualifies the year: a project year rendered bare would read as a
      -- manufacture year, which is the confusion `ipdb_date_kind` exists to prevent.
      format('IPDB {} "{}" ({}) has no catalog model and none matches its name and maker; {} under other makers',
             ipdb_id, coalesce(ipdb_name, '?'),
             coalesce(ipdb_date_year::VARCHAR ||
                      CASE WHEN ipdb_date_kind IN ('project', 'project_inferred')
                           THEN ' project' ELSE '' END, 'undated'),
             plural(n_namesake_models, 'namesake', 'namesakes'))
  END AS message
FROM ipdb_models_unmatched AS w
INNER JOIN _eds_rule_registry AS reg
  ON  reg.detail_view = 'ipdb_models_unmatched'
  AND reg.classification = w.classification
WHERE reg.rule IS NOT NULL;

-- ─── dead ids ──────────────────────────────────────────────────────────────
-- The one place the catalog is positively wrong rather than incomplete, and so the one
-- rule here that reaches `error` -- but only where the deletion is CONFIRMED. An
-- unexplained absence is as likely to be a crawl that missed a page as a real deletion,
-- and calling that an error would assert something the dump cannot support.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  ipdb_id::VARCHAR AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  NULL::VARCHAR AS discriminator,
  CASE WHEN retraction_reason IS NOT NULL
    THEN format('{} cites IPDB {}, a listing IPDB has deleted; see retraction_reason', model_slug, ipdb_id)
    ELSE format('{} cites IPDB {}, absent from the merged dump with no recorded retraction; load the page', model_slug, ipdb_id)
  END AS message
FROM ipdb_ids_not_in_dump
INNER JOIN _eds_rule_registry AS reg
  ON  reg.detail_view = 'ipdb_ids_not_in_dump'
  -- The class is derived here rather than carried on the view: the CASE is total, so
  -- it cannot mint a class the registry lacks.
  AND reg.classification = CASE WHEN retraction_reason IS NOT NULL
                                THEN 'retracted' ELSE 'unexplained' END
WHERE reg.rule IS NOT NULL;

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
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  ipdb_id::VARCHAR AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  -- Both sides of the disagreement: the situation changes when either does.
  coalesce(corporate_entity_slug, '-') || ' vs '
    || coalesce(ipdb_corporate_entity_slug, ipdb_corporate_entity_text, '-') AS discriminator,
  CASE w.classification
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
  END AS message
FROM ipdb_model_corporate_entity_mismatched AS w
INNER JOIN _eds_rule_registry AS reg
  ON  reg.detail_view = 'ipdb_model_corporate_entity_mismatched'
  AND reg.classification = w.classification
WHERE reg.rule IS NOT NULL;

-- ─── corporate entities ────────────────────────────────────────────────────
-- Entity grain, not model grain: one company the catalog holds no id for silently
-- unresolves every model IPDB files under it, and fixing it once fixes them all.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  ipdb_corporate_entity_id::VARCHAR AS external_id,
  NULL::VARCHAR AS entity_type,     -- no catalog record: that is the finding
  NULL::VARCHAR AS entity_public_id,
  NULL::VARCHAR AS discriminator,
  format('IPDB corporate entity {} "{}" is on no live catalog record; {} depend{} on it{}',
         ipdb_corporate_entity_id, coalesce(ipdb_corporate_entity_name, '?'),
         plural(n_ipdb_models, 'IPDB model', 'IPDB models'),
         CASE WHEN n_ipdb_models = 1 THEN 's' ELSE '' END,
         -- Ordered: messages are kept deterministic, and an unordered aggregate would
         -- render the same finding differently between runs.
         CASE WHEN len(catalog_name_matches) > 0
              THEN ' — catalog names matching: ' || array_to_string(list_sort(catalog_name_matches), ', ')
              ELSE '' END) AS message
FROM ipdb_corporate_entities_unmatched AS u
INNER JOIN _eds_rule_registry AS reg
  ON reg.detail_view = 'ipdb_corporate_entities_unmatched' AND reg.classification IS NULL
-- Deduplication, matching the OPDB twin — a per-ROW predicate, not a class exclusion,
-- so it stays here rather than in the registry: where the id-acquirable rule below
-- fired for this id, both rules describe the same missing link from opposite ends, and
-- the acquirable side survives because it names a catalog record. Guarded on that rule
-- actually firing, never on a name match alone. The wide view keeps every row.
WHERE reg.rule IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM corporate_entities_missing_ipdb_id AS a
                  WHERE a.ipdb_corporate_entity_id = u.ipdb_corporate_entity_id);

INSERT INTO _external_data_source_findings BY NAME
SELECT
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  ipdb_corporate_entity_id::VARCHAR AS external_id,
  'corporate-entity' AS entity_type,
  corporate_entity_slug AS entity_public_id,
  NULL::VARCHAR AS discriminator,
  -- "e.g." only when the id is actually an example: with one match it IS the record.
  CASE WHEN n_ipdb_matches = 1
    THEN format('{} carries no IPDB id; IPDB record {} matches it by name',
                corporate_entity_slug, ipdb_corporate_entity_id)
    ELSE format('{} carries no IPDB id; {} match it by name, e.g. record {}',
                corporate_entity_slug, plural(n_ipdb_matches, 'IPDB record', 'IPDB records'),
                ipdb_corporate_entity_id)
  END AS message
FROM corporate_entities_missing_ipdb_id
INNER JOIN _eds_rule_registry AS reg
  ON reg.detail_view = 'corporate_entities_missing_ipdb_id' AND reg.classification IS NULL
WHERE reg.rule IS NOT NULL;

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
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  ipdb_id::VARCHAR AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  -- A model carries many credits: the credit's own key completes the identity.
  coalesce(role_slug, '?') || ' / ' || coalesce(ipdb_person_name, '?') AS discriminator,
  CASE WHEN n_person_matches = 1
    THEN format('{} is not credited to {} as {}, which IPDB records',
                model_slug, coalesce(ipdb_person_name, '?'), coalesce(role_slug, '?'))
    ELSE format('{}: IPDB credits "{}" as {}, a name matching {} catalog people; resolve by hand',
                model_slug, coalesce(ipdb_person_name, '?'), coalesce(role_slug, '?'), n_person_matches)
  END AS message
FROM ipdb_credits_missing
INNER JOIN _eds_rule_registry AS reg
  ON  reg.detail_view = 'ipdb_credits_missing'
  -- The class is derived here; the CASE is total, so it cannot mint an unregistered
  -- class, and the unmatched-person class routes to no rule (covered at person grain).
  AND reg.classification = CASE WHEN n_person_matches = 1 THEN 'person_resolved'
                                WHEN n_person_matches > 1 THEN 'person_ambiguous'
                                ELSE 'person_unmatched' END
WHERE reg.rule IS NOT NULL;

INSERT INTO _external_data_source_findings BY NAME
SELECT
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  NULL::VARCHAR AS external_id,     -- person grain: no single IPDB id owns this
  NULL::VARCHAR AS entity_type,     -- no catalog record: that is the finding
  NULL::VARCHAR AS entity_public_id,
  -- Person grain with no record-level keys at all: the name IS the identity.
  ipdb_person_name AS discriminator,
  format('IPDB credits "{}" on {} as {}, matching no live catalog person',
         ipdb_person_name, plural(n_models, 'model', 'models'),
         -- Already sorted by the view; spelled again here so the message's determinism
         -- does not depend on a detail of a view someone may later change.
         array_to_string(list_sort(role_slugs), ', ')) AS message
FROM ipdb_people_unmatched
INNER JOIN _eds_rule_registry AS reg
  ON reg.detail_view = 'ipdb_people_unmatched' AND reg.classification IS NULL
WHERE reg.rule IS NOT NULL;

-- ─── specialties ───────────────────────────────────────────────────────────
-- Warnings, both. IPDB asserting a classification we lack is the catalog being
-- incomplete, not wrong -- and the archive captures behind these are typically years
-- old, which is the wrong footing for an error.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  ipdb_id::VARCHAR AS external_id,
  'model' AS entity_type,
  model_slug AS entity_public_id,
  -- A model carries many specialties: the assertion's own key completes the identity.
  specialty || ' / ' || coalesce(target_slug, target_value) AS discriminator,
  -- The resolved slug, not IPDB's wording -- the slug is what the patch asserts. The
  -- structural model-relationship rows have no slug and fall back to the edge type.
  format('{} does not carry {} {}, which IPDB lists as specialty "{}" (observed {})',
         model_slug, target_entity_type, coalesce(target_slug, target_value), specialty,
         coalesce(observed_on::VARCHAR, 'undated')) AS message
FROM ipdb_model_specialties_missing
INNER JOIN _eds_rule_registry AS reg
  ON reg.detail_view = 'ipdb_model_specialties_missing' AND reg.classification IS NULL
WHERE reg.rule IS NOT NULL;

-- Specialty grain: one row is one vocabulary decision. `external_id` is NULL because no
-- single IPDB listing owns the question, and `entity_type` is NULL because the record
-- whose absence is the finding cannot be named.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  reg.source, reg.resolution_stage, reg.rule, reg.severity, reg.detail_view,
  NULL::VARCHAR AS external_id,
  NULL::VARCHAR AS entity_type,
  NULL::VARCHAR AS entity_public_id,
  -- Value grain with no record-level keys at all: the value IS the identity.
  specialty || ' / ' || target_entity_type || ' / ' || ipdb_wording AS discriminator,
  -- "e.g." only when the sample is actually a sample: the list caps at 5, so at or
  -- below that it IS the population and hedging it would understate what is known.
  format('IPDB specialty "{}" maps to {} "{}", which the catalog does not have; {} affected: {}{}',
         specialty, target_entity_type, ipdb_wording,
         plural(n_models, 'model', 'models'),
         CASE WHEN n_models > 5 THEN 'e.g. ' ELSE '' END,
         array_to_string(sample_model_slugs, ', ')) AS message
FROM ipdb_specialty_vocabulary_absent
INNER JOIN _eds_rule_registry AS reg
  ON reg.detail_view = 'ipdb_specialty_vocabulary_absent' AND reg.classification IS NULL
WHERE reg.rule IS NOT NULL;

-- ═══ SUMMARY & CHECKS ══════════════════════════════════════════════════════

-- Metric names carry their grain, per the bridge header. The specialty family is a
-- PARTITION of `specialty_assignments`: carried + missing + vocabulary-absent +
-- on-unmatched-listings sums to it exactly, so a reader who notices a gap has found a
-- bug, not an undocumented exclusion.
CREATE OR REPLACE VIEW ipdb_summary AS
  SELECT 'unmatched_listings_' || classification AS metric, count(*) AS value
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
  UNION ALL SELECT 'dump_credits', count(*) FROM px.ipdb.model_credits
  UNION ALL SELECT 'catalog_models_with_ipdb_id', count(*) FROM models WHERE ipdb_id IS NOT NULL
  UNION ALL SELECT 'specialty_assignments', count(*) FROM px.ipdb.model_specialties
  UNION ALL SELECT 'specialty_listings_covered', count(DISTINCT ipdb_id) FROM px.ipdb.model_specialties
  -- The coverage cliff, beside the covered count where it cannot be missed: specialty
  -- data is archive-sourced and reaches ~2% of listings. A model with no row has NOT
  -- BEEN CHECKED, not been cleared -- without this number, the small `missing` count
  -- reads as near-complete classification, which inverts the truth.
  UNION ALL SELECT 'specialty_listings_unchecked', count(*) FROM px.ipdb.models AS im
    WHERE NOT EXISTS (SELECT 1 FROM px.ipdb.model_specialties AS s WHERE s.ipdb_id = im.ipdb_id)
  UNION ALL SELECT 'specialty_carried_assignments', count(*) FROM _eds_ipdb_specialties WHERE carried
  UNION ALL SELECT 'specialty_missing_assignments', count(*) FROM ipdb_model_specialties_missing
  UNION ALL SELECT 'specialty_vocabulary_absent_values', count(*) FROM ipdb_specialty_vocabulary_absent
  UNION ALL SELECT 'specialty_vocabulary_absent_assignments', count(*)
    FROM _eds_ipdb_specialties WHERE model_slug IS NOT NULL AND NOT target_exists
  -- The named remainder: assignments on listings no model matches, already reported
  -- under `ipdb-model-*` and deliberately excluded from every specialty worklist.
  UNION ALL SELECT 'specialty_assignments_on_unmatched_listings', count(*)
    FROM _eds_ipdb_specialties WHERE model_slug IS NULL
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

-- Empty when healthy. Invariants of this file's own views, never findings about the
-- data. The ladder, worklist-grain, classification and decode-key anchors live in
-- `identity_checks`; what remains here guards the IPDB-only sections.
CREATE OR REPLACE VIEW ipdb_checks AS
  -- The pairing points at the listing the catalog is expected to hold instead. If that
  -- one is missing too, the row is no longer explaining anything away.
  SELECT 'duplicate_target_not_in_catalog' AS check_name,
         d.duplicate_of_ipdb_id::VARCHAR AS detail
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
  -- The classification vocabulary lives in the rule registry, and only there: an
  -- emitted class the registry has never heard of means the CASE grew a branch nobody
  -- decided a finding policy for.
  SELECT 'corporate_entity_classification_unregistered', c.classification
  FROM (SELECT DISTINCT classification FROM ipdb_model_corporate_entity_mismatched) AS c
  WHERE NOT EXISTS (SELECT 1 FROM _eds_rule_registry AS r
                    WHERE r.detail_view = 'ipdb_model_corporate_entity_mismatched'
                      AND r.classification = c.classification)

  UNION ALL
  -- Person resolution is a lookup, so it must leave the credit grain alone.
  SELECT 'credits_not_one_row_per_dump_credit',
         (SELECT count(*) FROM px.ipdb.model_credits)::VARCHAR || ' dump credits -> '
           || (SELECT count(*) FROM _eds_ipdb_credits)::VARCHAR || ' resolved'
  WHERE (SELECT count(*) FROM _eds_ipdb_credits)
      > (SELECT count(*) FROM px.ipdb.model_credits)

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
  -- STRICTER than the assertion layer's unified grain, which includes the target in
  -- its key: one row per (listing, specialty) is this section's own promise. A
  -- specialty mapped onto two targets would fan the missing-specialties worklist
  -- out, and that is a mapping decision to adjudicate, not a shape to inherit
  -- silently.
  SELECT 'specialty_not_one_row_per_assignment',
         ipdb_id::VARCHAR || ' / ' || specialty
  FROM _eds_ipdb_specialties
  GROUP BY ipdb_id, specialty HAVING count(*) > 1

  UNION ALL
  -- A closed vocabulary, and the anchor for the whole section: if pinexplore's rule
  -- table were emptied or the join silently produced nothing, every specialty view
  -- would go quiet and read exactly like a catalog that already carries everything.
  SELECT 'specialty_rules_missing', 'px.ipdb.specialties is empty'
  WHERE (SELECT count(*) FROM px.ipdb.specialties) = 0

  UNION ALL
  -- The summary PROMISES these partitions ("a reader who notices a gap has found a
  -- bug"), so they are asserted, not just stated: the next specialty bucket added
  -- without joining the sum breaks here, loudly, instead of breaking the promise.
  SELECT 'specialty_assignment_partition_broken',
         format('carried {} + missing {} + vocab-absent {} + on-unmatched {} <> assignments {}',
                carried, missing, absent, unmatched, total)
  FROM (SELECT
          (SELECT count(*) FROM _eds_ipdb_specialties WHERE carried) AS carried,
          (SELECT count(*) FROM ipdb_model_specialties_missing) AS missing,
          (SELECT count(*) FROM _eds_ipdb_specialties
             WHERE model_slug IS NOT NULL AND NOT target_exists) AS absent,
          (SELECT count(*) FROM _eds_ipdb_specialties WHERE model_slug IS NULL) AS unmatched,
          (SELECT count(*) FROM px.ipdb.model_specialties) AS total)
  WHERE carried + missing + absent + unmatched <> total

  UNION ALL
  SELECT 'specialty_coverage_partition_broken',
         format('covered {} + unchecked {} <> dump models {}', covered, unchecked, total)
  FROM (SELECT
          (SELECT count(DISTINCT ipdb_id) FROM px.ipdb.model_specialties) AS covered,
          (SELECT count(*) FROM px.ipdb.models AS im
             WHERE NOT EXISTS (SELECT 1 FROM px.ipdb.model_specialties AS s
                               WHERE s.ipdb_id = im.ipdb_id)) AS unchecked,
          (SELECT count(*) FROM px.ipdb.models) AS total)
  WHERE covered + unchecked <> total;
COMMENT ON VIEW ipdb_checks IS
  'Empty when healthy — the IPDB-only sections'' anchors: duplicate-listing targets, credit grain and role vocabulary, corporate-entity grain, the spelling-scoped specialty-target gate, and the summary''s promised partitions. The ladder and worklist anchors live in identity_checks; the carriage and lookup anchors in assertions_checks.';
