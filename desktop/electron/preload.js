/**
 * Preload script for Electron
 * Exposes a safe API to the renderer process via contextBridge.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // App info
    getVersion: () => ipcRenderer.invoke('get-version'),
    getPlatform: () => process.platform,

    // Safe storage (for encrypting API keys)
    encrypt: (text) => ipcRenderer.invoke('safe-encrypt', text),
    decrypt: (buffer) => ipcRenderer.invoke('safe-decrypt', buffer),

    // Window controls
    minimize: () => ipcRenderer.send('window-minimize'),
    maximize: () => ipcRenderer.send('window-maximize'),
    close: () => ipcRenderer.send('window-close'),
});
