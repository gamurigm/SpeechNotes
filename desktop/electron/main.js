/**
 * SpeechNotes Desktop - Electron Main Process (CJS)
 */

const { app, BrowserWindow, dialog, ipcMain, shell, safeStorage, net: electronNet } = require('electron');
const path = require('node:path');
const { spawn } = require('node:child_process');
const net = require('node:net');
const http = require('node:http');

// ---------------------------------------------------------------------------
// Paths (differ between dev and packaged)
// ---------------------------------------------------------------------------

const isDev = !app.isPackaged;

function resourcePath(...segments) {
    if (isDev) {
        return path.join(__dirname, '..', ...segments);
    }
    return path.join(process.resourcesPath, ...segments);
}

const BACKEND_PORT = 9443; 
const FRONTEND_PORT = 3006;

let backendProcess = null;
let frontendProcess = null;
let mainWindow = null;
let activeGoogleAuth = null;

// ---------------------------------------------------------------------------
// Utility: wait for a TCP port to be listening
// ---------------------------------------------------------------------------

function waitForPort(port, host = '127.0.0.1', timeout = 60000) {
    return new Promise((resolve, reject) => {
        const deadline = Date.now() + timeout;

        function tryConnect() {
            if (Date.now() > deadline) {
                return reject(new Error(`Timeout waiting for port ${port}`));
            }
            const socket = net.connect(port, host);
            socket.once('connect', () => {
                socket.destroy();
                console.log(`[Electron] Port ${port} on ${host} is ready!`);
                resolve();
            });
            socket.once('error', () => {
                socket.destroy();
                setTimeout(tryConnect, 1000);
            });
        }

        tryConnect();
    });
}

function finishGoogleAuth(auth, error, result) {
    if (activeGoogleAuth !== auth) return;
    activeGoogleAuth = null;
    if (auth.timeout) clearTimeout(auth.timeout);
    if (auth.server?.listening) auth.server.close();
    if (error) auth.reject(error);
    else auth.resolve(result);
}

