# Config Initialization

This guide defines the default shape of `config init`

Use it when the application needs to generate a minimal valid config directory, secret files, or baseline resource files

## Contents

- [Required instructions](#required-instructions)
- [Local flow](#local-flow)
- [Focused example](#focused-example)

## Required Instructions

- Keep `config init` limited to config material
- Generate a runnable baseline natively in Go
- Resolve `Paths` once and write generated files through that value
- Create parent directories automatically
- Refuse to overwrite existing files unless an explicit force flag is set
- Write secret files with restrictive permissions
- Return enough result data for the caller to print the written paths
- Keep mutable operational setup in a separate top-level `init` path

## Local Flow

The default initialization flow is:

1. resolve `config-dir` and `data-dir`
2. build `Paths` from those root paths
3. build `Default()` config and apply init-time overrides
4. validate the generated config
5. create config, data, and secret directories
6. write config files, resource files, and secret files through `Paths`
7. return the paths that were created

If the application also needs database setup or durable seed state, use `$work-with-go-services` and read its bootstrap-initialization reference.

## Focused Example

```go
package config

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type InitOptions struct {
	Overrides Overrides
	Force     bool
	ThemeName string
	APIKey    string
}

type InitResult struct {
	Paths      Paths
	ThemePath  string
	APIKeyPath string
}

func Init(configDir string, dataDir string, opts InitOptions) (InitResult, error) {
	paths := ResolvePaths(configDir, dataDir)

	cfg := Default()
	cfg.mergeOverrides(opts.Overrides)
	if err := cfg.Validate(); err != nil {
		return InitResult{}, err
	}

	themeName := strings.TrimSpace(opts.ThemeName)
	if themeName == "" {
		themeName = "default"
	}

	apiKey := strings.TrimSpace(opts.APIKey)
	if apiKey == "" {
		generated, err := generateSecret()
		if err != nil {
			return InitResult{}, err
		}
		apiKey = generated
	}

	if err := os.MkdirAll(paths.ConfigDir, 0o755); err != nil {
		return InitResult{}, fmt.Errorf("create config dir: %w", err)
	}
	if err := os.MkdirAll(paths.DataDir, 0o755); err != nil {
		return InitResult{}, fmt.Errorf("create data dir: %w", err)
	}
	if err := os.MkdirAll(paths.SecretsDir, 0o700); err != nil {
		return InitResult{}, fmt.Errorf("create secrets dir: %w", err)
	}

	if err := writeFileAtomic(paths.ConfigFile, mustYAML(cfg), 0o644, opts.Force); err != nil {
		return InitResult{}, err
	}
	if err := NewTheme(paths.ConfigDir, themeName, ThemeOptions{Force: opts.Force}); err != nil {
		return InitResult{}, err
	}
	if err := writeFileAtomic(
		filepath.Join(paths.SecretsDir, "api_key"),
		[]byte(apiKey+"\n"),
		0o600,
		opts.Force,
	); err != nil {
		return InitResult{}, err
	}

	secret, err := generateSecret()
	if err != nil {
		return InitResult{}, err
	}
	if err := writeFileAtomic(paths.SigningKeyFile, []byte(secret+"\n"), 0o600, opts.Force); err != nil {
		return InitResult{}, err
	}

	return InitResult{
		Paths:      paths,
		ThemePath:  filepath.Join(paths.ThemesDir, themeName+".yaml"),
		APIKeyPath: filepath.Join(paths.SecretsDir, "api_key"),
	}, nil
}

func generateSecret() (string, error) {
	buf := make([]byte, 32)
	if _, err := rand.Read(buf); err != nil {
		return "", err
	}
	return hex.EncodeToString(buf), nil
}
```

This is the default shape to preserve:

- `config init` creates a local baseline without external templates
- `Init(...)` resolves `Paths` first and writes through it consistently
- repeated runs stay non-destructive unless `--force` is explicit
- secret files are written with tighter permissions than ordinary config files
- mutable runtime setup stays out of `config init`
