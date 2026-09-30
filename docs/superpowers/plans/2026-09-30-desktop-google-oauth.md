# Desktop Google OAuth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let SpeechNotes Desktop complete Google sign-in in the system browser and establish a normal NextAuth session inside Electron.

**Architecture:** Electron creates a loopback callback listener and registers it with the local Next.js server before opening the system browser. NextAuth authenticates Google in that browser, then issues a short-lived one-time code for the authenticated user; Electron redeems the code through a credentials provider to create its own JWT session.

**Tech Stack:** Electron 33, Next.js 16, NextAuth 4, Node.js HTTP and crypto.

**Spec:** `docs/superpowers/specs/2026-09-30-desktop-google-oauth-design.md`

## Global Constraints

- The callback listener binds only to `127.0.0.1` and accepts one callback.
- The server stores only a hash of each handoff code; it is state-bound and expires after two minutes.
- The completion route validates the callback address and must not allow arbitrary redirects.
- No provider secrets or reusable session tokens go in the callback URL.
- Normal browser Google sign-in and credentials sign-in remain unchanged.
- Always close the local listener after success, failure, timeout, or window shutdown.
- The in-memory handoff map is capped at 32 active entries and is local to one Next.js process; pending states expire after three minutes and handoff codes after two minutes.

## Review Focus

- Callback URL tampering or non-loopback targets: the start route rejects targets other than `http://127.0.0.1:<port>/callback`.
- Wrong, missing, expired, or replayed state/code: completion and redemption fail without creating a session.
- User denies Google consent or closes the browser: Electron times out, reports the failure, and closes its listener.
- Google credentials are absent: Google sign-in remains unavailable while credentials sign-in remains usable.
- Standard browser login: the ordinary Google button keeps its existing callback and session behavior.

---

### Task 1: NextAuth handoff request and code redemption

**Files:**
- Create: `web/lib/desktop-auth-handoff.ts`
- Create: `web/app/api/auth/desktop/start/route.ts`
- Create: `web/app/desktop/auth/complete/route.ts`
- Modify: `web/lib/auth.ts`

**Interfaces:**
- `registerDesktopAuthRequest(callbackUrl: string): { state: string }` validates and stores the callback and a three-minute state expiry in a process-local map; returns a random state while storing its hash.
- `completeDesktopAuthRequest(state: string, userId: string): { callbackUrl: string; code: string } | null` issues a random code only for a live, unused state and stores only its hash.
- `consumeDesktopAuthCode(code: string, state: string): Promise<{ id: string; email: string | null; name: string | null } | null>` consumes a matching live code once and returns its user.
- `POST /api/auth/desktop/start` accepts `{ callbackUrl }`, calls the register function, and responds `{ state }`.
- `GET /desktop/auth/complete?state=...` requires an active NextAuth session and redirects only to the callback stored for that state.
- NextAuth credentials provider id `desktop-google` accepts `code` and `state`, calls `consumeDesktopAuthCode`, and returns the existing user for the JWT session strategy.

- [ ] Implement the bounded process-local map in `web/lib/desktop-auth-handoff.ts` on a `globalThis` singleton so App Router handlers share it; use SHA-256 hashes for state and code lookups, 32 active entries maximum, three-minute state expiry, two-minute code expiry, and opportunistic cleanup. Add the spec's `ponytail:` ceiling comment.
- [ ] Validate callback URLs at the trust boundary: allow only `http:`, host `127.0.0.1`, a valid nonzero port, path `/callback`, and no credentials, query, or fragment.
- [ ] Implement `POST /api/auth/desktop/start` and the authenticated completion route. Reject invalid, expired, and duplicate states; never redirect to a callback supplied by the completion request.
- [ ] Add the `desktop-google` credentials provider without changing existing Google or username/password provider behavior.
- [ ] Review the implementation against the wrong-state, expiry, replay, missing-Google-credentials, and normal-browser cases in Review Focus.
- [ ] Commit as `feat(auth): add one-time desktop login handoff`.

### Task 2: Electron system-browser callback

**Files:**
- Modify: `desktop/electron/main.js`
- Modify: `desktop/electron/preload.js`

**Interfaces:**
- Expose `startGoogleAuth(): Promise<{ code: string; state: string }>` through preload, backed by IPC channel `google-auth:start`.
- Main process handler starts an HTTP server on `127.0.0.1` port `0`, registers `http://127.0.0.1:<assigned-port>/callback` through the start route, and opens `http://localhost:3006/login?desktop_state=<state>` with `shell.openExternal`.
- The callback listener accepts one GET `/callback`, verifies the registered state, returns a short “return to SpeechNotes” page, and resolves the IPC call with `{ code, state }`.

- [ ] Add the `google-auth:start` IPC handler and preload method; import Electron `ipcMain` and `shell`.
- [ ] Bind the listener to loopback on an ephemeral port and register its exact URL with `POST /api/auth/desktop/start` before opening the external browser.
- [ ] Wait at most three minutes for one valid callback; ignore invalid paths, methods, and states without resolving the login.
- [ ] Close the listener after success, timeout, browser-launch failure, a repeated start, or app shutdown; never log callback codes.
- [ ] Return distinct errors for browser-launch failure and timeout.
- [ ] Commit as `feat(desktop): open Google sign-in in the system browser`.

### Task 3: Connect the login UI to desktop handoff

**Files:**
- Modify: `web/app/login/page.tsx`
- Create: `web/types/electron.d.ts`

**Interfaces:**
- In Electron, the Google button awaits `window.electronAPI.startGoogleAuth()` and calls `signIn('desktop-google', { code, state, redirect: false, callbackUrl: '/' })`.
- In a normal browser, the button retains `signIn('google', { callbackUrl: '/' })`.
- In the external browser, `?desktop_state=...` makes Google sign-in use `/desktop/auth/complete?state=<encoded state>` as its callback URL.

- [ ] Add the ambient `window.electronAPI.startGoogleAuth` type and branch the Google button on its presence.
- [ ] Use the desktop completion callback only when `desktop_state` is present; leave normal browser callback behavior unchanged.
- [ ] Show useful pending and error feedback for browser launch, timeout (including a denied or abandoned browser login), and failed handoff; allow retry.
- [ ] Confirm the successful flow redirects Electron to `/` and leaves the external browser on a completion page; review the normal web login path and the failure cases in Review Focus.
- [ ] Commit as `feat(auth): connect Electron Google sign-in`.
