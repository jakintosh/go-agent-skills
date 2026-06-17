# Integrating CLI Root with `command-go/pkg/envs`

**Pre-requisite:** `./README.md`
**Package:** `git.sr.ht/~jakintosh/command-go/pkg/envs`

Use this guide when a CLI calls an HTTP API and needs named environments for base URL and API key pairs.

The `envs` package provides the standard `env` command tree, config-file persistence, active-environment resolution, and helpers for building a `wire.Client`.

## Required

- Put `envs.ConfigOptions` or `envs.ConfigOptionsAnd(...)` on the root command.
- Put `wire.ClientOptions` or `wire.ClientOptionsAnd(...)` on the API-calling subtree.
- Register `envs.Command(...)` as a root-level subtree named `env`.
- Provide an `envs.KeyBackend` through `envs.CommandOptions`.
- Use `envs.LoadConfig(...)`, `envs.ResolveClient(...)`, or `envs.ResolveClientContext(...)` in handlers instead of opening `environments.json` directly.
- Keep API-calling handlers thin: resolve a client, call the API, print output.

## Root Options

The root command owns config and environment selection because those options apply across the command tree.

```go
var rootCommand = &args.Command{
	Name: BIN_NAME,
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

`envs.ConfigOptions` provides:

- `--config-dir`
- `--env`

## API Client Options

The API-calling branch owns direct client overrides because local commands should not imply HTTP access.

```go
var apiCommand = &args.Command{
	Name: "api",
	Help: "call the HTTP API",
	Options: wire.ClientOptions,
	Subcommands: []*args.Command{
		apiUserCommand,
	},
}
```

`wire.ClientOptions` provides:

- `--base-url`
- `--api-key`

Use `wire.ClientOptionsAnd(...)` when the branch also needs local options such as output format.

## Environment Command

Configure the built-in `env` command with a default config directory and key backend.

```go
var envsOpts = envs.CommandOptions{
	DefaultConfigDir: DEFAULT_CFG,
	KeyBackend: keys.EnvBackend{
		CollectionPath: "/api/v1/settings/keys",
	},
}
```

When the project uses `command-go/pkg/keys`, use `keys.EnvBackend`. Its collection path must match where the keys handler is mounted in the HTTP API.

## Resolving a Client

Use `envs.ResolveClient(...)` when an ordinary request command needs a `wire.Client`.

```go
func buildClient(
	i *args.Input,
) (
	wire.Client,
	error,
) {
	return envs.ResolveClient(i, DEFAULT_CFG, "/api/v1")
}
```

Resolution order is:

1. `--config-dir`, then the default config dir, to find `environments.json`.
2. `--env`, then `CLI_ENV`, then stored `activeEnv`, to choose the environment.
3. `--base-url` and `--api-key`, then the active environment values, to build the client.
4. `pathPrefix`, normalized and appended to the resolved base URL.

The config directory is created with `0700` permissions and `environments.json` is written with `0600` permissions.

## Inspecting Client Resolution

Use `envs.ResolveClientContext(...)` when a command needs to explain or validate how the client was resolved.

This is useful for:

- `status` commands
- diagnostic output
- bootstrap checks
- key-management commands
- setup flows that need to report missing configuration

```go
func inspectClient(
	i *args.Input,
) error {
	resolution, err := envs.ResolveClientContext(i, DEFAULT_CFG, "/api/v1")
	if err != nil {
		return err
	}

	fmt.Println("env:", resolution.EnvName)
	fmt.Println("env source:", resolution.EnvSource)
	fmt.Println("env exists:", resolution.EnvExists)
	fmt.Println("base url:", resolution.BaseURL)
	fmt.Println("base url source:", resolution.BaseURLSource)
	fmt.Println("api key configured:", resolution.APIKeySet)
	fmt.Println("api key source:", resolution.APIKeySource)

	return nil
}
```

`ClientResolution` keeps both the final client and safe inspection fields:

- `Client` is the final `wire.Client` used for requests.
- `EnvName`, `EnvSource`, and `EnvExists` describe environment selection.
- `BaseURL` is the normalized service base URL before `PathPrefix` is appended.
- `Client.BaseURL` is the final request base URL after `PathPrefix` is appended.
- `APIKeySet` reports whether a key was resolved without exposing the secret.
- `BaseURLSource` and `APIKeySource` describe where each value came from.
- `PathPrefix` records the normalized path prefix used to build the final client.

String values on `ClientResolution` are normalized for callers. Environment names and API keys are trimmed, base URLs are trimmed and have trailing slashes removed, and path prefixes are trimmed into a leading-slash form such as `/api/v1`.

Resolution sources are `SourceUnset`, `SourceOption`, `SourceOS`, and `SourceConfig`. Environment names may come from `--env`, `CLI_ENV`, or config. Base URLs and API keys may come from options or config.

Status and debug output should prefer `APIKeySet` and `APIKeySource` over `resolution.Client.APIKey`. The raw API key remains on `resolution.Client.APIKey` only so requests can be made.

Use the requirement helpers when a command has a hard dependency:

```go
resolution, err := envs.ResolveClientContext(i, DEFAULT_CFG, "/api/v1")
if err != nil {
	return err
}
if err := resolution.RequireBaseURL(); err != nil {
	return err
}
if err := resolution.RequireAPIKey(); err != nil {
	return err
}

client := resolution.Client
```

## Full Example

```go
import (
	"git.sr.ht/~jakintosh/command-go/pkg/args"
	"git.sr.ht/~jakintosh/command-go/pkg/envs"
	"git.sr.ht/~jakintosh/command-go/pkg/keys"
	"git.sr.ht/~jakintosh/command-go/pkg/wire"
)

const DEFAULT_CFG = "/etc/<bin>"

var envsOpts = envs.CommandOptions{
	DefaultConfigDir: DEFAULT_CFG,
	KeyBackend: keys.EnvBackend{
		CollectionPath: "/api/v1/settings/keys",
	},
}

var apiCommand = &args.Command{
	Name: "api",
	Help: "call the HTTP API",
	Options: wire.ClientOptions,
	Subcommands: []*args.Command{
		apiUserCommand,
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

## Command Line Interface

The `env` subtree provides:

```text
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

API-calling subtrees that include `wire.ClientOptions` also accept:

```text
    --base-url................API base URL override
    --api-key.................API key override
```
