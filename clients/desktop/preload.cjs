const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('blackjackClient', {
    openServer: (address) => ipcRenderer.invoke('blackjack:open-server', address)
});
