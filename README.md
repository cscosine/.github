# cscosine/.github

The organisation-level repository of cscosine (public; the only one):

- [profile/README.md](profile/README.md): the public page of the organisation (links, get started; its projects section
  and status line generated nightly).
- [CONTRIBUTING.md](CONTRIBUTING.md): how changes move (branches, releases, the fast path); shown by GitHub in every
  repository without its own.
- [LICENSING.md](LICENSING.md): the licensing policy; [LICENSE](LICENSE).
- [plans/](plans/README.md): the plans of the organisation and their progress.
- [ECOSYSTEM.md](ECOSYSTEM.md): every repository, versions, dependencies, forks, the template version of each, what
  needs attention (generated nightly).
- [scripts/](scripts/): `github_settings.py` (repository settings, rulesets and labels, from `github-settings.json`; run
  locally with an admin login), `ecosystem_report.py` and `ecosystem.py` (the generated parts above, in this order).
- [assets/](assets/): [cscosine-logo.svg](assets/cscosine-logo.svg) / `.png`: the logo;
  [cscosine-mark.svg](assets/cscosine-mark.svg) / `.png` (800 × 800): the mark alone, centred to fit in a circle, for
  round avatars.

The files every repository shares (setup, checks, CI of the tools, the agent files) and the
[**rules of every repository**](https://github.com/cscosine/cs-project-template/blob/main/template/.claude/cscosine-rules.md)
(`template/.claude/cscosine-rules.md`, imported by each `CLAUDE.md`) live in
[cs-project-template](https://github.com/cscosine/cs-project-template), their only source.

## A new repository

Created from [cs-project-template](https://github.com/cscosine/cs-project-template) (its README: create, update), then
registered here, one line each in `scripts/`:

- [github-settings.json](scripts/github-settings.json): the name under its kind.
  `scripts/github_settings.py --apply <name>` then sets its rulesets, settings and labels, and the nightly report tracks
  it in `ECOSYSTEM.md` (releases, CI, template version, drift).
- [ecosystem.json](scripts/ecosystem.json) (public repositories worth showing): its group and one sentence, for the
  organisation page.

## Claude Code plugins

This repository is the organisation's plugin marketplace
([.claude-plugin/marketplace.json](.claude-plugin/marketplace.json)). Plugin `cs-org`
([plugins/cs-org/](plugins/cs-org/)): how changes move in the cscosine repositories (`cs-workflow`), the release train
across projects (`cs-release-train`), the forks (`cs-fork-sync`), the state of a local workspace (`cs-local-status`),
the state of the organisation (`cs-ecosystem-status`, members).

The plugins of the tools and libraries live in their own repository, in an `agent-plugin/` folder next to the code
they describe (the marketplace points to it on `main`), so an API change updates its skill in the same PR:

| Plugin | Repository | Skills |
|---|---|---|
| `cscmake` | [csCMake/agent-plugin](https://github.com/cscosine/csCMake/tree/main/agent-plugin) | `cscmake-usage`: using csCMake in a project |

```
/plugin marketplace add cscosine/.github
/plugin install cs-org@cscosine
/plugin install cscmake@cscosine
```

Every repository created from the template declares the marketplace in its `.claude/settings.json` and enables
`cs-org`, so Claude Code proposes it when the folder is trusted.

## Avatars

No service sets an avatar everywhere from one upload: Google and GitHub each keep their own. Use
[assets/cscosine-mark.png](assets/cscosine-mark.png) (round avatars) and upload it by hand, again after every change of
the logo:

| Where | How |
|---|---|
| Google account `cscosine@gmail.com` (Gmail and every Google service) | myaccount.google.com → Personal info → Photo |
| GitHub user `cscosine-dev` | github.com → Settings → Public profile → Profile picture |
| GitHub organisation `cscosine` | github.com/organizations/cscosine/settings/profile → Profile picture (today the full logo; the mark reads better at small sizes) |
| Gravatar (for the other sites: WordPress, forums, many developer tools) | gravatar.com: sign in with `cscosine@gmail.com`, upload the image, assign it to that address |

To come: other community files, reusable workflows, the plugins of the tools and libraries.
