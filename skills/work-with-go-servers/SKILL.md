---
name: work-with-go-servers
description: Guide Go production server composition. Use for design, implementation, debugging, testing, or review of internal/server, dependency construction or cleanup, handler mounting, deployment paths, listening, shutdown, or process lifecycle; exclude endpoint behavior.
---

# Work with Go Servers

Use this skill for the outer production boundary that turns resolved runtime configuration and ready packages into one running process. Inspect the whole composition path and load the references that match the work.

## Preserve the boundary

- Keep runtime configuration resolution outside `internal/server`; pass resolved values in explicitly.
- Open runtime dependencies before constructing the service and transport packages.
- Construct dependencies from the inside out and clean them up in the reverse ownership order.
- Mount package-owned API and web handlers as route trees without moving their endpoint behavior into the server.
- Apply deployment base paths outside reusable inner routers.
- Keep listen, shutdown, signal, cleanup, and process-lifetime coordination in the server or process runner.
- Keep command handlers thin: resolve runtime, invoke the server entry point, and report errors.

## Consult the knowledge base

1. Inspect the command entry point, resolved runtime, server package, constructed dependencies, mounted handlers, and relevant tests.
2. Identify whether the change affects serving shape, dependency ownership, composition roots, mounting, base paths, or shutdown.
3. Read every matching reference before editing or reviewing.
4. Follow effects into adjacent config, service, database, routing, API, web, and user domains.
5. Apply the guidance as a strong default while preserving coherent local conventions outside the requested scope.
6. Explain material deviations when the project's process model requires a different composition shape.

## Select references

- Read [serving-stack.md](references/serving-stack.md) whenever creating or changing `internal/server`, production dependency construction, route mounting, deployment base paths, listening, cleanup, or graceful shutdown.
- Read [composition-roots.md](references/composition-roots.md) when deciding where production or test dependencies are built, separating real and test wiring, or exposing a constructed handler independently from listening.

Read both references for most structural server changes. A new runtime dependency, HTTP surface, or lifecycle hook usually affects both the serving stack and its composition root.

## Include adjacent domains

- Consult [config guidance](../work-with-go-config/SKILL.md) for authored configuration, initialization, resource paths, and runtime resolution.
- Consult [service guidance](../work-with-go-services/SKILL.md) when construction, bootstrap work, or service lifecycle hooks change.
- Consult [database guidance](../work-with-go-databases/SKILL.md) for database opening, migration readiness, cleanup, or persistence behavior.
- Consult [routing guidance](../compose-go-http-routes/SKILL.md) for reusable inner route trees, middleware boundaries, and package-handler mounts.
- Consult [API guidance](../work-with-go-http-apis/SKILL.md) for JSON endpoint behavior and API-owned middleware.
- Consult [web UI guidance](../work-with-go-web-uis/SKILL.md) for rendered routes and browser behavior.
- Consult [Consent user guidance](../work-with-consent-users/SKILL.md) when the composition root constructs Consent clients or mounts authentication handlers.
- Consult [CLI guidance](../work-with-go-clis/SKILL.md) when a command resolves runtime and starts the server.

## Validate the result

- Prefer the repository's documented formatting, test, lint, and check commands.
- Test constructed handlers without a real listener when practical.
- Verify production mount paths, deployment base paths, and coexistence of every HTTP surface.
- Verify dependency cleanup and error propagation on partial construction failures.
- Exercise cancellation and graceful shutdown when process lifecycle changes.
- Keep endpoint-contract tests in their owning API or web packages.

## Keep the skill current

Update the narrowest reference when repeated server work exposes missing or stale guidance. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, or reference routing needs to change.
