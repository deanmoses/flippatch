-- IDENTITY: which catalog record is each external listing? Both sources decoded into
-- one listing shape, one matching ladder run over them, one classification, one
-- replay.
--
-- IDENTITY, NOT CONTENT. This file decides what a listing IS -- never whether its
-- field values agree. Comparing values presupposes the very link this file exists to
-- earn, and lives downstream of it: scalar fields against the testimony pool in
-- `fields.sql`, credits and specialties and vocabulary in the per-source files.
--
-- `.read` this from a campaign analysis after flipcommons' foundation (the per-source
-- files read it themselves, so a campaign normally reaches for `ipdb.sql` or
-- `opdb.sql` rather than this):
--
--     .read ../flippatch/scripts/analysis/external_data_sources/identity.sql
--
-- It reads `bridge.sql` itself, so the attach, the watermark and the bridge's own
-- invariants come with it.
--
-- WHY ONE IMPLEMENTATION. IPDB and OPDB differ in what they can SAY — OPDB has machine
-- groups and an ipdb_id cross-reference, IPDB has corporate entities and undated
-- listings — but not in how a listing is matched to a catalog model. The decision
-- procedure (candidate tiers, the verdict discipline, the year triangle, the
-- classification lattice, the known-good replay) is one algorithm, and it lives here
-- exactly once. Each source contributes:
--
--   a DECODE      its dump translated into catalog terms (`_eds_ipdb_dump`,
--                 `_eds_opdb_dump`), from which the unified `_eds_listings` shape is
--                 drawn — a leg the source cannot supply is NULL, and every tier
--                 already treats NULL as "this leg does not support the pairing".
--                 IPDB rows carry no group, so the title tier never fires for them:
--                 the same degeneracy the ladder already handles for an OPDB listing
--                 whose group no title links.
--   ENRICHMENTS   evidence with no counterpart in the other source, joined into the
--                 classification ABOVE the shared lattice: OPDB's ipdb_id route,
--                 moved-id changelog and contested-maker guard; IPDB's confirmed
--                 duplicate listings.
--
-- Everything downstream of the match — credits, specialties, vocabulary, titles,
-- maker comparisons, findings, summaries — stays in the per-source files, which read
-- this one.

.read ../flippatch/scripts/analysis/external_data_sources/bridge.sql

-- ═══ DECODE: IPDB ══════════════════════════════════════════════════════════

-- One row per IPDB model, as IPDB states it, decoded into catalog terms.
--
-- Reads pinexplore's MART. It is the only thing here that may be read: the staging and
-- reference layers under it are that repo's working material. The mart is also where
-- the corrections live -- records whose scraped manufacturer IPDB's own page denies
-- arrive with those fields already cleared, and IPDB's two ways of writing "no
-- manufacturer" (ids 0 and 328) arrive as NULL rather than as a company.
--
-- That last point is why the filters downstream are `IS NOT NULL` rather than a NOT IN
-- against a list of placeholder ids. A forgotten `IS NOT NULL` compares against NULL
-- and matches nothing; a forgotten NOT IN compares against a real corporate entity and
-- matches the wrong one.
--
-- Every `ipdb_` column is IPDB's assertion; the two slugs are that assertion decoded, not
-- the catalog's own answer -- `ipdb_corporate_entity_slug` is the corporate entity IPDB's
-- id points at, which is the thing the catalog's own value gets compared against.
--
-- The decode joins on `ipdb_manufacturer_id`, the catalog's handle on an IPDB maker,
-- which resolves all but two of them and cannot multiply the grain: that column is unique
-- across live corporate entities, asserted in `identity_checks`.
-- MATERIALIZED, with the view above it kept as the DEFINITION WITNESS. The relation is
-- scanned dozens of times per run -- every summary branch, every check -- and as a view
-- each scan re-read and re-joined the dump. As a table it is computed once. The
-- `_source` view exists so `external_data_sources_boundary_checks` can still see the
-- `px.` reads: that guard regex-scans VIEW definitions, and DuckDB keeps no defining SQL
-- for a table, so materializing without the witness would silently retire the guard on
-- exactly the relations that read pinexplore. Never read `_source` directly.
CREATE OR REPLACE VIEW _eds_ipdb_dump_source AS
  SELECT
    im.ipdb_id,
    im.name                                                         AS ipdb_name,
    im.ipdb_corporate_entity_id,
    im.corporate_entity_text                                        AS ipdb_corporate_entity_text,
    -- The HEADER-PARSED year, never `date_of_manufacture`: that field is a timestamp,
    -- so a year-only listing arrives padded to Jan 1 and its year is indistinguishable
    -- from real precision -- the trap campaigns 0277/0268 document. The header parse
    -- covers every dated listing (checked: zero rows carry a date the header lacks) and
    -- brings `date_kind`, without which the year is not comparable: a project year
    -- answers `project_year`, never `production_year`. The kind rides beside the year
    -- so no consumer can take one without seeing the other.
    im.additional_details_date_year::INT   AS ipdb_date_year,
    im.additional_details_date_kind        AS ipdb_date_kind,
    im.carried_forward,
    im.duplicate_of_ipdb_id,
    corporate_entity.slug                                           AS ipdb_corporate_entity_slug,
    corporate_entity.manufacturer_slug                              AS ipdb_manufacturer_slug
  FROM px.ipdb.models AS im
  LEFT JOIN corporate_entities AS corporate_entity
    ON corporate_entity.ipdb_manufacturer_id = im.ipdb_corporate_entity_id;
