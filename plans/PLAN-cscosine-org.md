# Plan: organising cscosine: templates, rules, skills, GitHub practices

Date: 2026-11-20 · Status: **approved**, in progress (S0, S1b done; S3 adopted, Renovate next) · Related: `done/PLAN-stable-dev-ubuntu26mac-libs.md` (done),
`done/PLAN-review-stable-dev.md` (S1b), `PLAN-csorchestrator-architecture.md` (to approve), `../TODO.md`

Goal: every repository of the organisation looks the same, is created and updated from one template, follows the
same process (branches, PRs, CI, releases), and an agent can work in any of them, or across several, with the right
rules and skills loaded. One place says what exists, how it depends on what, and at which version.

---

## 0. Summary

| Topic | Today | Target |
|---|---|---|
| Project structure | Similar by copy: 4 variants of `setup.sh`, 6 of `.pre-commit-config.yaml`, 11 different `pyproject.toml` for 11 repositories | One Copier template, `kind` per repository; `copier update` brings every repository to the new version; Renovate opens the PRs |
| Ownership of files | Implicit | Every file has one owner: the template, a generator (csCMake presets, csorchestrator workflow), or the project |
| Plans | Not versioned: the `PLAN-*.md` live only on this disk | In `.github` (`plans/`), with the generated overview and the org admin scripts (GitHub API only); no new repository |
| Agent rules | Per repository (`AGENTS.md` + `CLAUDE.md` in csCMake; `.agents/skills/` in 5 repositories, which Claude Code does not read) | Org rules written once in the template, so every repository carries them; process skills in a public plugin; usage skills next to the code |
| Process | Direct pushes to `dev` / `main`, no PRs, no protection, rc tags by hand | `main` trunk + `stable` (outer), tags for releases; only no force push / deletion enforced; multi-repo changes with one branch name and one plan step |
| Overview and versions | In heads, partly in `../TODO.md` | Generated nightly from releases, manifests and Copier answers into `ECOSYSTEM.md` (graph, versions, drift) |
| GitHub | Free plan, issues / projects / rulesets unused | Rulesets on public repositories, PR templates, release notes from PRs, Dependabot / Renovate, progress tracked in the plans themselves (no issues); Team plan only if the private libraries must be protected |

**Recommended order**: S0 (plans into `.github`, rules, GitHub settings; then the repositories going public) → finish stable-dev → csorchestrator
R0 → Copier template "base" layer → csorchestrator R1… → template layers for csCMake / csorchestrator projects once
R4 has fixed the project API. Details in §8.

---

## 1. Inventory: kinds of repository

The 37 repositories of the organisation fall into a few kinds; the template, the rules and the overview all key on it.

| Kind | Repositories | Built with | Visibility |
|---|---|---|---|
| `tool` (Python package) | csCMake (Python + CMake), csorchestrator, csWiki | pyproject, pytest, own CI | public |
| `distribution` (recipe, no own sources: builds and releases other repositories) | third_party_base_libs, csqt6, csopencvcpu, csopencvcuda, csfoundation, csoptimization | csorchestrator | public |
| `library` (first-party C++) | csCore, csLie, csCamera, csVisOpenGL (in csfoundation); csNelson, csBlockMatrix (in csoptimization) | csCMake | private → **public** for the csfoundation ones (decided 2026-11-20); csNelson, csBlockMatrix stay private until mature |
| `application` (own sources + recipe) | csImgTracker, csSkiTracker | csCMake + csorchestrator | public |
| `fork` (branch `cs-main` / `main-original`) | fmt, Catch2, eigen3, libassert, cpptrace, magic_enum, tl-*, tclap, NamedType, fmt-eigen, pipes, opencv, opencv_contrib | upstream build, CMake patches | public (eigen3 private → **public**, decided 2026-11-20) |
| `meta` | .github (org page, plans, rules, licensing, overview, admin scripts, plugin marketplace) | — | public |
| legacy | csProjectManager, csMetaProjectAll, csVis | — | private: **archive** (read-only, still visible). csOrchestratorTestRepo stays: used by csorchestrator tests |

Observations:

- `library` repositories are checked out by their distribution under `csfoundation/workspace/` and
  `csoptimization/workspace/`; nothing else needs to clone them.
- pipes is dropped by stable-dev (its §1, last row): archive the fork when done.
- `kind` becomes a Copier answer; the list of repositories by kind is `scripts/github-settings.json` in
  `.github` (no GitHub topics: they would repeat it).

---

## 2. Templates with Copier

### 2.1 Why Copier

