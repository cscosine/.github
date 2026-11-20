# Working on cscosine repositories

How changes move in the cscosine repositories, with the commands for each case. GitHub shows this file in every
repository that has none of its own.

## The model in one table

| Branch | What it is | How it changes |
|---|---|---|
| `main` | The last release; every commit on it is tagged `vX.Y.Z` | **Only through a pull request from `dev`** (the release) |
| `dev` | Integration; kept green; what the other repositories build against | Direct pushes are fine; never force pushed, never deleted |
| `feature/<topic>`, `fix/<topic>` | Work in progress | Anything goes (push, force push, rebase); deleted after the merge |

Tags: `vX.Y.Z` (and `vX.Y.Z-cs.N` in the forks) are permanent: they cannot be moved or deleted. Release candidates
`vX.Y.Z-rcN` can be deleted, never moved: a broken rc gets the next number.

GitHub enforces all of this. A refused push looks like:

```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Changes must be made through a pull request.
```

## What a pull request is

A pull request (PR) is a request to merge one branch into another, kept on GitHub: the list of commits, the diff,
the CI results and a description. Here it is used for one thing that must not go wrong (a release into `main`) and,
optionally, to record or discuss a larger change into `dev`. With the GitHub CLI (`gh`) it is two commands:
`gh pr create` opens it, `gh pr merge` merges it.

## Scenarios

### 1. A small change

```bash
git switch dev && git pull --ff-only
# edit, test locally
git commit -am "[area] What changes and why"
git push                                  # CI runs on dev
```

### 2. A larger change: a feature branch

```bash
git switch -c feature/better-tracking dev
# commit as often as you like; rewrite freely (rebase -i, commit --amend, push --force)
git push -u origin feature/better-tracking
gh workflow run <workflow> --ref feature/better-tracking   # CI on the branch (or: Actions tab → Run workflow)
```

When it is green, tidy the history (squash the "wip" commits), then either:

```bash
# a) merge it yourself
git switch dev && git pull --ff-only
git merge --no-ff feature/better-tracking -m "Merge feature/better-tracking: what it brings"
git push && git push origin --delete feature/better-tracking

# b) or through a PR, to keep a record / ask for a review
gh pr create --base dev --title "Better tracking: what it brings" --body "Why, what changed, how it was tested"
gh pr merge --merge --delete-branch       # merge commit, branch deleted
```

### 3. A change across several repositories

Example: csVisOpenGL needs a change for csImgTracker.

1. The **same branch name** everywhere: `feature/<topic>` in csVisOpenGL, csfoundation, csImgTracker.
2. The repository that builds the others (here csfoundation) points to the providers' `feature/<topic>` in one
   extra commit, runs its CI on the branch (scenario 2), and drops that commit before merging.
3. Merge into `dev` **in the release-chain order** (csVisOpenGL, then csfoundation, then csImgTracker), each `dev`
   green before the next; a new rc where the next repository needs one.

### 4. A release candidate

```bash
git switch dev && git pull --ff-only     # dev green on CI
git tag v1.4.0-rc1 && git push origin v1.4.0-rc1   # the release job publishes a pre-release
```

### 5. A release

```bash
gh pr create --base main --head dev --title "Release v1.4.0" --body "What is in it (or: the CHANGELOG section)"
# CI runs on the PR; when green:
gh pr merge --merge                      # keep dev: no --delete-branch
git fetch origin
git tag v1.4.0 origin/main && git push origin v1.4.0       # the release job publishes the release
git switch dev && git merge --ff-only origin/main && git push   # dev level with main again
```

### 6. Mistakes

| What happened | What to do |
|---|---|
| A bad commit is on `dev` | `git revert <sha>` and push (history on `dev` is never rewritten) |
| Pushed to `main` by mistake | Refused by GitHub: push to `dev` instead, or open a release PR |
| A broken release candidate | `gh release delete v1.4.0-rc1 --cleanup-tag`, fix on `dev`, tag `v1.4.0-rc2` |
| A broken stable release | Cannot be moved or deleted: fix on `dev`, release `v1.4.1` |
| `dev` really must be rewritten (rare) | Ask a maintainer: the rule is switched off for that operation, then on again |
| A feature branch got messy | It is yours: `git rebase -i`, `git push --force-with-lease` |

## Commits and pull requests

- A commit message says **what** and **why**; its first line stands on its own (`[area] Short summary`).
- Docs and comments describe the present; history belongs in commit messages and `CHANGELOG.md`.
- A user-visible change gets a `CHANGELOG.md` entry; a new behaviour gets a test.
- Generated files (CI workflows, presets, `dependencies/`) are regenerated, never edited by hand.
- PR labels feed the release notes: `feature`, `fix`, `breaking`, `ci`, `docs`.
