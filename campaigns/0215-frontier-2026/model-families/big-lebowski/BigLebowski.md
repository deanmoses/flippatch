# The Big Lebowski — 0271-0274

## Status

**Authored + snapshot-validated 2026-08-19, uncommitted.** Four patches, **0271-0274**, claimed in order from 0271 (next free after 0270). One model created, one Title merged, two siblings filled in. `make validate` clean, `make verify-quote-verbatim` 33+3+26 verified / 0 failed, `make validate-in-db` 7 records / 0 errors / 0 warnings. `make verify-quote-support` is **owed for all four** — every run dies on the first call with a 400, credit balance too low (the same wall 0242 hit).

**0272** moves the maker's corporate entity to Herkenbosch — see Corporate entity below. **0273 + 0274** complete the family: all three models gathered under one Title, the two older siblings filled in, and the gaps 0271 left on the Jesus Edition closed. Both authored 2026-08-19 on user direction after 0271 shipped with the siblings untouched.

Not on 0215's original list; added 2026-08-19 after a Pinside new-games sweep found two 2026 machines missing from the catalog. The other one — Stern's Pokémon Home Edition — is **held**, see [../pokemon/Pokemon.md](../pokemon/Pokemon.md) → Home Edition.

## Models

- The Big Lebowski (Jesus Edition) (Dutch Pinball • 2026) — `the-big-lebowski-jesus-edition`, **created by this patch**. Announced 2026-08-10, 300 units, first deliveries September 2026.
- The Big Lebowski (Dutch Pinball • 2015) — `the-big-lebowski-pinball-first-model`, ipdb 6320, opdb G5WBr-MvB3E. 95 built.
- The Big Lebowski Pinball (Second Model) (Dutch Pinball • 2019) — `the-big-lebowski-pinball-second-model`, ipdb 6833. No IPDB-recorded quantity: "No specific/limited quantity is expected to be made, per the manufacturer."

All three sit under one Title, `the-big-lebowski`, as of 0273.

## Catalog baseline (surveyed 2026-08-19)

The Jesus Edition did not exist. The two siblings' state, which is what the variant carry rests on:

| field                 | first model (2015)             | second model (2019)            |
| --------------------- | ------------------------------ | ------------------------------ |
| production year/month | 2015/5                         | 2019/8                         |
| production_status     | —                              | —                              |
| game_format           | —                              | —                              |
| tech generation       | solid-state                    | solid-state                    |
| display_type          | lcd                            | —                              |
| system                | —                              | —                              |
| player_count          | 4                              | 4                              |
| production_quantity   | 95                             | —                              |
| cabinet               | —                              | —                              |
| credits               | 12                             | 12 (identical set)             |
| features              | 12                             | 12 (identical set, with counts) |
| themes                | bowling, licensed, movies, sports | bowling, licensed, sports   |

**0271 asserted nothing on either sibling — that was a mistake**, corrected by 0273 on user direction. The campaign's "complete the family's siblings" rule is not optional, and it earns its keep here: the manual and the two IPDB rows describe all three machines, so the sibling fill cost one extra evidence pass and no new research.

**What 0273 added.** Both siblings: `production_status: produced`, `game_format: pinball`, `cabinet: floor`, and seven feature attachments (`bash-toys`, `static-toys`, `ramps`, `ramp-diverters`, `speech`, `targets`, `balls` ×6) plus `led-general-illumination`. The second model additionally: `display_type: lcd`, the `movies` theme, and its move to the shared Title. The Jesus Edition additionally: `cabinet: floor`, `ramps`, `ramp-diverters`, `static-toys`, `targets`, `balls` ×6. All three now carry the same 21-feature core, and the only feature any of them holds alone is the Jesus Edition's anti-reflective glass and art blades.

**Do not re-assert** on either sibling: `production_year`/`production_month`, `player_count`, `technology_generation`, `production_quantity` (first model), `manufacturer_model_identifier`, `abbreviation` (TBL2016 / TBL2019 — both already resolve from IPDB), all 12 credits, and the twelve features they arrived with.

