#!/usr/bin/env python3
"""Generate ECOSYSTEM.md: every cscosine repository, CI, versions, dependencies, and what needs attention.

    python3 scripts/ecosystem_report.py            # writes ECOSYSTEM.md at the repository root
    python3 scripts/ecosystem_report.py --stdout

Reads GitHub only (REST API; GH_TOKEN / GITHUB_TOKEN, else the token of the local gh login) and the upstream tags of
the forks (git ls-remote). Pins checked against the latest releases / tags: csCMake (`cscmake_version`), the providers
(`release_tag`, and its `project_version`), the tags of the inner repositories a distribution builds (`repo_ref_dict`,
`RepoRefBuildPublishConfig`), csorchestrator
(`csorchestrator_version` answer) and the template; bumping them stays manual. The repositories and their kinds: scripts/github-settings.json; what each outer project
builds: scripts/ecosystem.json. A private repository (if any) is listed with a lock. Nothing is changed on GitHub.
"""

import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "scripts" / "github-settings.json"
OUT = ROOT / "ECOSYSTEM.md"
STALE_DAYS = 30


def token() -> str | None:
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok
    hosts = Path.home() / ".config" / "gh" / "hosts.yml"
    if hosts.exists():
        m = re.search(r"oauth_token:\s*(\S+)", hosts.read_text())
        return m.group(1) if m else None
    return None


TOKEN = token()


def curl(url: str) -> tuple[int, str]:
    cmd = ["curl", "-sS", "-L", "--max-time", "30", "--retry", "3", "-w", "\n%{http_code}", "-H", "Accept: application/vnd.github+json"]
    if TOKEN and "api.github.com" in url:
        cmd += ["-H", f"Authorization: Bearer {TOKEN}"]
    out = subprocess.run([*cmd, url], capture_output=True, text=True, check=True).stdout
    body, _, code = out.rpartition("\n")
    return int(code), body


def api(path: str) -> object | None:
    code, body = curl(f"https://api.github.com/{path}")
    if code == 404:
        return None
    if code != 200:
        raise RuntimeError(f"GET {path}: HTTP {code}: {body[:200]}")
    return json.loads(body)


def file_on_main(org: str, repo: str, path: str) -> str | None:
    r = api(f"repos/{org}/{repo}/contents/{path}?ref=main")
    return base64.b64decode(r["content"]).decode() if r else None  # type: ignore[index]


def vkey(tag: str) -> tuple[int, ...]:
    """Order of versions: 1.2.3-rc4 < 1.2.3; -cs.N / -cpu.N / -rcN compared by their numbers."""
    nums = [int(x) for x in re.findall(r"\d+", tag)]
    final = 0 if re.search(r"-rc\d+$", tag) else 1
    return (*nums[:3], final, *nums[3:])


_TAGS: dict[str, list[str]] = {}


def tags(org: str, repo: str) -> list[str]:
    if repo not in _TAGS:
        _TAGS[repo] = [t["name"] for t in (api(f"repos/{org}/{repo}/tags?per_page=100") or [])]  # type: ignore[union-attr]
    return _TAGS[repo]


def fork_refs(proj: str) -> dict[str, str]:
    """The refs of the inner repositories, with `{NAME}` from `NAME = "..."` resolved: `repo_ref_dict={"repo": "ref"}`
    or `"repo": RepoRefBuildPublishConfig("ref", ...)` entries."""
    consts = dict(re.findall(r'^\s*([A-Z_][A-Z0-9_]*) = "([^"]*)"', proj, re.M))
    block = re.search(r"repo_ref_dict=\{((?:[^{}]|\{[^{}]*\})*)\}", proj)  # f-string fields: one level of braces
    refs = dict(re.findall(r'"([^"]+)":\s*f?"([^"]+)"', block.group(1))) if block else {}
    refs.update(re.findall(r'"([^"]+)":\s*RepoRefBuildPublishConfig\(\s*f?"([^"]+)"', proj))
    return {r: re.sub(r"\{([A-Z_][A-Z0-9_]*)\}", lambda m: consts.get(m.group(1), m.group(0)), v) for r, v in refs.items()}


