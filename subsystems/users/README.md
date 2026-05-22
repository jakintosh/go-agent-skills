# User Accounts With Consent

This guide defines the default shape for adding user accounts to a server application with Consent.

Use it when an application needs login, per-user data, account-scoped service methods, or a server-rendered UI that protects reads and mutations with Consent-issued cookies.

Consent owns authentication, credentials, grants, roles, sessions, token refresh, and profile authority. The application owns local account records and all application data attached to those accounts.

## Owns

The user accounts subsystem owns:

- the local `accounts` table
- the mapping from Consent subject to local account ID
- cached display/profile fields needed by the application
- request authentication context in `internal/web`
- account-scoped service inputs and store methods
- account foreign keys on application-owned tables

It does not own password storage, login forms, Consent user roles, integration grants, token issuing, or profile authority.

## Required Instructions

- Use the Consent `sub` claim as the durable external identity key.
- Store a local account ID and use that ID as the foreign key for application data.
- Treat handles and profile fields as cached display data, not stable identity.
- Keep Consent client construction in `internal/server` or another composition root.
- Pass authentication into `internal/web` through a small `AuthConfig`.
- Depend on `client.Verifier` in `internal/web`, not `*client.Client`.
- Mount Consent package handlers for `/auth/callback`, `/auth/logout`, and `/.well-known/consent-integration`.
- Request the `identity` scope for account setup.
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

- `internal/server` loads the Consent verification key, constructs the token validator, constructs the Consent client, builds the authorize URL, and mounts auth handlers.
- `internal/web` verifies each request, resolves the local account, renders login/logout links, and passes local account IDs into service calls.
- `internal/service` defines the `Account` type, account lookup/upsert behavior, account-scoped input types, and service-owned store contracts.
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

The normal request flow is:

1. A user visits a page that needs an account.
2. `internal/web` calls `VerifyAuthorizationGetCSRF`.
3. If verification fails, the page renders a login link or redirects to the Consent authorize URL.
4. Consent authenticates the user and redirects to `/auth/callback`.
5. The Consent client exchanges the authorization code, sets cookies, and redirects back into the app.
6. `internal/web` verifies the cookies, reads `accessToken.Subject()`, and resolves a local account.
7. The app creates or updates the local account from the Consent subject and optional profile data.
8. Service calls receive `account.ID`.
9. Database queries include `account_id` in reads and writes.

For state-changing requests:

1. Render the current CSRF secret from `VerifyAuthorizationGetCSRF` into the form or request URL.
2. Read the submitted CSRF value in the mutation handler.
3. Call `VerifyAuthorizationCheckCSRF`.
4. Resolve the local account from the returned access token.
5. Call the service with the local account ID.

## Production Wiring

The composition root should build a Consent client and pass only the needed interfaces into `internal/web`.

```go
type AuthConfig struct {
	Verifier client.Verifier
	ProfileFetcher interface {
		FetchUserInfo(accessToken string) (*client.UserInfo, error)
	}
	LoginURL  string
	LogoutURL string
}

func buildAuthConfig(
	publicKey *ecdsa.PublicKey,
	consentURL string,
	consentIssuer string,
	publicURL string,
	integrationName string,
) (
	AuthConfig,
	map[string]http.HandlerFunc,
	error,
) {
	appURL, err := url.Parse(publicURL)
	if err != nil {
		return AuthConfig{}, nil, err
	}
	audience := appURL.Host

	validator := tokens.InitClient(tokens.ClientOptions{
		VerificationKey: publicKey,
		IssuerDomain:    consentIssuer,
		ValidAudience:   audience,
	})
	authClient := client.Init(validator, consentURL)

	homepage := strings.TrimRight(publicURL, "/")
	manifest := client.IntegrationManifest{
		Name:           integrationName,
		Display:        "Documents",
		Audience:       audience,
		Redirect:       homepage + "/auth/callback",
		Homepage:       homepage,
		Logo:           homepage + "/static/consent-logo.png",
		ConsentIssuer:  consentIssuer,
		ConsentBaseURL: consentURL,
	}

	return AuthConfig{
			Verifier:       authClient,
			ProfileFetcher: authClient,
			LoginURL:       buildAuthorizeURL(consentURL, integrationName, []string{"identity", "profile"}),
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

## Account Resolution

Resolve the local account after token verification. Create the local account lazily on first successful login.

```go
type AuthContext struct {
	IsAuthenticated bool
	AccountID       string
	Subject         string
	Handle          string
	CSRFToken       string
	LoginURL        string
	LogoutURL       string
}

func (w *Web) resolveAuthContext(
	rw http.ResponseWriter,
	r *http.Request,
) (
	AuthContext,
	error,
) {
	ctx := AuthContext{
		LoginURL:  w.loginURL(r),
		LogoutURL: w.auth.LogoutURL,
	}

	accessToken, csrf, err := w.auth.Verifier.VerifyAuthorizationGetCSRF(rw, r)
	if err != nil {
		return ctx, nil
	}

	account, err := w.accountForToken(accessToken)
	if err != nil {
		return ctx, err
	}

	ctx.IsAuthenticated = true
	ctx.Subject = accessToken.Subject()
	ctx.AccountID = account.ID
	ctx.Handle = account.Handle
	ctx.CSRFToken = csrf
	ctx.LogoutURL = logoutURL(w.auth.LogoutURL, csrf)
	return ctx, nil
}

