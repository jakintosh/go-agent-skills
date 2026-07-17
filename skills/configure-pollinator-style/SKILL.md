---
name: configure-pollinator-style
description: Manage the marked Pollinator Style routing block in a harness's repository or global guidance file. Use to configure, update, inspect, repair, or remove ambient routing; default to repository scope unless the user explicitly requests global setup.
---

# Configure Pollinator Style

Use the bundled script to manage one marked Pollinator Style routing block without overwriting other agent instructions. After a successful configuration, give the user the fixed welcome described below.

## Select the harness

The script configures exactly one agentic harness per run, named with the required `--harness` flag. Choose the value for the harness you are operating in:

- `--harness claude` for Claude Code (guidance file `CLAUDE.md`).
- `--harness codex` for Codex (guidance file `AGENTS.md`).

If the user names a harness, use it. Otherwise default to the harness you are running in. Only configure more than one harness when the user explicitly asks, running the script once per harness.

## Choose the scope

- Default to the current repository when the user says “configure,” “set up,” “install,” or “enable” without naming a scope.
- Use global scope only when the user explicitly asks for global, personal, all-repository, or cross-repository behavior.
- Treat removing or inspecting configuration the same way: repository scope by default, global only when explicit.

## Run the configurator

Resolve this skill's directory and run, passing the harness selected above:

```sh
python3 <skill-dir>/scripts/configure_routing.py --harness <harness>
```

Use the relevant options:

- `--harness <harness>` (required) names the harness to configure, such as `claude` or `codex`.
- `--scope global` for explicitly requested global configuration.
- `--repo-root <path>` when the intended repository is not the current working directory.
- `--remove` when the user asks to remove Pollinator Style routing.
- `--dry-run` when the user asks to inspect what would happen without changing a file.
- `--allow-override` only after the user confirms that an active override guidance file should be modified. This applies only to harnesses that support an override file (Codex's `AGENTS.override.md`).

The script emits one JSON object. Treat it as the source of truth for the harness, the guidance filename, the target path, whether the file and router already existed, and whether content changed. Do not manually recreate the router block.

If the script returns `confirmation_required`, explain that the harness's active override guidance file takes precedence and ask whether to update it. If confirmed, rerun with `--allow-override`. If the script reports malformed or duplicate markers, stop without editing and report the exact file.

For global scope, request filesystem approval when the environment requires it. Never redirect output into an instruction file or overwrite the file wholesale.

## Personalize from evidence

After a successful repository configuration, inspect only enough of the repository to add one useful sentence:

- If `go.mod` exists, inspect recognizable package and project paths such as `internal/service`, `internal/database`, `internal/api`, `internal/web`, `internal/server`, `internal/config`, `cmd`, `pkg`, and `Makefile`. Name up to three clearly detected domains and say that ordinary requests affecting them can route to the matching skills automatically.
- If `go.mod` exists without recognizable domain paths, say that Pollinator routing is ready for applicable Go work and will select installed domain skills as the code evolves.
- If no `go.mod` exists, say that no Go module was detected and the routing will remain dormant until applicable Go work appears.

Use the repository’s actual name from the script result. Mention only domains supported by concrete repository evidence; do not speculate about architecture. Omit the personalized sentence for global scope or when inspection is unavailable.

## Report completion

For `created_file`, `added_router`, `updated_router`, or `unchanged`, use this structure and wording closely:

```text
Pollinator Style is ready for <repository name or “your global agent profile”>.

- Guidance file: `<absolute path>`
- Result: <result sentence>

<optional repository-specific sentence>

How it works: You do not need to mention Pollinator Style or name a skill in ordinary requests. Ask for the change normally. The router tells the agent to inspect the code, identify every affected engineering domain, select the matching installed Pollinator Style skills, and load only the references needed for the work.

<new-session sentence>
```

Map `action` to the result sentence exactly:

- `created_file`: `Created the guidance file and added Pollinator Style routing.`
- `added_router`: `The guidance file already existed; added Pollinator Style routing without changing its other instructions.`
- `updated_router`: `Pollinator Style routing was already present; updated it to the current version.`
- `unchanged`: `Pollinator Style routing was already present and current; no changes were needed.`

When `changed` is true, use: `Start a new session in the configured harness so the updated guidance is loaded from the beginning.`

When `changed` is false, use: `No reload is required for this configuration result.`

For removal, report the same guidance file and map:

- `removed_router`: `Removed the Pollinator Style routing block and preserved the file's other instructions.`
- `not_present`: `No Pollinator Style routing block was present; no changes were needed.`

Do not include the welcome explainer after removal. For `--dry-run`, clearly say that no file was changed and describe the reported action as what would happen.
