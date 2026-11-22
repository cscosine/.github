# Plan: csorchestrator, from internal tool to a mature, deployable framework

Date: 2026-11-16 · Status: **to approve** · Follows: `done/PLAN-stable-dev-ubuntu26mac-libs.md` (to finish first)

Goal: csorchestrator released and pinned like any other dependency; a model where steps are data, a configure stage
separate from generate / run, selection of what to run (phases, steps, actions, variants), explicit handling of
privileged and destructive operations, one event stream for every output (console, Markdown, TUI), and backends
other than GitHub Actions possible without touching every step.

---

## 0. Summary

| Topic | Today | Target |
|---|---|---|
| csorchestrator itself | 0.1.0, no tags, `pip install -e ../csorchestrator`, `portable/` copied as `csorchestratorsdk/` | Tagged releases, pinned by consumers, version stamped in workflows and manifests, no vendored SDK |
| Steps | Classes that register every backend's code (`__post_init__`) | Data (id, tags, inputs, outputs, effects, when, actions); backends own a table of handlers per step type |
| Reporting | `Report` (strings), a reporter with 15 methods, sinks, 3 result types | One event bus, `Diagnostic`, one `Result[T]`, a run record; console / Markdown / TUI as subscribers |
| Dependencies | Downloaded while `create_orchestrator()` runs; release tags typed by hand in every consumer | `configure` stage: resolved plan + lock file; `create_orchestrator()` pure |
| Running | Everything, on every host-compatible variant | Selection by id / tag / phase / variant, actions per step (configure, build, test, clean), dependency awareness |
| Privileges | `sudo apt install` runs locally unless the script remembered to skip it | Steps declare effects; policy `print / ask / apply / skip`; one pre-flight before the run |
| Backends | GitHub Actions (YAML with inline Python) | Thin backends that call `csorchestrator exec` on the runner; local containers; GitLab if needed |
| Interfaces | CLI (`run`, `describe`, `generate-github-workflow`) | CLI + Textual TUI (also in a browser) + generated VS Code tasks |
| Checkout | A temporary clone per repository and per run to check it; a dirty repository or another branch stops the run | `git ls-remote` / one fetch, in parallel; a policy per repository (`auto`, `keep`, `update`, `strict`, `reset`); local overrides (`path`, `ref`) in a workspace file |
| Project API | Functions with up to ~26 parameters, parallel dicts keyed by name, split between `<name>_project.py` and `<name>_config.py`; build order = dict order | Objects: `Project`, `Repo`, `Provider`, `depends_on`, `build`, `publish`; build order from the graph; manifests generated from it, `*_config.py` no longer needed; low-level steps as the escape hatch |

---

## 1. Assessment

### 1.1 Purpose

csorchestrator lets you write a **build-and-release pipeline for a family of interdependent CMake repositories once,
in Python**. A project script (`<name>_project.py`, `create_orchestrator()`) is:

- **run locally** (the variants compatible with the host);
- **translated into a GitHub Actions workflow**: a matrix job (OS × architecture × compiler × generator) and, on a
  `v*` tag, a release job;
- **published as a binary distribution**: per-variant archives, a release manifest (`*.csOrchestratorManifest`), a
  bundle (with the project's `*_config.py`), attached to a GitHub Release.

Consumers download providers' releases transitively, by library and variant (`ManifestGithub`,
`resolve_libs_deps_and_install_dependencies`). In practice it is a **serverless binary package manager on GitHub
Releases plus a CI generator**, paired with csCMake (csCMake: variants, presets, packages; csorchestrator: matrix,
release, distribution, deployment runs).

Size: ~9k lines in `src/` (+ ~4.9k of tests), 331 commits since 2026-03. Consumers: third_party_base_libs, csqt6,
csopencvcpu, csopencvcuda, csfoundation, csoptimization, csImgTracker, csSkiTracker (generated workflows 470 to 940
lines each).

### 1.2 The way of working it implies

- **A release train.** A change in csCMake or csorchestrator travels in a fixed order (csorchestrator, csCMake →
  third_party_base_libs → opencv / csopencvcpu / csqt6 → csfoundation → csoptimization → applications), with a new rc
  per repository, by hand. `done/PLAN-stable-dev-ubuntu26mac-libs.md` is that train written out.
- **Pins typed by hand in every consumer.** `ManifestGithub(..., release_tag="v0.1.0-rc6")` for
  third_party_base_libs is in 5 configuration files; provider blocks are copied between consumers. Already
  inconsistent: the csopencvcpu provider has `project_version="5.0.0"` and tag `v5.0.1-rc3`.
- **Executable metadata.** A provider's `*_config.py` ships in its bundle and consumers import it: flexible, but every
  published release is tied to the csorchestrator API of the day.
- **csorchestrator is never released.** Consumers install it editable from the sibling folder and the workflows
  embed the code of whatever was checked out locally: **an old release cannot be rebuilt exactly**, and no workflow
  records which csorchestrator generated it. This is the largest maturity gap.

