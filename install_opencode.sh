#!/usr/bin/env bash
# Install (or uninstall) Pollinator Style skills for OpenCode.
#
# OpenCode has no plugin manifest; it discovers skills by directory. This copies
# every skill under skills/ into OpenCode's user skill directory
# (${XDG_CONFIG_HOME:-~/.config}/opencode/skills), overwriting previous copies of
# these skills while leaving unrelated skills in place. Re-run after `git pull`
# to update. Pass --uninstall to remove them again.

set -euo pipefail
shopt -s nullglob

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src_dir="$repo_dir/skills"
dest_dir="${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills"

uninstall=0
case "${1:-}" in
  --uninstall) uninstall=1 ;;
  -h | --help)
    echo "Usage: $(basename "$0") [--uninstall]"
    echo "  (default)    copy Pollinator Style skills into $dest_dir"
    echo "  --uninstall  remove the Pollinator Style skills from that directory"
    exit 0
    ;;
  "") ;;
  *)
    echo "error: unknown argument: $1" >&2
    echo "run with --help for usage" >&2
    exit 2
    ;;
esac

if [ ! -d "$src_dir" ]; then
  echo "error: skills directory not found at $src_dir" >&2
  exit 1
fi

if [ "$uninstall" -eq 1 ]; then
  removed=0
  for skill_path in "$src_dir"/*/; do
    name="$(basename "$skill_path")"
    target="$dest_dir/$name"
    if [ -e "$target" ]; then
      rm -rf "$target"
      echo "removed $name"
      removed=$((removed + 1))
    fi
  done
  echo "Uninstalled $removed skill(s) from $dest_dir"
  exit 0
fi

mkdir -p "$dest_dir"
installed=0
for skill_path in "$src_dir"/*/; do
  name="$(basename "$skill_path")"
  target="$dest_dir/$name"
  rm -rf "$target"
  cp -R "$src_dir/$name" "$target"
  echo "installed $name"
  installed=$((installed + 1))
done
echo "Installed $installed skill(s) into $dest_dir"
echo "Start a new OpenCode session to load them."
