# Subsystems

This directory is a brief index of the architectural guides used across the style system.

- [`public-packages.md`](./public-packages.md): This is the guide for deciding what belongs in public packages and how exported package surfaces should read.

- [`api/README.md`](./api/README.md): Use the API family for JSON HTTP endpoint structure, API DTOs, route composition, service calls, and HTTP responses.
  - [`api/error-mapping.md`](./api/error-mapping.md): Read this when handlers need consistent service-to-HTTP error translation rules.
  - [`api/testing.md`](./api/testing.md): Read this when testing API route wiring, middleware, request decoding, response DTOs, or status behavior in-process.
  - [`api/with-keys.md`](./api/with-keys.md): Read this when an API uses `command-go/pkg/keys` for API-key auth or key management.
  - [`api/with-cors.md`](./api/with-cors.md): Read this when an API uses `command-go/pkg/cors` for dynamic CORS origin management.

- [`cli/README.md`](./cli/README.md): Use the CLI family for command-tree structure, especially when a binary exposes multiple operational surfaces.
  - [`cli/with-config.md`](./cli/with-config.md): Read this when CLI commands need root path flags, runtime config loading, or a `config` command subtree.
  - [`cli/integrating-envs.md`](./cli/integrating-envs.md): Read this when environment variables need to be surfaced cleanly through the command interface.
  - [`cli/integrating-version.md`](./cli/integrating-version.md): Read this when a binary needs a standard version constant and version-reporting behavior.
  - [`cli/calling-api.md`](./cli/calling-api.md): Read this when CLI commands call a JSON HTTP API with `wire.Client`.

- [`config/README.md`](./config/README.md): Use the config family for applications that own authored config, resolved runtime state, secret loading, and config-backed resources.
  - [`config/runtime-resolution.md`](./config/runtime-resolution.md): Read this when defining merge precedence, derived paths, and the single runtime resolution flow.
  - [`config/initialization.md`](./config/initialization.md): Read this when implementing `config init` and other generated config bootstrap behavior.
  - [`config/resources.md`](./config/resources.md): Read this when the config directory owns file-backed resource families such as themes or templates.

- [`database/README.md`](./database/README.md): Use the database family for SQL adapter structure, connection setup, migrations, and persistence mechanics.
  - [`database/migrations.md`](./database/migrations.md): Read this for the default migration shape and ordered schema-change workflow.
  - [`database/migrations-with-go.md`](./database/migrations-with-go.md): Read this when a migration needs procedural Go code instead of only SQL strings.
  - [`database/query-methods.md`](./database/query-methods.md): Read this when implementing ordinary adapter read and write methods.
  - [`database/testing.md`](./database/testing.md): Read this when testing database adapter behavior, open behavior, migrations, transactions, or persistence invariants.
  - [`database/transactions.md`](./database/transactions.md): Read this when one persistence operation needs transactional coordination across several statements.

- [`makefiles/README.md`](./makefiles/README.md): Use this guide when creating or reviewing a project's `Makefile`.

- [`routing/README.md`](./routing/README.md): Use the routing family for composing one HTTP route tree from smaller mountable route groups.
  - [`routing/middleware-boundaries.md`](./routing/middleware-boundaries.md): Read this when deciding where auth, CORS, or similar middleware should wrap a subtree.
  - [`routing/mounting-package-handlers.md`](./routing/mounting-package-handlers.md): Read this when an existing package already exposes a handler that should be mounted directly.

- [`server/README.md`](./server/README.md): Use the server family for production serving composition, dependency opening, route-tree mounting, listen behavior, and deployment base paths.
  - [`server/composition-roots.md`](./server/composition-roots.md): Read this when production wiring and test wiring need separate composition roots.

- [`service/README.md`](./service/README.md): Use the service family for the core `internal/service` package, constructor shape, domain behavior, store contracts, and dependency boundaries.
  - [`service/bootstrap-initialization.md`](./service/bootstrap-initialization.md): Read this when startup must explicitly initialize durable application state.
  - [`service/lifecycle-hooks.md`](./service/lifecycle-hooks.md): Read this when the service owns long-lived background work or coordinated startup and shutdown hooks.

- [`store/README.md`](./store/README.md): Use the store family for the service-owned persistence contract between domain code and adapters.
  - [`store/with-database.md`](./store/with-database.md): Read this when implementing those store contracts inside `internal/database`.

- [`users/README.md`](./users/README.md): Use this guide when a server application needs Consent-backed login, local account records, account-scoped domain data, or user-aware `internal/web` routes.

- [`web/README.md`](./web/README.md): Use the web family for server-rendered browser interfaces, HTMX progressive enhancement, renderer/template boundaries, view models, forms, mutations, flash messages, static assets, and focused UI tests.
  - [`web/view-models.md`](./web/view-models.md): Read this when shaping display-ready data for `html/template`.
  - [`web/htmx-request-flow.md`](./web/htmx-request-flow.md): Read this when implementing full-page and fragment response behavior.
  - [`web/renderer-and-templates.md`](./web/renderer-and-templates.md): Read this when defining renderer methods, named templates, fragments, and stable swap targets.
  - [`web/forms-and-mutations.md`](./web/forms-and-mutations.md): Read this when implementing form validation, create/update/delete flows, redirects, HTMX mutation responses, or flash messages.
  - [`web/testing.md`](./web/testing.md): Read this when testing web handlers, render-path parity, view models, fragments, and form responses.
  - [`web/static-assets.md`](./web/static-assets.md): Read this when adding plain CSS, small enhancement JavaScript, or static file serving.
