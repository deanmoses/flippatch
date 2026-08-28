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
-- MATERIALIZED, with the view above kept as the DEFINITION WITNESS -- see the IPDB twin
-- for why the witness has to exist. Never read `_source` directly.
CREATE OR REPLACE VIEW _eds_opdb_dump_source AS
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
CREATE OR REPLACE TABLE _eds_opdb_dump AS SELECT * FROM _eds_opdb_dump_source;

-- ─── the ipdb_id route: link-by-id, above the whole name ladder ────────────
--
-- 92% of OPDB listings cross-reference an IPDB id, and the catalog's own ipdb_id
-- links are unique (asserted in ipdb_checks) -- so an unmatched listing whose
-- ipdb_id a catalog model already holds is ID-GRADE evidence, needing no name and no
-- triangle (the identity doc's "OPDB's ipdb_id" rule: link by id before any entity
-- tier). Trusted only while the transitive chain contradicts nothing; the doc's
-- three exceptions, checked coarsest first:
--
--   shared           several OPDB listings carry this ipdb_id -- OPDB splits
--                    variants finer than IPDB (both Metallica Premiums
--                    cross-reference IPDB 6029), so the id names a variant FAMILY,
--                    not this listing. Never a link; the evidence rides the row.
--   conflict         the model holding the ipdb_id already links a DIFFERENT
--                    opdb_id: possible-duplicate evidence, never a backfill.
--   titles_disagree  the listing's group and the model's title are both linked and
--                    differ; someone is wrong about grouping, and linking would
--                    take a side silently.
--   linkable         a clean chain -- the verdict columns fill and the worklist
--                    classifies it a backfill.
CREATE OR REPLACE VIEW _eds_opdb_ipdb_route AS
  SELECT
    d.opdb_id,
    d.opdb_ipdb_id,
    m.slug AS ipdb_route_model_slug,
    (SELECT count(*) FROM px.opdb.models AS om
       WHERE om.ipdb_id = d.opdb_ipdb_id)  AS n_listings_sharing_ipdb_id,
    CASE
      WHEN (SELECT count(*) FROM px.opdb.models AS om
              WHERE om.ipdb_id = d.opdb_ipdb_id) > 1        THEN 'shared'
      WHEN m.opdb_id IS NOT NULL                            THEN 'conflict'
      WHEN t_group.id IS NOT NULL AND t_model.id IS NOT NULL
       AND t_group.id <> t_model.id                         THEN 'titles_disagree'
      ELSE                                                       'linkable'
    END AS ipdb_id_chain,
    CASE WHEN (SELECT count(*) FROM px.opdb.models AS om
                 WHERE om.ipdb_id = d.opdb_ipdb_id) = 1
          AND m.opdb_id IS NULL
          AND NOT (t_group.id IS NOT NULL AND t_model.id IS NOT NULL
                   AND t_group.id <> t_model.id)
         THEN m.slug END    AS unlinked_model_slug,
    CASE WHEN (SELECT count(*) FROM px.opdb.models AS om
                 WHERE om.ipdb_id = d.opdb_ipdb_id) = 1
          AND m.opdb_id IS NOT NULL
         THEN m.slug END    AS linked_model_slug,
    CASE WHEN (SELECT count(*) FROM px.opdb.models AS om
                 WHERE om.ipdb_id = d.opdb_ipdb_id) = 1
         THEN m.opdb_id END AS linked_model_opdb_id,
    m.production_year       AS ipdb_route_model_production_year
  FROM _eds_opdb_dump AS d
  INNER JOIN models AS m ON m.ipdb_id = try_cast(d.opdb_ipdb_id AS BIGINT)
  LEFT JOIN titles AS t_group ON t_group.opdb_id = d.title_opdb_id
  LEFT JOIN titles AS t_model ON t_model.id = m.title_id
  WHERE NOT EXISTS (SELECT 1 FROM models AS x WHERE x.opdb_id = d.opdb_id);

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

-- The maker disagreements, at PAIR grain and derived once, so the model ladder above
-- and the maker worklist below cannot drift apart about which pairings are contested.
-- `opdb_checks` asserts the two agree.
--
-- A pairing is contested when a linked model's catalog manufacturer differs from the one
-- OPDB names for the same machine AND nobody has adjudicated the pair. Bally Wulff
-- against OPDB's Bally is the live example.
CREATE OR REPLACE VIEW _eds_opdb_disagreeing_pairs AS
  SELECT DISTINCT m.manufacturer_slug, d.opdb_manufacturer_slug
  FROM _eds_opdb_dump AS d
  INNER JOIN models AS m ON m.opdb_id = d.opdb_id
  LEFT JOIN _eds_opdb_manufacturer_exceptions AS ex
    ON  ex.opdb_manufacturer_id = d.opdb_manufacturer_id
    AND ex.manufacturer_slug    = m.manufacturer_slug
  WHERE d.opdb_manufacturer_slug IS NOT NULL
    AND m.manufacturer_slug      IS NOT NULL
    AND m.manufacturer_slug IS DISTINCT FROM d.opdb_manufacturer_slug
    AND ex.reason IS NULL;

-- THE MAKER LEG CANNOT ALWAYS DISCRIMINATE, and this names the listings where it cannot.
--
-- The ladder's tiers 1 and 2 both decide by maker: among same-named catalog models, the
-- one whose manufacturer matches OPDB's wins. That is sound only while the maker names
-- one company on both sides. Where a pairing is contested -- OPDB files Bally Wulff's
-- games under Bally -- the SAME name can sit under both manufacturers, and matching the
-- maker picks the wrong one with full confidence. Catalog `karate-fight` (Bally Wulff)
-- and `karate-fight-2` (Bally) are both 1986 "Karate Fight"; OPDB says Bally; the true
-- link is the Bally Wulff one. Replaying the ladder over the links we already hold finds
-- exactly this row and no other (`known_good_replay.sql`).
--
-- Deliberately NARROW. Keying on "the OPDB maker appears in some contested pair" would
-- taint all 762 Bally listings for the sake of two Bally Wulff machines. The condition is
-- a same-named RIVAL under the contested counterpart -- the actual ambiguity -- which
-- today flags one listing in the replay and none in the live worklist.
--
-- The winner cannot be its own rival: at tiers 1 and 2 its manufacturer equals the
-- listing's OPDB maker, and a contested pair is by construction two DIFFERENT makers.
CREATE OR REPLACE VIEW _eds_opdb_maker_contested AS
  SELECT
    d.opdb_id,
    list_sort(list(DISTINCT rival.slug || ' (' || rival.manufacturer_slug || ')'))[:5]
      AS contested_rival_models
  FROM _eds_opdb_dump AS d
  INNER JOIN models AS rival ON name_norm(rival.name) = name_norm(d.opdb_name)
  INNER JOIN _eds_opdb_disagreeing_pairs AS p
    ON  p.manufacturer_slug      = rival.manufacturer_slug
    AND p.opdb_manufacturer_slug = d.opdb_manufacturer_slug
  GROUP BY d.opdb_id;

