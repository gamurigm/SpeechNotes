# Tauri Desktop Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` for native execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Electron desktop runtime with a production Windows Tauri app while preserving SpeechNotes behavior.

**Architecture:** Tauri Rust supervises a bundled FastAPI backend and a bundled Node runtime serving the existing Next.js standalone app on loopback. The frontend invokes one narrow Rust command for the existing external-browser OAuth handoff. Keep Electron files until the Tauri installer passes production acceptance, then remove the old runtime and update active docs and launch scripts.

**Tech Stack:** Tauri 2.11, Rust, Next.js standalone, Node.js 22+, FastAPI/PyInstaller, Prisma/SQLite, Windows NSIS.

**Spec:** `docs/superpowers/specs/2026-09-30-tauri-desktop-migration-design.md`

## Tauri References

- [Configuration reference](https://v2.tauri.app/reference/config/) — supports a remote frontend URL and bundled resources.
- [Capabilities](https://tauri.app/security/capabilities/) — remote origins receive Tauri access only through explicit capabilities.

## Global Constraints

- Target Windows production packaging first; keep the Next.js server because the app uses NextAuth, Prisma, API routes, and FastAPI rewrites.
- Production backend and frontend bind only to `127.0.0.1`; ports remain 9443 and 3006.
- Bundle Node and the PyInstaller backend so installed use does not depend on system Node.js or Python.
- Never copy `.env` files, workspace `dev.db`, or API secrets into Tauri resources.
- Store runtime SQLite files in Tauri per-user app data; migrate Electron's existing `speechnotes.db` only when the new destination does not exist.
- Keep Electron until Tauri production checks pass. Leave Cypress' Electron browser dependency because it is only the current E2E browser.
- Preserve existing local changes in `.env.example`, `README.md` (model default), `backend/services/agents/pydantic_agent.py`, `web/app/dashboard/page.tsx`, `web/app/dashboard/components/LogoutButton.tsx`, and `desktop/electron/main.js`; merge README launch-doc updates without replacing its model change and stage only files belonging to a task.

## Files and Responsibilities

- `backend.spec`: tracked PyInstaller definition with import paths rooted at the repository so clean builds include `backend.*` modules.
- `.gitignore`: track `backend.spec`; ignore generated Tauri resources/build output.
- `web/scripts/prepare-tauri-resources.mjs`: build/copy standalone Next, Node, backend, Prisma migrations/CLI resources while excluding env files.
- `web/scripts/prepare-tauri-resources.test.mjs`: Node built-in tests for resource copying and env-file exclusion.
- `web/prisma/migrations/**`: initial versioned schema and future production database upgrades.
- `web/src-tauri/src/runtime.rs`: production/dev service startup, port and HTTP readiness checks, process ownership, data paths, and shutdown.
- `web/src-tauri/src/google_auth.rs`: loopback callback validation and one-time browser sign-in handoff.
- `web/src-tauri/src/lib.rs`: register Tauri commands, plugins, managed runtime state, and shutdown handling.
- `web/src-tauri/tauri.conf.json`, `web/src-tauri/capabilities/default.json`: app identity, local frontend URL, Windows bundle resources, and exact loopback command capability.
- `web/app/login/page.tsx`, `web/types/tauri.d.ts`: use Tauri's typed invoke path for desktop Google sign-in while leaving browser login unchanged.
- `web/package.json` and `web/package-lock.json`: Tauri API dependency and desktop scripts.
- `run_all.ps1`, `README.md`: start and document the Tauri development and production flows.
- `desktop/`: remove Electron runtime/package only after the installer passes acceptance.

## Review Focus

- Port 3006 or 9443 already has a listener: assert startup fails clearly and never loads an unrelated dev server.
- A packaged child executable is missing or exits early: assert startup reports the failing service and closes any child already started.
- Resource staging sees `.env`, `.env.*`, or a workspace database: assert secrets and development data are excluded.
- OAuth callback has a wrong host/path, duplicate or missing code/state, or mismatched state: assert it is rejected and no session code is returned.
- App exit or failed startup occurs after one service starts: assert owned processes are stopped and per-user database files are retained.

## Implementation Tasks

### Task 1: Make backend and Tauri runtime resources reproducible

- [ ] Add Node built-in test `prepare resources excludes env files and copies required runtime assets` in `web/scripts/prepare-tauri-resources.test.mjs`. Use a temporary fixture with `server.js`, `.next/static`, `public`, `.env`, `.env.production`, and `nested/.env`; assert required files are copied and every env file is absent.
- [ ] Add a temporary resource-copy helper that copies all files; run `node --test scripts/prepare-tauri-resources.test.mjs` from `web` and confirm the assertion fails because `.env` is copied.
- [ ] Track the existing root `backend.spec` by adding `!/backend.spec` after the `*.spec` ignore rule. Remove its ignored runtime-hook dependency and resolve the project root from `SPECPATH` for both the analysis entry point and `pathex`.
- [ ] Implement an exported resource-copy helper in `web/scripts/prepare-tauri-resources.mjs`; make it copy the Next standalone output, `.next/static`, `public`, Node from `process.execPath`, and PyInstaller output into `web/src-tauri/resources`, filtering `.env*` files at every depth.
- [ ] Add the initial Prisma migration generated from `web/prisma/schema.prisma`. Include the migration directory and the Prisma CLI/engine files needed to run `prisma migrate deploy` against the per-user auth database.
- [ ] Make the staging command run PyInstaller from repository root with explicit build/dist paths, then stage backend and frontend assets. Add generated resources to `.gitignore`.
- [ ] Run `node --test scripts/prepare-tauri-resources.test.mjs`; expect PASS. Run the resource staging command; inspect only file names to confirm `server.js`, `node.exe`, backend executable, and migration are present and no `.env`/`dev.db` is present.

### Task 2: Add Tauri process supervision and local data setup

- [ ] Add Rust test `startup_rejects_an_occupied_service_port` for the loopback port preflight helper; assert port 3006 and 9443 are rejected while a test listener owns them. Start with a stub that accepts occupied ports, run `cargo test` from `web/src-tauri`, and confirm the assertion fails.
- [ ] Implement `DesktopRuntime` in `web/src-tauri/src/runtime.rs`. In release, resolve Tauri resources, ensure app-data directories exist, migrate legacy `speechnotes.db` only if the target is absent, run bundled Prisma migrations with the bundled Node runtime, and spawn backend and Next standalone child processes.
- [ ] In debug, spawn the repository `.venv` backend and let Tauri's dev command run Next.js. Pass `SQLITE_DB_DIR`, `DATABASE_URL`, `HOST`, `PORT`, and `HOSTNAME` as appropriate without writing secrets to logs.
- [ ] Before spawning, fail if 3006 or 9443 is occupied. After spawning, require both child processes to remain alive and pass HTTP health checks (`/health` and `/login`) before permitting the window to load.
- [ ] Store child handles in Tauri-managed state; stop children on startup failure and `RunEvent::Exit`. Forward output to Tauri logs with environment values redacted.
- [ ] Configure `tauri.conf.json` with identifier `com.speechnotes.desktop`, version `1.0.0`, frontend URL `http://localhost:3006`, resource mappings, and Windows NSIS target. Do not auto-create a window from config; configure the 1400x900 window from Rust only after both health checks pass.
- [ ] Add the Tauri dialog plugin for a visible startup error, and limit the remote capability to `http://localhost:3006` and the desktop auth command.
- [ ] Register runtime setup and exit cleanup from `lib.rs`. Run `cargo test`; expect PASS. Run `cargo check` and `npm run build` from `web`; expect both to pass.

### Task 3: Route development startup through Tauri

- [ ] Add scripts `tauri:dev`, `tauri:build`, and `tauri:resources` in `web/package.json`; add `@tauri-apps/api` and refresh `web/package-lock.json` using npm.
- [ ] Set Tauri `beforeDevCommand` to `npm run dev` and `devUrl` to `http://localhost:3006`.
- [ ] Update `run_all.ps1` to retain its MongoDB precheck and start `npm run tauri:dev` from `web`; remove separate backend/frontend windows and broad process/port killing because Tauri now owns its backend and reports port conflicts.
- [ ] Launch `run_all.ps1` and confirm a single Tauri window uses the Next dev server and its own backend; close it and confirm neither process remains.

### Task 4: Port the desktop Google sign-in handoff

- [ ] Add Rust unit tests for valid callback acceptance and rejection of wrong method, origin, path, duplicate/missing parameters, oversized code, and wrong state. Use a permissive validator stub first and confirm assertions fail before implementing validation.
- [ ] Implement `start_google_auth` in `web/src-tauri/src/google_auth.rs`: bind an ephemeral listener on `127.0.0.1`, register its callback with `POST http://localhost:3006/api/auth/desktop/start` using `reqwest`, open the existing login URL with the Rust opener plugin, await the matching callback for at most three minutes, then close the listener.
- [ ] Initialize the Tauri opener plugin in Rust and restrict the callback command to the configured local app origin; do not expose general-purpose shell execution.
- [ ] Change `web/app/login/page.tsx` to detect Tauri with `isTauri()` and call `invoke('start_google_auth')`; keep the existing NextAuth web login branch for normal browsers. Replace `web/types/electron.d.ts` with Tauri typings only if required by the implementation.
- [ ] Run the focused Rust callback tests and `npm run build`; expect PASS. Manually complete Google sign-in in the Tauri dev app and confirm the desktop session opens at `/`.

### Task 5: Build and verify the production Tauri app, then retire Electron

- [ ] Run `npm run tauri:build` from `web`; confirm NSIS output is created and inspect the staged resources to confirm `.env*`, `dev.db`, and API secrets are absent.
- [ ] Install and launch the packaged app with system Node.js/Python unavailable from `PATH`. Confirm its own child processes serve `/health` and `/login`, and confirm password and Google sign-in.
- [ ] Record a short sample, confirm the existing live transcription cadence, press Stop, and confirm final text appears in the Markdown viewer. Close the app and confirm its owned processes stop and SQLite files remain under Tauri app data.
- [ ] Launch with port 3006 occupied; confirm the app reports the collision and does not open the unrelated server.
- [ ] Only after all acceptance checks pass, remove `desktop/electron/`, Electron-only package/lock/debug files, the Electron login declaration/branch, and stale Electron desktop runtime instructions. Keep the PyInstaller definition used by Tauri.
- [ ] Update README and active launch scripts to document Tauri dev and Windows production build. Review remaining `Electron` references; retain only Cypress' E2E browser dependency and historical design/report material.
- [ ] Run final `cargo test`, `cargo check`, `npm run build`, and `npm run tauri:build`; report any existing failures by command and exact output.

## Execution Recommendation

**Native execution** is recommended: these tasks share the same Tauri resource layout and runtime interfaces, and implementation order is strictly sequential through production acceptance before Electron removal.