### 1.3 Health

| Area | State |
|---|---|
| Architecture, typing, lint | Good: layers enforced by import-linter, mypy strict, ruff, pre-commit, CI on 3 OS × Python 3.11–3.14 |
| Tests | 154 pass, 84 skipped by default (slow / git); 54% branch coverage; no coverage gate |
| Documentation | README mostly development setup and partly stale (`3rdPartyBaseLibs`, `qt6.py`); no user guide |
| Variant matrix | Hand-kept copy of csCMake's; Ubuntu 26.04 and macOS missing (`TODO-cscmake-alignment.md`) |
| Supply chain | No sha256 in manifests or on download; Mesa downloaded without a hash; no attestations |
| CI cost | No ccache / `actions/cache`; every project builds every variant |
| Public API | Consumers import internal paths (`frontend.step.step_get_precompiled_lib_github…`): a refactor breaks 8 repositories |

### 1.4 Positioning

| Alternative | What it covers | What csorchestrator does that it does not |
|---|---|---|
| Conan 2 | Version resolution, lockfiles, binary caching, profiles | Conan needs recipes (a second build description) and a binary server; csCMake's 4 configurations (incl. `paranoid`) are awkward there |
| vcpkg | Manifests, triplets, registries for forks, binary cache on GitHub Packages | Debug / Release only; ports are a parallel build description; Qt-size builds are slow |
| Pixi / conda-forge, Spack, Nix | Reproducible binaries | Weak on Windows / MSVC (Nix) or HPC-oriented (Spack); no CI generation |
| Dagger | Same pipeline locally and in CI | Generic: no C++ variants, no binary distribution |
| cibuildwheel | Variant matrix, builds, tests on clean machines | Python wheels only |
| Bazel / Buck2 | Hermetic multi-repository builds | A different world: every CMake build rewritten |

There is little room as a general product against Conan / vcpkg (they cover most of the distribution part). What is
specific: **no server** (GitHub Releases only), **pure CMake** with `find_package`, **one definition** for the local
run, the CI matrix and the release, **deployment smoke runs** on clean runners.

Fits: small teams / SMEs (vision, robotics, scientific C++) with 5–20 interdependent repositories and forked
third-party libraries, shipping prebuilt multi-platform binaries and applications, on GitHub, without an infra team.
Does not fit: organisations already on Artifactory / Conan / Bazel; ecosystems with many independent publishers that
need semver resolution.

Position: **the release pipeline for csCMake ecosystems** (csCMake + csorchestrator as a pair), not a package
manager. Mature for the own repositories first; external users second.

---

## 2. Architecture diagnosis

### A1. Visitor plus capability registry, coupled the wrong way

- `execute_orchestrator` walks phases → steps, calling a visitor (`OrchestratorVisitorLocalExecutor`,
  `OrchestratorVisitorGitHubWorkflowPreparation`) and, in lockstep, a reporter (the observer-like part: 15 abstract
  methods mixing lifecycle events with one-off `report_*` calls).
- The visitor asks the step for a capability (`step.get_capability(StepCapabilityLocalExecution)`); each step
  registers **every backend's** implementation in `__post_init__` (e.g. `StepBashScriptCommand` imports both the
  GitHub translation and local execution). Consequences:
  - a new backend means editing every step;
  - steps are not data: they cannot be serialised, compared or shown in a UI;
  - extras (`StepSkipExecutionOnLocal`, `StepExecuteOnlyOn`, `StepGithubIfAlways`) are interpreted by hand in each
    backend, with no shared meaning;
  - a backend skips unsupported steps silently ("does not support local execution": an info, not an error).
- Release creation is outside the model: special-cased at the end of `validate_and_execute_orchestrator`
  (`wf_config.create_release_on_tag`).

### A2. A linear list without inputs and outputs

Phases → steps in order; nothing declares what a step needs or produces. This blocks selection ("build only" does not
know it needs the checkout and the libraries, or whether they are there), cleaning (which folder belongs to which
step), incremental runs (is a step up to date?) and any UI beyond a list.

### A3. GitHub expressions in the domain

`repo_access_token="${{ secrets.ACTIONS_ORG_ACCESS }}"` in project scripts; `${{ matrix.os }}` in templates. A second
backend first needs backend-neutral values.

### A4. Reports are strings; three result types

`Report` = lists of strings (no step id, time, duration, exit code, command, log file, hint), plus `Expected[T,E]` and
`OptionalResultWithReport[T]`. Hard to render well (Markdown) and impossible to drive a UI from.

### A5. The project script has side effects

With `download_dependencies_manifest_and_bundle=True`, `create_orchestrator()` downloads manifests and bundles into
`dependencies/`: `describe` and `generate-github-workflow` do network I/O and write files, cannot run offline, and
their result depends on what was downloaded. It is an implicit **configure** stage.

