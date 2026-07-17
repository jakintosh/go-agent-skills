# Integrating Users With Consent

This guide defines the default shape for adding Consent-backed users to a server application.

Use it when an application needs login, per-user data, account-scoped service methods, server-rendered routes protected by Consent cookies, or production registration as a Consent integration.

Consent owns authentication, credentials, grants, roles, sessions, token refresh, token signing, and profile authority. The application owns local account records, cached profile fields needed by its UI, and all application data attached to those local accounts.

## Owns

The user subsystem owns:

- the local `accounts` table
- the mapping from Consent subject to local account ID
- cached display/profile fields used by the application
- request authentication context in `internal/web`
- account-scoped service inputs and store methods
- account foreign keys on application-owned tables
- the app-side Consent integration config consumed by the serving stack

It does not own password storage, login forms, Consent user roles, integration grants, token issuing, refresh-token persistence, or profile authority.

## Required Instructions

- Use the Consent `sub` claim as the durable external identity key.
- Store a local account ID and use that ID as the foreign key for application data.
- Treat handles and profile fields as cached display data, not stable identity.
- Keep Consent client construction in `internal/server` or another composition root.
- Keep app-side Consent runtime config explicit: Consent base URL, integration name, public URL, and verification key path.
- Pass authentication into `internal/web` through a small `AuthConfig`.
- Depend on `client.Verifier` in `internal/web`, not `*client.Client`.
- Mount Consent package handlers for `/auth/callback`, `/auth/logout`, and `/.well-known/consent-integration`.
- Request the `identity` scope for every account-backed app.
- Request the `profile` scope only when the app needs Consent profile data such as a handle.
- Use `VerifyAuthorizationGetCSRF` when rendering pages that include state-changing controls.
- Use `VerifyAuthorizationCheckCSRF` before processing state-changing requests.
- Include the current CSRF secret when linking or posting to `HandleLogout`.
- Use `pkg/testing.TestVerifier` for tests and local browser development without a Consent server.

## Canonical Shape

Use this package shape:

```text
internal/server/
  server.go

internal/web/
  web.go
  router.go
  auth.go

internal/service/
  service.go
  store.go
  accounts.go

internal/database/
  database.go
  migrations.go
  accounts.go
```

The ownership split should stay clear:

- `internal/server` loads runtime config, reads Consent's DER verification key, constructs the token validator, constructs the Consent client, builds the authorize URL, creates the integration manifest, and mounts auth package handlers.
- `internal/web` verifies each request, resolves the local account, renders login/logout links, includes CSRF values in forms, and passes local account IDs into service calls.
- `internal/service` defines the `Account` type, account lookup/upsert behavior, account-scoped input types, account-scoped authorization rules, and service-owned store contracts.
- `internal/database` creates the `accounts` table, implements account store methods, and enforces account ownership with foreign keys and account-scoped queries.

## Data Model

Store Consent identity separately from local account identity.

```sql
CREATE TABLE accounts (
  id TEXT PRIMARY KEY,
  consent_subject TEXT NOT NULL UNIQUE,
  handle TEXT NOT NULL,
  profile_refreshed_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE documents (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  title TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_documents_account ON documents(account_id);
```

The application may make `handle` unique when URLs or display rules require it. Even then, use `accounts.id` for ownership checks and foreign keys.

Service methods should receive the local account ID:

```go
type CreateDocumentInput struct {
	AccountID string
	Title     string
}

func (s *Service) CreateDocument(
	input CreateDocumentInput,
) (
	*Document,
	error,
) {
	input.AccountID = strings.TrimSpace(input.AccountID)
	input.Title = strings.TrimSpace(input.Title)
	if input.AccountID == "" || input.Title == "" {
		return nil, ErrInvalidInput
	}

	return s.store.CreateDocument(input.AccountID, input.Title)
}
```

Keep the Consent subject at the account boundary. Domain tables should not need to know how the user authenticated.

## Canonical Flow

The normal browser flow is:

1. `internal/server` builds the Consent auth config from resolved runtime config.
2. The route tree exposes `/auth/callback`, `/auth/logout`, and `/.well-known/consent-integration`.
3. A user visits a page that needs an account.
4. `internal/web` calls `VerifyAuthorizationGetCSRF`.
5. If verification fails, the page renders a login link or redirects to Consent's `/authorize` URL.
6. Consent authenticates the user and redirects to `/auth/callback`.
7. The Consent client exchanges the authorization code, sets cookies, and redirects back into the app.
8. `internal/web` verifies the cookies, reads `accessToken.Subject()`, and resolves a local account.
9. The app creates or updates the local account from the Consent subject and optional scoped profile data.
10. Service calls receive `account.ID`.
11. Database queries include `account_id` in reads and writes.

