# Galactic Tank Force — family campaign record (patch 0222)

American Pinball's 5th title. Original non-licensed Dennis Nordman design, unveiled 2023-03-22, famous for live-action FMV performances by four actors on the display. Five catalog models: Classic, Deluxe, Limited Edition, Signature (2023) and Victory Edition (2026, created bare by 0215).

## Baseline survey (2026-08-10, dev DB at patch 0221)

| field | classic | deluxe | limited-edition | signature | victory-edition |
| --- | --- | --- | --- | --- | --- |
| year / month | 2023 / 3 | 2023 / 3 | 2023 / 3 | 2023 / 3 | 2026 / — |
| production_status | — | — | — | — | — |
| game_format | — | — | — | — | — |
| system | — | — | — | — | — |
| cabinet | — | — | — | — | — |
| display_type | lcd (opdb) | — | — | — | — |
| technology_generation | solid-state | — | — | — | — |
| player_count | 4 (opdb) | — | — | — | — |
| model number | — | — | — | — | — |
| credits | none | none | none | none | none |
| gameplay features | 15 (see below) | same 15 | same 15 | same 15 | — |
| themes | outer-space, science-fiction | same | same | same | same |
| tags | — | — | limited-edition | limited-edition | — |
| variant_of | — | classic | classic | classic | — |
| production_quantity | — | — | — | — | — |
| description | — | — | — | — | — |

The 15 seeded features (actor `flipcommons-catalog`, uniform across the 2023 four): auto-launch, ball-locks×3, flippers×2, magnets×1, multiball, orbits×2, pop-bumpers×3, ramps, rollovers, skill-shot, slingshots×2, spinners×2, standup-targets, up-posts×1, vertical-up-kickers×2. Victory has none of them.

Raw `opdb_features`: Classic "Pro edition", Deluxe "Premium edition", LE and Signature both "Limited edition". No model in the family has an IPDB row, so there are no `ipdb:` cites — everything rests on AP's own documents plus journalism.

## The editions, disentangled

Pinball News (2023-03-22, launch day): "It is now confirmed that there will be four versions of the game available: Classic, Deluxe, Limited and Signature with only the latter two including the tank-like cabinet sides and backbox." So LE and Signature both have the tank cabinet; Classic and Deluxe are conventional cabinets, Deluxe adding side art / shaker / AURA / Magic Glass / knocker over Classic.

- **Signature** (AP announcement 2023-11-20): 200 units, "custom painted 'Glow Tech' toys that shift colors with the playfield lighting, Radiant Rubber Reactive Bands from TITAN, retro green powder coated metal, retro-SciFi Diamond Coated Playfield Artwork by Christopher Franchi, and a 3-Dimension Lenticular Backglass", plus the "Fold-n-Fight Tank Turret" backbox. Shipping began Feb 2024 with a merch package (posters, banner, lunchbox, thermos, playfield cover, pint glass) — Arcade Heroes 2024-02-19.
- **Victory Edition** (announced 2026-07-30, ships August 2026): final production run, 100 individually numbered units, $8,995. AP: "The cabinet artwork, translite, and core playfield feature the same setup of the now-retired Deluxe Edition" — so its base is **Deluxe**, not Classic. Adds Galactic Blue armor, numbered Captain Kyan apron, Franchi-designed lit topper, upgraded interactive tank sculpt (The Art of Pinball, 3 embedded interactive LEDs, retains the motorized action).
- **Trap**: the live 2026 product page's "Limited" panel mixes Signature content (tank cabinet, signed apron, merch list) and its add-ons block is literally headed "Signature Add Ons" — the WP rebuild collapsed LE and Signature into one panel. Use the 2023-era archived pages and the Signature announcement for the 2023 editions, not the live page's "Limited" panel.

## Evidence inventory (all cached in the pinexplore web cache)

First-party, live (americanpinball.com — resolves to the AP citation root; store.americanpinball.com resolves as a subdomain):

