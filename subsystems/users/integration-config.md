# Consent Integration Config

This guide defines the app-side production config needed to integrate a project with Consent.

Use it when building the production auth client, loading the Consent verification key, deriving the JWT audience, generating the integration manifest, constructing the authorize URL, or mounting Consent package handlers.

Assume `./README.md` already defined the account model and `internal/web` auth boundary.

## Required Instructions

- Keep Consent runtime config in the app's config/runtime layer, not in `internal/web`.
- Resolve the Consent base URL, integration name, public URL, and verification key path before constructing the web app.
- Load Consent's DER verification key as an ECDSA public key.
- Use the public URL host as the JWT audience.
- Use the Consent URL host as the token issuer domain unless the app has a specific authority-domain override.
- Build `/authorize` links with the integration name and requested scopes.
- Mount Consent's package handlers directly.
- Serve `client.HandleIntegrationManifest(...)` at `client.IntegrationManifestPath`.
- Keep the manifest's audience, redirect, homepage, and logo derived from the public URL.
- Derive public callback and asset URLs with URL-aware helpers when `PUBLIC_URL` may include a path.

## Runtime Inputs

The app should resolve a small production auth config from ordinary app config sources.

```go
type ConsentConfig struct {
	BaseURL             string
	IntegrationName     string
	PublicURL           string
	VerificationKeyFile string
}
```

A CLI or environment layer may expose these as flags and environment variables:

```text
--consent-url / CONSENT_URL
--integration-name / CONSENT_INTEGRATION
--public-url / PUBLIC_URL
--config-dir / CONFIG_DIR
```

The verification key should be a file inside the app's config directory. The app can choose the filename; document it and keep it stable. Consent generates its public key as `verification_key.der` in the Consent server's config secrets directory, and the app usually receives that DER file by mount, copy, or symlink.

## Production Builder

Keep the production builder in `internal/server` or another composition root.

```go
type ProductionAuth struct {
	Config AuthConfig
	Routes map[string]http.HandlerFunc
}

func buildProductionAuth(
	cfg ConsentConfig,
) (
	ProductionAuth,
	error,
) {
	publicKey, err := loadConsentPublicKey(cfg.VerificationKeyFile)
	if err != nil {
		return ProductionAuth{}, err
	}

	consentBase, issuer, err := processConsentURL(cfg.BaseURL)
	if err != nil {
		return ProductionAuth{}, err
	}

	app, err := buildProductionAppConfig(cfg.PublicURL)
	if err != nil {
		return ProductionAuth{}, err
	}

	validator := tokens.InitClient(tokens.ClientOptions{
		VerificationKey: publicKey,
		IssuerDomain:    issuer,
		ValidAudience:   app.Audience,
	})
	authClient := client.Init(validator, consentBase)

	manifest := client.IntegrationManifest{
		Name:           cfg.IntegrationName,
		Display:        "Documents",
		Audience:       app.Audience,
		Redirect:       app.CallbackURL,
		Homepage:       app.Homepage,
		Logo:           app.LogoURL,
		ConsentIssuer:  issuer,
		ConsentBaseURL: consentBase,
	}

	return ProductionAuth{
		Config: AuthConfig{
			Verifier:       authClient,
			ProfileFetcher: authClient,
			LoginURL:       buildAuthorizeURL(consentBase, cfg.IntegrationName, []string{"identity", "profile"}),
			LogoutURL:      "/auth/logout",
		},
		Routes: map[string]http.HandlerFunc{
			"/auth/callback":               authClient.HandleAuthorizationCode(),
			"/auth/logout":                 authClient.HandleLogout(),
			client.IntegrationManifestPath: client.HandleIntegrationManifest(manifest),
		},
	}, nil
}
```

If the app does not need profile data, remove `ProfileFetcher` and use `[]string{"identity"}` for the authorize scopes.

## Public URL Processing

The public URL is the user's external entry point for this app. Use its host as the audience. Preserve its path when the app is deployed below a reverse-proxy prefix.

```go
type ProductionAppConfig struct {
	Audience    string
	Homepage    string
	CallbackURL string
	LogoURL     string
}

func buildProductionAppConfig(
	rawPublicURL string,
) (
	ProductionAppConfig,
	error,
) {
	homepage, audience, err := processPublicURL(rawPublicURL)
	if err != nil {
		return ProductionAppConfig{}, err
	}

	callbackURL, err := url.JoinPath(homepage, "auth", "callback")
	if err != nil {
		return ProductionAppConfig{}, err
	}

	logoURL, err := url.JoinPath(homepage, "static", "consent-logo.png")
	if err != nil {
		return ProductionAppConfig{}, err
	}

	return ProductionAppConfig{
		Audience:    audience,
		Homepage:    homepage,
		CallbackURL: callbackURL,
		LogoURL:     logoURL,
	}, nil
}
```

The redirect and homepage hosts must match the audience. Paths may differ. For example, an app with `PUBLIC_URL=https://example.com/tools/documents` still uses `example.com` as the audience and `https://example.com/tools/documents/auth/callback` as the redirect.

## Verification Key Loading

Consent client apps validate tokens with Consent's public verification key.

```go
func loadConsentPublicKey(
	filename string,
) (
	*ecdsa.PublicKey,
	error,
) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", filename, err)
	}

	pub, err := x509.ParsePKIXPublicKey(data)
	if err != nil {
		return nil, err
	}

	ecdsaPub, ok := pub.(*ecdsa.PublicKey)
	if !ok {
		return nil, fmt.Errorf("not an ECDSA public key")
	}
	return ecdsaPub, nil
}
```

Do not fetch the verification key over the request path during normal startup. Treat it as deployed runtime config so the app can fail fast when key material is missing.

## Route Mounting

Mount package handlers at the process route root before mounting the app's catch-all browser router.

```go
root := http.NewServeMux()
for path, handler := range auth.Routes {
	root.HandleFunc(path, handler)
}
wire.Subrouter(root, "/", webApp.Router())
```

If the browser UI has tenant or catch-all paths, reserve `auth`, `dev`, `static`, and `.well-known` at the top level so those package handlers stay reachable.
