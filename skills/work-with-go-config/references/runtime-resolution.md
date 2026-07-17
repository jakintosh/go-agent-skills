# Runtime Resolution

This guide defines the default shape of authored config loading, runtime resolution, and resolved inspection output

Use it when you are implementing `Load(...)`, `Resolve(...)`, root path resolution, secret loading, or `config show --resolved`

## Contents

- [Required instructions](#required-instructions)
- [Local flow](#local-flow)
- [Focused example](#focused-example)

## Required Instructions

- Resolve root paths in `internal/config`, not in each command
- Resolve `Paths` once from `config-dir` and `data-dir`, and treat the rest of the filesystem layout as derived contract
- Use CLI override, then environment variable, then config file, then compiled default precedence for ordinary settings
- Use CLI override, then environment variable, then default precedence for root paths such as `config-dir` and `data-dir`
- Load authored config strictly and validate after all merges
- Load secrets from environment first and file fallback second
- Build a redacted resolved view for inspection output
- Keep commands and services out of secondary merge logic

## Local Flow

The default resolution flow is:

1. resolve `config-dir` and `data-dir`
2. build `Paths` from those root paths
3. load authored config starting from `Default()`
4. merge environment values
5. apply explicit CLI overrides
6. validate the merged config
7. load secrets and config-backed resources through `Paths`
8. derive any remaining runtime-only values
9. return `Runtime`

If startup needs to create baseline files first, read [initialization.md](./initialization.md)

## Focused Example

```go
package config

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

const DefaultConfigDir = "~/.config/example"
const DefaultDataDir = "~/.local/share/example"

type Overrides struct {
	Host *string
	Port *int
}

type Config struct {
	Host string `yaml:"host"`
	Port int    `yaml:"port"`
}

type Paths struct {
	ConfigDir      string `yaml:"config_dir"`
	DataDir        string `yaml:"data_dir"`
	ConfigFile     string `yaml:"config_file"`
	SecretsDir     string `yaml:"secrets_dir"`
	SigningKeyFile string `yaml:"signing_key_file"`
	ThemesDir      string `yaml:"themes_dir"`
	DatabaseFile   string `yaml:"database_file"`
}

type Runtime struct {
	Paths        Paths
	Host         string
	Port         int
	SigningKey   []byte
	SecretSource string
}

type RuntimeView struct {
	Paths        Paths      `yaml:"paths"`
	Host         string     `yaml:"host"`
	Port         int        `yaml:"port"`
	Secrets      SecretView `yaml:"secrets"`
}

type SecretView struct {
	SigningKeySet    bool   `yaml:"signing_key_set"`
	SigningKeySource string `yaml:"signing_key_source"`
}

func ResolveConfigDir(value string) string {
	resolved := strings.TrimSpace(value)
	if resolved == "" {
		resolved = strings.TrimSpace(os.Getenv("APP_CONFIG_DIR"))
	}
	if resolved == "" {
		resolved = DefaultConfigDir
	}
	return expandHome(resolved)
}

func ResolveDataDir(value string) string {
	resolved := strings.TrimSpace(value)
	if resolved == "" {
		resolved = strings.TrimSpace(os.Getenv("APP_DATA_DIR"))
	}
	if resolved == "" {
		resolved = DefaultDataDir
	}
	return expandHome(resolved)
}

func ResolvePaths(configDir string, dataDir string) Paths {
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

func Load(paths Paths) (Config, error) {
	cfg := Default()

	data, err := os.ReadFile(paths.ConfigFile)
	if err != nil {
		if os.IsNotExist(err) {
			return cfg, nil
		}
		return Config{}, fmt.Errorf("read config: %w", err)
	}

	decoder := yaml.NewDecoder(bytes.NewReader(data))
	decoder.KnownFields(true)
	if err := decoder.Decode(&cfg); err != nil {
		return Config{}, fmt.Errorf("decode config: %w", err)
	}

	return cfg, nil
}

func Resolve(configDir string, dataDir string, overrides Overrides) (Runtime, error) {
	paths := ResolvePaths(configDir, dataDir)

	cfg, err := Load(paths)
	if err != nil {
		return Runtime{}, err
	}
	if value := strings.TrimSpace(os.Getenv("APP_HOST")); value != "" {
		cfg.Host = value
	}
	if overrides.Host != nil {
		cfg.Host = *overrides.Host
	}
	if overrides.Port != nil {
		cfg.Port = *overrides.Port
	}
	if err := cfg.Validate(); err != nil {
		return Runtime{}, err
	}

	signingKey, source, err := readSecret(
		"APP_SIGNING_KEY",
		paths.SigningKeyFile,
	)
	if err != nil {
		return Runtime{}, err
	}

	return Runtime{
		Paths:        paths,
		Host:         cfg.Host,
		Port:         cfg.Port,
		SigningKey:   signingKey,
		SecretSource: source,
	}, nil
}

func (r Runtime) View() RuntimeView {
	return RuntimeView{
		Paths:        r.Paths,
		Host:         r.Host,
		Port:         r.Port,
		Secrets: SecretView{
			SigningKeySet:    len(r.SigningKey) > 0,
			SigningKeySource: r.SecretSource,
		},
	}
}
```

This is the default shape to preserve:

- only `config-dir` and `data-dir` are path inputs
- `Paths` locks in all expected files and directories from those inputs
- authored config decoding is strict
- `Resolve(...)` owns precedence and secret loading
- inspection output reports secret presence and source, not secret values
