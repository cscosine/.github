# cscosine/.github

The organisation-level repository of cscosine (public; the only one):

- `profile/README.md`: the public page of the organisation (its projects section generated nightly).
- `CONTRIBUTING.md`: how changes move (branches, releases, the fast path); shown by GitHub in every repository
  without its own.
- `LICENSING.md`: the licensing policy.
- [plans/](plans/README.md): the plans of the organisation and their progress.
- [rules/](rules/README.md): the rules of every repository (the "cscosine rules" section of each `CLAUDE.md`).
- `ECOSYSTEM.md`: every repository, versions, dependencies, what needs attention (generated nightly).
- `scripts/`: `github_settings.py` (repository settings and rulesets, from `github-settings.json`; run locally with
  an admin login), `ecosystem.py` and `ecosystem_report.py` (the generated parts above).
- `assets/cscosine-logo.svg` / `.png`: the logo; `assets/cscosine-mark.svg` / `.png` (800 × 800): the mark alone,
  centred to fit in a circle, for round avatars.

## Claude Code plugins

This repository is the organisation's plugin marketplace (`.claude-plugin/marketplace.json`). Plugin `cs-org`
(`plugins/cs-org/`): how changes move in the cscosine repositories (`cs-workflow`), the release train across projects
(`cs-release-train`), the forks (`cs-fork-sync`), the state of a local workspace (`cs-local-status`), the state of the
organisation (`cs-ecosystem-status`, members).

```
/plugin marketplace add cscosine/.github
/plugin install cs-org@cscosine
```

The repositories will declare it in their `.claude/settings.json` (project template), so Claude Code proposes it.

## Avatars

No service sets an avatar everywhere from one upload: Google and GitHub each keep their own. Use
`assets/cscosine-mark.png` (round avatars) and upload it by hand, again after every change of the logo:

| Where | How |
|---|---|
| Google account `cscosine@gmail.com` (Gmail and every Google service) | myaccount.google.com → Personal info → Photo |
| GitHub user `cscosine-dev` | github.com → Settings → Public profile → Profile picture |
| GitHub organisation `cscosine` | github.com/organizations/cscosine/settings/profile → Profile picture (today the full logo; the mark reads better at small sizes) |
| Gravatar (for the other sites: WordPress, forums, many developer tools) | gravatar.com: sign in with `cscosine@gmail.com`, upload the image, assign it to that address |

To come: other community files, reusable workflows, the plugins of the tools and libraries.
