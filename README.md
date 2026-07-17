# Pollinator Style

Pollinator Style is a plugin for agentic coding harnesses containing Studio Pollinator's opinionated Go engineering guidance.

The plugin uses progressive disclosure so ordinary design, implementation, debugging, testing, and review tasks can draw on detailed guidance without loading the entire knowledge base. Skill metadata identifies relevant domains, each `SKILL.md` selects the applicable concerns, and focused references supply detailed rules and examples only when needed.

## Supported harnesses

The knowledge base is a set of harness-agnostic skills. Each supported harness discovers them through its own manifest and, when configured, routes to them through its own guidance file.

| Harness | Manifest | Guidance file |
| --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json` | `CLAUDE.md` |
| Codex | `.codex-plugin/plugin.json` | `AGENTS.md` |

Support for additional harnesses is added by contributing another manifest and a configurator branch; see [`CONTRIBUTING.md`](CONTRIBUTING.md). Everything under `skills/` is shared across harnesses unchanged.

## Repository structure

```text
.claude-plugin/
  plugin.json
  marketplace.json
.codex-plugin/
  plugin.json
skills/
  configure-pollinator-style/
    SKILL.md
    agents/openai.yaml
    scripts/
  <domain-skill>/
    SKILL.md
    agents/openai.yaml
    references/
```

Each harness's manifest discovers every skill under `skills/`. Domain knowledge lives in the narrowest reference that owns the concern, while `SKILL.md` files contain activation boundaries, universal invariants, reference routing, adjacent-domain routing, and validation behavior. Per-skill `agents/openai.yaml` files carry Codex interface metadata and are ignored by harnesses that do not use them.

## Skill catalog

| Skill | Domain |
| --- | --- |
| [`work-with-go-services`](skills/work-with-go-services/SKILL.md) | Domain behavior, service construction, errors, permissions, service-owned stores, bootstrap, and lifecycle hooks |
| [`work-with-go-databases`](skills/work-with-go-databases/SKILL.md) | SQL adapters, migrations, queries, scans, transactions, durable constraints, and persistence tests |
| [`work-with-go-http-apis`](skills/work-with-go-http-apis/SKILL.md) | JSON HTTP contracts, DTOs, handlers, error mapping, API tests, keys, and CORS |
| [`compose-go-http-routes`](skills/compose-go-http-routes/SKILL.md) | Route-tree composition, package-handler mounting, and middleware boundaries |
| [`work-with-go-servers`](skills/work-with-go-servers/SKILL.md) | Production dependency composition, mounting, listening, cleanup, and graceful shutdown |
| [`work-with-go-clis`](skills/work-with-go-clis/SKILL.md) | Command trees, config wiring, named environments, version metadata, and API clients |
| [`work-with-go-config`](skills/work-with-go-config/SKILL.md) | Authored config, runtime resolution, initialization, secrets, paths, and config-backed resources |
| [`work-with-go-web-uis`](skills/work-with-go-web-uis/SKILL.md) | Server-rendered HTML, templates, view models, HTMX, forms, static assets, and web tests |
| [`work-with-consent-users`](skills/work-with-consent-users/SKILL.md) | Consent integration, local accounts, account resolution, CSRF, local testing, and deployment |
| [`design-go-public-packages`](skills/design-go-public-packages/SKILL.md) | Deliberate `pkg/` APIs, exported compatibility surfaces, package docs, and external reuse |
| [`work-with-go-makefiles`](skills/work-with-go-makefiles/SKILL.md) | Go project Makefile targets, workflows, variables, cleanup, and help output |

[`configure-pollinator-style`](skills/configure-pollinator-style/SKILL.md) manages persistent ambient routing in a harness's guidance file.

## Configure ambient routing

After installing and enabling the plugin, configure the current repository by asking your agent:

> Configure this repository for Pollinator Style.

The setup skill runs for the harness you are using, discovers that harness's active guidance file, preserves its existing content, and manages one marked Pollinator Style block. The block tells the agent to inspect the code, select every materially affected skill from its description, load only relevant references, and reconsider selection as scope emerges.

Repository scope is the default. For global behavior, ask explicitly:

> Configure Pollinator Style for my global agent guidance.

To remove the managed block while preserving other instructions:

> Remove Pollinator Style routing from this repository.

The configurator reports the harness, the guidance file, whether it changed, the resulting action, and a short explanation of implicit routing. Start a new session in that harness whenever the guidance file changes.

## Contributing

Add knowledge to the narrowest reference that owns the concern. Change `SKILL.md` when activation, universal invariants, consultation behavior, adjacent-domain routing, or reference selection changes. Create a new skill only for a stable domain that should activate independently.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for skill structure, writing conventions, and validation requirements.
