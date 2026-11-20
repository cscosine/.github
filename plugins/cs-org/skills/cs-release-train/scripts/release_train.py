#!/usr/bin/env python3
"""Release train: release candidates (or releases) of several cscosine projects, one at a time.

    release_train.py <plan.json> [--dry-run]

Plan (JSON):

    {
      "org": "cscosine",
      "workspace": "/path/to/the/clones",
      "branch": "main",
      "steps": [
        {"repo": "third_party_base_libs", "tag": "v0.1.0-rc10",
         "commit_message": "...",                       # optional: regenerate the workflow and commit first
         "tag_inner": {"dir": "workspace", "branch": "main",
                       "tags": {"eigen3": "v5.0.1-cs.2", "fmt": "v12.2.1-cs.2"}}},   # optional
        {"repo": "csqt6", "tag": null},                 # push only (no build)
        {"repo": "csfoundation", "tag": "v0.1.0-rc10", "commit_message": "..."}
      ]
    }

Per step: (commit_message) regenerate the workflow (`./<repo>_project.py generate-github-workflow`, the providers'
new releases must exist by then) and commit with the repository's .venv; push the branch and cancel its build (the tag
build is the test and the release); (tag_inner) record the inner repositories' heads; push the tag; wait for the tag
run; re-run jobs cancelled without a runner (GitHub capacity, up to 3 times); check the release; (tag_inner) tag the
inner repositories on the recorded heads. Stops at the first failure. Resumable: a step whose tag already exists on
GitHub waits for its run instead of pushing again.

One build at a time on purpose: GitHub's runners are limited (macOS: 5 jobs at once on the Free plan).
"""

import json
import subprocess
import sys
import time
from pathlib import Path

COAUTHOR = ""  # an agent adds its own trailer to commit_message if it wants one


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}: {(r.stderr or r.stdout).strip()[-800:]}")
    return r.stdout.strip()


def gh(path: str, method: str = "GET") -> object:
    out = run(["gh", "api", "-X", method, path], check=method == "GET")
    return json.loads(out) if out else None


def in_venv(repo: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", "-c", f"source .venv/bin/activate && {script}"], cwd=repo, capture_output=True,
                          text=True)


def commit(repo: Path, message: str, tmp: Path) -> None:
    msg_file = tmp / f"msg-{repo.name}.txt"
    msg_file.write_text(message + "\n")
    for _ in range(3):  # a hook may regenerate files (e.g. launch.json): add them and commit again
        run(["git", "add", "-A"], cwd=repo)
        r = in_venv(repo, f"git commit -q -F {msg_file}")
        if r.returncode == 0:
            return
    raise RuntimeError(f"{repo.name}: commit failed: {(r.stdout + r.stderr)[-1500:]}")


def find_run(org: str, repo: str, branch: str, sha: str, timeout_s: int) -> dict:
    start = time.time()
    while time.time() - start < timeout_s:
        for r in gh(f"repos/{org}/{repo}/actions/runs?branch={branch}&per_page=10")["workflow_runs"]:  # type: ignore[index]
            if r["head_sha"] == sha:
                return r
        time.sleep(20)
    raise RuntimeError(f"{repo}: no run for {branch} {sha[:8]} after {timeout_s}s")


def wait_done(org: str, repo: str, run_id: int) -> dict:
    while True:
        r = gh(f"repos/{org}/{repo}/actions/runs/{run_id}")
        if r["status"] == "completed":  # type: ignore[index]
            return r  # type: ignore[return-value]
        time.sleep(120)


def bad_jobs(org: str, repo: str, run_id: int) -> list[dict]:
    jobs = gh(f"repos/{org}/{repo}/actions/runs/{run_id}/jobs?per_page=100")["jobs"]  # type: ignore[index]
    return [j for j in jobs if j["conclusion"] not in ("success", "skipped")]


def wait_with_reruns(org: str, repo: str, run_id: int, attempts: int = 3) -> dict:
    done = wait_done(org, repo, run_id)
    for i in range(attempts):
        bad = bad_jobs(org, repo, run_id)
        if done["conclusion"] == "success" or not bad or not all(
                j["conclusion"] == "cancelled" and not j.get("runner_name") for j in bad):
            return done
        log(f"{repo}: {len(bad)} job(s) cancelled without a runner (GitHub capacity): re-running ({i + 1})")
        gh(f"repos/{org}/{repo}/actions/runs/{run_id}/rerun-failed-jobs", "POST")
        time.sleep(60)
        done = wait_done(org, repo, run_id)
    return done


