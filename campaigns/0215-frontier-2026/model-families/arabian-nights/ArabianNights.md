# Tales of the Arabian Nights

Patch: `patches/0226-arabian-nights.yaml` (claimed 2026-08-11; 0225 was already spoken for by a concurrent session).

Supplement: `patches/0228-arabian-nights-documents.yaml` (claimed 2026-08-12) — the [document-cites](../../RULEBOOK.md#document-cites) pilot: the Williams-era documents 0226 recorded as unused (Operations Manual May 1996, Operators Handbook, parts list, Service Bulletin #91, flyer sides). Numbered above 0227 because it cites the `williams` publisher root seeded there.

## Models

- Tales of the Arabian Nights (30th Anniversary Remake) (Pedretti Gaming • 2026) — `tales-of-the-arabian-nights-30th-anniversary-remake`
- Tales of the Arabian Nights (Legacy Edition Remake) (Pedretti Gaming • 2026) — `tales-of-the-arabian-nights-legacy-edition-remake`
- Tales of the Arabian Nights (Williams • 1996) — `tales-of-the-arabian-nights`, ipdb:3824

## Baseline (surveyed 2026-08-11)

The two remakes hold only what 0215 created: name, slug, title, theme ×4 (fantasy, literature, myth-and-legend, mythology), year, status, corporate_entity. Everything else is open. The 1996 original is richly seeded from IPDB/OPDB: all 10 credits (Popadiuk design; McMahon art; Rhine + Morris animation; Zabriskie music + sound; Koziarz software; Skalon/Pizarro/Loveday mechanics), 10 gameplay features, system WPC-95, display dot-matrix, production_quantity 3128, month 5, player_count. Its open gaps: `game_format`, `production_status`, and toy classification (IPDB's `Toys:` line — Genie bash toy, Lamp on spinning posts — was never classified into the 0219 toys tree).

## The maker's real domain

**`pinballremakes.com` IS Pedretti Gaming's own site** — footer: Via Martin Luther King 3, 24060 Bagnatica (BG), info@pedrettigaming.it, "© 2021-2026 Pinball Remakes - REA: BG 445013". `pedrettigaming.it` 301-redirects there; `pedrettigaming.com` fails DNS and has **nothing in Wayback** (CDX empty for the whole domain, checked 2026-08-11). The **Pedretti Gaming citation root already exists and covers pinballremakes.com** — no new root needed. Their store also uses `shop.pedrettigaming.it` (parts; not needed by this family).

## Evidence inventory (all cached)

- **Pinball News press-release reprint** `https://www.pinballnews.com/site/2026/06/15/tales-of-the-arabian-nights-remake-revealed` — press-release tier (Pedretti's words verbatim, datelined Bagnatica, Italy – June 15, 2026). The whole release sits in one table-cell block. Carries: both editions, 399 hard cap for 30th, "Initial production limited to 500 units in 2026" for Legacy (soft), MSRPs ($10,999 / $11,999), Brian Allen + Flyland Designs new art on 30th, Legacy keeps 1996 art + metallic trims, dual code 1.0 + enhanced 1.5+, RGB feature list (Magic Lamp RGB, Genie internal RGB, GameSync RGB sidebars, illuminated playfield back panel), Athyrio (software partner), FAST Pinball (electronics), SCORBIT + LAN/Wi-Fi online updates, PPS partnership, About-Pedretti (founded 1976, "Northern Italy").
- **Maker product pages** (first-party) — `https://www.pinballremakes.com/prodotto/acconto-preordine-tales-of-the-arabian-nights-legacy-edition` and `https://www.pinballremakes.com/prodotto/deposit-preorder-europe-only-tales-of-the-arabian-nights-30th-anniversary-edition`. Dense maker-authored feature copy per edition: **21.5" HD LCD display** (both), full RGB LED lightshows (playfield, G.I., bumpers, apron, backbox, speakers, sidebars), Invisible Magic Glass, Infinite Mirror Side Rails, Glowing Stars Ramp LEDs, Playfield Lighted Backpanel, Premium Sound System, GameSync Lighting™ RGB speakers + sidebars, shaker motor, upgraded Lamp and Genie toys, Glitter Gold Lamp, Scorbit, online updates. Legacy: "Night Sky" trims, €9,300 + VAT. 30th: Flyland Design art, "Purple Glitter" trims, certificate + metal plaque, €10,000 + VAT, Backbox GameSync Lighting.
- **PPS deposit pages** (licensor + named release partner, so first-party-adjacent) — `https://www.planetarypinball.com/mm5/merchant.mvc?Product_Code=PPS-TOTAN-AE-DEPOSIT&Screen=PROD` and `...PPS-TOTAN-LE-DEPOSIT...`. Cleanest per-edition bullet lists. AE: "Strictly limited to 399 units worldwide", "MSRP $11,995. 399 units worldwide. No second run planned.", numbered certificate + metal plaque, "Reimagined artwork by Brian Allen / Flyland Designs". LE: "500 units maximum. Initial production run only.", "Original classic artwork style". Both: "XL 21.5\" LCD HD Display", "**Infinite mirror side blades**" (PPS's wording; the maker says "Side Rails"), "Manufactured in Italy by Pedretti Gaming", license boilerplate naming **LNW Gaming, Inc.** as trademark holder.
- **Kineticist news** (journalism) — `https://www.kineticist.com/news/totan-remake-launch` (carries "The original Tales of the Arabian Nights shipped from Williams in 1996, designed by John Popadiuk" — the clean produced-status quote for the 1996 model; also Athyrio partnership dated 2025-12-30) and `https://www.kineticist.com/news/totan-remake-teased`. Kineticist's manufacturer page (`/manufacturers/pedretti-gaming`) confirms Bagnatica and notes production runs through Euro Pinball Corp (Pedretti + Pinball Brothers JV).
- **YouTube** (research-only) — `watch?v=iZ3itu2F8cE` (Pedretti's "First Look with Daniele Acciari") and `watch?v=At-TkFCy27Y`. Auto-captions garble names ("Daniel Alchieri", "speedball"); nothing citable that the text sources don't carry better.
- **ipdb:3824** — resolved, 1304 chars; full credit lines, `MPU: Williams WPC-95`, `Model Number: 50047`, Notable Features, `Toys: Lamp on top of spinning posts. Genie bash toy.`

## Traps

- **LCD, not DMD.** The press release's "New DMD display animations" describes animation content; both maker product pages and PPS say **21.5" HD LCD**. `display_type: lcd` for both remakes, cited to the product page.
- **Three MSRPs in the wild**: release text $10,999/$11,999; Pinball News's own summary paragraph $10,995/$11,995; PPS $10,995/$11,995. Price is not a catalog field, so nothing to assert — but don't quote the PN summary thinking it's the release.
- **Legacy's 500 is soft.** "Initial production limited to 500 units in 2026" / "Initial production run only." — a first-run size, not a total cap. Only the 30th's 399 ("No second run planned") is asserted as `production_quantity`.
- **1996 `production_status` rests on Kineticist's "shipped from Williams" line**, not on the `ipdb:3824` row. The row also indexes first-party Williams documents this patch did not use — an Operations Manual (May 1996), an Operators Handbook, a parts list, Service Bulletin #91 and both flyer sides.
- **The location conflict is real but settled by weight of evidence** (pending user ruling — see Decisions): catalog says `italy/pc/podenzano`; maker footer, REA BG 445013, dateline, Facebook, and Kineticist all say Bagnatica (BG). The Podenzano claim survives only on third-party dealer copy, possibly describing the parent Pedretti Group. `italy/bg/bagnatica` already exists in the location tree (id 391).

## Decisions (all user-ruled 2026-08-11)

- **Location correction** — assert `location: italy/bg/bagnatica` on `corporate-entity.pedretti-gaming`, superseding the seed's Podenzano, cited to the maker's site.
- **Lineage** — both editions `remake_of` → `tales-of-the-arabian-nights`; 30th Anniversary additionally `variant_of` → Legacy. Precedent: the seed's own Pedretti Funhouse remakes (`funhouse-remake-limited-edition` is `variant_of` `funhouse-remake-collectors-edition`, both `remake_of` `funhouse`) — the pricier, strictly-limited edition points at the cheaper one.
- **GameSync Lighting™** — a single brand leaf `gamesync-lighting` under `interactive-lighting` (the JJP `aura-lighting` precedent), locations recorded in the note. Not the 0220 Expression DAG.
- **Invisible Magic Glass** — new brand child `invisible-magic-glass` under `anti-reflection-playfield-glass`; possibly the same product as 0223's `magic-glass`, kept separate rather than risk a wrong conflation (mergeable later).
- **Remake credit rule applied**: Popadiuk (design), Rhine + Morris (animation), Zabriskie (music, sound) carry to both remakes cited to ipdb:3824. **McMahon (art) carries only to Legacy** — the 30th's art package is new (Brian Allen, who exists as `person.brian-allen` from 0223). Mechanics and software do not carry.

## Feature mapping (remakes, both editions unless noted)

Existing vocab, attach directly: `mirror-blades` (PPS "Infinite mirror side blades"), `shaker-motors`, `cabinet-armor` (Night Sky / Purple Glitter metal armor trims — per-edition brand names in notes), `bash-toys` (Genie — classification via ipdb Toys line + product page "upgraded Lamp and Genie toys"), `static-toys` (Lamp on spinning posts / Glitter Gold Lamp centerpiece). Proposals pending user: **`gamesync-lighting`** as a single brand leaf under `interactive-lighting` (the JJP `aura-lighting` precedent, not the heavier 0220 Expression DAG — locations recorded in the note), **`invisible-magic-glass`** as a new brand child of `anti-reflection-playfield-glass` (possibly the same product as 0223's `magic-glass`; kept separate rather than risk a wrong conflation — mergeable later), and whether to create a generic **lighted backpanel** node for "fully integrated illuminated playfield back panel".

For the 1996 original: `game_format: pinball` (ipdb Notable Features line, as 0223 did), `production_status: produced` (Kineticist), `bash-toys` + `static-toys` (ipdb Toys line).

## Not asserted (and why)

- **Legacy `production_quantity`** — the 500 is a first-run size, explicitly "Initial production run only", not a cap.
- **`system` on the remakes** — FAST Pinball is the electronics vendor, but no source names a platform product, no FAST system entity exists, and the seed's Pedretti Funhouse remakes carry no system either.
- **Scorbit / Wi-Fi connectivity as features** — service integrations, not modeled; Bon Jovi (0224, also Scorbit-equipped) asserted none.
- **Premium Sound System** — marketing phrase with no generic vocab target.
- **`month` on the remakes** — announced June 2026 but not released; CV remake (0223) precedent is no month for announced machines.
- **Athyrio software credit** — a company, not a person; catalog credits are persons. Sam Zehr is Athyrio's principal per Kineticist, but no source credits him personally with this game's software.
- **MSRP / pricing / warranties** — not catalog fields.
- **RGB-location enumeration** (playfield/G.I./bumpers/apron/backbox) — folded into the gamesync-lighting note rather than per-location vocab.

## Sought and not found

- **Pedretti PDFs for TOTAN** — the maker's Downloads page (re-fetched 2026-08-11) still lists only Funhouse/Whirlwind documents; a TOTAN operations manual will likely appear when machines ship. Re-check at ship time.
- **Wayback for `pedrettigaming.com`** — CDX empty for the entire domain.
- **A PPS Williams game-gallery page for TOTAN** (the cirqus `rules.html` twin) — 404 at every guessed path; the gallery has no TOTAN entry.
- **Any statement of the remake's own design/engineering team** — no source names one.

## Future unique features (for the coming UniqueFeature entity)

- 1996: the outlane "spikes" rings — "The top of each flipper inlane has a circle of metal 'spikes' that can rise up... to temporarily encircle the ball and stop it from exiting the outlane" (ipdb:3824). Also the Genie bash toy and the Lamp-on-spinning-posts as identities.
- Remakes: Glitter Gold Lamp centerpiece, Glowing Stars Ramp LEDs, Night Sky trims (Legacy), Purple Glitter trims + numbered certificate + metal plaque (30th), Magic Lamp RGB + Genie internal RGB.

## The 0228 documents supplement (2026-08-12)

The document-cites pilot. Generator: [gen_documents.py](gen_documents.py).

**Documents surveyed** (one metadata search names all nine unacquired IPDB-indexed TOTAN documents):

- **Declared + cited (0228)**: Operations Manual (16-50047-101 FINAL MAY 1996, 160 sheets) and the two-sided flyer — both cached from **archive.org copies** (`Williams_Tales_of_the_Arabian_Nights_Operations_Manual`, `arabian-nights-pinball-us-flier`), identity verified against the covers and PPS's Online Game Manuals index row. Both scans; OCR'd. IPDB's copies ride as `catalog` links.
- **Cached, not declared**: Operators Handbook (May 1996, 16-10252, archive.org `arcademanual_Tales_Of_The_Arabian_Nights_HAN`) — 16 sheets of service menus and FCC boilerplate, no game fact a claim needs. Declaring waits for a claim that cites it.
- **IPDB-only, not acquired**: Service Bulletin #91 (wire dressing), WPC-95 Schematic Manual (platform doc — document-to-System attachment is out of scope), Parts List (.txt), instruction card scan. None evidences a missing claim; hand-import when one does.
- **Third-party rulesheet** (Lehan v1.2) — stays `web` per the design, uncited.

**What the documents newly evidence**: IPDB's Notable Features line names **no ramps**, so 0226 couldn't assert them. 0228 adds `ramps` (flyer back: "Fly on the Magic Carpet Ramps around Ancient Baghdad") and `diverter-ramps` (manual printed page 1-43: ramp diverter coil #21 + adjustment A2.19). Both quotes are author transcriptions from rendered sheets (SKIP-PDF).

**Resolved non-conflict**: the flyer's "3-ball Multi-Ball" describes Genie Multiball's start; IPDB's line reads "2- 3- and 4-ball multiball", so the seeded `4-ball-multiball` (the maximum) stands.

**Cabinet ruling (user, 2026-08-12)**: `cabinet: floor` IS asserted on standard machines when evidence supports it — 0228 classifies the 1996 model from the flyer's specifications line (76" height, 29" width, 250 lbs uncrated), the campaign's first `cabinet` assertion.

**Library hygiene done in pinexplore**: archive.org URLs attached to the seeded documents (merge), flyer front/back image documents folded into one flyer work, `citation_ref` + publisher set on all three — which is exactly the join the quote gates now resolve document refs through.

## Gate-run history

- **2026-08-11 `verify-quote-verbatim`**: 0 failed on the first emit (all 0226 quotes lifted from `web_cache.py quote` output / `make show-source --check`).
- **2026-08-11 `verify-quote-support 0226`** (190k tokens): 1 warning — `numbered-plaques` on the 30th Anniversary is "a collector's item, not a gameplay feature". **Kept**: presentation features are vocabulary by the 0218 charter, and `numbered-plaques` was created in 0220 and attached to Stern's MTMTE LE with the same collector meaning (same warning class as 0221's `cabinet-armor`).
- **2026-08-12 `verify-quote-verbatim`** (0228): 0 failed; both document-ref cites report SKIP-PDF, resolved through the library — the first document-ref gate run.
- **2026-08-12 `verify-quote-support 0228`** (0 tokens): both claims skipped as PDF-source author-checked; 0 warnings.
