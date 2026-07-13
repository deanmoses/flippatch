"""AI corpus sweep — judge corpus-vs-catalog deltas for one sparse field at a time.

The parts kit behind docs/plans/AiCorpusSweep.md: a deterministic reconciler
(Layer 1), a stateless trusted-tier fan-out judging every candidate from its
full source note (Layer 2), and deterministic gates that decide trust —
verbatim quote, unique target resolution, catalog diff — routing only
disagreements and doubt to a human review table (Layer 3).

The input is a small JSONL contract (:mod:`ai_corpus_sweep.candidates`) any
candidate-mining session can emit; the output is a durable, resumable
``results.json`` plus a skimmable ``REVIEW.md``.
"""
