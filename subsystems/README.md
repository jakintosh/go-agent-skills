# Subsystems

This directory is a brief index of the architectural guides used across the style system.

- [`api-tests.md`](./api-tests.md): This is the testing guide for API surfaces when you need the expected shape of handler- and route-level HTTP tests.

- [`app-view-models.md`](./app-view-models.md): This is the guide for shaping view models that sit between application logic and rendered UI.

- [`database-tests.md`](./database-tests.md): This is the testing guide for database adapters when you need the expected structure of persistence-focused tests.

- [`project-actions.md`](./project-actions.md): This is the guide for modeling project-scoped actions and the boundaries around how they execute.

- [`public-packages.md`](./public-packages.md): This is the guide for deciding what belongs in public packages and how exported package surfaces should read.

- [`server-rendered-htmx-ui.md`](./server-rendered-htmx-ui.md): This is the guide for building server-rendered HTMX interfaces and their application boundaries.

- [`api-handlers/README.md`](./api-handlers/README.md): Use the API handlers family for JSON HTTP endpoint structure, keeping request parsing, service calls, and HTTP responses in the right place.
  - [`api-handlers/error-mapping.md`](./api-handlers/error-mapping.md): Read this when several handlers need the same service-to-HTTP error translation rules.

- [`cli/README.md`](./cli/README.md): Use the CLI family for command-tree structure, especially when a binary exposes multiple operational surfaces.
  - [`cli/with-config.md`](./cli/with-config.md): Read this when CLI commands need root path flags, runtime config loading, or a `config` command subtree.
  - [`cli/integrating-envs.md`](./cli/integrating-envs.md): Read this when environment variables need to be surfaced cleanly through the command interface.
  - [`cli/integrating-version.md`](./cli/integrating-version.md): Read this when a binary needs a standard version constant and version-reporting behavior.

- [`config/README.md`](./config/README.md): Use the config family for applications that own authored config, resolved runtime state, secret loading, and config-backed resources.
  - [`config/runtime-resolution.md`](./config/runtime-resolution.md): Read this when defining merge precedence, derived paths, and the single runtime resolution flow.
  - [`config/initialization.md`](./config/initialization.md): Read this when implementing `config init` and other generated config bootstrap behavior.
  - [`config/resources.md`](./config/resources.md): Read this when the config directory owns file-backed resource families such as themes or templates.

- [`database/README.md`](./database/README.md): Use the database family for SQL adapter structure, connection setup, migrations, and persistence mechanics.
  - [`database/migrations.md`](./database/migrations.md): Read this for the default migration shape and ordered schema-change workflow.
  - [`database/migrations-with-go.md`](./database/migrations-with-go.md): Read this when a migration needs procedural Go code instead of only SQL strings.
  - [`database/query-methods.md`](./database/query-methods.md): Read this when implementing ordinary adapter read and write methods.
  - [`database/transactions.md`](./database/transactions.md): Read this when one persistence operation needs transactional coordination across several statements.

- [`routing/README.md`](./routing/README.md): Use the routing family for composing one HTTP route tree from smaller mountable route groups.
  - [`routing/deployment-mounting.md`](./routing/deployment-mounting.md): Read this when routes need to live under a deployment base path or separate serving layer.
  - [`routing/middleware-boundaries.md`](./routing/middleware-boundaries.md): Read this when deciding where auth, CORS, or similar middleware should wrap a subtree.
  - [`routing/mounting-package-handlers.md`](./routing/mounting-package-handlers.md): Read this when an existing package already exposes a handler that should be mounted directly.

- [`service/README.md`](./service/README.md): Use the service family for the core `internal/service` package, constructor shape, dependency boundaries, and router ownership.
  - [`service/bootstrap-initialization.md`](./service/bootstrap-initialization.md): Read this when startup must explicitly initialize durable application state.
  - [`service/composition-roots.md`](./service/composition-roots.md): Read this when production wiring and test wiring need separate composition roots.
  - [`service/lifecycle-hooks.md`](./service/lifecycle-hooks.md): Read this when the service owns long-lived background work or coordinated startup and shutdown hooks.
  - [`service/serving.md`](./service/serving.md): Read this when the service also owns HTTP serving behavior such as listen, shutdown, or base-path mounting.

- [`store/README.md`](./store/README.md): Use the store family for the service-owned persistence contract between domain code and adapters.
  - [`store/with-database.md`](./store/with-database.md): Read this when implementing those store contracts inside `internal/database`.
