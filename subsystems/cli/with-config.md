# Wiring a CLI to a Config Subsystem

This guide defines the default shape for a CLI that consumes `internal/config`

Use it when the binary has root path flags, a `config` subtree, or runtime commands that call `config.Resolve(...)`

## Required

- Keep root path flags such as `--config-dir` and `--data-dir` on the root command
- Keep `config` as its own command subtree when the application has a real config subsystem
- Keep handlers thin: collect inputs, call `config.Load(...)`, `config.Resolve(...)`, `config.Init(...)`, or resource helpers, then print output
- Keep invocation-specific runtime overrides on the command that uses them
- Keep `config init` separate from top-level mutable `init`

## Local Flow

The default CLI flow is:

1. the root command defines shared path options
2. `config init` calls `config.Init(...)`
3. `config show` calls `config.Load(...)`
4. `config show --resolved` calls `config.Resolve(...)`
5. runtime commands such as `serve` call `config.Resolve(...)` and pass `Runtime` into other constructors

## Focused Example

```go
var root = &args.Command{
	Name: "example",
	Options: []args.Option{
		{
			Long: "config-dir",
			Type: args.OptionTypeParameter,
			Help: "path to the authored config directory",
		},
		{
			Long: "data-dir",
			Type: args.OptionTypeParameter,
			Help: "path to mutable runtime data",
		},
	},
	Subcommands: []*args.Command{
		configCommand,
		initCommand,
		serveCommand,
	},
}

var configCommand = &args.Command{
	Name: "config",
	Subcommands: []*args.Command{
		configInitCommand,
		configShowCommand,
		configThemeCommand,
	},
}

var configShowCommand = &args.Command{
	Name: "show",
	Options: []args.Option{
		{
			Long: "resolved",
			Type: args.OptionTypeFlag,
			Help: "show resolved runtime values",
		},
	},
	Handler: func(i *args.Input) error {
		configDir := i.GetParameterOr("config-dir", "")
		dataDir := i.GetParameterOr("data-dir", "")

		if i.GetFlag("resolved") {
			runtime, err := config.Resolve(configDir, dataDir, config.Overrides{})
			if err != nil {
				return err
			}
			return writeYAML(runtime.View())
		}

		cfg, err := config.Load(configDir)
		if err != nil {
			return err
		}
		return writeYAML(cfg)
	},
}

var serveCommand = &args.Command{
	Name: "serve",
	Options: []args.Option{
		{
			Long: "host",
			Type: args.OptionTypeParameter,
			Help: "override server host",
		},
		{
			Long: "port",
			Type: args.OptionTypeParameter,
			Help: "override server port",
		},
	},
	Handler: func(i *args.Input) error {
		runtime, err := config.Resolve(
			i.GetParameterOr("config-dir", ""),
			i.GetParameterOr("data-dir", ""),
			config.Overrides{
				Host: i.GetParameter("host"),
				Port: i.GetIntParameter("port"),
			},
		)
		if err != nil {
			return err
		}

		svc, err := service.New(service.Options{
			DatabasePath: runtime.DatabasePath,
			SigningKey:   runtime.SigningKey,
			Themes:       runtime.Themes,
		})
		if err != nil {
			return err
		}

		return svc.Serve(runtime.Host, runtime.Port)
	},
}
```

This is the default shape to preserve:

- the root command defines one shared environment shape
- the `config` subtree owns config material and inspection
- runtime commands keep only command-local overrides
- handlers call into `internal/config` instead of reimplementing precedence rules
