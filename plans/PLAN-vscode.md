# Plan: VS Code on a project of the workspace, as an IDE

Status: experiment positive (2026-11-22); reviewed 2026-11-23 (§4: Windows / macOS, extensions, library / standalone /
mixed), revised steps in §5 replace §3. Decisions of 2026-11-23: §4.7.

## 0. Why

A developer runs csorchestrator once (or only up to the dependencies of the library they work on), then works on one
repository in VS Code alone, as in Visual Studio: pick the configuration, build, run or debug one test or the
application, install for the next library, all from the IDE. The build folders are csorchestrator's own (no second
build, no `dev` presets): VS Code attaches to them.

## 1. The experiment (csLie, branch `feature/vscode-setup`, commit `d706e21`)

- `open-code.sh [filter]` (repository root): finds the builds of the repository in `<workspace>/build/*/<repository>`
  (the cache's `CMAKE_HOME_DIRECTORY` must be this checkout), keeps the one whose folder name or C++ compiler matches
  the filter (several and no filter: lists them and stops), writes `<build>/<repository>.code-workspace` from its
  `CMakeCache.txt` (rewritten only when its content changes: an open window reloads it) and runs `code` on it.
- The workspace file (build-specific): `cmake.useCMakePresets: never`, `cmake.sourceDirectory`, `cmake.buildDirectory`
  (absolute), `cmake.generator` (from the cache), `cmake.cmakePath` / `cmake.ctestPath` (`CMAKE_COMMAND` /
  `CMAKE_CTEST_COMMAND` of the cache; a snap path `/snap/<name>/<rev>/` written as `/snap/<name>/current/`),
  `cmake.configureOnOpen`, `cmake.defaultVariants` (the build types = `CMAKE_CONFIGURATION_TYPES`, Debug first),
  `clangd.arguments` (`--compile-commands-dir=<build>`, `--background-index`, `--header-insertion=never`).
- `.vscode/` (shared by every build): `settings.json` (cpptools IntelliSense off, clangd on; Test Explorer grouped by
  `" - "`; `cmake.ctest.debugLaunchTarget`), `launch.json` ("Debug the CTest test": `${cmake.testProgram}` /
  `${cmake.testArgs}`; "Debug the launch target": a Catch2 test spec prompt; gdb, lldb on macOS), `tasks.json`
  (pre-commit). README: "Working in VS Code".
- Verified: the script (no filter, unknown filter, gcc, clang), the workspace files (valid JSON), a reconfigure as CMake
  Tools does it (`-G "Ninja Multi-Config" -DCMAKE_EXPORT_COMPILE_COMMANDS=TRUE`) on csorchestrator's cache, Debug-only
  build, one test by filter, the CTest list the Test Explorer reads; in VS Code by the user: kit, configure, targets,
  outline ("looks almost nice").
- `.vscode/` is a template part: the branch is the experiment, not merged as is (V5 moves the parts to their owners).

### What the experiment found

| Finding | Consequence |
|---|---|
| `cmake --list-presets=all` in a project: 479 lines (every OS / distro / arch / compiler) | the preset list is unusable in VS Code; conditions can filter on the OS only |
| CMake Tools 1.25: no setting selects a configure preset or a kit; the choice is per workspace state | one choice per window, remembered; a workspace file per build gives one state per build |
| Without presets CMake Tools asks for a kit; `[Unspecified]` (`__unspec__`) keeps the cache's compiler | one click the first time per window (V3) |
| Without presets CMake Tools picks its own generator (Ninja) | `cmake.generator` from the cache, else the configure fails on the generator mismatch |
| Its build types are Debug / Release / MinSizeRel / RelWithDebInfo | `cmake.defaultVariants` from `CMAKE_CONFIGURATION_TYPES` (csLie's Paranoid) |
| CMake as a snap: VS Code reports "bad CMake executable" (`/snap/bin` not on its PATH) | `cmake.cmakePath` / `cmake.ctestPath` from the cache, absolute |
| csCMake reads no preset-only environment at configure (Linux; only `MACOSX_DEPLOYMENT_TARGET` on macOS) | a reconfigure without the preset is safe: everything is in the cache |
| Folder `.vscode/settings.json` overrides the workspace file for resource-scoped settings | build-specific keys only in the workspace file, never in `.vscode/` |
| clangd: one compile database; `clangd.arguments` is window-scoped | `--compile-commands-dir=<build>` in the workspace file; nothing copied into the sources |
| Build folder names: csorchestrator uses short ones on purpose (`v1lu22.04x64ggdnm`, Windows path length) | the script matches the cache, not the name; csorchestrator knows both (V5) |
| Shift+F5 / Ctrl+Shift+F5 build before running (`cmake.buildBeforeRun`); F5 from Run and Debug does not | `preLaunchTask` in `launch.json` (V4) |

## 2. Decisions and options discussed (2026-11-22, with the user)

- **Attach to csorchestrator's build folders**, no user presets (`dev`, …): sharing them is fine. One window per build
  (gcc and clang side by side), not a compiler switch inside one window.
- **Who writes the workspace file** (V5): csCMake at configure time, opt-in through a `$penv{…}` switch in
  `cscmake-common-project-setup` (as `CSCMAKE_PREFIX_PATH_HEAD`), written with `file(CONFIGURE)` (only when changed),
  top-level project only: exact paths, any way of configuring, generic. Or csorchestrator after it configures (knows
  every repository and the short names). The script stays as the entry point (finds and opens).
- **Preset filter** (optional, V8, for those who use presets): csCMake's `cs-host-<os>` presets
  (`presets/common/config-hosts.json`) get `allOf(host, anyOf($penv{CSCMAKE_PRESETS_FILTER} empty, matches
  ${presetName}))`; tested on a mock: only the matching configure presets and their build / test presets remain; unset,
  nothing changes (CI).
- **csfoundation as one multi-root window** (V7): one root per library, `cmake.buildDirectory` with
  `${workspaceFolderBasename}`, `cmake.copyCompileCommands` per root for clangd. The catch: the libraries meet through
  `install/` (go-to-definition opens the installed copy of a header; build order by hand). Options: a "rebuild the chain"
  task; symlinked installs for local work (`CMAKE_INSTALL_MODE=REL_SYMLINK_OR_COPY`, never in csorchestrator: the
  archives); a superbuild by a dependency provider rejected (each library is a top-level `cs_initialize_project` with
  its own configurations).
- csorchestrator "only the dependencies of X" (`--until` / `--skip`): to check what `run` offers (V6).

## 3. Steps

| # | Step | Content | Status |
|---|---|---|---|
| V0 | Experiment | csLie `feature/vscode-setup` (§1) | done |
| V1 | Choosing the build | No argument: automatic by a priority chain (gcc before clang; configurable, e.g. an env variable) and says which; `--list`: one line per build (`gcc : csv1-linux-…-gcc-…`, `clang : csv1-…`) and what differs between them (compiler and version, generator, configurations, cmake version, last configure); `--ui`: a small TUI picker of the builds; a filter argument as now. CMake: the one of the cache by default (automatic), `--cmake <path>` to override | todo |
| V2 | Windows (and macOS) | `open-code.ps1` with the same options; the priority chain over the Windows builds (msvc, msvcclang; ninja / ninjamulticonfig / Visual Studio generators) and their configurations; the cache's cmake (Visual Studio's or another); `cppvsdbg` in `launch.json` for MSVC; long paths (short folder names); macOS: lldb, appleclang | todo |
| V3 | No kit prompt | e.g. `cmake.additionalKits` with a kit file of the build's own compiler, or whatever CMake Tools allows by then; else the README line "pick `[Unspecified]`" | todo |
| V4 | Build before every run | `preLaunchTask` (CMake: build) in both `launch.json` configurations; check that a Test Explorer run builds first | todo |
| V5 | Owners | `.vscode/` (settings, launch, tasks) to the template (C++ projects); the workspace-file writer to csCMake (opt-in) or csorchestrator (decide); `open-code.sh` / `.ps1` to the template; the csLie experiment branch then deleted | todo |
| V6 | csorchestrator up to a project | run only the dependencies of a repository (prepare `libs/`, `install/`, configure it), then VS Code takes over | todo |
| V7 | csfoundation multi-root (optional) | the workspace of §2, with symlinked installs as an opt-in | todo |
| V8 | Preset filter (optional) | `CSCMAKE_PRESETS_FILTER` in csCMake (§2) | todo |
| V9 | Roll out | csCore, csCamera, csVisOpenGL, csNelson, csBlockMatrix, the applications (a launch target that is an application, not tests) | todo |

## 4. Review (2026-11-23)

### 4.1 The script, as it is

- Linux, sibling layout: works (re-run 2026-11-23: no filter lists both builds, `clang` writes the workspace file).
- It only looks in `<repo>/../build/*/<repo>/CMakeCache.txt`. csCMake's binaryDir is
  `<CSCMAKE_WORKSPACE_ROOT>/build/<sub>/<sourceDirName>/<single-config sub>`, so it misses:
  - the **standalone** layout (csImgTracker, csSkiTracker): `<project>/workspace/build/<sub>/<project>`;
  - the **env** layouts: `$CSCMAKE_WORKSPACE_ROOT/build/...`;
  - **single-config** builds (the arm64 Ninja variants): one more level, `.../<repo>/debug|release|relWithDebInfo`.
  Fix: search `<repo>/workspace/build`, `<repo>/../build` and `$CSCMAKE_WORKSPACE_ROOT/build`, depth 2 and 3, keep the
  caches whose `CMAKE_HOME_DIRECTORY` is this checkout (already the check).
- JSON written by string concatenation: fine with Linux paths, breaks on a quote or backslash. A generator that builds
  the object and serialises it is safer (a must on Windows).
- macOS: the bash is 3.2-compatible as written (no `mapfile`, empty arrays never expanded); `code` must be installed
  in PATH by hand (VS Code: "Shell Command: Install 'code' command in PATH"). Not run on a Mac.
- Windows: the bash script cannot serve (Git Bash sees `/c/...`, the cache says `C:/...`): a real `open-code.ps1`
  (V2), or one implementation in Python (§4.6).

### 4.2 Windows and macOS: what changes per build

| Build | IntelliSense | Debugger | Environment |
|---|---|---|---|
| Linux gcc / clang, Ninja (Multi-Config) | clangd on the compile database | cppdbg + gdb | none |
| macOS appleclang, Ninja Multi-Config | clangd | cppdbg + lldb (or CodeLLDB, to try) | none |
| macOS, **Xcode** generator | **no compile database**: cpptools + CMake Tools provider | lldb | none |
| Windows msvc / msvcclang, **Visual Studio** generator (the default variants) | **no compile database**: cpptools + CMake Tools provider | **cppvsdbg** | none (the generator finds MSVC) |
| Windows msvc / msvcclang, Ninja | clangd (reads cl / clang-cl commands) | cppvsdbg | **the MSVC dev environment**: a kit with `environmentSetupScript` = the `vcvars64.bat` next to the cache's `cl.exe` (`cmake.additionalKits`), not "launch from a Developer prompt" (a running VS Code keeps its own environment) |

Consequences:
- The engine choice is per build, so it belongs to the generated workspace file, not `.vscode/settings.json`:
  `C_Cpp.intelliSenseEngine` (`disabled` or `default`), `clangd.enable` (exists, clangd 0.6.0),
  `C_Cpp.default.configurationProvider: ms-vscode.cmake-tools`. The template's `.vscode/settings.json` today has
  `C_Cpp.intelliSenseEngine: disabled` and `clangd.arguments`: both move out (a folder setting wins over the workspace
  file for resource-scoped keys).
- Debugging: `type` cannot be platform-specific in `launch.json` (`windows: {type: …}` is not allowed). CMake Tools 1.25
  picks the debugger from the cache by itself (cppvsdbg for MSVC, gdb / lldb otherwise) when debugging a target or a
  test without a launch configuration (`cmake.ctest.neverDebugTestsWithLaunchConfiguration: true`), and
  `cmake.debugConfig` adds `args` / `cwd`. So: Test Explorer debug and "Debug target" need no `launch.json`; the
  "Catch2 test spec" configuration goes into the generated workspace file (`launch` section), with the right `type`
  for the build. To verify on each OS.
- Windows path length: the short build folders (`v1wv10x64gm22nm`) are the csorchestrator default there; the finder
  matches caches, not names, so nothing to do.
- Generator preference when several builds: Ninja Multi-Config > Ninja > Visual Studio / Xcode (clangd, faster);
  on Windows msvc > msvcclang, on Linux gcc > clang (V1 priority chain).

### 4.3 Extensions

| Extension | Verdict |
|---|---|
| ms-vscode.cmake-tools | keep (≥ 1.25: `cmake.debugConfig.type`, test debugging without launch.json) |
| llvm-vs-code-extensions.vscode-clangd | keep; disabled per build where there is no compile database |
| ms-vscode.cpptools | keep: debugger everywhere, IntelliSense for Visual Studio / Xcode builds |
| ms-python.* , charliermarsh.ruff, ms-python.mypy-type-checker | keep (projects, tools) — not for a library window |
| bierner.markdown-mermaid, iulian-radu-at.vscode-tasks-sidebar | keep |
| vadimcn.vscode-lldb (CodeLLDB) | add for macOS if cpptools' lldb-mi disappoints on arm64 (try first) |
| twxs.cmake | not recommended (abandoned; CMake Tools has CMake language support); no `unwantedRecommendations` (user, 2026-11-23) |
| ms-vscode.cpptools-extension-pack | not needed (pulls themes) |
| a Catch2 test adapter (matepek) | not needed: catch_discover_tests + CMake Tools already give one Test Explorer entry per test case; it would duplicate them |

Formatting: `editor.formatOnSave` with clangd formats with clangd's own clang-format (here 18…23 installed),
pre-commit pins clang-format **20.1.4**: format on save and the hook can disagree. Options: no format on save for
C/C++ (pre-commit is the authority), or `clang-format==20.1.4` in the venv + `xaver.clang-format` pointed at it.
Proposal: the first (simple), revisit later.

### 4.4 Library, standalone, mixed: one model

Every C++ source root of a project builds at `<project>/workspace/build/<sub>/<root folder name>`:
- library (csLie in csfoundation): `csfoundation/workspace/build/<sub>/csLie`;
- standalone (csImgTracker): `csImgTracker/workspace/build/<sub>/csImgTracker` (the project root is the source);
- mixed (a project with its own sources and checked-out libraries): both of the above under the same `<sub>`.

So a window = a **project** + a **variant** (`<sub>`) + a list of **roots** (the project itself if it has a
`CMakeLists.txt`, and any `workspace/<repo>` asked for). In a `.code-workspace` with several folders the settings are
window-wide, and one value serves every root: `cmake.buildDirectory: <project>/workspace/build/<sub>/${workspaceFolderBasename}`
(single-config: `+/<config sub>`). clangd has one compile database per window: with one root,
`--compile-commands-dir=<build>` (nothing in the sources, gcc and clang windows side by side); with several roots,
`cmake.copyCompileCommands: ${workspaceFolder}/compile_commands.json` (gitignored; one variant at a time for these
roots). The roots still meet through `install/`: the project sees a library change after its build + install (a
"build and install the chain" task; V7's symlinked installs).

Python: a project window also gets `python.defaultInterpreterPath` = the project's `.venv` (`bin/python` or
`Scripts\python.exe`), so it no longer depends on the shell that started `code`.

### 4.5 Template impact

- Today: `open-code.*` and `.vscode/settings.json` are excluded for `kind == library`; the library gets
  `extensions.json` only. That matches "a library is opened from its project": keep it, the library gets nothing new
  (except, possibly, the C++ part of `extensions.json`).
- `project`: `open-code.sh` / `.ps1` become `open-code [--build <filter>] [--list] [<repo> ...]` (no repo: the project
  itself; `<repo>`: a checked-out library, alone or with the project); `.vscode/settings.json` loses the C/C++ engine
  keys; `extensions.json` as in §4.3; `.gitignore` gets `compile_commands.json`; README "Working in VS Code".
- `tool`: unchanged (Python only).

### 4.6 Decision: where the logic lives

| Option | For | Against |
|---|---|---|
| A. `open-code.sh` + `open-code.ps1` in the template (as now) | no dependency | two implementations, JSON by hand, Windows / macOS only tested by hand |
| B. **csorchestrator** (`csorchestrator vscode …`, Python, the venv of the project has it), template scripts = activate venv + call it | one implementation, JSON by `json.dump`, tested by pytest on the 3 OS in csorchestrator's CI; csorchestrator already knows the layout, the variants, the short names and the repos of the project | a csorchestrator release to change it; libraries depend on the project's venv (already the case) |
| C. csCMake at configure (`file(CONFIGURE)`, opt-in) | exact, any way of configuring | per build only: knows neither the project's other roots, the venv, nor the choice between builds |

Recommendation: **B**, with the finder logic in `portable/` style (stdlib only). The experiment's bash stays the
reference until B exists.

### 4.7 Decisions (2026-11-23, with the user)

- **Simplest consistent setup**: option A for now, the scripts `open-code.sh` + `open-code.ps1` (not a .bat). Ideally
  csorchestrator fills in the build folder (it knows it): later, B stays the direction.
- Layouts: **standalone and sibling** (inner) only; the **mixed** case dropped for now (V8 parked); **macOS out** for
  now (V4 parked; the scripts keep the harmless `osx` lines).
- One click the first time is fine if documented: the kit `[Unspecified]` stays (CMake Tools keeps the kit only in the
  window state, no setting preselects it). The script prints the steps and opens the README at "Working in VS Code"
  (`code <workspace> --goto README.md:<line>`).
- One `.vscode/settings.json` for every OS: it keeps only what is the same everywhere; what depends on the build
  (IntelliSense engine: clangd or cpptools; debugger: gdb `cppdbg` on Linux, `cppvsdbg` on Windows; generator platform
  / toolset) goes in the generated workspace file, `launch` included (`.vscode/launch.json` removed).
- One script for every kind: with a `.venv` (projects, tools) it activates it and sets `python.defaultInterpreterPath`
  in the workspace file; no `CMakeLists.txt`, or no build yet: it opens the folder with the venv only (the template's
  current venv-only `open-code` behaviour). An application gets Python and C++ in one window.
- No folder names in the scripts: the workspace root comes from the csCMake layout the repository declares in
  `csCMakeProjectSetup.json` (standalone: `<repo>/workspace`, sibling: the parent folder, env:
  `$CSCMAKE_WORKSPACE_ROOT`), the builds from csCMake's `<workspace root>/build`. cmake / ctest: the absolute paths in
  the build's cache. VS Code: its `code` command on the PATH, else the script says which file to open.
  Template (V7): the copier answer `workspace_dir` and csCMake's standalone layout (`${sourceDir}/workspace`, also the
  include path of csCMakeProjectSetup.json) must agree: drop the question or make the layout follow it.