def main() -> int:
    plan = json.loads(Path(sys.argv[1]).read_text())
    dry = "--dry-run" in sys.argv
    org, ws, branch = plan.get("org", "cscosine"), Path(plan["workspace"]), plan.get("branch", "main")
    tmp = Path(sys.argv[1]).resolve().parent
    for step in plan["steps"]:
        name, tag, message = step["repo"], step.get("tag"), step.get("commit_message")
        repo = ws / name
        log(f"== {name}")
        resumed = bool(tag) and bool(run(["git", "ls-remote", "origin", f"refs/tags/{tag}"], cwd=repo))
        if dry:
            log(f"[dry] {'resume ' + tag if resumed else ('regenerate + commit, ' if message else '') + 'push ' + branch}"
                + (f", tag {tag}" if tag and not resumed else "") + (", tag inner" if step.get("tag_inner") else ""))
            continue
        inner = step.get("tag_inner")
        heads: dict[str, str] = {}
        if resumed:
            log(f"{tag} already on GitHub: waiting for its run")
            sha = run(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=repo)
        else:
            if message:
                r = in_venv(repo, f"./{name}_project.py generate-github-workflow")
                if r.returncode != 0:
                    log(f"FAIL {name}: workflow generation: {(r.stdout + r.stderr)[-1200:]}")
                    return 1
                commit(repo, message, tmp)
                log(f"committed {run(['git', 'log', '--oneline', '-1'], cwd=repo)}")
            if run(["git", "status", "--porcelain"], cwd=repo):
                log(f"FAIL {name}: uncommitted changes")
                return 1
            sha = run(["git", "rev-parse", "HEAD"], cwd=repo)
            run(["git", "push", "-q", "origin", branch], cwd=repo)
            log(f"pushed {branch} {sha[:8]}")
            if not tag:
                continue
            try:
                branch_run = find_run(org, name, branch, sha, 300)
                gh(f"repos/{org}/{name}/actions/runs/{branch_run['id']}/cancel", "POST")
                log(f"cancelled the {branch} run {branch_run['id']} (the tag build is the test)")
            except RuntimeError as e:
                log(f"(no {branch} run to cancel: {e})")
            if inner:
                for r_name in inner["tags"]:
                    heads[r_name] = run(["git", "-C", str(repo / inner["dir"] / r_name), "ls-remote", "origin",
                                         f"refs/heads/{inner.get('branch', 'main')}"]).split()[0]
            run(["git", "tag", "-a", tag, sha, "-m", f"{name} {tag}"], cwd=repo)
            run(["git", "push", "-q", "origin", tag], cwd=repo)
            log(f"pushed tag {tag}")
        tag_run = find_run(org, name, tag, sha, 600)
        log(f"tag run {tag_run['id']}: {tag_run['html_url']}")
        done = wait_with_reruns(org, name, tag_run["id"])
        if done["conclusion"] != "success":
            log(f"FAIL {name} {tag}: {done['conclusion']}; jobs: "
                f"{[j['name'][:80] for j in bad_jobs(org, name, tag_run['id'])][:10]}")
            return 1
        rel = gh(f"repos/{org}/{name}/releases/tags/{tag}")
        log(f"OK {name} {tag}: prerelease={rel['prerelease']} assets={len(rel['assets'])}")  # type: ignore[index]
        if inner and heads:
            for r_name, r_tag in inner["tags"].items():
                r_dir = repo / inner["dir"] / r_name
                run(["git", "fetch", "-q", "origin"], cwd=r_dir)
                run(["git", "tag", "-a", r_tag, heads[r_name], "-m", f"{r_name} {r_tag}: built by {name} {tag}"],
                    cwd=r_dir)
                run(["git", "push", "-q", "origin", r_tag], cwd=r_dir)
            log(f"inner repositories tagged: {', '.join(f'{k} {v}' for k, v in inner['tags'].items())}")
    log("TRAIN DONE")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        log(f"FAIL: {e}")
        sys.exit(1)
