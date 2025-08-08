const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');
const fs = require('fs');

// Global variables
let mainWindow;
let pythonProcess;
const BACKEND_PORT = 5000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

/**
 * Setup application error handling
 */
function setupErrorHandling() {
  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Promise Rejection at:', promise, 'reason:', reason);
  });

  process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
  });
}

/**
 * Configure application logging
 * @returns {string} Path to the log file
 */
function setupLogging() {
  const logDir = path.join(app.getPath('userData'), 'logs');
  
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  
  const logFile = path.join(logDir, `app-${new Date().toISOString().replace(/[:.]/g, '-')}.log`);
  const logStream = fs.createWriteStream(logFile, { flags: 'a' });
  
  // Override console methods to write to log file
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
  
  // Log app startup info
  console.log('=== ECT TECHNIS STARTUP ===');
  console.log('App version:', app.getVersion());
  console.log('Platform:', process.platform, process.arch);
  console.log('Is packaged:', app.isPackaged);
  
  return logFile;
}

/**
 * Create the main application window
 */
function createWindow() {
  setupErrorHandling();
  setupLogging();
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: false,
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

  // Show loading screen
  showLoadingScreen()
    .then(() => startApplicationFlow())
    .catch(error => {
      console.error('Failed to start application:', error);
      showError('Failed to start application: ' + error.message);
    });

  // Window event handlers
  mainWindow.on('closed', cleanupOnExit);
}

/**
 * Show initial loading screen
 */
async function showLoadingScreen() {
  try {
    await mainWindow.loadFile(path.join(__dirname, '../frontend/loading.html'));
    console.log('Loading screen displayed');
    mainWindow.show();
  } catch (error) {
    console.error('Failed to load loading screen:', error);
    mainWindow.show(); // Show window anyway even if loading screen fails
    throw error;
  }
}

/**
 * Start the main application flow
 */
async function startApplicationFlow() {
  try {
    // Start backend server
    startPythonServer();
    
    // Wait for backend to be ready
    await waitForBackend();
    
    // Update loading progress
    await updateLoadingProgress('100%', 'Chargement de l\'application...');
    
    // Load main application after short delay
    setTimeout(async () => {
      try {
        await mainWindow.loadFile(path.join(__dirname, '../frontend/index.html'));
        console.log('Main application loaded successfully');
        
        // Set backend URL in window
        await mainWindow.webContents.executeJavaScript(`
          window.BACKEND_URL = '${BACKEND_URL}';
          console.log('Backend URL set to:', window.BACKEND_URL);
        `);
      } catch (error) {
        console.error('Error loading main application:', error);
        showError('Failed to load application interface');
      }
    }, 500);
  } catch (error) {
    console.error('Application startup failed:', error);
    showError(`Impossible de démarrer l'application: ${error.message}`);
  }
}

/**
 * Start the Python backend server
 */
function startPythonServer() {
  console.log('Starting Python backend...');
  
  try {
    if (app.isPackaged) {
      startPackagedBackend();
    } else {
      startDevelopmentBackend();
    }
    
    // Set up process event handlers if successfully started
    if (pythonProcess) {
      setupPythonProcessHandlers();
    }
  } catch (error) {
    console.error('Failed to start backend:', error);
    showError(`Failed to start backend: ${error.message}`);
  }
}

/**
 * Start the packaged backend executable
 */
function startPackagedBackend() {
  // Find the packaged executable
  const resourcesPath = process.resourcesPath;
  const possiblePaths = [
    path.join(resourcesPath, 'backend', 'ect-backend.exe'),
    path.join(resourcesPath, 'app', 'backend', 'ect-backend.exe')
  ];
  
  let backendExecutable;
  let workingDir;
  
  for (const testPath of possiblePaths) {
    if (fs.existsSync(testPath)) {
      backendExecutable = testPath;
      workingDir = path.dirname(testPath);
      break;
    }
  }

  if (!backendExecutable) {
    throw new Error('Backend executable not found');
  }
  
  console.log(`Starting packaged backend: ${backendExecutable}`);
  pythonProcess = spawn(backendExecutable, [], {
    cwd: workingDir,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
    windowsHide: true
  });
  
  console.log('Backend process started, PID:', pythonProcess.pid);
}

/**
 * Start the development backend using Python interpreter
 */
function startDevelopmentBackend() {
  const pythonScript = path.join(__dirname, '../backend/app.py');
  
  if (!fs.existsSync(pythonScript)) {
    throw new Error('Development Python script not found');
  }
  
  const workingDir = path.dirname(pythonScript);
  
  console.log(`Starting development backend: ${pythonScript}`);
  pythonProcess = spawn('python', [pythonScript], {
    cwd: workingDir,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
    windowsHide: true
  });
  
  console.log('Development backend started, PID:', pythonProcess.pid);
}

/**
 * Set up event handlers for the Python backend process
 */
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

/**
 * Wait for the backend server to be ready
 * @returns {Promise<number>} The port number of the backend
 */
async function waitForBackend() {
  const maxAttempts = 60;
  const delay = 500;
  
  console.log('Waiting for backend to start...');
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      if (pythonProcess && pythonProcess.killed) {
        throw new Error('Python process was terminated');
      }
      
      const response = await axios.get(`${BACKEND_URL}/health`, { timeout: 2000 });
      
      if (response.status === 200) {
        console.log('Backend is ready');
        return BACKEND_PORT;
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

/**
 * Update the loading progress in the loading screen
 * @param {string} progress - Progress percentage (e.g. '50%')
 * @param {string} message - Status message to display
 */
async function updateLoadingProgress(progress, message) {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  
  try {
    await mainWindow.webContents.executeJavaScript(`
      const progressBar = document.getElementById('progress-bar');
      const statusMessage = document.getElementById('status-message');
      if (progressBar) progressBar.style.width = '${progress}';
      if (statusMessage) statusMessage.innerText = '${message}';
    `);
  } catch (error) {
    console.log('Progress update failed, but continuing:', error.message);
  }
}

/**
 * Show an error message to the user
 * @param {string} message - Error message to display
 */
async function showError(message) {
  console.error('Application Error:', message);
  
  if (mainWindow && !mainWindow.isDestroyed()) {
    try {
      await mainWindow.webContents.executeJavaScript(`
        document.body.innerHTML = \`
          <div style="padding: 20px; font-family: Arial, sans-serif; text-align: center;">
            <h2 style="color: #d32f2f;">Application Error</h2>
            <p>${message}</p>
            <p>Please restart the application or contact support if the problem persists.</p>
            <button onclick="window.location.reload()" style="padding: 8px 16px; margin-top: 10px;">Retry</button>
          </div>
        \`;
      `);
    } catch (error) {
      console.error('Failed to display error message:', error);
    }
  }
}

/**
 * Clean up resources when the application is exiting
 */
function cleanupOnExit() {
  console.log('Cleaning up resources...');
  
  if (pythonProcess) {
    try {
      pythonProcess.kill('SIGTERM');
      pythonProcess = null;
    } catch (error) {
      console.error('Error killing Python process:', error);
    }
  }
  
  mainWindow = null;
}

// Register IPC handlers
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
app.whenReady().then(createWindow).catch((error) => {
  console.error('Error during app ready:', error);
});

app.on('window-all-closed', () => {
  cleanupOnExit();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', cleanupOnExit);