def newer_fork_tag(tag: str, available: list[str]) -> str | None:
    """The newest tag of the same variant (`-cs` / `-cpu` / `-cuda`, or plain semver for a library of ours) newer than
    `tag`, if any (finals only)."""
    m = re.fullmatch(r"v[\d.]+-(cs|cpu|cuda)\.\d+(-rc\d+)?", tag)
    if m:
        same = [t for t in available if re.fullmatch(rf"v[\d.]+-{m.group(1)}\.\d+", t)]
    elif re.fullmatch(r"v\d+\.\d+\.\d+(-rc\d+)?", tag):
        same = [t for t in available if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    else:
        return None  # a branch, or another scheme
    best = max(same, key=vkey, default=None)
    return best if best and vkey(best) > vkey(tag) else None


def link(org: str, repo: str, sub: str = "") -> str:
    return f"[{repo}](https://github.com/{org}/{repo}{sub})"


def grouped(items: list[str]) -> list[str]:
    """The attention items as a nested list: one entry per repository (by name), its items below it."""
    by_repo: dict[str, list[str]] = {}
    for item in items:
        head, sep, rest = item.partition(": ")
        if not sep:
            head, rest = item, ""
        by_repo.setdefault(head, []).append(rest)
    lines = []
    for head in sorted(by_repo, key=lambda h: h.lower()):
        lines.append(f"- {head}")
        lines += [f"  - {r}" for r in by_repo[head] if r]
    return lines


def at(org: str, repo: str, ref: str, kind: str) -> str:
    """`repo ref`, linked to the repository at that ref (`kind`: "tree" for a tag or branch, "releases/tag")."""
    return f"[{repo} `{ref}`](https://github.com/{org}/{repo}/{kind}/{ref})"


def _real(runs: list[dict]) -> list[dict]:
    """Completed runs that are not cancelled or skipped (a release cancels the `main` run its tag build replaces)."""
    return [r for r in runs if r["status"] == "completed" and r["conclusion"] not in ("cancelled", "skipped")]


def _mark(run: dict, label: str) -> str:
    return f"{'✅' if run['conclusion'] == 'success' else '❌'} [{label}]({run['html_url']})"


def ci_status(org: str, repo: str, outer_repo: bool, attention: list[str]) -> tuple[str, str, str]:
    """The CI cells of a repository: the last real run of each workflow on `main`, the builds of its newest tag (outer
    repositories; failed -> attention, as no newer tag built green), the last run of each workflow on `stable`
    (failed -> attention). Each run a mark linking to it, labelled by the workflow file."""
    wfs = (api(f"repos/{org}/{repo}/actions/workflows?per_page=100") or {}).get("workflows", [])  # type: ignore[union-attr]
    # GitHub keeps listing a deleted workflow file: only the files on main, and the Pages deployment (dynamic; not
    # Dependabot's dependency graph)
    on_main = {f["path"] for f in api(f"repos/{org}/{repo}/contents/.github/workflows?ref=main") or []}  # type: ignore[union-attr]
    wfs = [w for w in wfs if w["path"] in on_main or w["path"].startswith("dynamic/pages/")]  # type: ignore[index]
    name = {w["id"]: w["path"].rsplit("/", 1)[-1].removesuffix(".yml") for w in wfs}  # type: ignore[index]
    main_marks = []
    for w in sorted(wfs, key=lambda w: name[w["id"]].lower()):  # type: ignore[index]
        if w["state"] != "active":  # type: ignore[index]
            continue
        runs = api(f"repos/{org}/{repo}/actions/workflows/{w['id']}/runs?branch=main&per_page=20") or {}  # type: ignore[index]
        done = _real(runs.get("workflow_runs", []))  # type: ignore[union-attr]
        if done:
            main_marks.append(_mark(done[0], name[w["id"]]))  # type: ignore[index]
            if done[0]["conclusion"] != "success":
                attention.append(f"{link(org, repo)}: `main` {name[w['id']]} {done[0]['conclusion']} "  # type: ignore[index]
                                 f"({done[0]['html_url']})")
    tag_cell = ""
    if outer_repo:
        # a tag as it is now (name and commit): not the runs of a deleted tag of the same name, nor of old workflows
        existing = {t["name"]: t["commit"]["sha"] for t in api(f"repos/{org}/{repo}/tags?per_page=100") or []}  # type: ignore[union-attr]
        pushes = (api(f"repos/{org}/{repo}/actions/runs?event=push&per_page=100") or {}).get("workflow_runs", [])  # type: ignore[union-attr]
        tag_runs = [r for r in _real(pushes) if re.match(r"v\d", r["head_branch"] or "") and r["workflow_id"] in name
                    and existing.get(r["head_branch"]) == r["head_sha"]]
        if tag_runs:
            newest = max(tag_runs, key=lambda r: r["created_at"])["head_branch"]
            of_tag: dict[int, dict] = {}
            for r in tag_runs:  # newest first: the last run of each workflow for that tag
                if r["head_branch"] == newest:
                    of_tag.setdefault(r["workflow_id"], r)
            tag_cell = f"`{newest}` " + " ".join(_mark(r, name[r["workflow_id"]]) for r in of_tag.values())
            failed = [name[r["workflow_id"]] for r in of_tag.values() if r["conclusion"] != "success"]
            if failed:
                attention.append(f"{link(org, repo)}: build of the newest tag {newest} failed ({', '.join(failed)}), "
                                 "no newer tag")
    stable_marks = []
    stable = (api(f"repos/{org}/{repo}/actions/runs?branch=stable&per_page=30") or {}).get("workflow_runs", [])  # type: ignore[union-attr]
    last: dict[int, dict] = {}
    for r in _real(stable):
        if r["workflow_id"] in name:
            last.setdefault(r["workflow_id"], r)
    for r in last.values():
        stable_marks.append(_mark(r, name[r["workflow_id"]]))
        if r["conclusion"] != "success":
            attention.append(f"{link(org, repo)}: `stable` {name[r['workflow_id']]} {r['conclusion']} "
                             f"({r['html_url']})")
    return "<br>".join(main_marks), tag_cell, "<br>".join(stable_marks)


def main() -> int:
    cfg = json.loads(SETTINGS.read_text())
    org = cfg["org"]
    kinds = {r: k for k, rs in cfg["kinds"].items() for r in rs}
    public_cfg = json.loads((ROOT / "scripts" / "ecosystem.json").read_text())
    builds = {e["repo"]: e.get("builds", []) for g in public_cfg["groups"] for e in g["repos"]}
    outer = [r for r, k in kinds.items() if k in ("tool", "distribution", "application")]
    attention: list[str] = []
    now = time.time()

    # --- repositories
    rows = ["| Repository | Kind | Visibility | Default | Branches | Rulesets |", "|---|---|---|---|---|---|"]
    branches: dict[str, list[dict]] = {}
    for repo in sorted(kinds, key=str.lower):
        info = api(f"repos/{org}/{repo}")
        if info is None:
            attention.append(f"{repo}: in the settings, not found on GitHub")
            continue
        br = api(f"repos/{org}/{repo}/branches?per_page=100") or []
        branches[repo] = br  # type: ignore[assignment]
        try:
            rs = ", ".join(sorted(r["name"] for r in api(f"repos/{org}/{repo}/rulesets") or [])) or "–"  # type: ignore[union-attr]
        except RuntimeError:
            rs = "?"
        lock = " 🔒" if info["visibility"] != "public" else ""  # type: ignore[index]
        rows.append(f"| {link(org, repo)}{lock} | {kinds[repo]} | {info['visibility']} | {info['default_branch']} | "  # type: ignore[index]
                    f"{', '.join(b['name'] for b in br)} | {rs} |")  # type: ignore[index]
        if info["default_branch"] != "main" and repo != "opencv_contrib":  # type: ignore[index]
            attention.append(f"{link(org, repo)}: default branch `{info['default_branch']}`, expected `main`")  # type: ignore[index]
        for b in br:  # type: ignore[union-attr]
            if b["name"].startswith(("feature/", "fix/", "sync/")):
                c = api(f"repos/{org}/{repo}/commits/{b['commit']['sha']}")
                date = c["commit"]["committer"]["date"]  # type: ignore[index]
                age = (now - time.mktime(time.strptime(date, "%Y-%m-%dT%H:%M:%SZ"))) / 86400
                if age > STALE_DAYS:
                    attention.append(f"{link(org, repo)}: branch `{b['name']}` untouched for {int(age)} days")

    # --- versions of the outer projects
    latest: dict[str, str] = {}
    published: dict[str, dict[str, str]] = {}  # repo -> tag -> publication date (newest = latest, whatever the scheme)
    vrows = ["| Project | Final | Candidate | Commits on main since | stable |", "|---|---|---|---|---|"]
    for repo in sorted(outer, key=str.lower):
        rels = [r for r in (api(f"repos/{org}/{repo}/releases?per_page=50") or []) if not r["draft"]]  # type: ignore[union-attr]
        published[repo] = {r["tag_name"]: r["published_at"] for r in rels}
        by_date = sorted(published[repo], key=published[repo].get)  # type: ignore[arg-type]
        finals = [t for t in by_date if not next(r for r in rels if r["tag_name"] == t)["prerelease"]]
        rcs = [t for t in by_date if t not in finals]
        newest = by_date[-1] if by_date else None
        if newest:
            latest[repo] = newest
        since = "–"
        if newest:
            cmp_ = api(f"repos/{org}/{repo}/compare/{newest}...main")
            since = str(cmp_["ahead_by"]) if cmp_ else "?"  # type: ignore[index]
        st = "–"
        if any(b["name"] == "stable" for b in branches.get(repo, [])) and finals:
            c = api(f"repos/{org}/{repo}/compare/{finals[-1]}...stable")
            st = "at the last final" if c and c["ahead_by"] == 0 and c["behind_by"] == 0 else "not at the last final"  # type: ignore[index]
            if st != "at the last final":
                attention.append(f"{link(org, repo)}: `stable` is not at a final release (last final: {finals[-1]})")
        newer_rc = rcs and (not finals or published[repo][rcs[-1]] > published[repo][finals[-1]])
        vrows.append(f"| {link(org, repo)} | {finals[-1] if finals else '–'} | {rcs[-1] if newer_rc else '–'} | "
                     f"{since} | {st} |")

    # --- dependencies (recipes on main) and drift of the pins
    cscmake_latest = latest.get("csCMake")
    drows = ["| Project | csCMake | Providers (pinned release) | Builds (inner repository at ref) |", "|---|---|---|---|"]
    edges: set[tuple[str, str]] = set()
    for repo in sorted(outer, key=str.lower):
        proj = file_on_main(org, repo, f"{repo}_project.py") or ""
        conf = file_on_main(org, repo, f"{repo}_config.py") or ""
        if not proj:
            continue
        m = re.search(r'cscmake_version = "([^"]+)"', proj)
        cm = m.group(1) if m else "–"
        if m and cscmake_latest and "v" + cm != cscmake_latest and \
                published["csCMake"].get("v" + cm, "") < published["csCMake"][cscmake_latest]:
            attention.append(f"{link(org, repo)}: csCMake {cm}, latest is {cscmake_latest}")
        pins = re.findall(r'git_repo="([^"]+)".{0,300}?release_tag="([^"]+)"', conf, re.S)
        for dep, pv, tag in re.findall(r'git_repo="([^"]+)".{0,300}?project_version="([^"]+)".{0,300}?release_tag="([^"]+)"',
                                       conf, re.S):
            if not tag.startswith(f"v{pv}"):
                attention.append(f"{link(org, repo)}: pins {dep} {tag} with project_version {pv}")
        for dep, tag in pins:
            edges.add((dep, repo))
            if dep in latest and tag != latest[dep] and published[dep].get(tag, "") < published[dep][latest[dep]]:
                attention.append(f"{link(org, repo)}: pins {dep} {tag}, latest is {latest[dep]}")
        ref = re.search(r'common_repo_ref = "([^"]+)"', proj)
        inner = builds.get(repo, [])
        for r in inner:
            edges.add((repo, r))
        frefs = fork_refs(proj)
        for r, fref in frefs.items():
            newer_tag = newer_fork_tag(fref, tags(org, r))
            if newer_tag:
                attention.append(f"{link(org, repo)}: builds {r} `{fref}`, newer is {newer_tag}")
        # one line per provider / inner repository, each linked at the version shown (release, or tree at tag / branch)
        common = ref.group(1) if ref else "main"
        inner_txt = "<br>".join(at(org, r, frefs.get(r, common), "tree") for r in inner) or "–"
        pins_txt = "<br>".join(at(org, d, t, "releases/tag") for d, t in pins) or "–"
        drows.append(f"| {link(org, repo)} | {cm} | {pins_txt} | {inner_txt} |")

    # --- forks: base, our tags, newer upstream
    frows = ["| Fork | Upstream | Base | Our commits | Our tags on it | Newer upstream releases |",
             "|---|---|---|---|---|---|"]
    for repo in sorted((r for r, k in kinds.items() if k == "fork"), key=str.lower):
        readme = file_on_main(org, repo, "cscosine/README.md") or ""
        if "the cscosine copy" in readme:
            frows.append(f"| {link(org, repo)} | (a copy of our own) | | | | |")
            continue
        up = re.search(r"\| Upstream \| <?([^ >|]+)", readme)
        base = re.search(r"\| Base \| upstream (?:tag )?`([^`]+)`", readme)
        if not (up and base):
            frows.append(f"| {link(org, repo)} | ? | ? | | | |")
            if repo != "opencv_contrib":
                attention.append(f"{link(org, repo)}: no cscosine/README.md with upstream and base")
            continue
        url, b = up.group(1).rstrip("/"), base.group(1)
        out = subprocess.run(["git", "ls-remote", "--tags", "--refs", url + ".git"], capture_output=True, text=True,
                             timeout=120).stdout
        up_tags = [t.split("refs/tags/")[1] for t in out.split() if t.startswith("refs/tags/")]
        newer = sorted((t for t in up_tags if re.fullmatch(r"v?\d+(\.\d+){1,3}", t) and vkey(t) > vkey(b)), key=vkey)
        ours = sorted((t["name"] for t in (api(f"repos/{org}/{repo}/tags?per_page=100") or [])  # type: ignore[union-attr]
                       if re.fullmatch(rf"v{re.escape(b.lstrip('v'))}-(cs|cpu|cuda)\.\d+", t["name"])), key=vkey)
        # our commits on the upstream base: the size of the patch stack a sync rebases
        cmp = api(f"repos/{org}/{repo}/compare/{b}...main")
        ahead = str(cmp["ahead_by"]) if isinstance(cmp, dict) else "?"  # type: ignore[index]
        frows.append(f"| {link(org, repo)} | {url} | `{b}` | {ahead} | {', '.join(ours) or '–'} | "
                     f"{', '.join(newer[-3:]) or '–'} |")
        if newer:
            attention.append(f"{link(org, repo)}: upstream has {', '.join(newer[-3:])} (we are on {b})")

    # copies of our own: libraries around upstream files whose upstream is inactive (no syncs)
    crows = ["| Library | Came from | Our version |", "|---|---|---|"]
    for repo in sorted((r for r, k in kinds.items() if k == "library"), key=str.lower):
        readme = file_on_main(org, repo, "cscosine/README.md") or ""
        if "the cscosine copy" in readme:
            came = re.search(r"\| Came from \| <?([^ >|]+)", readme)
            ver = re.search(r"\| Our version \| `([^`]+)`", readme)
            crows.append(f"| {link(org, repo)} | {came.group(1) if came else '?'} | `{ver.group(1) if ver else '?'}` |")

    # --- project template (cs-project-template): the version each repository is on (.copier-answers.yml on main)
    template = "cs-project-template"
    ttags = sorted((t["name"] for t in (api(f"repos/{org}/{template}/tags?per_page=100") or [])  # type: ignore[union-attr]
                    if re.fullmatch(r"v\d+\.\d+\.\d+", t["name"])), key=vkey)
    tlatest = ttags[-1] if ttags else None
    trows = [f"Latest template: {tlatest or '–'}", "", "| Repository | Kind | Template | Answers |", "|---|---|---|---|"]
    not_adopted: list[str] = []
    # not on the template on purpose: the template itself, and what the template uses (ecosystem.json outside_template)
    outside = set(public_cfg.get("outside_template", [template]))
    for repo in sorted((r for r, k in kinds.items() if k not in ("fork", "meta") and r not in outside), key=str.lower):
        answers = file_on_main(org, repo, ".copier-answers.yml")
        if answers is None:
            not_adopted.append(repo)
            continue
        commit = re.search(r"^_commit:\s*(\S+)", answers, re.M)
        version = commit.group(1) if commit else "?"
        given = ", ".join(f"{k}={v}" for k, v in re.findall(r"^(kind|workspace_dir|csorchestrator_version):\s*(\S+)",
                                                             answers, re.M))
        trows.append(f"| {link(org, repo)} | {kinds[repo]} | {version} | {given or '–'} |")
        if tlatest and version != tlatest:
            attention.append(f"{link(org, repo)}: template {version}, latest is {tlatest} (`copier update`)")
        orch = re.search(r"^csorchestrator_version:\s*(\S+)", answers, re.M)
        olatest = max((x for x in tags(org, "csorchestrator") if re.fullmatch(r"v\d+\.\d+\.\d+(-rc\d+)?", x)),
                      key=vkey, default=None)  # tags: csorchestrator has no GitHub releases
        if orch and olatest and vkey(orch.group(1)) < vkey(olatest):
            attention.append(f"{link(org, repo)}: csorchestrator {orch.group(1)}, latest is {olatest} "
                             "(answer `csorchestrator_version`, then `copier update`)")
    if not_adopted:
        trows += ["", "Not on the template yet: " + ", ".join(link(org, r) for r in not_adopted) + "."]

    # --- version bump: a repository with commits on main since its last final release must already declare the next
    # version (bumped in the first commit that changes it: CONTRIBUTING.md, "Versions"). Its version: pyproject.toml
    # (tools, distributions, applications), project(... VERSION) of the top CMakeLists.txt (libraries). Not checked:
    # the distributions versioned by their upstream product (ecosystem.json `upstream_versioned`: csqt6 v6.12.0-cs.N,
    # csopencvcpu v5.1.0-cpu.N), whose level of ours is in the tag only.
    upstream_versioned = set(public_cfg.get("upstream_versioned", []))
    for repo in sorted((r for r, k in kinds.items() if k in ("tool", "distribution", "application", "library")
                        and r not in upstream_versioned), key=str.lower):
        finals = sorted((t for t in tags(org, repo) if re.fullmatch(r"v\d+\.\d+\.\d+", t)), key=vkey)
        if not finals:
            continue
        if kinds[repo] == "library":
            m = re.search(r"project\s*\([^)]*?VERSION\s+(\d+\.\d+\.\d+)", file_on_main(org, repo, "CMakeLists.txt") or "",
                          re.I)
        else:
            m = re.search(r'^version\s*=\s*"([^"]+)"', file_on_main(org, repo, "pyproject.toml") or "", re.M)
        if not m or m.group(1) != finals[-1][1:]:
            continue
        cmp_ = api(f"repos/{org}/{repo}/compare/{finals[-1]}...main")
        if cmp_ and cmp_["ahead_by"] > 0:  # type: ignore[index]
            attention.append(f"{link(org, repo)}: {cmp_['ahead_by']} commit(s) on `main` since {finals[-1]}, "  # type: ignore[index]
                             f"version still {m.group(1)} (bump it: CONTRIBUTING.md, Versions)")

    # --- CI: every repository with workflows (tools, distributions, applications, libraries: the checks everywhere)
    ci_repos = [r for r, k in kinds.items() if k in ("tool", "distribution", "application", "library")]
    cirows = ["| Repository | `main` (each workflow) | Last tag build | `stable` |", "|---|---|---|---|"]
    for repo in sorted(ci_repos, key=str.lower):
        main_cell, tag_cell, stable_cell = ci_status(org, repo, outer_repo=repo in outer, attention=attention)
        if main_cell or tag_cell or stable_cell:
            cirows.append(f"| {link(org, repo)} | {main_cell or '–'} | {tag_cell or '–'} | {stable_cell or '–'} |")

    graph = ["```mermaid", "flowchart LR", *[f"  {a} --> {b}" for a, b in sorted(edges)], "```"]
    doc = "\n".join([
        "# The cscosine ecosystem",
        "",
        "Generated by `scripts/ecosystem_report.py` from GitHub (nightly: `.github/workflows/ecosystem.yml`). Do not",
        "edit: change the repositories, or the script.",
        "",
        "## Needs attention",
        "",
        *(grouped(attention) or ["Nothing."]),
        "",
        "## CI",
        "",
        "The last real run (completed, not cancelled or skipped) of each workflow on `main`; the builds of the newest",
        "tag that still exists (outer repositories); the last run of each workflow on `stable`.",
        "",
        *cirows,
        "",
        "## Versions (outer projects)",
        "",
        *vrows,
        "",
        "## Dependencies (recipes on `main`)",
        "",
        *drows,
        "",
        *graph,
        "",
        "## Project template",
        "",
        *trows,
        "",
        "## Forks",
        "",
        "A fork is an upstream release plus our commits (`cscosine/README.md` in the fork says why each one exists);",
        "syncs: the `cs-fork-sync` skill.",
        "",
        *frows,
        "",
        "Copies of our own (upstream inactive, no syncs; a csCMake project of ours around the upstream files):",
        "",
        *crows,
        "",
        "## Repositories",
        "",
        *rows,
        "",
    ])
    if "--stdout" in sys.argv:
        print(doc)
    else:
        OUT.write_text(doc)
        print(f"{OUT.name}: {len(attention)} item(s) need attention")
    return 0


if __name__ == "__main__":
    sys.exit(main())