## User decisions

- **Create the Jesus Edition, hold the Pokémon Home Edition** (user, 2026-08-19).
- **`variant_of`, not a standalone model** (user, 2026-08-19): "it looks like all the features are cosmetic, so variant_of". Every difference the maker lists is artwork, trim, glass, blades, apron, decals, plus software content — no layout or mech change.
- **Base = the 2019 second model**, the machine in production when the Jesus Edition was revealed, not the 2015 first run. Session call, stated to the user.
- **One Title for all three** (user, 2026-08-19): "All three should be in a single title: The Big Lebowski." 0273 moves the second model onto `the-big-lebowski` and 0274 deletes the title it orphans. The second model keeps its own Model row — the user's reading of IPDB is that the Second Model is a deliberate, distinct machine ("they're very intentional it's an updated model"), even though Pinside collapses the family to two entries.
- **Fill in the whole family** (user, 2026-08-19), reversing 0271's decision to touch only the new model.
- **The maker's location is Herkenbosch, not Reuver** (user, 2026-08-19), confirmed from multiple sources with `https://dutchpinball.com/contact` named as the cite.
- **A patch supports the new state, not the old one** (user, 2026-08-19). 0272's changeset note originally narrated the move and named the superseded address; the quote already carries the new address, and a note explaining what a value used to be is not evidence for what it is. Deleted. Likewise the **location create carries no cite at all** — citing a machine's press coverage to establish that a town exists is not what a citation is for.

## Evidence inventory (all cached in the pinexplore web cache)

