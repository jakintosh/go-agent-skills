# Config Systems

This guide defines the standard shape for configuration systems in this style.

It applies to services that have moved beyond ad hoc runtime flags and need a real configuration subsystem with:

- authored config on disk
- resolved runtime state
- secret loading
- config-backed resources
- native bootstrap flows

The goal is to make configuration:

- explicit
- inspectable
- safe by default
- easy to bootstrap locally
- centralized instead of re-implemented across commands

## When to use this guide

Use this guide when:

- a service has more than a handful of runtime flags
- configuration must be loaded from disk, env, and CLI overrides
- the application manages config-backed resources such as themes, templates, providers, or policies
- the program needs a native `config init` flow
- the program needs both authored-config and resolved-runtime inspection

## Non-goals

This guide does not define:

- one specific file format such as YAML vs JSON vs TOML
- one exact CLI surface for every application
- one universal resource model for every kind of config-backed object

It does define the subsystem boundaries, resolution model, and bootstrap behavior that a real config system should have.

## Core rules

- Treat config as a subsystem, not a helper.
- Create an `internal/config` package that owns configuration behavior.
- Separate authored config from resolved runtime.
- Resolve precedence in one place only.
- Keep config-dir and data-dir separate.
- Keep secrets out of the main config file.
- Treat config-backed resource families as first-class files.
- Be non-destructive by default.
- Separate `config init` from top-level mutable `init`.
- Keep root path flags global so every command resolves the same environment shape.
- Make inspection easy with authored and resolved views.
- Make services consume resolved runtime, not raw flags, env vars, or config files.

## What this subsystem should achieve

A good config system should let a reader or operator answer:

- What is the authored config contract?
- What runtime values will the process actually use?
- Which values came from defaults, files, env, or CLI?
- Where are secrets loaded from?
- Where do config-backed resources live?
- How do I bootstrap a runnable local instance safely?

If those answers are scattered across commands, `main.go`, service constructors, and random helpers, the config system is too implicit.

## Canonical package shape

Use a dedicated package:

```text
internal/config/
  config.go
  runtime.go
  init.go
  <resource>.go
```

The ownership boundary matters more than the exact filenames:

- `config.go` owns authored config schema, defaults, load/save, and validation
- `runtime.go` owns full resolution into process-ready runtime state
- `init.go` owns native bootstrap behavior
- `<resource>.go` files own config-backed resource families

Commands should call into this package.

Services should consume runtime values produced by this package.

## Canonical type split

At minimum, keep two distinct shapes:

```go
type Config struct {
	Host string `yaml:"host"`
	Port int    `yaml:"port"`
}

type Runtime struct {
	ConfigDir string
	DataDir   string

	Host string
	Port int

	SigningKey []byte
}
```

The point is not the field list. The point is the boundary:

- `Config` is what humans author or what `config init` writes
- `Runtime` is what the process consumes after all merges, loads, and derivations

Do not collapse those two concepts into one struct once the config system becomes real.

## Resolution model

`Resolve()` should be the only place that merges:

- compiled defaults
- config file contents
- environment variables
- explicit CLI overrides
- secret loading
- config-backed resources
- derived paths

Canonical precedence:

1. explicit CLI overrides
2. environment variables
3. config file contents
4. compiled defaults

For root path inputs such as `config-dir` and `data-dir`, use the same idea:

1. explicit CLI value
2. environment variable
3. default path

Do not re-implement this precedence in each command.

## Canonical CLI shape

When a project has a true config subsystem, a good default CLI looks like:

```text
<app>
  --config-dir ...
  --data-dir ...
  config init
  config show
  config show --resolved
  config <resource> ...
  init
  serve
```

Interpretation:

- root options define the environment shape for all commands
- `config init` creates config files, secrets, and config-backed resources
- `config show` prints authored config
- `config show --resolved` prints the fully resolved runtime view
- `config <resource> ...` manages resource families
- top-level `init` performs mutable operational initialization
- `serve` resolves runtime and starts the service

