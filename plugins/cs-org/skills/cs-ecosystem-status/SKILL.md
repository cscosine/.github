---
name: cs-ecosystem-status
description: The state of the whole cscosine organisation: every repository (private too), versions, dependencies and what needs attention (providers pinned behind their latest release, csCMake behind, unreleased commits, stable off a final, forks with newer upstream releases, red main CI, stale branches). Use when the user asks what is out of date, what to release next, the state of the ecosystem, or to refresh ECOSYSTEM.md.
---

# Ecosystem status

`ECOSYSTEM.md` in the private `cscosine/.github-private` is generated from GitHub by
`scripts/ecosystem_private.py` (a member's clone of `.github-private` next to the other repositories).

```bash
cd <workspace>/.github-private && git pull --ff-only
python3 scripts/ecosystem_private.py          # the local gh login sees the private repositories
git diff --stat ECOSYSTEM.md
```

Then:

1. Summarise the "Needs attention" list, grouped: pins and csCMake behind (a release train fixes them: propose its
   order and tags, `cs-release-train`), unreleased commits / `stable` (a release, or nothing to do), forks with a newer
   upstream (`cs-fork-sync`), red CI (read the run), stale branches (ask before deleting).
2. Commit `ECOSYSTEM.md` only when the user asks ("ECOSYSTEM.md regenerated").

The public counterpart (the organisation page) is regenerated nightly by the `ecosystem` workflow of
`cscosine/.github`. The nightly run of the private one (`.github/workflows/ecosystem.yml` of `.github-private`)
needs Actions minutes for private repositories and the repository secret `ACTIONS_ORG_ACCESS`.
