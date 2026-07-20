-- Gameplay-feature vocabulary analysis for the gameplay_features campaign.
--
-- Goal: find the gameplay features IPDB names in its Notable Features text that
-- never became structured catalog data, so the campaign can extend the
-- gameplay-feature vocabulary and then assign the new features to models.
--
-- ANALYSIS-LOCAL LAYER. The generic catalog decode (the `models` view, the read-only
-- connection, etc.) is FLIPCOMMONS' shared foundation, reused VERBATIM via the
-- `.read` below — flippatch keeps no copy of it. See this dir's README.md.
--
-- HOW TO RUN. This must run with cwd = the flipcommons checkout, so that BOTH the
-- `.read scripts/analysis/catalog.sql` below AND the foundation's own relative
-- `ATTACH backend/db.sqlite3` resolve there. `make analyze` handles the cwd/path
-- resolution and delegates to flipcommons' shared runner (scripts/analysis/analysis),
-- which prints the analysis_context watermark + gpf_summary and gates on
-- gpf_checks. Do not run this file directly:
--
--     P=patches/authoring/0178-gameplay-features/features.sql
--     make analyze FILE=$F PREFIX=gpf                        # summary, gated on checks
--     make analyze FILE=$F Q="FROM gpf_gap LIMIT 60;"        # the gap, by reach
--     make analyze FILE=$F CMD=ui                            # live GUI at localhost:4213
--
-- Nothing is persisted; every count is a live snapshot of the dev DB.
--
-- THE SIGNAL. IPDB's Notable Features is a free-text blob that opens with a
-- comma-separated feature list: "Trap holes (25), Rollover buttons (2), Magic
-- Squares, Bally Hole". The seed harvest that built our 177-feature vocabulary
-- parsed it with a `(N)` filter — it only kept segments carrying a parenthesized
-- COUNT (pinexplore sql/04_staging.sql, `WHERE regexp_matches(segment,
-- '\(\d+\)')`). Every COUNTLESS feature name was silently dropped. That is a
-- systematic hole, not a scatter of misses: a feature IPDB never counts (Magic
-- Squares, Bally Hole, end-of-ball bonus, knocker) could not enter the vocabulary
-- by that path at all.
--
-- So this plan re-parses the same text WITHOUT the count filter and asks, of each
-- distinct segment: does it already resolve to a catalog gameplay feature? The
-- residue — uncounted AND unmatched — is the gap. It is raw and noisy: the blob
-- also carries cabinet facts, scoring limits, reward rules, sound hardware and
-- sentence fragments, and only some of the residue is a genuine playfield
-- mechanism. Section 2's `_gpf_class` is where that human call is recorded.

-- == 1 · FOUNDATION ==========================================================
.read scripts/analysis/catalog.sql

-- == 2 · REFERENCE ===========================================================

-- The catalog's gameplay-feature vocabulary, flattened to every string that should
-- resolve to a feature: the slug, the display name, and each alias. Used to decide
-- whether a parsed IPDB segment is already modelled.
--
-- Built on the foundation's `gameplay_feature_vocab` / `gameplay_feature_aliases`,
-- which this campaign prompted: the foundation had the model→feature GRAIN
-- (`model_gameplay_features`) but no vocabulary, so this view used to reach into
-- fc.catalog_gameplayfeature* directly. Flattening slug/name/alias into one
-- `term` column is the DETECTOR's business and stays analysis-local, exactly as the
-- foundation's comment on theme_aliases says it should.
CREATE OR REPLACE VIEW _gpf_vocab AS
            SELECT slug, name_norm(slug) AS term, 'slug' AS via
            FROM gameplay_feature_vocab
  UNION ALL SELECT slug, name_norm(name), 'name'
            FROM gameplay_feature_vocab
  UNION ALL SELECT feature_slug, name_norm(alias), 'alias'
            FROM gameplay_feature_aliases;

-- The reach threshold the hand classification covers. Terms at or above it are
-- accounted for exhaustively — either as a new feature below or as a call in
-- `_gpf_class` — and gpf_checks enforces that. The long tail below it is left
-- raw, and gpf_summary reports how much reach that leaves unaudited so the prose
-- can't overclaim completeness.
CREATE OR REPLACE VIEW _gpf_threshold AS SELECT 4 AS min_models;