Copier keeps the answers and the template version in `.copier-answers.yml`; `copier update` re-applies the newer
template as a three-way merge (the project's changes are kept, conflicts shown inline). This is the property that
matters: not creating projects (rare), but **keeping 20 repositories aligned** as the shared files evolve. Cookiecutter
cannot update; a GitHub "template repository" copies once.

### 2.2 One template, `kind` as a question

One repository `cscosine/cs-project-template`, tagged (`v1.0.0`, …; Copier uses tags to know what to update to),
with:

```yaml
# copier.yml (sketch)
_subdirectory: template
_min_copier_version: "9.4"
project_name: { type: str }
kind: { type: str, choices: [tool, distribution, library, application] }
languages: { type: str, choices: [python, cpp, cpp+python], default: "{{ 'python' if kind == 'tool' else 'cpp+python' }}" }
visibility: { type: str, choices: [public, private] }
python_min: { type: str, default: "3.11" }
use_cscmake: { type: bool, default: "{{ kind in ['library', 'application'] }}" }
use_csorchestrator: { type: bool, default: "{{ kind in ['distribution', 'application'] }}" }
_skip_if_exists: [README.md, "{{ project_name }}_project.py", CMakeLists.txt, src/**]
_tasks: [ "git init -b dev", "./setup.sh --no-venv-prompt" ]
```

Layers are Jinja conditions in the template (files named `{% if use_cscmake %}CMakePresets.json{% endif %}.jinja`), not
separate templates: one answers file, one `copier update` per repository. Several Copier templates per project are
possible (one answers file each) but double the maintenance; not worth it at this size.

### 2.3 Who owns which file

The rule that makes updates safe: **one owner per file**, written in the template's README and in the repository
rules.

| Owner | Files | Edited by hand? |
|---|---|---|
| Template (Copier) | `setup.sh` / `.ps1`, `open-code.*`, `.gitattributes`, `.gitignore`, `.pre-commit-config.yaml`, `conftest.py`, tool sections of `pyproject.toml` (ruff, mypy, pytest, import-linter skeleton), `.github/` (PR template, `release.yml`, `dependabot.yml`, the CI of `tool` repositories), `AGENTS.md`, `CLAUDE.md` (org part: **the org rules of §4, whose only source is the template**), `.claude/settings.json`, `LICENSE`, `CITATION.cff` | No: change the template, then `copier update` |
| Template, created once | `README.md`, `<name>_project.py`, `CMakeLists.txt`, `src/`, `tests/` skeletons, `TODO.md` | Yes, after creation (`_skip_if_exists`) |
| csCMake | `CMakePresets.json` (generated), `csCMakeProjectSetup.json` (`cscmake-generate-presets`) | No |
| csorchestrator | `.github/workflows/<name>.yml`, `dependencies/*` | No: regenerate |
| Project | Sources, project section of `pyproject.toml`, `CLAUDE.md` project section | Yes |

Mixed files (`pyproject.toml`, `CLAUDE.md`) keep a template part and a project part; Copier's merge handles that well
as long as the project part stays in its own section.

### 2.4 What goes into the template first

Only what is already shared and stable: the files whose drift was measured (`setup.sh`, `open-code.*`, pre-commit,
`.gitattributes`, `.gitignore`, `conftest.py`, the tool sections of `pyproject.toml`), plus the new `AGENTS.md` /
`CLAUDE.md` / PR template / `release.yml`. Adopting the template in an existing repository: `copier copy --overwrite`
on a branch, review the diff, keep what the project really needs as project parts, PR.

The csCMake and csorchestrator layers (`CMakeLists.txt` skeleton, `<name>_project.py`, `*_config.py`) wait for
csorchestrator R4: the project API changes (`Project` / `Repo` / `Provider`, `*_config.py` dropped) and the template
would have to be written twice.

### 2.5 Keeping it updated

- Renovate has a Copier manager: it sees a new template tag and opens a PR "update template to vX" in every
  repository (running `copier update`). Dependabot does not know Copier. Renovate also bumps GitHub Actions and,
  with a regex manager, the `release_tag="v…"` pins of the recipes until csorchestrator R3 gives a lock file.
- The template has its own CI: render every `kind`, run `setup.sh` + pre-commit + tests on the result.
- csCMake today ships `templates/` (CMake config / env templates): those are csCMake's own runtime templates, not
  project templates; they stay.

---

## 3. Where plans and org-level files live

One public repository, `cscosine/.github` (decided 2026-11-20: no private repository, `.github` retired):

| Content | Where |
|---|---|
| The public org page | `profile/README.md` (its projects section generated nightly, §6) |
| Plans and their progress | `plans/` (`plans/README.md` the index, `plans/done/` when finished) |
| Rules of every repository | Not here: `cs-project-template` (`template/.claude/cscosine-rules.md`, imported by each `CLAUDE.md`), their only source since 2026-11-21 (`rules/` removed) |
| How changes move | `CONTRIBUTING.md` (GitHub shows it in every repository without its own) |
| Licensing | `LICENSING.md` (the policy), `plans/PLAN-licensing.md` (open points) |
| The full state of the ecosystem | `ECOSYSTEM.md` (generated nightly, §6) |
| Org admin | `scripts/` (GitHub settings and rulesets, the generators) |
| Agent skills | the Claude Code plugin marketplace, plugin `cs-org` (§5.2) |
| Logo and avatars | `assets/` |

It is a plain repository cloned next to the others when needed; it does not clone, list or inspect the local folders,
it only reads GitHub. The folder holding the clones (here `myWorkspace/`) stays a plain folder. Every repository is
public; a repository made private later appears in the overview with a 🔒.

### 3.1 What someone who clones only one project gets

| Need | Comes from | Needs `.github` cloned? |
|---|---|---|
| Org rules (branches, PRs, generated files, commits, ways of working) | The template-owned part of the project's `CLAUDE.md` / `AGENTS.md`, kept current by `copier update` | No |
| Skills (process, csCMake, csorchestrator, the libraries it uses) | Plugins of the public marketplace, declared in the project's `.claude/settings.json` (§5.2) | No |
| Build, run, CI | `setup.sh`, csorchestrator (pinned), released providers downloaded | No |
| Working on a library the project uses | Today the release chain; later a local release store in csorchestrator (§4.7) | No |
| Multi-repo PRs, releases, release trains | Skills of the `cs-org` plugin, calling `git` / `gh` in the repositories involved | No |
| Plans, overview of the organisation | `.github` (or read on GitHub) | To edit them |


### 3.1b How a member works

Convention, not tooling: **clone what you work on, side by side in one folder of your choice**. Nothing manages that
folder; the cross-repository skills only look for siblings in it.

| Doing | Clone |
|---|---|
| Work on one repository (e.g. csfoundation) | That repository only: `git clone`, `./setup.sh`, start Claude Code in it. Rules come from its `CLAUDE.md`, skills from the plugins (installed by Claude Code from GitHub into `~/.claude/plugins`, not a clone to manage). Its inner libraries (csCore, …) are cloned by its own run into `workspace/`, and edited there on a feature branch |
| A change across repositories (e.g. csfoundation + csImgTracker) | Both, as siblings. `cs-multi-repo-change` finds them next to each other; one it needs and does not find, it offers to clone |
| Read or update the plans | `.github`. The status of a plan step is updated there in a small commit; when it is not cloned, the agent leaves the step id in the PR body and the update is done later |
| Develop the `cs-org` skills, the org profile, community files | `.github` |
| Develop the template | `cs-project-template` |

Nobody needs `.github` cloned to *use* the skills or to work on code.

### 3.2 Tracking progress without issues

One source of truth, so nothing has to be kept aligned: **the plans are the tracker**.

- Every roadmap table has a **Status** column (`todo` / `doing` / `done` + date / `dropped`), and steps have ids
  (`S0`, `R1`, …).
- The PR that completes a step updates its status in `.github` (for a step done in another repository: a one-line PR
  in `.github`, or the agent does it at the end of the work: rule in the org rules, done by the `cs-git-workflow`
  skill when `.github` is cloned next to the repository).
- PR bodies name the step id; `git log --grep S0` across the repositories finds the work of a step.
- `plans/README.md` (generated by a small script) lists every plan with its status line and the open steps: the
  dashboard.
- A finished plan moves to `plans/done/`; handoff notes for a single chat (like the csCMake 1.0 migration notes) are
  deleted when their work is done.

Issues and a GitHub Project become worth it with a second regular contributor, or outside users reporting bugs; then
the step ids become issues (a script can create them from the tables, one way: plan → issues).

---

## 4. Common rules (for people and agents)

Written once, in the template (the org part of `CLAUDE.md` / `AGENTS.md`), so every repository carries the same text;
enforced where possible by GitHub (§7) rather than by trust. Until the template exists (S3), they are added by hand to
each repository's `CLAUDE.md` as it is touched.

### 4.1 Branches (decided 2026-11-20)

| Branch | Where | Meaning |
|---|---|---|
| `main` | every repository, default | The trunk; built on push and weekly (schedule): catches inner changes and runner-image changes |
| `stable` | outer repositories | The last final release, fast-forwarded to each final tag; never built |
| `feature/*`, `fix/*` | any | Work; CI on demand (dispatch) |
| `cpu`, `cuda` | the opencv fork | `main` + the variant's setup |

Releases are tags on `main` commits (rc, then final); inner repositories are tagged on the commits an outer release
built. Migrated 2026-11-20 from `dev` + `main`: `dev` renamed `main`, the old `main` / `cs-main` / `main-cpu` /
`main-cuda` deleted, their unique commits kept as `legacy-*` tags.

### 4.2 Changes touching several repositories

1. One topic, **one branch name** in every touched repository (`feature/<topic>`), and the **plan step** it belongs to
   (e.g. `S0`, `R1`) in every PR body.
2. While the branch runs CI, consumers point to the providers' `feature/<topic>` (the "CI on feature/…" extra commit of
   stable-dev §2, later a `cs-workspace.local.toml` override, csorchestrator B12); dropped before merging.
