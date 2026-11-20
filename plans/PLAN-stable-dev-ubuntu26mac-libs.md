# Plan: stable `dev` with Ubuntu 26.04 + macOS and the updated third-party libraries

Date: 2026-11-16 · Status: **done** (2026-11-16; checked 2026-11-20), open: csCMake 0.x tags and `v1.0.0`, csopencvcuda (§4.9); review: `PLAN-review-stable-dev.md`

Goal: every project of the ecosystem on `dev` builds and releases on all the configurations (Linux 22.04 / 24.04 / 26.04
x64 + arm64, Windows, macOS 15 / 26 with Ninja Multi-Config and Xcode), with the updated third-party libraries, pipes
dropped and the Qt deployment and GUI-run helpers made part of csCMake / csorchestrator (D6). History on `dev`: a few
meaningful commits per project, no TEMP commits, no test tags.

The work done so far (`feature/ubuntu26mac`, `feature/update_libs`, test releases `-testu26mac` / `-testupdlibs`) is
the proof that it works; this plan re-applies it cleanly, plus the decisions below.

---

## 1. Decisions (agreed)

| # | Decision |
|---|---|
| D1 | `consumer_mapping` is **not** merged: a provider the consumer does not name means identity, as before. csImgTracker / csSkiTracker name `"csopencvcpu": "csopencvcpu_mapping"` (as `qt6_mapping`). |
| D2 | Release step: the generated-for-release files (manifest, bundle) are downloaded in a folder of their own, outside the archive globs: no file listed twice (replaces the filter of `eab30b2`). |
| D3 | OpenMP: `cs_target_use_openmp` (csCMake) does nothing on Apple Clang (message); a csCore header with `CS_OMP(...)` (`_Pragma` only with `_OPENMP`) and `maxThreads()` (1 without OpenMP). The pragmas of csNelson / csBlockMatrix use it: no macOS flags in their CMake. OpenMP vs thread pool: later, with their refactoring (2026-11-16, kept for now; to revisit: OpenMP not deprecated, but serial on macOS (Apple Clang), MSVC 2.0, runtime mixing, poor composition with other pools; options: `cs::parallelFor` in csCore over a small `std::jthread` pool (no dependency, parallel on macOS), or wrapping oneTBB (already in csopencvcpu) / Taskflow; C++17 parallel algorithms not portable (Apple libc++), C++26 `std::execution` not shipped yet). |
| D4 | csAssert: the header as a `.hpp.in` template (same design: one header, the levels as per-configuration compile definitions). |
| D5 | csVisOpenGL: core profile on macOS only (4.1); Linux / Windows keep the compatibility context until phase 2 of `docs/evolution-assessment.md`. Known macOS limitation until then: lines 1 px wide, points not smoothed. |
| D6 | First class: Qt deployment helper in csCMake, system requirements of the Qt plugins declared by csqt6, GUI-run recipe in csorchestrator. The smoke **check** stays in each application. |
| D7 | Qt **6.12.0** (LTS), macOS from **14.4**; the GPL-only Qt modules neither cloned nor built (list in csqt6 README). OpenCV: Xcode too if its test passes, then Qt is the only provider with a mapping. |
| D8 | macOS deployment target: **csCMake sets no value**, it only checks (§4.8). Each project declares its own `CMAKE_OSX_DEPLOYMENT_TARGET`; each package records the value it was built with; a dependency built for a newer macOS than the consumer → FATAL_ERROR "raise to ≥ X". Lower is always fine. |
| — | pipes dropped (no consumer but the csCore `pipes` wrapper). tclap, NamedType, tl-optional, tl-expected, fmt-eigen, magic_enum stay. |

---

## 2. Way of working (every repository)

1. Branch **`feature/stable-dev`** from `dev`; the final content as a few curated commits (listed per project in §4),
   built from the old feature branches (squash / cherry-pick + clean-up), not a merge of them.
2. One extra commit **"CI on feature/stable-dev"** (`on_push_branches`, regenerated workflow) only while the branch
   runs CI; for first-party libraries built by a consumer (csCore, csVisOpenGL, csBlockMatrix, csNelson) the consumer
   (csfoundation, csoptimization) points to `feature/stable-dev` in that same extra commit.
3. Branch CI green on every config (+ smoke runs) → drop the extra commit → `git merge --no-ff` into `dev`
   ("Merge feature/stable-dev: …", as `feature/productize`) → `dev` CI green → **rc tag on `dev`** → release
   checked (assets count, Latest).
