"""Editorial classification for patch 0031 — corporate-entity operating_status
(+ model-level cleanup fixes). Frozen human judgment as data.

`gen.py` reads each row, pulls the verbatim quote from the pinexplore web cache
(by `cache_url`, matching on `needle`, or a `quote` override) and the live
`expect:` guard from the flipcommons DB, then emits the patch via patchkit.

Recency rule (per review): an `ongoing` verdict needs a 2023-or-newer source
showing current production; `ended` is permanent so any dated source is fine.
Web sources are fetched once into the pinexplore cache (docs/WebCache.md); we
cite the primary URL (archive permalinks are a separate base-system concern).

Each ROW dict:
  slug      corporate-entity (or model, for GAME_FORMAT) public_id
  field     'operating_status' | 'game_format'
  value     the claim value
  source    human source name for the note ('<source> says "<quote>"')
  cite      what goes in cite: (a URL, or a scheme like 'opdb:2153')
  cache_url page in the web cache to quote from (defaults to cite when a URL)
  needle    unique substring of the evidence sentence (re-extracted live)
  quote     OPTIONAL verbatim override when the page has no clean sentence
  reason    editorial note (README / audit)
"""

# New citation-source roots this patch seeds (existing roots — Wikipedia, Pinball
# News, Pinside, Kineticist, Multimorphic, Stern Pinball, Museum of the Game, OPDB
# — are reused, not re-declared). (name, homepage, description)
NEW_ROOTS = [
    (
        "Arcade Heroes",
        "https://arcadeheroes.com/",
        "Arcade and amusement industry news site covering coin-op releases and trade shows.",
    ),
    (
        "This Week in Pinball",
        "https://twip.kineticist.com/",
        "Weekly pinball news archive now hosted by Kineticist.",
    ),
    (
        "Ramp's Pinball",
        "https://www.rampspinball.com/",
        "Manufacturer site of Ramp's Pinball, whose debut machine is Road Trip.",
    ),
    (
        "Vector Pinball",
        "https://vectorpinball.com/",
        "Manufacturer site of Vector Pinball, an Australian pinball maker.",
    ),
    (
        "VPForums",
        "https://www.vpforums.org/",
        "Long-running virtual-pinball community forum.",
    ),
    (
        "Bingo Pinballs",
        "https://bingo.cdyn.com/",
        "Reference site documenting bingo-style coin-op amusement machines and their makers.",
    ),
    (
        "Recreativas.org",
        "https://www.recreativas.org/",
        "Spanish-language database of arcade and amusement machines.",
    ),
]

