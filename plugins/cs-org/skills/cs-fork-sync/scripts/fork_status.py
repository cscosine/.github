#!/usr/bin/env python3
"""State of cscosine forks: upstream, base tag, our patches, newer upstream releases, our last tag.

    fork_status.py <fork clone> [<fork clone> ...]

Reads each fork's cscosine/README.md (the `Upstream` and `Base` rows), fetches the upstream tags (no other change to
the clone) and prints, per fork: base tag, our commits on top (`git log <base>..main`), the newest upstream release
tags after the base, and our last `-cs.N` (or `-cpu.N` / `-cuda.N`) tag.
"""

import re
import subprocess
import sys
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def version_key(tag: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", tag)[:4])


def main() -> None:
    for arg in sys.argv[1:]:
        repo = Path(arg)
        readme = repo / "cscosine" / "README.md"
        if not readme.exists():
            print(f"{repo.name}: no cscosine/README.md (not a documented fork)")
            continue
        text = readme.read_text()
        if "the cscosine copy" in text:
            print(f"== {repo.name}: a copy of our own (no upstream syncs; cscosine/README.md says where it came from)")
            continue
        up = re.search(r"\| (?:Upstream|Came from) \| <?([^ >|]+)", text)
        base = re.search(r"\| Base \| upstream (?:tag )?`([^`]+)`", text)
        if not (up and base):
            print(f"{repo.name}: Upstream / Base rows not found in cscosine/README.md")
            continue
        url, base_tag = up.group(1).rstrip("/"), base.group(1)
        remote_tags = subprocess.run(["git", "ls-remote", "--tags", "--refs", url + ".git"], capture_output=True,
                                     text=True).stdout.split()
        upstream = [t.removeprefix("refs/tags/") for t in remote_tags if t.startswith("refs/tags/")]
        releases = [t for t in upstream if re.fullmatch(r"v?\d+(\.\d+){1,3}", t)]
        newer = sorted((t for t in releases if version_key(t) > version_key(base_tag)), key=version_key)
        ours = git(repo, "log", "--oneline", f"{base_tag}..origin/main") if git(repo, "rev-parse", "-q", "--verify",
                                                                                 base_tag) else "(base tag not in clone)"
        own = sorted((t for t in git(repo, "tag", "-l").split()
                      if re.fullmatch(rf"v{re.escape(base_tag.lstrip('v'))}-(cs|cpu|cuda)\.\d+", t)),
                     key=lambda t: (t.split("-")[-1].split(".")[0], int(t.rsplit(".", 1)[1])))
        own_str = ", ".join(own) if own else "-"
        print(f"== {repo.name}  upstream {url}  base {base_tag}  our tags on this base: {own_str}")
        print("   our commits:\n" + "\n".join("     " + line for line in ours.splitlines()))
        print(f"   newer upstream releases: {', '.join(newer[-5:]) if newer else 'none'}")


if __name__ == "__main__":
    main()