-- ─────────────────────────────────────────────────────────────────────────────
-- THE CAMPAIGN'S VOCABULARY. The single source for BOTH patches: gen.py reads
-- this to emit 0178 (the creates) and 0179 (the assignments), so the feature
-- list exists once and cannot drift between them.
--
-- PRINCIPLE: position is a distinguishing fact, so it earns its own feature under
-- a parent — a Left Kickback Lane is not an alias of Kickback Lanes, it is a
-- child of it, and an Upper Right Kickback Lane is a child of Right Kickback
-- Lane, not the same thing. Only genuine synonyms with no positional content
-- become aliases. The catalog already worked this way before the campaign
-- (`right-side-ball-return-gates` and `mid-field-ball-return-gates` are both
-- children of `ball-return-gates`); this extends it rather than inventing it.
--
-- Columns:
--   slug/name   the feature to create.
--   parents     `gameplay_feature_parent` members. Empty = top-level. Two parents
--               is legal and used where a feature is genuinely both (an Upper
--               Right Ball Return Gate is upper AND right-side).
--   aliases     display-cased synonyms — phrasings with no positional content of
--               their own, folded into the feature rather than split off.
--   terms       normalised IPDB terms that ASSIGN this feature, matched exactly.
--               A term may appear under two features: "left and right dual
--               inlanes" assigns both the left and the right child, because it
--               asserts two features rather than naming a third.
--   pattern     a regex alternative to `terms`, for families whose phrasing is too
--               varied to enumerate (the bingo mechanisms). Loose on purpose and
--               paid for by _gpf_family_excluded.
--   counted     the term's leading number word becomes the membership COUNT
--               ("six cards" → bingo-cards x6). Only where the count IS the fact.
--
-- A feature with NEITHER terms NOR pattern is a TAXONOMY NODE: created because a
-- child needs it as a parent, though no IPDB text names it. Deliberate, and
-- gpf_checks knows to expect zero assignments for it.
CREATE OR REPLACE VIEW _gpf_new AS
  SELECT * FROM (VALUES
    -- ══ Bingo mechanisms — regex families ═════════════════════════════════
    ('magic-squares', 'Magic Squares', []::VARCHAR[], []::VARCHAR[], []::VARCHAR[], 'magic square', false),
    ('magic-screen', 'Magic Screen', [], [], [], 'magic screen', false),
    ('magic-lines', 'Magic Lines', [], [], [], 'magic line', false),
    ('mystic-lines', 'Mystic Lines', [], [], [], 'mystic line', false),
    ('bally-hole', 'Bally Hole', [], ['Ballyhole'], [], 'bally ?hole', false),
    ('bingo-cards', 'Bingo Cards', [], [], ['one card', 'two cards', 'three cards', 'six cards'], NULL, true),
    ('super-cards', 'Super Cards', ['bingo-cards'], [], ['two super cards'], NULL, true),

    -- ══ Ordinary mechanisms the count filter hid — regex families ══════════
    ('detour-gates', 'Detour Gates', ['ball-return-gates'], [], [], 'detour gate', false),
    ('crossover-return-lanes', 'Crossover Return Lanes', ['lanes'], [], [], 'crossover return lane', false),
    ('turret-shooters', 'Turret Shooters', ['ball-shooters'], [], [], 'turret shooter', false),
    ('mini-playfields', 'Mini-Playfields', [], ['Mini Playfields', 'Mini-Bagatelle'], [], 'mini playfield|mini bagatelle', false),
    ('lockdown-bar-buttons', 'Lockdown Bar Buttons', [], ['Action Button'], [], 'button on (the )?lockdown bar', false),
    ('action-rings', 'Action Rings', [], [], [], 'action ring', false),
    ('ball-cannons', 'Ball Cannons', [], [], [], '(ball|playfield) cannon', false),
    ('ball-elevators', 'Ball Elevators', [], [], [], 'ball elevator', false),
    ('roulette-wheels', 'Roulette Wheels', [], [], [], 'roulette wheel', false),
    ('tilting-playfields', 'Tilting Playfields', [], [], [], 'tilting playfield', false),

    -- ══ Positional children of existing features ══════════════════════════
    -- ball-return-gates: joins the existing right-side/mid-field children.
    ('upper-ball-return-gates', 'Upper Ball Return Gates', ['ball-return-gates'], [], ['upper ball return gate'], NULL, false),
    ('right-outlane-ball-return-gates', 'Right Outlane Ball Return Gates', ['right-side-ball-return-gates'], [], ['right outlane ball return gate'], NULL, false),
    ('upper-right-ball-return-gates', 'Upper Right Ball Return Gates', ['upper-ball-return-gates', 'right-side-ball-return-gates'], [], ['upper right ball return gate'], NULL, false),
    -- kickback / kickback lanes. right-kickback-lanes is a NODE: no IPDB text
    -- says it, but Upper Right Kickback Lane is a kind of it.
    ('left-outlane-kickbacks', 'Left Outlane Kickbacks', ['kickback'], ['Left Kickback Outlane'], ['left outlane kickback', 'left kickback outlane'], NULL, false),
    ('left-kickback-lanes', 'Left Kickback Lanes', ['kickback-lanes'], ['Left-Side Kickback Lane'], ['left kickback lane', 'left side kickback lane'], NULL, false),
    ('upper-left-kickback-lanes', 'Upper Left Kickback Lanes', ['left-kickback-lanes'], [], ['upper left kickback lane'], NULL, false),
    ('right-kickback-lanes', 'Right Kickback Lanes', ['kickback-lanes'], [], [], NULL, false),
    ('upper-right-kickback-lanes', 'Upper Right Kickback Lanes', ['right-kickback-lanes'], [], ['upper right kickback lane'], NULL, false),
    ('left-kicker-lanes', 'Left Kicker Lanes', ['kicker-lanes'], ['Left-Side Kicker Lane'], ['left kicker lane', 'left side kicker lane'], NULL, false),
    ('upper-left-kicker-lanes', 'Upper Left Kicker Lanes', ['left-kicker-lanes'], [], ['upper left kicker lane'], NULL, false),
    ('right-kicker-lanes', 'Right Kicker Lanes', ['kicker-lanes'], [], [], NULL, false),
    ('upper-right-kicker-lanes', 'Upper Right Kicker Lanes', ['right-kicker-lanes'], [], ['upper right kicker lane'], NULL, false),
    -- inlanes: "left and right dual inlanes" assigns BOTH children.
    ('dual-inlanes', 'Dual Inlanes', ['inlanes'], [], ['dual inlanes'], NULL, false),
    ('left-dual-inlanes', 'Left Dual Inlanes', ['dual-inlanes'], ['Dual Left Inlanes', 'Left-Side Dual Inlanes'], ['left dual inlanes', 'dual left inlanes', 'left side dual inlanes', 'left and right dual inlanes'], NULL, false),
    ('right-dual-inlanes', 'Right Dual Inlanes', ['dual-inlanes'], ['Dual Right Inlanes', 'Right-Side Dual Inlanes', 'Right Side Dual Inlanes'], ['right dual inlanes', 'dual right inlanes', 'right side dual inlanes', 'right side dual inlanes', 'left and right dual inlanes'], NULL, false),
    ('dual-outlanes', 'Dual Outlanes', ['outlanes'], [], ['dual outlanes', 'left and right dual outlanes'], NULL, false),
    ('triple-outlanes', 'Triple Outlanes', ['outlanes'], [], ['triple outlanes'], NULL, false),
    ('center-up-posts', 'Center Up-Posts', ['up-posts'], ['Up-Post Between Flippers'], ['center up post', 'up post between flippers'], NULL, false),
    ('right-ball-return-rollunders', 'Right Ball Return Rollunders', ['rollunders'], [], [], NULL, false),
    ('upper-right-ball-return-rollunders', 'Upper Right Ball Return Rollunders', ['right-ball-return-rollunders'], ['Upper Right Return Ball Rollunder'], ['upper right ball return rollunder', 'upper right return ball rollunder'], NULL, false),
    ('plunger-skill-shots', 'Plunger Skill Shots', ['skill-shot'], [], ['plunger skill shot'], NULL, false),
    ('ramp-skill-shots', 'Ramp Skill Shots', ['skill-shot'], [], ['ramp skill shot'], NULL, false),
    ('elevated-shooter-lanes', 'Elevated Shooter Lanes', ['shooter-lanes'], ['Elevated Ball Shooter Lane'], ['elevated ball shooter lane'], NULL, false),
    ('player-controlled-diverter-ramps', 'Player-Controlled Diverter Ramps', ['diverter-ramps'], ['Player-Controllable Diverter Ramp'], ['player controllable diverter ramp'], NULL, false),
    ('center-drop-targets', 'Center Drop Targets', ['drop-targets'], ['Drop Target Between Flippers'], ['drop target between flippers'], NULL, false),

    -- ══ Promoted from the fence ═══════════════════════════════════════════
    -- Held back under the original err-on-caution rule, then promoted when the
    -- campaign's principle changed to preferring detail over conflation.
    ('shaker-motors', 'Shaker Motors', [], [], ['shaker motor'], NULL, false),
    ('time-clocks', 'Time Clocks', [], [], ['time clock'], NULL, false),
    ('lane-change', 'Lane Change', [], [], ['lane change'], NULL, false),
    ('video-modes', 'Video Modes', [], [], ['video mode'], NULL, false),
    ('free-ball-return-lanes', 'Free Ball Return Lanes', ['lanes'], ['Free Ball Return Lane Behind Flipper'], ['free ball return lane', 'free ball return lane behind flipper'], NULL, false),
    ('free-ball-gates', 'Free Ball Gates', ['ball-return-gates'], [], [], NULL, false),
    ('right-outlane-free-ball-gates', 'Right Outlane Free Ball Gates', ['free-ball-gates'], [], ['right outlane free ball gate'], NULL, false),
    ('captive-ball-spinners', 'Captive Ball Spinners', ['captive-ball', 'spinners'], [], ['captive ball spinner'], NULL, false),
    ('captive-ball-walkers', 'Captive Ball Walkers', ['captive-ball'], [], ['captive ball walker', 'captive ball walker with carry over feature'], NULL, false),
    ('stationary-posts', 'Stationary Posts', [], [], [], NULL, false),
    ('center-stationary-posts', 'Center Stationary Posts', ['stationary-posts'], ['Mini-Post Screw Between Flippers', 'Stationary Post Between Flippers'], ['mini post screw between flippers', 'stationary post between flippers'], NULL, false),
    ('right-outlane-stationary-posts', 'Right Outlane Stationary Posts', ['stationary-posts'], [], ['right outlane has a mini post'], NULL, false),
    ('outholes', 'Outholes', [], [], ['two outholes', 'two outhole troughs', 'the outhole trough in this game is actually five additional scoring pockets'], NULL, false),
    ('drop-lanes', 'Drop Lanes', ['lanes'], [], [], NULL, false),
    ('left-drop-lanes', 'Left Drop Lanes', ['drop-lanes'], [], ['left drop lane'], NULL, false),
    ('projection-roto-units', 'Projection Roto Units', ['roto-targets'], [], ['projection roto unit under playfield'], NULL, false),
    -- Backbox and backglass name the same place, so they are one family with the
    -- backglass phrasings folded in as aliases; mechanical vs light IS a real
    -- distinction and splits into children.
    ('backbox-animations', 'Backbox Animations', [], ['Backglass Animation'], ['backbox animation', 'backglass animation'], NULL, false),
    ('mechanical-backbox-animations', 'Mechanical Backbox Animations', ['backbox-animations'], [], ['mechanical backbox animation'], NULL, false),
    ('backbox-light-animations', 'Backbox Light Animations', ['backbox-animations'], ['Backglass Light Animation'], ['backbox light animation', 'backglass light animation'], NULL, false),
    ('playfield-animations', 'Playfield Animations', [], [], ['playfield animation'], NULL, false),

    -- ══ Found once the gap's length ceiling was lifted ════════════════════
    -- IPDB sometimes names a feature in a whole clause rather than a noun
    -- phrase, and an earlier 40-character cap hid every one of them.
    ('open-elbow-inlanes', 'Open-Elbow Inlanes', ['inlanes'], [], ['open elbow inlanes allow ball to pass from inlane to outlane and vice versa', 'open elbow inlane allows ball to pass from inlane to outlane and vice versa'], NULL, false),
    ('right-open-elbow-inlanes', 'Right Open-Elbow Inlanes', ['open-elbow-inlanes'], [], ['open elbow right inlane allows ball to pass from inlane to outlane and vice versa'], NULL, false),
    ('bounce-back-outlanes', 'Bounce-Back Outlanes', ['outlanes'], [], ['bounce back outlanes allow the player to nudge a draining ball back into play'], NULL, false),
    ('looping-shooter-lanes', 'Looping Shooter Lanes', ['shooter-lanes'], [], ['this game has a shooter lane to allow the ball to loop 360 degrees around the playfield before entering into play'], NULL, false),
    ('serial-rollover-lanes', 'Serial Rollover Lanes', ['lanes', 'rollovers'], [], ['right side of playfield has parallel lanes of serial rollovers', 'two parallel lanes of serial rollovers'], NULL, false),
    ('rebound-rubbers', 'Rebound Rubbers', [], [], ['large non kicking rebound rubber between and below flippers'], NULL, false),
    ('graduated-skill-shots', 'Graduated Skill Shots', ['skill-shot'], [], ['graduated skill shot on right side of playfield'], NULL, false)
  ) AS t(slug, name, parents, aliases, terms, pattern, counted);

