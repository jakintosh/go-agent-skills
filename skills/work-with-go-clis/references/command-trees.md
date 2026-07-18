# Building a CLI Command Tree

**Package:** `git.sr.ht/~jakintosh/command-go/pkg/args`

This guide defines the standard shape for CLI command trees in the Studio Pollinator style system, using the `git.sr.ht/~jakintosh/command-go/pkg/args` package.

Use the latest compatible release of `git.sr.ht/~jakintosh/command-go` when starting or updating a project:

```sh
go get git.sr.ht/~jakintosh/command-go@latest
```

The examples intentionally omit a module version so readers do not copy a stale pin from the guide. Let the project's `go.mod` record the selected version.

It focuses on how commands are organized, where environment and config concerns live, and how handlers should read when a binary exposes several operational surfaces.

The goal is to make the CLI:

- easy to scan, easy to extend
- consistent about config and environment resolution
- aligned with the service, API, and server surfaces it controls

## Contents

- [Package layout](#package-layout)
- [Defining a tree root](#defining-a-tree-root)
- [Defining subcommands](#defining-subcommands)
- [Option and operand style](#option-and-operand-style)
- [Extending or refactoring an existing CLI](#extending-or-refactoring-an-existing-cli)
- [Command tree design](#command-tree-design)
- [API resource subtrees](#api-resource-subtrees)
- [Small helpers](#small-helpers)
- [Testing expectations](#testing-expectations)

## Package layout

The expected package layout is:

```
cmd/<bin>/
  main.go
  subcmd1.go
  subcmd2.go
  subcmd3.go
```

- `main.go` owns the root command and shared helpers
- Top-level command files own one subtree each
- Define the root and every reusable subtree as package-level `var` values
- Wire subcommands by reference rather than by large inline literals

## Defining a tree root

- Build and parse one root command in `cmd/<bin>/main.go`
- Define `HelpOption` with short `-h` and long `--help`
- Define each `&args.Command` as a named global variable
- Include subcommands by name reference rather than inline nesting
- Define any root-level options such as `--config-dir` or `--data-dir`

```go
import "git.sr.ht/~jakintosh/command-go/pkg/args"

const (
	BIN_NAME = "<bin>"
	AUTHOR = "<author>"
	VERSION = "<version>"
)

var root = &args.Command{
	Name: BIN_NAME,
	Config: &args.Config{
		Author:  AUTHOR,
		Version: VERSION,
		HelpOption: &args.HelpOption{
			Short: 'h',
			Long:  "help",
		},
	},
	Help: "<description>",
	Options: []args.Option{
		{
			Long: "config-dir",
			Type: args.OptionTypeParameter,
			Help: "path to config directory",
		},
	},
	Subcommands: []*args.Command{
		apiCmd,
		initCmd,
		serveCmd,
		statusCmd,
	},
}

func main() {
	root.Parse()
}
```

## Defining subcommands

- Define subcommands as package-level named variables
- Define all necessary inputs as "Operand"
- Define all optional inputs as "Options"
  - `OptionTypeParameter`: options with associated values
  - `OptionTypeArray`: options with multiple associated values
  - `OptionTypeFlag`: options that are boolean (true/false)
- Use branch commands to group workflows and leaf commands to execute behavior
- Put shared options at the highest command where they make semantic sense
- Define operands and options inline; avoid extracting argument slices into intermediate variables
- Keep command handlers inline on the command definition unless the handler is large enough to obscure the tree
- Handlers should not contain any business logic, and should only convert CLI context into config, server, client, or core domain service calls
- Use `input.GetOperand(<name>)` to parse mandatory operand values
- Use the most relevant option parser:
  - `GetParameter()/GetIntParameter()`: gets string/int value or `nil` if not found
  - `GetParameterOr()/GetIntParameterOr()`: gets string/int value or a default value if not found
  - `GetFlag()/GetFlagCount()`: get the presence of a flag, or the total time a flag was used
  - `GetArray()`/`GetIntArray()`: get all values for an array
- Remember that options declared on parent commands are available to all descendants
- Treat parser validation as already complete when the handler runs
- Structure command handlers by phases:
	1. Extract inputs
	2. Validate inputs
	3. Set up dependencies
	4. Execute
	5. Format output

A full subcommand example:
```go
var widgetCmd = &args.Command{
	Name: "widget",
	Help: "process widgets",
	Operands: []args.Operand{
		{
			Name: "name",
			Help: "widget name",
		},
	},
	Options: []args.Option{
		{
			Long: "date",
			Type: args.OptionTypeParameter,
			Help: "date widget created",
		},
		{
			Long: "tags",
			Type: args.OptionTypeArray,
			Help: "widget tags",
		},
		{
			Long: "stocked",
			Type: args.OptionTypeFlag,
			Help: "is widget in stock",
		},
		{
			Long: "count",
			Type: args.OptionTypeParameter,
			Help: "widget count",
		},
	},
	Handler: func(i *args.Input) error {

		// parse inputs
		name := i.GetOperand("name")
		dateStr := i.GetParameterOr("date", "1999-12-31")
		count := i.GetIntParameterOr("count", 0)

		// validate inputs
		date, err := parseDateStr(dateStr)
		if err != nil {
			return fmt.Errorf("invalid date: %w", err)
		}

		// set up service
		svcOpts := service.Options{
			Name: name,
		}
		svc, err := service.New(svcOpts)
		if err != nil {
			return err
		}

		// execute
		result, err := svc.Do(date, count)
		if err != nil {
			return err
		}

		// format output
		fmt.Printf("output: %v", result)
		return nil
	},
}
```

## Option and operand style

Use operands for required ordered values that read naturally by position:

```text
<bin> import <source> <destination>
<bin> api user get <id>
```

Use options for optional values, toggles, repeated inputs, and values whose meaning is clearer when named:

```go
Options: []args.Option{
	{
		Short: 'v',
		Long:  "verbose",
		Type:  args.OptionTypeFlag,
		Help:  "increase log verbosity",
	},
	{
		Long: "timeout",
		Type: args.OptionTypeParameter,
		Help: "request timeout in seconds",
	},
	{
		Long: "tag",
		Type: args.OptionTypeArray,
		Help: "resource tag",
	},
}
```

The `args` parser supports long options with separate or equals values, grouped short flags, repeated flags, repeated arrays, and `--` to stop option parsing. Do not reimplement these mechanics in handlers.

## Extending or refactoring an existing CLI

When adding to an existing command tree, preserve the established user-facing shape unless there is an explicit product reason to change it.

- Keep existing command names, option names, operands, output formats, and exit behavior stable
- Add new leaves or branches by defining named commands and wiring them into the nearest existing parent
- Move options upward only when the option is genuinely shared by the full subtree
- Convert ad hoc `flag` or `os.Args` parsing into operands, options, and handlers without changing caller-visible behavior

This keeps refactors from becoming accidental CLI redesigns.

## Command tree design

A good command tree should make the operational surface obvious.

Typical top-level commands include:

- `serve`
- `init`
- `config`
- `api`

Use `serve` and `api` together when the binary deliberately exposes both server and client roles.

### `config` and `init` commands

Use a `config` subtree when the application has:

- authored config on disk
- resolved runtime inspection
- config-backed resource management

If these needs are clearly present, read [config-integration.md](./config-integration.md).

If these needs are not clearly defined yet, skip this.

---

Use a top-level `init` command when the application has mutable bootstrap work such as:

- database initialization
- schema setup
- explicit key bootstrap
- durable seed state

If these needs are not clearly defined yet, skip this.

---

If relevant, keep `config init` and top-level `init` separate.
- `<bin> config init` initializes the **configuration material**
- `<bin> init` initializes the **program state**

## API resource subtrees

When the CLI manages resource families, give each family a stable subtree.

For example:

```
<bin> api user list
<bin> api user create
<bin> api user delete
```

This works best when the CLI shape mirrors the service's resource vocabulary and, when reasonable, the HTTP resource paths as well.

For `serve`, prefer resolving runtime config and delegating serving composition to `internal/server` rather than constructing service/API packages in the command handler.

If CLI commands call a JSON API, read [calling-api.md](./calling-api.md).

## Small helpers

Small helpers are useful for repeated mechanics such as:

- loading credentials from a directory
- writing JSON output
- building shared client parameters

Keep these helpers narrow and mechanical; they should remove boilerplate, not hide the command's intent.

## Testing expectations

CLI command structure should make it easy to test:

- root command composition
- option/env/default precedence
- command-local validation
- config/environment integration
- command output for representative success and failure cases
- explicit init behavior, including idempotent repeated runs

Prefer tests that exercise commands in-process with explicit input values rather than shelling out to a built binary for default coverage.
