# Config-Backed Resources

This guide defines the default shape for resource families stored under the config directory.

Use it when authored config includes collections such as themes, templates, providers, policies, or environments.

## Contents

- [Required instructions](#required-instructions)
- [Local shape](#local-shape)
- [Focused example](#focused-example)

## Required Instructions

- Store each resource as its own file under a dedicated directory.
- Keep the root config file focused on process-level settings.
- Give each resource family a narrow helper surface such as `List`, `Show`, `New`, `Delete`, and `Load`.
- Detect filename collisions and invalid resource names.
- Load required resource families from `internal/config`, not from unrelated packages.
- Keep destructive operations explicit, usually behind `--force`.

## Local Shape

Use a layout like:

```text
<config-dir>/
  config.yaml
  secrets/
    signing_key
  themes/
    default.yaml
    dark.yaml
```

The usual flow for one family is:

1. keep files under one dedicated directory
2. resolve one resource by stable name
3. decode each resource strictly
4. detect duplicate keys before returning a collection
5. derive the family directory from `Paths`
6. load the family during `Resolve(...)` when runtime needs it

## Focused Example

```go
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type Theme struct {
	Name      string `yaml:"name"`
	FromEmail string `yaml:"from_email"`
}

type ThemeRef struct {
	Name string
	Path string
}

type ThemeOptions struct {
	Force bool
	Theme *Theme
}

func ListThemes(configDir string) ([]ThemeRef, error) {
	paths := ResolvePaths(configDir, "")
	return listThemeRefs(paths.ThemesDir)
}

func ShowTheme(configDir string, name string) (Theme, error) {
	paths := ResolvePaths(configDir, "")
	path, err := resolveThemePath(paths.ThemesDir, name)
	if err != nil {
		return Theme{}, err
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return Theme{}, fmt.Errorf("read theme: %w", err)
	}

	var theme Theme
	if err := decodeYAML(data, &theme); err != nil {
		return Theme{}, fmt.Errorf("decode theme: %w", err)
	}
	return theme, nil
}

func NewTheme(configDir string, name string, opts ThemeOptions) error {
	paths := ResolvePaths(configDir, "")
	trimmed := strings.TrimSpace(name)
	if trimmed == "" {
		return fmt.Errorf("theme name is required")
	}

	theme := opts.Theme
	if theme == nil {
		theme = &Theme{Name: trimmed}
	}

	data, err := encodeYAML(theme)
	if err != nil {
		return err
	}

	path := filepath.Join(paths.ThemesDir, trimmed+".yaml")
	return writeFileAtomic(path, data, 0o644, opts.Force)
}

func DeleteTheme(configDir string, name string, force bool) error {
	if !force {
		return fmt.Errorf("theme delete is non-destructive by default; re-run with --force")
	}

	paths := ResolvePaths(configDir, "")
	path, err := resolveThemePath(paths.ThemesDir, name)
	if err != nil {
		return err
	}
	return os.Remove(path)
}

func LoadThemes(configDir string) (map[string]Theme, error) {
	paths := ResolvePaths(configDir, "")
	refs, err := listThemeRefs(paths.ThemesDir)
	if err != nil {
		return nil, err
	}

	out := make(map[string]Theme, len(refs))
	for _, ref := range refs {
		theme, err := ShowTheme(configDir, ref.Name)
		if err != nil {
			return nil, err
		}
		out[ref.Name] = theme
	}
	return out, nil
}

func listThemeRefs(dir string) ([]ThemeRef, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}

	refs := make([]ThemeRef, 0)
	seen := map[string]struct{}{}
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		ext := strings.ToLower(filepath.Ext(entry.Name()))
		if ext != ".yaml" && ext != ".yml" {
			continue
		}

		name := strings.TrimSuffix(entry.Name(), ext)
		if _, ok := seen[name]; ok {
			return nil, fmt.Errorf("theme key collision for %q", name)
		}
		seen[name] = struct{}{}
		refs = append(refs, ThemeRef{
			Name: name,
			Path: filepath.Join(dir, entry.Name()),
		})
	}

	sort.Slice(refs, func(i, j int) bool {
		return refs[i].Name < refs[j].Name
	})
	return refs, nil
}
```

This is the default shape to preserve:

- each resource has its own file
- resource directories come from centralized `Paths`
- helper functions stay local to `internal/config`
- collisions are treated as errors
- config resource CRUD stays separate from the root config file