-- ─── the model-matching ladder ─────────────────────────────────────────────
--
-- Matching an OPDB listing to a catalog model runs down evidence tiers, strongest
-- first. Above everything sits the ipdb_id route -- an id, not a match. The name
-- tiers below apply to what it could not settle. The catalog-id tier is implicit --
-- every view here is scoped to listings whose id no model carries -- and below it:
--
--   1. title_and_maker  name match among the models of the catalog title that links
--                       the listing's own GROUP (OPDB group = catalog Title), with
--                       the maker matching too
--   2. maker            name-and-maker match across the whole catalog. Above the
--                       title-only tier because the maker is a leg of the identity
--                       triangle: catalog `cobra` is Bell Games, and Playbar's Cobra
--                       machine must resolve to the Playbar `cobra-2` on another
--                       title, not to the same-title model whose maker CONTRADICTS
--                       the listing's.
--   3. title            name match among the linked title's models alone -- needs no
--                       maker, so it reaches listings `maker_unresolved` used to
--                       strand. Last, because it holds both maker-unknown and
--                       maker-contradicted matches.
--
-- The first tier holding any candidate answers, and it answers PLURALLY when it holds
-- more than one: a verdict is published only when the winning tier holds exactly one
-- model, and anything else is `multiple_candidates` -- never the alphabetically first
-- match dressed up as an answer. A bare name match with neither title nor maker
-- behind it is not a candidate at all; that is `_eds_opdb_namesakes`, evidence rather
-- than an answer.
--
-- THE THIRD LEG OF THE TRIANGLE IS THE YEAR, and it REFUTES, never elects. Model
-- identity is (name, maker, year) with the year allowed off by one but no more; OPDB
-- states a year on every listing, so a candidate whose catalog year (production or
-- project, either kind corroborates identity) sits more than a year away is not this
-- machine -- a remake, a different era's namesake -- and leaves the pool. It does not
-- vanish: `year_conflict` classifies the listings it strands, and the refuted list
-- rides the worklist row. Year CORROBORATION never breaks a plural tie, because the
-- true match can be the yearless candidate -- Meteor's is -- and electing the dated
-- one is the arbitrary-pick bug wearing a year. A candidate with no catalog year
-- cannot be refuted; absence refutes nothing.

-- One row per (unmatched listing, candidate model): every catalog model answering the
-- listing's name with at least one tier of support, flagged by tier.
--
-- Matched on `name_norm`, not `name_key`: `name_key` strips a trailing parenthetical,
-- and on OPDB the parenthetical IS the identity -- the unmatched set is full of
-- "(Pro)" / "(Premium)" / "(LE)" edition rows whose base machine the catalog holds.
--
-- The flags coalesce to false so a NULL on either side (no linked title, no resolved
-- maker) reads as "this tier does not support the pairing", not as unknown.
-- MATERIALIZED: see the IPDB twin. Unscoped for the replay, so the row count is the
-- whole dump rather than the unmatched tail, and re-deriving it per scan dominated the run.
CREATE OR REPLACE TABLE _eds_opdb_candidate_models AS
  SELECT
    d.opdb_id,
    m.slug            AS model_slug,
    m.opdb_id         AS model_opdb_id,
    m.production_year,
    coalesce(m.production_year, m.project_year) AS model_display_year,
    coalesce(m.title_id = t.id, false)                              AS in_group_title,
    coalesce(m.manufacturer_slug = d.opdb_manufacturer_slug, false) AS maker_matches,
    -- NULL-safe by construction: a NULL year on either side lands `unknown` in the
    -- first branch; in the second, an `abs` against a NULL catalog year is NULL, and
    -- `NULL OR true` is true while `NULL OR false` falls through to `refuted` --
    -- which is correct, because the only year the catalog states is then off.
    CASE WHEN d.opdb_year IS NULL
           OR (m.production_year IS NULL AND m.project_year IS NULL)  THEN 'unknown'
         WHEN abs(d.opdb_year - m.production_year) <= 1
           OR abs(d.opdb_year - m.project_year) <= 1                  THEN 'corroborated'
         ELSE                                                              'refuted'
    END AS year_verdict
  FROM _eds_opdb_dump AS d
  LEFT JOIN titles AS t ON t.opdb_id = d.title_opdb_id
  INNER JOIN models AS m ON name_norm(m.name) = name_norm(d.opdb_name)
  -- NOT filtered to unmatched listings, deliberately. Scoping the ladder to the rows
  -- it is asked about would make it untestable: `known_good_replay.sql` re-derives the
  -- links we ALREADY hold and compares, which is only evidence about the shipping
  -- matcher if it runs the shipping views rather than a copy of them. Every consumer
  -- that wants only unmatched listings filters at its own site -- `opdb_models_unmatched`
  -- in its WHERE, `_eds_opdb_group_titles` in its candidate branch -- so live output is
  -- unchanged and the replay reads the real thing.
  WHERE coalesce(m.title_id = t.id, false)
     OR coalesce(m.manufacturer_slug = d.opdb_manufacturer_slug, false);

