#!/usr/bin/env python3
"""Generate the "projects" section of profile/README.md from GitHub: what each project is, its latest release and
release candidate, its CI status, what it is built on, and the release chain as a Mermaid graph.

    python3 scripts/ecosystem.py            # rewrite the section between the markers
    python3 scripts/ecosystem.py --check    # exit 1 if the section is out of date

Reads public data only (the GitHub REST API; GITHUB_TOKEN / GH_TOKEN when set, for the rate limit): repositories it
cannot see (private) are left out. What each project is: the `description` answer of its .copier-answers.yml on main
(`what` in scripts/ecosystem.json for a repository without one). The groups and inner repositories:
scripts/ecosystem.json. What a
project is built on: the providers its recipe pins on main (`git_repo=` / `release_tag=` of `<repo>_config.py`).
The health line (how many items need attention): the "Needs attention" section of ECOSYSTEM.md, so
scripts/ecosystem_report.py runs first.
"""

import json
import os
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "scripts" / "ecosystem.json"
README = ROOT / "profile" / "README.md"
REPORT = ROOT / "ECOSYSTEM.md"
START, END = "<!-- ecosystem:start -->", "<!-- ecosystem:end -->"


def _curl(url: str, headers: list[str]) -> tuple[int, str]:
    """GET with curl (present on every runner; it falls back between IPv6 and IPv4 where urllib can hang)."""
    cmd = ["curl", "-sS", "-L", "--max-time", "30", "--retry", "3", "-w", "\n%{http_code}"]
    for h in headers:
        cmd += ["-H", h]
    out = subprocess.run([*cmd, url], capture_output=True, text=True, check=True).stdout
    body, _, code = out.rpartition("\n")
    return int(code), body


def api(path: str) -> object | None:
    headers = ["Accept: application/vnd.github+json"]
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers.append(f"Authorization: Bearer {token}")
    code, body = _curl(f"https://api.github.com/{path}", headers)
    if code == 404:
        return None
    if code != 200:
        raise RuntimeError(f"GET {path}: HTTP {code}: {body[:200]}")
    return json.loads(body)


def raw(org: str, repo: str, path: str) -> str | None:
    code, body = _curl(f"https://raw.githubusercontent.com/{org}/{repo}/main/{path}", [])
    return body if code == 200 else None


def releases(org: str, repo: str) -> tuple[str | None, str | None]:
    """(latest final release, latest release candidate newer than it)."""
    final = api(f"repos/{org}/{repo}/releases/latest")
    rels = api(f"repos/{org}/{repo}/releases?per_page=30") or []
    rc = next((r for r in rels if r["prerelease"] and not r["draft"]), None)  # type: ignore[union-attr]
    final_tag = final["tag_name"] if final else None  # type: ignore[index]
    if rc and final and rc["published_at"] < final["published_at"]:  # type: ignore[index]
        rc = None
    return final_tag, rc["tag_name"] if rc else None


def providers(org: str, repo: str) -> list[tuple[str, str]]:
    text = raw(org, repo, f"{repo}_config.py") or ""
    return re.findall(r'git_repo="([^"]+)".{0,300}?release_tag="([^"]+)"', text, re.S)


def description(org: str, repo: str) -> str | None:
    """The `description` answer of the repository's .copier-answers.yml on main (plain, quoted or wrapped scalar)."""
    text = raw(org, repo, ".copier-answers.yml") or ""
    m = re.search(r"^description:[ \t]*(.*(?:\n[ \t]+\S.*)*)", text, re.M)
    if not m:
        return None
    value = " ".join(part.strip() for part in m.group(1).splitlines())
    if len(value) >= 2 and value[0] == value[-1] == "'":
        value = value[1:-1].replace("''", "'")
    elif len(value) >= 2 and value[0] == value[-1] == '"':
        value = json.loads(value)
    return value or None


def link(org: str, repo: str) -> str:
    return f"[{repo}](https://github.com/{org}/{repo})"


def release_link(org: str, repo: str, tag: str | None) -> str:
    return f"[{tag}](https://github.com/{org}/{repo}/releases/tag/{tag})" if tag else "–"


def health(org: str) -> str:
    """One line: how many items of ECOSYSTEM.md need attention, linking to it."""
    url = f"https://github.com/{org}/.github/blob/main/ECOSYSTEM.md"
    if not REPORT.exists():
        return f"Full status of every repository: [ECOSYSTEM.md]({url})."
    text = REPORT.read_text()
    section = text.split("## Needs attention", 1)[1].split("\n## ", 1)[0] if "## Needs attention" in text else ""
    count = sum(1 for line in section.splitlines() if line.startswith("  - "))  # the items, under their repository
    state = "everything up to date" if count == 0 else f"{count} item(s) need attention"
    return (f"**Status** (updated nightly): {state} · every repository, versions, dependencies, forks, template: "
            f"[ECOSYSTEM.md]({url})")


def generate() -> str:
    cfg = json.loads(CONFIG.read_text())
    org = cfg["org"]
    public = {r["name"] for r in api(f"orgs/{org}/repos?type=public&per_page=100") or []}  # type: ignore[union-attr]
    lines = ["| Project | What it is | Release | Candidate | CI | Built on |", "|---|---|---|---|---|---|"]
    edges: list[tuple[str, str]] = []
    for group in cfg["groups"]:
        lines.append(f"| **{group['name']}** | | | | | |")
        for entry in group["repos"]:
            repo = entry["repo"]
            if repo not in public:
                continue  # private (or gone): not on the public page
            final, rc = releases(org, repo)
            wf = entry.get("workflow", f"{repo}.yml")
            badge = (f"[![CI](https://github.com/{org}/{repo}/actions/workflows/{wf}/badge.svg?branch=main)]"
                     f"(https://github.com/{org}/{repo}/actions/workflows/{wf})")
            deps = providers(org, repo)
            for dep, _tag in deps:
                edges.append((dep, repo))
            inner = [r for r in entry.get("builds", []) if r in public]
            built_on = ", ".join(f"{link(org, d)} `{t}`" for d, t in deps) or "–"
            what = (description(org, repo) or entry.get("what", "")) + (f" (builds {', '.join(link(org, r) for r in inner)})" if inner else "")
            lines.append(f"| {link(org, repo)} | {what} | {release_link(org, repo, final)} | "
                         f"{release_link(org, repo, rc)} | {badge} | {built_on} |")
    graph = ["```mermaid", "flowchart LR"]
    graph += [f"  {a} --> {b}" for a, b in sorted(set(edges))]
    graph.append("```")
    return "\n".join([START, "", health(org), "", *lines, "", "The release chain (who builds on whom):", "", *graph, "", END])


def main() -> int:
    text = README.read_text()
    if START not in text or END not in text:
        print(f"{README}: the markers {START} / {END} are missing", file=sys.stderr)
        return 2
    new = text[: text.index(START)] + generate() + text[text.index(END) + len(END):]
    if "--check" in sys.argv:
        return 0 if new == text else 1
    if new != text:
        README.write_text(new)
        print("profile/README.md updated")
    else:
        print("profile/README.md up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