For state-changing requests:

1. Render the current CSRF secret from `VerifyAuthorizationGetCSRF` into the form or request URL.
2. Read the submitted CSRF value in the mutation handler.
3. Call `VerifyAuthorizationCheckCSRF`.
4. Resolve the local account from the returned access token.
5. Call the service with the local account ID.

## Canonical Example

Keep production wiring outside `internal/web`, and pass only the app-facing auth shape inward.

```go
type AuthConfig struct {
	Verifier client.Verifier
	ProfileFetcher interface {
		FetchUserInfo(accessToken string) (*client.UserInfo, error)
	}
	LoginURL  string
	LogoutURL string
}

type ConsentRuntime struct {
	BaseURL         string
	IssuerDomain   string
	Integration    string
	PublicURL      string
	VerificationKey *ecdsa.PublicKey
}

func BuildConsentAuth(
	rt ConsentRuntime,
) (
	AuthConfig,
	map[string]http.HandlerFunc,
	error,
) {
	publicURL, err := url.Parse(rt.PublicURL)
	if err != nil {
		return AuthConfig{}, nil, err
	}
	audience := publicURL.Host
	homepage := strings.TrimRight(rt.PublicURL, "/")
	callbackURL, err := url.JoinPath(homepage, "auth", "callback")
	if err != nil {
		return AuthConfig{}, nil, err
	}
	logoURL, err := url.JoinPath(homepage, "static", "consent-logo.png")
	if err != nil {
		return AuthConfig{}, nil, err
	}

	validator := tokens.InitClient(tokens.ClientOptions{
		VerificationKey: rt.VerificationKey,
		IssuerDomain:    rt.IssuerDomain,
		ValidAudience:   audience,
	})
	authClient := client.Init(validator, strings.TrimRight(rt.BaseURL, "/"))

	manifest := client.IntegrationManifest{
		Name:           rt.Integration,
		Display:        "Documents",
		Audience:       audience,
		Redirect:       callbackURL,
		Homepage:       homepage,
		Logo:           logoURL,
		ConsentIssuer:  rt.IssuerDomain,
		ConsentBaseURL: strings.TrimRight(rt.BaseURL, "/"),
	}

	return AuthConfig{
			Verifier:       authClient,
			ProfileFetcher: authClient,
			LoginURL:       buildAuthorizeURL(rt.BaseURL, rt.Integration, []string{"identity", "profile"}),
			LogoutURL:      "/auth/logout",
		},
		map[string]http.HandlerFunc{
			"/auth/callback":               authClient.HandleAuthorizationCode(),
			"/auth/logout":                 authClient.HandleLogout(),
			client.IntegrationManifestPath: client.HandleIntegrationManifest(manifest),
		},
		nil
}
```

If the app does not need profile data, omit `ProfileFetcher` and request only `identity`. In that shape, the local account can still use the Consent subject as its stable setup key, but it should not invent user-facing profile data.

## Leaf Docs

- Read `./account-resolution.md` when implementing `internal/web` auth context, account lookup, profile refresh, protected routes, and CSRF handling.
- Read `./integration-config.md` when implementing production Consent client construction, integration manifest generation, handler mounting, public URL processing, and verification-key loading.
- Read `./local-testing.md` when wiring `pkg/testing.TestVerifier`, dev auth handlers, and tests that need authenticated requests without a Consent server.
- Read `./production-deployment.md` when documenting or deploying the app with Consent registration, mounted verification keys, environment variables, reverse proxy paths, and operator checks.

## Common Touchpoints

- `../server/README.md` for serving package ownership
- `../server/composition-roots.md` for runtime wiring
- `../config/README.md` for app-side config files, resolved runtime config, and secret paths
- `../service/README.md` for service boundaries and store contracts
- `../database/README.md` for database adapter shape
- `../web/README.md` for server-rendered UI structure
- `../web/forms-and-mutations.md` for mutation handler flow
- `../routing/mounting-package-handlers.md` for mounting package-owned auth handlers
