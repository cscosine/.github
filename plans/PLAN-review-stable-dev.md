# Plan: review of the stable-dev changes (Ubuntu 26.04, macOS, library updates)

Date: 2026-11-20 · Status: **in progress**: every row reviewed (2026-11-20); open: decisions on tclap / NamedType / fmt-eigen, the opencv fork and versions (5.1, 5.2), small fixes 10.1, `-cs.2` tags after the next third_party_base_libs CI · Reviews the work of
`PLAN-stable-dev-ubuntu26mac-libs.md` (done; its §4.8 macOS deployment-target round included)

Goal: every change of that round read once by the owner, and for each one: is it right, is it **in the right place**,
is it documented and tested, is nothing left behind. Findings are fixed through PRs (the first use of the PR flow).

---

## 1. Scope

In scope: what the stable-dev round and its §4.8 round changed, per repository (ranges below).

Out of scope (separate reviews if wanted): the "evolution assessment" / "roadmap" documents added to the first-party
libraries on 2026-11-15/16; csImgTracker's 0.2.x work (new UI, icon, About) after rc2; csopencvcuda (not in the round).

| # | Repository | Range to review | Size | Notes |
|---|---|---|---|---|
| 1 | csCMake | `bd91296..dev` (6 commits) | 34 files, +1459 / −29 | Qt helper `cs_deployment_qt_gui`, OpenMP with Apple Clang, macOS deployment target (declare, check, record, hooks on packages found) |
| 2 | csorchestrator | `931b28b..dev` (6 commits) | 21 files, +903 / −74 | Variants, release files outside the artifacts, GUI deployment runs; 3 TODO commits |
| 3 | third_party_base_libs | `5b23729..dev` (5 commits) | 6 files, +764 / −62 | Variants, library updates, pipes dropped, TODO; mostly the generated workflow |
| 4 | Forks (eigen3, fmt, cpptrace, libassert, magic_enum, Catch2, tl-expected, tl-optional) | the **whole patch stack** on `dev` (1 to 17 commits each) | small | `dev` was rebuilt on the new upstream releases: review our commits as a stack, not a diff |
| 5 | opencv fork (`dev-cpu`), csopencvcpu | opencv: our 7 commits on `dev-cpu`; csopencvcpu `48dd8a3..dev` (3 commits) | 7 files, +797 / −99 | KleidiCV / GCC 15, `@loader_path`, freetype off on macOS, deployment target; Xcode → Ninja Multi-Config mapping |
| 6 | csqt6 | `92ea982..dev` (5 commits) | 11 files, +817 / −42 | Qt 6.12.0, macOS 14.4, GPL-only modules out, runtime system requirements of the plugins, README |
| 7 | csCore, csLie, csCamera, csVisOpenGL | `dev` since 2026-11-12, without the assessment documents (4 / 1 / 2 / 4 commits) | small | csAssert as one header, `CS_OMP`, pipes removed, `<cassert>`, core profile on macOS, sample deployment + `--smoke`, deployment target |
| 8 | csBlockMatrix, csNelson | same (4 / 3 commits) | small | GCC 15 fix, OpenMP through csCore, `<cassert>`, deployment target |
| 9 | csfoundation, csoptimization | `8d2a23f..dev` (2) / `bc0c52f..dev` (1) | ~+1100 each | Mostly the generated workflow; the recipe changes |
| 10 | csImgTracker, csSkiTracker | the stable-dev merges (`dc51072`, `804a738`) and their rc2 commits | — | Deployment + smoke run, mapping, providers' pins |

Order: as the release chain (tools first, applications last): a finding in csCMake can change what is right below it.

## 2. How to review one repository

1. `git log --reverse --stat <range>`: read the messages first; then commit by commit (`git show`), not the global diff
   (except for the forks: `git log -p <upstream-tag>..dev`).
2. Generated files (workflows, `CMakePresets.json`, `dependencies/*`): not read line by line; check they are what the
   generator produces today (`./<name>_project.py generate-github-workflow` / `cscmake-generate-presets`, then
   `git diff` empty).
3. The checklist (§3) for each commit; findings written in the table of §4, one line each.
4. Fixes: one branch per repository (`fix/review-stable-dev`), PR into `dev`, the finding ids in the PR body.

An agent pre-review is available: for one repository at a time, it reads the range against §3 and proposes findings,
which you accept, reject or change. You decide; nothing is fixed without a finding you accepted.

