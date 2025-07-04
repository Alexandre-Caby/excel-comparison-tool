const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');
const fs = require('fs');

let mainWindow;
let pythonProcess;

// Enhanced logging that works in packaged apps
function setupEnhancedLogging() {
  const logDir = path.join(app.getPath('userData'), 'logs');
  
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  
  const logFile = path.join(logDir, `app-${new Date().toISOString().replace(/[:.]/g, '-')}.log`);
  const logStream = fs.createWriteStream(logFile, { flags: 'a' });
  
  const originalLog = console.log;
  const originalError = console.error;
  
  console.log = function(...args) {
    const message = `[${new Date().toISOString()}] [LOG] ${args.join(' ')}`;
    logStream.write(message + '\n');
    originalLog.apply(console, args);
  };
  
  console.error = function(...args) {
    const message = `[${new Date().toISOString()}] [ERROR] ${args.join(' ')}`;
    logStream.write(message + '\n');
    originalError.apply(console, args);
  };
  
  console.log('=== ECT TECHNIS STARTUP ===');
  console.log('Log file:', logFile);
  console.log('App version:', app.getVersion());
  console.log('Electron version:', process.versions.electron);
  console.log('Node version:', process.versions.node);
  console.log('Platform:', process.platform, process.arch);
  console.log('Is packaged:', app.isPackaged);
  console.log('App path:', app.getAppPath());
  console.log('Resources path:', process.resourcesPath);
  console.log('User data:', app.getPath('userData'));
  
  return logFile;
}

function createWindow() {
  const logFile = setupEnhancedLogging();
  
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

  // Show debug info immediately
  mainWindow.webContents.once('dom-ready', () => {
    console.log('DOM ready - injecting debug info');
    mainWindow.webContents.executeJavaScript(`
      document.body.style.backgroundColor = '#f0f0f0';
      document.body.innerHTML = '<div style="padding: 20px; font-family: monospace;"><h2>ECT Technis Debug Info</h2><pre id="debug-info">Loading...</pre></div>';
      document.getElementById('debug-info').textContent = 'Log file: ${logFile.replace(/\\/g, '\\\\')}\\nWaiting for Python backend...';
    `);
  });

  // Start Python backend
  startPythonServer();

  // Load a basic page first
  mainWindow.loadFile(path.join(__dirname, '../frontend/index.html')).catch(() => {
    console.error('Failed to load local file, creating fallback page');
    mainWindow.loadURL('data:text/html,<html><body><h1>ECT Technis Debug Mode</h1><p>Check logs for details</p></body></html>');
  });
  
  mainWindow.show();

  // Try to connect to backend after a delay
  setTimeout(() => {
    waitForBackend().then((port) => {
      console.log(`Backend ready on port ${port}, reloading UI`);
      mainWindow.loadURL(`http://localhost:${port}`);
    }).catch((error) => {
      console.error('Backend failed to start:', error);
      mainWindow.webContents.executeJavaScript(`
        document.body.innerHTML = '<div style="padding: 20px; color: red;"><h2>Backend Error</h2><pre>${error.message}</pre><p>Check logs at: ${logFile.replace(/\\/g, '\\\\')}</p></div>';
      `);
    });
  }, 2000);

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (pythonProcess) {
      console.log('Terminating Python process...');
      pythonProcess.kill('SIGTERM');
    }
  });
}

function startPythonServer() {
  console.log('=== STARTING PYTHON SERVER ===');
  
  let pythonScript;
  let pythonExecutable = 'python';
  let workingDir;
  
  if (app.isPackaged) {
    console.log('Running in packaged mode');
    const resourcesPath = process.resourcesPath;
    
    // List contents of resources directory
    console.log('Resources directory contents:');
    try {
      const resourceFiles = fs.readdirSync(resourcesPath);
      resourceFiles.forEach(file => {
        const fullPath = path.join(resourcesPath, file);
        const stats = fs.statSync(fullPath);
        console.log(`  ${stats.isDirectory() ? 'DIR' : 'FILE'}: ${file}`);
      });
    } catch (err) {
      console.error('Error listing resources:', err);
    }
    
    // Check possible Python script locations
    const possiblePaths = [
      path.join(resourcesPath, 'app', 'secure_src', 'backend', 'app.py'),
      path.join(resourcesPath, 'secure_src', 'backend', 'app.py'),
      path.join(resourcesPath, 'app', 'backend', 'app.py'),
      path.join(resourcesPath, 'backend', 'app.py')
    ];
    
    console.log('Checking for Python script in possible locations:');
    for (const testPath of possiblePaths) {
      const exists = fs.existsSync(testPath);
      console.log(`  ${exists ? '✓' : '✗'} ${testPath}`);
      if (exists && !pythonScript) {
        pythonScript = testPath;
        workingDir = path.dirname(testPath);
      }
    }
    
    // Check for bundled Python
    const possiblePythonPaths = [
      path.join(resourcesPath, 'python', 'python.exe'),
      path.join(resourcesPath, 'python', 'pythonw.exe')
    ];
    
    console.log('Checking for bundled Python:');
    for (const testPath of possiblePythonPaths) {
      const exists = fs.existsSync(testPath);
      console.log(`  ${exists ? '✓' : '✗'} ${testPath}`);
      if (exists) {
        pythonExecutable = testPath;
        break;
      }
    }
  } else {
    console.log('Running in development mode');
    pythonScript = path.join(__dirname, '../backend/app.py');
    workingDir = path.dirname(pythonScript);
  }
  
  if (!pythonScript) {
    console.error('CRITICAL: Python script not found!');
    return;
  }
  
  if (!fs.existsSync(pythonScript)) {
    console.error(`CRITICAL: Python script does not exist at: ${pythonScript}`);
    return;
  }
  
  console.log(`Python executable: ${pythonExecutable}`);
  console.log(`Python script: ${pythonScript}`);
  console.log(`Working directory: ${workingDir}`);
  
  try {
    console.log('Spawning Python process...');
    pythonProcess = spawn(pythonExecutable, [pythonScript], {
      cwd: workingDir,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      windowsHide: false // Show console for debugging
    });

    console.log(`Python PID: ${pythonProcess.pid}`);
    
    pythonProcess.stdout.on('data', (data) => {
      console.log(`Python stdout: ${data.toString().trim()}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python stderr: ${data.toString().trim()}`);
    });
    
    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
    });
    
    pythonProcess.on('error', (error) => {
      console.error('Python process error:', error);
    });
  } catch (error) {
    console.error('Exception starting Python process:', error);
  }
}

async function waitForBackend(maxAttempts = 30, ports = [5000, 5001, 5002, 5003]) {
  console.log('Waiting for backend to become available...');
  
  for (const port of ports) {
    console.log(`Trying port ${port}...`);
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      try {
        const response = await axios.get(`http://localhost:${port}/health`, { timeout: 2000 });
        console.log(`Backend is ready on port ${port}!`);
        return port;
      } catch (error) {
        attempts++;
        console.log(`Port ${port} attempt ${attempts}/${maxAttempts}: ${error.message}`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }
  
  throw new Error('Backend failed to start on any port');
}

// IPC handlers
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
app.whenReady().then(createWindow);

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

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
  }
});