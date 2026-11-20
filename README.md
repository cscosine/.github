# cscosine/.github

Organisation-wide files of cscosine, read by GitHub:

- `profile/README.md`: the public page of the organisation.
- `CONTRIBUTING.md`: how changes move (branches, pull requests, releases), with the commands; shown by GitHub in every
  repository without its own.
- `assets/cscosine-logo.svg`: the logo (source); `assets/cscosine-logo.png`: its 920 × 920 export, the organisation
  avatar. GitHub has no API for the avatar: after a change, upload the PNG in the organisation settings (Profile).
- `assets/cscosine-mark.svg` / `.png` (800 × 800): the mark alone (CS and the curve), centred to fit in a circle:
  for round avatars (accounts, small sizes where the text of the full logo is unreadable).

## Claude Code plugins

This repository is the organisation's plugin marketplace (`.claude-plugin/marketplace.json`). Plugin `cs-org`
(`plugins/cs-org/`): how changes move in the cscosine repositories (`cs-workflow`), the release train across projects
(`cs-release-train`), the forks (`cs-fork-sync`), the state of a local workspace (`cs-local-status`).

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