### A6. The checkout step is slow and all-or-nothing

`StepGetRepositoryGitHub` (local), on a repository already present, runs `validate_and_sync_repo`:

1. dirty (`is_dirty(untracked_files=True)`) → **error**, the run stops (the checkout is the first phase);
2. **a full temporary clone** (`try_git_clone_checkout(..., depth_one=True)`) of the remote, only to learn the kind of
   the ref (branch / tag / commit) and its commit;
3. remote URLs compared as strings (an SSH clone against an HTTPS URL → error);
4. branch: another local branch → error; detached HEAD → error; then `fetch` and `pull --ff-only` (two more network
   operations);
5. repositories one after the other, through GitPython.

So: three network operations per repository per run, and the normal development situation (editing csCore on a
feature branch while building csfoundation) is an error. There is no option between "fail" and nothing.

### A7. The recipe API is functions and parallel dicts

- `create_default_orchestrator_and_default_checkout_build_upload` takes ~26 parameters; `checkout_repos`,
  `build_repos`, `create_and_upload_artifacts` take dicts keyed by repository name, extracted from
  `RepoRefBuildPublishConfigDict` with `extract_*` helpers.
- One repository is described in up to five places, linked by strings: the `repos` dict (ref, build configs, publish
  mode), `LIBRARY_DEPENDENCIES` / `LIBRARY_DEPENDENCIES_DEV`, `external_dependencies` / `external_dependencies_dev`
  per provider, the provider blocks (`ManifestGithub`), the system packages (`install_requirements`).
- Half of it is in `<name>_config.py`, because that file ships in the bundle and consumers import it to learn the
  provider's dependencies and system packages; each consumer re-implements `install_<name>_build_dependencies`.
- The dependency graph is known (it goes into the manifest) but **not used to order the build**: `build_repos`
  follows the order of the dict.
- Phase names are strings, with suffix parameters (`phase_name_suffix`) to keep them unique.

---

## 3. Proposals

### B1. Steps as data, backends own handlers

```python
# domain: data only
@dataclass(frozen=True)
class CMakeBuild(Step):          # id, tags, inputs, outputs, effects, when: inherited
    source_dir: Path
    config: BuildConfig

# backend: a table of handlers per step type; steps do not know backends
local = Backend("local")
@local.handles(CMakeBuild)
def _(step: CMakeBuild, ctx: LocalCtx, events: EventBus) -> StepResult: ...

github = Backend("github")
@github.handles(CMakeBuild)
def _(step: CMakeBuild, ctx: GhCtx) -> list[GhStep]: ...
```

- Validation: every step of the plan has a handler in the chosen backend, else an error listing the missing ones.
- Extras become shared, typed fields read the same way by every backend: `when: Condition` (OS / architecture /
  variant, always, CI only, local only), `once_per: "matrix" | "run"`, `effects` (B3).
- Release creation: ordinary phases of a `release` job.
- Migration: an adapter keeps today's `StepXxx(...)` constructors and recipes working; consumers move one commit
  each. **Golden tests first** (R0): the generated workflow of every consumer as a snapshot; refactors give a zero
  diff.

### B2. One event bus, structured diagnostics, a run record

- Events: `RunStarted`, `PhaseStarted`, `StepStarted`, `StepOutput(line, stream)`, `StepFinished(status, duration,
  diagnostics)`, `StepSkipped(reason)`, `ConfirmationRequested(...)`, `RunFinished`.
- Subscribers: console (plain / colored), Markdown, JSON log, `$GITHUB_STEP_SUMMARY`, TUI. They replace the reporter
  interface, the composite reporter and the sinks.
- `Diagnostic(level, code, message, step_id, hint)`; one `Result[T]` (value + diagnostics) replaces `Report`,
  `Expected`, `OptionalResultWithReport`.
- Run record: `workspace/.csorchestrator/runs/<id>.json` (plan, selection, status and duration per step, artifacts
  with sha256). Markdown is a rendering of it (re-renderable, comparable between runs); the TUI reads the last status
  of each step from it.

### B3. Effects, policy, inputs

- Each step declares `effects ⊆ {SYSTEM_MODIFY, PRIVILEGED, NETWORK, INTERACTIVE, DESTRUCTIVE}`.
- Policy per environment: `--system=print|ask|apply|skip`. Local default `ask`: a **pre-flight** collects every
  privileged need before the run ("missing: libxcb-cursor0 xvfb → `sudo apt install …` [apply / print script /
  skip]"), asks once, never prompts during the run. CI default `apply`. `print` writes `prerequisites.sh` / `.ps1`.
- Typed inputs: `Secret("ORG_TOKEN")` (GitHub `${{ secrets.… }}`, GitLab CI variable, locally an environment
  variable / keyring / `gh auth token`), `Param("cscmake_version", default=…)` overridable from the CLI,
  `MatrixVar("os")`.