-- One row per listing with any candidate: the winning tier's answer, verdict columns
-- filled ONLY when it is unique. This is the one place "uniquely resolved" is defined
-- -- exactly one candidate at the winning tier -- so every consumer (the model
-- worklist, the group-title verdicts) inherits the same gate instead of re-deriving
-- it, which is how the too-loose tier-2 gate bug happened last time.
--
-- With exactly one winning row, `min` of each column reads that row whole, NULLs
-- included; with more than one, every verdict column is NULL and the sorted capped
-- list plus `n_candidates` carry the plural answer.
-- MATERIALIZED for the same reason as the candidates it aggregates.
CREATE OR REPLACE TABLE _eds_opdb_model_resolution AS
  WITH winning AS (
    SELECT *,
      CASE WHEN in_group_title AND maker_matches THEN 1
           WHEN maker_matches THEN 2
           ELSE 3 END AS tier
    FROM _eds_opdb_candidate_models
    -- The triangle's refutation: a candidate more than a year away is not this
    -- machine and never enters a pool. It resurfaces through `refuted` below.
    WHERE year_verdict <> 'refuted'
    QUALIFY tier = min(tier) OVER (PARTITION BY opdb_id)
  ),
  refuted AS (
    -- A refuted candidate that is already LINKED says so: whether the near-miss is
    -- spoken for by another external id is the fact that turns "investigate a year
    -- discrepancy" into "this is a different machine; create it".
    SELECT
      opdb_id,
      count(*) AS n_year_refuted,
      list_sort(list(model_slug || ' (' || coalesce(model_display_year::VARCHAR, '?')
        || coalesce(', links OPDB ' || model_opdb_id, '') || ')'))[:5]
        AS year_refuted_models
    FROM _eds_opdb_candidate_models
    WHERE year_verdict = 'refuted'
    GROUP BY opdb_id
  ),
  verdicts AS (
    SELECT
      opdb_id,
      match_basis,
      n_candidates,
      candidate_model_slugs,
      -- `resolved_year_verdict` qualifies a verdict: 'corroborated' means the full
      -- triangle agrees, 'unknown' that the catalog states no year to check.
      CASE WHEN n_candidates = 1 THEN only_year_verdict END AS resolved_year_verdict,
      CASE WHEN n_candidates = 1 AND n_linked = 0 THEN only_slug END AS unlinked_model_slug,
      CASE WHEN n_candidates = 1 AND n_linked = 1 THEN only_slug END AS linked_model_slug,
      CASE WHEN n_candidates = 1 AND n_linked = 1 THEN only_opdb_id END AS linked_model_opdb_id,
      CASE WHEN n_candidates = 1 AND n_linked = 1 THEN only_year END AS linked_model_production_year
    FROM (
      SELECT
        opdb_id,
        CASE min(tier) WHEN 1 THEN 'title_and_maker'
                       WHEN 2 THEN 'maker'
                       ELSE        'title' END              AS match_basis,
        count(*)                                            AS n_candidates,
        count(*) FILTER (WHERE model_opdb_id IS NOT NULL)   AS n_linked,
        list_sort(list(model_slug))[:5]                     AS candidate_model_slugs,
        min(model_slug)                                     AS only_slug,
        min(model_opdb_id)                                  AS only_opdb_id,
        min(production_year)                                AS only_year,
        min(year_verdict)                                   AS only_year_verdict
      FROM winning
      GROUP BY opdb_id
    )
  )
  -- FULL join: a listing whose every candidate was year-refuted has no verdict row,
  -- and its refuted evidence is exactly what the worklist needs to say so.
  SELECT
    coalesce(v.opdb_id, rf.opdb_id) AS opdb_id,
    v.match_basis,
    coalesce(v.n_candidates, 0)     AS n_candidates,
    v.candidate_model_slugs,
    v.resolved_year_verdict,
    v.unlinked_model_slug,
    v.linked_model_slug,
    v.linked_model_opdb_id,
    v.linked_model_production_year,
    coalesce(rf.n_year_refuted, 0)  AS n_year_refuted,
    rf.year_refuted_models
  FROM verdicts AS v
  FULL JOIN refuted AS rf ON rf.opdb_id = v.opdb_id;

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
--   moved_successor         This id is where a moved id LANDED: some catalog model's
--                           stale opdb_id names it as successor. The repoint reported by
--                           `opdb-id-moved` covers it -- one action, so no second
--                           finding -- and `moved_from_model_slug` names the model to
--                           repoint. First in precedence because the successor usually
--                           also name-matches that very model, and reading it as a
--                           `possible_duplicate` restates the same repoint as new work.
--   catalog_holds_unlinked  The ladder resolved UNIQUELY to a model with no OPDB id
--                           AND the year corroborates. A backfill: patch the id, do
--                           not create a record.
--   possible_duplicate      The ladder resolved uniquely, year corroborated, to a
--                           model already linked to a DIFFERENT OPDB id. Read both
--                           OPDB pages.
--   year_unverified         Exactly one model answers, but the year triangle CANNOT
--                           CLOSE -- the catalog model is undated -- so the match is
--                           unproven and linking it would be a guess (the identity
--                           doc's NEVER-GUESS rule: a missing leg blocks the link,
--                           full stop). Verify the year on the OPDB page, date the
--                           model, then link.
--   multiple_candidates     The winning tier holds MORE than one model, so the ladder
--                           answers plurally: `candidate_model_slugs` lists them and
--                           `match_basis` says which tier. Adjudicate before
--                           patching; no arbitrary candidate is ever presented as
--                           the answer.
--   year_conflict           Every name match the tiers found is refuted by the year
--                           triangle: more than a year from the catalog's dates.
--                           Either a wrong year on one side or a different era's
--                           machine -- `year_refuted_models` lists them with their
--                           years. Read the pages; do not create a record blind.
--   maker_unresolved        No candidate search was possible: the listing has no
--                           maker to match on AND no catalog title links its group.
--                           NOT a statement that the catalog lacks the machine --
--                           read `n_namesake_models` and the OPDB page.
--   absent                  A search ran -- within the group's linked title, by name
--                           and maker, or both -- and found nothing, with nothing
--                           even year-refuted. A candidate new record.
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
      WHEN moved_from.model_slug IS NOT NULL  THEN 'moved_successor'
      -- The ipdb_id route outranks the whole name ladder: an id, not a match, so no
      -- triangle applies (identity doc: link by id before any entity tier). Only a
      -- CLEAN chain links; its exceptions fall through to the ladder with the
      -- evidence riding the row.
      WHEN ir.unlinked_model_slug IS NOT NULL THEN 'catalog_holds_unlinked'
      WHEN ir.linked_model_slug IS NOT NULL   THEN 'possible_duplicate'
      -- THE MAKER LEG IS CONTESTED HERE, so a tier that decided by maker did not
      -- decide anything. Ranked below the ipdb_id route (an id outranks a name
      -- ambiguity) and above every confident ladder class, so a unique-looking
      -- answer resting on a maker two systems disagree about goes to manual
      -- adjudication instead of becoming a link instruction. Only the SINGULAR case
      -- needs it: a plural answer is already `multiple_candidates`.
      WHEN mc.opdb_id IS NOT NULL
       AND r.n_candidates = 1
       AND r.match_basis IN ('title_and_maker', 'maker') THEN 'maker_contested'
      -- The confident ladder classes demand the CLOSED triangle: unique candidate
      -- AND the year corroborated. A unique match whose year leg cannot close is
      -- `year_unverified` -- never a link instruction.
      WHEN r.unlinked_model_slug IS NOT NULL
       AND r.resolved_year_verdict = 'corroborated' THEN 'catalog_holds_unlinked'
      WHEN r.linked_model_slug IS NOT NULL
       AND r.resolved_year_verdict = 'corroborated' THEN 'possible_duplicate'
      WHEN r.n_candidates = 1                 THEN 'year_unverified'
      WHEN r.n_candidates > 1                 THEN 'multiple_candidates'
      WHEN r.n_year_refuted > 0               THEN 'year_conflict'
      WHEN d.opdb_manufacturer_slug IS NULL
       AND linked_title.id IS NULL            THEN 'maker_unresolved'
      ELSE                                         'absent'
    END                                  AS classification,
    moved_from.model_slug                AS moved_from_model_slug,
    parent.slug                          AS parent_model_slug,
    linked_title.slug                    AS linked_title_slug,
    CASE WHEN ir.unlinked_model_slug IS NOT NULL
           OR ir.linked_model_slug IS NOT NULL THEN 'ipdb_id'
         ELSE r.match_basis END          AS match_basis,
    coalesce(ir.unlinked_model_slug, r.unlinked_model_slug) AS unlinked_model_slug,
    coalesce(ir.linked_model_slug, r.linked_model_slug)     AS linked_model_slug,
    coalesce(ir.linked_model_opdb_id, r.linked_model_opdb_id) AS linked_model_opdb_id,
    coalesce(CASE WHEN ir.linked_model_slug IS NOT NULL
                  THEN ir.ipdb_route_model_production_year END,
             r.linked_model_production_year) AS linked_model_production_year,
    r.resolved_year_verdict,
    coalesce(r.n_candidates, 0)          AS n_candidates,
    r.candidate_model_slugs,
    coalesce(r.n_year_refuted, 0)        AS n_year_refuted,
    r.year_refuted_models,
    ir.opdb_ipdb_id,
    ir.ipdb_route_model_slug,
    ir.ipdb_id_chain,
    ir.n_listings_sharing_ipdb_id,
    coalesce(n.n_namesake_models, 0)     AS n_namesake_models,
    n.namesake_model_slugs,
    -- The evidence behind `maker_contested`: the same-named models sitting under the
    -- manufacturer OPDB's maker is contested against. Present on any row where the
    -- ambiguity exists, whatever the classification, so a reader can see it was
    -- considered rather than infer it from the class.
    mc.contested_rival_models
  FROM _eds_opdb_dump AS d
  LEFT JOIN _eds_opdb_ipdb_route AS ir USING (opdb_id)
  LEFT JOIN _eds_opdb_model_resolution AS r USING (opdb_id)
  LEFT JOIN _eds_opdb_maker_contested AS mc USING (opdb_id)
  LEFT JOIN _eds_opdb_namesakes  AS n USING (opdb_id)
  LEFT JOIN models AS parent       ON parent.opdb_id = d.opdb_variant_of
  LEFT JOIN titles AS linked_title ON linked_title.opdb_id = d.title_opdb_id
  -- A scalar subquery, so it cannot fan the grain out even if several stale ids moved
  -- onto one successor (a merge); `min` then picks a deterministic representative and
  -- the others are still visible in `opdb_ids_stale`.
  LEFT JOIN LATERAL (
    SELECT min(m.slug) AS model_slug
    FROM models AS m
    INNER JOIN px.opdb.model_ids AS i ON i.opdb_id = m.opdb_id
    WHERE i.status = 'moved' AND i.current_opdb_id = d.opdb_id
  ) AS moved_from ON true
  WHERE NOT EXISTS (SELECT 1 FROM models AS m WHERE m.opdb_id = d.opdb_id);