## `config init` vs `init`

Keep these separate.

`config init` is for creating files and config-backed resources:

- write `config.yaml`
- create resource directories
- generate secret files
- create a minimal valid local baseline

Top-level `init` is for mutable operational state:

- database setup
- keys/bootstrap state
- schema creation
- seed records
- API-side initialization

This separation matters because it keeps file generation:

- understandable
- non-destructive
- repeatable

And it prevents config setup from quietly mutating operational state.

## Filesystem shape

Use a filesystem layout that separates authored config from mutable runtime state.

```text
<config-dir>/
  config.yaml
  secrets/
    <secret files>
  <resource-kind>/
    <resource-name>.yaml

<data-dir>/
  <database and other mutable state>
```

General rules:

- keep core process settings in the root config file
- keep resources in dedicated subdirectories
- keep file-backed secrets in a dedicated `secrets/` directory
- compute derived runtime paths centrally instead of rebuilding them throughout the codebase

## Config-backed resources

If the application has collections such as:

- themes
- templates
- providers
- policies
- environments

store them as separate files under the config directory instead of embedding them into one large root config blob.

That improves:

- ownership boundaries
- CRUD command design
- validation
- diffability
- reviewability

The root config file should describe process-level settings, not become the home for every resource catalog in the system.

## Secret handling

Keep secrets out of the main config file.

Prefer this shape:

- explicit environment override first
- file-backed secret fallback for local development
- restrictive file permissions
- no secret values in inspection output

Inspection output may say:

- secret is set
- secret file exists
- secret source is env or file

It should not print the actual secret value.

## Safe write behavior

Config generation should be non-destructive by default.

Recommended behavior:

- create parent directories automatically
- fail if a target file already exists unless an explicit force flag is set
- write through a temporary file and rename atomically when practical
- use restrictive permissions for secret files

This is important because config bootstrap commands tend to be run repeatedly in local environments.

## Canonical implementation flow

### 1. Defaults and validation

Keep a complete baseline config and explicit validation.

```go
func Default() Config {
	return Config{
		Host: "127.0.0.1",
		Port: 8080,
	}
}

func (c Config) Validate() error {
	if c.Port < 1 || c.Port > 65535 {
		return fmt.Errorf("invalid port")
	}
	return nil
}
```

The details will vary, but the pattern should hold:

- define defaults centrally
- normalize before validation if needed
- validate after all merges

### 2. Load authored config strictly

Treat unknown fields and invalid values as startup problems, not as soft warnings.

```go
func Load(configDir string) (Config, error) {
	path := filepath.Join(configDir, "config.yaml")

	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, err
	}

	cfg := Default()
	if err := strictYAMLDecode(data, &cfg); err != nil {
		return Config{}, err
	}

	if err := cfg.Validate(); err != nil {
		return Config{}, err
	}

	return cfg, nil
}
```

Strictness is a feature here. The config system should reduce ambiguity, not absorb it.

### 3. Resolve runtime once

The runtime resolver should assemble the full process-ready object.

```go
type ResolveOptions struct {
	ConfigDir string
	DataDir   string

	HostOverride *string
	PortOverride *int
}

func Resolve(opts ResolveOptions) (Runtime, error) {
	cfg, err := Load(opts.ConfigDir)
	if err != nil {
		return Runtime{}, err
	}

	host := cfg.Host
	if envHost := os.Getenv("APP_HOST"); envHost != "" {
		host = envHost
	}
	if opts.HostOverride != nil && *opts.HostOverride != "" {
		host = *opts.HostOverride
	}

	signingKey, err := loadSecret(
		"APP_SIGNING_KEY",
		filepath.Join(opts.ConfigDir, "secrets", "signing_key"),
	)
	if err != nil {
		return Runtime{}, err
	}

	return Runtime{
		ConfigDir:  opts.ConfigDir,
		DataDir:    opts.DataDir,
		Host:       host,
		Port:       cfg.Port,
		SigningKey: signingKey,
	}, nil
}
```

