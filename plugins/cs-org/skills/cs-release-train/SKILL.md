---
name: cs-release-train
description: Release several cscosine projects in a row (a release train): third_party_base_libs, csqt6, csfoundation, csopencvcpu, csoptimization, csImgTracker, csSkiTracker, one build at a time, each pinning the releases of the previous ones. Use when the user asks to rebuild or release the chain, to propagate a csCMake / provider release to the projects, or to make release candidates or final releases of several cscosine projects.
---

# Release train

A train runs the projects in the release-chain order, **one build at a time** (GitHub's runners are limited; a
project needs the previous one's release anyway): third_party_base_libs → csqt6 → csfoundation → csopencvcpu →
csoptimization → csImgTracker, csSkiTracker. Rules of the releases: the `cs-workflow` skill.

## 1. Prepare (the user reviews before anything is pushed)

For each project, in its clone (`<workspace>/<repo>`, on `main`, clean):

- the recipe: the csCMake version (`cscmake_version` in `<repo>_project.py`), the providers' tags
  (`release_tag=` / `project_version=` in `<repo>_config.py`), the project version when it changes (`version=` in
  `<repo>_project.py`, `pyproject.toml`, `CMakeLists.txt` of the applications);
- the tags the train will push: they are known in advance (next rc of each project), so the consumers can pin them
  before the providers are released.

Do not regenerate the workflows of projects whose providers are not released yet: generating downloads the
providers' manifests. The script regenerates each one when its turn comes.

A project whose inputs did not change (e.g. csqt6 when only its workflow was regenerated): commit with `[skip ci]` in
the message and give it no tag (push only).

## 2. The plan file

Write `plan.json` next to a scratch folder (format in `scripts/release_train.py`'s docstring): one step per project,
`tag` (or `null` for push only), `commit_message` (when the script must regenerate and commit), and `tag_inner` for
a project whose inner repositories get tags on the commits it built (third_party_base_libs: the forks `-cs.N`;
csfoundation / csoptimization: the libraries, their own versions).

## 3. Run

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/cs-release-train/scripts/release_train.py plan.json --dry-run
python3 ${CLAUDE_PLUGIN_ROOT}/skills/cs-release-train/scripts/release_train.py plan.json | tee train.log
```

Run it in the background (hours: OpenCV takes about two) and watch the log for `OK`, `FAIL`, `re-running`,
`TRAIN DONE`. Report each project as it is released.

## 4. When it stops

- `FAIL ... cancelled` with jobs that never got a runner: already re-run 3 times; re-run later
  (`gh api -X POST repos/cscosine/<repo>/actions/runs/<id>/rerun-failed-jobs`), then start the script again: it resumes
  at the step whose tag exists.
- A real build failure: read the failed job's log (`gh run view <id> --log-failed`), fix on `main`, delete the rc
  (`gh release delete <tag> --cleanup-tag`; nothing was published if the run failed), use the next rc number in the
  plan, run again. A final tag cannot be deleted: use the next patch version.
- Before the train: runs started by branch operations (creating / renaming branches) hold the runners; cancel them.