COMMENT ON VIEW opdb_models_unmatched IS
  'Worklist — one row per OPDB listing no live model carries the id of, classified moved_successor / catalog_holds_unlinked / possible_duplicate / maker_contested / multiple_candidates / year_unverified / year_conflict / maker_unresolved / absent. The ipdb_id route links first where its chain is clean (match_basis ipdb_id; a shared id or a grouping disagreement blocks it, the evidence riding the row); then the name ladder (name within the group''s linked title, then name and maker, the year refuting any candidate more than a year off). A maker-decided answer whose maker pairing is itself contested is held back as maker_contested, its rivals on the row. Rows are expected.';

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
    m.production_year,
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

-- The titles an OPDB group's OWN machines point at -- the decisive evidence for
-- matching a group to a title, one row per group with any machine verdict.
--
-- A group has no maker, so matching its bare name is weak: a name can answer to
-- several titles, and only a machine's maker tells them apart (two catalog titles
-- answer to "Top Hand", and the name route once proposed the wrong one). But the group
-- HAS machines, and where those connect to catalog models, the models' own titles
-- settle what the group is. Two evidence tiers feed the vote: a LINKED machine's
-- title is a verdict, and an unmatched machine votes the titles of its CANDIDATES.
--
-- The candidate vote is deliberately looser than the model ladder's verdict: title
-- identity is FAMILY grain, and family evidence survives what model evidence cannot.
-- A plural candidate set confined to one title is a clean family vote (Meteor's three
-- bootlegs all live under `meteor`), and the year triangle is not consulted -- a
-- family spans years, and a year-refuted model twin still places the machine in that
-- family. Model-grain uniqueness questions stay in the model worklist, where they
-- belong.
--
-- ONE distinct title across the tiers is decisive, and the verdict columns fill only
-- then -- split by whether that title already links a group -- so a consumer can
-- coalesce them over weaker evidence and never publish half a verdict. MORE than one
-- title means the two sides DISAGREE about grouping -- which side is right is
-- adjudicated per group, never assumed; see `opdb_title_splits` -- so the verdict
-- columns stay NULL and `machines_title_slugs` shows the whole split rather than an
-- arbitrary pick papering over it.
CREATE OR REPLACE VIEW _eds_opdb_group_titles AS
  WITH machine_titles AS (
    SELECT om.title_opdb_id, t.slug AS title_slug, t.opdb_id AS title_group_opdb_id
    FROM px.opdb.models AS om
    INNER JOIN models AS m ON m.opdb_id = om.opdb_id
    INNER JOIN titles AS t ON t.id = m.title_id
    UNION
    SELECT om.title_opdb_id, t.slug, t.opdb_id
    FROM px.opdb.models AS om
    INNER JOIN _eds_opdb_candidate_models AS cm ON cm.opdb_id = om.opdb_id
    INNER JOIN models AS m ON m.slug = cm.model_slug
    INNER JOIN titles AS t ON t.id = m.title_id
    -- UNLINKED machines only: this branch exists so a machine with no id link can still
    -- vote its title through its candidates. A LINKED machine already votes through the
    -- branch above, via its actual link, and letting its candidates vote too would add
    -- the titles of same-named rivals -- manufacturing a `split_across_titles` out of a
    -- namesake. The filter sits here rather than in the candidate view because that view
    -- is deliberately unscoped so the known-good replay can exercise it.
    WHERE NOT EXISTS (SELECT 1 FROM models AS x WHERE x.opdb_id = om.opdb_id)
  )
  SELECT
    opdb_id,
    n_machines_title_slugs,
    machines_title_slugs,
    CASE WHEN n_machines_title_slugs = 1 AND only_title_group_opdb_id IS NULL
         THEN only_title_slug END AS unlinked_title_slug,
    CASE WHEN n_machines_title_slugs = 1 AND only_title_group_opdb_id IS NOT NULL
         THEN only_title_slug END AS linked_title_slug,
    CASE WHEN n_machines_title_slugs = 1
         THEN only_title_group_opdb_id END AS linked_title_opdb_id
  FROM (
    -- The UNION above dedupes whole rows and a slug names exactly one title, so when
    -- one distinct slug survives there is exactly one row, and `min` of each column
    -- reads that row whole -- the published pair cannot mix two titles.
    SELECT
      title_opdb_id                        AS opdb_id,
      count(DISTINCT title_slug)           AS n_machines_title_slugs,
      list_sort(list(DISTINCT title_slug)) AS machines_title_slugs,
      min(title_slug)                      AS only_title_slug,
      min(title_group_opdb_id)             AS only_title_group_opdb_id
    FROM machine_titles
    GROUP BY title_opdb_id
  );