4. A consumer starts only after its providers have the rc release (release chain below).
5. Forks (third-party libraries): their update is a rebase on a new upstream tag, so `dev` is **moved** to the new
   branch (force push) and the old `dev` kept as a tag `legacy-<old version>`. Needs explicit OK (§6, Q1).

Chain: csorchestrator, csCMake → third_party_base_libs (+ forks) → opencv fork, csopencvcpu, csqt6 → csCore,
csVisOpenGL, csBlockMatrix, csNelson → csfoundation → csoptimization → csImgTracker, csSkiTracker.

---

## 3. Releases

| Project | Now (Latest) | After |
|---|---|---|
| csorchestrator | no releases (used locally to generate the workflows) | `dev` merged |
| csCMake | v1.0.0-rc4 (Latest: v0.4.0) | **v1.0.0-rc5** |
| third_party_base_libs | v0.1.0-rc6 | **v0.1.0-rc7** |
| opencv fork | tag v5.0.2-cpu (branch `dev-cpu`) | **new tag**, e.g. `v5.0.2-cpu.1` (Q2) |
| csopencvcpu | v5.0.1-rc3 | **v5.0.1-rc4** |
| csqt6 | v6.11.1-rc3 | **v6.11.1-rc4** (full Qt rebuild, ~2.5 h per macOS job; Q3) |
| csfoundation | v0.1.0-rc8 | **v0.1.0-rc9** |
| csoptimization | v0.1.0-rc4 | **v0.1.0-rc5** |
| csImgTracker / csSkiTracker | v0.1.0-rc1 | **v0.1.0-rc2** |

Every project moves to csCMake **1.0.0-rc5** (today rc1 in most, rc4 in the applications).

---

## 4. Per project: commits and checks

### 4.1 csorchestrator
Commits:
1. *Ubuntu 26.04 and macOS (15, 26; Apple Clang; Ninja, Ninja Multi-Config, Xcode) as opt-in variants* — today
   `52b9384`, `369207f`, `2e48427` (`get_supported_os_version_list` keeps the defaults,
   `get_all_supported_os_version_list`), with their tests.
2. *Release: the generated-for-release files in a folder of their own* (D2) — replaces `eab30b2`.
3. *GUI deployment run on the CI runners* (D6): a recipe (e.g. `add_gui_deployment_run(o, deployment, command, …)`)
   with xvfb on Linux, Mesa llvmpipe on Windows (`opengl32sw.dll`), the session desktop on macOS, the environment
   (`QT_OPENGL`, `QT_FORCE_STDERR_LOGGING`, `GALLIUM_DRIVER`); and the **runtime system requirements of a provider**
   (e.g. the xcb packages of csqt6) installed with its download, before the build (the deployment resolves the
   plugins at install).

Not merged: `88f84ef` (`consumer_mapping`, D1).
Checks: unit tests, lint; generation of every project's workflow (diff reviewed).

### 4.2 csCMake
Commits:
1. *macOS deployment target 13.3* (`cs-host-macos`; the float `std::to_chars` of Apple libc++) — today `2069a6f` +
   `904553e`, with docs, test, CHANGELOG.
2. *Qt deployment helper* (D6), `qt/` folder: one function (e.g. `cs_deployment_qt_gui(<deployment> [OFFSCREEN])`)
   with the plugins and folders per OS (platforms; xcb GL / wayland on Linux; `bin/platforms` on Windows / macOS;
   `opengl32sw.dll` on Windows). First check whether Qt's `qt_deploy_runtime_dependencies` fits with
   `cs_deployment`; if it does, the helper wraps it.
3. *`cs_target_use_openmp`: nothing on Apple Clang* (D3).

Checks: csCMake tests; release **v1.0.0-rc5**.

### 4.3 third_party_base_libs and the forks
Forks (`dev` moved, old `dev` tagged `legacy-*`; Q1):

| Fork | New `dev` |
|---|---|
| eigen3 | upstream 5.0.1 + 1 commit (csCMake presets, tests / BLAS / LAPACK / demos / docs off); replaces the 3.4.0 downloader (its macOS fix is obsolete) |
| fmt | 12.2.1 + our commits, incl. the Xcode `format-impl-test` fix |
| cpptrace | 1.0.4 + our commits |
| libassert | 2.2.1 + our commits + `LIBASSERT_USE_EXTERNAL_CPPTRACE` ON |
| magic_enum | 0.9.8 + our commits + clang-cl test flag |
| Catch2 | 3.16.1 + our commits |
| tl-expected | 1.3.1 + our commits |
| tl-optional | 1.1.0 commit + package version 1.1.0 |
| pipes | not merged: repository archived on GitHub, kept as a reference in TODO.md |