- **Maker product page** — `https://dutchpinball.com/games/the-big-lebowski-jesus-edition`. The densest source and the one that describes _this_ model rather than the family: the Introduction paragraphs plus a Key Features list that merges the shared TBL features ("3 flippers", "Multi-level playfield", "Bash Toys (Rug and Dude's Car)", "Up to 5-ball multiball", "Brunswick™ Bowling Alley with 10 controlled pins", "Deep rule sheet", "101 LED lit inserts", "More than 250 quotes and clips from the movie") with the Jesus-exclusive ones ("Premium anti-reflective playfield glass", "Custom inner art blades", "New custom voice callouts", "Premium DP Crystal™ Cabinet Decals", "Illuminated Starry Lit Jesus Edition apron", "Individually numbered Certificate of Authenticity"). Carries "Production is strictly limited to just 300 individually numbered machines worldwide" and an "Available now" badge that is an ordering badge, not a production statement.
- **Maker news post, 2026-08-10** — `https://dutchpinball.com/news/meet-the-big-lebowski-jesus-edition`. The reveal in Dutch Pinball's own voice: the name and the Universal Pictures licence in one sentence, "Limited to just 300 individually numbered machines worldwide", "Reservations are now open", and the exclusive-features bullet list (whose "New illuminated bowling alley launch button" wording the product page does **not** carry — the page says "Illuminated Jesus bowling ball launch button"). Footer gives first-party corporate identity: Dutch Pinball B.V., Veldweg 26, 6075 NL Herkenbosch, KvK 59188146.
- **Pinball News reveal, 2026-08-10** — `https://www.pinballnews.com/site/2026/08/10/the-big-lebowski-jesus-edition-revealed`. Journalism plus **the manufacturer's press release reprinted verbatim**, which is where the two facts the maker's own pages omit live: "First deliveries are scheduled for September 2026." and the "pinball machines" phrasing that establishes `game_format`. Also "The Jesus Edition will be built, like the original, at the Dutch Pinball factory in Herkenbosch in the Netherlands." and the €15,995 / $14,995 pricing.
- **Maker contact page** — `https://dutchpinball.com/contact`. A **Headquarters** block giving the company's address in its own words; the sole cite for the move in 0272. The same address repeats in every page's footer, so name the Headquarters block in the locator.
- **`ipdb:6320`** — the first model's row, and the family's densest single source. Its Notable Features and Toys blocks are what most of 0273's feature work rests on ("Carpet bash toy unrolls when repeatedly hit.", "Parking garage building on upper mini-playfield with car bash toy.", "White Russian mixed drink in glass. Bowling pin in upper left playfield.", "Bowling ball return on left ramp.", "Ramp diverter.", "Speech.", "On the elevated mini-playfield are a garage building, two targets, a looping lane, and a scoop.", "Playfield - all lamps are LED. Cabinet - all lamps are LED."). Its Notes carry the production facts ("The manufacturer made a quantity of 95 of this First Model.", "The manufacturer advised us that the first shipment of this game occurred April 2016."), the DP-069 model number, the Achiever Edition plaque, and the $9,995 launch price.
- **`ipdb:6833`** — the second model's row. The variant-carry evidence for player count, technology generation, all 12 credits, and the counted hardware ("Flippers (3), Pop bumpers (2), Slingshots (2), Kick-out hole (1), Spinning target (1), Captive ball (1), Scoop (1), Elevated mini-playfield. Ramp diverter. Left outlane kickback. Up to 5-ball multiball. Speech."). Its Notes are the Title merge's evidence — "This is a revised edition of their original model" and the manufacturer's own revision list, which opens "Cosmetically nothing changed" — and they rule out a quantity: "No specific/limited quantity is expected to be made, per the manufacturer."
- **TBL Operations Manual v1.12 (2021)** — `https://cms.dutchpinball.com/uploads/Dutch_Pinball_2021_The_Big_Lebowski_Pinball_Manual_1_12_f7ce352aaa.pdf`, 6.7 MB, real text layer. The family's workhorse after 0273, and it covers all three machines. Printed page 12 = PDF 12, GAME SETUP INSTRUCTION, carries the box contents ("4 Pinball legs [...] 4 Pinball Leg levelers with tightening nuts [...] 8 Leg bolts", "6 Steel pinballs (5 for the playfield, and 1 for the Bowling Alley)", "The 'Rug' (rolled up)") and the safety line "A pinball machine is an extremely heavy machine..."; printed page 17 = PDF 17 STEP 12 raises the backbox; printed page 55 = PDF 55, DISPLAY, is the LCD evidence. All three sheets rendered and read. Also confirms max 4 players in MISCELLANEOUS.
- **TBL Leaflet (2016)** — `https://cms.dutchpinball.com/uploads/TBL_Leaflet_2016_4880394784.pdf`. Cached, not cited: its feature list is the same one the Jesus Edition page states in its own right, and the page is the better source for a claim about the Jesus Edition.
- **The old TBL microsite** — `http://www.thebiglebowskipinball.com/game.php` and `/faq`, read through Wayback `id_` snapshots (2016-10-07 and 2016-10-14). Fetched in the hunt for dimensions; neither has any. The FAQ is quotable if a later session wants it ("Yes, The Big Lebowski™ Pinball is a real pinball machine, no video game.", "The Big Lebowski™ Pinball will be manufactured at our facility located in The Netherlands.", the worldwide-exclusive Universal licence) — but the domain is not a citation root, so using it costs a root plus the `archive:` mechanics. The manual said the same things without either.
- **Also cached, uncited**: the maker's TBL base product page, support page, news index and homepage; `TBL_Score_Cards`, `TBL_Pinball_Rules_Flowchart` and the hi-res manual were seen on the base page but not fetched.

`dutchpinball.com` and `cms.dutchpinball.com` both already resolve to the **Dutch Pinball** citation root; no `sources:` block was needed.

## Traps

**The maker's own pages omit the ship date.** Both Dutch Pinball pages say reservations are open and neither dates delivery. "First deliveries are scheduled for September 2026." exists only in the press release, which Dutch Pinball did not post itself — it survives in Pinball News's verbatim reprint. `production_status` and `production_year` both rest on it, cited to PN with the locator drawing the line (RULEBOOK → Operating the quote gates).

**"Available now" on the product page is not `produced`.** It is the ordering badge — the base TBL page carries "Sold out" in the same slot. With first deliveries scheduled after the authoring date, the status is `announced` ("officially announced but not yet shipped", DomainModel).