-- WORKLIST — OPDB machine groups with no catalog title, classified on two evidence
-- routes: what the group's own machines say (`_eds_opdb_group_titles` above, decisive
-- wherever it speaks) and, below that, a name-only candidate search whose counts
-- qualify it. Precedence is the coalesce order -- the machine route's verdict columns
-- fill only when decisive, so each column takes the strongest route that has an
-- answer. A group usually goes unmatched for the same reason its machines do: a
-- release newer than the catalog's last OPDB acquisition.
--
-- `split_across_titles` outranks every other class -- the machines' own split verdict
-- makes any name-route reading of the group noise -- and asserts only DISAGREEMENT:
-- OPDB groups machines the catalog holds under more than one title. Which side is
-- right is adjudicated per group, never assumed. A tournament combo ("Family Guy /
-- Shrek") is a correct catalog split, but the identical signature is produced by a
-- misfiled model or a wrong tier-2 inference, so an `absent` finding (create the
-- combo title) would be exactly wrong and a blanket all-clear would be too. The
-- finding is emitted at the split grain from `opdb_title_splits` below.
CREATE OR REPLACE VIEW opdb_titles_unmatched AS
  SELECT
    ot.opdb_id,
    ot.name        AS opdb_title_name,
    ot.year        AS opdb_year,
    ot.n_models    AS n_opdb_models,
    CASE
      WHEN md.n_machines_title_slugs > 1      THEN 'split_across_titles'
      WHEN md.unlinked_title_slug IS NOT NULL THEN 'catalog_holds_unlinked'
      WHEN md.linked_title_slug IS NOT NULL   THEN 'possible_duplicate'
      -- The name route's verdicts are gated by the YEAR LEG (identity doc: a name
      -- alone is a guess). A title has no year of its own; the comparable fact is
      -- its EARLIEST dated model year, because OPDB's group year is the family's
      -- original release. A candidate title with no dated model corroborates
      -- nothing; one more than a year off contradicts. Machine votes above are
      -- deliberately not year-gated -- members outrank both name and year.
      WHEN c.unlinked_title_slug IS NOT NULL
        OR c.linked_title_slug IS NOT NULL    THEN
        CASE WHEN c.candidate_earliest_model_year IS NULL         THEN 'year_unverified'
             WHEN abs(ot.year - c.candidate_earliest_model_year) > 1 THEN 'year_conflict'
             WHEN c.unlinked_title_slug IS NOT NULL               THEN 'catalog_holds_unlinked'
             ELSE                                                      'possible_duplicate'
        END
      WHEN c.n_candidates > 1                 THEN 'multiple_candidates'
      ELSE                                         'absent'
    END            AS classification,
    coalesce(md.unlinked_title_slug, c.unlinked_title_slug)   AS unlinked_title_slug,
    coalesce(md.linked_title_slug, c.linked_title_slug)       AS linked_title_slug,
    coalesce(md.linked_title_opdb_id, c.linked_title_opdb_id) AS linked_title_opdb_id,
    md.machines_title_slugs,
    coalesce(md.n_machines_title_slugs, 0) AS n_machines_title_slugs,
    coalesce(c.n_candidates, 0)            AS n_candidates,
    c.candidate_title_slugs,
    c.candidate_earliest_model_year
  FROM px.opdb.titles AS ot
  LEFT JOIN _eds_opdb_group_titles AS md USING (opdb_id)
  -- The name route, under the ladder's verdict discipline: verdict columns fill only
  -- when exactly one title answers the name, a plural answer is the count and sorted
  -- capped list, and with one row `min` reads that row whole.
  LEFT JOIN (
    SELECT
      opdb_id,
      n_candidates,
      candidate_title_slugs,
      CASE WHEN n_candidates = 1 AND n_linked = 0 THEN only_slug END    AS unlinked_title_slug,
      CASE WHEN n_candidates = 1 AND n_linked = 1 THEN only_slug END    AS linked_title_slug,
      CASE WHEN n_candidates = 1 AND n_linked = 1 THEN only_opdb_id END AS linked_title_opdb_id,
      CASE WHEN n_candidates = 1 THEN only_earliest_year END AS candidate_earliest_model_year
    FROM (
      SELECT
        ot2.opdb_id,
        count(*)                                      AS n_candidates,
        count(*) FILTER (WHERE t.opdb_id IS NOT NULL) AS n_linked,
        list_sort(list(t.slug))[:5]                   AS candidate_title_slugs,
        min(t.slug)                                   AS only_slug,
        min(t.opdb_id)                                AS only_opdb_id,
        -- `least` ignores NULLs, so this is the earliest year any model on the
        -- title states, production or project -- and NULL when none is dated.
        min(te.earliest_year)                         AS only_earliest_year
      FROM px.opdb.titles AS ot2
      INNER JOIN titles AS t ON name_norm(t.name) = name_norm(ot2.name)
      LEFT JOIN LATERAL (
        SELECT least(min(m.production_year), min(m.project_year)) AS earliest_year
        FROM models AS m WHERE m.title_id = t.id
      ) AS te ON true
      WHERE NOT EXISTS (SELECT 1 FROM titles AS x WHERE x.opdb_id = ot2.opdb_id)
      GROUP BY ot2.opdb_id
    )
  ) AS c USING (opdb_id)
  WHERE NOT EXISTS (SELECT 1 FROM titles AS t WHERE t.opdb_id = ot.opdb_id);
COMMENT ON VIEW opdb_titles_unmatched IS
  'Worklist — one row per OPDB machine group no live title carries the id of, classified split_across_titles / catalog_holds_unlinked / possible_duplicate / multiple_candidates / year_unverified / year_conflict / absent. The group''s own machines settle the title where they can (split_across_titles means they reach more than one title — reported from opdb_title_splits); the name-only fallback needs the group''s year within one of the candidate title''s earliest model year, its plural answers listed rather than picked from. Rows are expected.';