- `doctor`: tools (cmake, compilers, ninja, git, gh), their versions, tokens.

### B4. A configure stage

| Stage | Command | Does | Writes |
|---|---|---|---|
| Declare | the project script | `create_orchestrator()`, pure, no I/O | the project model |
| **Configure** | `csorchestrator configure` | reads the lock, fetches provider manifests (cached), resolves the dependency graph, selects variants, checks the host | `.csorchestrator/plan.json`, `cs.lock` |
| Generate | `generate github \| gitlab \| vscode-tasks` | translates the plan; deterministic, offline | workflow files |
| Run | `run [selection]` | executes the plan (or part of it) locally | run record |

- The lock file (provider → tag → sha256) comes with it; `deps outdated | bump | check` work on it.
- Values only known at CI run time (e.g. `cs-deployments.json` after the CMake configure) are deferred values in the
  plan, resolved by the step when it runs.
- Manifests become declarative (dependencies, system requirements, mapping); the executable `*_config.py` optional.

### B5. Other backends

| Backend | Fit | Gaps |
|---|---|---|
| GitLab CI | Good: `parallel:matrix`, stages, `needs`, artifacts, `release:` | Release assets are links (Generic Package Registry); macOS runners on paid tiers only; Windows SaaS runners limited or self-hosted |
| Jenkins | Feasible: declarative `matrix { axes }`, agent labels, `archiveArtifacts` / `stash` | No release / store concept; Groovy generation; agents always self-managed |
| Azure Pipelines | Close to GitHub | Only on demand |
| Local containers (Docker / Podman) | Very useful: the Ubuntu 22.04 / 24.04 / 26.04 variants locally; the bare-container deployment test | Linux only |

Common prerequisites: B1 (handlers), B3 (neutral values), a variant → runner table per backend, a **ReleaseStore**
abstraction (GitHub Releases, local folder; later GitLab packages, S3 / Artifactory) replacing the GitHub-specific
`ManifestGithub` / `github_release_download`.

**Runner exec mode**: instead of inline Python in the YAML, the runner installs the pinned csorchestrator and runs
`csorchestrator exec --plan plan.json --variant $V --phase <phase>`. Backends generate only the skeleton (matrix,
jobs, checkout, toolchain setup, cache, upload, release); the code that runs is the same locally and in CI. Native
steps stay where the platform does it better (checkout, `setup-msvc`, upload-artifact). Removes `csorchestratorsdk/`.

Order: abstractions (they simplify GitHub too) → local containers → GitLab when a real user needs it → Jenkins on
demand.

### B6. Selection

- Hierarchical ids: `deps/third_party_base_libs.fmt`, `build/csCore`.
- Standard tags set by the recipes: `checkout`, `deps`, `system`, `configure`, `build`, `test`, `install`, `package`,
  `deploy`, `release`; user tags on top.
- `run -s tag:build -s 'build/csCore' --skip tag:system --from build --until test --variant '*clang*'`; `--list`
  shows what would run.
- With inputs / outputs (A2): `--only build` with the libraries missing → "inputs missing from `deps/*`: include
  them?".
- Variants selectable locally (e.g. GCC and Clang Ninja Multi-Config on the same Ubuntu host).

### B7. Actions per step, clean

| Step type | Actions |
|---|---|
| CMake | `configure`, `build`, `test`, `install`, `workflow` (all), `fresh`, `clean` |
| Repository | `checkout`, `sync`, `status`, `clean` (refused on a repository with local changes) |
| Dependencies | `download`, `verify` (sha256), `clean` |
| Archives / deployments | `create`, `run`, `clean` |

- CMake: csCMake's configure / build / test presets → `cmake --preset`, `cmake --build --preset`, `ctest --preset`;
  `workflow` stays the default.
- `csorchestrator clean build|libs|install|deploy|all|<step-id>` from the declared outputs; dry run with paths and
  sizes; only paths inside the workspace root; never a repository with local changes; confirmation for
  `DESTRUCTIVE`.

### B8. Suggested, not silent

Covered by B3: system packages and other `SYSTEM_MODIFY` / `PRIVILEGED` steps are proposed by the pre-flight, applied
only on consent locally, always in CI.

### B9. TUI and GUI

- **Textual** TUI: tree of phases → steps with status, duration, log pane per step; variant picker; buttons run
  selected / run from here / retry failed / actions (configure, build, test, clean); confirmation dialogs for
  `PRIVILEGED` and `DESTRUCTIVE`. It consumes the plan, the event bus and the run record.
- The same TUI in a browser with `textual serve`: no second codebase for a "GUI".
- `generate vscode-tasks`: `.vscode/tasks.json` from the plan (a task per phase and action).
- A real web GUI only if there is demand beyond the own use.

### B10. Markdown report

