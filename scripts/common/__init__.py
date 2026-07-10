"""Shared library code the script packages build on rather than reinvent.

The umbrella namespace for anything reused across script groups. Two kinds live
under it: **domain-neutral** vocabulary at the top level — things any script
group may need regardless of what it does, starting with the ``Json`` type — and
**domain-specific** foundations in subpackages, currently :mod:`common.ai` (the
API-driven AI tooling's client, entity index, candidate model, and type
vocabulary). Kept minimal at every level: shared code lands here as a second
consumer appears, not ahead of need.
"""
