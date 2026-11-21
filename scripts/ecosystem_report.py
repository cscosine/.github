#!/usr/bin/env python3
"""Generate ECOSYSTEM.md: every cscosine repository, versions, dependencies, and what needs attention.

    python3 scripts/ecosystem_report.py            # writes ECOSYSTEM.md at the repository root
    python3 scripts/ecosystem_report.py --stdout

Reads GitHub only (REST API; GH_TOKEN / GITHUB_TOKEN, else the token of the local gh login) and the upstream tags of
the forks (git ls-remote). The repositories and their kinds: scripts/github-settings.json; what each outer project
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


def link(org: str, repo: str, sub: str = "") -> str:
    return f"[{repo}](https://github.com/{org}/{repo}{sub})"


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
            if cmp_ and cmp_["ahead_by"] > 0 and repo != "csWiki":  # type: ignore[index]
                attention.append(f"{link(org, repo)}: {cmp_['ahead_by']} commit(s) on `main` since {newest}")  # type: ignore[index]
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
    drows = ["| Project | csCMake | Providers (pinned) | Builds (inner, ref) |", "|---|---|---|---|"]
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
        for dep, tag in pins:
            edges.add((dep, repo))
            if dep in latest and tag != latest[dep] and published[dep].get(tag, "") < published[dep][latest[dep]]:
                attention.append(f"{link(org, repo)}: pins {dep} {tag}, latest is {latest[dep]}")
        ref = re.search(r'common_repo_ref = "([^"]+)"', proj)
        inner = builds.get(repo, [])
        for r in inner:
            edges.add((repo, r))
        drows.append(f"| {link(org, repo)} | {cm} | {', '.join(f'{d} `{t}`' for d, t in pins) or '–'} | "
                     f"{', '.join(inner) or '–'}{' (`' + ref.group(1) + '`)' if ref and inner else ''} |")

    # --- forks: base, our tags, newer upstream
    frows = ["| Fork | Upstream | Base | Our tags on it | Newer upstream releases |", "|---|---|---|---|---|"]
    for repo in sorted((r for r, k in kinds.items() if k == "fork"), key=str.lower):
        readme = file_on_main(org, repo, "cscosine/README.md") or ""
        if "the cscosine copy" in readme:
            frows.append(f"| {link(org, repo)} | (a copy of our own) | | | |")
            continue
        up = re.search(r"\| Upstream \| <?([^ >|]+)", readme)
        base = re.search(r"\| Base \| upstream (?:tag )?`([^`]+)`", readme)
        if not (up and base):
            frows.append(f"| {link(org, repo)} | ? | ? | | |")
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
        frows.append(f"| {link(org, repo)} | {url} | `{b}` | {', '.join(ours) or '–'} | {', '.join(newer[-3:]) or '–'} |")
        if newer:
            attention.append(f"{link(org, repo)}: upstream has {', '.join(newer[-3:])} (we are on {b})")

    # --- project template (cs-project-template): the version each repository is on (.copier-answers.yml on main)
    template = "cs-project-template"
    ttags = sorted((t["name"] for t in (api(f"repos/{org}/{template}/tags?per_page=100") or [])  # type: ignore[union-attr]
                    if re.fullmatch(r"v\d+\.\d+\.\d+", t["name"])), key=vkey)
    tlatest = ttags[-1] if ttags else None
    trows = [f"Latest template: {tlatest or '–'}", "", "| Repository | Kind | Template | Answers |", "|---|---|---|---|"]
    not_adopted: list[str] = []
    for repo in sorted((r for r, k in kinds.items() if k not in ("fork", "meta") and r != template), key=str.lower):
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
    if not_adopted:
        trows += ["", "Not on the template yet: " + ", ".join(link(org, r) for r in not_adopted) + "."]

    # --- CI of main
    for repo in sorted(outer, key=str.lower):
        runs = api(f"repos/{org}/{repo}/actions/runs?branch=main&per_page=10") or {}
        done = [r for r in runs.get("workflow_runs", []) if r["status"] == "completed"]  # type: ignore[union-attr]
        if done and done[0]["conclusion"] not in ("success", "skipped", "cancelled"):
            attention.append(f"{link(org, repo)}: last `main` run {done[0]['conclusion']} ({done[0]['html_url']})")

    graph = ["```mermaid", "flowchart LR", *[f"  {a} --> {b}" for a, b in sorted(edges)], "```"]
    doc = "\n".join([
        "# The cscosine ecosystem",
        "",
        "Generated by `scripts/ecosystem_report.py` from GitHub (nightly: `.github/workflows/ecosystem.yml`). Do not",
        "edit: change the repositories, or the script.",
        "",
        "## Needs attention",
        "",
        *([f"- {a}" for a in attention] or ["Nothing."]),
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
        *frows,
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
