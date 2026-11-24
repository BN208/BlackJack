const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('node:path');
const { normalizeServerAddress } = require('./server-address.cjs');

let mainWindow;

function showLauncher() {
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.loadFile(path.join(__dirname, 'launcher.html'));
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1100,
        height: 820,
        minWidth: 360,
        minHeight: 520,
        title: 'BlackJack',
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: true
        }
    });

    mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    mainWindow.webContents.on('will-navigate', (event, target) => {
        const url = new URL(target);
        const isLauncher = url.protocol === 'file:'
            && url.pathname === path.join(__dirname, 'launcher.html');
        if (!isLauncher && !['http:', 'https:'].includes(url.protocol)) {
            event.preventDefault();
        }
    });

    const fileMenu = {
        label: 'File',
        submenu: [
            { label: 'Change Server', click: showLauncher },
            { type: 'separator' },
            { role: 'quit' }
        ]
    };
    const editMenu = {
        label: 'Edit',
        submenu: [
            { role: 'undo' },
            { role: 'redo' },
            { type: 'separator' },
            { role: 'cut' },
            { role: 'copy' },
            { role: 'paste' },
            { role: 'selectAll' }
        ]
    };
    Menu.setApplicationMenu(Menu.buildFromTemplate([fileMenu, editMenu]));
    mainWindow.loadFile(path.join(__dirname, 'launcher.html'));
}

ipcMain.handle('blackjack:open-server', async (_event, address) => {
    const serverAddress = normalizeServerAddress(address);
    if (!mainWindow || mainWindow.isDestroyed()) {
        throw new Error('The BlackJack window is not available.');
    }
    await mainWindow.loadURL(serverAddress);
    return serverAddress;
});

app.whenReady().then(() => {
    createWindow();
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});
