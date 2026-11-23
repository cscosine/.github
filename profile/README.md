<p align="center">
  <img src="https://raw.githubusercontent.com/cscosine/.github/main/assets/cscosine-logo.svg" alt="cscosine" width="240">
</p>

<h3 align="center">COmputer Science engINEering, from the first prototype to the product that ships.</h3>

<p align="center">
  Computer vision · geometry · non-linear optimisation · modern C++ and Python
</p>

<p align="center">
  <a href="https://github.com/cscosine/.github/blob/main/ECOSYSTEM.md">📊 Status</a> ·
  <a href="https://github.com/cscosine/.github/blob/main/plans/README.md">🗺️ Roadmap</a> ·
  <a href="https://cscosine.github.io/csWiki/">📚 Docs</a> ·
  <a href="https://github.com/cscosine/.github/blob/main/CONTRIBUTING.md">🤝 Contributing</a> ·
  <a href="https://github.com/cscosine/.github/blob/main/LICENSING.md">⚖️ Licensing</a>
</p>

---

Most ideas die between the notebook and the release. **cscosine** is built for that gap: the science is done in
quick prototypes, then engineered into libraries and applications that build, test and release the same way on
Linux, Windows and macOS.

> The curve in the logo is an exact −cos *t* over one period: it starts on the ground, rises to the idea, and comes
> back down to earth as a product.

### How we work

| | |
|---|---|
| 🧪 **Prototype** | Try the idea fast, measure it, keep what works. |
| 🛠️ **Engineer** | One build system for every project, dependencies pinned to their releases, CI on the whole platform matrix: Ubuntu 22.04 / 24.04 / 26.04 (x64, arm64), Windows, macOS. |
| 📦 **Ship** | Tagged releases with ready-to-run archives; the licenses of what is inside respected and documented. |

### What lives here

<!-- ecosystem:start -->

