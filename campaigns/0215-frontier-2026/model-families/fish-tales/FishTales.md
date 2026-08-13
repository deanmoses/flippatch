# Fish Tales family — campaign notes

Patch: `patches/0225-fish-tales.yaml`. Two models: **Fish Tales: Ultimate Fishing Challenge (Kit)** (Cardona Pinball Designs, 2026, created bare by 0215) and **Fish Tales** (Williams, 1992, `ipdb:861`, already partly covered by the seed).

Supplement: `patches/0230-fish-tales-documents.yaml` (claimed 2026-08-12) — [document cites](../../RULEBOOK.md#document-cites) for the 1992 model; see [The 0230 documents supplement](#the-0230-documents-supplement-2026-08-12).

## Baseline survey (2026-08-11)

| field | fish-tales (1992) | ...-ultimate-fishing-challenge-kit (2026) |
| --- | --- | --- |
| credits | 7 roles (ipdb + catalog): design Ritchie, art McMahon, animation Slomiany, mechanics Skalon, music/sound Granner, software Penacho | none |
| display_type / system | dot-matrix / williams-wpc-fliptronics-2 | none / none |
| month / player_count / production_quantity | 10 / 4 / 13,640 | none |
| manufacturer_model_identifier / abbreviation | 50005 / FT | none |
| gameplay_feature | flippers ×2, multiball, spinning-targets ×1 (ipdb) | none |
| theme | fishing, sports | fishing, sports (0215) |
| production_status, game_format, cabinet, description, tag | all unset | all unset |

Duplicate scan ran against `model_claims` (active claims, both models) — the table above is what other actors already assert; everything the patch adds was checked against it.

## Evidence inventory

### First party (Cardona)

- **`https://cardonapinball.com/`, `/shop`, `/downloads`** — cached. The site is thin: a GoDaddy Website Builder site whose store is JS-rendered (a `--render` refetch of `/shop` still carries no product copy — the store loads via XHR; no per-product page found). The homepage meta description ("Explore Cardona Pinball for a wide range of pinball machines and products") is the site's densest quotable sentence. The `/downloads` page's anchor text labels every document.
- **Release notes PDFs** (on `img1.wsimg.com`, GoDaddy's shared CDN — see Traps): `FT release 2026 06 12.pdf` and `FT release 2026 07 13.pdf`, cached. Carry: the six official video links; the install procedure naming the **CPD CPU**, the **FAST controller** and **FAST sound board**, and USB power to the lower screen; per-release change history. June: "Added video mode", "Added announcer voices from Jada Holmes", "Added headphone support", caster's club MB fix. **"FT 2026 05 05 / First Commercial Release"** dates the first commercial code release.
- **Instruction card JPGs** (same host): `FT_instruction card left1.jpg`, `left2.jpg`, `_right.jpg` — cached, not yet transcribed (would need `web_import.py --text-file` before citing; nothing asserted rests on them).
- **YouTube channel** (six official videos linked from the release notes; `youtube:` cites, no root needed). Cached with transcripts: `1p6cpLBQJwk` (Game Announcement), `mvRdWatAink` (game play overview), `o-XezhzIBvg` (Kit Installation), `nS8trDTHXhU` (game play video #1). **No captions, uncached**: `JCEGnQBTUTQ` (Launch), `1QEV97geEiQ` (game play #2) — livestream-style, the fetcher caches nothing (see DataPatchAuthoring: a captionless video can't carry a quote).
  - Announcement carries: "officially licensed title from [...] Williams Planetary Pinball Supply", "brand new artwork [...] done by Brian Allen", the second display in the Stretch the Truth spot ("you get in um two screens"), "completely new game with all new um code, software, music, sound effects", "they made over 13,000 uh of these machines".
  - Overview carries: "It's a 15 inch screen", "there's a second five inch screen", the mode roster (original: Casters Club, Monster Fish, Rock the Boat, Frenzy), "three mini wizard modes and one full wizard mode", the Cactus Canyon-style "continued" framing.
  - Kit Installation carries: the hardware inventory (CPU + audio board + power supply on a metal plate, FAST board, speaker panel, mini display), HDMI 1 playfield monitor / HDMI 2 speaker panel monitor.

### Journalism

- **Kineticist interview** — `https://www.kineticist.com/news/james-cardona-interview` ("'Creators Gotta Create': James Cardona on the Business of Pinball 2.0 Kits", Colin Alsheimer, 2026-07-07), cached; Kineticist root already seeded. The family's richest source: "He writes the code, designs the games [...] while FAST Pinball handles the hardware"; "Brian Allen did my artwork"; the 2.0-kit category definition ("officially licensed products that install into classic Bally/Williams machines and turns them into a new game experience, while keeping the original intact"); Heart's "Barracuda" cleared through Sony Music; the $2,200 price; "Fish Tales is a perfect example with over 13,000 made"; the FAST-platform standardization story ("he wanted all the manufacturers on the same hardware which is why I had to switch to the FAST platform"); FT's original game "recoding [...] from scratch" and not yet complete.

### Structured rows

- **`ipdb:861`** (Fish Tales 1992) — the quotable row carries: `IPD No. 861 / October, 1992 / 4 Players`, `Model Number: 50005`, `MPU: Williams WPC (Fliptronics 2)`, the Notable Features line (criss-cross ramps ×2, rollunder spinner, multiball, captive ball, fishing-rod autoplunger, catapult), `Toys: Rotary fishing reel ball lock, moving fish topper.`, all seven person-credit lines, and the Notes naming the voice cast ("voices on this game were provided by Mark Ritchie, Steve Ritchie, Jim Gentile, Chris Granner, and possibly others") and "Jerry Pinsler sculpted the fish on the topper".

### Crowdsourced (research-only, never cited)

- **Pinside game archive** page (cached): names the full design team (James Cardona ×5 roles, Aaron Davis electronics, Brian Allen artwork), "Date April 2026", "Conversion kit, In production", "Generation FAST Pinball". Used as a hunting list per campaign practice.
- **Kineticist game index** row: same class.
- `draft-evidence-aggregator.csv` rows for this family are all Pinside-sourced.

## Traps

- **Cardona's documents live on `img1.wsimg.com`** (GoDaddy Website Builder CDN), a shared multi-tenant host with no maker-domain mirror (both plausible maker-domain URL shapes 404). Citable only via the **path-scoped `domains:` entry** on the Cardona root — `img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3` — the feature the user enabled for exactly this family (flipcommons `shared_hosts.py`; DataPatches.md → Citation sources). Registering the host bare is rejected by the apply.
- **Auto-caption spellings**: the transcripts render the title as "Fishtails" and the earlier kit as "No Good Gophers"; quotes must stay verbatim, so notes carry the correction where it matters.
- **Release-date conflict**: the maker's own release notes say `FT 2026 05 05 / First Commercial Release`; Kineticist says "Back in April, James Cardona released..." and Pinside says April 2026. Ruling below.
- **The Pinside "plays both games" claim is ahead of reality**: Kineticist (2026-07) has Cardona saying the original-game mode is being recoded from scratch and "we haven't completed the original game yet". The kit's dual-game promise is the category's, not yet FT's shipped state.

## Decisions

- **Path-scoped citation root** (user, 2026-08-11): the Cardona root rides in 0225 with the `img1.wsimg.com/blobby/go/4bd466e8-...` path-scoped domain, per DataPatches.md → Citation sources. This is the first patch to use the mechanism.
- **Kit `production_status: produced`, not `aftermarket`** — DomainModel defines `aftermarket` as "not an official commercial release"; the kit is an official, licensed, commercially sold product ("commercially produced and sold, even if only in small quantities" = `produced`).
- **`month: 5` for the kit** — the maker's own release notes label 2026-05-05 the First Commercial Release; primary outranks journalism's "Back in April" (which reads as the launch-event framing). Conflict recorded here; flagged to the user with the patch.
- **`model_relationship`: `conversion_kit` → `fish-tales`, `license_status: licensed`** — the DomainModel edge for kits; licensed per both the announcement video and Kineticist.
- **No credits carry from the 1992 donor to the kit** — a kit is neither a variant nor a remake; the kit replaces art, code, music, sound and animation wholesale.
- **System: create `fast-pinball` ("FAST Pinball")** — the kit runs Cardona's CPD CPU on the FAST platform; Kineticist documents the platform standardization across 2.0 makers (FAST also supplies Barrels of Fun and Euro Pinball Corp per the announcement video), so the node is shared, not Cardona-specific. `technology_subgeneration: ss-pc`. A System's `manufacturer` FK is NOT NULL at apply (the first snapshot apply failed on it), so **FAST Pinball is created as a manufacturer** — it genuinely makes the system, though no machines of its own.
- **FAST Pinball corporate entity + location (user catches, 2026-08-11)** — a bare manufacturer was the catalog's sole corporate-entity-less one (758 others all have one). Created `corporate-entity.fast-pinball` ("FAST Pinball LLC", per the site footer) with `location: [usa/wa/gig-harbor]` (location created in 0225, parent `usa/wa`). The maker's own site and LinkedIn say only "greater Seattle area"; the city rests on Skill Shot's "FAST Pinball HQ" venue listing (3226 Harborview Drive, Gig Harbor — the skill-shot.com root rides in 0225), corroborated by the maker's own Facebook page header ("FAST Pinball, LLC | Gig Harbor WA") and the Washington company registry (UBI 603387874, incorporated 2014-04-11, 8612 40th Street NW, Gig Harbor) — both on hosts the citation system cannot register (facebook.com is shared; the registry surfaces via aggregators), so they corroborate in the note rather than cite. The two street addresses are the office and the arcade/HQ venue; both are Gig Harbor, and only the city is asserted. The fastpinball.com root rides in 0225 too.
- **1992 voice credits ×4** (Mark Ritchie, Steve Ritchie, Jim Gentile, Chris Granner) from the `ipdb:861` Notes line; the "possibly others" hedge stays in the quote.
- **Jerry Pinsler → `art` credit on the 1992 machine** with a note that he sculpted the topper fish — matches his existing Party Zone `art` credit.
- **`game_format: pinball`** — 1992 cited to the ipdb Notable Features line (the 0220 older-sibling pattern); the kit cited to Kineticist's 2.0-kit definition with a classification note.

## Sought and not found

- **Music/sound composer for the kit's original score** — "all new um code, software, music, sound effects" (announcement) and the licensed "Barracuda", but no person is named for the original music anywhere first-party or journalistic. Not asserted.
- **Aaron Davis (electronics)** — Pinside-only as a role. fastpinball.com/about names Aaron Davis as FAST's co-founder (so the person is first-party attested), but no source credits him personally with the FT kit's electronics, and `electronics` isn't a credit role. Not asserted; the FAST hardware fact lives in the system + manufacturer + corporate-entity nodes instead.
- **The other voice actors** — Kineticist: "All the voice actors for Fish Tales are professionals and several work in radio for their day jobs", but only Jada Holmes is named (release notes). Only she is asserted.
- **Kit production quantity / player count** — no first-party statement found.
- **A Cardona flyer or product sheet** — none exists in the cache or on the site; the store is JS-only and carries no crawlable product page.
- ~~A city for Cardona Pinball Designs' corporate entity~~ — **resolved by the user (2026-08-11)**: the New Jersey business registry record, republished by City-Data, registers CARDONA PINBALL DESIGNS, LLC in **Pennsville, NJ** (entity 0450585629, registered 2021-01-06). Asserted with a `usa/nj/pennsville` location create and a City-Data.com root, the registry named in the note. The session's own hunt had come up dry — the Amazon author bio ("Southern New Jersey"; a deliverer host), Pinside's "NJ guy" (crowdsourced), and his own jamescardona.com pages (only his Lorain, Ohio upbringing) were all uncitable, cardonapinball.com publishes no address anywhere, and web searches for the registry missed the record because they queried "Cardona Pinball" without "Designs". Pennsville (Salem County) is consistent with all of it.
- **Written records behind the two captionless videos** (Launch, game play #2) — nothing cacheable; the four captioned videos cover the same ground.

## Not asserted (and why)

- **Kit credits for concept / rules / animation (James Cardona)** — Pinside-only role splits; the asserted `design` + `software` rest on Kineticist's "He writes the code, designs the games". (Animation is arguably supported by "I have been muddling through animation" — judged too oblique to cite as a credit.)
- **`cabinet`** for either model — no source states the cabinet class; prior families did not assert it either.
- **`description`** for either model — no 0216–0223 family wrote description claims; campaign scope.
- **Wizard/mini-wizard modes, per-mode roster** — rules content, not mechanism vocabulary.
- **Headphone support** (June notes) — reads as a software/service-menu feature; no evidence the kit ships a jack of its own. Recorded here rather than as vocabulary.
- **The 15-inch / 5-inch screen sizes** — no display-size field; sizes preserved in the quotes on the `display_type` cite.
- **Donor hardware facts on the kit model** (flippers, ramps, player count) — the donor machine supplies them; asserting them on the kit would double-count a machine the kit doesn't include.
- **Heart's "Barracuda" (Sony Music license)** — no catalog field for soundtrack contents; preserved here and in the cite quotes.

## Future unique features

- 1992: rotary fishing reel ball lock; moving fish topper (Jerry Pinsler sculpt); fishing-rod-shaped autoplunger; lightning-bolt flippers reportedly 1/8" shorter than standard Williams.
- Kit: 15-inch speaker-panel main display; second 5-inch playfield display in the Stretch the Truth location; five angler characters; licensed Heart "Barracuda" wizard-mode song.

## The 0230 documents supplement (2026-08-12)

Originally emitted by `gen_documents.py` (deleted 2026-08-13; in git history). [DocumentsAudit.md](../../DocumentsAudit.md) had held this family because its documents are IPDB-only; the user unblocked acquisition by having the session drive the **in-app browser** (fetch from page context, chunked base64 out, `web_import.py` in — each import carries `imported = 1`).

**Acquired** (all from ipdb.org, the only known holder — archive.org hunts recorded on the library docs): Operations Manual (16-50005-101, August 1992, 148 sheets, scanned + OCR'd), Operator's Handbook (June 1992, cached, service menus — **not declared**, no claim needs it), Parts List (plain text, fully gated), flyer front + back scans (merged into one library work; **back transcribed** via `--text-file`, so its quotes gate verbatim). Not acquired: promo video (.wmv, no transport), artwork/plastics scans, manual amendment.

**Claims** (all on the 1992 model): `video-modes` (flyer back), `pop-bumpers ×3` + `slingshots ×2` (the staples IPDB's Notable line skips — switch matrix printed page 3-4 names Left/Center/Right Jet and Left/Right Sling; parts list corroborates the jets), and `cabinet: floor` (assembly-instructions dimensions block, printed page 1-2, per the 2026-08-12 ruling). Bonus corroboration found, not asserted (already set): "This is a four ball game. Three balls in play and one captive ball." (manual printed page 1-2).

## Gate-run history

- **2026-08-11 `verify-quote-verbatim`**: 0 failed on the first emit; the 7 wsimg PDF cites report `SKIP-PDF` (their quotes were transcribed directly from the extracted text, so they are author-checked against the same rendering the next reader gets).
- **2026-08-11 `verify-quote-support 0225`** (one run, 14 calls / 137k tokens): 2 warnings.
  - `system.fast-pinball` `technology_subgeneration: ss-pc` — **genuine catch, folded in**: no cite established the PC-class hardware. Added the kit-installation video's port-panel quote ("HDMI 1, playfield monitor, Ethernet [...] two USB cable connections") and expanded the note.
  - `model.fish-tales` Jerry Pinsler `art` credit — **triaged, kept**: the checker reads sculpting as a distinct role from art, but the credit vocabulary has no sculptor role and Pinsler's existing Party Zone credit classifies his sculpting as `art`; the note now states that reasoning. Taxonomy-level disagreement per RULEBOOK → Operating the quote gates.
  - Not re-run after the fixes (RULEBOOK: a clean pass is not the goal; ~300k tokens a run).