third_party_base_libs commits:
1. *Ubuntu 26.04 and macOS variants* (matrix, `actionlint.yaml`).
2. *Libraries updated to their latest upstream release* (incl. libassert → cpptrace dependency).
3. *pipes dropped* (repository list, dependency declarations).
4. *TODO: state after the merge* (assessment, shortlist of candidate libraries, open points).

Checks: 20 configs; package checks (no runner / Homebrew library linked, `minos 13.3` on macOS, one cpptrace only);
release **v0.1.0-rc7**.

### 4.4 opencv fork, csopencvcpu, csqt6
- opencv fork (`dev-cpu`): the 3 commits as they are (`@loader_path` on macOS; KleidiCV with GCC ≥ 15; contrib
  freetype off on macOS); tag (Q2).
- csopencvcpu, commits:
  1. *Ubuntu 26.04 and macOS 15 / 26 (Ninja Multi-Config)*: matrix, macOS step, `csopencvcpu_mapping`
     (Xcode → Ninja Multi-Config), opencv tag, csCMake rc5.
  2. *third_party_base_libs rc7 (Eigen 5)*: from `feature/update_libs`.

  Release **v5.0.1-rc4**.
- csqt6, commits:
  1. *Ubuntu 26.04 and macOS 15 / 26 (Apple Clang, Ninja)*: matrix, `qt6_mapping` for macOS, macOS phase (free disk),
     deployment target 13.0, configure options in one string (`QT_CONFIGURE_OPTIONS`, MySQL / PostgreSQL drivers off).
  2. *Runtime system requirements of the Qt plugins* (D6: the xcb packages) for csorchestrator.

  Release **v6.11.1-rc4** (Q3).

### 4.5 First-party libraries (built by csfoundation / csoptimization)
- csCore:
  1. *csAssert: one header, the levels as per-configuration compile definitions* (Xcode), as a `.hpp.in` template
     (D4); Readme section.
  2. *OpenMP helper* (`CS_OMP`, `maxThreads`) (D3).
  3. *pipes module removed*.
- csVisOpenGL:
  1. *macOS: 4.1 core profile, the GLSL `#version` of the context* (D5).
  2. *Sample: deployment (csCMake Qt helper) and `--smoke`*.
- csBlockMatrix:
  1. *`SparseCoeffDiagonalMatrixBlock`: `outerSize()` out of `InnerIterator`* (GCC 15).
  2. *OpenMP through csCore* (no macOS flags; only the sample uses pragmas).
- csNelson: 1. *OpenMP through csCore* (pragmas → `CS_OMP`, `ParallelExecHelper` → `maxThreads`; no macOS flags).
- csLie, csCamera: no change.

Checks: local build + tests (Ninja and Ninja Multi-Config; csCore 289 tests); then through csfoundation /
csoptimization CI. **First build of these libraries with Eigen 5, fmt 12, cpptrace 1.0, libassert 2.2.**

### 4.6 csfoundation, csoptimization
- csfoundation: 1. *Ubuntu 26.04 and macOS; the csVisOpenGL sample deployed and run* (GUI-run recipe of
  csorchestrator, D6; no Qt xcb code in the project; pipes out of the csCore dependencies). Release **v0.1.0-rc9**.
- csoptimization: 1. *Ubuntu 26.04 and macOS*. Release **v0.1.0-rc5**.