-- WORKLIST — every OPDB group whose machines the catalog holds under more than one
-- title, MATCHED groups included.
--
-- The one split-grain readout. `opdb_titles_unmatched` classifies its rows
-- `split_across_titles`, but a matched group can split too -- its id sits on one
-- title while its machines resolve to others -- and the unmatched worklist never
-- looks at those. The signature proves only that the two sides disagree about
-- grouping; which side is right is adjudicated per group, by a person: a tournament
-- combo ("Family Guy / Shrek") is a correct catalog split to dismiss, but the same
-- rows have surfaced one clone family filed two different ways (Eight Ball Deluxe)
-- and two unrelated namesakes sharing a title (The Games) -- catalog defects no
-- other rule reports.
CREATE OR REPLACE VIEW opdb_title_splits AS
  SELECT
    g.opdb_id,
    ot.name AS opdb_title_name,
    t.slug  AS matched_title_slug,
    g.n_machines_title_slugs,
    g.machines_title_slugs
  FROM _eds_opdb_group_titles AS g
  INNER JOIN px.opdb.titles AS ot USING (opdb_id)
  LEFT JOIN titles AS t ON t.opdb_id = g.opdb_id
  WHERE g.n_machines_title_slugs > 1;
COMMENT ON VIEW opdb_title_splits IS
  'Worklist — one row per OPDB machine group whose machines resolve to more than one catalog title, matched groups included, with the linked title (if any) and every title the machines reach. A grouping disagreement to adjudicate per group: a correct catalog split gets dismissed, a misfiled model gets fixed. Rows are expected.';

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
      -- `first` ordered by the id `min` picked, so the published pair names ONE OPDB
      -- record -- deterministically and NULLs included, for the reasons on the
      -- model-matching ladder above.
      min(opdb_manufacturer_id)    AS opdb_manufacturer_id,
      first(name ORDER BY opdb_manufacturer_id) AS opdb_name
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

-- NO FIELD COMPARISON LIVES HERE, deliberately. A per-source scalar-field worklist
-- manufactures seesaw work, because sources disagree with each other and a dissent
-- another witness backs us on is a standoff, not a defect. Fields are compared against
-- the testimony POOL in `fields.sql` -- read its header before proposing one here.
--
-- Names are deliberately not compared anywhere: 135 models differ under `name_norm`
-- and nearly all of it is styling convention (subtitle punctuation, edition spelling),
-- a worklist with no action. The unmatched views compare names where a name is all
-- there is.

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
-- Seven warnings, one per classification, because the classes ask for different actions
-- and a dismissal keys on the rule. `moved_successor` is excluded, not downgraded: the
-- repoint is already reported by `opdb-id-moved`, and a second finding on the successor
-- id would restate it. It stays visible in the wide view.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'models' AS resolution_stage,
  CASE classification
    WHEN 'catalog_holds_unlinked' THEN 'opdb-model-unlinked'
    WHEN 'possible_duplicate'     THEN 'opdb-model-possible-duplicate'
    WHEN 'multiple_candidates'    THEN 'opdb-model-multiple-candidates'
    WHEN 'year_unverified'        THEN 'opdb-model-year-unverified'
    WHEN 'year_conflict'          THEN 'opdb-model-year-conflict'
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
      -- The ipdb_id route earns its own wording: the reader should know the link
      -- rests on an id chain, not a name match.
      CASE WHEN match_basis = 'ipdb_id' THEN
        format('OPDB {} "{}" cross-references IPDB {}, held by unlinked catalog model {}; backfill the opdb_id',
               opdb_id, coalesce(opdb_name, '?'), opdb_ipdb_id, coalesce(unlinked_model_slug, '?'))
      ELSE
        format('OPDB {} "{}" matches unlinked catalog model {}; backfill the opdb_id',
               opdb_id, coalesce(opdb_name, '?'), coalesce(unlinked_model_slug, '?'))
      END
    WHEN 'possible_duplicate' THEN
      CASE WHEN match_basis = 'ipdb_id' THEN
        format('OPDB {} "{}" cross-references IPDB {}, held by catalog model {}, which already links OPDB {}; read both pages',
               opdb_id, coalesce(opdb_name, '?'), opdb_ipdb_id,
               coalesce(linked_model_slug, '?'), coalesce(linked_model_opdb_id, '?'))
      ELSE
        format('OPDB {} "{}" matches catalog model {}, which already links OPDB {}; read both pages',
               opdb_id, coalesce(opdb_name, '?'), coalesce(linked_model_slug, '?'),
               coalesce(linked_model_opdb_id, '?'))
      END
    WHEN 'multiple_candidates' THEN
      -- The plural answer, listed and never picked from. The list is sorted at the
      -- source and capped at 5; `n_candidates` is the true count.
      format('OPDB {} "{}" matches {} by {} ({}); adjudicate before patching',
             opdb_id, coalesce(opdb_name, '?'),
             plural(n_candidates, 'catalog model', 'catalog models'),
             CASE match_basis WHEN 'title_and_maker' THEN 'name and maker within its linked title'
                              WHEN 'title'           THEN 'name within its linked title'
                              ELSE                        'name and maker' END,
             array_to_string(candidate_model_slugs, ', '))
    WHEN 'year_unverified' THEN
      format('OPDB {} "{}" ({}) matches {}{} by {}, but the catalog model is undated, so the match is unproven; verify the year on the OPDB page, date the model, then link',
             opdb_id, coalesce(opdb_name, '?'), coalesce(opdb_year::VARCHAR, 'undated'),
             coalesce(unlinked_model_slug, linked_model_slug),
             coalesce(' (links OPDB ' || linked_model_opdb_id || ')', ''),
             CASE match_basis WHEN 'title_and_maker' THEN 'name and maker within its linked title'
                              WHEN 'title'           THEN 'name within its linked title'
                              ELSE                        'name and maker' END)
    WHEN 'year_conflict' THEN
      format('OPDB {} "{}" ({}) matches {} by name but more than a year off ({}); read the pages -- a wrong year on one side, or a different era''s machine',
             opdb_id, coalesce(opdb_name, '?'), coalesce(opdb_year::VARCHAR, 'undated'),
             plural(n_year_refuted, 'catalog model', 'catalog models'),
             array_to_string(year_refuted_models, ', '))
    WHEN 'maker_unresolved' THEN
      CASE WHEN opdb_manufacturer_name IS NULL THEN
        format('OPDB {} "{}" names no maker at all and no title links its group, so no candidate search ran; {}',
               opdb_id, coalesce(opdb_name, '?'),
               plural(n_namesake_models, 'catalog namesake', 'catalog namesakes'))
      ELSE
        format('OPDB {} "{}" names maker "{}", whose id no live manufacturer carries, and no title links its group, so no candidate search ran; {}',
               opdb_id, coalesce(opdb_name, '?'), opdb_manufacturer_name,
               plural(n_namesake_models, 'catalog namesake', 'catalog namesakes'))
      END
    WHEN 'absent' THEN
      -- The relation qualifies what creating the record involves: an edition with a
      -- resolved parent is a smaller job than a standalone machine.
      format('OPDB {} "{}" ({}, {}) has no catalog model and no candidate matched its name{}{}{}',
             opdb_id, coalesce(opdb_name, '?'), coalesce(opdb_year::VARCHAR, 'undated'),
             opdb_relation,
             CASE WHEN parent_model_slug IS NOT NULL
                  THEN '; catalog parent ' || parent_model_slug ELSE '' END,
             CASE WHEN linked_title_slug IS NOT NULL
                  THEN '; files under title ' || linked_title_slug ELSE '' END,
             -- A blocked ipdb_id chain is still the best lead on the row: the reader
             -- should see the family the id names before creating anything.
             CASE WHEN ipdb_route_model_slug IS NOT NULL
                  THEN '; cross-references IPDB ' || opdb_ipdb_id || ', held by ' || ipdb_route_model_slug
                       || CASE WHEN ipdb_id_chain = 'shared'
                               THEN ' (' || n_listings_sharing_ipdb_id::VARCHAR || ' OPDB listings share the id)'
                               WHEN ipdb_id_chain = 'titles_disagree'
                               THEN ' (on a different title)'
                               ELSE '' END
                  ELSE '' END)
  END AS message,
  'opdb_models_unmatched' AS detail_view