**The two Dutch Pinball page URLs canonicalise without `www`.** `web_fetch.py https://www.dutchpinball.com/` caches as `https://dutchpinball.com/`; cite the bare-host form or the gate reports NO-SOURCE.

**The bullet lists differ between the maker's two pages.** Six of the Jesus-exclusive bullets are worded differently on the product page than in the news post, and one ("New illuminated bowling alley launch button") appears only in the news post. Check the span against the page you actually name in `ref:`.

**The old TBL microsite domain redirects into the cache's alias table.** `thebiglebowskipinball.com` is live but 301s to `dutchpinball.com`, so `web_fetch.py` on it stores the DP homepage with the old URL as an alias — the exact shape of the RULEBOOK's "never fetch the dead original URL" trap. The 2013-2016 microsite (`/game`, `/faq`, `/order`) survives only in Wayback and was read there with `id_`; nothing on it turned out to be worth citing, so no `archive:` cite was written and the alias was left in place. If a later session does cite it, delete that cache row first.

## Not asserted (and why)

- **`cabinet` was deferred by 0271 and asserted by 0273.** No dimensions or weight exist anywhere — the 2021 manual has no specifications table (searched cm, kg, lbs, inch, Height, Width, Depth — no hits), nor does the leaflet, the microsite or IPDB — so the 0228 classify-from-dimensions route has nothing to stand on. The manual's setup pages do the job instead: four legs with levelers and a backbox raised at the rear is a floor cabinet, and the note says so.
- **`production_month`** — the announcement is not a manufacture date (RULEBOOK ruling, 2026-08-13), and September 2026 is a scheduled delivery, not evidence of when assembly happened.
- **`system`** — TBL runs a PC-based platform (the manual describes a 2021 CPU board change and Mini-ITX compatibility) but neither TBL sibling has a `system` and nothing names the platform. Creating one would need a System entity with a manufacturer FK; deferred.
- **`101 LED lit inserts`** — no generic insert node exists in the vocabulary; `rgb-playfield-inserts` would be wrong (nothing says RGB) and `led-general-illumination` is GI, not inserts. Would need an `led-playfield-inserts` node; not created, since the campaign's vocabulary rule wants a deliberate generic addition rather than a drive-by.
- **`5-ball-multiball`** — the multiball subtree has 2-, 3-, 4- and 6-ball children but no 5-ball, and "Up to 5-ball multiball" is the maker's and IPDB's wording for both siblings. Attached plain `multiball` instead; the node is worth adding when someone opens the multiball vocabulary.
- **`diverter-ramps` — the wrong node.** IPDB's "Ramp diverter" is a diverter sitting at a ramp junction, which is `ramp-diverters` (parent `diverters`), not `diverter-ramps` (a ramp with one entrance and several exits, parent `ramps`). 0273 attaches `ramp-diverters` plus plain `ramps` for the bowling ball return, on all three models.
- **`sports` theme** — `bowling` is a child of `sports`, so only the leaf is attached on the Jesus Edition; the two siblings redundantly carry the parent from the seed and 0273 left that alone.
- **A "looping lane"** on the mini playfield (ipdb:6320) is not `orbits` — an orbit circles the main playfield. No generic loop node exists; left unattached.
- **Apparatenfabriek ARA B.V.**, credited by ipdb:6320 with additional mechanical engineering and (with Guus Fingskes) the electronic engineering, is a company. `credit:` needs a Person, so it is unrepresented.
- **Video clips** — "More than 250 quotes and clips from the movie" backs `speech`; the clips themselves are licensed content, not represented as a feature (the 0237 precedent).
- **The Certificate of Authenticity, the rug, the cabinet decals, the apron, the bowling-alley front sculpt, the launch button** — collector packaging and cosmetics; the numbered certificate is not a `numbered-plaques` match (different object), and nothing else maps to an existing generic node.

## Sought and not found (2026-08-19)

