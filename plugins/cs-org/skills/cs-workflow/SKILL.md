---
name: cs-workflow
description: How changes move in the cscosine repositories (csCMake, csorchestrator, third_party_base_libs, csqt6, csopencvcpu, csfoundation, csoptimization, the applications, the forks). Use when committing, branching, testing a branch on CI, changing several cscosine repositories together, making a release candidate or a release, or fixing something in a hurry in a cscosine repository.
---

# The cscosine way of working

The full guide for people, with every command: `CONTRIBUTING.md` of `cscosine/.github`
(https://github.com/cscosine/.github/blob/main/CONTRIBUTING.md). This skill is what an agent needs to act on it.

## The model

- `main`: the trunk and default branch of every repository. Direct commits are fine. Never force pushed or deleted
  (GitHub refuses it; forks: `main` is rebased on an upstream sync, see `cs-fork-sync`).
- `stable`: only on the projects that release (csCMake, csorchestrator, csWiki, third_party_base_libs, csqt6,
  csopencvcpu, csopencvcuda, csfoundation, csoptimization, csImgTracker, csSkiTracker): the last final release, only
  fast-forwarded to a final tag (`git push origin vX.Y.Z:stable`). Never commit on it.
- `feature/<topic>`, `fix/<topic>`: work in progress, free to rewrite; deleted after the merge.
- Releases are tags on `main` commits: `vX.Y.Z-rcN` (pre-release, deletable, never moved), `vX.Y.Z` (final, never
  moved or deleted). Forks: `vX.Y.Z-cs.N`. The opencv fork: `main` + `cpu` / `cuda` branches, tags
  `v<opencv>-cpu.N` / `-cuda.N`; csopencvcpu's releases follow its fork tag (`v5.0.0-cpu.1`, `-rcN`).
- Outer projects (they have CI and release) build inner repositories (first-party libraries, forks: no CI of their
  own). A change to an inner repository is tested through its outer project.

## Rules for an agent

- Leave changes unstaged for review and summarise; commit only when the user says so, push only when asked.
- Ask before anything irreversible or visible to others: tags, releases, deleting branches, force pushes, settings.
- Never edit generated files: the CI workflow (`./<name>_project.py generate-github-workflow`), presets
  (`cscmake-generate-presets`), `dependencies/`. Change the source, regenerate, commit both.
- Commit with the repository's `.venv` active (the pre-commit hooks need it); if a hook regenerates a file (e.g.
  `.vscode/launch.json`), add it and commit again.
- Do not run the CI matrix locally; one host build is enough.

## Procedures

| Task | Do |
|---|---|
| Small change | Commit on `main`, push: CI runs on `main` |
| Larger change | `feature/<topic>` from `main`; CI on demand: `gh workflow run <name>.yml --ref feature/<topic>`, `gh run watch`; when green, `git merge --no-ff` into `main` (or a PR) |
| Change across repositories | Same `feature/<topic>` in each; the outer recipe points to the inner `feature/<topic>` on its own feature branch; merge inner first, set the recipe back to `main`, merge the outer; release-chain order: csorchestrator, csCMake → third_party_base_libs → csqt6, csopencvcpu → csfoundation → csoptimization → applications |
| Release candidate | Tag `vX.Y.Z-rcN` on a `main` commit, push the tag: the tag build publishes a pre-release |
| Several projects in a row | `cs-release-train` (one build at a time, GitHub runner limits) |
| Final release | Tag `vX.Y.Z` on the chosen commit (usually the last rc), push it; `git push origin vX.Y.Z:stable` |
| In a hurry | Commit on `main`, push, cancel the `main` run (`gh run cancel <id>`), tag, push the tag: one build is the test and the release. A failed final tag: fix and tag the next patch |
| Bad commit on `main` | `git revert`, never rewrite |
| Broken rc | `gh release delete vX.Y.Z-rcN --cleanup-tag`, fix, tag the next rc |

## Pitfalls seen

- Creating or renaming a branch counts as a push: it starts builds with whatever workflow the branch has. Cancel the
  runs that are not wanted (`gh run list`, `gh run cancel`).
- A job cancelled with no runner assigned and no steps is GitHub capacity (macOS 26 runners), not the build:
  re-run the failed jobs (`gh api -X POST repos/cscosine/<repo>/actions/runs/<id>/rerun-failed-jobs`).
- A recipe pinning a branch of an inner repository builds whatever that branch is at build time: an exact rebuild of
  a release comes from its tags and its manifest, not from re-running a branch build.
