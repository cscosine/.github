# TODO: organisation-level content

Status 2026-11-22. Larger work is in the plans (`PLAN-cscosine-org.md`); this is the list of small items.

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
- [ ] Commit email of `cscosine-dev`: `cscosine@gmail.com` is public. Optional, for future commits only: "Keep my email
      addresses private" and the `…@users.noreply.github.com` address (local `user.email` of every clone); past
      commits keep the old address.
