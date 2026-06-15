# 0043–0046 — early-Japanese makers & models (eremeka)

Adds the early-Japanese makers and machines from the **eremeka catalog**
(thetastates.com / earlyarcadesjapan.blogspot.com — credit the catalog if it reaches
a public surface) that flipcommons lacks. Source data: The-Flip/mfgtimeline
`data/eremeka_machines.json` (89 games). `gen.py` emits four patches, split by entity
depth because creating an FK target and referencing it in the same patch is
unsupported:

- **0043** manufacturers (8) → **0044** corporate-entities (8) → **0045** titles (26)
  → **0046** models (28 = 26 creates + 2 reassigns).

Descriptions follow in the hand-written **0047** (manufacturers) and **0048** (models).

## The reconciliation (the key step)

flipcommons imported every game **IPDB** lists, so the eremeka games split three ways
— keyed on IPDB, not on fuzzy name matching:

- **Already present, correctly placed** → year-fixed in 0042 (apollo-moon, the-world-series, …).
- **Already present but orphaned** → reassigned. `beat-spark` (ipdb 6771) and `jumbokick`
  (6772) sit in flipcommons with no maker because IPDB lists them "Unknown Manufacturer";
  the eremeka catalog identifies them as Nihon Tenbo's *Beat & Spark* and *Jumbo Kick*, so
  0046 sets their `corporate_entity` and year rather than creating duplicates.
- **Absent from IPDB → create.** Confirmed by IPDB title search: none of the new makers' games,
  nor the gap-fill titles, exist in IPDB.

## Scope & editorial judgments

- **In scope:** 8 new makers (Nihon Tenbo, Kato, Showa Yuen, Children's Amusement Park
  Facilities, Banpresto, Tomato Land, Towa, Sunwise) and gap-fill titles under makers
  flipcommons already has (Sankyo, Komaya, Universal, Nihon Gorakuki, Nihon Jidou Hanbaiki).
- **Out of scope:** Sega, Taito, Capcom, Namco — already consolidated in flipcommons and tied to
  the unresolved Japanese/US era-split question.
- **Sankyo not merged.** eremeka labels everything "三共 (Sankyo)", but flipcommons splits it into
  two corporate entities (`sankyo-precision-equipment-…`, `sankyo-amusement-park-…`). eremeka is
  not an authority on corporate sub-structure, so we fill data without merging; gap-fill Sankyo
  titles file under the primary entity.
- **Locations:** Nihon Tenbo, Children's Amusement Park Facilities and Showa Yuen — no verified HQ —
  stay at country-level `japan`, set in 0044 under the eremeka cite (eremeka is a Japanese-games
  catalog, so "Japanese" is eremeka-supported). The **five** makers with a known HQ **city** get it in
  **0049 instead**, each cited to the source that actually states it — eremeka does not record HQ
  cities: Banpresto → Shinagawa (Wikipedia), Tomato Land → Higashi-Osaka (Mynavi), Sunwise → Mitaka
  (Weblio), Kato → Setagaya (Denfaminicogamer), Towa → Nakano (AMpress). The same provenance rule keeps
  the Banpresto/Tomato Land/Sunwise 0043 create-notes eremeka-only; their richer corporate facts live
  in the 0047 descriptions where the right source is cited. operating_status (0049): Tomato Land
  ongoing; Banpresto, Sunwise, Towa ended; Kato left unknown (its modern entity's status is ambiguous).
  Showa Yuen is **not** given a city or status: the modern 昭和遊園株式会社 (incorporated 1978, after the
  1970 Rocket V game) shares only a generic name with the EM-era maker — no source links them, so we
  do not assert an inferred identity (cf. the Sankyo non-merge).
- **Dedup of duplicate eremeka rows:** Soccer 8 (Kato, 2 identical rows) → 1; Slap Shot (Towa,
  1996 + 1997) → 1 at 1996.
- **Collision-safe slugs** where the English title already exists for an unrelated maker:
  `big-race-sankyo`, `home-run-nihon-tenbo`, `saturn-komaya`, `space-patrol-childrens`,
  `slap-shot-towa`, `rodeo-game-mate`.
- **Themes** map eremeka `theme ~ …` tags onto flipcommons Theme slugs (`THEME_MAP` in gen.py);
  non-theme tags (gambling/medal, videogame mechanic, appearance, players) are dropped.

## Dead ends (justify the country-level locations)

HQ and founding/closing dates for the EM-era makers (Nihon Tenbo 日本展望娯楽社, Kato,
Showa Yuen 昭和遊園, Children's Amusement Park Facilities 児童遊園設備) and for Towa are
**unrecoverable** — absent from Japanese Wikipedia, IPDB, arcade-museum and Japanese
company registries (Baseconnect, weblio) in both English and Japanese searches. The
eremeka project itself records games and years, not corporate histories. So those makers
are located at country level (`japan`) rather than a guessed city. Only the better-documented
modern firms (Banpresto, Tomato Land, Sunwise) yielded a city.

Run `gen.py` from the flipcommons backend (reads live DB for collision/location/theme/orphan
preflight, then emits the four patches).