3. One PR per repository, each naming the others and the plan step; **merged in dependency order** (csorchestrator, csCMake →
   third_party_base_libs → … → applications), each `main` green before the next.
4. A skill (§5, `cs-multi-repo-change`) does the branch creation, the extra commit, the PRs, the merge order.

### 4.3 Releases

1. Release candidate: tag `vX.Y.Z-rcN` on a commit of `main` (a GitHub pre-release), consumed by the other
   repositories.
2. Release: tag `vX.Y.Z` on the chosen commit (usually the last rc), `stable` fast-forwarded to it; release notes from
   the commits / PRs since the previous tag.
3. **A distribution tags what it built**: when csfoundation releases, every first-party library it built from a branch
   gets a tag on the exact commit. Proposal: each library keeps **its own semver** (`csCore v1.4.0`, from its
   `project(VERSION)`), tagged only if it changed since its last tag; the distribution manifest records library,
   version, tag and commit. Alternative: tag the libraries with the distribution's name (`csfoundation-v0.2.0`): simpler,
   but a library in two distributions gets two unrelated version lines. To decide (Q3).
4. **Refs:** a recipe names its refs explicitly: inner repositories at `main` (a `feature/*` while working on it),
   released providers by tag, csCMake by release. No per-branch tables, no build of `stable`: the weekly build of
   `main` covers both inner changes and environment drift (decided 2026-11-20, replacing the outer-`main` canary).
5. **Exact rebuilds come from tags and the manifest.** At an outer release the inner repositories are tagged on the
   commits built (libraries: their own semver, Q3; forks: `vX.Y.Z-cs.N`), and the release manifest records ref, tag and
   commit for each. Until csorchestrator records commits (its R1), the release skill tags and notes them.
6. **Builds once per commit where possible:** a tag may republish the build of its commit instead of rebuilding
   (csorchestrator plan §7c), an optimisation, not a rule.
7. A release train across repositories = the multi-repo rule (§4.2) with tags instead of merges, in dependency order;
   `cs-release-train` skill now, `csorchestrator ecosystem release` (R9) later.

### 4.4 Outer and inner repositories

csorchestrator builds and runs CI only in the **outer** project (distribution, application); the libraries and forks
it builds (**inner**) have no CI of their own. Consequences:

| | Outer (distributions, applications) and tools (csCMake, csorchestrator, csWiki) | Inner (first-party libraries, forks) |
|---|---|---|
| CI | Yes | No (built by the outer CI) |
| PR required | No (optional, to record or discuss); `main` / `stable` protected against force push and deletion | No |
| Force push / deletion of `main` (`cs-main`) | Blocked | Blocked |
| Force push on `main` | Blocked | Allowed on forks (patch stack rebased on sync, §4.6); blocked on first-party libraries |
| Stable tags (`vX.Y.Z`, forks `vX.Y.Z-cs.N`) | Immutable | Immutable (outer releases and manifests point to them) |
| Pre-release tags (`v*-rc*`, `v*-test*`) | Deletable, not movable | Deletable, not movable |

