# Pollinator Style

Pollinator Style is a plugin for agentic coding harnesses containing Studio Pollinator's opinionated Go engineering guidance.

The plugin uses progressive disclosure so ordinary design, implementation, debugging, testing, and review tasks can draw on detailed guidance without loading the entire knowledge base. Skill metadata identifies relevant domains, each `SKILL.md` selects the applicable concerns, and focused references supply detailed rules and examples only when needed.

## Supported harnesses

The knowledge base is a set of harness-agnostic skills. Each supported harness discovers them through its own install mechanism and, when configured, routes to them through its own guidance file.

| Harness | Skills installed via | Guidance file |
| --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json` manifest | `CLAUDE.md` |
| Codex | `.codex-plugin/plugin.json` manifest | `AGENTS.md` |
| OpenCode | [`install_opencode.sh`](install_opencode.sh) | `AGENTS.md` |

Support for additional harnesses is added by contributing another install mechanism and a configurator branch; see [`CONTRIBUTING.md`](CONTRIBUTING.md). Everything under `skills/` is shared across harnesses unchanged.

### Install for OpenCode

OpenCode has no plugin manifest, so it discovers skills by directory. Clone this repository and run the install script to copy the skills into OpenCode's user skill directory:

```sh
git clone https://git.studiopollinator.com/pollinator/style.git
cd style
./install_opencode.sh
```

Start a new OpenCode session and the skills are available in every project. Re-run `./install_opencode.sh` after `git pull` to update, or `./install_opencode.sh --uninstall` to remove them. Then enable ambient routing as described below.

## Repository structure

```text
.claude-plugin/
  plugin.json
.codex-plugin/
  plugin.json
install_opencode.sh
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

Every harness draws on the same skills under `skills/`: Claude Code and Codex discover them through their manifests, and OpenCode installs copies with `install_opencode.sh`. Domain knowledge lives in the narrowest reference that owns the concern, while `SKILL.md` files contain activation boundaries, universal invariants, reference routing, adjacent-domain routing, and validation behavior. Per-skill `agents/openai.yaml` files carry Codex interface metadata and are ignored by harnesses that do not use them.

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
