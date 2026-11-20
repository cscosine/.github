---
name: cs-local-status
description: The state of a local cscosine workspace: every repository cloned in it (and optionally the libraries and forks the projects check out), with branch, ahead / behind GitHub, uncommitted changes, latest tag. Use when the user asks what is out of date, unpushed or uncommitted locally, before a release train or a multi-repository change, or to tidy a workspace.
---

# Local workspace status

The cscosine repositories are cloned side by side in one folder of the user's choice (nothing manages it). This
reads every clone found there; it changes nothing.

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/cs-local-status/scripts/local_status.sh [<folder>] [--inner] [--no-fetch]
```

- `<folder>`: default, the parent folder of the current repository.
- `--inner`: also the clones the projects make in their `workspace/` folder (the libraries of csfoundation /
  csoptimization, the forks of third_party_base_libs, opencv).

Read the result as:

- `-N` behind: `git pull --ff-only` (ask first if the clone has local changes).
- `+N` ahead: local commits not on GitHub: show them (`git log @{u}..`) and ask before pushing.
- `dirty`: uncommitted changes: show `git status`, never discard them without asking.
- `no upstream`: a local branch without a GitHub counterpart (e.g. a branch renamed or deleted on GitHub): check
  whether its commits exist anywhere else (`git rev-list <branch> --not --remotes --tags`) before deleting it.