The specific fields do not matter as much as the ownership rule:

- `Resolve()` is the single merge point
- commands do not perform secondary merge logic
- services do not reopen config files or reread env vars

### 4. Bootstrap a runnable baseline

`config init` should know how to create a minimal valid config directory.

```go
type InitOptions struct {
	ConfigDir string
	Force     bool
}

func Init(opts InitOptions) error {
	if err := os.MkdirAll(filepath.Join(opts.ConfigDir, "secrets"), 0o755); err != nil {
		return err
	}

	cfgPath := filepath.Join(opts.ConfigDir, "config.yaml")
	if err := writeFileIfAllowed(cfgPath, mustYAML(Default()), opts.Force, 0o644); err != nil {
		return err
	}

	secretPath := filepath.Join(opts.ConfigDir, "secrets", "signing_key")
	if err := writeFileIfAllowed(secretPath, generateSecret(), opts.Force, 0o600); err != nil {
		return err
	}

	return nil
}
```

The application should be able to generate its own valid baseline without external templates.

## Command responsibilities

Commands should stay thin.

Good command responsibilities:

- read root path options
- collect invocation-specific overrides
- call `config.Load`, `config.Resolve`, `config.Init`, or resource helpers
- print authored or resolved views
- pass resolved runtime into service construction

Bad command responsibilities:

- reopening config files in several places
- duplicating precedence rules
- rebuilding derived paths
- loading secrets directly in unrelated commands

## Service responsibilities

Services should consume resolved runtime values only.

That means:

- no service package should reopen `config.yaml`
- no service package should reread environment variables
- no service package should know where secret files live

Those are config subsystem concerns.

## Testing expectations

At minimum, add tests for:

- defaults when no authored config is present, if supported
- strict decoding failures
- validation failures
- precedence across file, env, and CLI overrides
- root path resolution
- secret loading and secret redaction
- resource loading and resource collisions
- non-destructive `config init`
- force-overwrite behavior
- authored vs resolved inspection behavior

These tests are valuable because the config system is a contract surface, not just a helper library.

## Anti-patterns

- treating config as a few helpers scattered across `main.go`
- using one struct for both authored config and resolved runtime once the system becomes complex
- re-implementing precedence logic in each command
- mixing config files and mutable runtime state in the same directory
- storing secrets in the main config file
- embedding every resource family into one giant root config blob
- making `config init` mutate operational state
- making services read env vars or secret files directly
- printing secret values in inspection output
- silently overwriting config files during bootstrap

## Generic example

This is the target feel for a compact config subsystem:

```go
// internal/config/config.go
type Config struct {
	Host string `yaml:"host"`
	Port int    `yaml:"port"`
}

func Default() Config {
	return Config{
		Host: "127.0.0.1",
		Port: 8080,
	}
}

// internal/config/runtime.go
type Runtime struct {
	ConfigDir  string
	DataDir    string
	Host       string
	Port       int
	SigningKey []byte
}

// cmd/app/serve.go
Handler: func(i *args.Input) error {
	configDir := resolveConfigDir(i)
	dataDir := resolveDataDir(i)

	runtime, err := config.Resolve(config.ResolveOptions{
		ConfigDir: configDir,
		DataDir:   dataDir,
	})
	if err != nil {
		return err
	}

	svc, err := service.New(service.Options{
		Host:       runtime.Host,
		Port:       runtime.Port,
		SigningKey: runtime.SigningKey,
	})
	if err != nil {
		return err
	}

	return svc.Serve(runtime.Host, runtime.Port, "")
},
```

## Related guides

- `subsystems/cli-command-trees.md`
- `subsystems/service-construction.md`
- `subsystems/http-router-composition.md`
- `subsystems/database-adapters.md`
