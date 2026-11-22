# Plan: VS Code on a project of the workspace, as an IDE

Status: experiment positive (2026-11-22), not scheduled. To come back to: steps V1–V8.

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
