const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let win;

function createWindow () {
  win = new BrowserWindow({
    width: 1280,
    height: 720,
    frame: false,
    transparent: true,
    alwaysOnTop: true,

    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false,
    }
  });
  
  win.loadFile('index.html');

    win.webContents.openDevTools();
}

ipcMain.on('open-window', (event, filePage) => {
  if (win) {
    win.setAlwaysOnTop(false);
  }

  let childWindow = new BrowserWindow({
    width: 600,
    height: 500,
    parent: win,
    modal: true,
    resizable: false,
    frame: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    }
  });

  childWindow.loadFile(filePage);
  
  childWindow.setMenu(null);
  childWindow.center();
  childWindow.on('closed', () => {
    if (win) {
      win.setAlwaysOnTop(true);
      win.focus();
    }
  });
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});