The gate for an inner change is the **outer build**: the inner change lives on `feature/<topic>`, the outer
`feature/<topic>` points to it, its CI (on demand) validates the combination; then the inner branch is merged into its
`main`, the outer recipe set back to `main`, and the outer branch merged.

### 4.5 History: clean start or not

| Repositories | Proposal | Why |
|---|---|---|
| csCore, csLie, csCamera, csVisOpenGL | Clean start **now, before they go public**, if the secret scan finds something or the history is not worth showing (88 / 98 / 26 / 40 commits on `dev`); one "Import" commit per repository or a `git filter-repo` clean-up. The old history kept in one private archived repository (`cs-history`, a branch per library) | No tags of their own, private, consumed only by csfoundation through branches: the cheapest moment there will ever be. Cost: old csfoundation rcs that recorded their commits cannot be rebuilt exactly (acceptable before 1.0; the archive keeps the commits) |
| Already public (csCMake, csorchestrator, distributions, applications, csWiki) | **No rewrite**, now or at 1.0 | Already cloned; tags and release assets record commits. The clean start at 1.0 is the `v1.0.0` tag, a CHANGELOG starting there, and deleting the old pre-releases from the Releases page if they are noise (tags can stay) |
| Forks | **Never** rewrite upstream history | Needed for syncs; our part is cleaned by the patch-stack model (§4.6) |
| csNelson, csBlockMatrix | Decide when they go public | Same reasoning as the csfoundation libraries |

Postponing to 1.0 makes every case more expensive (more consumers, more tags, public for longer).

### 4.6 Forks: syncing with upstream, our changes

