const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');
const fs = require('fs');

let mainWindow;
let pythonProcess;

// Add global error handling
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Promise Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

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

// Helper function to safely execute JavaScript in renderer
async function safeExecuteJS(script, fallback = null, retries = 3) {
  if (!mainWindow || mainWindow.isDestroyed()) {
    console.warn('Cannot execute JS: window is destroyed or null');
    return false;
  }

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      // Wait for the webContents to be ready
      if (!mainWindow.webContents.isLoading() && mainWindow.webContents.getURL()) {
        const result = await mainWindow.webContents.executeJavaScript(script);
        return result;
      } else {
        console.log(`Waiting for webContents to be ready (attempt ${attempt})`);
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    } catch (error) {
      console.error(`JavaScript execution error (attempt ${attempt}):`, error.message);
      
      if (attempt === retries && fallback) {
        try {
          console.log('Attempting fallback script...');
          return await mainWindow.webContents.executeJavaScript(fallback);
        } catch (fallbackError) {
          console.error('Fallback script also failed:', fallbackError.message);
          return false;
        }
      }
      
      if (attempt < retries) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  }
  
  return false;
}

// Helper function to wait for DOM ready
function waitForDOMReady() {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('DOM ready timeout'));
    }, 10000);

    mainWindow.webContents.once('dom-ready', () => {
      clearTimeout(timeout);
      resolve();
    });

    // If already ready
    if (!mainWindow.webContents.isLoading()) {
      clearTimeout(timeout);
      resolve();
    }
  });
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

  // Show loading screen immediately
  mainWindow.loadFile(path.join(__dirname, '../frontend/loading.html'))
    .then(() => {
      console.log('Loading screen loaded successfully');
      mainWindow.show();
    })
    .catch((error) => {
      console.error('Failed to load loading screen:', error);
      mainWindow.show(); // Show anyway
    });

  // Start Python backend
  startPythonServer();

  // Show startup progress with safe execution
  let startupProgress = 0;
  const startupInterval = setInterval(async () => {
    if (startupProgress < 90) {
      startupProgress += 5;
      await safeExecuteJS(`
        try {
          const progressBar = document.getElementById('progress-bar');
          const statusMessage = document.getElementById('status-message');
          if (progressBar) progressBar.style.width = '${startupProgress}%';
          if (statusMessage) statusMessage.innerText = 'Démarrage du serveur en cours...';
        } catch (e) {
          console.warn('Progress update failed:', e);
        }
      `);
    }
  }, 300);

  // Wait for backend with better error handling
  waitForBackend()
    .then(async (port) => {
        clearInterval(startupInterval);
        console.log(`Backend ready on port ${port}`);
        
        // Update progress to 100%
        await safeExecuteJS(`
            try {
                const progressBar = document.getElementById('progress-bar');
                const statusMessage = document.getElementById('status-message');
                if (progressBar) progressBar.style.width = '100%';
                if (statusMessage) statusMessage.innerText = 'Chargement de l\'application...';
            } catch (e) {
                console.warn('Final progress update failed:', e);
            }
        `);

        // Create a global backend URL variable that will be exposed to renderer
        global.BACKEND_URL = `http://localhost:${port}`;
        
        // Load the main application with simplified approach
        setTimeout(() => {
            try {
                mainWindow.loadFile(path.join(__dirname, '../frontend/index.html'))
                    .then(() => {
                        console.log('Main application loaded successfully');
                        
                        // Inject the backend URL directly - simpler approach
                        mainWindow.webContents.executeJavaScript(`
                            window.BACKEND_URL = 'http://localhost:${port}';
                            console.log('Backend URL set to:', window.BACKEND_URL);
                            
                            // Set a flag to indicate backend is ready
                            localStorage.setItem('backendUrl', 'http://localhost:${port}');
                            localStorage.setItem('backendReady', 'true');
                            
                            // No complex event system, just a simple global
                            true;
                        `).catch(err => {
                            console.error('Failed to set backend URL:', err);
                        });
                    })
                    .catch((loadError) => {
                        console.error('Error loading main HTML file:', loadError);
                        showError('Failed to load application interface');
                    });
            } catch (error) {
                console.error('Error during app initialization:', error);
                showError('Failed to initialize application');
            }
        }, 500);
    })
    .catch(async (error) => {
        clearInterval(startupInterval);
        console.error('Backend failed to start:', error);
        await showError(`Impossible de démarrer le serveur: ${error.message}`);
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

async function showError(message) {
  console.error('Application Error:', message);
  
  if (mainWindow && !mainWindow.isDestroyed()) {
    const errorScript = `
      try {
        document.body.innerHTML = \`
          <div style="padding: 20px; font-family: Arial, sans-serif; text-align: center;">
            <h2 style="color: #d32f2f;">Application Error</h2>
            <p>${message}</p>
            <p>Please restart the application or contact support if the problem persists.</p>
            <button onclick="window.location.reload()" style="padding: 8px 16px; margin-top: 10px;">Retry</button>
          </div>
        \`;
        true;
      } catch (e) {
        console.error('Error displaying error message:', e);
        false;
      }
    `;
    
    await safeExecuteJS(errorScript);
  }
}

// IPC handlers
ipcMain.handle('select-files', async (event, options) => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile', 'multiSelections'],
      filters: [
        { name: 'Excel Files', extensions: ['xlsx', 'xls'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      ...options
    });
    return result;
  } catch (error) {
    console.error('Error in select-files dialog:', error);
    return { canceled: true, filePaths: [] };
  }
});

// App event handlers
app.whenReady().then(() => {
  createWindow();
}).catch((error) => {
  console.error('Error during app ready:', error);
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill('SIGTERM');
    } catch (error) {
      console.error('Error killing Python process:', error);
    }
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
    try {
      pythonProcess.kill('SIGTERM');
    } catch (error) {
      console.error('Error killing Python process on quit:', error);
    }
  }
});