CREATE OR REPLACE TABLE _eds_ipdb_dump AS SELECT * FROM _eds_ipdb_dump_source;

-- ═══ DECODE: OPDB ══════════════════════════════════════════════════════════

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
-- maker comparison in `opdb.sql` is at that coarser grain. The join cannot multiply the
-- grain: the id is unique across manufacturers, asserted in `identity_checks`.
-- MATERIALIZED, with the view above kept as the DEFINITION WITNESS -- see the IPDB
-- decode for why the witness has to exist. Never read `_source` directly.
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

-- ═══ THE UNIFIED SHAPE ═════════════════════════════════════════════════════

-- The catalog's links per source namespace, one relation: which model carries which
-- external id. External ids are VARCHAR here (OPDB's are opaque strings; IPDB's
-- integers cast canonically), so one join shape serves both.
CREATE OR REPLACE VIEW _eds_model_links AS
            SELECT 'ipdb' AS source, slug, ipdb_id::VARCHAR AS external_id
            FROM models WHERE ipdb_id IS NOT NULL
  UNION ALL SELECT 'opdb', slug, opdb_id
            FROM models WHERE opdb_id IS NOT NULL;

-- One row per external listing, either source, with nullable legs.
CREATE OR REPLACE VIEW _eds_listings AS
            SELECT 'ipdb' AS source,
                   ipdb_id::VARCHAR         AS external_id,
                   ipdb_name                AS name,
                   ipdb_manufacturer_slug   AS maker_slug,
                   ipdb_date_year           AS year,
                   NULL::VARCHAR            AS group_key   -- IPDB has no grouping
            FROM _eds_ipdb_dump
  UNION ALL SELECT 'opdb', opdb_id, opdb_name, opdb_manufacturer_slug,
                   opdb_year, title_opdb_id
            FROM _eds_opdb_dump;

-- ═══ ENRICHMENTS: OPDB ═════════════════════════════════════════════════════

-- ─── the ipdb_id route: link-by-id, above the whole name ladder ────────────
--
-- 92% of OPDB listings cross-reference an IPDB id, and the catalog's own ipdb_id
-- links are unique (asserted in `identity_checks`) -- so an unmatched listing whose
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

-- The maker disagreements, at PAIR grain and derived once, so the ladder's contested
-- guard and the maker worklist in `opdb.sql` cannot drift apart about which pairings
-- are contested. `opdb_checks` asserts the two agree.
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
-- exactly this row and no other (the known-good replay below).
--
-- Deliberately NARROW. Keying on "the OPDB maker appears in some contested pair" would
-- taint all 762 Bally listings for the sake of two Bally Wulff machines. The condition is
-- a same-named RIVAL under the contested counterpart -- the actual ambiguity -- which
-- today flags one listing in the replay and none in the live worklist.
--
-- The winner cannot be its own rival: at tiers 1 and 2 its manufacturer equals the
-- listing's OPDB maker, and a contested pair is by construction two DIFFERENT makers.
--
-- IPDB deliberately has no counterpart: its maker leg is an ID decode
-- (`corporate_entities.ipdb_manufacturer_id`), not a cross-system name pairing, so the
-- "same name under a contested counterpart" ambiguity cannot arise. The guard joins on
-- OPDB alone, and IPDB rows pass it vacuously.
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

-- ═══ THE MODEL-MATCHING LADDER ═════════════════════════════════════════════
--
-- Matching an external listing to a catalog model runs down evidence tiers, strongest
-- first. Above everything sits OPDB's ipdb_id route -- an id, not a match, applied in
-- the worklist below. The catalog-id tier is implicit -- the worklist is scoped to
-- listings whose id no model carries -- and below it:
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
-- IPDB rows carry no group, so for them only tier 2 can fire and the ladder reduces
-- to the name-and-maker search -- the degenerate case, not a second code path.
--
-- The first tier holding any candidate answers, and it answers PLURALLY when it holds
-- more than one: a verdict is published only when the winning tier holds exactly one
-- model, and anything else is `multiple_candidates` -- never the alphabetically first
-- match dressed up as an answer. A bare name match with neither title nor maker
-- behind it is not a candidate at all; that is `_eds_namesakes`, evidence rather
-- than an answer.
--
-- THE THIRD LEG OF THE TRIANGLE IS THE YEAR, and it REFUTES, never elects. Model
-- identity is (name, maker, year) with the year allowed off by one but no more; a
-- candidate whose catalog year (production or project, either kind corroborates
-- identity) sits more than a year away is not this machine -- a remake, a different
-- era's namesake -- and leaves the pool. It does not vanish: `year_conflict`
-- classifies the listings it strands, and the refuted list rides the worklist row.
-- Year CORROBORATION never breaks a plural tie, because the true match can be the
-- yearless candidate -- Meteor's is -- and electing the dated one is the
-- arbitrary-pick bug wearing a year. A candidate with no catalog year cannot be
-- refuted; absence refutes nothing. A sixth of IPDB's listings state no year, so on
-- that side the triangle closes only where both sides date the machine; OPDB states a
-- year on every listing.

