# Desktop Google OAuth design

## Goal

Let a user sign in to SpeechNotes Desktop with Google while keeping Google authentication in the user's default browser. Google blocks OAuth requests displayed in embedded user agents, including Electron windows. The existing `select_account` prompt only selects an account after Google accepts the client.

## Selected flow

1. In Electron, the Google button asks the main process to create a short-lived HTTP callback listener bound to `127.0.0.1` on an ephemeral port. The main process registers its callback URL with Next.js, which generates and returns a cryptographically random state value.
2. Electron opens the existing SpeechNotes login page in the system browser with that state. Google OAuth and the existing NextAuth callback continue to run in that browser, using the existing server-side Google credentials.
3. After NextAuth has created the browser session, a desktop completion route issues a random, short-lived handoff code for the authenticated user. The Next.js process stores only hashes of state and code, binds the code to the state, and expires it after two minutes.
4. The completion page redirects to the validated loopback callback with the code and state. The listener checks the state and passes the code to Electron over IPC.
5. Electron calls a dedicated NextAuth credentials provider with the code. The provider atomically consumes the unexpired code and returns its associated user; NextAuth then creates its normal JWT session cookie inside Electron.

The loopback callback must accept only `127.0.0.1`, the expected path, the expected state, and one callback. The completion route must use the callback address registered at flow start and must not allow arbitrary redirects. Store no Google access or refresh token for this sign-in handoff. Normal browser Google sign-in remains unchanged.

Keep pending requests and codes in a process-local map capped at 32 active entries, with a two-minute lifetime and opportunistic expiry cleanup. This desktop flow runs through one local Next.js server process; process restart invalidates outstanding attempts, which can be retried. `ponytail:` keep handoffs process-local; use shared storage only if this flow later needs to span Next.js processes or machines.

## Files and data

- `desktop/electron/main.js` and `desktop/electron/preload.js`: start/stop the callback listener, open the system browser, and deliver the result through a narrow IPC API.
- `web/app/login/page.tsx` and a small desktop completion route: select the desktop callback URL and return a successful handoff to Electron.
- `web/lib/auth.ts` and a handoff helper/API route: issue and consume one-time codes while using the existing NextAuth JWT session strategy.

## Failure behavior

Show a clear error in the desktop login UI if the external browser cannot be opened, the user cancels or denies access, the callback times out, the state is wrong, or the code has expired or was already used. Always close the local listener after success, failure, timeout, or window shutdown. Never put provider secrets or reusable session tokens in the callback URL.

## Acceptance criteria

- Google account selection and consent happen in the system browser, not Electron's embedded window.
- A successful browser sign-in establishes the same authenticated user in the Electron window.
- Existing web Google sign-in and credentials sign-in still work.
- Handoff codes are short-lived, bound to state, stored hashed in memory, and usable once.
- Invalid, expired, replayed, or mismatched codes cannot create an Electron session.
- The app returns to a useful state if the browser is closed or authentication is denied.

## Alternatives considered

- Keep Google OAuth in Electron and alter its user agent: rejected because Google explicitly disallows embedded user agents.
- Open the current web login in an external browser without a handoff: rejected because its session cookie belongs to that browser and does not authenticate Electron.
- Remove Google sign-in from desktop: rejected because it would not meet the requested desktop login behavior.
- Persist handoff codes in SQLite: rejected because this flow is confined to one local server process and the repository has no Prisma migration workflow.