FROM opdb_models_unmatched
WHERE classification <> 'moved_successor';

-- `split_across_titles` is excluded HERE only because its finding is emitted at the
-- split grain below, from `opdb_title_splits` -- which also covers the matched groups
-- this worklist cannot see. Reported elsewhere, like `moved_successor`; never
-- silently adjudicated.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'titles' AS resolution_stage,
  CASE classification
    WHEN 'catalog_holds_unlinked' THEN 'opdb-title-unlinked'
    WHEN 'possible_duplicate'     THEN 'opdb-title-possible-duplicate'
    WHEN 'multiple_candidates'    THEN 'opdb-title-multiple-candidates'
    WHEN 'year_unverified'        THEN 'opdb-title-year-unverified'
    WHEN 'year_conflict'          THEN 'opdb-title-year-conflict'
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
    WHEN 'multiple_candidates' THEN
      format('OPDB group {} "{}" matches {} by name ({}); adjudicate before patching',
             opdb_id, coalesce(opdb_title_name, '?'),
             plural(n_candidates, 'catalog title', 'catalog titles'),
             array_to_string(candidate_title_slugs, ', '))
    WHEN 'year_unverified' THEN
      format('OPDB group {} "{}" ({}) matches catalog title {} by name, but no model on it is dated, so the year leg cannot close; date a model, then link',
             opdb_id, coalesce(opdb_title_name, '?'), coalesce(opdb_year::VARCHAR, 'undated'),
             coalesce(unlinked_title_slug, linked_title_slug))
    WHEN 'year_conflict' THEN
      format('OPDB group {} "{}" ({}) matches catalog title {} by name, but its earliest model year {} is more than a year off; read the pages -- a wrong year on one side, or a different family',
             opdb_id, coalesce(opdb_title_name, '?'), coalesce(opdb_year::VARCHAR, 'undated'),
             coalesce(unlinked_title_slug, linked_title_slug),
             candidate_earliest_model_year)
    WHEN 'absent' THEN
      format('OPDB group {} "{}" ({}, {}) has no catalog title and none matches its name',
             opdb_id, coalesce(opdb_title_name, '?'), coalesce(opdb_year::VARCHAR, 'undated'),
             plural(n_opdb_models, 'OPDB model', 'OPDB models'))
  END AS message,
  'opdb_titles_unmatched' AS detail_view
FROM opdb_titles_unmatched
WHERE classification <> 'split_across_titles';

-- ─── grouping splits ───────────────────────────────────────────────────────
-- One rule over matched and unmatched groups alike. A split is a live disagreement
-- until a person adjudicates the group: dismiss it where the catalog's split is right
-- (a tournament combo), fix the records where it is not (a misfiled model, an
-- inconsistent clone filing). Nothing here presumes either verdict.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'titles' AS resolution_stage,
  'opdb-title-split-across-titles' AS rule,
  'warning' AS severity,
  opdb_id AS external_id,
  CASE WHEN matched_title_slug IS NOT NULL THEN 'title' END AS entity_type,
  matched_title_slug AS entity_public_id,
  -- The slug list is sorted at the source, so the message is deterministic.
  format('OPDB group {} "{}" holds machines the catalog files across {} titles ({}){}',
         opdb_id, coalesce(opdb_title_name, '?'), n_machines_title_slugs,
         array_to_string(machines_title_slugs, ', '),
         CASE WHEN matched_title_slug IS NOT NULL
              THEN '; the group id is linked by ' || matched_title_slug
              ELSE '; no title links the group id' END) AS message,
  'opdb_title_splits' AS detail_view
FROM opdb_title_splits;

-- ─── stale ids ─────────────────────────────────────────────────────────────
-- Three of the four classes are errors -- the changelog CONFIRMS the catalog is citing
-- something dead, superseded, or of the wrong kind -- and the unexplained class stays a
-- warning for the same reason IPDB's unexplained absences do: the dump cannot support
-- the stronger claim.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'models' AS resolution_stage,
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
  'titles' AS resolution_stage,
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
-- The ladder held an answer back because the maker leg could not discriminate. Filed at
-- MODELS stage (it is a model that went unlinked) but the message names the blocker,
-- which lives one stage up: adjudicate the maker pairing and this resolves itself.
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'models' AS resolution_stage,
  'opdb-model-maker-contested' AS rule,
  'warning' AS severity,
  opdb_id AS external_id,
  NULL::VARCHAR AS entity_type,
  NULL::VARCHAR AS entity_public_id,
  format('OPDB {} "{}" ({}) name-matches {} under OPDB''s maker {}, but {} answer{} to the same name under a manufacturer contested against it ({}); adjudicate the maker pairing first',
         opdb_id, opdb_name, coalesce(opdb_year::VARCHAR, '?'),
         coalesce(unlinked_model_slug, linked_model_slug, '?'),
         coalesce(opdb_manufacturer_slug, '?'),
         plural(len(contested_rival_models), 'model', 'models'),
         CASE WHEN len(contested_rival_models) = 1 THEN 's' ELSE '' END,
         array_to_string(contested_rival_models, ', ')) AS message,
  'opdb_models_unmatched' AS detail_view
FROM opdb_models_unmatched
WHERE classification = 'maker_contested';

INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'manufacturers' AS resolution_stage,
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
  'manufacturers' AS resolution_stage,
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
  'manufacturers' AS resolution_stage,
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
  'manufacturers' AS resolution_stage,
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
  'models' AS resolution_stage,
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

