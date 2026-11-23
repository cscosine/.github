#!/usr/bin/env bash
# One line per git repository found in a folder (default: the parent of the current repository), and with --inner the
# repositories the projects check out in their _csw/ folder: branch, ahead / behind its upstream, uncommitted
# changes, latest tag. Fetches first (--no-fetch to skip). Reads only; changes nothing.
set -u
root=""; inner=0; fetch=1
for a in "$@"; do
  case "$a" in
    --inner) inner=1 ;;
    --no-fetch) fetch=0 ;;
    *) root="$a" ;;
  esac
done
if [ -z "$root" ]; then
  top=$(git rev-parse --show-toplevel 2>/dev/null) && root=$(dirname "$top") || root=$(pwd)
fi
dirs=("$root"/*/)
[ "$inner" = 1 ] && dirs+=("$root"/*/_csw/*/)
printf "%-48s %-12s %-14s %-6s %s\n" "repository" "branch" "ahead/behind" "dirty" "latest tag"
for d in "${dirs[@]}"; do
  [ -e "$d/.git" ] || continue
  [ "$fetch" = 1 ] && git -C "$d" fetch -q --prune --tags origin 2>/dev/null
  b=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null)
  ab=$(git -C "$d" rev-list --left-right --count HEAD...@{u} 2>/dev/null | awk '{print "+"$1"/-"$2}')
  dirty=$(git -C "$d" status --porcelain 2>/dev/null | wc -l)
  tag=$(git -C "$d" describe --tags --abbrev=0 2>/dev/null)
  printf "%-48s %-12s %-14s %-6s %s\n" "${d#$root/}" "$b" "${ab:-no upstream}" "$dirty" "${tag:--}"
done
