---
name: cs-fork-sync
description: Maintain the cscosine forks of third-party libraries (eigen3, fmt, cpptrace, libassert, magic_enum, Catch2, tl-expected, tl-optional, opencv, ...): see where each is against upstream, sync a fork with a new upstream release, add or drop a patch, keep cscosine/README.md and CHANGELOG.md right. Use when the user asks to update a third-party library, sync a fork, check for new upstream versions, or change a patch of a fork.
---

# Forks of third-party libraries

## The model

- A fork's `main` = an upstream release tag + our commits on top, one commit per reason. `git log <base>..main` is
  the list of our changes. The upstream tag is in the fork too.
- `cscosine/README.md` (ours, upstream never touches it): upstream URL, base tag, a table of our commits with **why**,
  the license. `cscosine/CHANGELOG.md`: one entry per release of ours.
- Our releases: `v<upstream version>-cs.<n>` (the opencv fork: `-cpu.<n>` / `-cuda.<n>`, with `main` = the common stack
  and `cpu` / `cuda` = one setup commit each). Tagged once an outer project (third_party_base_libs, csopencvcpu) has
  built the commit.
- GitHub Actions is disabled on the forks: upstream's `.github/` stays as it is.
- `main` of a fork can be force pushed (only for a sync); deleting it is refused.
- tclap, NamedType, fmt-eigen are copies of our own (no syncs): their `cscosine/README.md` says where they came from.

## See where the forks are

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/cs-fork-sync/scripts/fork_status.py <workspace>/third_party_base_libs/workspace/*
```

It prints the base, our commits and the newer upstream releases of each fork.

## Sync a fork with a new upstream release

In the fork's clone (`<workspace>/third_party_base_libs/workspace/<fork>`, or `csopencvcpu/workspace/opencv`):

```bash
git fetch <upstream url>.git refs/tags/<new>:refs/tags/<new>
git switch -c sync/<new> main
git rebase --onto <new> <old base> sync/<new>        # our commits onto the new release
```

- Drop the commits upstream has absorbed (`git rebase -i`); keep each remaining one atomic, its message saying why.
- Update `cscosine/README.md` (base tag, the table of commits) and `cscosine/CHANGELOG.md` (`v<new>-cs.1`, to tag once
  built), in a commit of their own.
- Test through the outer project: on a `feature/<fork>-<new>` branch of third_party_base_libs, the recipe's ref for
  that fork set to `sync/<new>`; CI on demand (`gh workflow run third_party_base_libs.yml --ref feature/...`).
- Green: `git push --force-with-lease origin sync/<new>:main` (the fork's `main` moves to the new stack), the outer
  recipe back to `main`, merged; tag the fork `v<new>-cs.1` once the outer release built it (`cs-release-train`,
  `tag_inner`).
- opencv: rebase `main` first, then `cpu` and `cuda` on the new `main` (`git rebase --onto main <old main> cpu`).

## Add or drop a patch

A commit on the fork's `main` (or a feature branch, tested as above), a row in `cscosine/README.md`, a line in the
CHANGELOG under the next `-cs.<n>`. A generic fix is also proposed upstream: one patch less at the next sync.

## Clean up a fork's history (done once for the forks of 2026-11)

Tag the old `main` (`-cs.1`, what the outer project built), rebuild `main` from the upstream tag with one commit per
real change (files taken from the old `main`: `git checkout <old> -- <files>`), add `cscosine/`, check that the new
tree differs from the old one only where intended (`git diff --stat <old> main`), force push with lease.