-- Aliases for features that ALREADY EXIST. What's left once positional variants
-- have been split off into their own features: true synonyms, carrying no
-- distinguishing fact of their own.
CREATE OR REPLACE VIEW _gpf_existing_alias AS
  SELECT * FROM (VALUES
    ('auto-launch', 'Autoplunger', 'autoplunger'),
    ('auto-launch', 'Automatic Plunger', 'automatic plunger'),
    ('right-side-ball-return-gates', 'Right Ball Return Gate', 'right ball return gate'),
    ('spinners', 'Playfield Spinner', 'playfield spinner'),
    ('bumpers', 'Multi-Bumper', 'multi bumper')
  ) AS t(slug, alias, term);

-- Confirmed FALSE POSITIVES of the regex patterns, keyed by model id + feature.
-- A loose pattern's price, paid explicitly and auditably. Two kinds dominate: the
-- text describes ARTWORK depicting the thing rather than the mechanism, and the
-- text uses the feature's name to describe a DIFFERENT game's mechanism.
CREATE OR REPLACE VIEW _gpf_family_excluded AS
  SELECT * FROM (VALUES
    (6512, 'roulette-wheels', 'Vegas: "the pop bumper cap ARTWORK depicts a casino roulette wheel" — art, not a mechanism'),
    (4679, 'roulette-wheels', 'Riverboat Gambler: the roulette wheel is a BACKGLASS animation bet on from the lockdown bar, not a playfield device'),
    (  85, 'roulette-wheels', 'A-B-C: "playfield RESEMBLES a roulette wheel but DOES NOT SPIN" — an explicit denial of the mechanism'),
    ( 787, 'roulette-wheels', 'Bingo-Cards: same "resembles a roulette wheel but does not spin" denial'),
    (2552, 'magic-squares',   'Gulfstream: a Williams FLIPPER game whose centre playfield lights form a bingo-inspired "Magic Square" — same name, different mechanism, and the one non-bingo in the family')
  ) AS t(model_id, feature, reason);