-- ─── vocabulary ────────────────────────────────────────────────────────────
INSERT INTO _external_data_source_findings BY NAME
SELECT
  'opdb' AS source,
  'content' AS resolution_stage,
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
  'content' AS resolution_stage,
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
  SELECT 'unmatched_listings_' || classification AS metric, count(*) AS value
  FROM opdb_models_unmatched GROUP BY classification
  UNION ALL SELECT 'unmatched_titles_' || classification, count(*)
    FROM opdb_titles_unmatched GROUP BY classification
  UNION ALL SELECT 'title_splits', count(*) FROM opdb_title_splits
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
  UNION ALL SELECT 'vocabulary_missing_assignments', count(*) FROM opdb_model_vocabulary_missing
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
  'Headline counts for the OPDB comparison — the unmatched sets by classification, the stale ids, the maker disagreements, and the totals both sides are measured against. Field comparisons live in fields_summary.';

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
    ('moved_successor', 'catalog_holds_unlinked', 'possible_duplicate',
     'maker_contested', 'multiple_candidates', 'year_unverified', 'year_conflict',
     'maker_unresolved', 'absent')

  UNION ALL
  -- The CASE precedence: a successor usually also name-matches the model holding the
  -- old id, so a branch reordered above `moved_successor` would silently demote these
  -- to `possible_duplicate` and the repoint would read as new work.
  SELECT 'moved_successor_misclassified', u.opdb_id
  FROM opdb_models_unmatched AS u
  WHERE u.moved_from_model_slug IS NOT NULL
    AND u.classification <> 'moved_successor'

  UNION ALL
  SELECT 'title_classification_unknown', classification
  FROM opdb_titles_unmatched
  WHERE classification NOT IN
    ('split_across_titles', 'catalog_holds_unlinked', 'possible_duplicate',
     'multiple_candidates', 'year_unverified', 'year_conflict', 'absent')

  UNION ALL
  -- The verdict layer holds one row per group; if it ever fans out, the title worklist
  -- silently double-counts. Same anchor as the worklists' own grain checks.
  SELECT 'group_titles_not_one_row_per_group', opdb_id
  FROM _eds_opdb_group_titles GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  -- The CASE precedence: a split group's machines usually also name-match something,
  -- so a branch reordered above `split_across_titles` would silently demote these to a
  -- name-route class -- an `absent` finding would tell an operator to create a combo
  -- title, beside the split finding already reporting the group. Same guard as
  -- `moved_successor_misclassified`.
  SELECT 'split_across_titles_misclassified', u.opdb_id
  FROM opdb_titles_unmatched AS u
  WHERE u.n_machines_title_slugs > 1
    AND u.classification <> 'split_across_titles'

  UNION ALL
  SELECT 'stale_classification_unknown', classification
  FROM opdb_ids_stale
  WHERE classification NOT IN ('moved', 'deleted', 'container', 'unexplained')

  UNION ALL
  SELECT 'manufacturer_classification_unknown', classification
  FROM opdb_model_manufacturer_mismatched
  WHERE classification NOT IN ('excepted', 'catalog_has_none', 'opdb_unmatched', 'disagrees')

  UNION ALL
  -- `absent` asserts the catalog lacks a machine, which is only true if a search ran.
  -- The ladder has two searches: within the group's linked title (needs the title
  -- link) and by name-and-maker (needs the maker), so a row reaching `absent` with
  -- neither is the classification claiming a machine is missing that nobody looked
  -- for. The same regression guard as IPDB's, widened for the title tier.
  SELECT 'absent_without_candidate_search', opdb_id
  FROM opdb_models_unmatched
  WHERE classification = 'absent'
    AND opdb_manufacturer_slug IS NULL
    AND linked_title_slug IS NULL

  UNION ALL
  -- The resolution is a per-listing aggregate and must stay one row per listing; if
  -- it fans out, every consumer double-counts at once.
  SELECT 'resolution_not_one_row_per_listing', opdb_id
  FROM _eds_opdb_model_resolution GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  -- The ipdb_id route joins the catalog on models.ipdb_id, whose uniqueness
  -- ipdb_checks asserts -- but this view's grain is its own claim, so it is anchored
  -- here too.
  SELECT 'ipdb_route_not_one_row_per_listing', opdb_id
  FROM _eds_opdb_ipdb_route GROUP BY opdb_id HAVING count(*) > 1

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
  -- THE GUARD'S PRECEDENCE. `maker_contested` outranks every confident ladder class,
  -- so a singular maker-decided answer carrying contested rivals must never come back
  -- as a link instruction. A CASE branch reordered above it would silently restore the
  -- exact confident-wrong-answer this exists to prevent -- the same shape of guard as
  -- `moved_successor_misclassified`.
  SELECT 'maker_contested_misclassified', u.opdb_id
  FROM opdb_models_unmatched AS u
  WHERE u.contested_rival_models IS NOT NULL
    AND u.n_candidates = 1
    AND u.match_basis IN ('title_and_maker', 'maker')
    AND u.classification IN ('catalog_holds_unlinked', 'possible_duplicate',
                             'year_unverified')

  UNION ALL
  -- The ladder's contested-pair set and the maker worklist's must not drift: the guard
  -- above and `opdb_manufacturer_pairs_disagreeing` answer the same question from two
  -- definitions, and a divergence means one of them stopped tracking the adjudications.
  SELECT 'disagreeing_pairs_drifted',
         coalesce(a.manufacturer_slug, b.manufacturer_slug) || ' / ' ||
         coalesce(a.opdb_manufacturer_slug, b.opdb_manufacturer_slug)
  FROM _eds_opdb_disagreeing_pairs AS a
  FULL JOIN (SELECT manufacturer_slug, opdb_manufacturer_slug
             FROM opdb_manufacturer_pairs_disagreeing) AS b
    ON  a.manufacturer_slug      = b.manufacturer_slug
    AND a.opdb_manufacturer_slug = b.opdb_manufacturer_slug
  WHERE a.manufacturer_slug IS NULL OR b.manufacturer_slug IS NULL

  UNION ALL
  -- The anchor for the vocabulary section: pinexplore publishing NO assertions at all
  -- reads exactly like a catalog that already carries everything.
  -- Worded without naming the attach alias: the boundary check regex-scans view SQL
  -- and cannot tell an identifier from prose.
  SELECT 'vocabulary_assertions_missing', 'every pinexplore OPDB model vocabulary view is empty'
  WHERE (SELECT count(*) FROM _eds_opdb_vocabulary) = 0;
COMMENT ON VIEW opdb_checks IS
  'Empty when healthy — grain, closed-classification and join-key anchors for the OPDB comparison, plus the exception-slug resolution the inherited manufacturer exceptions demanded.';
