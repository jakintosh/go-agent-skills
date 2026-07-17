---
name: work-with-go-makefiles
description: Guide Makefiles for Go projects. Use for design, implementation, debugging, testing, or review of targets, variables, help, build, generation, tests, lint, installation, local init or run orchestration, cleanup, or reset behavior.
---

# Work with Go Makefiles

Use this skill as the project-action knowledge layer for Go repositories. Treat the Makefile as a discoverable interface over real project workflows, whether creating it or changing one target in an established file.

## Preserve the action surface

- Keep stable target names and user-overridable variables compatible unless a workflow redesign is explicit.
- Use the Makefile as the primary local action surface, with `help` as the default goal.
- Keep repeated paths, tools, binaries, ports, URLs, and inputs in clearly scoped variables.
- Keep operational recipes visible; silence only help output or commands with a specific need for quiet behavior.
- Compose public project and CLI commands instead of recreating application behavior in shell.
- Keep `clean` limited to reproducible build and test artifacts.
- Give local config, data, databases, secrets, or other runtime state an explicitly destructive target such as `reset`.
- Keep direct recipes readable and move genuinely orchestration-heavy workflows into a narrow script when that improves testing or reuse.

## Consult the knowledge base

1. Inspect the existing Makefile, documented contributor commands, binaries, generation directives, CI workflows, and local runtime dependencies.
2. Read [makefile-shape.md](references/makefile-shape.md) before creating, changing, debugging, or reviewing a Makefile.
3. Identify whether the change affects target compatibility, dependencies, variables, help, generation, checks, installation, initialization, serving, cleanup, or destructive state.
4. Preserve coherent repository-specific commands while applying the guide's target semantics and safety boundaries.
5. Explain any material deviation where the repository's established workflow makes the default unsuitable.

## Include adjacent domains

- Consult [Go CLI guidance](../work-with-go-clis/SKILL.md) when build, generate, install, init, or run targets expose or alter CLI behavior.
- Consult [Go config guidance](../work-with-go-config/SKILL.md) when targets choose config/data roots, generate config material, or remove local configuration state.
- Consult [Go server guidance](../work-with-go-servers/SKILL.md) when run or serve targets alter listener setup, infrastructure, lifecycle, or readiness behavior.
- Consult [Go service guidance](../work-with-go-services/SKILL.md) when init targets perform mutable application bootstrap or durable seed work.
- Consult [Go database guidance](../work-with-go-databases/SKILL.md) when targets initialize, migrate, seed, reset, or otherwise manipulate durable state.

Keep each domain's semantics in its owning skill. The Makefile should compose those public workflows and make them discoverable.

## Validate the result

- Start with a non-mutating inspection such as `make help` and a dry run where practical.
- Run every changed safe target, then the repository's documented checks in proportion to risk.
- Verify `.PHONY` declarations, target dependencies, variable expansion, override behavior, and help coverage.
- Confirm generation runs before builds when generated code affects compilation.
- Confirm `clean` cannot remove local runtime state and destructive targets have unmistakable names and documented scope.
- Exercise init and run from a clean disposable local setup when their orchestration changes.
- For reviews, report broken workflows, unsafe deletion scope, hidden prerequisites, and interface regressions rather than cosmetic preference alone.

## Keep the skill current

When repeated project work exposes a missing target convention, stale command, or unclear safety boundary, update [makefile-shape.md](references/makefile-shape.md). Change `SKILL.md` only when activation, universal boundaries, consultation behavior, or adjacent routing needs to change.
