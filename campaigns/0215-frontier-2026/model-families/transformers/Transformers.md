# Transformers

No patch number claimed yet — claim the next free number when work starts (see ENRICHMENT-PLAN.md → Model families).

## Models

- Transformers: More Than Meets the Eye (Pro) (Stern • 2026)
- Transformers: More Than Meets the Eye (Premium) (Stern • 2026)
- Transformers: More Than Meets the Eye (Limited Edition) (Stern • 2026)
- Transformers (Pro) (Stern • 2011)
- Transformers (Limited Edition) (Stern • 2011)
- Transformers Autobot Crimson (Limited Edition) (Stern • 2011)
- Transformers Decepticon Violet (Limited Edition) (Stern • 2011)
- Transformers The Pin (Stern • 2012)

## Tips

Transformers MTMTE manual has bookmarks (96 entries); read with `pypdf`.

## Traps

**The two 2011 manuals are the same file.** `Transformers-Manual.pdf` and `Transformers-Manual-LE.pdf` (both `wp.sternpinball.com/wp-content/uploads/2018/11/`) are **byte-identical** — one `content_sha`, `9a4ff4cc3f5391bf730d226eb969c855c7c8c0f429c33e66d846d4069c7898b8`, 134 sheets each. Stern serves one document under two names, so the `-LE` filename promises a per-edition source that does not exist: **the 2011 manuals cannot distinguish Pro from Limited Edition.** Anything the manual says applies to the 2011 family generally, not to an edition. Do not read the filename as evidence about the file — check the sha before treating two Stern manuals as two sources. (Same shape as the Pokémon trap in [pokemon](../pokemon/Pokemon.md), where Premium and LE share one manual.)

**Both 2011 manuals are OCR-only.** No text layer at all — 227,165 chars of OCR and nothing citable-by-extraction, so `quote` returns nothing and `search` answers from the `(ocr)` tier. Render the sheets and read them: words you read off a sheet **are** quotable, and `make verify-quotes` skips PDF quotes (`SKIP-PDF`), so transcribe exactly rather than lifting the OCR string — its readings are ~88% line-exact and a plausible-but-wrong one (`Magictan` for "Magician") would sail through. See ENRICHMENT-PLAN.md → Citing PDF evidence.

**`transformers-the-pin` is not under the `transformers` Title.** It has its own Title, `transformers-the-pin`, so a query scoped to `title_slug = 'transformers'` silently misses it. The family boundary here is this plan's, not the catalog's — enumerate the eight models by slug rather than by Title.

## Decided

**Matrix volume: emit the full grid.** All ~55 rows × 3 editions, every feature, including the ones common to all three. Do not prune to the distinguishing features.
