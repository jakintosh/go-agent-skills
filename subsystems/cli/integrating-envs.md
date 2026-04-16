# Integrating CLI root with `command-go/pkg/envs`

**Pre-requisite:** ./building-a-cli.md (how to build a CLI in general)
**Package:** `git.sr.ht/~jakintosh/command-go@v0.4.2`

For CLI projects that interact with an HTTP API, it can be useful to have a way to manage api endpoint/key pairs. The `command-go/pkg/envs` package provides an off-the-shelf `&args.Command` subtree that implements this behavior.

## Using `envs.CommandOptions`

`envs.CommandOptions` is a struct that configures the built-in "env" subcommand. It requires a default configuration directory to read from, and a "Key Backend".

Under the hood, the "env" subcommand provides a built in key-rotation command, which requires a backend interface that allows it to interact with the API key provider. If using the `command-go/pkg/keys` package to manage api keys (very likely), the `keys` package itself provides an implementation of that interface to use in `envs.CommandOptions`.

```go
var envsOpts = envs.CommandOptions{
	DefaultConfigDir: DEFAULT_CFG,
	KeyBackend: keys.EnvBackend{
		CollectionPath: "/keys",
	},
}
```

## Using `envs.ConfigOptions`

The built in "env" command will look for a set of options when executed. Instead of adding them manually, you can set the value of `Options` to `envs.ConfigOptions()`:

```go
var rootCommand = &args.Command{
	Name: BIN_NAME,
  // ..
	Options: envs.ConfigOptions(),
  // ...
}
```

If you want to add additional options on top of those, you can use `envs.ConfigOptionsAnd`:

```go
var rootCommand = &args.Command{
	Name: BIN_NAME,
  // ..
	Options: envs.ConfigOptionsAnd(
		args.Option{
			Short: 'v',
			Long:  "verbose",
			Type:  args.OptionTypeFlag,
			Help:  "enable verbose logs",
		},
	),
  // ...
}
```

## Using `envs.Command()`

Finally, to register the "env" command, use the `envs.Command()` function directly in the subcommand slice literal, passing in the `envs.CommandOptions` struct.

```go
var rootCommand = &args.Command{
  // ...
	Subcommands: []*args.Command{
		envs.Command(envsOpts),
	},
}
```

## Full code example

```go
import "git.sr.ht/~jakintosh/command-go/pkg/envs"

const (
	DEFAULT_CFG = "/etc/<bin>"
)

var envsOpts = envs.CommandOptions{
	DefaultConfigDir: DEFAULT_CFG,
	KeyBackend: keys.EnvBackend{
		CollectionPath: "/keys",
	},
}

var rootCommand = &args.Command{
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
	Options: envs.ConfigOptionsAnd(
		args.Option{
			Short: 'v',
			Long:  "verbose",
			Type:  args.OptionTypeFlag,
			Help:  "enable verbose logs",
		},
	),
	Subcommands: []*args.Command{
		apiCommand,
		envs.Command(envsOpts),
	},
}
```

## Command line interface

Once complete, the "env" command added to your tree will provide the following interface:
```
Usage: example env <subcommand> | [options...]

Subcommands:
    list......................list environments
    create....................create environment
    set.......................set active environment
    delete....................delete environment
    key.......................manage stored api key for active environment
    url.......................manage api base url for active environment

Options:
    --config-dir..............path to config directory
    --env.....................environment name override
```
