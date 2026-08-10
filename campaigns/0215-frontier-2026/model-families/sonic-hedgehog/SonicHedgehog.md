# Sonic the Hedgehog — Jersey Jack (2026)

## Status

- **DONE (2026-08-10): `patches/0221-sonic-hedgehog.yaml`, snapshot-validated, unshipped.** 35 entries, 29 changesets, 53 cites, all resolving to the Jersey Jack root. Gates: structural + lint clean; `verify-quote-verbatim` 125/0 (32 SKIP-PDF, author-checked off renders); `verify-quote-support` triaged (below). Applied on the 0214 snapshot with 0215–0220; fields, credits, features and variant links all verified through the foundation.
- Evidence is unusually strong: JJP publishes per-edition flyers, an all-models feature matrix, a manual, a rules flowchart, product pages with per-edition feature lists, and reprinted press coverage — all on citable hosts.

## Support-check triage (2026-08-10)

- `production_status = produced` warned on the availability quote alone; fixed by adding the product pages' delivery FAQ ("production schedules, inventory availability... If your game is in stock") plus a note. Second run accepted it.
- `variant_of` warned once (first run): the cite names three co-equal editions and the ladder is a convention argument in the note — the known note-explained false-positive class. User approved SE-as-base; kept.
- AE `cabinet-armor` "cosmetic, not gameplay" — misreads the taxonomy; presentation features are vocabulary by the 0218 charter, and 0220 attached `cabinet-armor` the same way. Warned in runs 2, 3 and 5 — **with and without a classification note** (one was added after run 3; runs 4–5 had it), so this is a taxonomy-level disagreement notes don't fix. Kept.
- Occasional warnings on classification-by-absence: run 5 flagged AE's `static-toys` ("the note is the author's inference — no source states the sculptures don't move"), run 4 flagged AE's equipment features; their CE/SE twins passed every time. Run-to-run sampling variance over the same convention 0220 established. Kept.
- The verifier's note-reading upgrade landed mid-campaign: run 1 flagged `variant_of` (note ignored); every later run passed it on the same note.
- Two AE claims failed with a structured-output schema error ("'supported' is a required property") identically in runs 1–3 — a deterministic verifier bug, **fixed upstream 2026-08-10**: run 5 judged all 26 judgeable claims with zero errors.

## Models

| slug                                    | edition            | price   | 0215 gave it                                             |
| --------------------------------------- | ------------------ | ------- | -------------------------------------------------------- |
| `sonic-the-hedgehog-collectors-edition` | Collector's ($15k) | $15,000 | name, slug, year 2026, title, corporate entity, 3 themes |
| `sonic-the-hedgehog-special-edition`    | Special ($12k)     | $12,000 | same                                                     |
| `sonic-the-hedgehog-arcade-edition`     | Arcade ($9,999)    | $9,999  | same                                                     |

No older siblings — all three are 2026. Catalog baseline (surveyed 2026-08-10, dev DB at 0220): **everything else is empty** — no month, game_format, cabinet, display, system, production_status, player_count, variant_of, credits, features, descriptions, production_quantity, tag.

## Edition structure — PROPOSAL (user decision needed)

The catalog's seeded JJP convention links each family's other editions `variant_of` the mid-tier base: Harry Potter (2025) is the exact analogue — `harry-potter-arcade-edition` and `harry-potter-collectors-edition` are both `variant_of` `harry-potter-wizard-edition`. Elton John CE → Platinum, Toy Story 4 CE → LE, Avatar CE → LE follow the same shape.

**Proposal: Special Edition is the base; Collector's Edition and Arcade Edition are `variant_of` it.** JJP's own framing supports the three-tier ladder (collection-page FAQ: CE "built to order with premium finishes", SE "fully loaded ... without going full CE", AE "same layout, the same shots, and the same speed at an entry-level price"). Under the variant rule (2026-08-07), credits and shared-design hardware then carry to CE and AE citing the shared evidence with a carry note.

## Evidence inventory (all cached in pinexplore web cache)

First-party, all on hosts resolving to the Jersey Jack root (`jerseyjackpinball.com` + `marketing.` subdomain — verified against `citation_roots`; no roots work needed for this family):

