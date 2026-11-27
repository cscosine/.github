# Plan: C++ rules of the organisation

**Status:** to discuss (written 2026-11-27). Then csCMake, the standard's text, the template, and each project's
adoption.

## 0. Why

- **Most code compiles without warnings.** `cscmake_default`, the default profile of `cs_initialize_project`, has
  only MSVC options (`/MP`, `/Zc:__cplusplus`). A target that does not opt in builds with the compiler's defaults:
  - GCC 11, no flags: misordered member initialisers, unused variables and uninitialised reads all pass silently.
  - Clang 14, no flags: only one uninitialised read is reported.
  - The same file with `-Wall`: GCC 3 × `-Wreorder`, `-Wuninitialized`, `-Wunused-variable`; Clang the same set.
  - Measured 2026-11-27 with a 3-line file. Today only a few targets opt in (`cscmake_warnings` /
    `cscmake_strict_warnings`), mostly the installed-header checks.
- **Some rules can't be checked by any compiler.** Two arose in a library's accuracy work (PLAN-libraries, LB2 / L0):
  - `S(1)` against `static_cast<S>(x)` in code templated on a scalar type.
  - The fixed-width `float32_t` / `float64_t` instead of `float` / `double`.

  These are aliases or cast spellings: the compiler sees the same thing. Only a reviewer, a person or an agent, can
  check them.
- **Not every project needs the same rigour.** A quick experimental app shouldn't carry the rules of a released
  library. But even the quick one should get the checks that catch real bugs for free (initialisation order,
  unused and uninitialised variables, a missing return).

The goal: **one C++ standard for the organisation.** It is written once, enforced by the compiler wherever a flag
exists and by review everywhere else. It has levels, and each project declares the one it follows.

## 1. Principles (proposed)

- **P1. The standard names no project.** The rules, the levels and the review procedure are generic. A project
  declares its level; the standard never lists who follows what. The same rule as csCMake and csorchestrator,
  which never contain the names of cscosine projects.
- **P2. A rule is enforced by the cheapest reliable means.**
  - First choice, a compiler flag in a csCMake profile: every build checks it, in CI too.
  - Then clang-tidy (later, §5).
  - Last, review by a person or an agent against the written rule.

  Every rule says how it is enforced. A rule that a flag covers is not repeated as a review item.
- **P3. Levels, not per-rule switches.** Three levels, each one including the one below. A project picks one; a
  folder of it (tests, tools, a generator) may pick a lower one. No per-rule opt-outs, so a project's level means the
  same everywhere.
- **P4. One declaration, read by both enforcers.** The level is written once, in the project's build, and csCMake
  applies the matching profiles. An agent reviewing the code reads the same declaration, so the two can't drift
  (§4).
- **P5. Existing code is brought to its level in a dedicated step**, as LB2 / L0 did for csLie's warnings. Until
  then a review reports only the lines a change touches.

## 2. The levels (proposed)

| Level | For | Compiler (csCMake) | Review |
|---|---|---|---|
| `base` | everything, experimental apps and quick tools included; the default | the essential warnings (B-rules, §3.1); the always-a-bug ones as errors | none required |
| `standard` | maintained applications and tools | `cscmake_warnings`, as errors in CI | the S-rules (§3.2) |
| `strict` | released libraries | `cscmake_strict_warnings`; sanitizers and standard library hardening in the test configuration | the S- and L-rules (§3.2) |

To discuss:
- **Q1.** Should `base` be the default of `cs_initialize_project` (every project gets it on its next csCMake
  release), or an opt-in? Making it the default follows "the ecosystem moves to a new API directly" and is the only
  way experimental projects get it. The cost: the warnings it reveals appear in every project at once (C0 measures
  them).
- **Q2.** In `base`, which warnings are errors? Proposal: only those that are always a bug:
  - a missing return (`-Werror=return-type`)
  - an uninitialised read (`-Werror=uninitialized`)
  - initialisation order (`-Werror=reorder`)

  Unused variables stay warnings, so an experiment can comment code out without breaking the build.
- **Q3.** Should warnings be errors in `standard` locally too, or only in CI? Proposal: everywhere, with a local
  csCMake switch (`CSCMAKE_WARNINGS_AS_ERRORS=OFF`, a cache variable) that lists every warning at once instead of
  stopping at the first error. In LB2 / L0 that meant editing the project's profiles temporarily.

