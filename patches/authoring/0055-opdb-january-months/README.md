# 0055 — retract OPDB's January months

OPDB encodes a year-only manufacture date as January 1, so an OPDB `month` of January carries no information. 0055 retracts the `month` claim (attributed to `opdb`, acting on its own claims) from all 870 models whose active OPDB month claim was January; no citations — the ChangeSet note explains the ingest refinement. Takes the 0055 numbering hole (patches after 0038, the prod boundary, are renumberable).

Effect on the dev catalog: 320 models fell back to a real (non-January) IPDB month; ~147 lost their month entirely; **~403 stayed January because IPDB's own claim beneath is also January** — IPDB's dump has the same year-only `YYYY-01-01` default (1,481 Januaries vs ~330/month average), so those remain ambiguous (real January vs. unknown) and would need the same treatment against `ipdb` if wanted.
