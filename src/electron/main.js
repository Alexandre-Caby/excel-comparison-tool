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
      // mainWindow.loadURL(`http://localhost:${port}`);
      mainWindow.loadFile(path.join(__dirname, '../frontend/index.html'));

      mainWindow.webContents.once('dom-ready', () => {
          mainWindow.webContents.executeJavaScript(`
              window.BACKEND_URL = 'http://localhost:${port}';
              console.log('Backend URL set to:', window.BACKEND_URL);
          `);
      });

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
  
  let backendExecutable;
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
        
        // If it's a directory, list its contents too
        if (stats.isDirectory() && file === 'backend') {
          try {
            const subFiles = fs.readdirSync(fullPath);
            subFiles.forEach(subFile => {
              console.log(`    FILE: ${subFile}`);
            });
          } catch (err) {
            console.error(`    Error listing ${file}:`, err);
          }
        }
      });
    } catch (err) {
      console.error('Error listing resources:', err);
    }
    
    // Look for the backend executable
    const possibleExecutablePaths = [
      path.join(resourcesPath, 'backend', 'ect-backend.exe'),
      path.join(resourcesPath, 'app', 'backend', 'ect-backend.exe'),
      path.join(resourcesPath, 'ect-backend.exe')
    ];
    
    console.log('Checking for backend executable:');
    for (const testPath of possibleExecutablePaths) {
      const exists = fs.existsSync(testPath);
      console.log(`  ${exists ? '[OK]' : '[ERROR]'} ${testPath}`);
      if (exists) {
        backendExecutable = testPath;
        workingDir = path.dirname(testPath);
        break;
      }
    }
    
    if (!backendExecutable) {
      console.error('CRITICAL: Backend executable not found!');
      showBackendError('Backend executable not found. Please reinstall the application.');
      return;
    }
  } else {
    console.log('Running in development mode');
    const pythonScript = path.join(__dirname, '../backend/app.py');
    if (fs.existsSync(pythonScript)) {
      console.log(`Using Python script: ${pythonScript}`);
      workingDir = path.dirname(pythonScript);
      
      // Try to spawn Python process
      try {
        pythonProcess = spawn('python', [pythonScript], {
          cwd: workingDir,
          env: { ...process.env, PYTHONUNBUFFERED: '1' },
          windowsHide: true
        });
        
        setupPythonProcessHandlers();
        return;
      } catch (error) {
        console.error('Failed to start Python in development mode:', error);
        showBackendError('Failed to start development backend. Make sure Python is installed.');
        return;
      }
    } else {
      console.error('Development Python script not found');
      showBackendError('Development backend script not found.');
      return;
    }
  }
  
  console.log(`Backend executable: ${backendExecutable}`);
  console.log(`Working directory: ${workingDir}`);
  
  try {
    console.log('Starting backend executable...');
    
    // Start the PyInstaller executable
    pythonProcess = spawn(backendExecutable, [], {
      cwd: workingDir,
      env: { 
        ...process.env, 
        PYTHONUNBUFFERED: '1',
      },
      windowsHide: true
    });

    setupPythonProcessHandlers();
    
  } catch (error) {
    console.error('Exception starting backend executable:', error);
    showBackendError(`Failed to start backend: ${error.message}`);
  }
}

function setupPythonProcessHandlers() {
  if (!pythonProcess) return;
  
  console.log(`Backend process PID: ${pythonProcess.pid}`);
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Backend stdout: ${data.toString().trim()}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Backend stderr: ${data.toString().trim()}`);
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    if (code !== 0 && code !== null) {
      showBackendError(`Backend process crashed with code ${code}`);
    }
  });
  
  pythonProcess.on('error', (error) => {
    console.error('Backend process error:', error);
    showBackendError(`Backend process error: ${error.message}`);
  });
}

function showBackendError(message) {
  console.error('Backend Error:', message);
  
  if (mainWindow) {
    mainWindow.webContents.executeJavaScript(`
      document.body.innerHTML = \`
        <div style="padding: 40px; font-family: Arial, sans-serif; text-align: center; background: #f5f5f5;">
          <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color: #d32f2f; margin-bottom: 20px;">Backend Error</h1>
            <p style="font-size: 16px; margin: 20px 0; color: #666;">${message}</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 4px; margin: 20px 0;">
              <h3 style="margin-top: 0;">Troubleshooting:</h3>
              <ul style="text-align: left; margin: 10px 0;">
                <li>Try restarting the application</li>
                <li>Check if antivirus software is blocking the application</li>
                <li>Run as administrator if needed</li>
                <li>Reinstall the application if the problem persists</li>
              </ul>
            </div>
            <button onclick="window.close()" 
                    style="background: #1976d2; color: white; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-size: 16px;">
              Close Application
            </button>
          </div>
        </div>
      \`;
    `);
  }
}

async function waitForBackend() {
  const maxAttempts = 60; // 30 seconds (500ms * 60)
  const delay = 500; // 500ms between attempts
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      console.log(`Attempting to connect to backend (${attempt}/${maxAttempts})...`);
      
      // Try to connect to Flask backend on default port
      const response = await axios.get('http://localhost:5000/health', { 
        timeout: 1000 
      });
      
      if (response.status === 200) {
        console.log('Backend is ready!');
        return 5000; // Return the port number
      }
    } catch (error) {
      // Silent fail - just continue trying
      if (attempt % 10 === 0) {
        console.log(`Still waiting for backend... (attempt ${attempt})`);
      }
    }
    
    // Wait before next attempt
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  
  throw new Error('Backend failed to start within 30 seconds');
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