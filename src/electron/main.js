const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');
const fs = require('fs');

let mainWindow;
let pythonProcess;

function setupLogging() {
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
  console.log('App version:', app.getVersion());
  console.log('Platform:', process.platform, process.arch);
  console.log('Is packaged:', app.isPackaged);
  
  return logFile;
}

function createWindow() {
  setupLogging();
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true,
      devTools: true
    },
    icon: path.join(__dirname, '../frontend/images/icon_excel_comparison.ico'),
    show: false,
    titleBarStyle: 'default',
    autoHideMenuBar: true,
    resizable: true,
    minWidth: 1200,
    minHeight: 800
  });

    // Add keyboard shortcut to open developer tools
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.control && input.shift && input.key.toLowerCase() === 'i') {
      mainWindow.webContents.toggleDevTools();
    }
    // Also allow F12
    if (input.key === 'F12') {
      mainWindow.webContents.toggleDevTools();
    }
  });

  // Show loading screen immediately
  mainWindow.loadFile(path.join(__dirname, '../frontend/loading.html')).catch(() => {
    console.error('Failed to load loading screen');
  });
  
  mainWindow.show();

  // Start Python backend
  startPythonServer();

  // Show clearer startup progress
  let startupProgress = 0;
  const startupInterval = setInterval(() => {
    if (startupProgress < 90) {
      startupProgress += 5;
      mainWindow.webContents.executeJavaScript(`
        document.getElementById('progress-bar').style.width = '${startupProgress}%';
        document.getElementById('status-message').innerText = 'Démarrage du serveur en cours...';
      `);
    }
  }, 300);

  // Wait for backend with better timeout handling
  waitForBackend()
      .then((port) => {
          clearInterval(startupInterval);
          console.log(`Backend ready on port ${port}`);
          
          mainWindow.webContents.executeJavaScript(`
            document.getElementById('progress-bar').style.width = '100%';
            document.getElementById('status-message').innerText = 'Chargement de l\'application...';
          `);

          // Set the backend URL and load the main app
          setTimeout(() => {
              mainWindow.loadFile(path.join(__dirname, '../frontend/index.html')).then(() => {
                  mainWindow.webContents.executeJavaScript(`
                    window.BACKEND_URL = 'http://localhost:${port}';
                    console.log('Backend URL set to:', window.BACKEND_URL);
                    window.dispatchEvent(new CustomEvent('backendReady', { 
                        detail: { backendUrl: 'http://localhost:${port}' } 
                    }));
                  `);
              });
          }, 500);
      })
      .catch((error) => {
          clearInterval(startupInterval);
          console.error('Backend failed to start:', error);
          showError(`Impossible de démarrer le serveur: ${error.message}`);
      });

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (pythonProcess) {
      pythonProcess.kill('SIGTERM');
    }
  });
}

function startPythonServer() {
  console.log('Starting Python backend...');
  
  let backendExecutable;
  let workingDir;
  
  if (app.isPackaged) {
    // Look for packaged executable
    const resourcesPath = process.resourcesPath;
    const possiblePaths = [
      path.join(resourcesPath, 'backend', 'ect-backend.exe'),
      path.join(resourcesPath, 'app', 'backend', 'ect-backend.exe')
    ];
    
    for (const testPath of possiblePaths) {
      if (fs.existsSync(testPath)) {
        backendExecutable = testPath;
        workingDir = path.dirname(testPath);
        break;
      }
    }

    if (!backendExecutable) {
      console.error('Backend executable not found');
      showError('Backend executable not found. Please reinstall the application.');
      return;
    }
  } else {
    // Development mode
    const pythonScript = path.join(__dirname, '../backend/app.py');
    
    if (fs.existsSync(pythonScript)) {
      workingDir = path.dirname(pythonScript);
      
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
        showError('Failed to start development backend. Make sure Python is installed.');
        return;
      }
    } else {
      console.error('Development Python script not found');
      showError('Development backend script not found.');
      return;
    }
  }
  
  console.log(`Starting backend: ${backendExecutable}`);
  
  try {
    pythonProcess = spawn(backendExecutable, [], {
      cwd: workingDir,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      windowsHide: true
    });

    console.log('Backend process started, PID:', pythonProcess.pid);
    setupPythonProcessHandlers();
    
  } catch (error) {
    console.error('Failed to start backend:', error);
    showError(`Failed to start backend: ${error.message}`);
  }
}

function setupPythonProcessHandlers() {
  if (!pythonProcess) return;
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data.toString().trim()}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data.toString().trim()}`);
  });
  
  pythonProcess.on('close', (code) => {
    if (code !== 0 && code !== null) {
      console.error(`Backend process exited with code ${code}`);
      showError(`Backend process crashed with code ${code}`);
    }
  });
  
  pythonProcess.on('error', (error) => {
    console.error('Backend process error:', error);
    showError(`Backend process error: ${error.message}`);
  });
}

async function waitForBackend() {
  const maxAttempts = 60;
  const delay = 500;
  
  console.log('Waiting for backend to start...');
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      if (pythonProcess && pythonProcess.killed) {
        throw new Error('Python process was terminated');
      }
      
      const response = await axios.get('http://localhost:5000/health', { 
        timeout: 2000 
      });
      
      if (response.status === 200) {
        console.log('Backend is ready');
        
        // Test if docs endpoint is working
        try {
          const docsTest = await axios.get('http://localhost:5000/api/docs/list', { 
            timeout: 2000 
          });
          console.log('Docs endpoint is working');
        } catch (docsError) {
          console.warn('Docs endpoint test failed:', docsError.message);
        }
        
        return 5000;
      }
    } catch (error) {
      if (attempt % 10 === 0) {
        console.log(`Still waiting for backend... (attempt ${attempt}/${maxAttempts})`);
      }
    }
    
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  
  throw new Error('Backend failed to start within 30 seconds');
}

function showError(message) {
  console.error('Application Error:', message);
  
  if (mainWindow) {
    mainWindow.webContents.executeJavaScript(`
      document.body.innerHTML = \`
        <div style="padding: 20px; font-family: Arial, sans-serif; text-align: center;">
          <h2 style="color: #d32f2f;">Application Error</h2>
          <p>${message}</p>
          <p>Please restart the application or contact support if the problem persists.</p>
          <button onclick="window.location.reload()" style="padding: 8px 16px; margin-top: 10px;">Retry</button>
        </div>
      \`;
    `);
  }
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