-- One row per (listing, candidate model): every catalog model answering the listing's
-- name with at least one tier of support, flagged by tier.
--
-- Matched on `name_norm`, not `name_key`: `name_key` strips a trailing parenthetical,
-- and the parenthetical IS the identity here -- the unmatched sets are full of
-- "(Pro)" / "(Premium)" / "(LE)" edition rows whose base machine the catalog holds.
--
-- The flags coalesce to false so a NULL on either side (no linked title, no resolved
-- maker) reads as "this tier does not support the pairing", not as unknown.
-- MATERIALIZED: the ladder is the layer's most-scanned computation and, since it is
-- deliberately unscoped for the replay, its most expensive. Computed once per session.
CREATE OR REPLACE TABLE _eds_candidates AS
  SELECT
    l.source,
    l.external_id,
    m.slug             AS model_slug,
    ml.external_id     AS model_linked_id,   -- the candidate's own link in this namespace
    m.production_year,
    coalesce(m.production_year, m.project_year) AS model_display_year,
    coalesce(m.title_id = t.id, false)                  AS in_group_title,
    coalesce(m.manufacturer_slug = l.maker_slug, false) AS maker_matches,
    -- NULL-safe by construction: a NULL year on either side lands `unknown` in the
    -- first branch; in the second, an `abs` against a NULL catalog year is NULL, and
    -- `NULL OR true` is true while `NULL OR false` falls through to `refuted` --
    -- which is correct, because the only year the catalog states is then off.
    CASE WHEN l.year IS NULL
           OR (m.production_year IS NULL AND m.project_year IS NULL)  THEN 'unknown'
         WHEN abs(l.year - m.production_year) <= 1
           OR abs(l.year - m.project_year) <= 1                       THEN 'corroborated'
         ELSE                                                              'refuted'
    END AS year_verdict
  FROM _eds_listings AS l
  LEFT JOIN titles AS t ON t.opdb_id = l.group_key
  INNER JOIN models AS m ON name_norm(m.name) = name_norm(l.name)
  LEFT JOIN _eds_model_links AS ml
    ON ml.source = l.source AND ml.slug = m.slug
  -- NOT filtered to unmatched listings, deliberately. Scoping the ladder to the rows
  -- it is asked about would make it untestable: the known-good replay below re-derives
  -- the links we ALREADY hold and compares, which is only evidence about the shipping
  -- matcher if it runs the shipping views rather than a copy of them. Every consumer
  -- that wants only unmatched listings filters at its own site -- `_eds_models_unmatched`
  -- in its WHERE, `_eds_opdb_group_titles` in its candidate branch -- so live output is
  -- unchanged and the replay reads the real thing.
  WHERE coalesce(m.title_id = t.id, false)
     OR coalesce(m.manufacturer_slug = l.maker_slug, false);

