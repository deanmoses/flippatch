"""AI page-data extractor — the cheap-model recall fan-out (first cut).

A developer inner-loop tool: it reads one cached source page about a pinball
machine, fans it out across narrow cheap-model slices — each asked about one
slice of the possible facts — deterministically checks every supporting quote
is verbatim, and hands back a JSON *packet of candidate claims with checked
evidence*. The expensive master session that runs it is the arbiter; the packet
is candidates, never facts. See ``docs/plans/AiPageDataExtractor.md``.

This is the first usable vertical: a model-info slice set on the cheap tier,
optional live vocab grounding from the flipcommons dev DB, field-keyed coverage
states, and quote verification. It still deliberately has no prompt caching,
extraction-record persistence, or entity-discovery target resolution.

It consumes ``common.ai`` (client + candidate model), ``common.catalog``
(catalog vocabulary / lookup), and ``quotes`` (source text +
``check_quote``) rather than reinventing them.
"""