- `https://americanpinball.com/galactic-tank-force` — live product page (WP rebuild, published 2026-06). og:description calls it "a sci-fi pinball machine" (game_format evidence). Victory Highlights section: 100 units, final run, "first launched in 2023", Deluxe-setup carry quote, "Designed by original game artist Chris Franchi" (topper). Per-edition Features blocks explicitly headed Deluxe / Victory / Limited — but see the LE/Signature trap above.
- `https://americanpinball.com/galactic-tank-force-victory-edition` — Victory announcement, posted 07/30/2026. "Just 100 units will be available and each will be individually numbered", "MSRP: $8,995", "Shipping Begins August 2026", Deluxe features list, "same $8,995 price as the previous deluxe (standard) edition".
- `https://americanpinball.com/galactic-tank-force-code-update` — July 2026 code update news (v26.07.27B; Tank Zulu mini-wizard mode, 3rd flipper button / left-magnet interaction).
- `https://store.americanpinball.com/products/galactic-tank-force-captain-kyan-victory-topper` and `.../galactic-tank-force-upgraded-interactive-tank-sculpt` — Victory add-ons ($179 / $299).
- `https://store.americanpinball.com/products/hot-wheels-aura-lighting` — "[MASM0271-00] AURA Lighting-Code Controlled … -Hot Wheels -Barry O's BBQ -Galactic Tank Force". Thin: names the kit and the games, does not describe what AURA physically is.

First-party support PDFs (HubSpot host `48804760.fs1.hubspotusercontent-na1.net`, attached to the AP root by 0217):

- **Game Manual** (`.../Game%20Manuals/Galactic%20Tank%20Force%20-%20Game%20Manual.pdf`, v1.0 Oct 2023, 58+ pages, text layer readable) — service manual: service menu, board connectors, code update, game rules chapter (SKILL SHOTS (2), MULTIBALL MODES (3), WIZARD MODES (3)). **No credits, no spec table, no system name, no display size.** Same content also at the old host `s4.american-pinball.com/img/support/2023-11/...` (Wayback-archived).
- **Quick Reference Guide** (`.../Quick%20Reference%20Guides/...`) — fuses/coils sheet, OCR-only (no text layer). Coil labels include KNOCKER and UPPER MAGNET. Render to cite.
- **Release notes** ×2 (25.08.28, 26.07.27B) + **Treads Installation Guide** — code history; treads guide is for the tank-cabinet treads panels ("Tank Treads July 3, 2023 Written by LUK").

First-party, Wayback (old site `american-pinball.com`; cite `ref` = original URL + `archive:` = snapshot, per RULEBOOK Citation roots → archive):

- 2023-06-06 product page `https://www.american-pinball.com/games/galactic-tank-force/` (snapshot `20230606065409`) — "American Pinball unleashes \"Galactic Tank Force\" on March 22nd, 2023!"; names the four actors ("Kerri Hoskins, Jeff Hoover, Mitchell Politt, and Clementine Morfoot"); story/features prose; links the GTK M13 flyer.
- Signature announcement `https://www.american-pinball.com/news/galactic-tank-force-signature-edition` (snapshot `20240229215015`, posted 11/20/2023) — the 200-unit quote and the Signature feature list, "Diamond Coated Playfield Artwork by Christopher Franchi".
- Slam Tilt team post `https://www.american-pinball.com/news/slam-tilt-podcast-interviews-the-galactic-tank-fo` (snapshot `20231002204904`, posted 8/14/2023) — **the credits source**: "Dennis Nordman (Design), Paul Reno (Design), Jack Haeger (Art Director), Christopher Franchi (Artist), and Steve Bowden (Rules)".
- Cast post `https://www.american-pinball.com/news/american-pinball-inc-with-the-stars-of-galactic-t` (snapshot `20231129091706`, posted 11/8/2023) — actors ↔ characters, spelled "Mitchell Pollitt" here.
- GTK M13 flyer `https://www.american-pinball.com/games/galactic-tank-force/img/GTK_M13_Flyer.jpg` (snapshot `20250920035317`) — playfield-callout flyer (JPG; **hand transcription filed 2026-08-10 via `web_import.py --text-file`, so its quotes gate like text**): L-A-B Lanes, Reactor Bumpers, Accelerator Targets, AIR Lock Targets, AIR Spinner, Planet Spinner, Alpha Flank Targets, Mission Lanes, Tank Battles, Atomic Shield, Controlled Diverter ("Use the third flipper button to divert ramp shots"), UFO Moving Target, Space Station AIR Lock, Plotnik's Lab. **Its playfield photo shows the machine's printed CREDITS panel beside the shooter lane** — the family's only first-party source for the full team: "Dennis Nordman & Paul Reno ... GAME DESIGN / Zofia Bil Ryan ... DIRECTOR OF MECH. ENGINEERING / Jack Haeger ... ART DIRECTION / Christopher Franchi ... ARTWORK / Jessica Durbala & Bobby Llereza ... 2D+VIDEO ART / Joe Schober, Casey Butler & Steve Bowden ... GAME CODE / Mitesh Pithva ... ENGINEERING / Matt Kern ... AUDIO ENGINEER / David Fix ... EXECUTIVE VICE PRESIDENT". Reading aids: the cursive is ~8 px tall at the flyer's 1259×1619 resolution — read via cropped 8× enlargements, with Llereza and Pithva cross-checked against AP animation-team coverage and staff listings, and Reno (vs a possible "Ryan" reading) settled by AP's own team post + Slam Tilt/Pinball News/pinballmag all naming Paul Reno. The only copy anywhere is Wayback's 585 KB JPG (the live URL 404s; the archived gallery previews are smaller).
- Board kit `https://store.american-pinball.com/products/api-galactic-tank-force-new-board-system-kit-kit0016-00` (snapshot `20240712140741`) — AP part-numbered PCBs (motherboard PCB0108-00, coil driver PCB0110-00, switchboards PCB0109-00); **no named control system**.
- Field guide news page (snapshot `20230606071043`) → links the field guide video.