- **A Jesus Edition manual, flyer or spec sheet.** The Jesus Edition product page's download block carries software only (TBL v1.15 and four older builds) — no PDF of its own. The base page's PDFs are all pre-2026.
- **Dimensions or weight** for any TBL model, in any source (see above).
- **Any Jesus-Edition-specific credit.** No source names a person for the new art package; Barry Driessen is quoted in the press release as founder, not as a credit. All 12 credits carry from the base.

## Future unique features (UniqueFeature backfill worklist)

Brunswick™ bowling alley with 10 controlled pins (shared with both siblings), Jesus-themed bowling alley front sculpt, illuminated bowling ball launch button, Illuminated Starry Jesus Edition apron, Premium DP Crystal™ cabinet decals, individually numbered Certificate of Authenticity, the included Big Lebowski rug, the unrevealed "one final surprise".

## Corporate entity — the move to Herkenbosch (0272)

`corporate-entity.dutch-pinball` was located at `netherlands/reuver`, the address IPDB recorded for the company's 2014 incarnation. The maker's own contact page publishes a **Headquarters** block reading "Dutch Pinball B.V. / Veldweg 26 / 6075 NL Herkenbosch / The Netherlands", and the 2026 press release places the factory there too ("The Jesus Edition will be built, like the original, at the Dutch Pinball factory in Herkenbosch in the Netherlands"). The user confirmed the move from multiple sources and named `https://dutchpinball.com/contact` as the cite (2026-08-19).

**[patches/0272-dutch-pinball-herkenbosch.yaml](../../../../patches/0272-dutch-pinball-herkenbosch.yaml)** creates `location.netherlands/herkenbosch` and supersedes the Reuver member — the 0024 Bally Wulff pattern: assert the new member, `remove:` the old one in the same entry. Kept as its own patch rather than folded into 0271.

**The location create carries no cite and the corporate-entity entry carries no note** (user, 2026-08-19). A location create is a bare fact of geography — citing the machine's press coverage to establish that a town exists is not what a citation is for. And the entry's quote already names the address, so a note narrating the move and the superseded Reuver address added nothing except a claim about the past; a patch supports the new state.

**No companion retract patch was needed.** The Reuver membership was a single claim (id 9080) held by `flipcommons-catalog` alone — checked in `claims` joined to `claim_identity_parts` before authoring — which is 0272's own attribution, so one `remove:` drops it with nothing lower-priority left to resurface. Had IPDB held a copy, the RULEBOOK's one-retract-per-holding-source rule would have applied.

**The manufacturer's location is derived**, rolled up from its corporate entities in the `manufacturers` view, so fixing the CE fixed `manufacturer.dutch-pinball` too — there is no second claim to write.

**A location create must also set `location_type` — see 0275, which types the five cities every patch create so far has left blank.** Its entries are bare (`location_type: city`, no cite, no note): the value restates what the record is, so it needed a narrow `note-required` exemption in the editorial lint (`SELF_EVIDENT_FIELDS`).

**Why the field is unset in the first place.** This session first recorded the opposite, reading the editor's `LocationChildCreateSchema` (which forbids a client-supplied `location_type`) as meaning the field is not settable. It forbids it because the *server* derives it there; the patch path has no such step, so a patch that omits it leaves the location untyped.

`netherlands/reuver` is now an orphan location with zero corporate entities. Left in place; nothing references it and deleting a location is not this patch's business.

## The first model's date — 2015-05 to 2016-04 (0276)

