# TODO: organisation-level content

Status 2026-11-22 (evening). Larger work is in the plans (`PLAN-cscosine-org.md`); this is the list of small items.

- [x] Public `cscosine/.github`: org page, logo and mark, avatars, `CONTRIBUTING.md`, plugin marketplace, plans, rules,
      licensing, the generated overview (`.github-private` retired).
- [x] `LICENSING.md`: the policy (open points: `PLAN-licensing.md`).
- [ ] Templates: `CITATION.cff`, `THIRD_PARTY_NOTICES` for deliveries, the "how to replace Qt" text for applications.
- [ ] Community files: `SECURITY.md`, issue and PR templates (when outside contributions come).
- [ ] Reusable workflows (optional): e.g. the CI of the Python tools, csCMake smoke.
- [ ] `ECOSYSTEM.md` grouped by project along the release chain: each outer project with its inner repositories, forks
      and attention items together (third_party_base_libs and its forks, then csqt6 / csopencvcpu, csfoundation and its
      libraries, ...), instead of one table per topic.
- [ ] **csWiki**: how-to pages (Qt LGPL compliance step by step, making a release), linking to `LICENSING.md`.
- [ ] **csorchestrator** (`PLAN-csorchestrator-architecture.md`): a license field per library in the manifest;
      `THIRD_PARTY_NOTICES` generated into every deployment; a check that fails when a GPL-only Qt module is installed;
      later an SBOM per release.
- [ ] **Every repository**: `CITATION.cff`; the copyright line (`PLAN-licensing.md`, L1).
- [ ] csopencvcuda: back into the chain, then its final; the only repository ECOSYSTEM.md still flags. Now a plan:
      `PLAN-csopencvcuda.md` (C0: rc1 built, to check; low priority, unused for now).
- [ ] **VS Code as an IDE** on the build folders of the workspace, for every C++ repository (template `.vscode/`, the
      workspace file written by csCMake or csorchestrator, `open-code.sh` / `.ps1`): now a plan, `PLAN-vscode.md`
      (experiment positive on csLie `feature/vscode-setup`; V1–V9, not scheduled).
- [ ] Commit email of `cscosine-dev`: `cscosine@gmail.com` is public. Optional, for future commits only: "Keep my email
      addresses private" and the `…@users.noreply.github.com` address (local `user.email` of every clone); past
      commits keep the old address.
- [x] Stale docs found during S4 (documentation only, `[skip ci]`): csfoundation `README.md` still names
      `csfoundation/csorchestrator_config.py` and constants that no longer exist (`CSFOUNDATION_PROJECT_VERSION`,
      `THIRD_PARTY_LIBRARY_DEPENDENCIES`, ...: now `csfoundation_config.py`); csorchestrator `README.md` "Using the
      package" example is outdated (compare with a real `*_project.py`). Done 2026-11-22: csfoundation #6, csorchestrator #7 (`[skip ci]`, no version bump; pipes
      removed from the csfoundation README, dropped 2026-11-16).
- [ ] csfoundation `csfoundation_project.py`: `phase_name_suffix="csoptimization dependencies"` (copy-paste); the fix
      regenerates the workflow (a build): with the next real csfoundation change.
- [ ] Drop tl-optional and tclap from third_party_base_libs, after their consumers move:
      - tl-optional: csCore (`language/Optional.hpp`, its tests `language/tests/optional`) moves to `std::optional`
        (check for `optional<T&>` and the monadic functions `map` / `and_then` / `or_else` in csCore and its
        consumers; with `PLAN-libraries.md` LB1), `tl-optional` out of csCore's CMake and of
        `csfoundation_config.py`, released through csfoundation.
      - tclap: csSkiTracker (`skiTrackerApp/CommandLineOptions.cpp`, its CMake, `csSkiTracker_config.py`) moves to
        CLI11 (in third_party_base_libs from 0.1.1).
      - Then both dropped in third_party_base_libs (the consumers pin a release of it, so the order is safe).
- [ ] Platform matrix: when to drop Ubuntu 22.04; macOS 15 for as long as GitHub provides the runner. CI cost of
      third_party_base_libs (20 jobs; per job, first run: Xcode ~16 min, macOS Ninja Multi-Config ~10, Ubuntu 26.04
      5-10): one generator per macOS version if needed.
- [ ] third_party_base_libs, optional: the Tracy viewer and `tracy-capture` built from the `tracy` fork. The upstream
      release has them prebuilt (Linux x64, macOS, Windows), but the Linux tools need glibc 2.38 (checked on v0.15.0;
      the viewer is an AppImage, not checked), so they do not run on Ubuntu 22.04, and there is no Linux arm64 build.
      Cost: a GUI application with system packages on the Linux runners (Wayland, xkbcommon, EGL, dbus, freetype; or
      X11 with glfw) and `CPM` downloads at configure (ImGui, capstone, …). If done: a deployment of the fork, Release
      only, one variant per system and architecture, a `--help` smoke run. Until then: the upstream viewer of the
      version of the client, where it runs (Ubuntu ≥ 24.04, macOS, Windows).
- [ ] third_party_base_libs: real recipe tests (the repository list, version alignment, build-matrix invariants;
      only placeholder tests today).
- [ ] Generated plans index (later, not S5 any more: S5 closed 2026-11-22 with the index hand-written): first one
      structure for the plans' status lines (`PLAN-libraries.md` differs), then `plans/README.md` written from them.
