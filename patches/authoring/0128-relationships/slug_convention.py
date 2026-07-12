"""Slug convention for licensed-build / bootleg / conversion patches.

When a derivative machine (licensed build, bootleg, or conversion) has a
disambiguation-numbered slug like `spin-out-2`, rename it to end in the maker
instead — `spin-out-maresa` — BUT ONLY when the derivative carries the SAME
name as the original it reproduces. If the names differ (Maresa's "Tahiti"
copies Gottlieb's "Tropic Isle"), the number is separating unrelated same-named
games rather than the original, so appending the maker clarifies no
relationship — leave the slug alone.

Established by patch 0128 (licensed builds); apply the same to bootleg and
conversion patches. See README.md "Slug convention". Pure functions — the
caller reads names/manufacturer strings from the DB and passes them in, then
checks the returned slug against existing slugs for collisions.
"""
import re

_LEGAL = r'(s-?a|spa|srl|inc|ltda|ltd|gmbh|co|incorporated|corporation|company)'

# Confirmed hand-short suffixes for makers whose IPDB string has no [Trade Name:]
# tag but that are universally known by a short name. Add to this as they're
# verified — checked first, before trade-name/entity derivation.
_OVERRIDES = {
    # Full legal name "Fipermatic Indústria Comércio Importação e Exportação
    # Ltda"; the backglass logo and every IPDB note call it just "Fipermatic".
    'fipermatic-industria-comercio-importacao-e-exportacao-ltda': 'fipermatic',
}


def _slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')


def _norm(s):
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def maker_suffix(ce_slug, ipdb_manufacturer):
    """Short maker token for the slug suffix: the IPDB trade name if the
    manufacturer has one, else the corporate-entity slug with legal-form and
    parent-company tails stripped.

    A DEFAULT to sanity-check, not gospel: some trade names slugify awkwardly
    (R.M.G. -> `r-m-g`), some entities have no trade name and a long legal slug
    (`fipermatic-industria-comercio-...` — pick a hand-short form), and two
    entities can share a suffix (e.g. both RMG rows -> `r-m-g`; check for
    collisions before writing).
    """
    if ce_slug in _OVERRIDES:
        return _OVERRIDES[ce_slug]
    m = re.search(r'\[Trade Name:\s*([^\],]+)', ipdb_manufacturer or '')
    if m:
        return _slugify(m.group(1))
    s = re.sub(r'-a-(division|subsidiary)-of-.*$', '', ce_slug)
    s = re.sub(rf'-{_LEGAL}$', '', s)
    return s


def rename(model_slug, model_name, original_name, suffix):
    """Return the new slug, or None to leave the slug unchanged.

    Renames only when BOTH hold: the slug ends in a disambiguation number, AND
    the derivative's name matches the original's name (a same-named build).
    Caller must still check the result against existing slugs for collisions.
    """
    if not re.search(r'-\d+$', model_slug):
        return None
    if _norm(model_name) != _norm(original_name):
        return None
    return re.sub(r'-\d+$', '', model_slug) + '-' + suffix
