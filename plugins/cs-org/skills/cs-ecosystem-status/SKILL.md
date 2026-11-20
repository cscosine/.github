---
name: cs-ecosystem-status
description: The state of the whole cscosine organisation: every repository, versions, dependencies and what needs attention (providers pinned behind their latest release, csCMake behind, unreleased commits, stable off a final, forks with newer upstream releases, red main CI, stale branches). Use when the user asks what is out of date, what to release next, the state of the ecosystem, or to refresh ECOSYSTEM.md.
---

# Ecosystem status

`ECOSYSTEM.md` of `cscosine/.github` is regenerated nightly from GitHub by `scripts/ecosystem_report.py` (workflow
`ecosystem`, which also regenerates the projects section of the org page). Read it on GitHub, or refresh it locally:

```bash
cd <workspace>/.github && git pull --ff-only
python3 scripts/ecosystem_report.py
git diff --stat ECOSYSTEM.md
```

Or run the workflow now: `gh workflow run ecosystem.yml -R cscosine/.github`.

Then summarise the "Needs attention" list, grouped:

- pins and csCMake behind: a release train fixes them (`cs-release-train`): propose its order and tags;
- unreleased commits on `main`, `stable` off a final: a release, or nothing to do yet;
- forks with a newer upstream release: `cs-fork-sync`;
- red CI on `main`: read the run (`gh run view <id> --log-failed`);
- stale branches: ask before deleting.

Commit a locally regenerated `ECOSYSTEM.md` only when the user asks.