- `setup.sh` / `.ps1` end with: activate, run the recipe, `./open-code.sh` (no more `code .`).
- Done on csLie `feature/vscode-setup` (unstaged): both scripts, standalone + sibling + single-config search, venv,
  README section. Tested on Linux (real csLie builds; fake
  caches for standalone, single-config, Visual Studio generator). `open-code.ps1` not run yet (no PowerShell here).

### 4.8 The workspace folder (next, after V7; 2026-11-23, with the user)

- The name `workspace` is fixed by csCMake's standalone layout (`${sourceDir}/workspace`, also in the projects'
  include paths of `CMakePresets.json` / `csCMakeProjectSetup.json`) and the recipes' `base_target_dir`; the template
  answer `workspace_dir` only looks configurable (all 8 projects: `workspace`).
- W1 csCMake owns the name: documented with the layouts (another place: the `env` layout).
- W2 template: drop the answer `workspace_dir` (the name literal in `.gitignore`, `pyproject.toml`,
  `.vscode/settings.json`, README) and delete the unused key from every `.copier-answers.yml` in the update commit.
- W3 csorchestrator, in its csCMake part (`frontend/cscmake_presets`): a repository declaring a standalone layout needs
  `base_target_dir` = the layout's folder, checked at the start with a clear message; a recipe without csCMake chooses
  its folder freely.