First-party video (YouTube, auto-captions ingested): `https://www.youtube.com/watch?v=VJ5Uds79dQw` — "Galactic Tank Force Field Guide - American Pinball" (2023-05-24), narrated gameplay/rules guide.

Journalism:

- Pinball News launch article `https://www.pinballnews.com/site/2023/03/22/galactic-tank-force-promo-released` — the four-versions quote; actor↔character mapping (spelled "Mitchell Pollitt"); "game designer Dennis Nordman appears in the game as the voice of the Nord-Man 3000 robot"; feature sightings (autoplunger, upkicker, player-operated ball diverter on second right flipper button, swinging UFO target, tank target bank).
- Arcade Heroes unveiling (2023-03-22) — corroboration; garbles the edition names ("Standard, Classic, Signature & Deluxe"), don't cite for editions. Kerri Hoskins is the Midway digitized-actor actress.
- Arcade Heroes Signature package (2024-02-19) — "they have begun shipping the Signature Edition (SE)", "There are only 200 of these being made", "signed by the whole team", "original non-licensed design by Dennis Nordman", "out since March 2023".
- Pinball News Expo 2023 report — seminar (David Fix & creative team), actors signing, "The editions with the illuminated tank tracks were on the stand too"; spells "Mitchell Politt".

Distributor (research/spec fallback; roots NOT seeded — citable only if we decide to create roots): PrimeTime Amusements (`Galactic Tank Force [Standard / Deluxe]`, dimensions/weight/electrical), Flip N Out (Signature), On Tilt (LE $10,995 / Deluxe $8,995 / "Signature edition contact for price"). Web results attribute "HD LCD display" and "1-4 players" spec text to reseller sheets (gameroomshop, luxegametables — not fetched).

The draft-evidence-aggregator's 4 GTF rows are all Victory credits from Pinside (Nordman/Schober/Franchi/Kern) — used as a research checklist only; Pinside is barred for this family (manufacturer PDFs exist).

## Primary-source conflicts

- **"Mitchell Politt" vs "Mitchell Pollitt"** — AP's own sources split: product page prose (2023 + live 2026) says Politt; AP's cast news post says Pollitt. Journalism splits identically (Pinball News launch: Pollitt; Pinball News Expo report: Politt). Needs a user ruling if we credit the actors.

## Sought and not found