## 3. The rules (draft catalogue)

Each rule: an ID, the level it starts at, how it is enforced, the reason, a good and a bad example, its exceptions.
The full text goes into the standard (§4). This table is the list to discuss.

### 3.1 Compiler-enforced (B = base, W = standard / strict)

| ID | Rule | Level | GCC / Clang | MSVC | Today |
|---|---|---|---|---|---|
| B1 | Members initialised in declaration order | base | `-Wreorder` (Clang `-Wreorder-ctor`) | `/w15038` | `cscmake_warnings` only |
| B2 | No unused variables, parameters, functions | base | `-Wunused` | `/W4` (C4100, C4189) | `cscmake_warnings` only |
| B3 | No read of an uninitialised variable | base | `-Wuninitialized` (+ GCC `-Wmaybe-uninitialized`, Clang `-Wsometimes-uninitialized`) | C4700, C4701 | `cscmake_warnings` only |
| B4 | Every path of a non-void function returns | base | `-Wreturn-type` | C4715 | compiler default (warning) |
| B5 | No implicit fallthrough in `switch` | base | `-Wimplicit-fallthrough` | C26819 (analyzer only) | `cscmake_warnings` only |
| B6 | No virtual functions without a virtual destructor | base | `-Wnon-virtual-dtor` | `/w14265` | `cscmake_warnings` only |
| W1 | No implicit narrowing or sign conversions | standard | `-Wconversion -Wsign-conversion` (incl. float) | `/w14242 /w14254 /w14826` | `cscmake_warnings` |
| W2 | No implicit float → double promotion | standard | `-Wdouble-promotion` | none | `cscmake_warnings` |
| W3 | No shadowed names | standard | `-Wshadow` | C4456–C4459 (`/W4`) | `cscmake_warnings` |
| W4 | No C-style casts; `nullptr`, not `0` | standard | `-Wold-style-cast -Wzero-as-null-pointer-constant` | none | `cscmake_warnings` |
| W5 | Standard C++ only (no extensions) | standard | `-Wpedantic` | `/permissive-` | `cscmake_warnings` |
| W6 | No exact `==` / `!=` on floating point; write the intent (`!(x > 0)`, `std::fpclassify`, a tolerance) | strict | `-Wfloat-equal` | none | `cscmake_warnings` |
| W7 | Overriding functions say `override` | standard | `-Wsuggest-override` (GCC), `-Winconsistent-missing-override` (Clang) | none | proposed (PLAN-libraries §3.1 B1) |
| W8 | More from PLAN-libraries §3.1 B1: `-Wcast-qual`, `-Wextra-semi`, `-Wundef`, `-Wmissing-declarations`; Clang `-Wcomma`, `-Wunreachable-code`, `-Wextra-semi-stmt` | standard | as listed | none | proposed |

Today `cscmake_warnings` holds every flag of W1–W6 and B1–B6 together. The levels split it into a `base` subset and
the rest (C2).

### 3.2 Review-enforced (S = standard, L = strict)

| ID | Rule | Level | Why no flag |
|---|---|---|---|
| S1 | Floating-point types are `float32_t` / `float64_t`, never `float` / `double`. Exceptions: the alias definitions, wider-than-double code (`__float128`), type names written into generated text | standard | Aliases: the compiler sees the same type |
| S2 | Casts: `static_cast<T>(x)` for a value computed at run time; `T(literal)` for a constant of a scalar type parameter (`S(1)`, `S(1) / S(6)`, not `S(1.0 / 6.0)`, which divides in double); never `T{x}` as a conversion | standard | Functional casts pass `-Wold-style-cast` |
| L1 | In code templated on a scalar type: `using std::sin; using std::sqrt; …` in the function and unqualified calls (`float` stays `float`; a scalar type with its own overloads finds them); literals as `S(…)`, never a bare `double` | strict | Unqualified `sin(float)` silently calls the C `double` function; a warning (W1 / W2) sees only part of it |
| L2 | Every public function template is instantiated by a test over `float32_t` and `float64_t` (where it is generic on the scalar) | strict | A template body is compiled, and warned about, only where it is instantiated |
| L3 | Public headers are self-contained | strict | Enforced already: `cs_target_check_installed_headers` |

