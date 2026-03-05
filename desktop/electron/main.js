/**
 * SpeechNotes Desktop - Electron Main Process
 *
 * Responsibilities:
 * 1. Launch the Python backend (PyInstaller binary) on startup
 * 2. Serve the Next.js standalone frontend
 * 3. Create the main BrowserWindow
 * 4. Kill all child processes on quit
 */

const { app, BrowserWindow, dialog, safeStorage, net: electronNet } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const net = require('net');
const http = require('http');

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
            const url = `http://${host}:${port}/`;
            const req = http.get(url, (res) => {
                console.log(`[Electron] Port ${port} on ${host} is ready! (status ${res.statusCode})`);
                res.resume();          // drain the response
                resolve();
            });
            req.on('error', () => {
                setTimeout(tryConnect, 1000);
            });
            req.setTimeout(2000, () => {
                req.destroy();
                setTimeout(tryConnect, 1000);
            });
        }

        tryConnect();
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
        // Frontend is started via `pnpm dev` externally
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