## 3. Checklist

| Id | Check |
|---|---|
| C1 **Right place** | Generic behaviour in csCMake / csorchestrator; what a library needs, in the library; what a provider imposes (e.g. Qt plugin system packages), declared by the provider, not repeated by each consumer; csCMake and csorchestrator contain no cscosine project names |
| C2 **One place** | Each concern implemented once. Known points to check: the macOS deployment target (plan §4.8 said "in the project setup preset"; first-party libraries call `cs_macos_deployment_target()` in `CMakeLists.txt`, forks set it in their csCMake setup: one mechanism or two, and is each documented?); OpenMP only through csCore `CS_OMP` (no `#pragma omp` left elsewhere, no macOS flags); `<cassert>` includes vs csAssert |
| C3 Decisions applied | D1–D8 of the stable-dev plan as decided (e.g. D5 core profile on macOS only; D7 GPL-only Qt modules not built; D8 csCMake sets no value) |
| C4 No leftovers | No `TEMP`, debug output, commented-out code, references to `feature/*` branches or `-test*` tags, hard-coded local paths, workarounds whose reason is gone |
| C5 Generated = generator | Generated files match a fresh generation |
| C6 Docs | README / docs / reference blocks / CHANGELOG describe the present state; new functions documented where the others are |
| C7 Tests | New behaviour has a test (csCMake, csorchestrator: unit tests; libraries: their tests; applications: the smoke run) |
| C8 Pins | Every consumer pins the same provider releases; csCMake version consistent along the chain; `project_version` matches the tag |
| C9 Commits | Messages say what and why; in forks, each patch atomic and with a reason (input for the fork model, S4b) |

## 4. Progress and findings