To discuss:
- **Q4. Candidates for more S- / L-rules.** Owning raw `new` / `delete` (RAII), `[[nodiscard]]` on pure functions
  (PLAN-libraries §3.1 B5), `const` correctness, `noexcept` on moves, include order (clang-format already sorts),
  naming. Proposal: start with S1, S2, L1–L3 and add a rule only when a review finds the same problem twice.
- **Q5. Where `float32_t` / `float64_t` come from.**
  - Today: a base library defines them as aliases of `float` / `double`.
  - In C++23, `std::float32_t` / `std::float64_t` (`<stdfloat>`) are *distinct* types, not aliases. The names
    would collide in meaning, and in name under `using namespace std`.
  - Options:
    - Keep the aliases, and plan the switch when the ecosystem moves to C++23.
    - Rename them now.

  This affects S1's text.

## 4. Where it lives (proposed)

- **The standard's text: a skill in the organisation's plugin** (`cs-org`, `skills/cs-cpp-rules/SKILL.md`). Rules
  with IDs, levels, examples, exceptions, and the review procedure: read the project's level, check only the S- /
  L-rules of that level, report each finding with its rule ID. It is used both when writing C++ code and when
  reviewing it. It names no project (P1).
- **The compiler part: csCMake.**
  - One profile per level: `cscmake_rules_base`, `cscmake_rules_standard`, `cscmake_rules_strict` (names to settle).
  - `cscmake_warnings` / `cscmake_strict_warnings` stay as building blocks.
  - The switch: `cs_initialize_project(... RULES <level>)`, which sets the default profiles. A folder lowers it with
    `cs_set_rules(<level>)` before its targets. It is the same directory variable mechanism as
    `CSCMAKE_DEFAULT_COMPILE_PROFILES`.
- **The declaration: one place (P4).** The `RULES` of the project's `cs_initialize_project` and any `cs_set_rules`
  of a folder. The agent reads the level there. The template's rules file (`.claude/cscosine-rules.md`, every
  repository) gets one line: "C++ code follows cs-cpp-rules at the level of `RULES` in `cs_initialize_project`
  (a folder may lower it with `cs_set_rules`)". `/code-review` then sees the rule through `CLAUDE.md` in every
  repository.
- **Q6.** Is a CMake argument the right single declaration, or a copier answer rendered into `AGENTS.md`? The CMake
  argument is enforced (the build uses it) and covers folders. A copier answer is visible without reading CMake but
  enforces nothing. Proposal: CMake.

## 5. clang-tidy

PLAN-libraries §3.1 B6 (the `.clang-tidy` in the template, a `Tidy` configuration, one CI job in an outer repository)
moves here. Some checks would turn review rules into tool rules:
- `cppcoreguidelines-pro-type-cstyle-cast` / `google-readability-casting` for part of S2.
- `modernize-use-override` for W7.
- `cppcoreguidelines-owning-memory` for RAII.

S1 has no check (a custom one is not worth it). Not before the levels are in place.

## 6. Steps

| # | Step | Content | Status |
|---|---|---|---|
| C0 | Measure | Build every C++ project once with the proposed `base` set and once with `cscmake_warnings`, without fixing: warnings per project and per flag. This gives the cost of Q1 and the levels | todo |
| C1 | Decide | Q1–Q6, the rule catalogue (§3), the profile and switch names; this plan updated | todo |
| C2 | csCMake | The level profiles, `RULES` / `cs_set_rules`, `CSCMAKE_WARNINGS_AS_ERRORS` (Q3), docs (compile-profiles guide, the `cscmake-usage` skill); a release candidate | todo |
| C3 | The standard | `cs-org` skill `cs-cpp-rules`: the rules of §3 as decided, the levels, the review procedure | todo |
| C4 | Template | The line in `.claude/cscosine-rules.md` (§4); a template release; `copier update` everywhere | todo |
| C5 | Pilot | A library already clean under strict warnings declares `strict` (its project-specific rule text in `AGENTS.md` replaced by the level); an agent reviews a real diff with the skill; the skill corrected | todo |
| C6 | Adoption | Each project declares its level and is brought to it in its own step (libraries: in their PLAN-libraries LB step; applications: their own plan or TODO). With Q1 = default `base`, this step starts as soon as C2 is released | todo |
| C7 | clang-tidy | §5, after C6 | todo |

Order: C0 and C1 together (the measurements inform the decisions), then C2 → C3 → C4 → C5 → C6.