ONGOING = [
    dict(
        slug="american-pinball-inc",
        source="Arcade Heroes",
        cite="https://arcadeheroes.com/2024/02/19/galactic-tank-force-signature-edition-package-now-available-from-american-pinball/",
        needle="Galactic Tank Force",
        reason="Shipping Galactic Tank Force Signature Edition (2024).",
    ),
    dict(
        slug="barrels-of-fun",
        source="Arcade Heroes",
        cite="https://arcadeheroes.com/2025/04/14/barrels-of-fun-unveils-dune-pinball/",
        needle="DUNE",
        reason="Revealed DUNE, its second game (2025).",
    ),
    dict(
        slug="chicago-gaming-company",
        source="Arcade Heroes",
        cite="https://arcadeheroes.com/2025/04/14/newsbytes-king-kong-harry-potter-galaxian-3/",
        needle="Medieval Madness",
        reason="New Medieval Madness production run (2025).",
    ),
    dict(
        slug="hexa-pinball",
        source="Kineticist",
        cite="https://www.kineticist.com/news/hexa-3-musketeers-pinball",
        needle="Musketeers",
        reason="Revealed second title, The 3 Musketeers (2026).",
    ),
    dict(
        slug="homepin-ltd",
        source="Kineticist",
        cite="https://www.kineticist.com/news/first-impressions-blues-brothers-pinball",
        needle="Blues Brothers",
        reason="Shipped Blues Brothers (2025).",
    ),
    dict(
        slug="jersey-jack-pinball-inc-lakewood-nj",
        source="Kineticist",
        cite="https://www.kineticist.com/news/jersey-jack-launches-harry-potter-pinball",
        needle="Harry Potter",
        reason="Launched Harry Potter pinball (2025).",
    ),
    dict(
        slug="multimorphic-inc",
        source="Multimorphic",
        cite="https://www.multimorphic.com/news/portal-production-update-october-2025/",
        needle="Portal",
        reason="Portal P3 game kit shipping (2025).",
    ),
    dict(
        slug="pedretti-gaming",
        source="Pinball News",
        cite="https://www.pinballnews.com/site/2024/05/14/funhouse-remake-revealed/",
        needle="Pedretti",
        reason="Italian maker; Funhouse remake (2024).",
    ),
    dict(
        slug="pinball-adventures",
        source="Kineticist",
        cite="https://www.kineticist.com/manufacturers/pinball-adventures",
        needle="debut title",
        reason="Active Canadian maker; debut Punny Factory released 2023.",
    ),
    dict(
        slug="pinball-brothers",
        source="Arcade Heroes",
        cite="https://arcadeheroes.com/2024/04/09/pinball-brothers-launches-game-3-abba/",
        needle="ABBA",
        reason="Released ABBA, third title (2024).",
    ),
    dict(
        slug="spooky-pinball-llc",
        source="Kineticist",
        cite="https://www.kineticist.com/news/spooky-pinball-reveals-new-evil-dead-pinball-machine",
        needle="Evil Dead",
        reason="Evil Dead on the line, shipping 2025.",
    ),
    dict(
        slug="stern-pinball-incorporated",
        source="Stern Pinball",
        cite="https://sternpinball.com/2025/01/03/stern-pinball-invites-players-to-embark-on-an-epic-journey-into-the-forgotten-realms-of-dungeons-dragons/",
        needle="largest manufacturer",
        reason="Largest maker; D&D announced (2025).",
    ),
    dict(
        slug="turner-pinball",
        source="Kineticist",
        cite="https://www.kineticist.com/news/new-pinball-machines-2025",
        needle="Turner Pinball",
        quote="Texas-based Turner Pinball's second title, Merlin's Arcade, swaps ninjas for wizards.",
        reason="Second title Merlin's Arcade (2025).",
    ),
    dict(
        slug="vector-pinball",
        source="Vector Pinball",
        cite="https://vectorpinball.com/about",
        needle="exporting",
        quote="Now in 2026 we are doing more exporting and offering some international licenced titles!",
        reason="Australian maker; Eight Ball Fury (2024); exporting/new titles (2026).",
    ),
    dict(
        slug="ramps-pinball",
        source="Ramp's Pinball",
        cite="https://www.rampspinball.com/machines/road-trip",
        needle="Expected Late 2026",
        quote="Expected Late 2026 [...] Coming soon.",
        reason="Has an announced model (Road Trip, Expected Late 2026) -> ongoing by definition.",
    ),
    dict(
        slug="for-amusement-only-games",
        source="Pinball News",
        cite="https://www.pinballnews.com/site/2025/07/01/steelbound-announced/",
        needle="Steelbound",
        reason="Steelbound, Baldridge's sixth P3 project (2025).",
    ),
    dict(
        slug="ian-harrower-games",
        source="Kineticist",
        cite="https://www.kineticist.com/manufacturers/ian-harrower-games",
        needle="indie game developer",
        quote="The commerical and open source pinball projects from indie game developer Ian Harrower.",
        reason="Own label, 2 games (Bird Watcher 2023, Blood Bank Billiards 2024); listed 2023-Present.",
    ),
    dict(
        slug="dutch-pinball",
        source="Pinball News",
        cite="https://www.pinballnews.com/site/2026/02/09/melvin-splits-with-dutch-pinball/",
        needle="still building",
        quote="DPX is a joint venture between Melvin and Dutch Pinball, using Melvin’s designs and intellectual property with the game built by Dutch Pinball at their factory in Herkenbosch in the Netherlands. DPX launched their first title, Alice’s Adventures In Wonderland, in October 2024, and are still building the game which has a limited run of 500 units.",
        reason="Dutch Pinball is still building Alice in 2026, with new in-house projects planned.",
    ),
    dict(
        slug="rebellion-pinball",
        source="Kineticist",
        cite="https://www.kineticist.com/manufacturers/rebellion-pinball",
        needle="2022-Present",
        quote="Rebellion Pinball Updated April 2026 Primary 2022-Present 1 Pinball Games [...] Space Singularity is a pinball creation project. Made from scratch by 4 friends.",
        reason="Ongoing hobby/homebrew project; commercial scale is not required for operating_status.",
    ),
]

