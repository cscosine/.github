# Plan: the first-party libraries: review, documentation, agent instructions

**Status:** todo (written 2026-11-22; not scheduled, independent of csorchestrator's rewrite). Libraries: csCore,
csLie, csCamera, csVisOpenGL (built by csfoundation), csNelson, csBlockMatrix (built by csoptimization).

## 0. Why

Each library has a design review in its repository, with the changes it proposes:

| Library | Review | Main proposals |
|---|---|---|
| csCore | `docs/evolution-assessment.md` | slim and / or rename; keep `assert` (the most valuable part); the alias components (`format`, `language`, `namedType`, …) reconsidered |
| csLie | `docs/evolution-assessment.md` | accuracy and edge cases first, then scope / representation, then speed |
| csCamera | `docs/evolution-assessment.md` | verified defects; the camera models to support; a target design (parameter vector + pure kernels, as csLie) |
| csVisOpenGL | `docs/evolution-assessment.md` | simplicity for robotics / SLAM, cameras and interaction, 2D use (csImgTracker) |
| csNelson | `ASSESSMENT.md` | bugs found, a measured baseline, then the CPU core reworked |
| csBlockMatrix | `ASSESSMENT.md` | issues found, compile-time periodic block patterns |

Their documentation is thin (READMEs of 14–38 lines) and agents get their usage from the index skills
`csfoundation-libs` / `csoptimization-libs` (plugins `csfoundation`, `csoptimization`, PLAN-cscosine-org S4), which
say which library for what, the CMake packages and how a project gets them, not how to use each API in detail.

## 1. Decisions

- **D1. Detailed instructions are the library's documentation**, in the library's repository next to the code: a
  README that describes the components and their use, a `docs/` guide where the library is large enough, the
  reference in the headers. People and agents read the same text.
- **D2. One plugin per distribution, not per library.** The index skill of `csfoundation` / `csoptimization` stays
  short and links to each library's documentation (GitHub URLs on `main`). A plugin is one folder of one repository:
  per-library plugins would add six marketplace entries and six switches per repository for no gain.
- **D3. A library-specific skill only on evidence**: when agents repeatedly get something wrong that the documentation
  cannot fix (PLAN-cscosine-org §5.4); then a skill in the distribution's plugin (`agent-plugin/skills/<library>-…`).
- **D4. Documentation with the review, not before**: written for the API the review settles, in the same PRs as the
  changes; the rule of the distributions' `AGENTS.md` (an API change updates the skill in the same PR) extends to
  the library's documentation.
- **To decide at LB1**: the documentation format, the same for every library: Markdown in `docs/` (read on GitHub)
  or a Sphinx site as csCMake's (published on Pages); the reference from the headers (Doxygen or none).

## 2. Steps

The order follows the dependencies (csCore is used by every other library) and the use (csImgTracker, csSkiTracker).
Each step: re-read the review, decide with the user what to do now, make the changes (tests first where the review
found defects), write the documentation (D1), update the index skill (D2), release through the distribution (the
library's own semver tag, the distribution's release, `stable`).

| # | Step | Content | Status |
|---|---|---|---|
| LB1 | csCore | the review's choice (slim / rename), the documentation format (above), README / guide | todo |
| LB2 | csLie | accuracy and edge cases, then the representation; guide (conventions: exp / log, Jacobians, tangent spaces) | in progress (§3) |
| LB3 | csCamera | the defects, the models, the target design (shared with LB2); guide (models, projection conventions) | todo |
| LB4 | csVisOpenGL | the architecture changes the applications need; macOS: a 4.1 core profile, lines 1 px wide and points not smoothed (`glLineWidth` > 1 and `GL_POINT_SMOOTH` do not exist in a core profile) until the core profile everywhere with lines and points expanded in the shaders (phase 2 of its review); guide (a `Frame`, visualizers, renderers, painters, the sample) | todo |
| LB5 | csBlockMatrix | the issues; OpenMP on macOS (with LB6); guide (dimension descriptors, layouts) | todo |
| LB6 | csNelson | the bugs and the baseline first; OpenMP on macOS: built serial today (Apple Clang has no OpenMP runtime, no Homebrew): libomp as a package of third_party_base_libs, a thread pool given by the caller, or no OpenMP at all (measure first: `OMP_NUM_THREADS=1` against the default on Linux); guide (sections, edges, solvers, a worked problem) | todo |
| LB7 | Index skills | `csfoundation-libs`, `csoptimization-libs` rewritten as indexes linking the guides; library skills only per D3 | todo |

LB7 can follow each library step by step instead of waiting for all of them.

## 3. LB2, csLie: the steps

Branch `feature/cslie-accuracy` in csLie (csfoundation gets the same branch, its recipe pointing to it, only to run
CI). Work in the local csfoundation workspace: `_csw/csLie`, built by a local run of `csfoundation_project.py`;
rebuild and test with `cmake --build _csw/build/<config dir>/csLie --config <Release|Paranoid|...>` and `ctest`. Both
branches are pushed: csLie `1f1bf47` (L0, on L1 `0d4853e`, on `main` after template v1.2.3), csfoundation `8feee4e` (the recipe builds
csLie at `feature/cslie-accuracy`; back to `main` at L7). CI on demand:
`gh workflow run csfoundation.yml --repo cscosine/csfoundation --ref feature/cslie-accuracy`.

Decisions (2026-11-22, with the user):

- **Accuracy first, on the current matrix API.** Quaternion storage and strong types (`SO3<S>`, …) come together in
  phase 2 of the review, measured first (compose, act on points, exp, log): one API break, not two. The fixes are
  built on one internal kernel of half-angle / Jacobian coefficients with per-precision Taylor cut-offs, so a
  quaternion layer reuses them.
- **Formulas taken from the other libraries, read, not built.** Excerpts of GTSAM, Sophus, manif and symforce, with
  their licenses and source commits: `workspace/csLie/_reference_impl/` (local only, in csLie's
  `.git/info/exclude`; delete it, and that line, when LB2 ends).
- **Accuracy tests against exact results.** `csLie/tests/reference/`: `QuadReference.hpp` (`__float128`),
  `generateReferenceData.cpp` (built where `__float128` and libquadmath exist: GCC on x86-64 Linux) and its output `ReferenceData.hpp` (hexadecimal literals,
  so the tests run on every platform). Tolerances in ε of each precision; the inputs cover 0, tiny angles, 1°, the
  formula switches, π − 10⁻ᵏ and exactly π.
- **Strict warnings on every csLie target** (`cscmake_strict_warnings`, csCMake as it is). The installed-header check
  alone does not see template bodies; the tests instantiate every public function in `float32_t` and `float64_t`.
  The same line for each library in its own LB step. An explicit instantiation file only in phase 1, when other
  scalar types (Jet, SIMD batch, CUDA) come. clang-tidy (`cscmake_clang_tidy`, no `.clang-tidy` yet): an
  organisation decision, later (TODO-org).

| # | Step | Content | Status |
|---|---|---|---|
| L0 | Build rules | `DEFAULT_COMPILE_PROFILES` with `cscmake_strict_warnings` in csLie's `cs_initialize_project`; fix the 77 warnings it reveals (22 in the library: double literals and unqualified `sin` / `cos` that make float compute in double, the review's finding 3; the rest in the tests); `so3Log`'s `n == 0` as `!(n > 0)` (`-Wfloat-equal`); the reference generator under the strict flags too (`__extension__` on `__float128` for `-Wpedantic`, its 5 exact float comparisons for `-Wfloat-equal`); csLie `AGENTS.md`: every public function has a test over `float32_t, float64_t` | done (2026-11-27): `1f1bf47` on `feature/cslie-accuracy`, pushed: GCC and Clang 0 warnings, Release and Paranoid, ctest green. `__extension__` not needed (GCC 11 accepts `__float128` under `-Wpedantic`); the generator had 3 exact float comparisons, not 5 |
| L1 | `so3Log` | Shepperd's method + `θ = 2·atan2(‖v‖, w)` (GTSAM); accuracy test | done (2026-11-27): `0d4853e` on `feature/cslie-accuracy`, CI green (csfoundation `feature/cslie-accuracy`); ≤ 1.13 ε (was NaN at π, ±inf at π − 1e-8 in float, 1229 ε at 1° in float). Also the reference check (moved here from L0): the generator built where `__float128` and libquadmath exist (`check_cxx_source_compiles`; GCC on x86-64 Linux, skipped elsewhere, Clang does not find `quadmath.h`), not installed; the CTest `csLie reference data up to date` fails when the committed `ReferenceData.hpp` is not its output; the target `csLieRegenerateReferenceData` rewrites it (`tests/reference/ReferenceData.cmake`, modes CHECK / WRITE); π as `4·atanq(1)` (`M_PIq`'s `Q` literal is rejected by `-std=c++17`). Re-check under L0 |
| L2 | `so3Exp` | the shared half-angle kernel: `h = sin(θ/2)/(θ/2)`, `c = cos(θ/2)`, `A = h·c`, `B = h²/2`; `using std::` | todo |
| L3 | `so3J`, `so3Jinv` | `C = (θ − sin θ)/θ³` and `D = (1 − A/(2B))/θ²` with per-precision Taylor below the cut-off (GTSAM `DexpFunctor`) | todo |
| L4 | `se3Exp`, `se3Log` | `t = Jl(ω)·ρ`, `ρ = Jl⁻¹(ω)·t` on the shared kernel (the ~1e-11 small-angle error) | todo |
| L5 | SO2 / SE2 | `se2Exp` without `1 − cos θ`; `se2Log` (missing): `a = (θ/2)·cot(θ/2)`, `b = θ/2` | todo |
| L6 | S2 | trig-free basis (`y/r`, `z/r`); the S2 log / ⊖ (missing): `atan2(‖p×q‖, p·q)` | todo |
| L7 | Release | csfoundation branch → CI; merge (csLie, then csfoundation); csLie 0.1.1 with csfoundation's next release; the review document updated (§2.3 findings fixed) | todo |

