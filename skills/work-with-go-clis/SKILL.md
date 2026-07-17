---
name: work-with-go-clis
description: Guide Go command-line interfaces. Use for design, implementation, debugging, testing, or review of command trees, commands and options, command-go handlers, API clients, named environments, config wiring, version metadata, or cmd files.
---

# Work with Go CLIs

Use this skill as a CLI-domain knowledge layer for both new commands and ongoing changes. Inspect the requested work, preserve the user-facing contract unless a redesign is explicit, and load only the references that cover the affected concerns.

## Preserve the boundary and contract

- Treat commands, operands, options, output, and exit behavior as a public interface.
- Keep one root command and represent reusable branches and leaves as named command values.
- Put shared options at the highest command where they are semantically valid; keep invocation-specific overrides on the command that consumes them.
- Keep handlers as adapters: extract and validate input, resolve dependencies, invoke one operation, and format output.
- Keep business policy, persistence construction, HTTP serving composition, and configuration precedence in their owning domains.
- Prefer the established `command-go` helpers for parsing, environments, API transport, and version metadata over local reimplementations.
- Preserve coherent local conventions when modifying an existing CLI unless they violate a boundary or the task explicitly requests migration.

## Consult the knowledge base

1. Inspect `cmd/`, relevant internal packages, CLI tests, `go.mod`, and build files before choosing references.
2. Read [command-trees.md](references/command-trees.md) for every CLI task; it defines the baseline tree and handler shape.
3. Classify all additional concerns exposed by the prompt and the existing implementation.
4. Read each matching reference before editing or reaching a review conclusion.
5. Re-evaluate the selection when implementation reveals config, client, environment, or generation implications not obvious from the prompt.
6. Apply the guidance as a strong default and explain material deviations required by the repository or task.

## Select additional references

- Read [calling-api.md](references/calling-api.md) when a command calls a JSON HTTP API, builds a `wire.Client`, marshals request DTOs, interprets HTTP errors, or prints API responses.
- Read [named-environments.md](references/named-environments.md) when a CLI uses `command-go/pkg/envs`, persists named endpoints or credentials, resolves client context, or exposes an `env` subtree.
- Read [config-integration.md](references/config-integration.md) when root path flags, a `config` subtree, runtime resolution, config initialization, or serve-command config wiring changes.
- Read [version-metadata.md](references/version-metadata.md) when adding or changing generated version data, the `version` command, root version metadata, or build-time generation.

Read multiple references when concerns overlap. An API command backed by named environments normally requires command trees, API calling, and named environments. A generated version command that changes the build workflow also requires the version reference and adjacent Makefile guidance.

## Include adjacent domains

- Consult [Go config guidance](../work-with-go-config/SKILL.md) when authored config schema, resolution precedence, resources, secrets, or initialization behavior changes; this skill owns only the CLI adapter to that domain.
- Consult [Go HTTP API guidance](../work-with-go-http-apis/SKILL.md) when the server-side HTTP contract, DTOs, error mapping, keys, or CORS behavior changes.
- Consult [Go server guidance](../work-with-go-servers/SKILL.md) when `serve` changes dependency composition, lifecycle ownership, listener behavior, or shutdown.
- Consult [Go service guidance](../work-with-go-services/SKILL.md) when a command changes service contracts, business operations, store ownership, or mutable application bootstrap.
- Consult [Go Makefile guidance](../work-with-go-makefiles/SKILL.md) when CLI generation, build, install, init, or run behavior changes project targets.
- Consult [public package guidance](../design-go-public-packages/SKILL.md) when a reusable API client or other CLI-supporting library changes its external Go contract.

Do not copy adjacent-domain rules into this skill. Consult the adjacent skill and keep only CLI-facing integration here.

## Validate the result

- Run the repository's documented formatting, test, lint, generate, and check commands in proportion to the change.
- Exercise command composition and parsing in process where possible.
- Cover representative help, input validation, inherited options, output, and error behavior.
- For API commands, verify client resolution, request paths and payloads, status-specific errors, and secret-safe diagnostics.
- For config or environment changes, verify the documented precedence and file-permission behavior through the owning domain's tests.
- For version changes, run generation and verify both ordinary and verbose output from a build with the expected git metadata.
- For reviews, report behavioral and boundary risks rather than harmless syntax variation.

## Keep the skill current

When repeated CLI work exposes a missing rule, stale API, or unclear branch, update the narrowest matching reference. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, adjacent routing, or reference selection needs to change.
