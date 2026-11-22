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
| LB2 | csLie | accuracy and edge cases, then the representation; guide (conventions: exp / log, Jacobians, tangent spaces) | todo |
| LB3 | csCamera | the defects, the models, the target design (shared with LB2); guide (models, projection conventions) | todo |
| LB4 | csVisOpenGL | the architecture changes the applications need; guide (a `Frame`, visualizers, renderers, painters, the sample) | todo |
| LB5 | csBlockMatrix | the issues; guide (dimension descriptors, layouts) | todo |
| LB6 | csNelson | the bugs and the baseline first; guide (sections, edges, solvers, a worked problem) | todo |
| LB7 | Index skills | `csfoundation-libs`, `csoptimization-libs` rewritten as indexes linking the guides; library skills only per D3 | todo |

LB7 can follow each library step by step instead of waiting for all of them.