- **All-models flyer** `https://marketing.jerseyjackpinball.com/distributors/Sonic/Flyers/73-100024-12-04%20-%20REV.%20A%20-%20SONIC%20FLYER,%20ALL%20MODELS.pdf` — **the densest source.** Page 2 (of 2): `Game Designer: Steve Ritchie`, `GAME FEATURES - ALL MODELS` list (27" LCD, Wi-Fi, Bluetooth audio, 8-inch subwoofer, RGB LED action button, player camera, stainless ramps/guides, 9-song soundtrack, polycarbonate upper playfield, 4 flippers, 9 stand-ups, 2 spring targets, Eggman bash toy, magnetic accelerator loop, Battle Zone! magnet, micro-LED rings, Chaos Emerald inserts, Sonic/Amy/Eggman sculpts, 1 spinner, 2 up-posts, inline 3-bank drop target lock, upper-playfield entry drop target, 6-ball multiball, official-cast callouts, Bash Dash captive ball lock, Spin Dash accelerator ramp feature) plus three per-edition columns. Part number 73-100024-12-04 Rev. A.
- **Per-edition flyers** (same directory, part numbers -01 SE, -02 CE, -03 AE) — one sheet of art + one of text each; per-edition exclusives without the column-attribution problem, since the whole flyer is about one edition.
- **Manual** `https://marketing.jerseyjackpinball.com/sonic/Sonic_Manual_10_July_2026.pdf` (cached 2026-07-10) — printed folio V (PDF sheet 5): `"Hall of Fame game designer Steve Ritchie is known for his fast-flowing games. He and his design team have created Sonic pinball."` Folio VII (sheet 7): specification table — 325 lbs with topper, 87 × 29 × 57 in., 120/230 VAC — the text layer flattens the table, so render the sheet and transcribe.
- **Rules flowchart** `https://marketing.jerseyjackpinball.com/distributors/Sonic/Rule%20Flowchart/Sonic%20Rules%20Flowchart_vA.pdf` — gameplay/mode structure; description material.
- **Collection page** `https://jerseyjackpinball.com/collections/sonic-the-hedgehog-pinball-game` — HTML (quote-gated!): designer FAQ (`The game was designed by Steve Ritchie`), three-edition comparison with prices, the 7 zones by name (Green Hill, Chemical Plant, Seaside Hill, Sky Sanctuary, Speed Highway, City Escape, Rooftop Run), 9-song soundtrack with Slash guitar solos, 5,000+ voice callouts (Roger Craig Smith as Sonic), 27" HD backglass display, Wi-Fi + Bluetooth, per-edition topper/cabinet prose, availability ("available for purchase directly from Jersey Jack Pinball").
- **Product pages** `https://jerseyjackpinball.com/products/sonic-collectors-edition`, `.../sonic-special-edition`, `.../sonic-arcade-edition` — HTML per-edition feature lists (the compare-flyer columns as plain bullet text, one page per edition — the cleanest per-edition cites available), prices and deposits, weight/dimensions FAQ.
- **Compare flyer** `https://jerseyjackpinball.com/cdn/shop/files/SONIC_Compare_Flyer.pdf` — **cached under the maker's own domain**, which resolves to the JJP root; the previously cached copy of the same file on `cdn.shopify.com` is research-only. Shopify serves `/cdn/shop/files/` on the store domain, so the maker-domain URL is real and stable enough to cite.
- **Blog reprint (Polygon)** `https://jerseyjackpinball.com/blogs/news/sonic-the-hedgehog-gets-his-first-offical-pinball-machine-and-its-designed-by-a-legend` — journalism reprinted on JJP's own blog: revealed on the franchise's 35th anniversary, "launching on June 23" (2026) — the month evidence; Ritchie interview quotes; "more than 6,000 spoken lines" (see traps).
- **Blog reprint** `https://jerseyjackpinball.com/blogs/news/pinball-pivots-to-millennial-nostalgia-and-gives-sonic-a-10-000-machine-of-his-own` — second reprinted article; pricing/editions.
- **Official trailer** `https://www.youtube.com/watch?v=pubrqKQZ3z8` — first-party YouTube, transcript cached.

- **Software changelog** `https://marketing.jerseyjackpinball.com/sonic/sonic_changelog.txt` — cached as plain text (2026-08-10, after pinexplore added the text handler), quotable and citable. Versions 00.90P (June 22, 2026) → 00.929 (Aug 4, 2026) — corroborates the June launch and shows active software support. `/sonic/` also hosts the game-code ISOs (not fetched — software, not documents).

Research-only (not citable):

- Pinside pages (3, cached) — unusable per campaign rule: manufacturer PDFs exist.
- `https://marketing.jerseyjackpinball.com/distributors/Sonic/` also has `AE/CE/SE Photography/`, `Cabinets/`, `Playfield Top/`, `Logo/` directories — images only, not fetched.

## Traps

- ~~`marketing.jerseyjackpinball.com` fails Python TLS verification~~ **fixed in pinexplore 2026-08-10** (along with a plain-text handler and a 134MB PDF cap). The flowchart and four flyers were first imported via `curl` + `web_import.py` during the outage, then refetched as real fetches once the fix landed — the cache rows are now ordinary fetches, not imports.
- **Voice-callout count conflicts**: JJP's own site says "5,000+ voice callouts", the reprinted Polygon article says "more than 6,000 spoken lines". Prefer the maker's own number if the field is asserted at all; don't cite the article for it.
- **Column attribution on the all-models flyer**: the per-edition columns extract as sequential bullet groups and look trustworthy, but per campaign rule, verify column membership by rendering the sheet — or cite the per-edition flyer / per-edition product page instead, which have no columns to splice.
- **Collection-page text duplicates every caption** (carousel markup) — quote from one instance, fine for verbatim gate, just don't be surprised by the doubling.
- **Product pages have a `+ Expand` accordion** — the cached text may not include collapsed content; if a needed span is missing, refetch with `--render`.
- **"RadCal", "Invisiglass", "Hotrails"** are JJP brand names — vocabulary work must follow the generic-only rule (branded child of generic, InvisiGlass pattern is literally already the worked example in the charter). `Hotrails (JJP Exclusive)` appears on the collection page playfield list but not in the flyer's all-models list — check what it actually is before classifying.
- The SE flyer says `Sculpted Micro-LED Rings` where AE has `Micro-LED Rings` and CE has `Gold Micro-LED Rings` — watch the wording when asserting per-edition finishes.

## Not asserted (and why)

- **month** — the reveal/launch date (June 23, 2026) dates the launch, not manufacture; same reasoning as the Transformers family. The user can overrule.
- **player_count** — no primary source states it (manual's "player" hits are the settings menu; Pinside's 4 is unusable here).
- **system + technology_generation** — no document names JJP's platform; the manual mentions SSDs but never a named system. Toy Story 4 carries `jersey-jack` as system from an earlier ingest; asserting it for Sonic needs evidence that doesn't exist yet.
- **Wider team credits** — the Pinside roster names ~20 people (Mastoras, Lachcik, Grupp, Brown, Young, Llereza, Colbert, Holstein, …) but no primary document or journalism names anyone except Ritchie and Slash. Pinside is barred for models with manufacturer PDFs. Re-check when JJP publishes a credits page or the game's attract-mode credits get documented.
- **descriptions** — a follow-up patch's job, per the campaign's inline-cite rules.
- **production_quantity / tags** — no quantity or limit published; CE is "built to order", not stated as limited.
- **Vocab candidates skipped**: External Volume Control Panel (operator convenience; borderline), RGB LED Action Button (no generic action-button node; `lockdown-bar-buttons` would over-read the evidence, which never states the location), 9 Licensed Song Soundtrack, Stainless Steel Precision Ball Guides, RadCal™/direct-print artwork tech, Hotrails (what it actually is is unestablished), Micro-LED Rings (Sonic-identity lighting; see below).

## Future unique features (UniqueFeature backfill worklist)

To be filled during feature classification — candidates already visible: Dr. Eggman animatronic bash toy, Amy Rose hammer sculpt, Bash Dash captive ball lock, Spin Dash action-button accelerator feature, Sonic vs. Eggman mechanical battle topper (CE), Superconducting Battle Zone! magnet, golden ring shooter knob.

## Decisions

- **(user, 2026-08-10): Special Edition is the base; Collector's Edition and Arcade Edition are `variant_of` it** — per Harry Potter precedent. The variant rule carries base credits and shared-design hardware to CE and AE, cited to the shared evidence with a carry note.