| # | Repository | Status | Findings (id: what → fix) |
|---|---|---|---|
| 1 | csCMake | done | **1.1** fixed (`b39dd9d`): `cs_require_macos_deployment_target`: its error says "raise it in `cscmake-project-setup-macos`", wrong for a csCMake project (`cs_macos_deployment_target`) names both (`modules/csMacosDeploymentTarget.cmake`, `8ce4164`). **1.2** accepted: Deployment target set two ways: csCMake projects `cs_macos_deployment_target()` in `CMakeLists.txt`, projects without csCMake (forks) the preset + `CMAKE_PROJECT_INCLUDE` script → by design (forks keep upstream `CMakeLists.txt`), documented. **1.3** accepted, TODO in csCMake (`cs_deployment_qt_jpg` / `cs_deployment_qt_svg`): `cs_deployment_qt_gui` ships platforms, styles, OpenGL; no `imageformats` / `iconengines` (JPEG, SVG through Qt) → not needed today (icons are PNG, images come from OpenCV): accept, add an option when an application needs it. Checked: no project names, no leftovers, tests for every new command, CHANGELOG coherent rc5 → rc7 |
| 2 | csorchestrator | done | **2.1** fixed (`a2335a7`): Mesa for the Windows GUI runs downloaded without a checksum (`application/recipes/gui_deployments.py`, `a4a480e`) SHA-256 pinned; runs in the Windows CI jobs of the projects with GUI runs once their workflows are regenerated. **2.2** dropped (csorchestrator is restructured, its plan): The same opt-in block (`get_context_list_linux("ubuntu26.04") + get_context_list_macos("macos15") + get_context_list_macos("macos26")`) copied in 6 projects the project API of the restructuring replaces it. **2.3** fixed (`a2335a7`): Project names in csorchestrator (docstring of `get_supported_os_version_list`: "csqt6, csopencvcuda") generic wording. Checked: release files fix (`7162fb0`) with test; GUI run recipes with tests; `.vscode/launch.json` is generated (`tools/generate_vscode_launch.py`) |
| 3 | third_party_base_libs | done (findings for the next change) | **3.1** `repo_access_token` (`ACTIONS_ORG_ACCESS`) no longer needed: every fork it builds is public now (same in csfoundation, csopencvcpu, csopencvcuda, the applications; only csoptimization still builds private repositories) → drop it at the next change. **3.2** csCMake pinned at `1.0.0-rc6`, the rest of the chain at `rc7` (rc7 matters for csCMake projects; fmt-eigen and tclap are, header-only, no deployment target) → `rc7` at the next rc. **3.3** `.github/actionlint.yaml` (Ubuntu 26.04 runner labels unknown to actionlint `v1.7.12` of pre-commit) is the same file in 8 repositories → a newer actionlint when it knows them, else a template-owned file (S3). Checked: the workflow regenerated with today's csorchestrator is identical (`git diff` empty); `csorchestratorsdk/` identical to csorchestrator's `portable/`; README versions = the forks; pipes removed everywhere |
| 4 | Forks | done | Common: the dead `cmakeUserPath.json` block of `.gitignore` (an old csProjectManager entry) removed in each fork; the presets follow the levels of the csCMake docs (level 1 header-only, 2 eigen3, 3 the compiled forks with their macOS target). **eigen3** done: one patch on upstream `5.0.1` (verified = GitLab tag); upstream tag `5.0.1` and `v5.0.1-cs.1` (= rc8 build, `e70fe6e`) pushed; `.gitignore` back to upstream, `cscosine/README.md` + `CHANGELOG.md`; `v5.0.1-cs.2` after the next third_party_base_libs CI; `cs-main` (old 3.4.0 history) replaced at the next release. **fmt** done: 16 commits → a clean stack on upstream `12.2.1` (csCMake presets, Xcode test fix, `cscosine/`), tree identical to the old `dev` except upstream's `.github/` and `.gitignore` restored; old `dev` tagged `v12.2.1-cs.1` (= rc8 build); `-cs.2` after the next third_party_base_libs CI. Decided for every fork: GitHub Actions disabled (settings script), upstream's `.github/` kept, `dev` rewritten as a clean stack after tagging the old one `-cs.1` | **cpptrace, libassert, magic_enum, Catch2, tl-expected, tl-optional** done the same way (2026-11-20, unattended): each verified based on its upstream tag; old `dev` tagged `-cs.1`; clean stack, tree identical to the old `dev` except upstream's `.github/`, `.gitignore` (and Catch2's `README-cs.md`, moved into `cscosine/README.md`). Open in cpptrace: the zstd / libdwarf lookup next to the install is a workaround (hints in `Findzstd.cmake` and the package config). **tclap, NamedType, fmt-eigen** untouched, need a decision: our changes restructure upstream into csCMake projects (tclap moves the headers, fmt-eigen reorganised, NamedType drops its bundled catch.hpp for Catch2), and their bases are untagged upstream commits (NamedType after `v1.1.0`, tclap a 2020 commit of the SourceForge mirror, fmt-eigen has no releases): base and `-cs.N` naming to choose.
| 5 | opencv fork, csopencvcpu | done (see Decisions) | csopencvcpu pins the opencv fork by tag (`v5.0.2-cpu.2`): already the model. Workflow = generator. **5.1** Three version numbers: project / manifest `5.0.0` (`OPENCV_VERSION`), releases `v5.0.1-rcN`, the fork `v5.0.2-cpu.N` (consumers pin `project_version="5.0.0"` with tag `v5.0.1-rc5`) → choose one scheme. **5.2** The opencv fork: `cpu` / `cuda` branches and `-cpu.N` tags (not `-cs.N`), and a first commit mixing several changes ("compile on cpu defaults, win clang, mavx2, cstring, mlas") → fork model for it to decide (large repository, two variants). **5.3** csCMake `rc6` (chain: rc7, now rc8) |
| 6 | csqt6 | done | D6 / D7 applied: GPL-only modules neither cloned nor built (listed, with the reason, in `utils/scripts.py`), the system packages of the Qt plugins declared by csqt6 and installed with its archives (right place), tests for the config; workflow = generator. Nothing to fix |
| 7 | csCore, csLie, csCamera, csVisOpenGL | done | Deployment targets 13.3 (csVisOpenGL 14.4, Qt), declared with `cs_macos_deployment_target`; OpenMP only through `CS_OMP` (no other `#pragma omp`, no macOS flags); core profile on macOS only (`Frame.cpp`), GLSL version from the context; csAssert one header (D4). Fixed (unattended): the dead `.gitignore` removed (`945f901`, `255cd8e`, `73daf71`, `6383351`) |
| 8 | csBlockMatrix, csNelson | done | Same checks as row 7 (13.3, OpenMP through csCore). Fixed (unattended): the dead `.gitignore` removed (`0f147e9`, `5583c0d`) |
| 9 | csfoundation, csoptimization | done | Pins consistent (third_party_base_libs rc8, csqt6 6.12.0-rc1, csfoundation rc9, csCMake rc7); workflows = generator (csfoundation: plus the Mesa checksum at its next regeneration); GUI run of the csVisOpenGL sample through the csorchestrator recipe. Next change: csCMake rc8, drop `repo_access_token` in csfoundation (3.1; csoptimization still builds private repositories) |
| 10 | csImgTracker, csSkiTracker | reviewed, small fixes | Pins consistent with the chain; workflows = generator (+ Mesa checksum at the next regeneration). **10.1** Both `*_project.py` create an orchestrator with `create_orchestrator_factory_all_supported_cases` and overwrite it right after with `create_default_orchestrator`: dead code (csorchestrator plan §7 quick fix). **10.2** The csopencvcpu pin `project_version="5.0.0"` / tag `v5.0.1-rc5`: follows 5.1 |