Then phase 1 (scalar-generic kernels), phase 2 (types, quaternion storage, the full Jacobian API), with the user.
Each step: the test first (it fails on the current code), then the fix; changes left unstaged for review, one commit
per step.

Order (2026-11-26, with the user): L1 first on `feature/cslie-accuracy` (done), then L0 on top of it, then L2–L6.
Next: L2. The organisation's C++ rules (levels, csCMake profiles, review rules): [PLAN-cpp-rules.md](PLAN-cpp-rules.md).

### 3.1 Build rules: measured, and the proposals to decide later

Measured on `feature/cslie-accuracy` (`1e19799`), Release, strict warnings on every target: GCC 77 unique warnings
(library 22: `SO3_impl` 14, `S2_impl` 4, `SE3_impl` 4; tests 55), Clang 66 (library 24, tests 42), a partly different
set: L0 builds clean on both. Eigen and Catch2 are system includes (no warnings from them). The library fixes: `using
std::sin; using std::cos; using std::sqrt; …` in each function (a scalar type with its own overloads, e.g. a Jet, still
finds them), literals as `S(…)`; no formula changes (L2–L6).

How csCMake applies the profiles today: `cs_add_compile_profile_rule` only defines a profile; a target gets the
default profiles of its folder (`DEFAULT_COMPILE_PROFILES` of `cs_initialize_project`, a directory variable: a
subfolder can set its own before its targets) plus those of `cs_target_use_compile_profiles(<target> …)`; options and
definitions are private (consumers never get them). In csLie, `csLie_paranoid` (UBSan) and `cscmake_strict_warnings`
were given only to the installed-header check; since L0 every target has `cscmake_strict_warnings`, UBSan is still
only on the installed-header check (B2).

