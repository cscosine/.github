# Working on cscosine repositories

How changes move in the cscosine repositories, with the commands for each case. GitHub shows this file in every
repository that has none of its own.

## The model in one table

| Branch | Where | What it is | How it changes |
|---|---|---|---|
| `main` | every repository (the default branch) | The trunk: the latest work, kept green | Direct pushes are fine; never force pushed, never deleted |
| `stable` | the projects that release (not the libraries and forks they build) | The last final release | **Only fast-forwarded to a final release tag**; never force pushed, never deleted |
| `feature/<topic>`, `fix/<topic>` | any | Work in progress | Anything goes (push, force push, rebase); deleted after the merge |

Releases are tags on commits of `main`: `vX.Y.Z-rcN` (release candidates) and `vX.Y.Z` (final). A final tag is
permanent: it cannot be moved or deleted. A release candidate can be deleted, never moved: a broken rc gets the next
number. Forks tag `vX.Y.Z-cs.N` (the upstream version, our patch level).

GitHub enforces only what cannot be undone: no force push or deletion of `main` / `stable`, final tags never moved or
deleted. A refused push looks like:

```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Cannot force-push to this branch
```

Everything else here (a feature branch, waiting for CI before tagging, a release candidate first, a pull request) is
good practice: skip it when in a hurry (scenario 6).

CI builds `main` on every push and every week (the latest code on the latest runner images), and every tag (the
release). A feature branch is built on demand. `stable` is never built: it only receives commits already built.

## Versions

Every repository declares its version: `version` in `pyproject.toml` (tools, distributions, applications),
`project(... VERSION x.y.z)` in the top `CMakeLists.txt` (libraries, copies). A tag `vX.Y.Z-rcN` or `vX.Y.Z` needs that
version to be `X.Y.Z` already.

- **When**: the first commit after a release that changes the repository also bumps the version (and opens the
  `## vX.Y.Z (unreleased)` section of `CHANGELOG.md`, where there is one). Not right after a release: the level is not
  known yet, and a repository that does not change keeps its version and is not released again. A later change that
  needs a higher level raises it before the first rc (patch → minor).
- **Which number** ([semantic versioning](https://semver.org)):

  | The change | From 1.0.0 | Before 1.0.0 (0.x) |
  |---|---|---|
  | Breaking: a consumer must change (removed or renamed API, changed behaviour) | major (1.4.2 → 2.0.0) | minor (0.1.3 → 0.2.0) |
  | A new feature, compatible | minor (1.4.2 → 1.5.0) | patch (0.1.3 → 0.1.4) |
  | A fix | patch (1.4.2 → 1.4.3) | patch (0.1.3 → 0.1.4) |

- **Exceptions**: a distribution of a third-party product carries its version plus a level of ours: csqt6
  `vX.Y.Z-cs.N` (the Qt version; `-cs.N` for each rebuild with changes of ours, none on the first build); csopencvcpu /
  csopencvcuda add their level as a suffix (`v5.1.0-cpu.3` → `-cpu.4`); forks follow upstream (`vX.Y.Z-cs.N`, `N` + 1
  for each change of ours).
- **Checked**: ECOSYSTEM.md flags a repository with commits on `main` since its last final tag whose version is still
  that tag's (not the distributions versioned by their upstream product: their level is in the tag).

## What a pull request is

A pull request (PR) is a request to merge one branch into another, kept on GitHub: the list of commits, the diff,
the CI results and a description. Here it is optional: to record or discuss a larger change into `main`. With the
GitHub CLI (`gh`) it is two commands: `gh pr create` opens it, `gh pr merge` merges it.

## Scenarios

### 1. A small change

```bash
git switch main && git pull --ff-only
# edit, test locally
git commit -am "[area] What changes and why"
git push                                  # CI runs on main
```

### 2. A larger change: a feature branch

```bash
git switch -c feature/better-tracking main
# commit as often as you like; rewrite freely (rebase -i, commit --amend, push --force)
git push -u origin feature/better-tracking
gh workflow run <workflow> --ref feature/better-tracking   # CI on the branch (or: Actions tab → Run workflow)
gh run watch
```

When it is green, tidy the history (squash the "wip" commits), then either:

```bash
# a) merge it yourself
git switch main && git pull --ff-only
git merge --no-ff feature/better-tracking -m "Merge feature/better-tracking: what it brings"
git push && git push origin --delete feature/better-tracking

# b) or through a PR, to keep a record / ask for a review
gh pr create --base main --title "Better tracking: what it brings" --body "Why, what changed, how it was tested"
gh pr merge --merge --delete-branch       # merge commit, branch deleted
```

### 3. A change across several repositories

Example: csVisOpenGL needs a change for csImgTracker.

1. The **same branch name** everywhere: `feature/<topic>` in csVisOpenGL, csfoundation, csImgTracker.
2. The repository that builds the others (here csfoundation) points to csVisOpenGL `feature/<topic>` in its recipe, on
   its own `feature/<topic>`; CI on demand (scenario 2).
3. Merge **in the release-chain order**: csVisOpenGL into its `main`; csfoundation's recipe back to `main`, merged; a
   release candidate where the next repository needs one; then csImgTracker.

### 4. A release candidate

```bash
git switch main && git pull --ff-only     # main green on CI
git tag v1.4.0-rc1 && git push origin v1.4.0-rc1   # the release job publishes a pre-release
```

### 5. A release

```bash
git tag v1.4.0 v1.4.0-rc2 && git push origin v1.4.0   # on the commit of the last rc: the release job publishes it
git push origin v1.4.0:stable                          # stable fast-forwards to the release
```

### 6. In a hurry: a one-line fix, released in one build

```bash
git switch main && git pull --ff-only
# the fix
git commit -am "[area] The fix" && git push       # (cancel the main run in the Actions tab to save the runners)
git tag v1.4.1 && git push origin v1.4.1          # the tag build is the test and the release
git push origin v1.4.1:stable
```

If the build fails, fix and tag `v1.4.2`: a final tag is never moved. Tidy up later (a fork fix onto the shared
branch, the CHANGELOG): nothing here blocks the release.

An urgent fix of a release while `main` has work not ready to release: branch from the release tag
(`git switch -c fix/1.4.1 v1.4.0`), fix, tag `v1.4.1` there, fast-forward `stable` to it, then merge the branch into
`main`.

### 7. Mistakes

| What happened | What to do |
|---|---|
| A bad commit is on `main` | `git revert <sha>` and push (history on `main` is never rewritten) |
| A broken release candidate | `gh release delete v1.4.0-rc1 --cleanup-tag`, fix on `main`, tag `v1.4.0-rc2` |
| A broken final release | It cannot be moved or deleted: fix on `main`, release `v1.4.1` |
| `main` really must be rewritten (rare) | Ask a maintainer: the rule is switched off for that operation, then on again |
| A feature branch got messy | It is yours: `git rebase -i`, `git push --force-with-lease` |

## Commits and pull requests

- A commit message says **what** and **why**; its first line stands on its own (`[area] Short summary`).
- Docs and comments describe the present; history belongs in commit messages and `CHANGELOG.md`.
- A user-visible change gets a `CHANGELOG.md` entry; a new behaviour gets a test.
- Generated files (CI workflows, presets, `dependencies/`) are regenerated, never edited by hand.
- PR labels feed the release notes: `feature`, `fix`, `breaking`, `ci`, `docs`.
