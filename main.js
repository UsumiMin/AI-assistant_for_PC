const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const fs   = require('fs');

const SETTINGS_PATH = path.join(app.getPath('userData'), 'settings.json');

const DEFAULT_SETTINGS = {
  volume:       80,
  subtitles:    true,
  miniMode:     true,
  miniPosition: 'right',
};

function loadSettings() {
  try {
    if (fs.existsSync(SETTINGS_PATH)) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8')) };
    }
  } catch (e) {
    console.error('[settings] Failed to load:', e);
  }
  return { ...DEFAULT_SETTINGS };
}

function saveSettings(data) {
  try {
    fs.writeFileSync(SETTINGS_PATH, JSON.stringify(data, null, 2), 'utf8');
  } catch (e) {
    console.error('[settings] Failed to save:', e);
  }
}

let currentSettings = loadSettings();

const FULL_W = 1280;
const FULL_H = 720;
const MINI_W = 260;
const MINI_H = 280;

let win;
let isMinimized = false;

let openChildCount = 0;

function setMainOnTop(value) {
  if (win && !win.isDestroyed()) {
    win.setAlwaysOnTop(value);
  }
}

function createWindow() {
  win = new BrowserWindow({
    width: FULL_W,
    height: FULL_H,
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
  /win.webContents.openDevTools();/

  win.webContents.on('did-finish-load', () => {
    win.webContents.send('apply-settings', currentSettings);
  });

  win.on('restore', () => {
    isMinimized = false;
    if (win && !win.isDestroyed()) {
      win.webContents.send('set-mini-mode', false);
    }
  });
}

function getMiniPosition() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  const x = currentSettings.miniPosition === 'left'
    ? 12
    : width - MINI_W - 12;
  return { x, y: height - MINI_H - 12 };
}

ipcMain.on('window-minimize', () => {
  if (isMinimized) return;
  isMinimized = true;

  if (!currentSettings.miniMode) {
    win.minimize();
    return;
  }

  const { x, y } = getMiniPosition();
  win.setBounds({ x, y, width: MINI_W, height: MINI_H }, true);
  win.webContents.send('set-mini-mode', true);
});

ipcMain.on('window-restore', () => {
  if (!isMinimized) return;
  isMinimized = false;

  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  win.setBounds({
    x: Math.round((width - FULL_W) / 2),
    y: Math.round((height - FULL_H) / 2),
    width: FULL_W,
    height: FULL_H,
  }, true);

  win.webContents.send('set-mini-mode', false);
});

ipcMain.handle('get-settings', () => currentSettings);

ipcMain.handle('save-settings', (event, newSettings) => {
  const oldMiniMode = currentSettings.miniMode;
  
  currentSettings = { ...currentSettings, ...newSettings };
  saveSettings(currentSettings);
  
  if (win && !win.isDestroyed()) {
    win.webContents.send('apply-settings', currentSettings);

    if (isMinimized && oldMiniMode && !currentSettings.miniMode) {
      isMinimized = false;
      const { width, height } = screen.getPrimaryDisplay().workAreaSize;
      win.setBounds({
        x: Math.round((width - FULL_W) / 2),
        y: Math.round((height - FULL_H) / 2),
        width: FULL_W,
        height: FULL_H,
      }, true);
      win.webContents.send('set-mini-mode', false);
    }
  }
  return true;
});

ipcMain.on('open-window', (event, filePage) => {
  const existing = BrowserWindow.getAllWindows().find(
    w => w !== win && !w.isDestroyed() && w.webContents.getURL().endsWith(filePage)
  );
  if (existing) {
    existing.focus();
    return;
  }

  openChildCount++;
  setMainOnTop(false);

  const childWindow = new BrowserWindow({
    width: 600,
    height: 500,
    parent: win,
    resizable: false,
    frame: false,
    alwaysOnTop: true,        
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    }
  });

  childWindow.loadFile(filePage);
  childWindow.setMenu(null);
  childWindow.center();

  function onResize(e, contentHeight) {
    if (!childWindow.isDestroyed()) {
      const [w] = childWindow.getSize();
      childWindow.setSize(w, contentHeight + 40);
      childWindow.center();
    }
  }
  ipcMain.once('resize-to-content', onResize);

  childWindow.on('closed', () => {
    ipcMain.removeListener('resize-to-content', onResize);

    openChildCount = Math.max(0, openChildCount - 1);

    if (openChildCount === 0) {
      setMainOnTop(true);
      if (win && !win.isDestroyed()) win.focus();
    }
  });
});

ipcMain.on('window-close', () => {
  app.quit();
});

ipcMain.on('change-avatar-script', (event, scriptName) => {
  currentSettings.avatarScript = scriptName;
  saveSettings(currentSettings);
  
  if (win && !win.isDestroyed()) {
    win.reload();
  }
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});