**Status** (updated nightly): everything up to date · every repository, versions, dependencies, forks, template: [ECOSYSTEM.md](https://github.com/cscosine/.github/blob/main/ECOSYSTEM.md)

| Project | What it is | Release | Candidate | Last build |
|---|---|---|---|---|
| **Tooling** | | | | |
| [csCMake](https://github.com/cscosine/csCMake) | CMake for families of C++ projects: targets, packages, presets for every platform | [v1.0.0](https://github.com/cscosine/csCMake/releases/tag/v1.0.0) | – | [✅ main](https://github.com/cscosine/csCMake/actions/runs/45088056746) |
| [csorchestrator](https://github.com/cscosine/csorchestrator) | One Python script per project: run locally or as a generated CI, releases as binary packages | – | – | [✅ main](https://github.com/cscosine/csorchestrator/actions/runs/45087641686) |
| [cs-project-template](https://github.com/cscosine/cs-project-template) | Copier template: the shared files and rules of every repository, created and kept up to date | – | – | [✅ main](https://github.com/cscosine/cs-project-template/actions/runs/45086659412) |
| [cs-pre-commit-hooks](https://github.com/cscosine/cs-pre-commit-hooks) | pre-commit hooks of every repository: gersemi with the csCMake signatures, cscmake-lint | [v1.0.0](https://github.com/cscosine/cs-pre-commit-hooks/releases/tag/v1.0.0) | – | [✅ main](https://github.com/cscosine/cs-pre-commit-hooks/actions/runs/45085988995) |
| **Foundations** | | | | |
| [third_party_base_libs](https://github.com/cscosine/third_party_base_libs) | Eigen, fmt, cpptrace, libassert, magic_enum, Catch2, ... built for every platform | [v0.1.0](https://github.com/cscosine/third_party_base_libs/releases/tag/v0.1.0) | – | [✅ main](https://github.com/cscosine/third_party_base_libs/actions/runs/45132698729) |
| [csqt6](https://github.com/cscosine/csqt6) | Qt 6 (LGPL modules) built for every platform | [v6.12.0](https://github.com/cscosine/csqt6/releases/tag/v6.12.0) | – | [✅ main](https://github.com/cscosine/csqt6/actions/runs/45089106279) |
| [csopencvcpu](https://github.com/cscosine/csopencvcpu) | OpenCV 5 (CPU) built for every platform | [v5.1.0-cpu.3](https://github.com/cscosine/csopencvcpu/releases/tag/v5.1.0-cpu.3) | – | [✅ v5.1.0-cpu.3](https://github.com/cscosine/csopencvcpu/actions/runs/44991670275) |
| [csfoundation](https://github.com/cscosine/csfoundation) | The base C++ libraries: core, Lie groups, cameras, OpenGL visualisation | [v0.1.0](https://github.com/cscosine/csfoundation/releases/tag/v0.1.0) | – | [✅ v0.1.0](https://github.com/cscosine/csfoundation/actions/runs/44999719820) |
| [csoptimization](https://github.com/cscosine/csoptimization) | Non-linear optimisation libraries | [v0.1.0](https://github.com/cscosine/csoptimization/releases/tag/v0.1.0) | – | [✅ v0.1.0](https://github.com/cscosine/csoptimization/actions/runs/45001631628) |
| **Applications** | | | | |
| [csImgTracker](https://github.com/cscosine/csImgTracker) | Image tracking application | [v0.2.2](https://github.com/cscosine/csImgTracker/releases/tag/v0.2.2) | – | [✅ v0.2.2](https://github.com/cscosine/csImgTracker/actions/runs/45002938555) |
| [csSkiTracker](https://github.com/cscosine/csSkiTracker) | Ski tracking application | [v0.1.0](https://github.com/cscosine/csSkiTracker/releases/tag/v0.1.0) | – | [✅ v0.1.0](https://github.com/cscosine/csSkiTracker/actions/runs/45002986356) |

The release chain (who builds on whom):

```mermaid
flowchart LR
  csfoundation --> csImgTracker
  csfoundation --> csSkiTracker
  csfoundation --> csoptimization
  csopencvcpu --> csImgTracker
  csopencvcpu --> csSkiTracker
  csoptimization --> csSkiTracker
  csqt6 --> csImgTracker
  csqt6 --> csSkiTracker
  csqt6 --> csfoundation
  third_party_base_libs --> csImgTracker
  third_party_base_libs --> csSkiTracker
  third_party_base_libs --> csfoundation
  third_party_base_libs --> csopencvcpu
  third_party_base_libs --> csoptimization
```

<!-- ecosystem:end -->

### Get started

| To | Do |
|---|---|
| Work on a project | `git clone` it, `./setup.sh` (Windows: `.\setup.ps1`), `source .venv/bin/activate`; its README says the rest |
| Start a new project | `copier copy gh:cscosine/cs-project-template <name>`: every repository is created and kept up to date from [cs-project-template](https://github.com/cscosine/cs-project-template) |
| Work with an AI agent | Claude Code reads each repository's rules (`CLAUDE.md`, `AGENTS.md`); the skills of the organisation: `/plugin marketplace add cscosine/.github`, then `/plugin install cs-org@cscosine` |
| Follow the work | [Status](https://github.com/cscosine/.github/blob/main/ECOSYSTEM.md) (nightly: versions, dependencies, what needs attention) · [Roadmap](https://github.com/cscosine/.github/blob/main/plans/README.md) (the plans and their steps) |
| Contribute | [How changes move](https://github.com/cscosine/.github/blob/main/CONTRIBUTING.md) (branches, PRs, releases) · [Rules](https://github.com/cscosine/cs-project-template/blob/main/template/.claude/cscosine-rules.md) |

Documentation: [csWiki](https://cscosine.github.io/csWiki/) · [csCMake](https://cscosine.github.io/csCMake/)

### Principles

- **One way to do each thing**, written once and reused by every project.
- **Traceable**: every release is tagged and names the releases it was built from.
- **Open**: our code is MIT; third-party code keeps its license, and we say which.
