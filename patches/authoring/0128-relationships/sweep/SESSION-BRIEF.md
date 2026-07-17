# Session brief — running 0128-relationships through the corpus sweep

You are continuing the 0128-relationships campaign ([../README.md](../README.md)), but driving it through the **AI corpus sweep** tool, which was just built and has never been used in anger. Your job is both: make campaign progress AND harden the tool by recording where it fails, misleads, or creates friction.

## Orient first (in this order)

1. [../README.md](../README.md) — the campaign: conventions, authoring recipe, the dev-DB rebuild loop. Follow its links to DomainModel.md / DataPatchAuthoring.md before authoring anything.
2. [docs/corpus_sweep/CorpusSweepOperating.md](../../../../docs/corpus_sweep/CorpusSweepOperating.md) — how to operate the sweep, its trust model, and what each disposition means. Read the whole thing before running anything.
3. [docs/plans/AiCorpusSweep.md](../../../../docs/plans/AiCorpusSweep.md) — the design (skim; the status header says what v1 has and lacks).

## What already exists in this dir

- [../emit_candidates.py](../emit_candidates.py) — regenerates `candidates.jsonl` here from [../Worklist.md](../Worklist.md) (298 rows, one per worklist row; the Worklist's target guesses ride as `hint`, which the sweep audits but **never shows to the model**). Run with `uv run python3 emit_candidates.py`.
- `candidates.jsonl` + `RECONCILE.md` — already generated once. **Regenerate both after every dev-DB rebuild** (the DB is ground truth and moves).
- [../check_status.py](../check_status.py) / [../STATUS.md](../STATUS.md) / [../reconcile_worklist.py](../reconcile_worklist.py) — the older per-campaign status tooling, still valid; the sweep supersedes its judgment role, not its bookkeeping.

## The loop

1. Rebuild the dev DB per README "The dev DB". Other sessions also rebuild it — if SQLite says "database is locked", another session is mid-rebuild; wait, don't force.
2. `uv run python3 emit_candidates.py`, then the free wiring check:

   ```bash
   make sweep ARGS="patches/authoring/0128-relationships/sweep/candidates.jsonl --no-ai"
   ```

3. **Trial:** `make sweep ARGS="patches/authoring/0128-relationships/sweep/candidates.jsonl --limit 10"` — then skim `REVIEW.md` here. If the model's verdicts or the field guidance look off (`scripts/ai_corpus_sweep/fields.py`), 🛑 **STOP and tell the user before the full run.**
4. **Full run:** `make sweep ARGS="patches/authoring/0128-relationships/sweep/candidates.jsonl --resume --max-requests 320"` (~298 trusted-tier calls, sub-dollar, 10–20 minutes). **Run it in the background** and poll while it goes — a blocking foreground call shows the user nothing for the whole run:
   - `make sweep ARGS="patches/authoring/0128-relationships/sweep/candidates.jsonl --status"` — progress/dispositions, free, safe anytime.
   - `results.json` and `REVIEW.md` are rewritten after **every** row, so Ctrl-C/kill loses at most the row in flight and `--resume` continues; you can start reading `REVIEW.md` escalations while the run is still going.
   - After a gate/tool fix or a dev-DB rebuild, `--regate` re-buckets all stored answers in seconds with **zero** AI spend — never re-run the AI over rows already judged.
5. Work `REVIEW.md` top-down: `conflict` and `set-but-unsupported` first (these are candidate **wrong existing values** — exactly what the tool was built for), then `hint-mismatch` (the sweep disagrees with the Worklist's old guess — decide from the verbatim quote and full note, prefer web-cache corroboration per README), then `ambiguous` / `unresolved` / `uncertain`. `fill` rows are pre-greened candidates, not verified facts: still spot-check a sample against the full IPDB note before authoring.
6. Author patches from confirmed rows per the README recipe — per-maker patches, the slug/naming conventions, and the OPDB-group check before any title merge (the README's 🛑 rules apply unchanged). Then the snapshot apply-verify loop, `make validate`, `make verify-quotes`.

## Hardening duty

Keep a running `TOOL-NOTES.md` in this dir as you go:

- **false greens** — anything pre-greened (`fill` / `agrees` / `no-claim`) you found wrong. These matter most; each one should be reported to the user immediately, not just logged.
- **false escalations** — rows the sweep flagged that were actually fine (these cost review time, not correctness).
- guidance gaps in `fields.py`, resolution failures (`unresolved` / `ambiguous` a human resolves trivially), rendering/UX friction, bugs.

Don't patch `scripts/ai_corpus_sweep/` yourself unless something blocks you; note it instead.

**Checkpoint with the user.** When you find a tool defect (especially a systematic one), report it and 🛑 **stop expanding scope** — don't hand-triage every row a broken gate mis-bucketed. State the finding, propose the fix, and wait; a fixed gate re-buckets everything via `--regate` for free, so per-row investigation ahead of the fix is wasted spend. Narrate what you're doing and roughly what it costs as you go — the user cannot see your tool calls' output and should never have to wonder whether you're producing value or looping.

## Hard rules

- Never `git commit`, never `make push` — both are the user's call, always.
- Don't edit Worklist.md except via `reconcile_worklist.py` stamping.
- Treat every IPDB note as a recall aid to vet against the full source, not authority.
