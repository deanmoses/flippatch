"""Citation verifier — the ``quote-supports-claim`` rule.

Builds on flippatch's deterministic ``verify-quote-verbatim`` (which confirms a quote is
verbatim in its source) with the AI question it can't answer: does the quote
actually *support* the claim it's cited for? Spans both description footnotes and
scalar/edit claim cites. See :mod:`ai_lint.quote_support.verify`.
"""
