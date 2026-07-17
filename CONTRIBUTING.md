# Contributing

This document defines how to maintain the Pollinator Style plugin and its domain skills.

## Repository structure

```text
.claude-plugin/
  plugin.json
.codex-plugin/
  plugin.json
install_opencode.sh
skills/
  <domain-skill>/
    SKILL.md
    agents/openai.yaml
    references/
```

- Each harness exposes `skills/` through its own install mechanism: the [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) manifest for Claude Code, the [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) manifest for Codex, and the [`install_opencode.sh`](install_opencode.sh) directory-copy script for OpenCode.
- [`skills/`](skills/) contains the setup skill, domain skills, and selectively loaded knowledge, shared across every harness.
- Each domain skill owns its detailed guidance. Do not duplicate the same rule or example across skills.

[`configure-pollinator-style`](skills/configure-pollinator-style/SKILL.md) is an operational setup skill. It owns the managed routing block written into each harness's guidance file and the completion message shown after configuration. Keep its router text, script behavior, README onboarding, and result vocabulary synchronized.

## Harness support

The skills are harness-agnostic; only a thin surface differs per harness. When adding or maintaining harness support, keep these pieces in sync:

- **Install mechanism.** A harness either discovers `skills/` through a manifest directory (`.claude-plugin/`, `.codex-plugin/`) or has skills installed into a directory it scans. OpenCode has no plugin manifest, so [`install_opencode.sh`](install_opencode.sh) copies each skill into `${XDG_CONFIG_HOME:-~/.config}/opencode/skills/`; re-running overwrites those skills and `--uninstall` removes them. Whichever mechanism a harness uses, do not move or rename `skills/`.
- **Guidance file.** The configurator writes the marked routing block into the harness's guidance file — `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex and OpenCode. Codex and OpenCode therefore share the same repository-root `AGENTS.md` block at project scope, which is intended and idempotent; they differ only in their global home (`~/.codex` versus `${XDG_CONFIG_HOME:-~/.config}/opencode`). Harness-specific precedence rules (Codex's `AGENTS.override.md` and `project_doc_fallback_filenames`) are handled only in that harness's branch.
- **Configurator branch.** [`scripts/configure_routing.py`](skills/configure-pollinator-style/scripts/configure_routing.py) selects a harness with the required `--harness` flag. Add a new harness by registering it in the `HARNESSES` table with its guidance filename and a `default_home` callable; supply a `home_env` only when the harness reads one, and set `override_name`/`uses_fallbacks` only for harness-specific precedence. The shared marker-block logic then applies unchanged.
- **Per-skill interface metadata.** `agents/openai.yaml` is Codex-only interface metadata. Harnesses that do not use it (such as Claude Code) ignore it. It is the one place where the Codex `$skill-name` invocation syntax is intentionally retained.

Keep everything else — `SKILL.md` bodies, references, and the README — written for agentic harnesses in general, naming a specific harness only in a dedicated harness section or a small callout where a detail genuinely differs.

## Skill boundaries

Create one skill for a stable domain of engineering judgment. A good boundary lets most meaningful work in that domain share the same small set of invariants while loading different references for different concerns.

Name skills broadly enough to cover design, implementation, debugging, testing, and review. Prefer a name such as `work-with-go-databases` over one limited to a single operation.

Use adjacent-domain routing when a change materially affects more than one skill. Do not load a skill merely because changed code calls or implements an unchanged dependency.

## `SKILL.md`

Keep `SKILL.md` concise and operational. Include:

1. Frontmatter containing only `name` and a concise, front-loaded `description`.
2. Universal domain boundaries and invariants.
3. A protocol for inspecting the target repository and selecting references.
4. Direct links to every owned reference, with precise selection conditions.
5. Adjacent-domain routing.
6. Validation and review behavior.
7. Maintenance guidance for future updates.

Put activation conditions in the description because the body loads only after activation. Front-load the domain, then name recognizable files and concepts plus design, implementation, debugging, testing, and review. Keep descriptions as the single source of truth for domain matching; the ambient router should coordinate selection without duplicating the catalog.

Keep detailed rules, examples, schemas, and optional branches in references rather than condensing them into `SKILL.md`.

## References

Keep references one level below `SKILL.md` and link every reference directly from it:

```text
skills/work-with-go-databases/
  SKILL.md
  references/
    adapter-shape.md
    migrations.md
    migrations-with-go.md
    query-methods.md
    testing.md
    transactions.md
```

Each reference should own one concern and remain useful as declarative library information. It may define ownership boundaries, required rules, canonical shapes, decisions, and examples.

For references longer than 100 lines, include a contents list near the top. Avoid reference chains that require reading one file to discover another; `SKILL.md` owns the complete routing map.

Detailed integration guidance belongs with the consuming domain. Provider skills should mention the touchpoint briefly in adjacent-domain routing without duplicating the integration rules.

## Agent metadata

Every skill should include Codex interface metadata at `agents/openai.yaml` with:

- a human-readable display name
- a 25–64 character short description
- a short default prompt that explicitly names the skill with Codex's `$skill-name` invocation syntax

This file is Codex-specific; other harnesses discover the skill from its `SKILL.md` frontmatter and ignore it. Enable implicit invocation by default. Add scripts, assets, or tool dependencies only when the skill uses them.

## Writing principles

- Define one strong default before documenting variants.
- Prefer positive, executable instructions.
- Use concise examples to demonstrate canonical structure.
- Keep instruction counts low and branching deliberate.
- Preserve coherent repository conventions outside the requested scope.
- Explain material deviations from the guidance.
- Update the narrowest reference when a rule or example changes.
- Update `SKILL.md` only when domain-wide behavior or routing changes.

## Validation

Run the skill creator's `quick_validate.py` against every changed skill and the plugin creator's `validate_plugin.py` against the repository root.

Also verify that:

- every harness manifest (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`) is valid JSON and still discovers `skills/`
- `install_opencode.sh` copies every skill into a scoped skill directory, overwrites cleanly on re-run, leaves unrelated skills in place, and removes only its own skills with `--uninstall` (test against a throwaway `XDG_CONFIG_HOME`)
- the configurator produces the expected result for each supported harness at repository and global scope (use `--dry-run`)
- every `SKILL.md` links directly to every owned reference
- every local Markdown link resolves
- every reference longer than 100 lines has a contents list near the top
- frontmatter contains only `name` and `description`
- every Codex default prompt names its skill
- no scaffold placeholders or trailing whitespace remain
- representative prompts activate the intended skills without loading unrelated domains
