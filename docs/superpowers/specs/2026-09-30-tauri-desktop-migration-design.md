# Tauri Desktop Migration Design

## Goal

Replace the Electron desktop runtime with a production-ready Tauri desktop app on Windows while preserving SpeechNotes' existing Next.js UI, FastAPI backend, Google sign-in, recording, transcription, and Markdown handoff.

## Current state

- `run_all.ps1` starts the backend and Next.js dev server, then attempts `pnpm tauri dev`.
- `web/src-tauri` is a minimal Tauri 2 shell. Its config points at `web/out`, but Next.js is configured for standalone server output and uses server routes for auth and API behavior.
- The Rust entry point only opens a window; it does not supervise the backend or frontend.
- The current Electron app starts a PyInstaller backend and a Next.js standalone server in production.
- Google desktop sign-in depends on Electron's loopback callback and IPC handoff. The web app already has server endpoints that register and complete this handoff.
- Electron is still referenced by `desktop/`, the login UI/type declarations, and README instructions. Cypress also uses its bundled Electron browser for E2E; that is a test runner, not the desktop runtime.

## Selected architecture

Keep the existing web and backend architecture. Do not convert Next.js to static export: API routes, NextAuth, Prisma, and the current rewrite to the FastAPI service require a server.

The Tauri Rust process owns the production service lifecycle. It starts the bundled PyInstaller backend and a bundled Node runtime running the Next.js standalone server, waits until both child processes and their HTTP endpoints are ready, then opens the app at the local Next.js URL. It stops both owned child processes when the desktop app exits. The frontend and backend listen only on loopback. If a required port is already occupied or a child exits during startup, Tauri reports a startup error and does not attach to another process such as a dev server.

The production bundle includes the standalone Next.js output, a Node executable, and the backend executable. Both the NextAuth Prisma database and backend SQLite data live in Tauri's per-user app data directory. Initialize the auth database from versioned Prisma schema migrations; never bundle the workspace `dev.db`. On first run, preserve the existing Electron backend settings database if it exists and the Tauri destination does not. The bundle does not include `.env` files or API secrets; server-only configuration is supplied at runtime through the user's environment/configuration.

Because the window loads the local Next.js HTTP server, configure Tauri's remote-origin capability for only the exact loopback app origin and only the desktop command needed by Google sign-in. Do not grant that capability to arbitrary websites or expose a general-purpose shell command.

Move the desktop Google sign-in handoff into a narrowly scoped Tauri command. It creates an ephemeral loopback callback, validates the HTTP method, host, path, code, and state, registers the callback with the existing Next.js endpoint, opens the system browser, and returns the validated code and state to the login page. The existing one-time server-side code exchange remains the authority for creating the app session. The command has a three-minute timeout and closes its callback listener on success, failure, cancellation, or app shutdown. No generic shell command is exposed to the webview.

Use the existing Tauri window and invoke APIs; remove the `electronAPI` login branch and its TypeScript declaration when switching the login UI. No other Electron bridge methods are currently used by the web UI.

## Migration stages

1. **Production runtime:** configure Windows Tauri packaging, prepare the standalone frontend, Node runtime, and backend as resources, and implement child process startup, readiness, error reporting, and shutdown.
2. **Desktop sign-in:** port the validated external-browser OAuth callback handoff to a Tauri command and switch the login page to it.
3. **Retire Electron:** only after the Tauri installer passes the acceptance checks, remove the Electron app/package, obsolete desktop login bridge/type, Electron launch instructions, and stale app-runtime references. Keep Cypress' Electron browser dependency unless its E2E runner is separately migrated.

## Failure handling and security

- Bind local services and OAuth callback listeners to `127.0.0.1` only.
- Never ship local `.env` files or hard-code API secrets into the installer.
- Validate OAuth callback origin, exact path, query cardinality, code length, and unpredictable state before returning credentials to the webview.
- Fail with a useful startup message if a required resource is absent, a service child exits, a health check fails, or a port is occupied. Do not silently use an unrelated process already listening on that port.
- Capture service startup output in application logs without exposing environment values.
- Always terminate only child processes started by this Tauri instance.

## Acceptance criteria

- A Windows production installer starts SpeechNotes without requiring system Node.js or Python.
- The packaged Tauri app starts its own backend and Next.js server, passes explicit health checks for both, and loads the login page.
- A clean install initializes its per-user auth database without copying a development database or `.env` file into the installer.
- Existing username/password sign-in and Google sign-in through the system browser work and establish a session in the desktop window.
- A recording receives the existing live transcription updates; Stop finalizes the recording and displays the Markdown document.
- Closing the app terminates its owned backend and frontend processes. Local SQLite data remains in the per-user app data directory.
- A port collision or missing service resource is reported without opening the wrong server.
- Tauri's production build produces a Windows installer that passes the checks above before Electron runtime files are removed.

## Scope boundaries

- This migration targets Windows production packaging first, matching the current desktop packaging request. macOS, Linux, and mobile Tauri packaging are not part of the first production acceptance gate.
- The Next.js user interface, FastAPI contracts, AI service integrations, and OAuth server routes remain in place.
- Rewriting the UI as a static export or native Rust frontend is out of scope.
- Electron removal happens after Tauri reaches production parity, so the existing desktop implementation remains available during the transition.