ENDED = [
    dict(
        slug="deeproot",
        source="Pinball News",
        cite="https://www.pinballnews.com/site/2021/08/21/game-over-for-deeproot-pinball/",
        needle="Securities and Exchange",
        reason="Collapsed 2021; SEC fraud charges; no machine ever shipped.",
    ),
    dict(
        slug="haggis-pinball",
        source="Pinball News",
        cite="https://www.pinballnews.com/site/2024/07/18/haggis-pinball-in-liquidation/",
        needle="ceased trading",
        reason="Ceased trading / liquidation July 2024.",
    ),
    dict(
        slug="heighway-pinball-ltd",
        source="Wikipedia",
        cite="https://en.wikipedia.org/wiki/Heighway_Pinball",
        needle="closed the doors",
        quote="By April 2018, Heighway Pinball had closed the doors on its factory, laid off its employees, and was liquidated soon afterward.",
        reason="Factory closed / liquidated April 2018.",
    ),
    dict(
        slug="marsaplay",
        source="Wikipedia",
        cite="https://en.wikipedia.org/wiki/List_of_pinball_manufacturers",
        needle="MarsaPlay",
        quote="MarsaPlay (2010-2013)",
        reason="Single game (New Canasta 2010); listed in Wikipedia's Past (defunct) section as 2010-2013.",
    ),
    dict(
        slug="whizbang-pinball",
        source="Wikipedia",
        cite="https://en.wikipedia.org/wiki/List_of_pinball_manufacturers",
        needle="WhizBang",
        quote="WhizBang Pinball (2011-2017)",
        reason="Boutique maker; listed in Wikipedia's Past (defunct) section as 2011-2017.",
    ),
    dict(
        slug="zidware",
        source="Wikipedia",
        cite="https://en.wikipedia.org/wiki/John_Popadiuk",
        needle="out of funding",
        reason="Out of funding 2015; Magic Girl/AIW/RAZA never delivered.",
    ),
    dict(
        slug="skit-b-pinball",
        source="VPForums",
        cite="https://www.vpforums.org/index.php?showtopic=30926",
        needle="license for Predator",
        reason="Predator cancelled 2015 over a fake license / refund scandal.",
    ),
    dict(
        slug="bandai-namco",
        source="Arcade Heroes",
        cite="https://arcadeheroes.com/2019/01/25/jaepo-2019-pinball-in-japan-bandai-namco-unveils-pac-man-panic/",
        needle="multiball battles",
        reason="Versus-pinball arcade novelty (2019); not a pinball OEM.",
    ),
    dict(
        slug="kieswetter-kg",
        source="Museum of the Game",
        cite="https://www.arcade-museum.com/Pinball/pinball-42",
        needle="Kieswetter",
        reason="Pinball-42 video-multigame novelty cabinet (2014); one-off.",
    ),
    dict(
        slug="the-pinball-company",
        source="Arcade Heroes",
        cite="https://arcadeheroes.com/2017/01/30/jetsons-pinball-announced-pinball-company-spooky-pinball/",
        needle="game distributor",
        quote="The Pinball Company is a game distributor who covers more than just pinball machines.",
        reason="A distributor/retailer, not a manufacturer; Jetsons built by Spooky.",
    ),
    dict(
        slug="valley-dynamo",
        source="Wikipedia",
        cite="https://en.wikipedia.org/wiki/Valley-Dynamo",
        needle="pool tables",
        quote="It has been the dominant manufacturer of coin-operated pool tables in North America for over 6 decades, and produces the US-ubiquitous Valley brand and decreasingly common Dynamo brand (once a competitor).",
        reason="Coin-op pool/foosball/air-hockey maker; not a pinball OEM.",
    ),
    dict(
        slug="novomatic-ag",
        source="Wikipedia",
        cite="https://en.wikipedia.org/wiki/Novomatic",
        needle="international gambling company",
        quote="Novomatic is an international gambling company based in Austria, founded by Johann Graf in 1980.",
        reason="Austrian gambling/slots firm; Pinball Roulette is a gambling machine, not pinball.",
    ),
    dict(
        slug="american-girl",
        source="Kineticist",
        cite="https://www.kineticist.com/games/pinball/the-flip-side-2019",
        needle="18-inch dolls",
        reason="Doll company; The Flip Side is a scaled toy for 18-inch dolls (2019, retired 2022).",
    ),
    dict(
        slug="sirmo-games-sa",
        source="Bingo Pinballs",
        cite="https://bingo.cdyn.com/machines/sirmo/magic_screen",
        needle="continues to manufacture",
        quote="Sirmo continues to manufacture the machines that look like a six card game, but due to the LCD display, they also have numerous special games included.",
        reason="Still trading, but now bingo/AWP gambling machines, not flipper pinball.",
    ),
    dict(
        slug="bifuca",
        source="Recreativas.org",
        cite="https://www.recreativas.org/pinball-tronic-4437-bifuca-sl",
        needle="pinball virtual",
        reason="Made Pinball Tronic, a video-screen 'virtual pinball'; small Spanish firm, defunct (dissolved 2012, BORME).",
    ),
    dict(
        slug="suncoast-pinball",
        source="This Week in Pinball",
        cite="https://twip.kineticist.com/p/this-week-in-pinball-september-30th-2019",
        needle="shutting down pinball operations",
        quote="It is with a heavy heart that Suncoast Pinball announces we will be shutting down pinball operations. Due to unexpected delays, higher than expected costs and other factors, continuing is not financially viable for us.",
        reason="Suncoast's own customer correspondence said it was shutting down pinball operations in 2019.",
    ),
    dict(
        slug="day-one-pinball-manufacturing-incorporated",
        source="Pinball News",
        cite="https://www.pinballnews.com/news/scoregasmmaster.html",
        needle="total of thirty",
        quote="Day One Pinball will build a total of thirty ScoreGasm Master games; ten prototypes and twenty production units.",
        reason="Fixed one-off run of ScoreGasm Master (2015), not an ongoing maker.",
    ),
    dict(
        slug="retro-pinball-llc",
        source="IPDB",
        cite="ipdb:5239",
        quote="Production ended in 2012 after 5 sample production games and 50 regular production games were built.",
        reason="IPDB explicitly says King of Diamonds production ended in 2012.",
    ),
]