function startGoogleAuth() {
    if (activeGoogleAuth) {
        finishGoogleAuth(activeGoogleAuth, new Error('Google sign-in restarted'));
    }

    return new Promise((resolve, reject) => {
        const auth = { resolve, reject, server: null, state: null, callbackUrl: null, timeout: null };
        activeGoogleAuth = auth;
        auth.server = http.createServer((req, res) => {
            let requestUrl;
            try {
                requestUrl = new URL(req.url || '/', auth.callbackUrl || 'http://127.0.0.1');
            } catch {
                res.writeHead(400, { 'Cache-Control': 'no-store' }).end('Invalid authentication response.');
                return;
            }

            const callbackOrigin = auth.callbackUrl ? new URL(auth.callbackUrl).origin : null;
            const codeValues = requestUrl.searchParams.getAll('code');
            const stateValues = requestUrl.searchParams.getAll('state');
            const code = codeValues[0];
            const state = stateValues[0];
            if (
                req.method !== 'GET' ||
                requestUrl.pathname !== '/callback' ||
                requestUrl.origin !== callbackOrigin ||
                req.headers.host !== new URL(auth.callbackUrl).host ||
                codeValues.length !== 1 ||
                stateValues.length !== 1 ||
                !code ||
                code.length > 128 ||
                !auth.state ||
                state !== auth.state
            ) {
                res.writeHead(400, { 'Cache-Control': 'no-store' }).end('Invalid authentication response.');
                return;
            }

            res.writeHead(200, {
                'Content-Type': 'text/plain; charset=utf-8',
                'Cache-Control': 'no-store',
            }).end('Google sign-in complete. You can return to SpeechNotes.');
            finishGoogleAuth(auth, null, { code, state });
        });

        auth.server.on('error', error => finishGoogleAuth(auth, error));
        auth.server.listen(0, '127.0.0.1', async () => {
            const address = auth.server.address();
            if (!address || typeof address === 'string') {
                finishGoogleAuth(auth, new Error('Could not start the sign-in callback.'));
                return;
            }

            auth.callbackUrl = `http://127.0.0.1:${address.port}/callback`;
            try {
                const origin = `http://localhost:${FRONTEND_PORT}`;
                const response = await fetch(`${origin}/api/auth/desktop/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ callbackUrl: auth.callbackUrl }),
                    signal: AbortSignal.timeout(5000),
                });
                if (!response.ok) throw new Error('Could not register the sign-in callback.');

                const payload = await response.json();
                if (typeof payload.state !== 'string' || payload.state.length > 128) {
                    throw new Error('Could not register the sign-in callback.');
                }
                auth.state = payload.state;
                auth.timeout = setTimeout(
                    () => finishGoogleAuth(auth, new Error('Google sign-in timed out.')),
                    3 * 60 * 1000,
                );
                await shell.openExternal(`${origin}/login?desktop_state=${encodeURIComponent(auth.state)}`);
            } catch (error) {
                finishGoogleAuth(auth, new Error(
                    error instanceof Error && error.message === 'Google sign-in timed out.'
                        ? error.message
                        : 'Could not open Google sign-in in your browser.',
                ));
            }
        });
    });
}

// ---------------------------------------------------------------------------
// Backend (Python)
// ---------------------------------------------------------------------------

function startBackend() {
    const exeName = process.platform === 'win32' ? 'speechnotes-backend.exe' : 'speechnotes-backend';
    const backendPath = isDev
        ? path.join(__dirname, '..', 'backend-dist', exeName)
        : path.join(process.resourcesPath, 'backend', exeName);

    console.log(`[Electron] Starting backend: ${backendPath}`);

    backendProcess = spawn(backendPath, [], {
        env: {
            ...process.env,
            SQLITE_DB_DIR: app.getPath('userData'),
        },
        stdio: ['ignore', 'pipe', 'pipe'],
    });

    backendProcess.stdout.on('data', d => console.log(`[Backend] ${d}`));
    backendProcess.stderr.on('data', d => console.error(`[Backend] ${d}`));
    backendProcess.on('close', code => {
        console.log(`[Backend] exited with code ${code}`);
        backendProcess = null;
    });
}

// ---------------------------------------------------------------------------
// Frontend (Next.js standalone server)
// ---------------------------------------------------------------------------

function startFrontend() {
    const serverEntry = isDev
        ? path.join(__dirname, '..', 'web', '.next', 'standalone', 'server.js')
        : path.join(process.resourcesPath, 'frontend', 'server.js');

    console.log(`[Electron] Starting frontend: ${serverEntry}`);

    frontendProcess = spawn(process.execPath.replace(/electron[^/\\]*$/i, 'node'), [serverEntry], {
        env: {
            ...process.env,
            PORT: String(FRONTEND_PORT),
            HOSTNAME: '127.0.0.1',
        },
        stdio: ['ignore', 'pipe', 'pipe'],
        cwd: path.dirname(serverEntry),
    });

    // In dev, we use the Next.js dev server directly instead
    if (isDev) {
        // Frontend is started via `npm run dev` externally
        frontendProcess = null;
    } else {
        frontendProcess.stdout.on('data', d => console.log(`[Frontend] ${d}`));
        frontendProcess.stderr.on('data', d => console.error(`[Frontend] ${d}`));
        frontendProcess.on('close', code => {
            console.log(`[Frontend] exited with code ${code}`);
            frontendProcess = null;
        });
    }
}

// ---------------------------------------------------------------------------
// Window
// ---------------------------------------------------------------------------

async function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 900,
        minHeight: 600,
        title: 'SpeechNotes',
        icon: path.join(__dirname, '..', 'assets', 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
        },
    });

    // Strip 'Electron' from the User-Agent so Google OAuth doesn't block the flow
    const originalUA = mainWindow.webContents.getUserAgent();
    mainWindow.webContents.setUserAgent(originalUA.replace(/Electron\/[\d.]+ /, ''));

    // Load the frontend — use 'localhost' (not 127.0.0.1) to match the OAuth callback URI
    const url = `http://localhost:${FRONTEND_PORT}`;
    console.log(`[Electron] Loading ${url}`);
    mainWindow.loadURL(url);

    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
    ipcMain.handle('google-auth:start', startGoogleAuth);
    try {
        if (!isDev) {
            // 1. Start backend (in production only; in dev run_all.ps1 handles it)
            startBackend();
            await waitForPort(BACKEND_PORT);
            console.log('[Electron] Backend is ready');

            // 2. Start frontend (in production only; in dev Next.js dev server runs separately)
            startFrontend();
            await waitForPort(FRONTEND_PORT, 'localhost');
            console.log('[Electron] Frontend is ready');
        } else {
            // In dev, just wait for the externally started backend & frontend
            console.log('[Electron] Dev mode – waiting for external backend & frontend...');
            await waitForPort(BACKEND_PORT, '127.0.0.1');
            console.log('[Electron] Backend is ready (external)');
            await waitForPort(FRONTEND_PORT, '127.0.0.1');
            console.log('[Electron] Frontend is ready (external)');
        }

        // 3. Create window
        await createWindow();
    } catch (err) {
        console.error('[Electron] Startup failed:', err);
        dialog.showErrorBox('SpeechNotes', `Failed to start: ${err.message}`);
        app.quit();
    }
});

app.on('window-all-closed', () => {
    app.quit();
});

app.on('before-quit', () => {
    if (activeGoogleAuth) {
        finishGoogleAuth(activeGoogleAuth, new Error('SpeechNotes is closing.'));
    }
    // Kill child processes
    if (backendProcess) {
        console.log('[Electron] Killing backend process');
        backendProcess.kill();
    }
    if (frontendProcess) {
        console.log('[Electron] Killing frontend process');
        frontendProcess.kill();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
