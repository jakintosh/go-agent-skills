# Contributing

This document defines how to maintain the Pollinator Style plugin and its domain skills.

## Repository structure

```text
.codex-plugin/
  plugin.json
skills/
  <domain-skill>/
    SKILL.md
    agents/openai.yaml
    references/
```

- [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) defines the installable plugin and discovers `skills/`.
- [`skills/`](skills/) contains the setup skill, domain skills, and selectively loaded knowledge.
- Each domain skill owns its detailed guidance. Do not duplicate the same rule or example across skills.

[`configure-pollinator-style`](skills/configure-pollinator-style/SKILL.md) is an operational setup skill. It owns the managed `AGENTS.md` block and the completion message shown after configuration. Keep its router text, script behavior, README onboarding, and result vocabulary synchronized.

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

Every skill should include `agents/openai.yaml` with:

- a human-readable display name
- a 25–64 character short description
- a short default prompt that explicitly names the skill with `$skill-name`

Enable implicit invocation by default. Add scripts, assets, or tool dependencies only when the skill uses them.

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

- every `SKILL.md` links directly to every owned reference
- every local Markdown link resolves
- every reference longer than 100 lines has a contents list near the top
- frontmatter contains only `name` and `description`
- every default prompt names its skill
- no scaffold placeholders or trailing whitespace remain
- representative prompts activate the intended skills without loading unrelated domains
