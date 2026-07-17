# Deploying Consent-Backed Apps

This guide defines the production deployment checklist for an app that integrates with Consent.

Use it when documenting operations, preparing Docker or systemd deployment, registering the app as a Consent integration, moving the Consent verification key into the app config, or verifying that login works end to end.

Assume [consent-user-shape.md](consent-user-shape.md) already defined the app architecture and [integration-config.md](integration-config.md) already defined the production auth builder.

## Contents

- [Required Instructions](#required-instructions)
- [Deployment Inputs](#deployment-inputs)
- [App Startup](#app-startup)
- [Registering In Consent](#registering-in-consent)
- [Reverse Proxy Paths](#reverse-proxy-paths)
- [Verification Checklist](#verification-checklist)

## Required Instructions

- Treat Consent registration and app runtime config as separate deployment steps.
- Register the app in Consent before users try to authorize it.
- Deploy Consent's public verification key to the app host or container.
- Keep the Consent signing key only with the Consent server.
- Start the app with a Consent base URL, integration name, public URL, and readable verification key file.
- Make the callback route, logout route, and `/.well-known/consent-integration` reachable at their public URLs.
- Make the manifest's redirect, homepage, and logo URLs reachable through the same public host as the audience.
- Re-register or update the Consent integration when the public host, callback path, homepage, logo, integration name, or role requirements change.
- Verify the well-known manifest before cutting over login.

## Deployment Inputs

A production app needs:

```text
CONSENT_URL=https://consent.example.com
PUBLIC_URL=https://app.example.com
CONSENT_INTEGRATION=documents
CONFIG_DIR=/app/config
DATA_DIR=/app/data
```

The app config directory must contain Consent's public verification key at the path expected by the app, for example:

```text
/app/config/consent_verification_key.der
```

Consent generates that public key in its own config secrets directory, usually as:

```text
<consent-config-dir>/secrets/verification_key.der
```

Copy, mount, or symlink that DER file into the app config directory. Do not copy Consent's private signing key into the app.

## App Startup

For a binary:

```sh
CONSENT_URL=https://consent.example.com \
PUBLIC_URL=https://app.example.com \
CONSENT_INTEGRATION=documents \
CONFIG_DIR=/srv/documents/config \
DATA_DIR=/srv/documents/data \
documents serve
```

For a container:

```sh
docker run -d \
  --name documents \
  --restart unless-stopped \
  -p 8080:80 \
  -v "$PWD/data:/app/data" \
  -v "$PWD/config:/app/config:ro" \
  -e CONSENT_URL=https://consent.example.com \
  -e PUBLIC_URL=https://app.example.com \
  -e CONSENT_INTEGRATION=documents \
  documents:latest
```

The app should fail startup when production auth is selected and required Consent config or key material is missing.

## Registering In Consent

The app exposes public registration metadata at:

```text
https://app.example.com/.well-known/consent-integration
```

In the Consent admin UI, import the app from its integration root. Consent fetches the well-known manifest, validates it, and creates the integration record. The same record can be created through the Consent CLI:

```sh
consent api integrations create documents \
  --config-dir /srv/consent/config \
  --display "Documents" \
  --audience app.example.com \
  --redirect https://app.example.com/auth/callback \
  --homepage https://app.example.com \
  --logo https://app.example.com/static/consent-logo.png
```

Add `--required-roles role-name` when only users with specific Consent roles should be allowed to authorize the integration.

Registration creates public app metadata in Consent. It does not deploy the app config, set app environment variables, or copy the verification key.

## Reverse Proxy Paths

`PUBLIC_URL` may include a path when the app is served below a shared host:

```text
PUBLIC_URL=https://example.com/tools/documents
```

In that shape:

- the JWT audience is still `example.com`
- the manifest redirect should be `https://example.com/tools/documents/auth/callback`
- the manifest homepage should be `https://example.com/tools/documents`
- the proxy must route the public callback path to the app's internal `/auth/callback`
- the proxy must route the public static logo path to the app's static handler

Consent's admin import starts from an integration root and fetches `/.well-known/consent-integration`. If a pathful deployment cannot expose that well-known path at the host root, register the integration manually through the CLI with the exact public redirect, homepage, and logo URLs.

## Verification Checklist

Before enabling users:

- `GET https://app.example.com/.well-known/consent-integration` returns JSON with the expected name, audience, redirect, homepage, and logo.
- `GET <logo URL from manifest>` returns an image.
- The Consent integration record matches the manifest.
- The app process can read the deployed verification key.
- The app's `/auth/callback` route is reachable through the public redirect URL.
- The login link points to `CONSENT_URL/authorize` with the integration name and scopes.
- A first login creates a local account with `consent_subject` set to the token subject.
- A mutation with the rendered CSRF token succeeds, and a mutation with a bad CSRF token fails.
- Logout clears local cookies through the Consent package logout handler.

Keep this checklist in the app's deployment notes when the project has an operations README.