Rendered from the run record: header (project, version, variant, host, versions of csorchestrator / cmake / compiler,
result); summary table (phase / step / status / duration); failures first (command, exit code, last lines of the log,
hint); dependency resolution (provider → tag → libraries → sha256); artifacts (name, size, sha256); full logs in
`<details>`. In CI also appended to `$GITHUB_STEP_SUMMARY`. `describe --format md`: a "how this project builds"
section for each consumer's README.

### B11. Other workflows (csCMake's, its own)

- **csCMake: no.** It is stdlib-only and the source of truth of the variants; its CI depending on csorchestrator
  (which reads csCMake's `variants.json`) would be a cycle. The real duplication is the variant → runner label and
  setup mapping (`ubuntu-26.04-arm`, `macos-15`, `brew install ninja`), in csCMake's `tests/smoke/ci_matrix.py` and in
  csorchestrator: move it **into data** (a `ci` section next to `variants.json`) read by both.
- **csorchestrator's own CI: no.** 86 stable lines, and it needs a generic matrix (Python versions) the C++ model does
  not have. Possible later as dogfooding of generic matrix axes (parking lot).

### B12. Checkout: fast, and under the developer's control

**Speed**

- Resolve the ref without a clone: `git ls-remote <url> <ref>` (one round trip: commit, and branch vs tag from
  `refs/heads/` / `refs/tags/`); in an existing repository, one `git fetch origin <ref>` and a comparison with
  `FETCH_HEAD`.
- Repositories in parallel (a thread pool; checkouts do not depend on each other).
- Plain `git` through `subprocess` (no GitPython startup, git's own error messages); URLs normalised before
  comparison (SSH / HTTPS, `.git` suffix).
- `--offline`: no network, the local state as it is (with the warnings below).
- `csorchestrator status`: a table of every repository (path, branch, commit, ahead / behind, dirty), from the local
  state only: instant.

**Policy per repository** (a default per environment, overridable per repository and from the CLI with
`--repos=<policy>` or `--repo csCore=keep`):

| State of the local repository | `auto` (local default) | `keep` | `update` | `strict` (CI, release) | `reset` |
|---|---|---|---|---|---|
| missing | clone | clone | clone | clone | clone |
| clean, on the ref, behind | fast-forward | as is + warning | fast-forward | fast-forward | fast-forward |
| clean, on the ref, diverged | as is + warning | as is + warning | error | error | reset (confirm) |
| on another branch | as is + warning | as is + warning | error | error | checkout ref (confirm) |
| dirty | as is + warning | as is + warning | error | error | stash + reset (confirm) |
| detached at the requested commit / tag | OK | OK | OK | OK | OK |

- Never overwrite work without consent: `reset` is `DESTRUCTIVE` (B3), stashes first, and asks.
- Every warning ends in the run record and the report: "csCore: local, branch `feature/x` @abc123, 3 modified files".
- A release (tag build) requires `strict`; the manifest records, for every repository built (provenance): URL, ref
  requested (tag or branch), commit, the tag on that commit if any, and the package version installed; the release
  notes and `ecosystem release` (R9) read them from there.

**Local overrides** (`cs-workspace.local.toml`, git-ignored; like CMake user presets, `go work`, Cargo `[patch]`):

```toml
[repos.csCore]
path = "../csCore"          # use this checkout instead of workspace/csCore (nothing cloned, policy keep)
[repos.csLie]
ref = "feature/lie-update"  # another ref than the project script's
```

This is the development mode: edit a library in its own folder, build its consumer against it, without touching the
project script or the generated workflow.

### B13. A structured project API

Two levels. **High level** (what csfoundation, csoptimization, third_party_base_libs, the applications use): objects
that describe repositories, providers and their relations. **Low level** (Qt, OpenCV CUDA, special cases): phases and
steps as today, mixable with the high level.

```python
from csorchestrator.api import Project, BuildConfig as C, Linux

p = Project("csfoundation", version="0.1.0", cscmake="1.0.0-rc5")

tpl = p.provider("third_party_base_libs", tag="v0.1.0-rc7")       # version and libraries from its manifest
qt  = p.provider("csqt6", tag="v6.11.1-rc4", mapping="qt6_mapping")

core = p.repo("csCore", ref="dev").build(C.ALL)
core.depends_on(tpl["eigen3", "fmt", "fmt-eigen", "libassert", "NamedType", "tl-expected", "tl-optional", "Catch2"])

lie = p.repo("csLie", ref="dev").build(C.ALL).depends_on(core, tpl["eigen3"]).test_depends_on(tpl["Catch2"])
cam = p.repo("csCamera", ref="dev").build(C.ALL).depends_on(core, tpl["eigen3"]).test_depends_on(tpl["Catch2"])
vis = (p.repo("csVisOpenGL", ref="dev").build(C.ALL)
       .depends_on(core, tpl["eigen3"], qt["qt6"]).test_depends_on(tpl["Catch2"])
       .system(apt=["libgl1-mesa-dev", "libopengl-dev", "mesa-common-dev"], when=Linux))

p.publish(core, lie, cam, vis)        # versions, archives, manifest, release on tag
```

An application:

```python
fnd = p.provider("csfoundation", tag="v0.1.0-rc9")
app = p.self_repo().build(C.ALL).depends_on(fnd["csCore", "csVisOpenGL"], ocv["opencv"])
app.deployment("app").gui_smoke(["{folder}/bin/csImgTracker", "--smoke"])     # D6 recipe
p.publish(app)
```

**What the high level does with the graph** (compiled into the plan at configure, B4):

- checkout of the repositories (parallel, B12), system requirements gathered and deduplicated (B3, one pre-flight),
  download of the provider libraries actually needed, transitively, for the selected repositories (today's
  `resolve_libs_deps_and_install_dependencies`, driven by the graph);
- **build in topological order** of `depends_on` (cycles → error at configure); independent repositories in parallel
  later;
- validation at configure: unknown library in a provider's manifest, dependency on a repository not declared, a
  `test_depends_on` used for the build;
- selection with the graph (B6): `run build/csLie` includes `csCore` (or uses its install if up to date); "only
  affected": the changed repositories and their dependents;
- `describe --graph`: a Mermaid diagram of repositories, providers and libraries;
- **the manifest generated from the graph**: dependencies, test dependencies, system requirements, publish mode
  (headers only). Consumers read them from the provider's manifest, so `<name>_config.py`, `LIBRARY_DEPENDENCIES` and
  the `install_<name>_build_dependencies` functions disappear (Q7 + Q11).

**Escape hatches** (in this order, the first that fits):

1. Options of the high level: `.build(C.ALL, cmake_options={...})`, `.checkout(shallow=True)`,
   `.publish_mode(HEADERS_ONLY)`, `.system(script=..., when=Windows)` (e.g. the CUDA install of csopencvcuda).
2. A **builder** instead of the csCMake one: `p.repo("qt6", url="git@github.com:qt/qt5.git", ref="v6.11.1")
   .checkout(shallow=True).build_with(QtBuilder(...))`. `Builder` is a protocol (it returns the steps of configure /
   build / test / install per OS); `CsCMakeBuilder` is the default, `ScriptBuilder` takes per-OS scripts.
3. Extra steps placed relative to the generated phases: `p.add(step, after="checkout")`, `repo.before_build(step)`,
   `repo.after_install(step)` (e.g. "free disk space" on Linux runners).
4. Low level: `p.orchestrator()` gives the phases and steps (today's model) for anything else.

csqt6 and csopencvcuda keep checkout, system requirements, dependencies, publish and release from the high level and
plug in a builder plus a few steps; third_party_base_libs, csfoundation, csoptimization and the applications become
high level only (today 120–330 lines of project + config each, e.g. csfoundation 123 + 204; expected 30–60).

**Migration**: the high level compiles to the new model (B1) and uses the configure stage (B4) to read the providers'
manifests (Q12; compiling to today's recipes first is possible but means writing the compiler twice). Each consumer
moves in one commit; the golden tests (R0) show the generated workflow unchanged, except for the build order where the
graph corrects it.

---

## 4. Target architecture

```
application   CLI · TUI (Textual) · generators (github, gitlab, vscode-tasks)
api           Project · Repo · Provider · Builder (CsCMake, Script, custom) → compiles to steps   (B13)
engine        Planner (configure → plan.json, cs.lock, graph, topological order) · Workspace (B12 policies,
              cs-workspace.local.toml) · Selector (ids / tags / dependencies)
              Executor · Policy (effects: print / ask / apply / skip) · EventBus · RunRecord
backends      local · container · github · gitlab · (jenkins)          ← handlers per step type
stores        GitHubReleases · LocalFolder · (GitLab packages, S3)     ← ReleaseStore
domain        Project · Step (id, tags, inputs, outputs, effects, when, actions) · Variant / Matrix
              Plan · Event · Diagnostic · Secret / Param / MatrixVar
foundation    file system, git, hashing, HTTP cache                   (portable/ removed: exec on the runner)
```

The import-linter contracts follow the new layers; `domain` stays free of I/O.

---

## 5. Roadmap

One phase at a time, CI green and every consumer's workflow regenerated (diff reviewed) before the next.

| # | Phase | Content | Estimate |
|---|---|---|---|
| R0 | Safety net | Releases of csorchestrator (CHANGELOG, tags, wheel), consumers pin it; version stamped in workflows and manifests; **golden tests** of the 8 consumers' workflows; public `csorchestrator.api` facade; "workflow up to date" check in consumer CI | 1–2 weeks |
| R1 | Checkout | B12 on the current model: `ls-remote` / one fetch, parallel, plain git, URL normalisation, policies `auto / keep / update / strict / reset`, `--offline`, `status`, `cs-workspace.local.toml` (`path`, `ref`); provenance in the manifest (ref, commit, tag, package version of every repository built) | 1–2 weeks |
| R2 | Core model | B1 (steps as data, handlers), B2 (event bus, Diagnostic, `Result[T]`, run record), B3 types (effects, Secret / Param / MatrixVar); adapter for the current API | 3–4 weeks |
| R3 | Configure stage | B4: pure `create_orchestrator`, `configure`, plan.json, cs.lock, manifest cache, offline, sha256; manifest schema v2 (declarative dependencies, test dependencies, system requirements); matrix from csCMake's `variants.json` (`TODO-cscmake-alignment.md`) | 2–3 weeks |
| R4 | Project API | B13: `Project` / `Repo` / `Provider` / `Builder`, topological build order, validation, `describe --graph`, manifest from the graph; consumers migrated one per commit (third_party_base_libs, csfoundation, csoptimization, applications; then csqt6, csopencvcpu, csopencvcuda with builders); `*_config.py` dropped | 3–4 weeks |
| R5 | Local experience | B6 selection (with the graph), variant selection, B7 actions and clean, B3 policy + pre-flight + `doctor`, B10 Markdown report + GitHub summary | 2–3 weeks |
| R6 | Runner exec mode | B5: `csorchestrator exec` on runners, smaller GitHub YAML, `csorchestratorsdk/` removed; ccache / `actions/cache`; per-project variant selection | 2 weeks |
| R7 | Interfaces | B9: Textual TUI (+ `textual serve`), `generate vscode-tasks` | 2–3 weeks |
| R8 | Backends | Local containers (+ bare-container deployment test), ReleaseStore, then GitLab if needed; Jenkins on demand | as needed |
| R9 | Ecosystem | `deps outdated / bump / check`; `ecosystem release` (the release train as a command, dry run by default); release notes across repositories; provenance / SBOM; documentation site and tutorial if going external | as needed |

R1 is independent of the refactor and gives the largest daily gain: it goes right after R0. R4 can start on the
current model (compiling to today's recipes) if it is wanted before R2–R3, at the cost of migrating its compiler
later.

### Checks per phase

- R0: golden tests pass on `dev`; a consumer regenerates with the pinned version and gets the same YAML except the
  version stamp.
- R1: a run with all repositories present and up to date makes one network operation per repository, in parallel
  (measured before / after on csfoundation); a dirty repository or a feature branch gives a warning, not an error, with
  `auto`; `strict` still fails; `reset` never runs without confirmation.
- R2: zero diff on the golden tests; coverage gate 70% (then 80% at R5); `--run-all` in a nightly job.
- R3: `describe` / `generate` run offline after one `configure`; the lock reproduces the same plan on another machine.
- R4: every migrated consumer generates the same workflow (golden tests) except the build order where the graph
  corrects it; a dependency cycle or an unknown provider library fails at configure; consumers build without the
  providers' `*_config.py`.
- R5: on a developer machine, a full run never calls `sudo` without consent; `clean` refuses a dirty repository.
- R6: generated workflows of every consumer green on every variant; a full rc of the release chain built with them.

### Risks

- A large refactor (R2–R4) while 8 repositories depend on csorchestrator: golden tests first, the adapter, one
  consumer per commit.
- Manifest schema v2 and the end of `*_config.py`: old releases (schema v1 + `*_config.py`) must stay consumable
  until every provider has a release with v2; the reader supports both.
- Generality creeping in: no Jenkins, no web GUI, no generic matrix until a real need.
- Overlap with `done/PLAN-stable-dev-ubuntu26mac-libs.md`: that plan finishes first; R0 goes into the next release cycle.

---

## 6. Decisions to take

| # | Question | Proposal |
|---|---|---|
| Q1 | Explicit configure stage (pure project script, plan.json, lock)? | Yes (B4) |
| Q2 | Runner exec mode (csorchestrator installed on runners, no inline Python, no vendored SDK)? | Yes (B5, R6) |
| Q3 | Distribution of csorchestrator: PyPI or tagged wheels on GitHub Releases? | GitHub first, PyPI when the API is stable |
| Q4 | TUI toolkit | Textual (+ `textual serve` instead of a separate GUI) |
| Q5 | Backends after GitHub | Local containers; GitLab only with a real user; Jenkins on demand |
| Q6 | Variant → runner mapping as data in csCMake (`ci` section next to `variants.json`)? | Yes, read by csCMake's smoke CI and by csorchestrator |
| Q7 | Manifests: declarative metadata, `*_config.py` optional? | Yes, with manifest schema v2 (R3) |
| Q8 | Default local checkout policy | `auto`: fast-forward when clean and on the ref, otherwise keep the repository as it is with a warning; `strict` in CI and for releases |
| Q9 | Local overrides in `cs-workspace.local.toml` (`path`, `ref`), git-ignored? | Yes (B12) |
| Q10 | Names of the high-level API | `Project`, `Repo` (`p.repo(...)`, `p.self_repo()`), `Provider`, `depends_on` / `test_depends_on`, `build`, `build_with(Builder)`, `system`, `publish` |
| Q11 | Drop `<name>_config.py` once consumers read dependencies from manifest v2? | Yes, after every provider has a v2 release (R4) |
| Q12 | Project API before the core refactor (compiling to today's recipes)? | No: after R3, so it compiles once, to the new model; R1 (checkout) covers the urgent part |

---

## 7. Quick fixes (independent of the plan)

- `csImgTracker_project.py`: the orchestrator is created with `create_orchestrator_factory_all_supported_cases`, then
  overwritten by `create_default_orchestrator`: drop the first.
- csopencvcpu provider in csImgTracker / csSkiTracker: `project_version="5.0.0"` with tag `v5.0.1-rc3`: check which
  one is meant.
- README: stale names (`3rdPartyBaseLibs`, `qt6.py`), test folder list.

## 7b. Requirements from the organisation plan (2026-11-20)

- **The release records ref, tag and commit of every repository built** (§4.3.6): in the manifest (R1), and a rebuild
  of an old release from its manifest (R3 lock file).
- **Release of an outer project with its inner repositories**: tag the inner repositories on the commits built (own
  semver for libraries, `-cs.N` for forks), move their `main`, then the outer release (R9 `ecosystem release`; a skill
  until then).

### 7c. Builds and releases (2026-11-20)

- Release candidates as pre-releases: the release job sets `prerelease` when the tag has `-rc` (done 2026-11-20).
- Builds on `main` (the trunk) and tags; none for `stable` or pull requests; a feature branch on demand (dispatch); the
  weekly schedule on `main` (done 2026-11-20).
- Later, an optimisation: a tag republishes the build of its commit (the `dev` run, its artifacts and the inner
  commits it recorded) instead of rebuilding; the final tag republishes the rc. Not a rule: a tag may always build.
- Schedule per project (e.g. monthly for csqt6).
- **Backlog from the organisation plan's minimal R0** (2026-11-21; `PLAN-cscosine-org.md` §7.3, §8 S2): a
  `pull_request` trigger for `main` in the generated workflows; a final `ci-ok` job (`needs:` all, `if: always()`)
  as the one stable check a ruleset can require; build once per commit (the republish above). Until then `main`
  builds after the merge.
- **Build after the checks** (2026-11-22, from `PLAN-cscosine-org.md` S8): the template's `.github/workflows/checks.yml`
  (full pre-commit in the project venv) runs beside the generated build workflow, not before it: a failed check does
  not stop the build. Later (R6, with the smaller generated YAML): `checks.yml` callable (`workflow_call`), the
  generated workflow calls it as its first job and the matrix `needs:` it, so a failed check skips the build (fewer
  builds). Then the template's tool `ci.yml` drops its own pre-commit step (it runs in every matrix job today) and
  calls `checks.yml` the same way. A ruleset requiring the checks on `main` is not the way: it ends direct commits.

## 8. Parking lot

**Local providers and multi-project runs** (added 2026-11-20; future, not scheduled). A local run already produces
what a release contains (archives, manifest, deploy folder). Use it as a provider:

- A **local release store**: a run of a provider (e.g. csfoundation, selecting only csVisOpenGL, B6) deploys to a
  local folder (`~/.cs/releases/<project>/<version-or-branch>/`) with the same manifest as a GitHub release. It is the
  `LocalFolder` ReleaseStore of B5 / R8.
- **Per-library provider selection in the consumer**: csImgTracker takes csVisOpenGL from that local store and
  everything else from the GitHub release. It is an explicit, manual choice (`cs-workspace.local.toml`, git-ignored:
  `[provider.csfoundation.libs.csVisOpenGL] store = "local"`), shown as a warning in every run and never allowed in
  CI or a release (`strict`). Consistency check: the local build must use the same versions of its own dependencies
  (csCore, third_party_base_libs, …) as the release it partially replaces, from the manifests; a mismatch stops the run.
- **Multi-project temporary workflows (GUI / TUI, B9)**: open several projects, compose a one-off run ("csfoundation:
  build + deploy csVisOpenGL locally → csImgTracker: build `main` variant with it"), run it, throw it away. Builds on B6
  (selection), B12 (workspace), the local store and the graph of B13.

Why this rather than building a provider library from source inside the consumer: it reuses the provider's own recipe
(build configuration, options, variants) unchanged, and it is the same mechanism as a real release, only stored
locally. It also gives the shortest loop for a project + library change (`PLAN-cscosine-org.md` §4.7). Until then that
loop is the release chain (rc of the provider), or a manual `CMAKE_PREFIX_PATH` to a local install.

Generic matrix axes (would allow csorchestrator's own CI); Azure Pipelines; web GUI; interoperability with vcpkg /
Conan registries (export, not compete).