### 4.7 csImgTracker, csSkiTracker
One commit each: *Ubuntu 26.04 and macOS; deployment (csCMake Qt helper) and smoke run (csorchestrator recipe, the
application's own `--smoke`); `csopencvcpu_mapping` named*. Release **v0.1.0-rc2**.
Not included: the clang-format drift of csSkiTracker `dev` (separate commit, if wanted).

### 4.8 macOS deployment target (D8), next round after csfoundation rc9
Rule: the project's value must be ≥ every dependency's value; below → stop with "raise `CMAKE_OSX_DEPLOYMENT_TARGET`
to ≥ X". Header-only libraries need no check (Apple's compiler already says "`to_chars` is unavailable: introduced in
macOS 13.3").

| Who | Sets | Checks / records |
|---|---|---|
| csCMake | nothing: 13.3 removed from `cs-host-macos` (`config-hosts.json`), docs + CHANGELOG | `cs_require_macos_deployment_target(<v> REASON …)`; records the value at install of every project built with its presets (`CMAKE_PROJECT_INCLUDE` from the macOS host preset: a csCMake script included after the top-level `project()`, which installs `share/cscmake/<project>.macos-deployment-target`; upstream CMakeLists untouched); `cs_find_package` compares each dependency's recorded value; no knowledge of any specific library outside its integrations (Qt: csQt, row below); warning when the project sets no value (binaries then built for the runner's macOS) |
| csorchestrator | nothing | nothing |
| third_party_base_libs forks | in each fork's `csCMakeProjectSetup.json`, preset `cscmake-project-setup-macos` (level 3 of csCMake's presets doc): cpptrace, magic_enum **13.3**; the others their real minimum | — |
| third_party_base_libs | baseline `MACOSX_DEPLOYMENT_TARGET` in its CI for every fork without its own value | — |
| csqt6 | 14.4 (already, `MACOS_CONFIGURE_CMAKE_ARGS`) | nothing: Qt ships its minimum itself (`QT_SUPPORTED_MIN_MACOS_VERSION`, `Qt6ConfigExtras.cmake`) |
| csCMake Qt plugin (`modules/integrations/csQt.cmake`) | — | a hook for `Qt6` (`cs_add_after_find_hook`, run by `cs_find_package` and by generated Configs after `find_dependency`): check against `QT_SUPPORTED_MIN_MACOS_VERSION`. Net at the end of the project: Qt loaded but never checked (plain `find_package`) → FATAL_ERROR "use cs_find_package"; bypass `CSCMAKE_QT_ALLOW_FIND_PACKAGE=ON` (named in the error message): warning, check still done from `${Qt6_DIR}/Qt6ConfigExtras.cmake`. No `cs_find_qt` |
| first-party libraries, csfoundation, csoptimization, applications | their value in `cscmake-project-setup-macos` (Qt consumers ≥ 14.4) | through `cs_find_package` |

Scenario check: csCMake none, Qt 14.4, other lib 15, app 16 → passes; app 15 with a lib built for 16 → stops at that
lib's `find_package`.
Size: csCMake ~150 lines (hooks, check, recorder, Qt hook + net, docs in code) + 23 tests + user guide (hooks: how to add one); one preset per fork / project.
Releases: csCMake rc6, third_party_base_libs rc8, then down the chain as in §2.

### 4.9 Clean-up
- Delete the test releases and tags: `-testu26mac` (csCMake, third_party_base_libs, csqt6, csopencvcpu, csfoundation,
  csoptimization), `-testupdlibs` (third_party_base_libs); check the Latest of every repository.
- Delete the branches `feature/ubuntu26mac` (all), `feature/update_libs` (all), `feature/stable-dev` (all).
- TODO.md of third_party_base_libs: section 4 marked done; memory note of the release chain updated.
- csCMake 0.x (from the csCMake 1.0 migration notes, deleted 2026-11-20): delete the tags `v0.1.0`, `v0.2.0-rc1`,
  `v0.2.0`, `v0.3.0`, `v0.4.0` and their GitHub Releases (ask first: cannot be undone; today `0.4.0` is still shown as
  Latest), then release csCMake `v1.0.0` if no rc needs an API change.
- csopencvcuda: not in this plan; it still pins csCMake `1.0.0-rc2` (the others `1.0.0-rc6` / `rc7`). Decide: align it
  in this round or in the next one.

---

## 5. Risks and fallbacks

| Risk | Where it shows | Fallback |
|---|---|---|
| Eigen 5 API changes in csCore / csLie / csBlockMatrix / csNelson | csfoundation / csoptimization CI (4.5) | fix in the library; or third_party with Eigen **3.4.1** (same API) and Eigen 5 on its own branch |
| fmt 12 / cpptrace 1.0 / libassert 2.2 in csCore (fmt-eigen, csAssert) | csfoundation CI | fix in csCore; or the previous version of that library only |
| `qt_deploy_runtime_dependencies` does not fit `cs_deployment` | csCMake (4.2) | the helper with our own per-OS lists (what works today) |
| csqt6 rebuild time / flakiness | 4.4 | re-run failed jobs only |
| A provider rc re-tagged while a consumer downloads | any | never re-tag while a consumer runs; cancel first |

---

## 6. Questions before starting

- **Q1** Forks: move `dev` to the updated branch (force push) and tag the old `dev` as `legacy-<version>`? (Needed
  because the updates are rebases on new upstream tags.)
- **Q2** opencv fork tag name for the 3 fixes: `v5.0.2-cpu.1`, or another convention?
- **Q3** csqt6: full rebuild for rc4 (D6 requirements + shared configure string), OK?
- **Q4** `main` / `cs-main` branches and non-rc releases: out of this plan (a later promotion), OK?
