"""Shared AI primitives for flippatch's API-driven tools.

The AI-judgment pieces that ``ai_lint``, ``ai_page_extract``, and the future
corpus sweep build on rather than reinvent: the Anthropic structured-call
``client`` and the candidate data model (``candidates``). See
``docs/plans/AiCommon.md``. Deterministic catalog lookup lives next door in
:mod:`common.catalog`; deterministic quote verification stays in
``quote_verify``.
"""
