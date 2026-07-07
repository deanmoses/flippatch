# 0079+ — Italian makers & models (tilt.it / IPDB.it)

Brings the flipcommons catalog up to full coverage of **IPDB.it — the Italian Pinball Database** (https://www.tilt.it/flipper_pinball/ipdb/), the reference archive of Italian-made pinball machines, online since 1995 and maintained as original research (site: "Dal 1995, l'archivio ufficiale dei flipper di produzione italiana!"). tilt.it is treated like the eremeka catalog was for the Japanese sweep (0043–0046): an original-research archive, effectively primary for machines that appear nowhere else. IPDB (`ipdb:N`) corroborates where it can; many machines are tilt.it-only.

## Evidence

All 47 pages (index + 46 maker/section pages) fetched into the pinexplore web cache on 2026-07-06 (`web_fetch.py`; the site 503s after ~20 requests at 2s spacing — the tail was fetched at 15s spacing). Quotes cite the page URLs; verbatim text is verified against the cache.

## The pipeline

1. `classify.py` (run from the pinexplore repo root) parses each cached maker page and cross-references every machine line against the catalog (`models`), the IPDB dump (`ipdb_machines`) and the OPDB dump (`opdb_machines`) in `explore.duckdb`. Outputs `makers.csv` + `worksheet.csv`.
2. Human review pass over `review=yes` rows and all dispositions; decisions recorded below. The reviewed worksheet is frozen in this dir.
3. `gen.py` (run from the flipcommons backend) reads the frozen worksheet + live DB and emits the dependency-ordered patches (manufacturers → corporate entities → titles → models).

## Page anatomy (what classify.py parses)

- Standard pages: `h1` maker name(s) (sometimes several eras: "BELL GAMES – BELL COIN MATICS – NUOVA BELL GAMES"), `h2` city/principals line ("(Bologna, Italy – Sig. Cavazza)"), then bare-year section markers ("1979", "(?) 1970" = uncertain) and machine lines.
- Machine lines: `Name (parenthetical) – em|ss – Np (notes)`. The parenthetical is usually the American original the game copies/rethemes ("Fantasy (Centaur)"), sometimes an artwork credit ("grafica di Cortez") or free text — disambiguated in review, never mechanically.
- Gallery-style pages (`ad/`): no h1; one `h2` per machine; maker name taken from the page `<title>`.
- Noise filtered: image galleries, photo-credit captions ("(collezione …)", "(sala-giochi …)"), share-widget footer, "ultimo aggiornamento" lines (kept as maker metadata).

## Matching rules

- Machine names normalized (case, accents, punctuation) for exact-name matching; no fuzzy edit-distance (false-positive prone on 2–4 word names).
- Catalog match is **high** confidence only when the model's corporate entity is among the maker page's candidates; name-only matches are **low** and review-flagged (e.g. Bell Games' "The King" ≠ Alben's 1959 The King).
- Maker candidates matched on legal-suffix-stripped, space-collapsed name keys ("Bensa srl" ↔ "Bensa s.a.s.", "Mondial Matic" ↔ "Mondialmatic"). Substring containment produces some false candidates ("DAMA" ⊂ "norDAMAtic"; Eagle ↔ the US Eagle firms) — resolved in review.

## Coverage (frozen after the 0083–0108 sweep)

376 machine rows parsed from 46 pages → 280 exists / 53 create / 1 reassign / 21 defer / 10 noise (`reviewed.csv`, one verdict + reason per row). After applying 0079–0108 to a flipcommons snapshot, **333 of 334 actionable rows resolve to a catalog model**; the one exception is the deliberately deferred unnameable Pinball Shop modification kit. Patch layout is one vertical patch per manufacturer (0083–0089 new makers, 0090–0107 existing makers, 0108 the maker-less unidentified kits), after 0079 (sources), 0080/0081 (provinces then cities — location parents must pre-exist), 0082 (the CEFF pilot).

## Review decisions

- **CEFF (pilot, patches 0079–0081).** Manufacturer + corporate entity + Five Martians title/model created as a single vertical patch (0081) — validated end-to-end against a flipcommons snapshot (same-file dependency-ordered creates work). **Joker Ball NOT created**: tilt.it itself says it is unclear whether it names a second model or a Five Martians gameplay feature — uncertain existence → no record (now written policy in DataPatchAuthoring.md → Creating new catalog entities). Five Martians carries no `year` and no `technology_generation` (tilt.it states neither; the two-versions note — score reels vs. millions — stays in the note/description, one Model). Corroboration sought (web search): tilt.it-only, said so in the create note.
- **AD is not a maker.** Its three page machines resolve to existing DAMA records; IPDB 4405's own note documents the aD/Md logo confusion ("We do not know the meaning of these logos"), and the "Spiders" photo backglass reads SPIDER = Dama's. No AD manufacturer created.
- **P.C. created to adopt the orphaned `marte`** (ipdb 5942, "Unknown Manufacturer"): the machine's own instruction card carries the P.C. mark; reassigned, not duplicated.
- **Dalla Pria created on first-party evidence** (dallapria.it: in games since 1958, Piove di Sacco; operating_status ongoing). Its **Stellar Airship stays deferred**: IPDB 4016 is first-party from Mr. Geiger (1979 SS conversion of Bally's Eight Ball) while tilt.it shows a Dalla Pria/ABM EM-Gottlieb kit of the same name/artist — unresolved, evidence banked.
- **Sidam Rugby is a video game** (game_format video-game, patch-0038 convention), 1979 preferred over arcade-museum's 1976 (RetroCampus + tilt.it/deb corroborate); year carries a four-source cite list.
- **elettronolo = elettrocoin**: page header names one firm under three names (Elettronolo/Elettrocoin/Elettrogiochi, Sesto Fiorentino); creates filed under `elettrocoin`.
- **Jungle Life ×3 created** (Zaccaria, LORI, Emmepi copies of the Gottlieb game), maker-suffixed slugs; the orphaned `jungle-life-2` (ipdb 5266, "might say Erremegi") left alone.
- **Manilamatic years dropped**: the page's 1976 header is impossible (Joker copies Premier's 1987 Monte Carlo; itmade.htm dates the Enada III reference 1974).
- **Deferred (21 rows, reasons in reviewed.csv)**: nameless machines (Bensa "???", GL "????"), tilt-hedged existence (Pasini "Bonnie '70 ?", BEM "identico a quello costruito dalla Playmec?"), the Zaccaria Ten Up phantom (IPDB quotes Croci: "the game never existed"; catalog `ten-up-2` flagged for a future cleanup), attribution conflicts parked for evidence (Big Sakem Nordamatic-vs-Ripepi, The Best Corsair, AI-LO brand), DAMA's caption-suspect bare-name list stretch (Flipper/O.K. Corral/Novelty/Player/Ponies — need human eyes on the photos), the unnameable Pinball Shop Space Shuttle kit.
- **Maker-less models kept maker-less with hedged attributions banked**: arabic-power, ascot ("purported to be BEM... not confirmed" — IPDB), space-woman (tilt itself hedges "GL ?"), sure-shot-5, grand-slam-10. CE assignment deferred to a corroborated pass.
- **Kit tagging completed in 0110** (post-apply review finding): the sweep tagged conversion-kit only where the review verdict said kit outright — the hedged creates (Hit and Run, Card Trix, Aquarium, ...) and the seeded IPDB models with explicit "(kit for ...)" page statements (Tex-Op, Bowling, El Viti, El Tigre, New City, Grand Slam, Lido) had none. 0110 tags all of them; section-membership-only cases say so in their notes. Still untagged: seeded section members with neither statement nor certainty (Thrills, The Royal, Sky Devil's, Time Out, KO, Countdown, Big Sakem, Cosmos, Neptune, Arrow, Hot Bullet, Mini Flipper) — follow-up when their kit-ness is corroborated.
- **Steeple's "(?)"**: tilt.it hedges the machine/name itself ("Steeple (?)"); the shipped 0085 note carries only the missing-technology hedge. The name hedge goes in the Phase-5 description.
- **Multi-source cites**: where the review pass found verifiable second sources under seeded roots, they ride the entry `cite:` lists (Rugby ×4, Pool Rabbit + VPForums, Big Dryvers + Pinside, Queen's Castle-era zaccaria-pinball.com quotes on their rows); unverifiable or unrooted ones (a Flickr photo, it.wikipedia) live in `third-sources.csv`/`corroborations.csv` for the description phase or a later roots patch.

## Corroboration ledger (`corroborations.csv`)

The apply engine takes at most one citation per fact per assertion, and rejects a same-value re-assertion once the attributing source already holds the field — so a fact can't gain corroborating evidence after the fact today. Multi-cite support is being added separately; until then, every *additional* source found for a fact (beyond the one cited in the patch) is banked in `corroborations.csv` (`entity_ref, field, value, ref, quote, note`) for a second pass that attaches them once the system supports it. Quotes in the ledger follow the same verbatim rules as patch quotes so the second pass can ship them unedited.

## Key reconciliation findings

- Far fewer makers are missing than the raw tilt.it index suggests: many exist under abbreviated or variant slugs (AMI, BEM, EGS `e-g-s`, IDI, MD, RMG, LORI, Pasini, Apple Time, Artigiana Ricambi `ditta-artigiana-ricambi`, ManilaMatic, Mondialmatic, Mr. Game `mr-game`, Bensa `bensa-sas`).
- Genuinely missing maker pages (as of the first classify pass): AD, Bontempi, CEFF, Dalla Pria/ABM, Ferna, G.Braun, GL, Italiana Biliardi, P.C., RIFLIP, SIDAM/SIPEM, Skill Game/The Best (TBC), AI-LO (unidentified-kit section).
- tilt.it's `elettronolo` page matched catalog `elettrocoin` — likely the same firm under different names; confirm in review before treating as a rename/alias rather than a new maker.
