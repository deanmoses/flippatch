# 0030 em-firm-years — authoring record

Corporate-entity active years for the four big early Chicago-era makers that
**0029 deliberately left unset** because they have no English Wikipedia article:
**Genco** (202 models), **Exhibit Supply** (156), **J. H. Keeney** (119) and
**Stoner** (75). The 0029 README flagged these as needing a wider net and likely a
new citation root — this patch does both.

**Attribution `flipcommons-catalog`**, one `cite:` per entry. Two makers cite an
already-seeded root; two cite **new roots this patch creates in its own `sources:`
block** (the 0012 mechanism — a patch can add roots and cite them in the same
file, since `sources:` is processed before `claims:`).

## Casting a wider net — sources

| Maker | Years | Source | Root |
| --- | --- | --- | --- |
| Genco | 1931–1958 | Wikipedia, *List of pinball manufacturers* — "Genco (1931-1958)" | seeded (0012) |
| Exhibit Supply | 1901–1979 | same list — "Exhibit Supply Company (1901-1979; pinball manufacturing 1932-1957)" | seeded (0012) |
| J. H. Keeney | 1934–1964 | American Jukebox History (`jukeboxhistory.info`) | **new** |
| Stoner Mfg. | 1931–1941 | Aurora Historical Society (`aurorahistory.org`) | **new** |

Wikipedia's **List of pinball manufacturers** (already seeded, but never used as a
cite until now) carries clean spans for Genco and Exhibit. It lists Keeney with no
years and omits Stoner, so those two drove the wider search.

### Dead ends (searched, not used)

- **arcade-museum.com company pages** — newer format gives only "released N machines
  … starting in YYYY" (first catalogued machine), no founding/closing. Not a
  corporate span.
- **arcade-history.com** — has manufacturer spans, but they are catalog-coverage
  ranges keyed to first/last catalogued machine, not corporate years: it lists
  "Keeney & Co., J.H. … 1931 - 1963" (vs the entity's actual Jan-1934 formation) and
  "Stoner Mfg. Corp. … 1933 - 1957" (neither the 1931 founding nor a real closing).
  Rejected in favour of the primary accounts.
- **German Wikipedia** (seeded) — no article for Keeney or Stoner.
- **Court records** (Lektro-Vend v. Vendo, 660 F.2d 255) confirm Stoner's April 1959
  sale to Vendo, but that is the *vending* company's end; see Stoner note below.

## Per-entity judgment

- **No per-field cite split was needed.** Each maker has a single source that
  supports both its years, so each is one entry with one cite (separate-cite
  entries were on the table but unnecessary here).
- **Catalog cross-check.** Each `year_start`/`year_end` was checked against the
  entity's own model-year range so a year never post-dates the first model or
  pre-dates the last: Genco models 1931–1958 (exact match), Exhibit 1932–1957
  (inside 1901–1979), Keeney 1934–1964 (exact match — confirming the Jan-1934
  formation over arcade-history's first-machine 1931), Stoner 1933–1941 (inside
  1931–1941).
- **Exhibit Supply** — corporate span 1901–1979 (the 0013/0029 corporate-existence
  convention); the note preserves the pinball-manufacturing sub-span 1932–1957,
  which is exactly this entity's catalog model range.
- **Keeney** — `year_start` 1934 is the formation of J. H. Keeney and Company
  (January 1934, after the predecessor Keeney and Sons was terminated November
  1933); `year_end` 1964 is the last pin game (the 1964 *Arrowhead*), after which
  American Jukebox History says the company went bankrupt "shortly after".
- **Stoner** — pinball era 1931–1941: founded 1931, left amusement production at the
  1941 wartime retooling for munitions (matching this entity's last catalog model,
  1941), after which Aurora Historical Society says it became a vending-machine
  maker. The corporation itself survived until its 1959 sale to Vendo, but that is
  the vending business, not this pinball entity — so `year_end` is 1941, not 1959.