- W4 the name itself: `<clones>/workspace/<project>/workspace` is confusing when the clones' folder is also called a
  workspace. Candidates: `_cs` (short, sorts first, not a Python package name), `cs-run`, `.cs` (hidden: less clutter,
  harder to find); not `csorchestrator` (would shadow the package when the recipe runs from the root). A rename
  touches csCMake's layout, every project's include paths and recipe, the template: one coordinated change with W1–W3.

## 5. Steps (revised 2026-11-23, replace §3)

| # | Step | Content | Status |
|---|---|---|---|
| V0 | Experiment | csLie `feature/vscode-setup` (§1) | done |
| V1 | Decide §4.6 | A for now (§4.7) | done |
| V2 | Generator | (in the scripts, §4.7: done on Linux) find builds (3 search roots, depth 2–3, single-config), `--list`, priority chain + filter, roots (project / repos), engine / debugger / kit per build (§4.2), workspace file by `json.dump`, written only when changed; pytest with fake caches of the 3 OS | todo |
| V3 | Windows | try on a Windows machine: Visual Studio generator (cpptools), Ninja + vcvars kit (clangd), cppvsdbg, Test Explorer | todo |
| V4 | macOS | try on a Mac: Ninja Multi-Config + lldb, Xcode + cpptools; CodeLLDB if needed | todo |
| V5 | Kit prompt | `[Unspecified]` the first time (Linux / macOS / VS generator); the generated kit on Windows Ninja: check whether CMake Tools can preselect it | todo |
| V6 | Build before run | `preLaunchTask` for the generated Catch2 configuration; Test Explorer run builds first? | todo |
| V7a | Template (2026-11-23, cs-project-template `feature/vscode-setup`, unstaged) | `open-code.*` for every kind and repository on the template (libraries and the forks on the template included; a fork not on the template gets nothing); `.vscode/settings.json` without the C/C++ engine keys (a library: C++ part only); README section in the `cs-template` block per kind; setup messages; `tests/check_open_code.py` in the template CI on the 3 OS (bash, bash 3.2, PowerShell 7 and 5.1). Not released alone: §6 | review |
| V7b | Adoption | with the workspace change, one round: §6 | todo |
| V7 | Template (original step) | the csLie files become the template's: `open-code.sh` / `.ps1` for **every** kind (today excluded for `library`, venv-only for the others), `.vscode/settings.json` without the C/C++ engine keys (also for `library`, C++ part only), the README section in the `cs-template` block; template release, `copier update` of the projects; csLie experiment branch deleted | todo |
| V8 | Mixed / multi-root | a project + its checked-out libraries in one window (§4.4); chain build + install task; symlinked installs opt-in | todo |
| V9 | csorchestrator up to a project | run only the dependencies of a repository (`--until` / `--skip`), then VS Code takes over | todo |
| V10 | Preset filter (optional) | `CSCMAKE_PRESETS_FILTER` (§2) | todo |
| V11 | Roll out | csCore, csCamera, csVisOpenGL, csNelson, csBlockMatrix, csImgTracker / csSkiTracker (launch target = the application) | todo |

