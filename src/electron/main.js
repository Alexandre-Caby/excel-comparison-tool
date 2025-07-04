// Not used but maybe later if development in desktop app

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true
    },
    icon: path.join(__dirname, '../frontend/images/icon_excel_comparison.ico'),
    show: false,
    titleBarStyle: 'default',
    autoHideMenuBar: true,
    resizable: true,
    minWidth: 1200,
    minHeight: 800
  });

  // Start Python backend
  startPythonServer();

  // Wait for backend to be ready, then load frontend
  waitForBackend().then(() => {
    // Load the app via localhost URL
    mainWindow.loadURL('http://localhost:5000');
    mainWindow.show();
    
    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  }).catch((error) => {
    console.error('Failed to start backend:', error);
    
    // Fallback: try to load local files
    console.log('Attempting fallback to local files...');
    mainWindow.loadFile(path.join(__dirname, '../frontend/index.html'));
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (pythonProcess) {
      console.log('Killing Python process...');
      pythonProcess.kill('SIGTERM');
      
      // Force kill after 5 seconds if still running
      setTimeout(() => {
        if (pythonProcess && !pythonProcess.killed) {
          pythonProcess.kill('SIGKILL');
        }
      }, 5000);
    }
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    require('electron').shell.openExternal(url);
    return { action: 'deny' };
  });
}

function startPythonServer() {
  let pythonScript;
  let pythonExecutable;
  
  if (app.isPackaged) {
    // In production: use resources path
    const resourcesPath = process.resourcesPath;
    pythonScript = path.join(resourcesPath, 'app', 'secure_src', 'backend', 'app.py');
    
    // Use bundled Python if possible (use pythonw.exe to hide console window)
    pythonExecutable = path.join(resourcesPath, 'python', 'pythonw.exe');
    if (!require('fs').existsSync(pythonExecutable)) {
      // Fallback to system Python
      pythonExecutable = 'pythonw';
    }
  } else {
    // In development
    pythonScript = path.join(__dirname, '../backend/app.py');
    pythonExecutable = 'python';
  }
  
  console.log('Starting Python server...');
  console.log('Python script path:', pythonScript);
  console.log('Python executable:', pythonExecutable);
  

  try {
    pythonProcess = spawn(pythonExecutable, [pythonScript], {
      cwd: path.dirname(pythonScript),
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      windowsHide: true
    });

    console.log(`Python PID: ${pythonProcess.pid}`);
    
    pythonProcess.stdout.on('data', (data) => {
      console.log(`Python stdout: ${data.toString()}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python stderr: ${data.toString()}`);
    });
    
    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
    });
    
    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      dialog.showErrorBox(
        'Backend Error',
        `Failed to start Python backend: ${error.message}\n\nPlease make sure Python is installed.`
      );
    });
  } catch (error) {
    console.error('Exception starting Python process:', error);
  }
}

async function waitForBackend(maxAttempts = 30) {
  let attempts = 0;
  
  console.log('Waiting for backend to be ready...');
  
  while (attempts < maxAttempts) {
    try {
      const response = await axios.get('http://localhost:5000/health', { 
        timeout: 5000 
      });
      console.log('Backend is ready!');
      return;
    } catch (error) {
      attempts++;
      console.log(`Waiting for backend... attempt ${attempts}/${maxAttempts}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  throw new Error('Backend failed to start after maximum attempts');
}

// IPC handlers for file dialogs
ipcMain.handle('select-files', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'Excel Files', extensions: ['xlsx', 'xls'] },
      { name: 'All Files', extensions: ['*'] }
    ],
    ...options
  });
  return result;
});

// App event handlers
app.whenReady().then(() => {
  createWindow();
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Handle app quit
app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
  }
});