The catalog resolved `production_year` 2015 / `production_month` 5 (flipcommons-catalog rank 1, OPDB rank 2, IPDB's 2016-04 outranked at 3). IPDB has the manufacturer's word — "The manufacturer advised us that the first shipment of this game occurred April 2016." — heads the row "IPD No. 6320 / April, 2016 / 4 Players", and abbreviates the machine TBL2016; Pinside lists it as 2016 too.

**This needed no retract, and the session's first reading that it did was wrong** (user caught it, 2026-08-19). Provenance.md → Superseding: "A new claim from the same source for the same claim key deactivates the old one." [patches/0276-big-lebowski-first-model-date.yaml](../../../../patches/0276-big-lebowski-first-model-date.yaml) asserts both fields as flipcommons-catalog, which is the actor already holding the winning claim, so the old ones deactivate and the new ones resolve. OPDB's 2015 was never the problem — it sits at rank 2 and loses either way.

The claim stack after the apply shows the mechanism exactly:

| field            | value | actor               | priority | rank |
| ---------------- | ----- | ------------------- | -------- | ---- |
| production_year  | 2016  | flipcommons-catalog | 300      | 1    |
| production_year  | 2015  | opdb                | 200      | 2    |
| production_year  | 2016  | ipdb                | 100      | 3    |
| production_year  | 2015  | flipcommons-catalog | 300      | —    |

A `retract:` would have been actively wrong here: it removes the value and lets the next source surface, which is OPDB's 2015 — the thing being corrected away.


## Follow-ups for whoever reopens the family

- **`system` is unset on all three.** TBL runs a PC-based platform (the manual describes a 2021 CPU board change and Mini-ITX compatibility) but no source names it, and a System create needs a manufacturer FK.
- **No dimensions or weight exist for any TBL model** in the manual, the leaflet, IPDB or the maker's pages. `cabinet: floor` therefore rests on the manual's setup pages (legs, leg levelers, backbox) rather than the 0228 classify-from-dimensions route.
- **`led-general-illumination` is on both siblings but not the Jesus Edition.** The chain that carries it to the second model — 6320's illumination line plus 6833's "Cosmetically nothing changed" — would need a third hop to reach the Jesus Edition, and the Jesus Edition's own page speaks of lit *inserts*, not general illumination. Left off deliberately.
- **`verify-quote-support` still owed for 0271-0276** (API credit exhaustion).

## Gate runs

- **2026-08-19 `make validate`**: two iterations. First failed the schema on `year:` — the model date field is now **`production_year`** and the schema rejects the old name outright; then the editorial lint rejected a 210-char patch description (max 80) and every note containing "currently".
- **2026-08-19 `make verify-quote-verbatim ARGS="0271"`**: 33 verified, 0 failed, 1 SKIP-PDF (the manual's DISPLAY page, read off a render of sheet 55).
- **2026-08-19 apply**: no snapshot reset needed — the dev DB was current through 0269, so 0270 and 0271 ingested straight on. Resolves as intended: 12 credits, 16 features, 3 themes, 1 tag, `variant_of` → 5936 (the second model), 34 cites.
- **2026-08-19 `make validate-in-db`**: 3 records audited across 0270–0271, 0 errors, 0 warnings.
- **2026-08-19 `make verify-quote-support ARGS="0271"`**: **did not run** — 28 claims in scope, died on call 1 with `400 … credit balance is too low`.
- **2026-08-19 0272**: `make validate` clean first pass; `make verify-quote-verbatim ARGS="0272"` 3 verified / 0 failed; ingested on top of 0271 (0270–0271 skipped as already applied); `make validate-in-db` 5 records across 0270–0272, 0 errors, 0 warnings. Resolves as intended — the corporate entity and the manufacturer both read `netherlands/herkenbosch`, with one location member, and Reuver drops to zero.
- **2026-08-19 0273 + 0274**: `make validate` clean after one lint iteration — the editorial lint rejects "No source" in a note (an absence claim the next source falsifies), so the cabinet note was rewritten to say what the manual shows rather than what nothing shows. `make verify-quote-verbatim ARGS="0273"` 26 verified / 0 failed / 12 SKIP-PDF. **The Title move and the Title delete are separate patches on purpose**: a delete's referrer check reads live database state, so it cannot see a move made in its own patch (the 0264/0265 precedent, which says so in a comment).
- **2026-08-19 rebuild**: restored `db.prod.patch-0269.2026-08-19.sqlite3`, which is prod through 0269 and dated the same day, then migrate + ingest of 0270-0274 in one pass. Replayed twice: once to fold `cabinet` onto the Jesus Edition, once after the user stripped 0272's note and the location cite. `make validate-in-db` 7 records across 0270-0274, 0 errors, 0 warnings. All three models resolve to one Title with a shared 21-feature core.