## 6. One chained change: VS Code + the workspace folder (2026-11-23, with the user)

The template changes twice (V7a, then W2 and the new folder name): released once, adopted once. Order (release chain):

| # | Repository | Change | Release |
|---|---|---|---|
| C1 | csCMake | W1: the standalone layout's folder renamed (W4) and documented as csCMake's; `cscmake-generate-presets` | rc |
| C2 | csorchestrator | W3: the standalone-layout check of `base_target_dir` in its csCMake part | rc |
| C3 | cs-project-template | V7a; W2 (no `workspace_dir`, the new name literal); `open-code` reads the workspace root from the layout file itself (`<csCMake>/presets/layout/<layout>.json`, `CSCMAKE_WORKSPACE_ROOT` with `${sourceDir}` / `${sourceParentDir}` / `$penv{}` expanded; before the first recipe run, csCMake not there yet: the include path's prefix), so no folder name in the scripts; optionally the Claude Code extension in `extensions.json` (§7) | one release |
| C4 | every repository on the template, release-chain order | `copier update` + the unused `workspace_dir` key deleted + (projects) include paths of `CMakePresets.json` / `csCMakeProjectSetup.json` and the recipe's `base_target_dir` to the new name + csCMake / csorchestrator to C1 / C2; one PR per repository, `[skip ci]` where nothing builds | per repository, as usual |
| C5 | csLie, csImgTracker | the `feature/vscode-setup` experiment branches deleted (ask first) | — |

Locally after C4: the old `workspace/` folders are stale (rename them or run the recipe again).

W4, the name: **`_csw`** (decided 2026-11-23): short (Windows path length), neutral (csCMake's folder too, used
without csorchestrator), not a Python package name, sorts first. `_csorchestrator-run` was considered: explicit, but
long and named after csorchestrator.

### 6.0 Progress

- 2026-11-23: C0 done (template `feature/vscode-setup` fb7fe5a, this plan). The user authorized working unattended
  (commits, pushes, releases) up to C4; at C4 the user supervises the adoption of one repository per kind, then
  allows the rest.
- C1: csCMake de3cc0a on `main`, `v1.1.0-rc1` tagged (release run 45207808372); smoke OK locally (host gcc).
- C2: csorchestrator 3956e86 on `main` (CI 45208321371); `v0.1.1-rc1` after its CI. The check runs in the local
  execution of the CMake workflow step only: the workflow generation has no project folder to read.
- C3: template `feature/vscode-setup` 99fd613 (CI 45208717043); then merged to `main`, `v1.2.0`. The Windows check of
  `open-code.ps1` (PowerShell 7 and 5.1) passed in the template CI (run 45206973532).

### 6.1 The steps in detail

**C0, before starting (this plan, the user):** review and commit V7a (template branch) and this plan; the csLie /
csImgTracker experiment branches stay as they are until C5. Not during the weekly run (Sun 20:00 to Mon 07:00 CET).

**C1, csCMake (`feature/csw-workspace`), release `1.1.0-rc1`:**
- `src/cscmake/presets/generate.py`: the standalone layouts `${sourceDir}/_csw` (and their description); regenerate
  `presets/layout/standalone*.json` (`cscmake-generate-presets`).
- Smoke test `tests/smoke/csSmokeStandalone/` (`CMakePresets.json`, `csCMakeProjectSetup.json`, `CMakeLists.txt`) and
  the docs that say `workspace/`: `README.md`, `docs/user/getting-started.md`, `docs/user/presets.md`,
  `docs/tutorials/other-layouts.md`, `docs/advanced/smoke-tests.md`; the skill `agent-plugin/skills/cscmake-usage`.
- W1: the docs of the layouts say the standalone folder is csCMake's and fixed (another place: the `env` layout).
- Version: **1.1.0** (the user, 2026-11-23): the standalone layout moves, breaking for its two users (csImgTracker,
  csSkiTracker), but every consumer is ours and moves in C4: a minor, not a major (an exception to "breaking = major",
  stated in the CHANGELOG entry; the pending 1.0.1 bump is absorbed).

**C2, csorchestrator (`feature/csw-workspace`), release `0.1.1-rc1` (its pending patch bump):**
- W3, in its csCMake part (where it runs `cmake --workflow --preset`): before configuring a source that has a
  `csCMakeProjectSetup.json`, read its layout file (`<CSCMAKE_ROOT>/presets/layout/<layout>.json`, the csCMake it
  checked out), expand `CSCMAKE_WORKSPACE_ROOT` (`${sourceDir}`, `${sourceParentDir}`, `$penv{}`) and check it is the
  recipe's `base_target_dir` for a standalone layout; else stop with a message naming both. No folder name in
  csorchestrator; a recipe without csCMake is not checked. Test with a fake layout file.
- `base_target_dir` is a required argument of the recipe helpers (no default: each recipe writes `Path("workspace")`),
  and so are `base_install_dir`, `base_libs_dir`, `base_build_dir` (and the deploy-archives folder), passed one by one:
  a recipe can make them disagree with csCMake's `<root>/install|libs|build`. The check: `base_target_dir` in
  `build_repos` (standalone: equal to the layout's root; the checked-out repositories, sibling: true by construction),
  and the install / libs / build folders against `<root>/...` where the helpers receive them. For S6 (csorchestrator
  rewrite): one workspace root in the recipe, the other folders derived from it, so the check is no longer needed.
- The tests and the comment that use `workspace/` as an example path: `_csw/` (cosmetic, same behaviour).
- The skill `agent-plugin/skills/csorchestrator-usage`, `TODO-cscmake-alignment.md` where they say `workspace/`.

**C3, cs-project-template, release `v1.2.0`** (an update needs manual changes in each project; a minor, as C1: every repository is ours and moves in C4):
- V7a (done on `feature/vscode-setup`).
- W2: drop `workspace_dir` from `copier.yml`; `_csw` literal in `.gitignore.jinja`, `pyproject.toml.jinja`,
  `.vscode/settings.json.jinja`, `README.md.jinja`; the template README (answers, update instructions: "delete the
  `workspace_dir` key from `.copier-answers.yml`").
- `open-code.sh` / `.ps1`: the workspace root from the layout file (as C2), the include path's prefix before the first
  recipe run (csCMake not there yet); no folder name left in the scripts; `tests/check_open_code.py` with fake layout
  files.
- Optional (decide at C3): the Claude Code extension in `extensions.json` (§7).
- CI of the template green on the 3 OS (the Windows check of `open-code.ps1`). The check runs in the `project` jobs only:
  the scripts are copied verbatim to every kind, so once per OS is enough, and it makes its own fake standalone,
  sibling, env and plain repositories.

**C4, adoption, one PR per repository (`feature/csw-workspace`), release-chain order:**
1. Tools: csCMake, csorchestrator, csWiki: `copier update` to v1.2.0 (their C1 / C2 branches can carry it).
2. third_party_base_libs (and its forks on the template: fmt-eigen, NamedType, tclap: `copier update` only).
3. csqt6, csopencvcpu, csopencvcuda.
4. csfoundation (and csCore, csLie, csCamera, csVisOpenGL), csoptimization (and csNelson, csBlockMatrix).
5. csImgTracker, csSkiTracker (standalone: the include paths too).
In each project: `copier update --defaults --vcs-ref v1.2.0`, delete `workspace_dir` from `.copier-answers.yml`;
recipe `base_target_dir = Path("_csw")`, csCMake `1.1.0` and csorchestrator `0.1.1` pins; standalone projects:
`CMakePresets.json` and `csCMakeProjectSetup.json` include `${sourceDir}/_csw/csCMake/...`; README mentions of
`workspace/`; `generate-github-workflow`; CI on the branch (one build), merge, release as usual. A library: `copier
update` only, in its project's PR (same branch name).
Locally: `mv workspace _csw` in each project (or run the recipe again); `open-code` then finds the builds.

**C5, clean-up:** delete the experiment branches `feature/vscode-setup` of csLie and csImgTracker (local and origin; ask
first); `.github`: the `cs-org` skills that say `workspace/` (`cs-local-status`, `cs-fork-sync`), the plans' "next"
lines, ECOSYSTEM.md picks up the template version by itself.

## 7. Using Claude Code with VS Code

- Open the repository with `open-code`, then Claude Code (extension or `claude` in the window's terminal): it starts in
  the repository, reads its `CLAUDE.md` (the cscosine rules, `AGENTS.md`) and enables the plugins of
  `.claude/settings.json` (trust the folder once). One session per repository / window.
- The IDE link is the gain for C++: Claude sees the open file, the selection and the diagnostics (clangd, CMake Tools),
  and shows its edits in the VS Code diff view: "fix the errors of this file", "explain this selection".
- An inner library (csLie): the window is the library; for the context of its project (the recipe, the other libraries,
  the plans) `/add-dir` the project root (`../..`) or `cscosine/.github`. A change across repositories follows the rules
  (same `feature/<topic>` everywhere).
- Building and testing from Claude: the build of the window (its folder is in the workspace file and in the script's
  output): `cmake --build <build> --config Debug`, `ctest --test-dir <build> -C Debug -R <test>`; one host build, never
  the CI matrix (rules); the recipe run stays the developer's.
- Leave the changes unstaged and review them in VS Code's Source Control view (rules: Claude never stages or commits on
  its own).
