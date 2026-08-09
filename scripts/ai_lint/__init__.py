"""AI editorial lint for data patches.

Two opt-in, AI-backed developer inner-loop tools that vet patch ``description:``
fields and citation ``quote:``\\ s *before* patches are ingested (patches are
immutable once applied). They are the AI-judgment layer on top of flippatch's
deterministic checkers (``patch_validation`` + ``quotes``): they reuse
those checkers' corpus resolver and patch-walking helpers and add the calls that
genuinely need a model.

Entrypoints:

- :mod:`ai_lint.description_check` — the four description rules
  (``missing-wikilink``, ``unknown-model``, ``plagiarism``,
  ``single-source-spine``).
- :mod:`ai_lint.quote_support` — ``quote-supports-claim``, spanning both
  description footnotes and scalar/edit claim cites.

Both require ``ANTHROPIC_API_KEY`` and are never part of the default
``make validate``. See ``docs/plans/AiLint.md``.
"""
