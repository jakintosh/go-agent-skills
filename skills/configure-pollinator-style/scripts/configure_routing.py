#!/usr/bin/env python3
"""Safely configure Pollinator Style routing in an agentic harness's guidance file.

One invocation targets exactly one harness, chosen with the required ``--harness``
flag. Each harness declares where its guidance lives and which harness-specific
files take precedence; the marker-block insert/update/remove logic is shared.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any, Callable


START_MARKER = "<!-- pollinator-style:start -->"
END_MARKER = "<!-- pollinator-style:end -->"
ROUTER_BLOCK = """<!-- pollinator-style:start -->
## Pollinator Style routing

For Go design, implementation, debugging, testing, and review work:

1. Inspect the relevant code, then use every available Pollinator Style skill whose described domain is materially affected.
2. Follow selected skills' adjacent-domain routing when another domain's contract or invariant changes; do not select skills merely for unchanged dependencies.
3. Load only the references relevant to the concrete work and re-evaluate selection as scope emerges.
4. Treat the guidance as a strong default while preserving coherent local conventions outside the requested scope, and explain material deviations.

Do not wait for the user to name a skill explicitly.
<!-- pollinator-style:end -->"""


class Harness:
    """Per-harness description of where routing guidance lives.

    A harness owns its guidance filename and global home. ``override_name`` and
    ``uses_fallbacks`` capture harness-specific precedence rules; harnesses
    without those concepts leave them unset and skip the related logic.
    """

    def __init__(
        self,
        name: str,
        guidance_filename: str,
        default_home: Callable[[], Path],
        home_env: str | None = None,
        override_name: str | None = None,
        uses_fallbacks: bool = False,
    ) -> None:
        self.name = name
        self.guidance_filename = guidance_filename
        self.home_env = home_env
        self.default_home = default_home
        self.override_name = override_name
        self.uses_fallbacks = uses_fallbacks


def opencode_default_home() -> Path:
    """Resolve OpenCode's config home, honoring XDG_CONFIG_HOME."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "opencode"


