---
name: work-with-go-config
description: Guide Go configuration systems. Use for design, implementation, debugging, testing, or review of authored config, runtime resolution, paths, defaults, precedence, secrets, initialization, resources, or internal/config.
---

# Work with Go Config

Use this skill as the configuration-domain knowledge layer for both initial system design and later modifications. Inspect the full resolution path, select the references that match every affected concern, and keep configuration ownership centralized.

## Preserve the boundary

- Keep `internal/config` as the single owner of authored configuration and runtime resolution behavior.
- Keep authored `Config` separate from resolved `Runtime`.
- Derive one centralized `Paths` value from the independently resolved config and data roots.
- Make `Resolve(...)` the only merge point for defaults, files, environment, CLI overrides, secrets, resources, and runtime-only values.
- Load authored data strictly, validate after merges, and keep secrets out of the main config file.
- Expose redacted resolved inspection data rather than secret values.
- Make generated writes non-destructive by default and destructive resource operations explicit.
- Pass resolved runtime values outward; do not let commands, services, or servers reopen config sources or invent secondary precedence.

## Consult the knowledge base

1. Inspect `internal/config`, its callers, tests, root path flags, environment names, and config/data filesystem layout.
2. Read [config-subsystem.md](references/config-subsystem.md) for every config task; it defines the subsystem ownership and baseline flow.
3. Identify every affected phase: authored loading, path resolution, precedence, secrets, resources, initialization, inspection, and downstream consumption.
4. Read each matching reference before editing or reaching a review conclusion.
5. Re-evaluate the selection when implementation reveals another source, write path, secret, or resource dependency.
6. Apply the guidance as a strong default and explain material deviations required by coherent repository constraints.

## Select additional references

- Read [runtime-resolution.md](references/runtime-resolution.md) whenever changing `Load(...)`, `Resolve(...)`, defaults, root paths, precedence, strict decoding, secret loading, runtime derivation, or resolved inspection.
- Read [initialization.md](references/initialization.md) whenever changing `config init`, generated baseline material, directory creation, force behavior, secret generation, or initialization result reporting.
- Read [config-backed-resources.md](references/config-backed-resources.md) whenever adding, modifying, loading, listing, creating, showing, or deleting a file-backed resource family such as themes, templates, providers, policies, or environments.

Read multiple references when concerns overlap. A new required resource commonly changes resource helpers, runtime resolution, config initialization, and tests.

## Include adjacent domains

- Consult [Go CLI guidance](../work-with-go-clis/SKILL.md) when root flags, `config` commands, inspection output, or runtime command wiring changes; config owns semantics and the CLI owns adaptation.
- Consult [Go server guidance](../work-with-go-servers/SKILL.md) when resolved runtime values change dependency composition, listeners, lifecycle behavior, or serving configuration.
- Consult [Go service guidance](../work-with-go-services/SKILL.md) when mutable application bootstrap or service construction changes; keep top-level operational `init` separate from `config init`.
- Consult [Go database guidance](../work-with-go-databases/SKILL.md) when database paths, opening options, migration behavior, or durable state semantics change; config may carry resolved values but does not own persistence behavior.
- Consult [Go Makefile guidance](../work-with-go-makefiles/SKILL.md) when local config/data inputs, initialization, reset, or run targets change.
- Consult [Consent user guidance](../work-with-consent-users/SKILL.md) when Consent URLs, integration names, public origins, modes, verification keys, or deployment inputs change.

Do not duplicate adjacent-domain policy in config. Resolve and expose the needed values, then let the owning domain consume them.

## Validate the result

- Run the repository's documented formatting, test, lint, and check commands in proportion to the change.
- Test every affected precedence layer, including unset, malformed, and conflicting inputs.
- Test strict decoding, validation after merges, path derivation, home expansion where supported, and missing-file behavior.
- Verify secret source ordering, file permissions, and redaction in all inspection and diagnostic output.
- Verify initialization is safe on first and repeated runs, including explicit force behavior and partial failures.
- For resource families, test invalid names, filename collisions, deterministic listing, strict decoding, non-destructive defaults, and runtime loading.
- Exercise downstream callers enough to prove they consume `Runtime` without reopening or re-resolving sources.
- For reviews, report precedence, secret-exposure, filesystem-safety, and ownership risks concretely.

## Keep the skill current

When repeated config work exposes a missing rule, stale example, or unclear branch, update the narrowest matching reference. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, adjacent routing, or reference selection needs to change.