Finding ids: `<#>.<n>` (e.g. `1.3`), status `open` / `fixed (PR link)` / `accepted as is`.

## 5. Done when

All rows `done`; every finding fixed or accepted; the fixes released down the chain as new rcs where they change a
build (otherwise they wait for the next rc); `PLAN-stable-dev-ubuntu26mac-libs.md` and this plan moved to `plans/done/`.

## Decisions (2026-11-20)

- cpptrace: zstd and libdwarf (its symbol and debug-info dependencies) are of no use to the cscosine code: they stay
  inside cpptrace, with the lookup workaround as it is.
- tclap: kept as it is (to be replaced), no upstream syncs; `cscosine/README.md` says where it came from (`2319766`).
- NamedType, fmt-eigen: small (5 headers / 640 lines; 1 header / 100 lines), upstream inactive: kept as repositories
  of our own, `cscosine/README.md` with origin, base, license, our changes (`c4c20b7`, `d49afe3`). No `-cs.N` tags:
  their own versions (1.1.0, 1.0.0) when released.
- csopencvcuda: dismissed for now, kept as it is as a future reference (out of the release chain).
- csImgTracker, csSkiTracker: no change (10.1 kept as it is).
- opencv fork (5.2, done 2026-11-20): one common stack `dev` on upstream `5.0.0` (csCMake presets, Windows MSVC /
  clang-cl, macOS RPATH and freetype, KleidiCV 26.09, `cscosine/`) and one setup commit per variant: `dev-cpu`
  (tree identical to the old one plus `cscosine/`), `dev-cuda` (gets the common fixes it lacked). Old heads kept as
  `v5.0.2-cpu.2`, `v5.0.2-cuda`. No variant settings passed from the outer projects.
- OpenCV versions (5.1): an exception to `-cs.N`. Fork tags `v<opencv>-cpu.<n>` / `v<opencv>-cuda.<n>` (first:
  `v5.0.0-cpu.1` once csopencvcpu has built the new `dev-cpu`); the distributions keep the OpenCV version (`5.0.0`)
  and their release tags follow the fork tag they ship (e.g. csopencvcpu `v5.0.0-cpu.1`, its candidates
  `v5.0.0-cpu.1-rc<n>`): no 4th component. The old `v5.0.1-rc*` pre-releases of csopencvcpu: deletable when the new
  scheme has its first release.
- opencv_contrib: keeps its simpler layout (`cpu` / `cuda` branches, one commit each) until it needs changes.
- csopencvcpu (2026-11-20): `228bf36` on `dev`: opencv `v5.0.0-cpu.1` (the fork's new layout, same build as
  `v5.0.2-cpu.2`), csCMake rc8, no `ACTIONS_ORG_ACCESS` (3.1), README with the version scheme, workflow regenerated.
  Next: `v5.0.0-cpu.1-rc1` once its CI on `dev` is green; then the rest of the chain.
- Found on the way (csorchestrator, for its plan): the generated release job does not mark a release candidate as a
  pre-release (`softprops/action-gh-release` without `prerelease`), so GitHub shows an rc as "Latest" (csopencvcpu
  `v5.0.1-rc5` today). The release job should set `prerelease` when the tag has `-rc`.
- Finals round (csCMake `v1.0.0` from the rc8 commit, then each project's final release, `stable` fast-forwarded):
  deferred (2026-11-20) until more is stabilised; the release candidates of this round stay the current versions.
