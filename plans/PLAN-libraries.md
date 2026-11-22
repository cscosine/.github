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
| LB4 | csVisOpenGL | the architecture changes the applications need; guide (a `Frame`, visualizers, renderers, painters, the sample) | todo |
| LB5 | csBlockMatrix | the issues; guide (dimension descriptors, layouts) | todo |
| LB6 | csNelson | the bugs and the baseline first; guide (sections, edges, solvers, a worked problem) | todo |
| LB7 | Index skills | `csfoundation-libs`, `csoptimization-libs` rewritten as indexes linking the guides; library skills only per D3 | todo |

LB7 can follow each library step by step instead of waiting for all of them.

## 3. LB2, csLie: the steps

Branch `feature/cslie-accuracy` in csLie (csfoundation gets the same branch, its recipe pointing to it, only to run
CI). Work in the local csfoundation workspace: `workspace/csLie`, built by a local run of `csfoundation_project.py`;
rebuild and test with `cmake --build workspace/build/<config dir>/csLie --config <Release|Paranoid|...>` and `ctest`. The branch is pushed (`1e19799`, L1); csfoundation's branch is not created yet (L7). In the local workspace the gcc
build folder of csLie was last configured from `main` (the VS Code experiment, `PLAN-vscode.md`): reconfigure and
rebuild on the branch before testing. VS Code on that build: csLie `feature/vscode-setup`, `./open-code.sh gcc`.

Decisions (2026-11-22, with the user):

- **Accuracy first, on the current matrix API.** Quaternion storage and strong types (`SO3<S>`, …) come together in
  phase 2 of the review, measured first (compose, act on points, exp, log): one API break, not two. The fixes are
  built on one internal kernel of half-angle / Jacobian coefficients with per-precision Taylor cut-offs, so a
  quaternion layer reuses them.
- **Formulas taken from the other libraries, read, not built.** Excerpts of GTSAM, Sophus, manif and symforce, with
  their licenses and source commits: `workspace/csLie/_reference_impl/` (local only, in csLie's
  `.git/info/exclude`; delete it, and that line, when LB2 ends).
- **Accuracy tests against exact results.** `csLie/tests/reference/`: `QuadReference.hpp` (`__float128`),
  `generateReferenceData.cpp` (run by hand, GCC on Linux) and its output `ReferenceData.hpp` (hexadecimal literals,
  so the tests run on every platform). Tolerances in ε of each precision; the inputs cover 0, tiny angles, 1°, the
  formula switches, π − 10⁻ᵏ and exactly π.
- **Strict warnings on every csLie target** (`cscmake_strict_warnings`, csCMake as it is). The installed-header check
  alone does not see template bodies; the tests instantiate every public function in `float32_t` and `float64_t`.
  The same line for each library in its own LB step. An explicit instantiation file only in phase 1, when other
  scalar types (Jet, SIMD batch, CUDA) come. clang-tidy (`cscmake_clang_tidy`, no `.clang-tidy` yet): an
  organisation decision, later (TODO-org).

| # | Step | Content | Status |
|---|---|---|---|
| L0 | Build rules | `DEFAULT_COMPILE_PROFILES` with `cscmake_strict_warnings` in csLie's `cs_initialize_project`; fix the 77 warnings it reveals (22 in the library: double literals and unqualified `sin` / `cos` that make float compute in double, the review's finding 3; the rest in the tests); `so3Log`'s `n == 0` as `!(n > 0)` (`-Wfloat-equal`); the generator built and checked by CTest where `__float128` and libquadmath exist (a `check_cxx_source_compiles`: GCC on x86-64 Linux; skipped elsewhere): its output must equal the committed `ReferenceData.hpp` (π as `4·atanq(1)`, `__extension__` on the type, so it builds with the strict flags; not installed); csLie `AGENTS.md`: every public function has a test over `float32_t, float64_t` | todo |
| L1 | `so3Log` | Shepperd's method + `θ = 2·atan2(‖v‖, w)` (GTSAM); accuracy test | WIP: committed and pushed on `feature/cslie-accuracy` (`1e19799`; ≤ 1.13 ε; was NaN at π, ±inf at π − 1e-8 in float, 1229 ε at 1° in float); re-check under L0 |
| L2 | `so3Exp` | the shared half-angle kernel: `h = sin(θ/2)/(θ/2)`, `c = cos(θ/2)`, `A = h·c`, `B = h²/2`; `using std::` | todo |
| L3 | `so3J`, `so3Jinv` | `C = (θ − sin θ)/θ³` and `D = (1 − A/(2B))/θ²` with per-precision Taylor below the cut-off (GTSAM `DexpFunctor`) | todo |
| L4 | `se3Exp`, `se3Log` | `t = Jl(ω)·ρ`, `ρ = Jl⁻¹(ω)·t` on the shared kernel (the ~1e-11 small-angle error) | todo |
| L5 | SO2 / SE2 | `se2Exp` without `1 − cos θ`; `se2Log` (missing): `a = (θ/2)·cot(θ/2)`, `b = θ/2` | todo |
| L6 | S2 | trig-free basis (`y/r`, `z/r`); the S2 log / ⊖ (missing): `atan2(‖p×q‖, p·q)` | todo |
| L7 | Release | csfoundation branch → CI; merge (csLie, then csfoundation); csLie 0.1.1 with csfoundation's next release; the review document updated (§2.3 findings fixed) | todo |

Then phase 1 (scalar-generic kernels), phase 2 (types, quaternion storage, the full Jacobian API), with the user.
Each step: the test first (it fails on the current code), then the fix; changes left unstaged for review, one commit
per step.