-- One row per listing with any candidate: the winning tier's answer, verdict columns
-- filled ONLY when it is unique. This is the one place "uniquely resolved" is defined
-- -- exactly one candidate at the winning tier -- so every consumer (the worklist,
-- OPDB's group-title verdicts, the replay) inherits the same gate instead of
-- re-deriving it, which is how the too-loose tier-2 gate bug happened last time.
--
-- With exactly one winning row, `min` of each column reads that row whole, NULLs
-- included; with more than one, every verdict column is NULL and the sorted capped
-- list plus `n_candidates` carry the plural answer.
-- MATERIALIZED for the same reason as the candidates it aggregates.
CREATE OR REPLACE TABLE _eds_model_resolution AS
  WITH winning AS (
    SELECT *,
      CASE WHEN in_group_title AND maker_matches THEN 1
           WHEN maker_matches THEN 2
           ELSE 3 END AS tier
    FROM _eds_candidates
    -- The triangle's refutation: a candidate more than a year away is not this
    -- machine and never enters a pool. It resurfaces through `refuted` below.
    WHERE year_verdict <> 'refuted'
    QUALIFY tier = min(tier) OVER (PARTITION BY source, external_id)
  ),
  refuted AS (
    -- A refuted candidate that is already LINKED says so: whether the near-miss is
    -- spoken for by another external id is the fact that turns "investigate a year
    -- discrepancy" into "this is a different machine; create it". `upper(source)`
    -- spells the namespace the id lives in -- "links IPDB 6029" / "links OPDB G50PZ".
    SELECT
      source, external_id,
      count(*) AS n_year_refuted,
      list_sort(list(model_slug || ' (' || coalesce(model_display_year::VARCHAR, '?')
        || coalesce(', links ' || upper(source) || ' ' || model_linked_id, '') || ')'))[:5]
        AS year_refuted_models
    FROM _eds_candidates
    WHERE year_verdict = 'refuted'
    GROUP BY source, external_id
  ),
  verdicts AS (
    SELECT
      source, external_id,
      match_basis,
      n_candidates,
      candidate_model_slugs,
      -- `resolved_year_verdict` qualifies a verdict: 'corroborated' means the full
      -- triangle agrees, 'unknown' that one side states no year to check.
      CASE WHEN n_candidates = 1 THEN only_year_verdict END               AS resolved_year_verdict,
      CASE WHEN n_candidates = 1 AND n_linked = 0 THEN only_slug END      AS unlinked_model_slug,
      CASE WHEN n_candidates = 1 AND n_linked = 1 THEN only_slug END      AS linked_model_slug,
      CASE WHEN n_candidates = 1 AND n_linked = 1 THEN only_linked_id END AS linked_model_external_id,
      CASE WHEN n_candidates = 1 AND n_linked = 1 THEN only_year END      AS linked_model_production_year
    FROM (
      SELECT
        source, external_id,
        CASE min(tier) WHEN 1 THEN 'title_and_maker'
                       WHEN 2 THEN 'maker'
                       ELSE        'title' END              AS match_basis,
        count(*)                                            AS n_candidates,
        count(*) FILTER (WHERE model_linked_id IS NOT NULL) AS n_linked,
        list_sort(list(model_slug))[:5]                     AS candidate_model_slugs,
        min(model_slug)                                     AS only_slug,
        min(model_linked_id)                                AS only_linked_id,
        min(production_year)                                AS only_year,
        min(year_verdict)                                   AS only_year_verdict
      FROM winning
      GROUP BY source, external_id
    )
  )
  -- FULL join: a listing whose every candidate was year-refuted has no verdict row,
  -- and its refuted evidence is exactly what the worklist needs to say so.
  SELECT
    source, external_id,
    v.match_basis,
    coalesce(v.n_candidates, 0)     AS n_candidates,
    v.candidate_model_slugs,
    v.resolved_year_verdict,
    v.unlinked_model_slug,
    v.linked_model_slug,
    v.linked_model_external_id,
    v.linked_model_production_year,
    coalesce(rf.n_year_refuted, 0)  AS n_year_refuted,
    rf.year_refuted_models
  FROM verdicts AS v
  FULL JOIN refuted AS rf USING (source, external_id);

-- Catalog models answering to an unmatched listing's NAME, whatever their maker.
--
-- The weaker companion of the ladder, and it exists because every tier needs a leg
-- beyond the name. Where the listing has none, the ladder cannot match anything at
-- all, and a count of zero there is "not looked for" rather than "not there" -- the
-- two read identically until this says otherwise.
--
-- A namesake is not a candidate. Machine names repeat freely across makers and decades
-- (eight live models are called Lady Luck), so this evidences the question rather than
-- answering it: a non-zero count means read the source page before creating a record.
CREATE OR REPLACE VIEW _eds_namesakes AS
  SELECT l.source, l.external_id,
         count(*)                    AS n_namesake_models,
         list_sort(list(m.slug))[:5] AS namesake_model_slugs
  FROM _eds_listings AS l
  INNER JOIN models AS m ON name_norm(m.name) = name_norm(l.name)
  WHERE NOT EXISTS (SELECT 1 FROM _eds_model_links AS x
                    WHERE x.source = l.source AND x.external_id = l.external_id)
  GROUP BY l.source, l.external_id;

-- ═══ THE WORKLIST CORE ═════════════════════════════════════════════════════

-- One row per unmatched listing, either source, classified. PRIVATE: the public
-- spellings are `ipdb_models_unmatched` and `opdb_models_unmatched` in the per-source
-- files, which join their dump's own columns back on and document the classifications
-- in each source's terms.
--
-- The CASE runs per-source overrides first, in the shipping precedence, then the
-- shared lattice:
--
--   duplicate_listing (IPDB)  a confirmed IPDB-side double entry whose twin the
--                             catalog links; carried on the mart row itself.
--   moved_successor (OPDB)    some catalog model's stale opdb_id names this id as
--                             successor; the repoint reported by `opdb-id-moved`
--                             covers it. First among OPDB classes because the
--                             successor usually also name-matches that very model.
--   the ipdb_id route (OPDB)  outranks the whole name ladder: an id, not a match, so
--                             no triangle applies. Only a CLEAN chain links; its
--                             exceptions fall through to the ladder with the
--                             evidence riding the row.
--   maker_contested (OPDB)    a singular maker-decided answer whose maker pairing is
--                             itself contested goes to manual adjudication instead of
--                             becoming a link instruction. Ranked below the ipdb_id
--                             route (an id outranks a name ambiguity) and above every
--                             confident ladder class.
--
-- The shared lattice: the confident classes demand the CLOSED triangle -- unique
-- candidate AND the year corroborated. A unique match whose year leg cannot close is
-- `year_unverified`, never a link instruction (the identity doc's NEVER-GUESS rule).
-- `maker_unresolved` means NO search leg was available -- no resolved maker and no
-- linked title to search within (for IPDB rows the title half is vacuous) -- so
-- `absent` is asserted only where a search actually ran.
CREATE OR REPLACE VIEW _eds_models_unmatched AS
  SELECT
    l.source,
    l.external_id,
    l.maker_slug,
    lt.slug                                   AS linked_title_slug,
    CASE
      WHEN dup.external_id IS NOT NULL        THEN 'duplicate_listing'
      WHEN mv.model_slug IS NOT NULL          THEN 'moved_successor'
      WHEN ir.unlinked_model_slug IS NOT NULL THEN 'catalog_holds_unlinked'
      WHEN ir.linked_model_slug IS NOT NULL   THEN 'possible_duplicate'
      WHEN mc.opdb_id IS NOT NULL
       AND r.n_candidates = 1
       AND r.match_basis IN ('title_and_maker', 'maker') THEN 'maker_contested'
      WHEN r.unlinked_model_slug IS NOT NULL
       AND r.resolved_year_verdict = 'corroborated' THEN 'catalog_holds_unlinked'
      WHEN r.linked_model_slug IS NOT NULL
       AND r.resolved_year_verdict = 'corroborated' THEN 'possible_duplicate'
      WHEN r.n_candidates = 1                 THEN 'year_unverified'
      WHEN r.n_candidates > 1                 THEN 'multiple_candidates'
      WHEN r.n_year_refuted > 0               THEN 'year_conflict'
      WHEN l.maker_slug IS NULL
       AND lt.id IS NULL                      THEN 'maker_unresolved'
      ELSE                                         'absent'
    END AS classification,
    CASE WHEN ir.unlinked_model_slug IS NOT NULL
           OR ir.linked_model_slug IS NOT NULL THEN 'ipdb_id'
         ELSE r.match_basis END               AS match_basis,
    coalesce(ir.unlinked_model_slug, r.unlinked_model_slug) AS unlinked_model_slug,
    coalesce(ir.linked_model_slug, r.linked_model_slug)     AS linked_model_slug,
    coalesce(ir.linked_model_opdb_id, r.linked_model_external_id) AS linked_model_external_id,
    coalesce(CASE WHEN ir.linked_model_slug IS NOT NULL
                  THEN ir.ipdb_route_model_production_year END,
             r.linked_model_production_year)  AS linked_model_production_year,
    r.resolved_year_verdict,
    coalesce(r.n_candidates, 0)               AS n_candidates,
    r.candidate_model_slugs,
    coalesce(r.n_year_refuted, 0)             AS n_year_refuted,
    r.year_refuted_models,
    coalesce(n.n_namesake_models, 0)          AS n_namesake_models,
    n.namesake_model_slugs,
    -- per-source evidence, NULL for the other source
    dup.duplicate_of_ipdb_id,
    mv.model_slug                             AS moved_from_model_slug,
    ir.opdb_ipdb_id,
    ir.ipdb_route_model_slug,
    ir.ipdb_id_chain,
    ir.n_listings_sharing_ipdb_id,
    -- The evidence behind `maker_contested`: present on any row where the ambiguity
    -- exists, whatever the classification, so a reader can see it was considered
    -- rather than infer it from the class.
    mc.contested_rival_models
  FROM _eds_listings AS l
  LEFT JOIN _eds_model_resolution AS r ON r.source = l.source AND r.external_id = l.external_id
  LEFT JOIN _eds_namesakes        AS n ON n.source = l.source AND n.external_id = l.external_id
  LEFT JOIN titles AS lt ON lt.opdb_id = l.group_key
  -- per-source enrichments; each join is scoped to its source, so the other's rows
  -- pass through untouched
  LEFT JOIN (SELECT ipdb_id::VARCHAR AS external_id, duplicate_of_ipdb_id
             FROM _eds_ipdb_dump WHERE duplicate_of_ipdb_id IS NOT NULL) AS dup
    ON l.source = 'ipdb' AND dup.external_id = l.external_id
  LEFT JOIN _eds_opdb_ipdb_route AS ir
    ON l.source = 'opdb' AND ir.opdb_id = l.external_id
  LEFT JOIN _eds_opdb_maker_contested AS mc
    ON l.source = 'opdb' AND mc.opdb_id = l.external_id
  -- A scalar subquery, so it cannot fan the grain out even if several stale ids moved
  -- onto one successor (a merge); `min` then picks a deterministic representative and
  -- the others are still visible in `opdb_ids_stale`.
  LEFT JOIN LATERAL (
    SELECT min(m.slug) AS model_slug
    FROM models AS m
    INNER JOIN px.opdb.model_ids AS i ON i.opdb_id = m.opdb_id
    WHERE l.source = 'opdb' AND i.status = 'moved' AND i.current_opdb_id = l.external_id
  ) AS mv ON true
  WHERE NOT EXISTS (SELECT 1 FROM _eds_model_links AS x
                    WHERE x.source = l.source AND x.external_id = l.external_id);

-- ═══ THE KNOWN-GOOD REPLAY ═════════════════════════════════════════════════
--
-- Does the matcher get right the answers we already know? 8k catalog models already
-- carry an IPDB or OPDB id. Those are the answer key. This covers up the answers: for
-- every already-linked listing it asks the ladder "which catalog model is this?", and
-- compares the answer to what's already on record. Repeat eight thousand times and
-- the question "is the matcher broken?" stops being a matter of belief.
--
-- IT RUNS THE SHIPPING LADDER, NOT A COPY OF IT: `_eds_candidates` and
-- `_eds_model_resolution` are deliberately unscoped (see the comment at each), so
-- this reads the same relations the worklist reads. If the ladder changes, this
-- measures the change; that property must survive any future edit.
--
-- WHAT IT DOES AND DOES NOT COVER. It exercises the NAME LADDER -- the heuristic
-- part, where a wrong answer is possible. The ipdb_id route above the ladder is an id
-- rather than a match and is scoped to unmatched listings, so it does not fire here;
-- neither do the manufacturer and title stages, which have no replay yet. The bar is
-- the one the worklist itself acts on: a unique candidate at the winning tier, the
-- year corroborated, and the maker leg uncontested. Anything short of that is not an
-- answer the layer would have offered, so it is not counted as one either.
--
-- THE ANSWER KEY IS NOT AXIOMATIC. A disagreement means the ladder and the recorded
-- link differ; which one is wrong is a question for a person.
-- `medieval-madness-remake-royal-edition` carries IPDB 6264 while IPDB's own name for
-- 6264 is the Limited Edition -- a real editorial disagreement, not a matcher bug. So
-- the per-row views are WORKLISTS, never `*_checks`: a row is something to read, and
-- gating the runner on it would fail every run over a question nobody has answered yet.
--
-- A DISAGREEMENT IS NOT AUTOMATICALLY A BAD LINK, which is why the counts split on
-- `would_link`. Most disagreements are answers the layer would have classified
-- `possible_duplicate` -- the candidate already carries someone else's id, so the
-- worklist says "read both pages" rather than "backfill this". Getting one of those
-- different costs a reader two page loads. The `would_link` half is the real measure:
-- an answer the layer would have handed over as a link, that the record contradicts.
--
-- ONE CAVEAT WORTH CARRYING. Some catalog names and years were themselves patched in
-- from these sources, so the agreement rate is flattered. It does not rescue the case
-- that matters -- choosing among same-named models is exactly where a derived name
-- gives no help -- but the headline number is an upper bound, not a guarantee.
--
-- MATERIALIZED: the summary and the checks between them scan this many times.
CREATE OR REPLACE TABLE _eds_replay AS
  SELECT
    l.source,
    l.external_id,
    l.name,
    l.year,
    l.maker_slug,
    truth.slug                                           AS recorded_model_slug,
    coalesce(r.unlinked_model_slug, r.linked_model_slug) AS ladder_model_slug,
    r.match_basis,
    r.resolved_year_verdict,
    mc.contested_rival_models,
    -- WOULD THE LAYER HAVE CALLED THIS A LINK? Only if nothing else is sitting on the
    -- candidate. A candidate already carrying a DIFFERENT id is `possible_duplicate` in
    -- the worklist -- read both pages -- so a wrong answer there costs a reader two page
    -- loads, not a bad link. Under replay the truth model necessarily carries this very
    -- listing's id, and that self-occupancy is not somebody else's claim, so it counts
    -- as free. This split is the whole point of the two disagreement metrics: the
    -- `would_link` count is the one that must stay at zero.
    (r.unlinked_model_slug IS NOT NULL
     OR r.linked_model_external_id = l.external_id)                   AS would_link,
    coalesce(r.unlinked_model_slug, r.linked_model_slug) = truth.slug AS agrees
  FROM _eds_listings AS l
  INNER JOIN _eds_model_links AS truth
    ON truth.source = l.source AND truth.external_id = l.external_id
  INNER JOIN _eds_model_resolution AS r
    ON r.source = l.source AND r.external_id = l.external_id
  LEFT JOIN _eds_opdb_maker_contested AS mc
    ON l.source = 'opdb' AND mc.opdb_id = l.external_id
  -- The live confident bar, mirrored: unique candidate, year corroborated, maker leg
  -- uncontested. Kept in step with `_eds_models_unmatched`'s confident classes.
  WHERE r.n_candidates = 1
    AND r.resolved_year_verdict = 'corroborated'
    AND mc.opdb_id IS NULL;

CREATE OR REPLACE VIEW opdb_known_good_replay AS
  SELECT external_id AS opdb_id, name AS opdb_name, year AS opdb_year,
         maker_slug AS opdb_manufacturer_slug, recorded_model_slug, ladder_model_slug,
         match_basis, resolved_year_verdict, contested_rival_models, would_link
  FROM _eds_replay
  WHERE source = 'opdb' AND NOT agrees
  ORDER BY would_link DESC, opdb_id;
COMMENT ON VIEW opdb_known_good_replay IS
  'Worklist — one row per already-linked OPDB listing where replaying the name ladder lands on a different model than the link on record, would_link first: true means the layer would have offered it as a backfill and is the serious kind, false means it would have gone to possible_duplicate for a human anyway. Empty is the healthy state; a row is an adjudication, not necessarily a bug.';

CREATE OR REPLACE VIEW ipdb_known_good_replay AS
  SELECT external_id::BIGINT AS ipdb_id, name AS ipdb_name, year AS ipdb_date_year,
         maker_slug AS ipdb_manufacturer_slug, recorded_model_slug, ladder_model_slug,
         resolved_year_verdict, would_link
  FROM _eds_replay
  WHERE source = 'ipdb' AND NOT agrees
  ORDER BY would_link DESC, ipdb_id;
COMMENT ON VIEW ipdb_known_good_replay IS
  'Worklist — one row per already-linked IPDB listing where replaying the name ladder lands on a different model than the link on record, would_link first: true means the layer would have offered it as a backfill and is the serious kind, false means it would have gone to possible_duplicate for a human anyway. Empty is the healthy state; a row is an adjudication, not necessarily a bug.';

-- The headline: how many answers the replay produced and how many it got different.
-- Source-labelled so these land beside each source's own metrics in the run summary.
-- Every fixed metric is emitted per source even at zero -- the two that matter most
-- are deliberately never absent: a disagreement the layer would have PUBLISHED as a
-- link is the failure the replay exists to detect, and its zero must stay visible.
CREATE OR REPLACE VIEW known_good_replay_summary AS
  WITH s AS (SELECT unnest(['ipdb', 'opdb']) AS source)
            SELECT s.source, 'replay_answers' AS metric,
                   (SELECT count(*) FROM _eds_replay r WHERE r.source = s.source) AS value FROM s
  UNION ALL SELECT s.source, 'replay_answers_would_link',
                   (SELECT count(*) FROM _eds_replay r WHERE r.source = s.source AND would_link) FROM s
  -- The tier breakdown, OPDB only: IPDB has one tier, so a breakdown would restate
  -- `replay_answers`.
  UNION ALL SELECT source, 'replay_answers_' || match_basis, count(*)
            FROM _eds_replay WHERE source = 'opdb' GROUP BY source, match_basis
  UNION ALL SELECT s.source, 'REPLAY_DISAGREEMENTS_would_link',
                   (SELECT count(*) FROM _eds_replay r WHERE r.source = s.source AND NOT agrees AND would_link) FROM s
  UNION ALL SELECT s.source, 'replay_disagreements_to_human',
                   (SELECT count(*) FROM _eds_replay r WHERE r.source = s.source AND NOT agrees AND NOT would_link) FROM s;
COMMENT ON VIEW known_good_replay_summary IS
  'How many links the replay re-derived confidently and how many came back different, per source — the OPDB half broken out by the tier that decided.';

-- Empty when healthy. Invariants of the replay itself, never findings about the data.
CREATE OR REPLACE VIEW known_good_replay_checks AS
  -- THE CHECK THE REPLAY EXISTS FOR. A replay that answers nothing scores a flawless
  -- zero-out-of-zero, and a broken join looks exactly like a perfect matcher -- the
  -- precise false confidence it was written to prevent. Both sources answer thousands
  -- of already-linked listings, so a collapse to nothing is a wiring fault.
  SELECT 'replay_produced_no_answers' AS check_name, s.source AS detail
  FROM (VALUES ('ipdb'), ('opdb')) AS s(source)
  WHERE NOT EXISTS (SELECT 1 FROM _eds_replay AS r WHERE r.source = s.source)

  UNION ALL
  -- One row per listing, or every count above is quietly multiplied.
  SELECT source || '_replay_not_one_row_per_listing', external_id
  FROM _eds_replay GROUP BY source, external_id HAVING count(*) > 1

  UNION ALL
  -- THE LADDER MUST STAY UNSCOPED, or the replay silently tests nothing: scoping the
  -- candidate table back to unmatched listings would empty it. The check above catches
  -- a total collapse; this one catches the specific regression, by asserting the
  -- ladder still reasons about listings that ARE linked.
  SELECT s.source || '_ladder_rescoped_to_unmatched', 'no linked listing reaches the resolution'
  FROM (VALUES ('ipdb'), ('opdb')) AS s(source)
  WHERE NOT EXISTS (
    SELECT 1 FROM _eds_model_resolution AS r
    INNER JOIN _eds_model_links AS l
      ON l.source = s.source AND r.source = s.source AND l.external_id = r.external_id);
COMMENT ON VIEW known_good_replay_checks IS
  'Empty when healthy — the replay actually ran, holds one row per listing, and the ladder is still unscoped enough to reach already-linked listings. A row means the replay is measuring nothing, which reads identically to a perfect score.';

-- ═══ SUMMARY & CHECKS ══════════════════════════════════════════════════════

-- The identity machinery's own headline, for a session editing this file
-- (`PREFIX=identity`). The per-source summaries in `ipdb.sql` / `opdb.sql` remain the
-- layer's public readout.
CREATE OR REPLACE VIEW identity_summary AS
  SELECT * FROM (
              SELECT source || '_listings' AS metric, count(*) AS value
              FROM _eds_listings GROUP BY source
    UNION ALL SELECT source || '_unmatched_listings', count(*)
              FROM _eds_models_unmatched GROUP BY source
    UNION ALL SELECT source || '_' || metric, value FROM known_good_replay_summary
              WHERE metric IN ('replay_answers', 'REPLAY_DISAGREEMENTS_would_link')
  ) ORDER BY metric;
COMMENT ON VIEW identity_summary IS
  'The identity machinery''s own headline — listings and unmatched counts per source, and the replay''s answer and must-stay-zero disagreement counts. The layer''s public readout is the per-source summaries.';

-- Empty when healthy. Invariants of the identity machinery, never findings about the data.
CREATE OR REPLACE VIEW identity_checks AS
  -- The catalog-side decode keys. Not unique by construction, and a second row would
  -- multiply every count taken off the dumps.
  SELECT 'corporate_entity_ipdb_id_not_unique' AS check_name,
         ipdb_manufacturer_id::VARCHAR AS detail
  FROM corporate_entities
  WHERE ipdb_manufacturer_id IS NOT NULL
  GROUP BY ipdb_manufacturer_id HAVING count(*) > 1

  UNION ALL
  SELECT 'manufacturer_opdb_id_not_unique', opdb_manufacturer_id::VARCHAR
  FROM manufacturers
  WHERE opdb_manufacturer_id IS NOT NULL
  GROUP BY opdb_manufacturer_id HAVING count(*) > 1

  UNION ALL
  -- The link keys everything rests on: every comparison assumes one catalog record
  -- per external id, and a duplicate would double-count silently everywhere at once.
  -- One check over both namespaces -- which also closes a gap: models.ipdb_id
  -- uniqueness was claimed by comments but never asserted before.
  SELECT 'model_external_id_not_unique', source || ' ' || external_id
  FROM _eds_model_links GROUP BY source, external_id HAVING count(*) > 1

  UNION ALL
  SELECT 'title_opdb_id_not_unique', opdb_id
  FROM titles WHERE opdb_id IS NOT NULL
  GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  -- The dumps are one row per listing by construction; the union must keep it so.
  SELECT 'listings_not_one_row_per_listing', source || ' ' || external_id
  FROM _eds_listings GROUP BY source, external_id HAVING count(*) > 1

  UNION ALL
  -- The per-listing aggregates must stay one row per listing; if one fans out, every
  -- consumer double-counts at once.
  SELECT 'resolution_not_one_row_per_listing', source || ' ' || external_id
  FROM _eds_model_resolution GROUP BY source, external_id HAVING count(*) > 1

  UNION ALL
  SELECT 'namesakes_not_one_row_per_listing', source || ' ' || external_id
  FROM _eds_namesakes GROUP BY source, external_id HAVING count(*) > 1

  UNION ALL
  SELECT 'unmatched_not_one_row_per_listing', source || ' ' || external_id
  FROM _eds_models_unmatched GROUP BY source, external_id HAVING count(*) > 1

  UNION ALL
  -- The ipdb_id route joins the catalog on models.ipdb_id, whose uniqueness is
  -- asserted above -- but this view's grain is its own claim, so it is anchored too.
  SELECT 'ipdb_route_not_one_row_per_listing', opdb_id
  FROM _eds_opdb_ipdb_route GROUP BY opdb_id HAVING count(*) > 1

  UNION ALL
  -- The classification vocabulary lives in the rule registry (`bridge.sql`), and only
  -- there: an emitted class the registry has never heard of means the CASE grew a
  -- branch nobody decided a finding policy for. Checked per source, because each
  -- source's worklist registers its own class set (only OPDB has moved_successor and
  -- maker_contested; only IPDB has duplicate_listing).
  SELECT 'classification_unregistered', u.source || ' -> ' || u.classification
  FROM (SELECT DISTINCT source, classification FROM _eds_models_unmatched) AS u
  WHERE NOT EXISTS (
    SELECT 1 FROM _eds_rule_registry AS r
    WHERE r.detail_view = u.source || '_models_unmatched'
      AND r.classification = u.classification)

  UNION ALL
  -- The CASE precedence. A confirmed duplicate also matches the `possible_duplicate`
  -- shape by construction, so a branch reordered above it would silently demote these
  -- and they would read as work to do.
  SELECT 'confirmed_duplicate_misclassified', external_id
  FROM _eds_models_unmatched
  WHERE duplicate_of_ipdb_id IS NOT NULL
    AND classification <> 'duplicate_listing'

  UNION ALL
  -- Same guard, same reason: a successor usually also name-matches the model holding
  -- the old id, so a branch reordered above `moved_successor` would silently demote
  -- these to `possible_duplicate` and the repoint would read as new work.
  SELECT 'moved_successor_misclassified', external_id
  FROM _eds_models_unmatched
  WHERE moved_from_model_slug IS NOT NULL
    AND classification <> 'moved_successor'

  UNION ALL
  -- THE GUARD'S PRECEDENCE. `maker_contested` outranks every confident ladder class,
  -- so a singular maker-decided answer carrying contested rivals must never come back
  -- as a link instruction. A CASE branch reordered above it would silently restore
  -- the exact confident-wrong-answer the guard exists to prevent.
  SELECT 'maker_contested_misclassified', external_id
  FROM _eds_models_unmatched
  WHERE contested_rival_models IS NOT NULL
    AND n_candidates = 1
    AND match_basis IN ('title_and_maker', 'maker')
    AND classification IN ('catalog_holds_unlinked', 'possible_duplicate',
                           'year_unverified')

  UNION ALL
  -- `absent` is the one classification that ASSERTS something about the catalog
  -- rather than reporting what was found, and it is only true if a search ran. The
  -- ladder has two searches: within the group's linked title (needs the title link)
  -- and by name-and-maker (needs the maker), so a row reaching `absent` with neither
  -- is the classification claiming a machine is missing that nobody looked for. That
  -- is exactly the bug `maker_unresolved` was added for, and this is its regression
  -- guard -- one copy, both sources: for IPDB rows the title half is vacuous.
  SELECT 'absent_without_candidate_search', source || ' ' || external_id
  FROM _eds_models_unmatched
  WHERE classification = 'absent'
    AND maker_slug IS NULL
    AND linked_title_slug IS NULL

  UNION ALL
  -- THE CHECK THE EXCEPTIONS LIST DEMANDED AT BIRTH: its predecessor carried a slug the
  -- catalog had renamed, and the exception silently stopped matching. A slug on no live
  -- manufacturer cannot except anything.
  SELECT 'exception_slug_unresolved', ex.manufacturer_slug
  FROM _eds_opdb_manufacturer_exceptions AS ex
  WHERE NOT EXISTS (SELECT 1 FROM manufacturers AS f WHERE f.slug = ex.manufacturer_slug);
COMMENT ON VIEW identity_checks IS
  'Empty when healthy — decode and link-key uniqueness, grain anchors for every identity relation, the closed classification set, the CASE-precedence guards, and the exception-slug resolution. Invariants of the identity machinery, never findings about the data.';