Today: `cs-main` is stale (eigen3's has no common ancestor with `dev`), `dev` is an upstream release plus our commits
(csCMake setup, presets, build fixes), `legacy-*` tags mark the old bases, nothing says which upstream version a fork
is on or why each change exists.

Model: **a patch stack on an upstream tag**.

- `main` = upstream release tag `vX.Y.Z` + our commits on top, each one atomic; `git log vX.Y.Z..main` *is* the list
  of our changes. Upstream is a remote (`upstream`), its tags fetched; no copy of upstream branches.
- Sync to a new upstream release: `git rebase --onto vNEW vOLD main` (dropping patches upstream has absorbed), built
  through the outer project (a feature branch first if wanted), then `main` force-pushed (allowed on forks).
- Our versions: `vX.Y.Z-cs.N` (upstream version, our patch level), replacing `legacy-*`.
- Genuine fixes (e.g. the libassert `-Wpedantic` warning, the fmt Xcode test) also go upstream as PRs: every
  patch upstream accepts is one less to rebase.

Where things are written:

| What | Where |
|---|---|
| Per fork: upstream URL (eigen3: GitLab), base tag, the list of patches with **why**, a changelog per `-cs.N`, fork-specific sync notes | `cscosine/README.md` + `cscosine/CHANGELOG.md` **in the fork**, in a folder upstream never touches, so it never conflicts on rebase; itself a `[cs]` commit |
| The sync procedure (generic) | Once: skill `cs-fork-sync` (with a script: fetch upstream, list new tags, rebase, report dropped / conflicting patches); referenced from every fork's `cscosine/README.md` |
| Overview: fork, upstream, base version, latest upstream version, patch count, our version | `third_party_base_libs/FORKS.md`, **generated** (`git ls-remote --tags upstream` + the forks' `cscosine/README.md`); also in `ECOSYSTEM.md` (§6) as "upstream outdated" |

### 4.7 Developing a project and a library together

Example: a feature in csImgTracker that needs a change in csVisOpenGL. Today the only path is the release chain:
csVisOpenGL change → csfoundation build + rc → csImgTracker pin bumped, a loop of hours, because csImgTracker consumes
csVisOpenGL **as a binary** of a csfoundation release (`csImgTracker_config.py`, `release_tag="v0.1.0-rc9"`); the
source exists only in `csfoundation/workspace/csVisOpenGL`.

Target (two loops):

**Local loop: future, in csorchestrator, not now.** A local csorchestrator run already produces a release (archives,
manifest, deploy folder). The plan: csfoundation run locally with only csVisOpenGL selected, deployed to a **local
release store**; csImgTracker takes csVisOpenGL from that store (manual selection in a git-ignored
`cs-workspace.local.toml`, warned at every run, refused in CI and releases) and everything else from the GitHub
release; later a csorchestrator TUI / GUI composes such multi-project runs. It reuses the provider's own recipe, so no
second way to build a library. Written in `PLAN-csorchestrator-architecture.md` §8 (parking lot), not scheduled.

Until then: the outer loop below (rc of csfoundation), or, for quick experiments, csVisOpenGL built in
`csfoundation/workspace/` and found first through a manual `CMAKE_PREFIX_PATH`. Agent: Claude Code started in
csImgTracker with `--add-dir ../csfoundation/workspace/csVisOpenGL`; the skills come from the plugins in any case.

**Outer loop, CI, the release chain (§4.2, §4.4).** The outer project of csVisOpenGL is **csfoundation**, so the change
always goes through it: csVisOpenGL `feature/<topic>` → csfoundation PR pointing to it (CI validates) → merge, rc →
csImgTracker PR bumping the csfoundation pin (CI validates the application). `cs-multi-repo-change` drives it, reading
the chain from the manifests (which provider each project pins): the developer asks for "PRs for this topic", the skill opens csVisOpenGL branch, csfoundation
PR, csImgTracker PR, in that order.

### 4.8 Soft rules

- Commits: imperative subject, `[area]` prefix where the repository uses one; curated history on `main` (squash /
  fixup on the feature branch, merge commit into `main`).
- Agents: never force push or delete `main` / `stable` (impossible anyway with the rulesets), never tag without being asked, never stage
  unrelated files; commit only when asked (as csCMake's `CLAUDE.md` already says).
- Generated files are never edited by hand (§2.3).
- Every PR: CI green, `pre-commit run --all-files` clean, `CHANGELOG.md` entry when user-visible.

Ways of working already in use (from the csCMake 1.0 migration notes, to go into the org rules as they are):

- Leave every change unstaged for review; stop and summarise before each commit; commit (`git add -A`, then commit)
  only when the user says so; push only when asked, after a few commits.
- Docs and comments describe the present only; history goes in commit messages and the changelog.
- No hidden side effects; no deprecation steps (the ecosystem moves to a new API directly).
- Do not run the CI matrix locally; one host build is fine.
- csCMake (and csorchestrator) are generic tools: never write the names of the cscosine projects into them.
- A change of csCMake found while working on a project is done in csCMake (its own rules) and released as the next rc;
  the project uses released csCMake packages, a clone of csCMake `dev` only while such a change is in progress.

---

## 5. Skills

### 5.1 Three families

| Family | Examples | Where |
|---|---|---|
| **Process** (org) | `cs-git-workflow` (branch, PR, CI watch, merge), `cs-multi-repo-change` (§4.2), `cs-release` and `cs-release-train` (§4.3), `cs-new-project` / `cs-update-project` (Copier), `cs-local-status` (branch, dirty, ahead / behind of every git repository found in the parent folder: no list needed) | Plugin `cs-org`, in `.github` |
| **Tools** (using csCMake / csorchestrator in a project) | `cscmake-usage` (variants, presets, packages, deployment helpers), `csorchestrator-usage` (project script, regenerate workflow, providers, run locally) | Authored in csCMake / csorchestrator (next to the docs), exported in the plugin |
| **Libraries** (using the code) | `csfoundation-libs`: what each library is for ("3D visualisation → csVisOpenGL", camera models → csCamera, Lie groups → csLie, asserts / logging / parallel → csCore); `csoptimization-libs` (csNelson, csBlockMatrix); `csqt6`, `csopencv` (which modules exist, how to link) | In the library / distribution repository, exported in the plugin |
| **Development** of one repository | `cscmake-development`, `csorchestrator-development`, `*-orchestrator-recipe` (exist today) | Stay in their repository |

Rule for library and tool skills: they live **next to the code they describe**, so a PR changing a public API updates
the skill in the same PR (a PR template checkbox; later a CI check that the skill mentions every public target).

### 5.2 Distribution: a Claude Code plugin marketplace in `.github`

A **plugin** is a folder with `.claude-plugin/plugin.json` (name, version, description) and `skills/<name>/SKILL.md`
(it may also carry commands, agents, hooks, scripts). A **marketplace** is a git repository with
`.claude-plugin/marketplace.json` listing plugins and where each one is. Both are plain files in git, no server.

The marketplace goes in the public `cscosine/.github` (public, so someone who clones only csImgTracker can install it):

```
.github/
  .claude-plugin/marketplace.json     name "cscosine"; lists the plugins below
  plugins/cs-org/                     the process skills, stored here
    .claude-plugin/plugin.json
    skills/cs-git-workflow/SKILL.md, cs-multi-repo-change/, cs-release/, cs-release-train/, cs-fork-sync/,
           cs-new-project/, cs-update-project/, cs-local-status/
```

```json
{ "name": "cscosine",
  "owner": { "name": "cscosine" },
  "plugins": [
    { "name": "cs-org", "source": "./plugins/cs-org" },
    { "name": "cscmake", "source": { "source": "git-subdir", "url": "https://github.com/cscosine/csCMake.git",
                                     "path": "agent-plugin", "ref": "main" } },
    { "name": "csfoundation", "source": { "source": "git-subdir", "url": "https://github.com/cscosine/csfoundation.git",
                                          "path": "agent-plugin", "ref": "main" } } ] }
```

- `cs-org` lives in `.github`. The tool and library plugins live **in their own repository** (`agent-plugin/` folder,
  same layout), referenced with a `git-subdir` source pinned to `main` (= the last release): skills stay next to the
  code and change in the same PR as the API they describe.
- Each repository's template-owned `.claude/settings.json` declares the marketplace and enables what it uses:

```json
{ "extraKnownMarketplaces": { "cscosine": { "source": { "source": "github", "repo": "cscosine/.github" } } },
  "enabledPlugins": { "cs-org@cscosine": true, "cscmake@cscosine": true, "csfoundation@cscosine": true } }
```

Use:

- Clone csImgTracker, start Claude Code, trust the folder: it proposes to add the `cscosine` marketplace and install
  the enabled plugins. By hand: `/plugin marketplace add cscosine/.github`, `/plugin install cs-org@cscosine`.
- Skills load by themselves when the request matches their description ("open the PRs for this change", "make the
  release"), or explicitly as `/cs-org:cs-release`. `/plugin marketplace update cscosine` picks up new versions.
- Developing a skill: edit it in the repository and test it with `claude --plugin-dir <path to the plugin>` before
  merging.

(Format checked against the official Anthropic marketplace, which uses the same `marketplace.json`, `plugin.json`,
`skills/` layout and `git-subdir` sources; the settings keys to confirm on the first install.)

### 5.3 `.agents/skills` vs `.claude/skills`

Claude Code reads `.claude/skills/` (and plugins), not `.agents/skills/`. Proposal: **`.claude/skills/` is the
location**, `AGENTS.md` stays as the tool-neutral entry point and links to the skills. If another agent tool is used
regularly, the template adds the other path as a symlink (on Windows this needs `core.symlinks`; acceptable since
setup already targets developers). Decide once (Q5), then migrate the 5 existing skills.

### 5.4 Skill quality

Short `description` with the trigger words (the description is what makes an agent load it); the body: what it is,
the decision table ("for X use Y"), commands, pitfalls; links to the docs rather than copies. A skill per question an
agent actually got wrong, not per library by default.

---

## 6. Overview of projects, relationships and versions

**Can be fully automated**; only the descriptions are manual.

| Data | Source | Manual? |
|---|---|---|
| Repositories, kind, description, status | `scripts/github-settings.json` (kinds) + GitHub (description, archived flag) | Yes, rarely |
| Latest release / rc per repository | GitHub API (`gh release list`) | No |
| Dependencies and pinned versions | csorchestrator manifests attached to each release (`*.csOrchestratorManifest`), and the recipes on `dev` | No |
| Which library commits a distribution shipped | Manifest (once §4.3.3 is in) | No |
| Template version, csorchestrator version per repository | `.copier-answers.yml`; the version stamp in generated workflows (csorchestrator R0) | No |
| CI state of `dev` / `main` | GitHub API | No |

The public organisation page gets the public part of it (§8 S5): versions, CI badges and the release-chain graph of the
public repositories, generated into `.github/profile/README.md` between markers, nightly. A script in `.github` (`scripts/ecosystem`) builds `ECOSYSTEM.md` from the GitHub API only (no clone): a Mermaid dependency graph (GitHub renders it), a table
of repositories × (kind, latest release, rc, `dev` CI, template version, csorchestrator version), and a **drift** section
(consumers pinned to an old provider rc, repositories behind the template, inconsistent pins such as the csopencvcpu
`project_version="5.0.0"` / tag `v5.0.1-rc3`). A scheduled workflow in `.github` regenerates it nightly and commits it;
the same script runs locally. It later becomes `csorchestrator deps outdated` / `check` (R9) for the dependency part.

An agent is not needed to produce it; an agent is useful to **act** on it (`cs-ecosystem-status` skill: "what is out
of date, propose the release train"), reading `ECOSYSTEM.md` or calling the same script.

---

## 7. GitHub: practices and how to adopt them

### 7.1 Constraints of the Free plan

- Rulesets and branch protection: available on **public** repositories; not on private ones without a paid plan.
  Making eigen3, csCore, csLie, csCamera, csVisOpenGL public (decided) leaves only csNelson, csBlockMatrix (and
  `meta` / legacy) unprotected, which is acceptable while they are immature. Side benefits: Actions minutes on standard
  runners are free for public repositories (macOS included), and csfoundation no longer needs an access token to
  check out its libraries (remains for csoptimization).
- Before switching a repository to public: `LICENSE` (MIT, D1 of `LICENSE_ASSESSMENT.md`; today none of the five has
  one; eigen3 keeps upstream's `COPYING.*`), the copyright line (open point L1), a secret scan of the **whole history**
  (gitleaks / trufflehog), no datasets or customer material in the history, README. Visibility is easy to switch but
  a public history may already be cloned: the scan comes first. Organisation-wide rulesets also need a
  paid plan (Team): on Free, rulesets are set per repository (scriptable with `gh api`, so applied to all at once by a
  script in `.github`).
- A single developer cannot approve their own PR: "require approvals" must be 0; the gate is **required status checks**
  and "changes only through a PR". An agent review (e.g. `/code-review` on the PR, or a review workflow) adds a second
  look without blocking.
- Team plan is worth it when the private libraries matter enough to protect, when a second regular contributor
  joins (required reviews, CODEOWNERS enforcement), or for org rulesets. Not needed for the first step.

### 7.2 What to adopt, by value

| Practice | Why here | Effort |
|---|---|---|
| **PRs where they mean something**: the release PR into `main` always; into `dev` for multi-repository or reviewed changes | A record of what a release contains; release notes from PR titles; agents propose on branches. Required on `dev` only once CI gates PRs (`ci-ok`) | Habit + skill |
| **Rulesets**, scoped as in §4.4 (applied by `scripts/github_settings.py`): outer repositories: `main` and `dev` no force push, no deletion (no PR rule: releases fast-forward `main`); inner first-party: `main` / `dev` no force push, no deletion; forks: `main`, `cpu`, `cuda` no deletion (force push allowed: they are rebased on each upstream tag, §4.6); every public repository, two tag rulesets: **stable** = include `refs/tags/v*`, exclude `refs/tags/v*-rc*` and `refs/tags/v*-test*`: restrict update + deletion; **pre-release** = include `refs/tags/v*-rc*`, `refs/tags/v*-test*`: restrict update only (an rc can be deleted, never moved; delete with `gh release delete <tag> --cleanup-tag`). No bypass actors | Makes §4 real for agents and for tired humans | One script |
| Repository settings: merge commits on (squash optional), auto-delete head branches, **auto-merge** on | Agent opens the PR, enables auto-merge, it merges when CI is green | One script |
| `.github/release.yml` + labels (`feature`, `fix`, `breaking`, `ci`, `docs`) | Release notes for free; `breaking` visible in the release train | Template |
| PR template (what / why, checks done, skill and docs updated, plan step, the other PRs of a multi-repo change) | Consistent PRs, agents fill it | Template |
| Dependabot alerts + secret scanning + push protection (free on public) | Security baseline | Settings |
| Renovate (or Dependabot for Actions) | Bump Actions, the Copier template, pins | Medium |
| Reusable workflows in a public `cscosine/.github` (e.g. the Python tool CI, lint, release-notes check), called with `uses: cscosine/.github/.github/workflows/x.yml@v1` | CI of the `tool` repositories written once; the generated workflows stay csorchestrator's | Medium |
| Environment `release` with protection for the release job | A tag push alone does not publish; one click to confirm | Low |
| Artifact attestations (`actions/attest-build-provenance`) on release archives (free on public) | Supply chain gap noted in the csorchestrator plan §1.3 | Low, with R0 |
| Signed tags / commits | Nice, not first | — |
| Merge queue, CODEOWNERS enforcement, required reviews | Need more contributors / plan | Later |

### 7.3 PRs without manual work

Everything is scriptable with `gh`; the browser is only for looking. Skills of the `cs-org` plugin (`cs-git-workflow`,
`cs-multi-repo-change`, `cs-release`), run in the repositories involved:

| Operation | Commands |
|---|---|
| Open | `git push -u origin feature/x` · `gh pr create --base dev --title … --body-file …` (body from the PR template, filled by the agent) |
| Merge when green | `gh pr merge --auto --merge --delete-branch` (needs "allow auto-merge" on the repository and at least one required check) |
| Wait | `gh pr checks --watch` · then `gh run watch` on the `dev` run after the merge |
| Multi-repo | Loop over the touched repositories in dependency order (from the providers each one pins; later the csorchestrator graph): open all PRs, merge one, wait for its `dev` CI, next; stop on the first red |
| Release | `gh pr create --base main --head dev --title "Release vX.Y.Z"` · merge · tag `vX.Y.Z` on `main` · push the tag (the generated release job does the rest) · bring `dev` level with `main` |
| Settings and rulesets | `gh api -X PATCH repos/cscosine/<r> …` and `gh api repos/cscosine/<r>/rulesets …` over every public repository, from a JSON in `.github/scripts/` (idempotent; the one org admin task) |

What has to change for it to work:

Deferred (R0 decided minimal, 2026-11-21, §8 S2): the three changes below are in csorchestrator's backlog; until
then PRs merge without a required check and `main` builds after the merge.

- **Workflows must run on PRs.** The csorchestrator-generated workflows run on pushes to listed branches (hence the
  "CI on feature/…" extra commit). The generator gets a `pull_request` trigger for `dev` / `main` (a csorchestrator R0
  item); the extra commit then is only needed for the consumers' pointers to providers' feature branches.
- **One stable check name.** A matrix produces dozens of job names that change with the variants; required checks need
  a fixed one. Each workflow ends with a job `ci-ok` (`needs:` all, `if: always()`, fails if any failed); the ruleset
  requires `ci-ok` only. Same in the template-owned CI of `tool` repositories.
- **`dev` after a release.** A merged release PR leaves a merge commit on `main` that `dev` lacks; the release script
  fast-forwards `dev` to `main` (a direct push, allowed on `dev`).
- PRs are authored with the user's token (as now with `gh`), so they trigger workflows normally (PRs opened with the
  Actions `GITHUB_TOKEN` would not).

### 7.4 `.github`

The only org-level repository, public (§3): default community files for every repository (`CONTRIBUTING.md`), the org
page, the plans, the rules, the licensing policy, the plugin marketplace, the admin scripts and the generated overview.
Its workflows run for free (a public repository).
---

## 8. Roadmap and the first step

| # | Step | Content | Size | Status |
|---|---|---|---|---|
| **S0a** | **Plans, `.github`, rules** | Plans moved to the org repository's `plans/` (`.github-private` then, `.github` since 2026-11-20) (README, status columns); `cscosine/.github` created (public: minimal profile, the place for the marketplace of S4); org rules (§4) written in `rules/cscosine-rules.md`, copied into a repository's `CLAUDE.md` when it is next touched | ½ day | done |
| **S0b** | **GitHub settings** | Script applying settings + rulesets (§7.2) to public repositories; labels; archive the legacy repositories; from now on, PRs into `dev` / `main` (until the generated workflows have `pull_request` + `ci-ok`, no required check on csorchestrator consumers) | 1 day | done (2026-11-20; csVis still to delete) |
| **S0c** | **Going public** | eigen3, csCore, csLie, csCamera, csVisOpenGL: secret scan, clean history if needed (§4.5), `LICENSE`, README, then public | 1 day | done (2026-11-20; no secrets; history kept, author emails as they are) |
| S1 | Finish stable-dev | Done (2026-11-16); open: csCMake 0.x tags and `v1.0.0`, csopencvcuda (its §4.9) | — | done |
| **S1b** | **Review of stable-dev** | `done/PLAN-review-stable-dev.md`: every change of the round reviewed (right place, one place, docs, tests, leftovers); fixes as PRs | ~1 week | done (2026-11-20; the chain rebuilt as rcs) |
| S2 | csorchestrator: minimal R0 | Decided 2026-11-20: no PyPI, no API promise until the rewrite (its plan). Only: tag csorchestrator `v0.1.0`; projects install it from the tag (default) through `setup.sh` / `setup.ps1`: `./setup.sh` = the pinned version, `--csorchestrator=<tag or branch>` = another one, `--csorchestrator=<path>` = editable local; the generated workflow states its csorchestrator version. Done with S3 (the setup scripts are template-owned, the default version a Copier answer `csorchestrator_version`) and before the finals round | ~1 day | doing (2026-11-21: `v0.1.0-rc1` tagged, the template's `setup.sh` / `setup.ps1` install it by default; final `v0.1.0` at the finals round. **R0 decided minimal** (2026-11-21): generated workflows build `main` after the merge, no PR builds; the `pull_request` trigger, the `ci-ok` job and build-once-per-commit (a tag republishes its commit's build) go to csorchestrator's backlog, `PLAN-csorchestrator-architecture.md` §7c; §7.3 waits for them) |
| S3 | Template: base layer | `cs-project-template` with the shared files of §2.4 and `kind`, including `setup.sh` / `setup.ps1` with the csorchestrator switch (S2) and the version as an answer; adopted by every repository; Renovate. Comes before the finals round (no longer waits for the csorchestrator rewrite) | ~1 week | doing (2026-11-21: adoption done, every repository on `cs-project-template` v0.2.5 (tools, distributions, csfoundation and csoptimization with their libraries, applications); open: Renovate (Copier update PRs on new template tags, Actions versions, pins)) |
| S4 | Skills, first set | Create `.github` with the marketplace and `cs-org` (`cs-git-workflow`, `cs-multi-repo-change`, `cs-release`); `agent-plugin/` in csCMake and csfoundation (`cscmake-usage`, `csfoundation-libs`); `.claude/skills` migration | ~1 week, then continuous | doing (2026-11-20: marketplace + cs-org in `.github`: cs-workflow, cs-release-train, cs-fork-sync, cs-local-status; next: tool / library plugins, `.claude/settings.json` via the template) |
| S4b | Forks | `cscosine/README.md` + `CHANGELOG.md` in each fork (patches listed from `git log <base>..dev`), `-cs.N` tags, `cs-fork-sync` skill, generated `FORKS.md`; upstream PRs for the generic fixes | 2–3 days | todo |
| S5 | Overview | `cs-ecosystem` script (GitHub API only) + nightly workflow → `ECOSYSTEM.md` in `.github` (all repositories, drift); and the public part generated into `.github/profile/README.md` between markers (`<!-- ecosystem:start/end -->`): public repositories with kind, latest release / rc, CI badge, what each is built on, and the Mermaid graph of the release chain; a scheduled workflow in `.github` (public data only) regenerates it nightly and on demand after a release. Manual input: the repository descriptions and kinds only | 2–3 days | doing (2026-11-20: public part done, `.github/scripts/ecosystem.py` + nightly workflow; next: the private `ECOSYSTEM.md` with drift) |
| S6 | csorchestrator rewrite | Its plan (R1 … R9, GUI / TUI) on csorchestrator `main` or a long feature branch; projects stay on their pinned version until moved one by one; PyPI when mature | weeks | todo |
| S7 | Template: csCMake / csorchestrator layers | `library`, `distribution`, `application` kinds; `cs-new-project` skill; the next new project is created from it | ~1 week | todo |

**Why S0 first**: it costs two or three days, changes nothing in the code, and everything after (stable-dev merges,
csorchestrator releases, template adoption PRs) then happens through PRs with CI gates and in a versioned place. It
also gives agents the rules before they start touching many repositories.

**Order (2026-11-20):** S4 and S5 now; then S3 with the minimal R0 (S2); then the finals round (csCMake `v1.0.0`,
every project's final, csorchestrator `v0.1.0` pinned); the csorchestrator rewrite (S6) whenever ready.

**csorchestrator or Copier first?** (earlier reasoning) csorchestrator R0, then the Copier base layer: R0 is the largest maturity gap
(no releases, unreproducible workflows) and the base layer of the template does not depend on it, so they can overlap;
but the C++ layers of the template must wait for R4, otherwise they template an API that is about to change. Copier is
"ready enough" today only for the shared tooling files, which is exactly where the measured drift is.

---

## 9. Decisions to take

| # | Question | Proposal |
|---|---|---|
| Q1 | Where plans and the overview live | `.github` (public): plans, `ECOSYSTEM.md`, scripts; `.github` retired (2026-11-20) |
| Q2 | Branches | `main` trunk everywhere (default), `stable` on outer repositories (fast-forwarded to final tags), tags for releases, `feature/*` with CI on demand; only no force push / deletion enforced (decided and migrated 2026-11-20) |
| Q3 | Tags of first-party libraries built by a distribution | Own semver per library, tagged when changed; manifest records the commit |
| Q4 | Refs of outer projects | Explicit in the recipe: inner `main` (or a feature branch), providers by tag; exact rebuilds from tags + manifest; weekly build of `main` (§4.3, 2026-11-20) |
| Q5 | Skills location | Marketplace + `cs-org` in the public `.github`; tool / library plugins in an `agent-plugin/` folder of their repository; repository-only skills in `.claude/skills/`; `.agents/skills` migrated (symlink if another tool needs it) |
| Q6 | One Copier template with `kind`, or one template per kind | One, with `kind` |
| Q7 | Renovate (Copier + Actions + pins) or Dependabot (Actions only) | Renovate |
| Q8 | Team plan | Not now; revisit when the private libraries need protection or a second contributor joins |
| Q9 | Tracking progress | The plans in `.github/plans/` are the only tracker (status column per step, updated in the PR that does the work); no issues, no Project; reconsider with a second regular contributor (§3.2) |
| Q10 | Old repositories csProjectManager, csVis, pipes | Deleted (2026-11-20; git bundles kept in `~/cscosine-deleted-repos/`); csMetaProjectAll already archived |
| Q11 | PRs and protection only on outer projects? | Protection everywhere it is free (no force push / deletion of `main` / `dev`, tags); the release PR into `main` on outer repositories; PRs into `dev` required later, with a CI check (§4.4) |
| Q12 | Clean history | Now for the csfoundation libraries before they go public (old history archived); never for public repositories and forks (§4.5) |
| Q13 | Fork model | Patch stack on an upstream tag, `vX.Y.Z-cs.N`, `cscosine/README.md` + `CHANGELOG.md` per fork, `cs-fork-sync` skill, generated `FORKS.md` (§4.6) |
| Q14 | Developing a project with a library from a provider | Now: release chain (rc). Future: local release store + per-library provider selection in csorchestrator (its §8), not scheduled (§4.7) |
| Q15 | Single source of the org rules | The template (`.claude/cscosine-rules.md`, imported by `CLAUDE.md`); not `.github`, not a plugin (done 2026-11-21) |