HARNESSES: dict[str, Harness] = {
    "codex": Harness(
        name="codex",
        guidance_filename="AGENTS.md",
        home_env="CODEX_HOME",
        default_home=lambda: Path.home() / ".codex",
        override_name="AGENTS.override.md",
        uses_fallbacks=True,
    ),
    "claude": Harness(
        name="claude",
        guidance_filename="CLAUDE.md",
        home_env="CLAUDE_HOME",
        default_home=lambda: Path.home() / ".claude",
    ),
    "opencode": Harness(
        name="opencode",
        guidance_filename="AGENTS.md",
        default_home=opencode_default_home,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Configure Pollinator Style routing in an agentic harness's guidance file.",
    )
    parser.add_argument(
        "--harness",
        choices=tuple(HARNESSES),
        required=True,
        help="Which agentic harness to configure (for example, codex or claude).",
    )
    parser.add_argument(
        "--scope",
        choices=("repo", "global"),
        default="repo",
        help="Configure the current repository by default, or the harness's global guidance.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root to configure instead of discovering it from the current directory.",
    )
    parser.add_argument(
        "--home",
        help="Harness home to use instead of the harness's home environment variable or default.",
    )
    parser.add_argument(
        "--allow-override",
        action="store_true",
        help="Allow modification of the harness's active override guidance file, when it has one.",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove the marked Pollinator Style routing block.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the action without writing the target file.",
    )
    return parser.parse_args()


def discover_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def home_path(harness: Harness, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    configured = os.environ.get(harness.home_env) if harness.home_env else None
    if configured:
        return Path(configured).expanduser().resolve()
    return harness.default_home().resolve()


def parse_fallback_names(config_path: Path) -> tuple[list[str] | None, str | None]:
    if not config_path.is_file():
        return None, None
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"could not read {config_path}: {exc}"

    match = re.search(
        r"(?ms)^\s*project_doc_fallback_filenames\s*=\s*(\[[^\]]*\])",
        text,
    )
    if match is None:
        return None, None
    try:
        value = ast.literal_eval(match.group(1))
    except (SyntaxError, ValueError):
        return None, f"could not parse project_doc_fallback_filenames in {config_path}"
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        return None, f"project_doc_fallback_filenames in {config_path} is not a string array"
    return [item.strip() for item in value], None


def fallback_names(repo_root: Path, home: Path) -> tuple[list[str], list[str]]:
    names: list[str] = []
    warnings: list[str] = []
    for config_path in (
        home / "config.toml",
        repo_root / ".codex" / "config.toml",
    ):
        configured, warning = parse_fallback_names(config_path)
        if warning:
            warnings.append(warning)
        if configured is not None:
            names = configured
    return names, warnings


def is_nonempty_file(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        return bool(path.read_text(encoding="utf-8").strip())
    except OSError:
        return False


def guidance_candidates(
    directory: Path,
    harness: Harness,
    fallbacks: list[str],
) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    if harness.override_name is not None:
        candidates.append((directory / harness.override_name, "override"))
    candidates.append((directory / harness.guidance_filename, "primary"))
    candidates.extend((directory / name, "fallback") for name in fallbacks)
    return candidates


def select_active_target(
    candidates: list[tuple[Path, str]],
) -> tuple[Path, str]:
    for path, kind in candidates:
        if is_nonempty_file(path):
            return path, kind
    for path, kind in candidates:
        if kind == "primary":
            return path, kind
    raise ValueError("guidance candidates did not include the primary guidance file")


def find_marked_targets(
    candidates: list[tuple[Path, str]],
) -> tuple[list[tuple[Path, str]], list[str]]:
    marked: list[tuple[Path, str]] = []
    warnings: list[str] = []
    for path, kind in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.append(f"could not inspect {path} for an existing router: {exc}")
            continue
        if START_MARKER in text or END_MARKER in text:
            marked.append((path, kind))
    return marked, warnings


def validate_markers(text: str) -> None:
    starts = text.count(START_MARKER)
    ends = text.count(END_MARKER)
    if starts != ends or starts > 1:
        raise ValueError(
            "expected zero or one complete Pollinator Style marker block"
        )


def add_or_update(text: str, file_existed: bool) -> tuple[str, str, bool]:
    validate_markers(text)
    if START_MARKER in text:
        start = text.index(START_MARKER)
        end = text.index(END_MARKER, start) + len(END_MARKER)
        existing = text[start:end]
        if existing == ROUTER_BLOCK:
            return text, "unchanged", True
        return text[:start] + ROUTER_BLOCK + text[end:], "updated_router", True

    prefix = text.rstrip()
    updated = ROUTER_BLOCK if not prefix else prefix + "\n\n" + ROUTER_BLOCK
    updated += "\n"
    action = "added_router" if file_existed else "created_file"
    return updated, action, False


def remove_router(text: str) -> tuple[str, str, bool]:
    validate_markers(text)
    if START_MARKER not in text:
        return text, "not_present", False

    start = text.index(START_MARKER)
    end = text.index(END_MARKER, start) + len(END_MARKER)
    before = text[:start].rstrip()
    after = text[end:].strip()
    if before and after:
        updated = before + "\n\n" + after + "\n"
    elif before:
        updated = before + "\n"
    elif after:
        updated = after + "\n"
    else:
        updated = ""
    return updated, "removed_router", True


def atomic_write(path: Path, text: str, previous_mode: int | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.chmod(temporary, previous_mode if previous_mode is not None else 0o644)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def emit(payload: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(exit_code)


def main() -> None:
    args = parse_args()
    harness = HARNESSES[args.harness]
    repo_root = (
        Path(args.repo_root).expanduser().resolve()
        if args.repo_root
        else discover_repo_root(Path.cwd())
    )
    home = home_path(harness, args.home)
    if args.scope == "global" or not harness.uses_fallbacks:
        names: list[str] = []
        warnings: list[str] = []
    else:
        names, warnings = fallback_names(repo_root, home)
    target_directory = home if args.scope == "global" else repo_root
    candidates = guidance_candidates(target_directory, harness, names)
    active_target, active_kind = select_active_target(candidates)
    marked_targets, marker_warnings = find_marked_targets(candidates)
    warnings.extend(marker_warnings)

    if len(marked_targets) > 1:
        emit(
            {
                "action": "error",
                "changed": False,
                "harness": harness.name,
                "repository_name": repo_root.name,
                "repository_root": str(repo_root),
                "scope": args.scope,
                "targets": [str(path) for path, _ in marked_targets],
                "warnings": warnings + [
                    "multiple Pollinator Style marker blocks exist at this scope; refusing to guess which one to manage"
                ],
                "would_change": False,
            },
            2,
        )

    if args.remove and marked_targets:
        target, target_kind = marked_targets[0]
    else:
        target, target_kind = active_target, active_kind

    if not args.remove and marked_targets and marked_targets[0][0] != target:
        emit(
            {
                "action": "error",
                "changed": False,
                "harness": harness.name,
                "repository_name": repo_root.name,
                "repository_root": str(repo_root),
                "scope": args.scope,
                "target": str(target),
                "target_kind": target_kind,
                "warnings": warnings + [
                    f"Pollinator Style routing exists in inactive guidance file {marked_targets[0][0]}; move or remove that block before configuring {target}"
                ],
                "would_change": False,
            },
            2,
        )

    file_existed = target.exists()

    if warnings and target_kind == "primary" and not is_nonempty_file(target):
        emit(
            {
                "action": "error",
                "changed": False,
                "file_existed": file_existed,
                "harness": harness.name,
                "repository_name": repo_root.name,
                "repository_root": str(repo_root),
                "router_existed": False,
                "scope": args.scope,
                "target": str(target),
                "target_kind": target_kind,
                "warnings": warnings + [
                    f"refusing to create {harness.guidance_filename} because an unparsed fallback configuration could be shadowed"
                ],
                "would_change": False,
            },
            2,
        )

    if target_kind == "override" and not args.allow_override:
        emit(
            {
                "action": "confirmation_required",
                "changed": False,
                "file_existed": file_existed,
                "harness": harness.name,
                "repository_name": repo_root.name,
                "repository_root": str(repo_root),
                "router_existed": False,
                "scope": args.scope,
                "target": str(target),
                "target_kind": target_kind,
                "warnings": warnings + [
                    f"the active {harness.override_name} takes precedence; confirm before modifying it"
                ],
                "would_change": False,
            },
            3,
        )

    try:
        original = target.read_text(encoding="utf-8") if file_existed else ""
    except OSError as exc:
        emit(
            {
                "action": "error",
                "changed": False,
                "harness": harness.name,
                "scope": args.scope,
                "target": str(target),
                "warnings": warnings + [f"could not read target: {exc}"],
                "would_change": False,
            },
            2,
        )

    try:
        if args.remove:
            updated, action, router_existed = remove_router(original)
        else:
            updated, action, router_existed = add_or_update(original, file_existed)
    except ValueError as exc:
        emit(
            {
                "action": "error",
                "changed": False,
                "file_existed": file_existed,
                "harness": harness.name,
                "repository_name": repo_root.name,
                "repository_root": str(repo_root),
                "router_existed": START_MARKER in original,
                "scope": args.scope,
                "target": str(target),
                "target_kind": target_kind,
                "warnings": warnings + [str(exc)],
                "would_change": False,
            },
            2,
        )

    would_change = updated != original
    changed = False
    if would_change and not args.dry_run:
        previous_mode = stat.S_IMODE(target.stat().st_mode) if file_existed else None
        try:
            atomic_write(target, updated, previous_mode)
        except OSError as exc:
            emit(
                {
                    "action": "error",
                    "changed": False,
                    "file_existed": file_existed,
                    "harness": harness.name,
                    "repository_name": repo_root.name,
                    "repository_root": str(repo_root),
                    "router_existed": router_existed,
                    "scope": args.scope,
                    "target": str(target),
                    "target_kind": target_kind,
                    "warnings": warnings + [f"could not write target: {exc}"],
                    "would_change": True,
                },
                2,
            )
        changed = True

    emit(
        {
            "action": action,
            "changed": changed,
            "dry_run": args.dry_run,
            "file_existed": file_existed,
            "guidance_filename": harness.guidance_filename,
            "harness": harness.name,
            "repository_name": repo_root.name,
            "repository_root": str(repo_root),
            "router_existed": router_existed,
            "scope": args.scope,
            "target": str(target),
            "target_kind": target_kind,
            "warnings": warnings,
            "would_change": would_change,
        }
    )


if __name__ == "__main__":
    main()