func logoutURL(
	base string,
	csrf string,
) string {
	if base == "" || csrf == "" {
		return base
	}
	u, err := url.Parse(base)
	if err != nil {
		return base
	}
	q := u.Query()
	q.Set("csrf", csrf)
	u.RawQuery = q.Encode()
	return u.String()
}
```

Account setup should use the subject first and profile data second:

```go
func (w *Web) accountForToken(
	accessToken *client.AccessToken,
) (
	*service.Account,
	error,
) {
	subject := accessToken.Subject()

	account, err := w.service.GetAccountBySubject(service.GetAccountBySubjectInput{
		Subject: subject,
	})
	if err == nil && !w.shouldRefreshProfile(account) {
		return account, nil
	}
	if err != nil && !errors.Is(err, service.ErrNotFound) {
		return nil, err
	}

	handle := subject
	refreshedAt := time.Now()
	if w.auth.ProfileFetcher != nil {
		userInfo, err := w.auth.ProfileFetcher.FetchUserInfo(accessToken.Encoded())
		if err != nil {
			if account != nil {
				return account, nil
			}
			return nil, err
		}
		if userInfo == nil || userInfo.Sub != subject || userInfo.Profile == nil {
			return nil, ErrAccountSetup
		}
		handle = strings.TrimSpace(userInfo.Profile.Handle)
		if handle == "" {
			return nil, ErrAccountSetup
		}
	}

	return w.service.UpsertAccount(service.UpsertAccountInput{
		Subject:     subject,
		Handle:      handle,
		RefreshedAt: refreshedAt,
	})
}
```

If profile refresh fails for an existing account, keep using the cached account. If profile fetch fails for a new account that requires profile data, show an account setup error.

## Protected Routes

Use a helper for mutation routes so authorization, CSRF, and account resolution stay consistent.

```go
func (w *Web) requireAuth(
	rw http.ResponseWriter,
	r *http.Request,
) (
	AuthContext,
	bool,
) {
	csrf := r.FormValue("csrf")
	if csrf == "" {
		csrf = r.URL.Query().Get("csrf")
	}

	accessToken, newCSRF, err := w.auth.Verifier.VerifyAuthorizationCheckCSRF(rw, r, csrf)
	if errors.Is(err, client.ErrCSRFInvalid) {
		http.Error(rw, "CSRF validation failed", http.StatusForbidden)
		return AuthContext{}, false
	}
	if err != nil {
		http.Error(rw, "Unauthorized", http.StatusUnauthorized)
		return AuthContext{}, false
	}

	account, err := w.accountForToken(accessToken)
	if err != nil {
		w.renderAccountSetupError(rw, r, err)
		return AuthContext{}, false
	}

	return AuthContext{
		IsAuthenticated: true,
		Subject:         accessToken.Subject(),
		AccountID:       account.ID,
		Handle:          account.Handle,
		CSRFToken:       newCSRF,
		LoginURL:        w.loginURL(r),
		LogoutURL:       logoutURL(w.auth.LogoutURL, newCSRF),
	}, true
}
```

Use `auth.CSRFToken` for application mutation forms. Use `auth.LogoutURL` for logout controls wired to Consent's package logout handler.

Handlers should call the service with `auth.AccountID`:

```go
func (w *Web) handleCreateDocument(
	rw http.ResponseWriter,
	r *http.Request,
) {
	auth, ok := w.requireAuth(rw, r)
	if !ok {
		return
	}

	input := service.CreateDocumentInput{
		AccountID: auth.AccountID,
		Title:     r.FormValue("title"),
	}
	doc, err := w.service.CreateDocument(input)
	if err != nil {
		w.writeError(rw, err)
		return
	}

	http.Redirect(rw, r, "/documents/"+url.PathEscape(doc.ID), http.StatusSeeOther)
}
```

## Integration Registration

Every production app must expose a Consent integration manifest:

```go
root.HandleFunc(client.IntegrationManifestPath, client.HandleIntegrationManifest(manifest))
```

The manifest tells Consent the app name, display name, audience, redirect URL, homepage URL, logo URL, Consent issuer, and Consent base URL. The app's `audience` should normally be its public host. The redirect and homepage hosts must match that audience.

Operators can register the app by importing:

```text
https://app.example.com/.well-known/consent-integration
```

The app must also receive Consent's DER verification key out of band, usually by mounting or copying the generated verification key into the app's config directory.

## Development And Testing

For local browser development without a Consent server, use `pkg/testing` and mount dev-only handlers.

```go
tv := testing.NewTestVerifier("localhost", "documents-dev")

auth := AuthConfig{
	Verifier:  tv,
	LoginURL:  "/dev/login",
	LogoutURL: "/dev/logout",
}

root.HandleFunc("/dev/login", tv.HandleDevLogin())
root.HandleFunc("/dev/logout", tv.HandleDevLogout())
```

For tests, inject `client.Verifier` into `internal/web` and pass a `TestVerifier`.

```go
func TestProtectedRoute(t *testing.T) {
	tv := testing.NewTestVerifier("consent.example.com", "documents.example.com")
	web := NewTestWeb(t, tv)

	req, err := tv.AuthenticatedRequest("GET", "/documents", testing.DefaultTestSubject)
	if err != nil {
		t.Fatal(err)
	}
	rr := httptest.NewRecorder()

	web.Handler().ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rr.Code, http.StatusOK)
	}
}
```

This keeps tests local: no Consent server, no network token refresh, and no production key material.

## Common Touchpoints

- `../server/README.md` for serving package ownership
- `../server/composition-roots.md` for runtime wiring
- `../service/README.md` for service boundaries and store contracts
- `../database/README.md` for database adapter shape
- `../web/README.md` for server-rendered UI structure
- `../web/forms-and-mutations.md` for mutation handler flow
- `../routing/mounting-package-handlers.md` for mounting package-owned handlers