# Model-level fixes that ride along with the maker statuses (each has a `field`).
#   game_format: Bifuca's Pinball Tronic is a video-screen 'virtual pinball', not pinball.
#   production_status: Road Trip is announced (Expected Late 2026), not a shipped 2025 game.
MODEL_FIXES = [
    dict(
        slug="pinball-tronic",
        field="game_format",
        value="miscellaneous",
        source="Recreativas.org",
        cite="https://www.recreativas.org/pinball-tronic-4437-bifuca-sl",
        needle="pinball virtual",
        reason="Video-screen playfield (two LCD monitors) in a pinball cabinet — a non-pinball game.",
    ),
    dict(
        slug="road-trip",
        field="production_status",
        value="announced",
        source="Ramp's Pinball",
        cite="https://www.rampspinball.com/machines/road-trip",
        needle="Expected Late 2026",
        quote="Expected Late 2026 [...] Coming soon.",
        reason="Debut machine is forthcoming, not a shipped 2025 game.",
    ),
    dict(
        slug="cactus-canyon-continued",
        field="production_status",
        value="aftermarket",
        source="OPDB",
        cite="opdb:2155",
        quote="Cactus Canyon Continued (Eric Priepke, 2012) [...] Converted game",
        reason="A third-party code patch / conversion for the existing Bally Cactus Canyon — aftermarket, not a new machine.",
    ),
    dict(
        slug="demolition-man-on-steroids",
        field="production_status",
        value="aftermarket",
        source="OPDB",
        cite="opdb:2153",
        quote="Demolition Man on Steroids (Pinnovating, 2013) [...] Converted game",
        reason="A third-party retheme/conversion of Williams' Demolition Man — aftermarket, not a new machine.",
    ),
]

# Genuinely ambiguous → NOT asserted; fall to the Commit-5 ended baseline. (slug, reason)
DEFER = [
    (
        "megaverse-project",
        "One NFT-themed one-off (Escape From The Megaverse, 2022). OPDB/Kineticist-style ledger evidence supports exactly one catalogued game and no visible production line, but inactivity/closure is still an inference, not a citable event.",
    ),
    (
        "mocean",
        "One P3 game (Dungeon Door Defender, 2023). Kineticist lists Mocean as Not Primary and 2023-Present, consistent with an active P3 ecosystem/module developer rather than a complete-machine manufacturer.",
    ),
    (
        "headsup-pinball",
        "Pinside/IPDB prove a limited 2022 Wizard run: planned quantity 16, 14 made as of March 2023, plus 12 conversion kits. This supports a small limited run but not closure, so do not assert active or ended here.",
    ),
    (
        "quetzal-pinball",
        "IPDB lists Quetzal as 2015-now and Wikipedia lists Quetzal as Present, but no clean 2023+ source showing current Quetzal-branded production surfaced. Do not assert active from stale/current-list evidence alone.",
    ),
    (
        "team-pinball",
        "Pinball News teaser calls Team Pinball a UK-based pinball software/hardware developer in 2026, and it provides code for Pedretti's Funhouse 2.0 kit; no current complete-machine production under its own name.",
    ),
    (
        "riot-pinball-llc",
        "Homebrew/design collective; designed Legends of Valhalla and licensed commercial production elsewhere. Existing evidence supports design activity, not complete-machine manufacture under Riot's own brand, and no closure source.",
    ),
    (
        "eric-priepke",
        "One model, Cactus Canyon Continued (2012) — an aftermarket code patch (fixed below); nothing since, not currently producing. No closure event to cite, so left to the baseline.",
    ),
    (
        "pinnovating",
        "One model, Demolition Man on Steroids (2013) — an aftermarket retheme (fixed below). Its OPDB 'Converted game' note supports aftermarket, NOT ended; dormant but no closure event to cite, so left to the baseline.",
    ),
    (
        "wee-chin-electric-machinery-inc",
        "IPDB proves WeChe/Wee Chin made Space War (2017), Bubbles Pop (2019), and Football (2019), with manufacturer-sourced files for the 2019 games. No 2023+ production or closure source surfaced; the company site still blocks automated fetch.",
    ),
]
