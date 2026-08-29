# 0286 / 0287 — External credits and tags, source-attributed

The companion to [`0284-external-field-backfill`](../0284-external-field-backfill/README.md): same scope, same attribution reasoning, for the content that is not a scalar field.

| patch                      | attribution | models | members    |
| -------------------------- | ----------- | ------ | ---------- |
| `0286-opdb-model-tags`     | `opdb`      | 2      | 2 tags     |
| `0287-ipdb-model-credits`  | `ipdb`      | 7      | 14 credits |

Credits are `art` ×7 and `design` ×7 — Jeremy Packer on art throughout, Jack Danger designing the Foo Fighters and Uncanny X-Men machines, Brian Eddy designing Venom. Tags are `limited-edition` on `predator-trophy-edition` and `sonic-the-hedgehog-collectors-edition`.

## Credits are cited, tags are not

IPDB's credit block is the pinball cataloguing standard and a deliberate exception to preferring primary sources, and its page is citable — so each credit rides its own changeset quoting the line that names it (`Design by: Jack Danger`). One quote, one credit, checkable on its own. All 14 verified.

OPDB has no citable page, so the tag rows carry the same `From the OPDB API.` note 0284 uses. A `tag` is a relationship member and not among the alias namespaces exempt from `note-required`, so a note is required rather than optional.

## Scope

The models whose external id was written by 0281/0283, read from `patch_claims`. Four credits sit just outside and stay there: `venom-limited-edition` and `venom-premium` were IPDB-linked before this pass, so their missing credits fall under the same "already ingested, or skipped for an unrecorded reason" rule that governs 0284.

## What the checks hold

Every credit's person and role must already resolve — the layer reports an unmatched person separately (`ipdb-person-unmatched`) and such a row must never reach a patch as a silent NULL. `cb_checks` also refuses an ambiguous person (more than one catalog match), an unmapped role label (which would make the credit unquotable), and any member the model already carries, since a member that is already present is a no-op and an entry whose only effect is a no-op is rejected at apply.

## Re-running

Like 0284, the already-present checks **fail by design** once these patches are applied. Regenerating requires a database restored to before 0286.