- **System** — the manual never names the control system; the board kit lists AP's own part-numbered PCBs with no system name. Pinside claims "Multimorphic P3-ROC" but is barred here (crowdsourced + manufacturer PDFs exist) and the AP-built boardset contradicts it. No `system` claim.
- ~~Software / sound credits (Joe Schober, Matt Kern)~~ — **resolved 2026-08-10**: the GTK M13 flyer's playfield photo carries the machine's printed credits panel naming both (plus Butler, Durbala, Llereza, Bil Ryan, Pithva); asserted once the flyer transcription was filed. The earlier dead ends stand as recorded: Pinside/Kineticist barred, AP's team post names neither, release notes unattributed, mattkern.com unquotable (stale, spam-injected credits page).
- **Display type/size** — no AP source states the display beyond "the machine's display". Reseller sheets say "HD LCD" but their roots aren't seeded. Classic's `lcd` (OPDB) stands; nothing asserted for the other four unless the distributor-root question is decided otherwise.
- **LE production quantity** — no source states how many Limited Editions were made (the 200 figure is Signature's).
- **Classic-edition shipping evidence** — the live page dropped Classic entirely and Pinside's group has no Classic row; no source states Classic units actually shipped. production_status for Classic rests on family-level "first launched in 2023" + retired language, weaker than the per-edition evidence for Deluxe/Signature.
- **Model numbers** — no manufacturer model identifiers found anywhere.

## Not asserted (and why)

- `cabinet: floor` — no source states the form factor in quotable words; 0216/0220/0221 skipped cabinet on the same grounds.
- Magnet count — the QRG's UPPER MAGNET coil alongside the code notes' "left magnet" suggests magnets ≥2, vs the seeded ×1; evidence too murky to supersede, parked (skill-shot/multiball counts WERE superseded, see Decisions).
- LE per-edition features (tank cabinet, treads, signed items) — no clean source separates LE's extras from Signature's (the live-page panel merge); unique features recorded below instead.
- Merch-package items (posters, banner, lunchbox, thermos, pint glass, playfield cover), signed apron, numbered apron decals — package contents and unique decorations, not machine features → future-unique-features list.
- Descriptions — no done family wrote model descriptions; out of campaign scope.
- Feature vocabulary considered and NOT created: wizard-modes / mini-wizard-modes (rules content, not a machine feature — the 0219 too-granular lesson); Glow Tech, TITAN reactive bands (branded finishes, not generic features); a location-axis node for AURA (no source states where on the machine AURA lives).

## Decisions

- **Themes stay untouched (user, 2026-08-10).** All five rows carry outer-space + science-fiction; the vocabulary parentage (science-fiction under outer-space) is wrong and the user will fix the vocabulary separately. 0222 asserts no themes and retracts none.
- **Actors credited as `other` + Nordman `voice` (user, 2026-08-10).** The four display-cast actors carry role `other` (the taxonomy has no performer role), with the actor↔character mapping recorded here: Hoskins→Empress Annoya, Hoover→Professor Plotnik, Pollitt→Duke Moonwalker, Morfoot→Captain Kyan. Nordman additionally carries `voice` for the Nord-Man 3000 robot (Pinball News).
- **Surname ruling: Pollitt (user, 2026-08-10).** Person created as `mitchell-pollitt` "Mitchell Pollitt" with "Mitchell Politt" as an alias (see Primary-source conflicts).
- **Victory Edition is `announced` (user, 2026-08-10).** "Shipping Begins August 2026" — announced per the vocabulary (officially announced but not yet shipped) as of authoring 2026-08-10. Revisit once shipping is documented.
- **skill-shot ×2 and multiball ×3 supersede the uncounted seed attachments (user, 2026-08-10)**, cited to the manual's rules-chapter headings (printed page 44, PDF page 54). The manual itself teases undocumented extra skill shots; the count follows the maker's own heading.
- **Victory's base is Deluxe, not Classic** — AP's own carry statement ("same setup of the now-retired Deluxe Edition"); the 2023 editions keep their existing variant_of Classic. Chain depth 2 (Victory→Deluxe→Classic) mirrors the Stern LE→Premium shape.
- **Bowden's "Rules" maps to `design`, Haeger's "Art Director" to `art`** — recorded in the patch notes.
- **Flyer credit-panel role mappings (2026-08-10)**: GAME CODE → software (Schober, Butler, Bowden — so Bowden carries design *and* software); 2D+VIDEO ART → animation (Durbala, Llereza); DIRECTOR OF MECH. ENGINEERING and ENGINEERING → mechanics (Bil Ryan, Pithva); AUDIO ENGINEER → sound (Kern). **David Fix (EXECUTIVE VICE PRESIDENT) is a corporate title, not a credit role — not asserted.**
- **Zofia Bil Ryan, not Sofia** — the machine's printed credits and Pinball News' launch coverage say Zofia; the Sofia spelling (Pinball News Expo report prose) is kept as a person alias. Not a primary-source conflict: AP itself never wrote Sofia.
- **Month semantics**: Victory `month: 7` = announcement/launch month (posted 07/30/2026), matching the 2023 rows' month 3 (unveiled March 22, 2023).
- Distributor citation roots (PrimeTime etc.) were NOT created for the sake of "HD LCD"/"1-4 players" spec text — reseller sheets, heavy root cost for weak facts; display and player_count stay unasserted on the non-Classic rows.

## Gate runs

- `make verify-quote-verbatim` (2026-08-10): first run 5× NO-SOURCE on the GTK M13 flyer JPG cite — **an image with OCR-only text has no skip lane and reports NO-SOURCE, unlike a PDF's SKIP-PDF** (tooling feedback filed). Re-cited the diverter to Pinball News' photo caption (text) with the flyer named in the note. Final: 203 verified / 0 failed / 37 SKIP-PDF (the manual counts quote, author-transcribed off page 54).
- `make verify-quote-support ARGS="0222"` (2026-08-10, 49 calls / ~256k tokens): 7 warnings, all kept after triage — 5× "motorized ≠ animatronic" (taxonomy-level; the animatronic-toys leaf is this taxonomy's node for motor-animated toys, 0220 Megatron precedent; note strengthened), 1× Victory `announced` (linter misreads the vocabulary — announced means not-yet-shipped, exactly the cited state; user-ruled), 1× Victory count-carry (the 0221 variant-ladder pattern, reasoning in the note). No re-run.
- Snapshot apply (2026-08-10, `db.prod.patch-0214.2026-08-03` + migrate + ingest all): 0222 success — 139 claims asserted, 0 retracted, 0 rejected, 61 citation instances; 10 credits per model; Victory carries 24 features with counts; supersedes landed (skill-shot 2 / multiball 3 family-wide). Left applied.
- **Round 2 (2026-08-10, after the flyer transcription was filed)** — the "no image skip lane" reading was wrong (user correction): an image quote *stays gated*; filing the hand transcription via `web_import.py --text-file` made all 20 flyer quotes verify (223/0). The patch grew to 66 entries: eight flyer credits per model (18-credit roster each), five new people (Butler, Durbala, Llereza, Bil Ryan, Pithva), moving-targets from the UFO callout, and the diverter re-cited to the flyer's own words. Support gate re-run (59 calls / ~299k tokens): 2 warnings, both prior-triaged keeps (Victory `announced`, variant count-carry) — every flyer credit and the strengthened animatronic note passed. Snapshot restored + replayed: 200 claims asserted, 0 rejected. First replay attempt hit `database is locked` from a long-running `manage.py runserver` (PID 10339, not this session's) plus a transient duckdb reader; retry after the reader exited succeeded with the server still up.

## Future unique features

- Fold-n-Fight Tank Turret backbox (LE, Signature) — the fold-down turret cabinet, "a one-of-a-kind attraction in itself"
- Tank tread side panels with animated LED lighting (LE, Signature; Treads Installation Guide)
- Interactive Tank Sculpt — motorized (all editions); Victory's Art of Pinball upgrade adds 3 embedded interactive LEDs
- Captain Kyan Victory Topper, dual-panel acrylic, dedicated LED strip, art by Chris Franchi (Victory)
- Swinging UFO target (all editions; Pinball News)
- Atomic Shield / controlled diverter on second right flipper button (all editions; flyer + Pinball News)
- Glow Tech color-shifting hand-painted toys (Signature)
- TITAN Radiant Rubber Reactive Bands (Signature)
- 3-Dimension Lenticular Backglass (Signature; also on live page's "Limited" panel — see trap)
- Individually numbered Captain Kyan apron 1–100 (Victory); signed apron (Signature)
- Illuminated shooter rod housing (Pinball News)