To decide later. B1 and B6 now belong to [PLAN-cpp-rules.md](PLAN-cpp-rules.md) (W8 and §5), the organisation's C++ rules;
the others stay with csLie:

| # | Proposal | Where | Note |
|---|---|---|---|
| B1 | More warnings in `cscmake_warnings`: `-Wcast-qual`, `-Wextra-semi`, `-Wundef`, `-Wmissing-declarations`, `-Wsuggest-override`; Clang `-Wcomma`, `-Wunreachable-code`, `-Wextra-semi-stmt` | csCMake (every project) | Not `-Wuseless-cast` (fires on `static_cast<S>` with `S = double`, bad for generic scalar code), not `-Weverything` |
| B2 | Paranoid of csLie on the tests too, with `cscmake_sanitize_address` and `cscmake_hardening_debug` next to UBSan | csLie | `cs_target_use_compile_profiles(csLieTest csLie_paranoid)` |
| B3 | `EIGEN_INITIALIZE_MATRICES_BY_NAN` on the test target in Paranoid | csLie (later each Eigen library) | An uninitialised matrix shows up as NaN in the tests |
| B4 | Floating-point contraction: GCC defaults to `-ffp-contract=fast` (FMA on aarch64, x86 with `-march`), which changes results at the ε the accuracy tests measure: `-ffp-contract=off` on the tests or tolerances that allow it; `-ffast-math` never | csLie tests; csCMake if it becomes a rule | Before L1's tolerances are final |
| B5 | `[[nodiscard]]`, `constexpr`, `noexcept` on the API | csLie | Phase 2 (an API change, with the types) |
| B6 | clang-tidy | template + csCMake + csfoundation CI | Below |

B6, clang-tidy (csCMake has `cscmake_clang_tidy`, no `.clang-tidy` exists yet; an organisation decision):

- One `.clang-tidy` in `cs-project-template`, the same in every repository; a repository relaxes it only in a
  `.clang-tidy` of a subfolder.
- Not in the normal builds (5–10× slower) and not in pre-commit (no build there, no `compile_commands.json`): a
  custom configuration `Tidy` (based on Debug, profile `cscmake_clang_tidy`) or `run-clang-tidy -p <build>` locally;
  in CI one job of the outer repository (csfoundation), Linux Clang, configuration `Tidy`.
- Header-only libraries: clang-tidy sees a header only through a `.cpp` that includes it (the tests, the
  installed-header check): `HeaderFilterRegex` on the project folder, Eigen and Catch2 excluded.
- First checks: `clang-analyzer-*`, `bugprone-*` without `easily-swappable-parameters` (noise in a math API),
  `performance-*`, a short list of `readability-*` / `modernize-*`; not `cppcoreguidelines-narrowing-conversions`
  (repeats `-Wconversion`) nor `misc-const-correctness` (slow, noisy with Eigen expressions). `WarningsAsErrors`
  after a clean first pass.
- csLie as the pilot (small), then the template; its own plan step, after L0.
