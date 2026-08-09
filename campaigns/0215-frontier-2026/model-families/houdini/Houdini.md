# Houdini — 0216

## Status

**Rewritten and snapshot-validated 2026-08-07 (deduped against 0215 on 2026-08-08); unshipped, awaiting user commit/push.** The first rewrite re-asserted `production_quantity` and `tag: limited-edition` on the 100th, which **patch 0215 already asserts** — the baseline survey checked neither field. A full claim-level scan (every 0216 claim vs every other actor's claims on the same key) found no other overlap; those two are out of the patch and gen.py, and the dev DB was rebuilt clean. Scan lesson: an exact duplicate (same actor + key + value) is **silently swallowed** by the apply and leaves no `patch_claims` row, so scan against `model_claims` from other actors, not against what the patch wrote — the tag dupe was invisible the first way, and production_quantity only surfaced because 0215 asserted the number `100` while the emitter wrote the string `"100"`. The original thin 0216 (8 claims, 100th-only) was replaced outright per the pre-rewrite note here. The rewrite: 28 entries across all three family models, sources = the AP announcement, the AP `/houdini` product page, and `ipdb:6470`; all gates green (`make validate`, `make verify-quotes` 27/27) and applied cleanly on the snapshot below with credits/lineage/fields/features/tag all resolving as intended. `make verify-citations` (AI lint) not run — API credit balance too low at the time.

**Dev-DB rebuild recipe (user, 2026-08-07):** restore from `db.prod.patch-0214.2026-08-03.sqlite3`, run `migrate`, then `ingest_patches --patches-dir ../../flippatch/patches`. Rebuild as often as needed.

## Models

- Houdini 100th Anniversary (American Pinball • 2026)
- Houdini: Master of Mystery (American Pinball • 2017)
- Houdini: Master of Mystery (Deluxe) (American Pinball • 2017)
- `houdini-master-mystery` isn't a sibling, leave it alone. IPDB 6469, year NULL, `unreleased` — the never-built Popadiuk/Andrews design, not an edition of anything. Its own `ipdb_notes` say it "was not produced and was replaced by American Pinball Inc.'s 2017 'Houdini Master of Mystery' with a playfield from a different designer, and different backbox and artwork."

## Catalog baseline (surveyed 2026-08-07, dev DB with current 0216 applied)

What each model already holds; **only assert what's missing.**

| field | mom 2017 | deluxe 2017 | 100th 2026 |
| --- | --- | --- | --- |
| year / month | 2017 / 10 | 2017 / 10 | 2026 / — |
| production_status | — | — | produced (0216) |
| game_format | — | — | pinball (0216) |
| tech generation | solid-state | — | — |
| display_type | lcd | — | — |
| system | multimorphic-p3-roc | — | — |
| model_number | GAM0001 | — | — |
| players | 4 | — | — |
| lineage | — | variant_of → mom ✓ | **no edge** |
| description | empty | empty | empty |
| credits | full (Balcer design+mech, Busch/Riesterer art, Raneses anim, Kern music+sound, Kugler sw) | **none** | Franchi art only (0216) |
| gameplay features | catapults 2, flippers 2, magnets 3, multiball, pop-bumpers 3, slingshots 2 | **none** | flippers, knockers, magnets 3, multiball, shaker-motors, toppers, video-modes 1 (0216) |

`production_status` vocabulary is announced/produced/unreleased/one-off/aftermarket — there is **no retired value**, so the site's RETIRED badges on the Classic/Deluxe carousel panels answer no catalog field. All three models are `produced`.

## Evidence inventory (all cached in pinexplore web cache)

- **`https://americanpinball.com/houdini`** — the 2017 product page (headless render; JS tabs). Carries: the "Choose Your Edition" carousel (Classic / Deluxe / 100th Anniversary), explicitly-headed **"Deluxe Features"** (Shaker, Interior Side Art, Topper, Knocker, Magic Glass, Steampunk Flippers), game-level **"Additional Features"** (Playfield: 3 magnets, 6 balls, catapults…; Rules: 5 Multiballs, 1 Video Mode, 10 Stage Modes…; Cabinet: 15.6" LCD, **4** Stereo Speakers, 75"H × 29"W × 55"D, 275 lbs boxed), FAQ ("Designer Joe Balcer…", "Houdini uses 6 pinballs"). HTML page → quotes are gated by `make verify-quotes`.
- **`https://americanpinball.com/houdini-100th-anniversary-pinball`** — the 100th announcement, posted 03/19/2026. Facts: "limited production run of just 100 machines worldwide", $7,995, Franchi cabinet art, "custom topper, Magic Glass, shaker motor, knocker, and mirrored art blades as standard equipment", and the variant framing ("versions of the game"). This is the only 100th-specific document that exists — no flyer, no manual, no AP YouTube reveal found (web-searched 2026-08-07; only third-party hands-on videos and distributor listings, which we don't need since AP's own copy is live).
- **Houdini Game Manual** (193 sheets, real text layer) — `48804760.fs1.hubspotusercontent-na1.net/.../Houdini%20-%20Game%20Manual.pdf`. A **service** manual: P3-ROC system (sheets 14–15), electrical, service menus. **No people credits anywhere in it.** Documents the 2017 machine.
- **Houdini Flyer, 2 sheets, via Wayback `id_` snapshot** — `web.archive.org/web/20250325113004id_/https://www.american-pinball.com/games/houdini/Houdini-Pinball-Flyer.pdf` (cite `ref` = the original `american-pinball.com` URL + `archive:`). Outlined type, OCR-only — **render and transcribe**. Sheet 2 is the densest 2017 source: Interactive Game Features (Three Magnets, Two Catapults, Magic Stage with Multiple Servos, Mechanical Trunk, Hidden Ball Subway System, 6 Balls…), Cabinet Features (15.6" LCD **1360 × 768**, **6** Stereo Speakers, H: 75" W: 29" D: 55", 275lbs. Boxed), Rule Features (5 Multiballs, 3 Magician Mode, 1 Master Magician Mode, 10 Stage Modes Including Video Mode…), "P-ROC Electronic System", footer "Manufactured by American Pinball, Inc. USA © 2017". No people credits.
- **Quick Reference Guide** — fuse/coil service card. Research-only.
- **9 service bulletins / install guides** (topper, shaker, knocker kit, EOS, coil kit, power supply, speaker grill, skill shot, scoop) — corroborate add-on hardware; unlikely to be cited.
- **`/games`, `/released`, `/retired` listing pages** (fetched 2026-08-07) — Houdini family shows "Released" via an image filename (`Houdini-100-09`); positional/mark evidence at best, and with no retired production_status value there is nothing they'd support anyway.

## Traps

- **The Wayback wrapper is in the cache too.** The bare `20250325113004/...` snapshot cached the HTML viewer ("Wayback Machine", 2 matches); the `id_` snapshot is the real PDF. Use the `id_` one.
- **Speaker count conflicts across primary sources.** Flyer (2017) and IPDB say **6** stereo speakers; the current website's Additional Features says **4**. Do not assert either without a user decision.
- **The manual and flyer document the 2017 machine.** Anything asserted about the 100th from them is an assumption, not evidence (the original 0216 gen.py warning stands). The 100th's own facts come from the announcement and the `/houdini` page — which *does* cover the 100th, since its edition carousel includes it and its game-level Additional Features describe the game all three editions are editions of.
- **Per-edition claims from the carousel are positional.** Classic/Deluxe/100th panels repeat identical headings; only "Deluxe Features" is explicitly labeled. Don't cite a panel by position — same splice problem as a matrix column.

## Decided (user, 2026-08-07)

1. **Speakers: 4, cited from the current AP site.** The flyer/IPDB say 6; the site is AP's current word and wins.
2. **Variant ⇒ all credits apply.** The user's rule: a variant carries every credit of its base. Both the Deluxe and the 100th get the full 2017 team (Balcer design+mechanics, Busch/Riesterer art, Raneses animation, Kern music+sound, Kugler software), cited `ipdb:6470` — the base game's row, quoting its credit fields. The 100th additionally keeps Franchi (art, announcement).
3. **`variant_of`: yes** — the 100th → `houdini-master-of-mystery`. (The "different design" the user half-remembered is the never-built 2016 `houdini-master-mystery`, not the 100th.)
4. **`production_count: 100`: yes**, from the announcement.

Enabler for #2: `ipdb_row_text` in `scripts/quote_verify/verify_quotes.py` must render the IPDB credit fields (DesignBy, ArtBy, DotsAnimationBy, MechanicsBy, MusicBy, SoundBy, SoftwareBy) plus ModelNumber and MPU so those quotes verify — done this session.

## Decided (user, 2026-08-08) — the feature sweep, `patches/0219-houdini-features.yaml`

After `0218-presentation-feature-vocab` (represent ALL features, gameplay-affecting or not) and the verbatim-wording policy (manufacturer's wording unless extremely clearly a synonym; when in doubt, a child feature):

- **`mirrored-art-blades`** — new child of BOTH `art-blades` and `mirror-blades` (two-parent precedent: `led-illuminated-art-blades`). On the 100th, from the announcement's equipment sentence.
- **`interior-side-art`** — new child of `art-blades`. On the Deluxe, from the site's "Deluxe Features" list.
- **`steampunk-flippers`** — new child of `flippers`; on Deluxe + 100th. And **`flipper-toppers`** as its OWN node — flipper caps are NOT cabinet `toppers`; the shared word is exactly the false synonym the verbatim policy catches. IPDB "Game-specific flipper toppers", flyer "Custom Laser Cut Flipper Toppers!".
- **Full vocab sweep** for the rest (18 new nodes in 0219): balls, subways, stages, stage-curtains (child of stages), trunks, marquees, spirit-planchettes, milk-cans, bumper-tops, rgb-playfield-inserts, led-general-illumination, cabinet-armor, playfield-lcds, mylar-playfield-protection + the four above. **`ball-locks` already existed in the seed vocabulary** — don't create it (the first apply failed on exactly that); its "Ball Staging/Lock Mechanisms" alias would be a fact added to an existing entity, left as a user call.
- **Speakers resolved per the earlier ruling**: `{speakers: 4}` + `stereo-sound` on all three models, cited to the current site's "4 Stereo Speakers". The glass split: base model gets `anti-reflection-playfield-glass` (IPDB "Glare-reduced playfield glass"), the editions get `magic-glass` (the branded child) from site/announcement.
- **0219 must follow 0218** (numeric order; it attaches 0218's nodes). Family dirs are unnumbered since 2026-08-08 — a session claims the next free patch number when work starts (see ENRICHMENT-PLAN.md → Model families).
- **Multiball count (user-approved 2026-08-08):** "5 Multiballs" is five multiball **modes** — the site's rules list counts modes ("10 Stage Modes incl. Straight Jacket Multiball") and the 6-ball complement is stated separately — so `{multiball: 5}` rides on all three models in 0219, citing the site. On the base model this is an approved modification outranking the count-less ipdb seed claim; on the editions it supersedes 0216's count-less assertion at apply time.

Tooling enabler (TDD'd this session): `verify_quotes` now resolves a cite via its `archive:` URL when the `ref` itself isn't in the cache — the flyer is the first archived-document cite, cached under the Wayback `id_` snapshot URL while the cite's `ref` stays the dead publisher URL. Its transcribed quotes report `SKIP-PDF`, as designed.

## Decided (user, 2026-08-08, later) — toys rationalization of 0219

The first 0219 was judged **too granular and model-specific** against [0218](../../../../patches/0218-presentation-feature-vocab.yaml)'s standard, and the toys question was settled corpus-wide in [campaigns/features-corpus/CHARTER.md](../../../../campaigns/features-corpus/CHARTER.md): toys are vocab nodes under a new `toys` interior parent (chosen over a `model.toys` text field for encyclopedia entries on iconic toys and per-title edition comparison). 0219 regenerated accordingly:

- **New `toys` node**, created here (parentless interior node; is-a holds — a trunk IS a toy).
- **Re-parented under `toys`**: `stages`, `trunks`, `marquees`, `spirit-planchettes`, `milk-cans`. Aliases unchanged.
- **`stage-curtains` deleted** — a curtain is *part of* the stage toy, not a kind of stage (the parent link is is-a only; this was the recorded violation). The "Automated Main Stage Curtain!" flyer span and its assignments are dropped; the automated curtain belongs in the `stages` node's eventual description (0074-style descriptions patch, still owed).
- Unchanged: the generic mechs (`subways`, `balls`, `bumper-tops`, `rgb-playfield-inserts`, `led-general-illumination`, `cabinet-armor`, `playfield-lcds`, `mylar-playfield-protection`), the 0218-style children (`steampunk-flippers`, `interior-side-art`, `mirrored-art-blades`, `flipper-toppers`), and every count.
