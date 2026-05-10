# Defining a Config Subsystem

This guide defines the default shape of `internal/config`. The core philosophy is that the binary should be able to create and manage its own config, without needing to ship example config or an out-of-band manual

Use this guide when the application has authored config on disk, resolved runtime state, secret loading, config-backed resources, or a native `config init` flow.

The config subsystem defines authored config schema, defaults, loading, saving, validation, derived filesystem paths, runtime resolution, secret loading, redacted inspection output, native `config init` behavior, and config-backed resource families such as themes, templates, providers, or policies.

## Required Instructions

- Create `internal/config` as the single owner of configuration behavior
- Keep authored `Config` and resolved `Runtime` as separate types
- Create one centralized `Paths` value from resolved `config-dir` and `data-dir`, and use it across the subsystem
- Make `Resolve(...)` the only place that merges defaults, config files, environment, CLI overrides, secrets, resources, and derived paths
- Track `config-dir` and `data-dir` separate, foundational inputs to the config system
- Keep secrets out of the main config file
- Load authored config strictly and fail on unknown or invalid fields
- Keep commands thin and keep the serving stack consuming resolved runtime only
- Provide both authored and resolved inspection paths
- Make generated writes non-destructive by default
- Store config-backed resource families as files under the config directory

## Canonical Shape

Use a layout like:

```text
internal/config/
  config.go
  paths.go
  runtime.go
  init.go
  <resource>.go
```

Keep the ownership split clear:

- `config.go` owns `Config`, defaults, load, save, and validation
- `paths.go` owns `Paths` and `ResolvePaths(...)`
- `runtime.go` owns `Runtime`, `Resolve(...)`, derived paths, and resolved inspection
- `init.go` owns `config init` config file bootstrapping
- resource files own one config-backed family each

If you are implementing `Resolve(...)`, read `./runtime-resolution.md`

If you are implementing `config init`, read `./initialization.md`

If the config directory owns a resource family, read `./resources.md`

If the CLI needs to expose `config` commands or root path flags, read `../cli/with-config.md`

## Canonical Flow

The default runtime flow is:

1. a command forwards raw root-path inputs and invocation-specific overrides to `internal/config`
2. `Resolve(...)` resolves config paths, loads authored config, merges environment and CLI overrides, loads secrets and resources, and derives runtime-only values
3. the command passes `Runtime` into `internal/server`
4. the server opens other dependencies from `Runtime` and constructs service/API packages
5. service and API packages consume ready-to-use dependencies and do not re-open config files, environment variables, or secret files

## Canonical Example

```go
package config

import "path/filepath"

type Overrides struct {
	Host *string
	Port *int
}

type Config struct {
	Server ServerConfig `yaml:"server"`
}

type Paths struct {
	ConfigDir      string
	DataDir        string
	ConfigFile     string
	SecretsDir     string
	SigningKeyFile string
	ThemesDir      string
	DatabaseFile   string
}

type ServerConfig struct {
	Host string `yaml:"host"`
	Port int    `yaml:"port"`
}

type Runtime struct {
	Config
	Paths      Paths
	SigningKey []byte
	Themes     map[string]Theme
}

func ResolvePaths(
	configDir string,
	dataDir string,
) Paths {
	resolvedConfigDir := ResolveConfigDir(configDir)
	resolvedDataDir := ResolveDataDir(dataDir)

	return Paths{
		ConfigDir:      resolvedConfigDir,
		DataDir:        resolvedDataDir,
		ConfigFile:     filepath.Join(resolvedConfigDir, "config.yaml"),
		SecretsDir:     filepath.Join(resolvedConfigDir, "secrets"),
		SigningKeyFile: filepath.Join(resolvedConfigDir, "secrets", "signing_key"),
		ThemesDir:      filepath.Join(resolvedConfigDir, "themes"),
		DatabaseFile:   filepath.Join(resolvedDataDir, "app.db"),
	}
}

func Resolve(
	configDir string,
	dataDir string,
	overrides Overrides,
) (
	Runtime,
	error,
) {
	paths := ResolvePaths(configDir, dataDir)

	cfg, err := Load(paths)
	if err != nil {
		return Runtime{}, err
	}
	if err := cfg.mergeEnv(); err != nil {
		return Runtime{}, err
	}
	cfg.mergeOverrides(overrides)
	if err := cfg.Validate(); err != nil {
		return Runtime{}, err
	}

	signingKey, err := readSecret(
		"APP_SIGNING_KEY",
		paths.SigningKeyFile,
	)
	if err != nil {
		return Runtime{}, err
	}

	themes, err := LoadThemes(paths.ConfigDir)
	if err != nil {
		return Runtime{}, err
	}

	return Runtime{
		Config:     cfg,
		Paths:      paths,
		SigningKey: signingKey,
		Themes:     themes,
	}, nil
}
```

This is the default shape to preserve:

- commands pass raw inputs into `internal/config`
- `Paths` locks in the filesystem contract from the resolved root directories
- `Resolve(...)` performs the full merge once
- runtime-only values live on `Runtime`
- other subsystems consume `Runtime`, not raw config sources

## Leaf Docs

- Read `./runtime-resolution.md` for merge precedence, `ResolvePaths(...)`, strict loading, secrets, and redacted inspection
- Read `./initialization.md` for `config init`, safe writes, and generated baseline files
- Read `./resources.md` for config-backed resource families

## Common Touchpoints

- `subsystems/cli/README.md` for command tree shape
- `subsystems/cli/with-config.md` for CLI wiring and `config` subcommands
- `subsystems/server/README.md` for serving composition
- `subsystems/service/README.md` for service construction boundaries
- `subsystems/service/bootstrap-initialization.md` for top-level mutable initialization outside `config init`
