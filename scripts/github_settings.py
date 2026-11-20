#!/usr/bin/env python3
"""Bring the settings, GitHub Actions switch, rulesets and labels of the cscosine repositories to github-settings.json.

Dry run by default: prints what would change, per repository. ``--apply`` makes the changes (``--archive`` also
archives the repositories listed under "archive"). Idempotent: a second run reports nothing to do.

Uses the GitHub API through ``gh api`` (the user's token, admin of the organisation). Standard library only.

    scripts/github_settings.py                     # dry run, every repository
    scripts/github_settings.py csCMake fmt         # dry run, some repositories
    scripts/github_settings.py --apply             # apply
    scripts/github_settings.py --apply --archive   # apply and archive
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CONFIG = Path(__file__).with_name("github-settings.json")


class GhError(RuntimeError):
    pass


def gh(path: str, method: str = "GET", body: Any = None) -> Any:
    cmd = ["gh", "api", "-X", method, "-H", "Accept: application/vnd.github+json", path]
    if body is not None:
        cmd += ["--input", "-"]
    res = subprocess.run(cmd, input=None if body is None else json.dumps(body), capture_output=True, text=True)
    if res.returncode != 0:
        raise GhError(f"{method} {path}: {res.stdout.strip() or res.stderr.strip()}")
    return json.loads(res.stdout) if res.stdout.strip() else None


# ------------------------------------------------------------------------------------------------ desired state
def ruleset_body(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "target": spec["target"],
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": spec["include"], "exclude": spec["exclude"]}},
        "rules": spec["rules"],
    }


def normalise_ruleset(rs: dict[str, Any], managed: dict[str, Any] | None = None) -> dict[str, Any]:
    """The fields we manage, in a comparable form. ``managed``: the desired ruleset; only its rule parameters are
    compared (GitHub adds defaults for the others)."""
    keys = {r["type"]: set(r.get("parameters", {})) for r in (managed or rs).get("rules", [])}
    rules = []
    for r in rs.get("rules", []):
        params = {k: (sorted(v) if isinstance(v, list) else v) for k, v in (r.get("parameters") or {}).items()
                  if k in keys.get(r["type"], set())}
        rules.append({"type": r["type"], **({"parameters": params} if params else {})})
    cond = rs.get("conditions", {}).get("ref_name", {})
    return {
        "target": rs.get("target"),
        "enforcement": rs.get("enforcement"),
        "bypass_actors": rs.get("bypass_actors", []),
        "include": sorted(cond.get("include", [])),
        "exclude": sorted(cond.get("exclude", [])),
        "rules": sorted(rules, key=lambda r: r["type"]),
    }


# ------------------------------------------------------------------------------------------------ one repository
class Plan:
    def __init__(self, repo: str) -> None:
        self.repo = repo
        self.lines: list[str] = []
        self.actions: list[tuple[str, str, Any]] = []  # (method, path, body)

    def add(self, text: str, method: str, path: str, body: Any) -> None:
        self.lines.append(text)
        self.actions.append((method, path, body))

    def note(self, text: str) -> None:
        self.lines.append(f"({text})")


def plan_repo(cfg: dict[str, Any], repo: str, kind: str, archive: bool) -> Plan:
    org = cfg["org"]
    p = Plan(repo)
    info = gh(f"repos/{org}/{repo}")
    base = f"repos/{org}/{repo}"

    if info.get("archived"):
        p.note("archived: nothing to do")
        return p

    if kind == "archive":
        if archive:
            p.add("archive the repository (read-only; can be unarchived)", "PATCH", base, {"archived": True})
        else:
            p.note("to archive: run with --archive")
        return p

    # settings
    want = dict(cfg["settings"])
    if info.get("private"):
        want.pop("allow_auto_merge", None)  # not available for private repositories on the Free plan
    diff = {k: v for k, v in want.items() if info.get(k) != v}
    if diff:
        txt = ", ".join(f"{k}: {info.get(k)} -> {v}" for k, v in diff.items())
        p.add(f"settings: {txt}", "PATCH", base, diff)

    # GitHub Actions: off where the repository runs no CI of its own (forks: upstream's workflows stay in the tree)
    want_actions = cfg.get("actions_enabled_by_kind", {}).get(kind)
    if want_actions is not None:
        enabled = gh(f"{base}/actions/permissions").get("enabled")
        if enabled != want_actions:
            p.add(f"actions enabled: {enabled} -> {want_actions}", "PUT", f"{base}/actions/permissions",
                  {"enabled": want_actions})

    # rulesets
    names = cfg["rulesets_by_kind"].get(kind, [])
    if names and info.get("private"):
        p.note("private: rulesets need a paid plan, skipped (applied once the repository is public)")
    elif names:
        existing = {r["name"]: r for r in gh(f"{base}/rulesets?includes_parents=false")}
        for name in names:
            body = ruleset_body(name, cfg["rulesets"][name])
            if name not in existing:
                p.add(f"ruleset {name}: create ({describe(body)})", "POST", f"{base}/rulesets", body)
                continue
            current = gh(f"{base}/rulesets/{existing[name]['id']}")
            if normalise_ruleset(current, body) != normalise_ruleset(body):
                p.add(f"ruleset {name}: update ({describe(body)})", "PUT", f"{base}/rulesets/{existing[name]['id']}", body)

    # labels
    label_set = cfg["labels_by_kind"].get(kind)
    if label_set:
        have = {lb["name"]: lb for lb in gh(f"{base}/labels?per_page=100")}
        for lb in cfg["labels"][label_set]:
            cur = have.get(lb["name"])
            if cur is None:
                p.add(f"label {lb['name']}: create", "POST", f"{base}/labels", lb)
            elif cur["color"].lower() != lb["color"].lower() or (cur.get("description") or "") != lb["description"]:
                p.add(f"label {lb['name']}: update", "PATCH", f"{base}/labels/{lb['name']}",
                      {"color": lb["color"], "description": lb["description"]})
    return p


def describe(body: dict[str, Any]) -> str:
    inc = ", ".join(r.split("/", 2)[2] for r in body["conditions"]["ref_name"]["include"])
    exc = body["conditions"]["ref_name"]["exclude"]
    rules = ", ".join(r["type"] for r in body["rules"])
    return f"{inc}{' except ' + ', '.join(r.split('/', 2)[2] for r in exc) if exc else ''}: {rules}"


# ------------------------------------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos", nargs="*", help="only these repositories (default: all in the configuration)")
    ap.add_argument("--apply", action="store_true", help="make the changes (default: dry run)")
    ap.add_argument("--archive", action="store_true", help="also archive the repositories under 'archive'")
    args = ap.parse_args()

    cfg = json.loads(CONFIG.read_text())
    kind_of = {r: k for k, rs in cfg["kinds"].items() for r in rs} | {r: "archive" for r in cfg["archive"]}

    org_repos = {r["name"] for r in gh(f"orgs/{cfg['org']}/repos?per_page=100")}
    unknown = org_repos - set(kind_of) - set(cfg["ignored"])
    if unknown:
        print(f"not in the configuration (left as they are): {', '.join(sorted(unknown))}\n")

    repos = args.repos or sorted(kind_of, key=str.lower)
    total = 0
    for repo in repos:
        if repo not in kind_of:
            print(f"{repo}: not in the configuration", file=sys.stderr)
            return 2
        try:
            plan = plan_repo(cfg, repo, kind_of[repo], args.archive)
        except GhError as e:
            print(f"{repo}: ERROR {e}")
            continue
        changes = [ln for ln in plan.lines if not ln.startswith("(")]
        total += len(changes)
        print(f"{repo} [{kind_of[repo]}]: {'nothing to do' if not plan.lines else ''}")
        for ln in plan.lines:
            print(f"    {ln}")
        if args.apply:
            for method, path, body in plan.actions:
                try:
                    gh(path, method, body)
                except GhError as e:
                    print(f"    FAILED: {e}")
    print(f"\n{total} change(s) {'applied' if args.apply else 'to apply (dry run; --apply to make them)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