-- Every category a Notable Features term can fall into. A CLOSED vocabulary —
-- gpf_checks rejects anything outside it.
-- Terms that BECOME a feature are not listed here at all — they live in
-- `_gpf_new` / `_gpf_existing_alias` above, so no term is described twice. What
-- remains is everything the campaign does NOT turn into vocabulary:
--   fence         still genuinely ambiguous after the campaign widened its rule
--                 to prefer detail over conflation — an unqualified "upper gate"
--                 or "lower gate" that may be a ball-return gate, a conjunction
--                 the splitter left glued together. Recorded so the call is
--                 auditable rather than lost.
--   descriptive   an existing feature, but the phrase DESCRIBES an instance
--                 rather than naming the feature ("two slingshot kickers in upper
--                 playfield"). Too specific to adopt — nobody would search it.
--   negation      an ABSENCE statement ("no slingshots", 113 models). Must never
--                 become a feature — a naive assignment would invert the meaning.
--                 The single most dangerous class in this data.
-- The rest name the dimension the term actually belongs to, or that it is not a
-- fact at all: cabinet, construction, display, sound, lighting, art, scoring,
-- reward, play-rule, dimension, tech, layout, toy, fragment.
CREATE OR REPLACE VIEW _gpf_category AS
  SELECT * FROM (VALUES
    ('fence'), ('descriptive'), ('negation'),
    ('cabinet'), ('construction'), ('display'), ('sound'), ('lighting'), ('art'),
    ('scoring'), ('reward'), ('play-rule'), ('dimension'), ('tech'), ('layout'),
    ('toy'), ('fragment')
  ) AS t(category);

-- The human read of every gap term at or above the threshold that does NOT become
-- vocabulary. NOT derived from the DB — this is the judgment, made reproducible.
-- `groups` names the related existing feature where there is one.
CREATE OR REPLACE VIEW _gpf_class AS
  SELECT * FROM (VALUES
    ('cabinet advertised as walnut finish', 'art', ''),
    ('hand drawn translite', 'art', ''),
    ('photographic translite', 'art', ''),
    ('the ramp is unpainted metal', 'art', ''),
    ('the ramps are unpainted metal', 'art', ''),
    ('bubble level in shooter lane', 'cabinet', ''),
    ('cigarette holder on each side rail', 'cabinet', ''),
    ('coin slot in lockdown bar', 'cabinet', ''),
    ('console cabinet', 'cabinet', ''),
    ('drop down cabinet', 'cabinet', ''),
    ('injection molded backbox', 'cabinet', ''),
    ('legs', 'cabinet', ''),
    ('lockdown bar', 'cabinet', ''),
    ('metal legs', 'cabinet', ''),
    ('metal rails with cigarette holders', 'cabinet', ''),
    ('reclined backbox', 'cabinet', ''),
    ('reverse wedge head', 'cabinet', ''),
    ('short backbox', 'cabinet', ''),
    ('square machine', 'cabinet', ''),
    ('the side rails', 'cabinet', ''),
    ('this is a square machine', 'cabinet', ''),
    ('wedge head', 'cabinet', ''),
    ('wedge head backbox', 'cabinet', ''),
    ('wedgehead backbox', 'cabinet', ''),
    ('widebody cabinet', 'cabinet', ''),
    ('wood legs', 'cabinet', ''),
    ('chrome metal playfield', 'construction', ''),
    ('formica cabinet', 'construction', ''),
    ('invisiglass playfield glass', 'construction', ''),
    ('metal playfield', 'construction', ''),
    ('plastic playfield surface', 'construction', ''),
    ('plexiglas backglass', 'construction', ''),
    ('plexiglas playfield cover', 'construction', ''),
    ('plexiglass playfield', 'construction', ''),
    ('injection molded bumpers', 'descriptive', 'bumpers'),
    ('multiball play', 'descriptive', 'multiball family'),
    ('the captive balls', 'descriptive', 'captive-ball'),
    ('two slingshot kickers in upper playfield', 'descriptive', 'slingshots'),
    ('variable multiball', 'descriptive', 'multiball family'),
    ('and 10 inches high', 'dimension', ''),
    ('and 17 inches deep', 'dimension', ''),
    ('and 18 inches deep', 'dimension', ''),
    ('and 18 inches deep overall', 'dimension', ''),
    ('and 202 cm high', 'dimension', ''),
    ('and 26 inches high', 'dimension', ''),
    ('and 36 inches high', 'dimension', ''),
    ('and 37 inches high', 'dimension', ''),
    ('and 38 inches high', 'dimension', ''),
    ('and 38 inches high in the back', 'dimension', ''),
    ('and 39 inches high', 'dimension', ''),
    ('and 39 inches high in the back', 'dimension', ''),
    ('and 40 inches high', 'dimension', ''),
    ('and 42 inches high', 'dimension', ''),
    ('and 54 inches high', 'dimension', ''),
    ('and 6 inches high', 'dimension', ''),
    ('and 62 inches high', 'dimension', ''),
    ('and 7 inches high', 'dimension', ''),
    ('and 75 1 2 inches high 250 lbs', 'dimension', ''),
    ('and 75 1 2 inches high 260 lbs', 'dimension', ''),
    ('and 8 1 4 inches high in the back', 'dimension', ''),
    ('and 8 inches high', 'dimension', ''),
    ('and 8 inches high in the back', 'dimension', ''),
    ('and 9 inches high', 'dimension', ''),
    ('backglass measures 21 by 21 inches', 'dimension', ''),
    ('backglass measures 22 by 19 inches', 'dimension', ''),
    ('backglass measures 22 by 20 inches', 'dimension', ''),
    ('cabinet advertised as 36 inches long', 'dimension', ''),
    ('cabinet advertised as 55 inches long', 'dimension', ''),
    ('cabinet advertised as 56 inches high', 'dimension', ''),
    ('cabinet advertised as 57 inches high', 'dimension', ''),
    ('cabinet measures 36 inches long', 'dimension', ''),
    ('game advertised as 132 cm long', 'dimension', ''),
    ('game is 40 inches long by 20 inches wide', 'dimension', ''),
    ('alpha numeric', 'display', ''),
    ('alphanumeric displays', 'display', ''),
    ('blue futaba displays', 'display', ''),
    ('bulb scoring', 'display', ''),
    ('color lcd', 'display', ''),
    ('color lcd backbox display', 'display', ''),
    ('five score reels', 'display', ''),
    ('half moon credit window', 'display', ''),
    ('has the panascope feature', 'display', ''),
    ('lcd scoring display', 'display', ''),
    ('miniature lcd screen on playfield', 'display', ''),
    ('nixie tube electronic scoring', 'display', ''),
    ('panascope display', 'display', ''),
    ('score drum in playfield', 'display', ''),
    ('ball guides and playfield inserts', 'fence', 'playfield hardware, not a scoring mechanism'),
    ('ball pitching and batting devices', 'fence', 'baseball-novelty device; one-off phrasing'),
    ('both slingshots operate simultaneously', 'fence', 'behaviour of an existing feature'),
    ('lower gate', 'fence', 'unqualified gate; may be a ball-return-gate'),
    ('upper gate', 'fence', 'unqualified gate; may be a ball-return-gate'),
    ('active pinballs', 'fragment', 'a ball count, not a feature'),
    ('also', 'fragment', ''),
    ('and quarters', 'fragment', ''),
    ('at start of game', 'fragment', ''),
    ('blue', 'fragment', ''),
    ('dimes', 'fragment', ''),
    ('for instance', 'fragment', ''),
    ('gi special led s', 'fragment', ''),
    ('green', 'fragment', ''),
    ('has lights and bells', 'fragment', ''),
    ('instead', 'fragment', ''),
    ('land in kick out holes', 'fragment', ''),
    ('large', 'fragment', ''),
    ('nine multiball modes and one wizard mode', 'fragment', ''),
    ('or 10 balls', 'fragment', ''),
    ('or 10 balls for 5 cents', 'fragment', ''),
    ('or 10 replays', 'fragment', ''),
    ('or 5 ball play', 'fragment', ''),
    ('or 6 ball multiball', 'fragment', ''),
    ('or 7 ball play', 'fragment', ''),
    ('or for 5 cents', 'fragment', ''),
    ('per player', 'fragment', ''),
    ('plus extra balls', 'fragment', ''),
    ('two', 'fragment', ''),
    ('up to 6 balls in simultaneous play', 'fragment', ''),
    ('uses two 20 digit', 'fragment', ''),
    ('when hit', 'fragment', ''),
    ('when lowered', 'fragment', ''),
    ('white', 'fragment', ''),
    ('figure 8 playfield layout', 'layout', ''),
    ('split level playfield', 'layout', ''),
    ('two playfields', 'layout', ''),
    ('two level playfield', 'layout', ''),
    ('wide flipper gap', 'layout', ''),
    ('backglass marquee', 'lighting', ''),
    ('backglass spinning lights', 'lighting', ''),
    ('blacklighting', 'lighting', ''),
    ('factory led s', 'lighting', ''),
    ('illuminated backglass', 'lighting', ''),
    ('illuminated backglass marquee', 'lighting', ''),
    ('led game lighting', 'lighting', ''),
    ('no flippers', 'negation', 'flippers'),
    ('no left outlane', 'negation', 'outlanes'),
    ('no outhole', 'negation', 'outhole'),
    ('no outlanes', 'negation', 'outlanes'),
    ('no plunger', 'negation', 'ball-shooters'),
    ('no pop bumpers', 'negation', 'pop-bumpers'),
    ('no right outlane', 'negation', 'outlanes'),
    ('no slingshots', 'negation', 'slingshots'),
    ('the game has no plunger', 'negation', 'ball-shooters'),
    ('convertible to add a ball', 'play-rule', ''),
    ('maximum 1 buy in ball per player', 'play-rule', ''),
    ('maximum 3 buy in balls per player', 'play-rule', ''),
    ('no adjustment for 5 ball play', 'play-rule', ''),
    ('non payout', 'play-rule', ''),
    ('novelty play only', 'play-rule', ''),
    ('one ball per play', 'play-rule', ''),
    ('operates on old english pennies', 'play-rule', ''),
    ('penny or nickel play', 'play-rule', ''),
    ('single entry coin chute accepts nickels', 'play-rule', ''),
    ('six coin maximum', 'play-rule', ''),
    ('tilt ends ball in play', 'play-rule', ''),
    ('tilt penalty is ball in play', 'play-rule', ''),
    ('unlimited buy in balls per player', 'play-rule', ''),
    ('uses 1 steel ball', 'play-rule', ''),
    ('dispenses tickets', 'reward', ''),
    ('double match award can be set for 2', 'reward', ''),
    ('double match awards 2 or 10 replays', 'reward', ''),
    ('optional payout hopper', 'reward', ''),
    ('special game', 'reward', ''),
    ('diagonal scoring', 'scoring', ''),
    ('double triple scores', 'scoring', ''),
    ('end of ball bonus', 'scoring', ''),
    ('end of ball bonus score', 'scoring', ''),
    ('has your number match feature', 'scoring', ''),
    ('lite a name', 'scoring', ''),
    ('ok feature', 'scoring', ''),
    ('outhole bonus feature', 'scoring', ''),
    ('red ball counts double', 'scoring', ''),
    ('red letter game', 'scoring', ''),
    ('and speech', 'sound', ''),
    ('custom speech', 'sound', ''),
    ('electronic sound', 'sound', ''),
    ('electronic sounds', 'sound', ''),
    ('has speech', 'sound', ''),
    ('music', 'sound', ''),
    ('sound effects', 'sound', ''),
    ('speech', 'sound', ''),
    ('stereo sound', 'sound', ''),
    ('battery operated', 'tech', ''),
    ('battery operated', 'tech', ''),
    ('equipped with electropak', 'tech', ''),
    ('no electronic logic in game features', 'tech', ''),
    ('operates on batteries', 'tech', ''),
    ('relays all on circuit boards', 'tech', ''),
    ('used 3 dry cell batteries', 'tech', ''),
    ('moving band members', 'toy', ''),
    ('swinging bell w mounted pinball', 'toy', ''),
    ('tnt detonator with moving handle', 'toy', ''),
    ('skill lane option for 5 ball jurisdictions', 'play-rule', ''),
    ('tilt is reset by ball passing through rollunder wire at bottom of playfield below flippers', 'play-rule', ''),
    ('player bats the ball airborne into the bleachers for scoring', 'descriptive', 'baseball novelty play, not a named mechanism'),
    ('advertised as 50 inches long by 24 inches wide', 'dimension', ''),
    ('advertised as 44 inches long by 22 inches wide', 'dimension', ''),
    ('advertised as 40 inches long by 20 inches wide', 'dimension', ''),
    ('advertised as 44 inches long and 22 inches wide', 'dimension', ''),
    ('cabinet advertised as 44 inches long and 22 inches wide', 'dimension', ''),
    ('cabinet advertised as 40 inches long and 20 inches wide', 'dimension', ''),
    ('wood cabinet with decal artwork advertised as 34 inches long', 'cabinet', ''),
    ('the backglass does not have the bally logo', 'art', ''),
    ('a slingshot is used to interact with the two pop bumpers', 'descriptive', 'slingshots'),
    ('ball shot into play crosses the playfield to get to the top', 'descriptive', ''),
    ('lights on playfield indicate men on bases', 'display', ''),
    ('metal cigarette holders on side woodrails', 'cabinet', ''),
    ('metal rails with a cigarette holder on each rail', 'cabinet', ''),
    ('backglass has a score to beat window allowing the operator to place a card behind the backglass showing a suggested high score visible to the player', 'display', ''),
    ('each free play hole is marked a rejouer', 'art', ''),
    ('relay tester in lower cabinet for trouble shooting', 'tech', ''),
    ('backglass has a last ball in play light', 'display', ''),
    ('both players matching lit number at end of game awards 2 or 10 replays', 'reward', ''),
    ('each player score matching at end of game awards 1 replay', 'reward', ''),
    ('pressing either flipper button operates both flippers simultaneously', 'descriptive', 'flippers'),
    ('each of two levers control four flippers simultaneously', 'descriptive', 'flippers'),
    ('the translite is a combination of hand drawing and photography', 'art', ''),
    ('this feature carries over from game to game', 'fragment', ''),
    ('wood playfield with heat transfer laminate artwork', 'construction', ''),
    ('ball enters playfield from between the flippers when right flipper button is pressed', 'descriptive', 'turret-shooters'),
    ('cabinet advertised as finished in rich walnut with all metal parts chromium plated', 'art', ''),
    ('last two digits of score are dummy zeroes', 'display', ''),
    ('low height console cabinet allows for player to be seated', 'cabinet', ''),
    ('this game had playfield inserts near the flippers that lit for high roto target values so players who were looking at the flippers would be made aware when those high roto target values came around', 'display', ''),
    ('upper left lane has a unique tilt rollover', 'descriptive', 'rollovers'),
    ('backbox has a 26 inch high definition lcd display', 'display', ''),
    ('ball is pitched from above the playfield down a metal slide', 'descriptive', ''),
    ('ball shooter trajectory crosses mid playfield to reach upper playfield', 'descriptive', 'ball-shooters'),
    ('both kick out holes kick the ball up the playfield', 'descriptive', 'kick-out-holes'),
    ('buy back feature allows up to 6 extra balls at 1 coin per ball', 'play-rule', ''),
    ('colorful playfield array of lights track progress of hitting targets', 'display', ''),
    ('only one extra ball per ball in play is given', 'play-rule', ''),
    ('powerful slingshot kickers propel the ball to the upper playfield', 'descriptive', 'slingshots'),
    ('small lcd in upper right playfield indicates to player what objectives to accomplish', 'display', ''),
    ('the automatic flippers activate when balls land in the pockets in front of them', 'descriptive', 'automatic-flippers'),
    ('the flipper button is located on lower left of backglass frame and is labeled skill control', 'descriptive', ''),
    ('the kick out hole propels ball to the outhole', 'descriptive', 'kick-out-holes'),
    ('the replay counter is three digits to accommodate the star feature', 'display', ''),
    ('the top two pop bumpers operate simultaneously', 'descriptive', 'pop-bumpers'),
    ('this is a one ball game with a small bingo type playfield in an upright cabinet', 'play-rule', 'one-ball game format, set by 0175'),
    ('rotating drum in playfield indicates target value', 'display', 'a value indicator, filed with score drum in playfield'),
    ('two on the upper transparent playfield', 'fragment', ''),
    ('clear coated playfield', 'construction', ''),
    ('three level playfield', 'layout', ''),
  ) AS t(term, category, groups);

-- == 3 · ANALYSIS ============================================================
-- parse -> normalise -> resolve -> gap -> review.

-- parse --
-- Clean the blob before splitting, mirroring the seed harvest so the comparison
-- is like-for-like: strip the "Notable Features:" prefix, turn the U+FFFD
-- mojibake (which replaced hyphens, apostrophes and bullets) into a space, and
-- insert a comma before a period+uppercase run-on ("5 cents.Flippers") so the
-- comma split handles it without eating the first letter.
--
-- Then TRUNCATE AT THE FIRST BLANK LINE. IPDB's blob is two parts: a
-- comma-separated feature list, then — after a blank line — a fixed stats tail
-- ("Maximum displayed point score is …", "Replay wheel maximum: 37", "Sound: 3
-- chimes, knocker."). The tail is machine specs and sound hardware, never
-- playfield mechanisms, and left in it dominates the gap by sheer repetition
-- (knocker alone reaches 281 models). Cutting it is the single biggest
-- noise reduction available and costs no real feature — the seed harvest's `(N)`
-- filter happened to suppress the same tail, so cutting it also keeps this
-- re-parse honest against what the harvest actually saw.
CREATE OR REPLACE VIEW _gpf_cleaned AS
  SELECT
    m.id AS model_id,
    regexp_extract(
      regexp_replace(
        replace(
          regexp_replace(m.ipdb_notable_features, '^Notable Features:\s*', ''),
          '�', ' '
        ),
        '\.([A-Z])', ', \1', 'g'
      ),
      '(?s)^(.*?)(\r?\n[ \t]*\r?\n|$)', 1  -- head only: up to the first blank line
    ) AS features_text,
    m.ipdb_notable_features AS raw
  FROM models m
  WHERE m.ipdb_notable_features IS NOT NULL;

-- Split into segments on comma or period+space; drop any preamble up to a colon
-- ("The following have wireforms: Flippers" → "Flippers"). One row per
-- model+segment — the grain the whole analysis rests on.
CREATE OR REPLACE VIEW _gpf_segment AS
  SELECT
    model_id,
    trim(regexp_replace(
      trim(unnest(regexp_split_to_array(features_text, ',|\.\s'))),
      '^.*:\s*', ''
    )) AS segment
  FROM _gpf_cleaned;

-- normalise --
-- Reduce a segment to its lookup key: strip the trailing "(N)" count and any
-- trailing punctuation, lowercase, collapse whitespace. `qty` records whether
-- the segment carried a count — the very filter the seed harvest applied, and
-- so the axis this whole analysis turns on.
CREATE OR REPLACE VIEW _gpf_norm AS
  SELECT
    model_id,
    segment,
    TRY_CAST(regexp_extract(segment, '\((\d+)', 1) AS INTEGER) AS qty,
    regexp_matches(segment, '\(\d+\)') AS counted,
    -- The lookup key, via the foundation's `name_norm`: strip the trailing "(N)"
    -- count FIRST (name_norm would turn "(25)" into a bare " 25 " token), then let
    -- the macro fold diacritics, lowercase, and collapse every run of
    -- non-letter/non-digit to one space. This replaces a hand-rolled normalizer
    -- that only collapsed whitespace — so "Open-elbow inlanes" and "open elbow
    -- inlanes" now key alike, and "Trocadéro" stops depending on its accent.
    name_norm(regexp_replace(segment, '\s*\(.*$', '')) AS term,
    -- IPDB's fixed stats lines. The blank-line truncation above removes most of
    -- them, but a minority of entries separate the tail with a SINGLE newline, so
    -- the patterns are also named explicitly here. Machine specs, not features.
    regexp_matches(lower(trim(segment)),
      '^(maximum displayed point score|replay wheel maximum|sound:)') AS is_stat
  FROM _gpf_segment
  WHERE segment <> '';

-- resolve --
-- Attach each segment to the catalog vocabulary it already belongs to, if any.
-- A term can be plural in IPDB and singular in the catalog (or the reverse), so
-- match the term, its de-pluralised form and its pluralised form.
CREATE OR REPLACE VIEW _gpf_resolved AS
  SELECT
    n.*,
    (SELECT v.slug FROM _gpf_vocab v
      WHERE v.term = n.term
         OR v.term = regexp_replace(n.term, 's$', '')
         OR v.term = n.term || 's'
      LIMIT 1) AS feature_slug
  FROM _gpf_norm n;

-- gap --
-- The residue: distinct terms IPDB names that resolve to NO catalog gameplay
-- feature, ranked by reach (how many models say it). `counted_models` is the
-- tell — a term with counted occurrences was in the seed harvest's sights and
-- still missed, whereas an all-uncounted term was never eligible.
--
-- Noise floor: terms are trimmed to those that look like a feature phrase — 3 to
-- 40 characters, at least one letter, not starting with a digit (which strips
-- "5 balls for 5 cents", "999 points per player", "27 inches wide") and not a
-- newline-mangled fragment. This is a first cut for READING, not a claim: every
-- surviving row still needs the human call recorded in `_gpf_class`.
CREATE OR REPLACE VIEW gpf_gap AS
  SELECT
    r.term,
    count(DISTINCT r.model_id) AS models,
    count(DISTINCT r.model_id) FILTER (WHERE r.counted) AS counted_models,
    min(r.segment) AS example_segment
  FROM _gpf_resolved r
  WHERE r.feature_slug IS NULL
    AND NOT r.is_stat
    -- NO UPPER LENGTH BOUND. An earlier cut capped terms at 40 characters to keep
    -- the gap readable, which quietly hid every feature IPDB describes in a full
    -- clause -- "Open-elbow inlanes allow ball to pass from inlane to outlane and
    -- vice-versa" is 74 characters and reaches 31 models. Worse, the completeness
    -- check only fires on terms that REACH this view, so the hidden band could
    -- never be reported as unaudited: the audit read clean precisely because it
    -- was not looking. The floor stays (a 1-2 character term is never a feature).
    AND length(r.term) >= 3
    AND regexp_matches(r.term, '[a-z]')
    AND NOT regexp_matches(r.term, '^[0-9]')
    AND r.term NOT LIKE '%' || chr(10) || '%'
  GROUP BY r.term
  ORDER BY models DESC, r.term;

-- before/after --
-- Public projections of the two things this campaign changes, so a run can be
-- frozen with `CMD=snapshot` before applying the patches and diffed against the
-- live views after. That is what proves the patches touched ONLY what they meant
-- to: any row in the after-set that isn't a planned create, alias or assignment
-- is collateral damage.
--
--   make analyze FILE=$F CMD=snapshot ARGS="gpf_vocab gpf_memberships"
--   -- then, after ingest, ATTACH the snapshot and EXCEPT the two pairs.
CREATE OR REPLACE VIEW gpf_vocab AS
  SELECT slug, term, via FROM _gpf_vocab;

CREATE OR REPLACE VIEW gpf_memberships AS
  SELECT m.slug AS model_slug, f.feature_slug, f.count
  FROM model_gameplay_features f
  JOIN models m ON m.id = f.model_id;

-- Everything a gap term above the threshold can be ACCOUNTED for by: it becomes a
-- feature, it becomes an alias on an existing feature, or it carries a call in
-- _gpf_class. Exactly one of the three, and the completeness check leans on it.
CREATE OR REPLACE VIEW gpf_accounted AS
  -- term-matched features name their terms outright ...
            SELECT unnest(terms) AS term, 'feature' AS via, slug AS target
            FROM _gpf_new WHERE len(terms) > 0
  -- ... while pattern-matched ones account for whatever their regex catches, so a
  -- phrasing nobody enumerated ("left and right crossover return lanes") still
  -- counts as handled rather than reading as an unjudged gap term.
  UNION ALL SELECT DISTINCT n.term, 'feature', f.slug
            FROM _gpf_new f JOIN _gpf_norm n ON regexp_matches(n.term, f.pattern)
            WHERE f.pattern IS NOT NULL
  UNION ALL SELECT term, 'alias',    slug   FROM _gpf_existing_alias
  UNION ALL SELECT term, category,   groups FROM _gpf_class;

-- review --
-- The gap with the human call attached. Unclassified rows (below the threshold)
-- sort last; within a category, by reach. This is the read-through view.
CREATE OR REPLACE VIEW gpf_review AS
  SELECT
    g.term, g.models, coalesce(a.via, '(unaccounted)') AS category, a.target
  FROM gpf_gap g
  LEFT JOIN gpf_accounted a ON a.term = g.term
  ORDER BY (a.via IS NULL), a.via, g.models DESC, g.term;

-- The models a new feature would be asserted on — the generator feed. One row per
-- model+feature, carrying the IPDB segment that evidences it (the verbatim text a
-- patch note would quote) and the model's existing game_format, which is how the
-- bingo-family rows get sanity-checked against 0172.
CREATE OR REPLACE VIEW gpf_assignments AS
  WITH match AS (
    -- A feature claims a model two ways, and a feature uses ONE of them:
    --   pattern — a regex over the normalised term, for families whose phrasing
    --             is too varied to enumerate. Magic Lines is why this exists: as
    --             exact terms it scores ZERO models (every phrasing sits under the
    --             classification threshold); as a pattern it finds 9.
    --   terms   — exact normalised terms, for the positional variants. Here
    --             exactness is the point: "left kickback lane" and "upper left
    --             kickback lane" are DIFFERENT features, and a regex loose enough
    --             to catch one would swallow the other.
    SELECT f.slug AS feature, n.model_id, n.segment, n.term, f.counted, f.pattern
    FROM _gpf_new f
    JOIN _gpf_norm n
      ON (f.pattern IS NOT NULL AND regexp_matches(n.term, f.pattern))
      OR (f.pattern IS NULL AND list_contains(f.terms, n.term))
  ),
  hit AS (
    SELECT
      x.feature,
      m.slug, m.ipdb_id, m.label, m.game_format_slug,
      min(x.segment) AS segment,
      -- The membership COUNT, for the few features where the count IS the fact
      -- ("six cards" → bingo-cards x6). Everything else is asserted bare, even
      -- where IPDB supplies a number.
      CASE WHEN bool_or(x.counted)
           THEN max(CASE WHEN regexp_matches(x.term, '^one ')   THEN 1
                         WHEN regexp_matches(x.term, '^two ')   THEN 2
                         WHEN regexp_matches(x.term, '^three ') THEN 3
                         WHEN regexp_matches(x.term, '^four ')  THEN 4
                         WHEN regexp_matches(x.term, '^five ')  THEN 5
                         WHEN regexp_matches(x.term, '^six ')   THEN 6 END)
      END AS feature_count,
      -- The cite quote, taken from the RAW IPDB text rather than the parsed
      -- segment. The parse is lossy on purpose — it folds U+FFFD to a space and
      -- rewrites period+uppercase run-ons into commas — so a segment is NOT
      -- reliably a verbatim substring of the source, and `make verify-quotes`
      -- would reject it. Re-finding the phrase in `raw` and running to the next
      -- comma, period or newline yields a span that is verbatim by construction.
      -- The span stops at a comma, period, newline OR the U+FFFD mojibake: patchkit
      -- STRIPS U+FFFD from a quote (it is encoding damage, not source text), so a
      -- span running through one would be emitted differently from how it appears
      -- in the source and verify-quotes would rightly reject it.
      -- The term is now name_norm'd, so its spaces stand for whatever punctuation
      -- the source actually used ("open elbow" <- "Open-elbow"). Matching it back
      -- against the RAW text therefore needs each space to accept any run of
      -- non-alphanumerics, or no term with a hyphen in the source would ever be
      -- found again.
      -- Matching a normalized needle back against the RAW haystack. Both the
      -- term and the pattern are written in name_norm space, where a single space
      -- stands for whatever punctuation the source used, so EVERY space in either
      -- must become "any run of non-alphanumerics" before it meets raw text.
      -- Zero-or-more, not one-or-more: name_norm folds "Ballyhole" to 'ballyhole'
      -- with no space at all, and the `bally ?hole` pattern has to keep matching
      -- both that and "Bally Hole".
      -- No regexp_escape: name_norm guarantees a term holds only letters, digits
      -- and single spaces, so there is no metacharacter to escape -- and escaping
      -- would actively BREAK this, since it renders a space as '\ ' whose
      -- backslash then escapes the '[' of the class. Plain replace() for the same
      -- reason: a regexp REPLACEMENT string interprets backslash escapes.
      min(regexp_extract(c.raw,
        '(?i)((?:' || replace(coalesce(x.pattern, x.term), ' ', '[^a-zA-Z0-9]*')
        || ')[^,.\r\n�]*)', 1)) AS quote,
      min(c.raw) AS raw
    FROM match x
    JOIN models m ON m.id = x.model_id
    JOIN _gpf_cleaned c ON c.model_id = m.id
    WHERE NOT EXISTS (
      SELECT 1 FROM _gpf_family_excluded e
      WHERE e.model_id = m.id AND e.feature = x.feature
    )
    GROUP BY x.feature, m.slug, m.ipdb_id, m.label, m.game_format_slug
  )
  SELECT
    feature, slug, ipdb_id, label, game_format_slug, segment, feature_count, quote,
    -- Where the quote starts in the raw source. A model matching several features
    -- gets its spans joined with " [...] " into ONE cite, and `make verify-quotes`
    -- requires the spans to appear IN SOURCE ORDER — so the generator sorts on
    -- this, not on the feature name.
    position(quote IN raw) AS quote_pos
  FROM hit
  ORDER BY feature, slug;

-- The generator feed for 0178. `assignable` marks the features IPDB actually
-- names; the rest are taxonomy nodes, created so a child has a parent.
CREATE OR REPLACE VIEW gpf_new_vocab AS
  SELECT slug, name, parents, aliases,
         (pattern IS NOT NULL OR len(terms) > 0) AS assignable
  FROM _gpf_new
  ORDER BY slug;

-- Public projection of the aliases that hang on features which already existed.
CREATE OR REPLACE VIEW gpf_existing_alias AS
  SELECT slug, alias FROM _gpf_existing_alias ORDER BY slug, alias;

-- One row per feature the campaign creates: what 0178 emits, and what reach 0179
-- gives it. `kind` separates the three shapes a row can have, and `models` = 0 is
-- EXPECTED for a node — it exists so a child has a parent, not because IPDB names
-- it.
CREATE OR REPLACE VIEW gpf_new_features AS
  SELECT
    f.slug AS feature,
    CASE WHEN f.pattern IS NOT NULL THEN 'pattern'
         WHEN len(f.terms) = 0      THEN 'node'
         ELSE 'terms' END AS kind,
    (SELECT count(*) FROM gpf_assignments a WHERE a.feature = f.slug) AS models,
    len(f.parents) AS parents,
    len(f.aliases) AS aliases,
    (SELECT count(*) FROM _gpf_family_excluded x WHERE x.feature = f.slug) AS excluded,
    list_aggregate(f.parents, 'string_agg', ' + ') AS parent_slugs
  FROM _gpf_new f
  ORDER BY models DESC, f.slug;

-- == 4 · SUMMARY & CHECKS ====================================================

CREATE OR REPLACE VIEW gpf_summary AS
            SELECT 'models_with_text'   AS metric, count(*) AS value FROM _gpf_cleaned
  UNION ALL SELECT 'segments',          count(*)                     FROM _gpf_norm
  UNION ALL SELECT 'segments_counted',  count(*)                     FROM _gpf_norm WHERE counted
  UNION ALL SELECT 'segments_uncounted',count(*)                     FROM _gpf_norm WHERE NOT counted
  UNION ALL SELECT 'terms',             count(DISTINCT term)         FROM _gpf_norm
  UNION ALL SELECT 'terms_resolved',    count(DISTINCT term)         FROM _gpf_resolved WHERE feature_slug IS NOT NULL
  UNION ALL SELECT 'gap_terms',         count(*)                     FROM gpf_gap
  UNION ALL SELECT 'vocab_features',    count(DISTINCT slug)         FROM _gpf_vocab
  -- the audit: how much of the gap is accounted for
  UNION ALL SELECT 'accounted_terms',   count(DISTINCT term)         FROM gpf_accounted
  UNION ALL SELECT 'unaccounted_terms', count(*)                     FROM gpf_review WHERE category = '(unaccounted)'
  UNION ALL SELECT 'gap_models_accounted',
                   (SELECT count(DISTINCT r.model_id) FROM _gpf_resolved r
                     JOIN gpf_accounted a ON a.term = r.term)
  -- the verdict: what the two patches contain
  UNION ALL SELECT 'new_features',      count(*)                     FROM _gpf_new
  UNION ALL SELECT 'new_feature_nodes', count(*)                     FROM gpf_new_features WHERE kind = 'node'
  UNION ALL SELECT 'new_feature_aliases',
                   (SELECT sum(len(aliases)) FROM _gpf_new) + (SELECT count(*) FROM _gpf_existing_alias)
  UNION ALL SELECT 'new_assignments',   count(*)                     FROM gpf_assignments
  UNION ALL SELECT 'cat_fence',         count(*)                     FROM _gpf_class WHERE category = 'fence'
  UNION ALL SELECT 'cat_descriptive',   count(*)                     FROM _gpf_class WHERE category = 'descriptive'
  UNION ALL SELECT 'cat_negation',      count(*)                     FROM _gpf_class WHERE category = 'negation'
  UNION ALL SELECT 'cat_elsewhere',     count(*)                     FROM _gpf_class
                                                                     WHERE category NOT IN ('fence','descriptive','negation')
  ORDER BY metric;

CREATE OR REPLACE VIEW gpf_checks AS
  -- ANCHORS: a known counted feature must still resolve. This is the only class
  -- that catches the parse going dark wholesale — a renamed foundation column or
  -- a rotted regex — which a row-level invariant cannot see.
            SELECT 'anchor_flippers_dark' AS check, NULL AS term, 'Flippers (2) no longer resolves' AS detail
            WHERE NOT EXISTS (SELECT 1 FROM _gpf_resolved WHERE term = 'flippers' AND feature_slug = 'flippers')
  UNION ALL SELECT 'anchor_trapholes_dark', NULL, 'Trap holes (25) no longer resolves'
            WHERE NOT EXISTS (SELECT 1 FROM _gpf_resolved WHERE term = 'trap holes' AND feature_slug = 'trap-holes')
  -- ANCHOR, POST-LANDING: Magic Squares is the term that opened this campaign, so
  -- it is the canary for the whole thing. Before 0178 it had to appear in the gap;
  -- now it must RESOLVE, to the feature 0178 created.
  UNION ALL SELECT 'anchor_landed_dark', 'magic squares', 'Magic Squares no longer resolves to magic-squares'
            WHERE NOT EXISTS (
              SELECT 1 FROM _gpf_resolved WHERE term = 'magic squares' AND feature_slug = 'magic-squares')
  -- The blank-line truncation must never swallow the whole entry.
  UNION ALL SELECT 'empty_head', c.model_id::VARCHAR, left(c.raw, 60)
            FROM _gpf_cleaned c WHERE trim(c.features_text) = ''
  -- No stats line may reach the gap.
  UNION ALL SELECT 'stats_leaked_to_gap', g.term, g.example_segment
            FROM gpf_gap g
            WHERE regexp_matches(g.term, '^(maximum displayed|replay wheel|sound:)')

  -- ══ COMPLETENESS ═══════════════════════════════════════════════════════════
  -- Every gap term at or above the threshold must be accounted for. This is what
  -- stops the audit rotting as the catalog moves: a term that crosses the
  -- threshold shows up here until someone judges it.
  UNION ALL SELECT 'unaccounted_above_threshold', g.term, g.models::VARCHAR
            FROM gpf_gap g
            WHERE g.models >= (SELECT min_models FROM _gpf_threshold)
              AND NOT EXISTS (SELECT 1 FROM gpf_accounted a WHERE a.term = g.term)
  -- and no term may be accounted for twice in ways that contradict each other
  -- (a term cannot both become a feature and be filed as scoring).
  UNION ALL SELECT 'term_double_booked', a.term, string_agg(DISTINCT a.via, ' + ')
            FROM gpf_accounted a GROUP BY a.term
            HAVING count(DISTINCT a.via) > 1 AND bool_or(a.via <> 'feature')
  -- VOCABULARY: every call must use a known category.
  UNION ALL SELECT 'unknown_category', c.term, c.category
            FROM _gpf_class c
            WHERE c.category NOT IN (SELECT category FROM _gpf_category)

  -- ══ THE VOCABULARY TABLE IS WELL FORMED ════════════════════════════════════
  -- A feature must be matched one way or be an explicit node, never both.
  UNION ALL SELECT 'feature_pattern_and_terms', f.slug, 'has both a pattern and terms'
            FROM _gpf_new f WHERE f.pattern IS NOT NULL AND len(f.terms) > 0
  -- Every parent must exist: either already in the catalog, or created by this
  -- same campaign. A typo here would silently orphan a branch of the tree.
  UNION ALL SELECT 'parent_missing', f.slug, p.parent
            FROM (SELECT slug, unnest(parents) AS parent FROM _gpf_new) p
            JOIN _gpf_new f ON f.slug = p.slug
            WHERE NOT EXISTS (SELECT 1 FROM _gpf_vocab v WHERE v.slug = p.parent)
              AND NOT EXISTS (SELECT 1 FROM _gpf_new n WHERE n.slug = p.parent)
  -- No feature may be its own parent, and no slug may be declared twice.
  UNION ALL SELECT 'self_parent', f.slug, 'names itself as parent'
            FROM (SELECT slug, unnest(parents) AS parent FROM _gpf_new) f WHERE f.slug = f.parent
  UNION ALL SELECT 'duplicate_feature', f.slug, count(*)::VARCHAR
            FROM _gpf_new f GROUP BY f.slug HAVING count(*) > 1
  -- An alias must not collide with a feature name the campaign also creates.
  UNION ALL SELECT 'alias_collides_with_feature', a.alias, a.slug
            FROM (SELECT slug, unnest(aliases) AS alias FROM _gpf_new
                  UNION ALL SELECT slug, alias FROM _gpf_existing_alias) a
            WHERE EXISTS (SELECT 1 FROM _gpf_new n WHERE lower(n.name) = lower(a.alias))
  -- Every feature with terms or a pattern must find at least one model — an
  -- assignable feature that assigns nothing has a broken matcher. NODES are
  -- exempt by design: they exist to parent a child, not to be assigned.
  UNION ALL SELECT 'assignable_feature_dark', n.feature, n.kind
            FROM gpf_new_features n WHERE n.kind <> 'node' AND n.models = 0
  -- A node, conversely, must NOT pick up assignments — if it does, it is really
  -- an assignable feature and its row should say so.
  UNION ALL SELECT 'node_has_assignments', n.feature, n.models::VARCHAR
            FROM gpf_new_features n WHERE n.kind = 'node' AND n.models > 0
  -- A node earns its place ONLY by parenting something. One with no children and no
  -- models is dead vocabulary — it would show an empty page and explain nothing.
  -- Needs the foundation's `children`, which is why this check could not be written
  -- before gameplay_feature_vocab existed.
  UNION ALL SELECT 'node_parents_nothing', n.feature, 'no children and no models'
            FROM gpf_new_features n
            JOIN gameplay_feature_vocab v ON v.slug = n.feature
            WHERE n.kind = 'node' AND len(v.children) = 0

  -- ══ THE CITE IS SOUND ══════════════════════════════════════════════════════
  UNION ALL SELECT 'assignment_without_quote', a.slug, a.feature
            FROM gpf_assignments a WHERE coalesce(trim(a.quote), '') = ''
  UNION ALL SELECT 'quote_not_verbatim', a.slug, a.feature
            FROM gpf_assignments a
            JOIN models m ON m.slug = a.slug
            WHERE a.quote <> '' AND position(a.quote IN m.ipdb_notable_features) = 0
  -- A counted feature must actually have got a count, and an uncounted one must
  -- not have picked one up.
  UNION ALL SELECT 'counted_without_count', a.slug, a.feature
            FROM gpf_assignments a JOIN _gpf_new f ON f.slug = a.feature
            WHERE f.counted AND a.feature_count IS NULL
  UNION ALL SELECT 'uncounted_with_count', a.slug, a.feature
            FROM gpf_assignments a JOIN _gpf_new f ON f.slug = a.feature
            WHERE NOT f.counted AND a.feature_count IS NOT NULL

  -- ══ LANDED: the patches did what the analysis said ═════════════════════════
  -- Every feature 0178 declares must exist in the vocabulary.
  UNION ALL SELECT 'feature_not_created', f.slug, 'missing from the catalog vocabulary'
            FROM _gpf_new f
            WHERE NOT EXISTS (SELECT 1 FROM _gpf_vocab v WHERE v.slug = f.slug)
  -- Every alias 0178 declares must resolve its IPDB term to the intended feature.
  UNION ALL SELECT 'alias_not_resolving', a.term, a.slug
            FROM _gpf_existing_alias a
            WHERE NOT EXISTS (SELECT 1 FROM _gpf_resolved r
                               WHERE r.term = a.term AND r.feature_slug = a.slug)
  -- Every assignment 0179 emits must be a live membership.
  UNION ALL SELECT 'assignment_not_applied', a.slug, a.feature
            FROM gpf_assignments a
            WHERE NOT EXISTS (SELECT 1 FROM gpf_memberships g
                               WHERE g.model_slug = a.slug AND g.feature_slug = a.feature)
  -- SAFETY: a negation term must NEVER have become a feature. `no slingshots`
  -- reaches 113 models; asserting it would invert what the source says.
  UNION ALL SELECT 'negation_became_feature', c.term, c.groups
            FROM _gpf_class c
            WHERE c.category = 'negation'
              AND EXISTS (SELECT 1 FROM _gpf_vocab v WHERE v.term = c.term)
  -- Every family exclusion must still be a live pattern hit, else it is stale.
  UNION ALL SELECT 'stale_family_exclusion', x.feature, x.model_id::VARCHAR
            FROM _gpf_family_excluded x
            JOIN _gpf_new f ON f.slug = x.feature
            WHERE f.pattern IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM _gpf_norm n
                WHERE n.model_id = x.model_id AND regexp_matches(n.term, f.pattern));
