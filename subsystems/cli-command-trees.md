# CLI Command Trees

This guide defines the standard shape for CLI command trees in this style system.

It focuses on how commands are organized, where environment and config concerns live, and how handlers should read when a binary exposes several operational surfaces.

The goal is to make the CLI:

- easy to scan
- easy to extend without nested command sprawl
- consistent about config and environment resolution
- aligned with the service and API surface it controls

## When to use this guide

Use this guide when you are:

- creating the initial command tree for a Go binary
- adding a new top-level command or resource subtree
- deciding where config, environment, and credential concerns belong
- restructuring a CLI that has grown through ad hoc inline nesting

## Non-goals

This guide does not define:

- the internals of the config subsystem
- service construction and dependency wiring details
- HTTP router composition
- shell automation such as `make` targets

## Core rules

- Use one root command in `cmd/<bin>/main.go`.
- Define `HelpOption` with short `-h` and long `--help`.
- Treat environment and config integration as a root-level concern.
- Define each `args.Command` as a named global variable.
- Include subcommands by name rather than inline nesting.
- Split command files by concern so engineers can find command surfaces quickly.
- Keep command handlers inline on the command definition.
- Structure command handlers by phases: extract inputs, validate inputs, set up dependencies, execute, format output.
- Add a top-level `init` command when the application has explicit mutable bootstrap work.
- Keep `config` as its own subtree when the application has a real config subsystem.
- Align CLI resource trees with API resource paths when that keeps the system easier to learn.
- Commands should largely be an "interface": parsing user input from the command line, normalizing/structuring it, calling service functions, and formatting results back to expected CLI text. "Business logic" should not be present in cli command handlers, and this should suggest that new functionality is needed in the domain.

## Canonical shape

The expected package layout is:

```text
cmd/<bin>/
  main.go
  serve.go
  init.go
  config.go
  api.go
  <resource>.go
```

The boundary matters more than the exact filenames:

- `main.go` owns the root command and shared helpers
- top-level command files own one subtree each
- resource files own one coherent command family

## Root command responsibilities

The root command should define the binary's shared environment shape.

That usually includes:

- `HelpOption`
- version command integration
- root path options such as `--config-dir` and `--data-dir`
- environment/config integration through `envs.Command(...)`
- named top-level subcommands

A typical root shape looks like:

```go
var RootCmd = &args.Command{
	Name: "themesvc",
	HelpOption: args.Option{
		Name:  "help",
		Short: 'h',
	},
	Subcommands: []*args.Command{
		version.Command,
		envs.Command(DefaultEnvConfig, keys.NewEnvKeyBackend("/api/v1/settings")),
		ServeCmd,
		InitCmd,
		ConfigCmd,
		APICmd,
	},
}
```

The important idea is that the root defines shared execution context once. Do not scatter environment/config registration across unrelated subcommands.

## Named command variables

Define commands as package-level named variables:

```go
var ServeCmd = &args.Command{
	Name: "serve",
	Handler: func(inv *args.Invocation) error {
		// ...
		return nil
	},
}
```

Prefer this over factory functions that build commands on demand.

Why this shape works:

- the command tree is visible at a glance
- subcommands can be composed by name
- command structure stays declarative instead of being hidden in setup logic

## Handler flow

CLI handlers should read in obvious phases.

The default order is:

1. extract inputs
2. validate and normalize
3. set up dependencies
4. execute the operation
5. format output

For example:

```go
var CreateThemeCmd = &args.Command{
	Name: "create",
	Handler: func(inv *args.Invocation) error {
		name := inv.Arg("name")
		configDir := resolveOption(inv, "config-dir", "THEMESVC_CONFIG_DIR", defaultConfigDir())

		if name == "" {
			return errors.New("name is required")
		}

		runtime, err := config.Resolve(config.Options{
			ConfigDir: configDir,
		})
		if err != nil {
			return err
		}

		if err := runtime.ThemeStore.Create(name); err != nil {
			return err
		}

		return wire.WriteJSON(inv.Stdout, map[string]string{
			"name": name,
		})
	},
}
```

Do not interleave parsing, validation, setup, and execution in a long chain. The reader should be able to scan the handler from top to bottom and see the operational flow immediately.

## Command tree design

A good command tree should make the operational surface obvious.

Typical top-level commands include:

- `serve`
- `init`
- `config`
- `api`

Use `serve` and `api` together when the binary deliberately exposes both server and client roles.

Use a `config` subtree when the application has:

- authored config on disk
- resolved runtime inspection
- config-backed resource management

Use a top-level `init` command when the application has mutable bootstrap work such as:

- database initialization
- schema setup
- explicit key bootstrap
- durable seed state

Keep `config init` and top-level `init` separate. The first creates files and local config material. The second mutates operational state.

## Resource subtrees

When the CLI manages resource families, give each family a stable subtree.

For example:

```text
themesvc api themes list
themesvc api themes create
themesvc api themes delete
```

This works best when the CLI shape mirrors the service's resource vocabulary and, when reasonable, the HTTP resource paths as well.

Do not hide a whole resource family behind one giant command with mode flags.

## Small helpers

Small helpers are useful for repeated mechanics such as:

- option/env/default precedence
- loading credentials from a directory
- writing JSON output
- building shared client parameters

Keep these helpers narrow and mechanical.

They should remove boilerplate, not hide the command's intent.

## Testing expectations

CLI command structure should make it easy to test:

- root command composition
- option/env/default precedence
- command-local validation
- config/environment integration
- command output for representative success and failure cases
- explicit init behavior, including idempotent repeated runs

Prefer tests that exercise commands in-process with explicit input values rather than shelling out to a built binary for default coverage.

## Anti-patterns

- multiple root commands spread across files
- factory functions that build the whole command tree dynamically
- inline nested anonymous subcommands that hide structure
- repeating config-dir or data-dir resolution separately in many commands
- mixing input extraction and execution in dense expressions
- using `config init` to mutate runtime state
- putting unrelated resource families into one broad catch-all command

## Generic example

```text
docsvc
  serve
  init
  config
    init
    show
    show --resolved
    templates
      list
      create
      delete
  api
    documents
      list
      get
      create
      delete
```

This shape gives a reader quick answers to:

- how the service starts
- how local config is created
- how mutable runtime state is initialized
- how config-backed resources are managed
- how client-style operations are organized

## Related guides

- `config-systems.md`
- `service-construction.md`
- `http-router-composition.md`
