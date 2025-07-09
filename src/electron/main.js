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
      webSecurity: true,
      devTools: true  // Enable DevTools even in production
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
    
    // Add comprehensive frontend logging
    mainWindow.webContents.executeJavaScript(`
        console.log('=== FRONTEND LOGGING INITIALIZED ===');
        
        // 1. Capture all fetch requests (API calls)
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            console.log('[DEBUG] API Request:', {
                url: args[0],
                method: args[1]?.method || 'GET',
                body: args[1]?.body ? 'FormData/Body present' : 'No body'
            });
            
            return originalFetch.apply(this, args)
                .then(response => {
                    console.log('[OK] API Response:', {
                        url: args[0],
                        status: response.status,
                        ok: response.ok
                    });
                    return response;
                })
                .catch(error => {
                    console.error('[ERROR] API Error:', {
                        url: args[0],
                        error: error.message
                    });
                    throw error;
                });
        };
        
        // 2. Capture file selections
        document.addEventListener('change', function(e) {
            if (e.target.type === 'file') {
                console.log('[DEBUG] File Selected:', {
                    inputId: e.target.id,
                    files: Array.from(e.target.files).map(f => \`\${f.name} (\${f.size} bytes)\`)
                });
            }
        });
        
        // 3. Capture all button clicks
        document.addEventListener('click', function(e) {
            if (e.target.tagName === 'BUTTON' || e.target.type === 'submit' || e.target.closest('button')) {
                const button = e.target.tagName === 'BUTTON' ? e.target : e.target.closest('button');
                console.log('[DEBUG] Button Clicked:', {
                    text: button.textContent?.trim() || button.value,
                    id: button.id,
                    class: button.className
                });
            }
        });
        
        // 4. Capture form submissions
        document.addEventListener('submit', function(e) {
            console.log('[DEBUG] Form Submitted:', {
                formId: e.target.id,
                action: e.target.action || 'No action'
            });
        });
        
        // 5. Capture navigation/tab changes
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('nav-tab') || e.target.closest('.nav-tab')) {
                console.log('[DEBUG] Tab Changed:', {
                    tab: e.target.textContent?.trim(),
                    id: e.target.id
                });
            }
        });
        
        // 6. Capture errors
        window.addEventListener('error', function(e) {
            console.error('[ERROR] JavaScript Error:', {
                message: e.message,
                filename: e.filename,
                line: e.lineno,
                column: e.colno
            });
        });
        
        // 7. Override console to send logs to Electron
        ['log', 'warn', 'error', 'info'].forEach(method => {
            const original = console[method];
            console[method] = function(...args) {
                // Keep original behavior
                original.apply(console, args);
            };
        });
        
        console.log('[OK] Frontend logging setup complete');
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
    // Test backend health first
    setTimeout(testBackendHealth, 5000);
    
    waitForBackend().then((port) => {
      console.log(`Backend ready on port ${port}, reloading UI`);
      mainWindow.loadFile(path.join(__dirname, '../frontend/index.html'));

      mainWindow.webContents.once('dom-ready', () => {
          mainWindow.webContents.executeJavaScript(`
              window.BACKEND_URL = 'http://localhost:${port}';
              console.log('Backend URL set to:', window.BACKEND_URL);
              
              // Test the connection from the frontend
              fetch(window.BACKEND_URL + '/health')
                .then(response => response.json())
                .then(data => console.log('Frontend health check succeeded:', data))
                .catch(error => console.error('Frontend health check failed:', error));
          `);
      });

    }).catch((error) => {
      console.error('Backend failed to start:', error);
      showBackendError(error.message);
    });
  }, 2000);

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (pythonProcess) {
      console.log('Terminating Python process...');
      pythonProcess.kill('SIGTERM');
    }
  });

  if (app.isPackaged) {
    mainWindow.webContents.openDevTools();
  }
}

function startPythonServer() {
  console.log('=== STARTING PYTHON SERVER ===');
  
  let backendExecutable;
  let workingDir;
  
  if (app.isPackaged) {
    console.log('Running in packaged mode');
    const resourcesPath = process.resourcesPath;
    console.log('Resources path:', resourcesPath);
    
    // List contents of resources directory
    console.log('Resources directory contents:');
    try {
      const resourceFiles = fs.readdirSync(resourcesPath);
      resourceFiles.forEach(file => {
        const fullPath = path.join(resourcesPath, file);
        const stats = fs.statSync(fullPath);
        console.log(`  ${stats.isDirectory() ? 'DIR' : 'FILE'}: ${file}`);
        
        // If it's a directory, list its contents too
        if (stats.isDirectory() && (file === 'backend' || file === 'docs')) {
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
      console.error('Searched paths:', possibleExecutablePaths);
      showBackendError('Backend executable not found. Please reinstall the application.');
      return;
    }
  } else {
    console.log('Running in development mode');
    const pythonScript = path.join(__dirname, '../backend/app.py');
    console.log('Looking for Python script:', pythonScript);
    
    if (fs.existsSync(pythonScript)) {
      console.log(`Using Python script: ${pythonScript}`);
      workingDir = path.dirname(pythonScript);
      
      // Try to spawn Python process
      try {
        console.log('Spawning Python process...');
        pythonProcess = spawn('python', [pythonScript], {
          cwd: workingDir,
          env: { ...process.env, PYTHONUNBUFFERED: '1' },
          windowsHide: true
        });
        
        console.log('Python process spawned successfully');
        setupPythonProcessHandlers();
        return;
      } catch (error) {
        console.error('Failed to start Python in development mode:', error);
        showBackendError('Failed to start development backend. Make sure Python is installed.');
        return;
      }
    } else {
      console.error('Development Python script not found at:', pythonScript);
      showBackendError('Development backend script not found.');
      return;
    }
  }
  
  console.log(`Backend executable: ${backendExecutable}`);
  console.log(`Working directory: ${workingDir}`);
  console.log('Executable exists:', fs.existsSync(backendExecutable));
  console.log('Working directory exists:', fs.existsSync(workingDir));
  
  try {
    console.log('Starting backend executable...');
    console.log('Spawn arguments:', {
      executable: backendExecutable,
      args: [],
      options: {
        cwd: workingDir,
        env: { 
          ...process.env, 
          PYTHONUNBUFFERED: '1',
        },
        windowsHide: true
      }
    });
    
    // Start the PyInstaller executable
    pythonProcess = spawn(backendExecutable, [], {
      cwd: workingDir,
      env: { 
        ...process.env, 
        PYTHONUNBUFFERED: '1',
      },
      windowsHide: true
    });

    console.log('Backend executable spawn completed');
    console.log('Process PID:', pythonProcess.pid);
    
    setupPythonProcessHandlers();
    
  } catch (error) {
    console.error('Exception starting backend executable:', error);
    console.error('Error stack:', error.stack);
    showBackendError(`Failed to start backend: ${error.message}`);
  }
}

function setupPythonProcessHandlers() {
  if (!pythonProcess) return;
  
  console.log(`Backend process PID: ${pythonProcess.pid}`);
  
  // Enhanced stdout logging
  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString().trim();
    console.log(`Backend stdout: ${output}`);
    
    // Log each line separately for better readability
    output.split('\n').forEach(line => {
      if (line.trim()) {
        console.log(`Backend stdout: ${line.trim()}`);
      }
    });
  });
  
  // Enhanced stderr logging
  pythonProcess.stderr.on('data', (data) => {
    const output = data.toString().trim();
    console.error(`Backend stderr: ${output}`);
    
    // Log each line separately for better readability
    output.split('\n').forEach(line => {
      if (line.trim()) {
        console.error(`Backend stderr: ${line.trim()}`);
      }
    });
  });
  
  pythonProcess.on('close', (code, signal) => {
    console.log(`Backend process exited with code ${code}, signal: ${signal}`);
    if (code !== 0 && code !== null) {
      console.error(`Backend process crashed with exit code ${code}`);
      showBackendError(`Backend process crashed with code ${code}`);
    }
  });
  
  pythonProcess.on('error', (error) => {
    console.error('Backend process error:', error);
    console.error('Error details:', {
      code: error.code,
      errno: error.errno,
      syscall: error.syscall,
      path: error.path,
      spawnargs: error.spawnargs
    });
    showBackendError(`Backend process error: ${error.message}`);
  });
  
  // Add exit handler
  pythonProcess.on('exit', (code, signal) => {
    console.log(`Backend process exit event - code: ${code}, signal: ${signal}`);
  });
  
  // Log process spawn success
  console.log('Backend process handlers set up successfully');
  console.log('Backend process details:', {
    pid: pythonProcess.pid,
    killed: pythonProcess.killed,
    connected: pythonProcess.connected
  });
}

async function waitForBackend() {
  const maxAttempts = 60; // 30 seconds (500ms * 60)
  const delay = 500; // 500ms between attempts
  
  console.log('Starting backend connection attempts...');
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      console.log(`Attempting to connect to backend (${attempt}/${maxAttempts})...`);
      
      // Check if Python process is still running
      if (pythonProcess && pythonProcess.killed) {
        console.error('Python process was killed, cannot continue');
        throw new Error('Python process was terminated');
      }
      
      // Try to connect to Flask backend on default port
      const response = await axios.get('http://localhost:5000/health', { 
        timeout: 1000 
      });
      
      console.log(`Backend response: ${response.status} - ${JSON.stringify(response.data)}`);
      
      if (response.status === 200) {
        console.log('Backend is ready!');
        return 5000; // Return the port number
      }
    } catch (error) {
      // Log connection errors periodically
      if (attempt % 10 === 0) {
        console.log(`Still waiting for backend... (attempt ${attempt})`);
        console.log(`Connection error: ${error.message}`);
        
        // Check if process is still alive
        if (pythonProcess) {
          console.log('Python process status:', {
            pid: pythonProcess.pid,
            killed: pythonProcess.killed,
            exitCode: pythonProcess.exitCode,
            signalCode: pythonProcess.signalCode
          });
        } else {
          console.error('Python process is null/undefined');
        }
      }
    }
    
    // Wait before next attempt
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  
  console.error('Backend connection timeout reached');
  console.error('Final Python process status:', pythonProcess ? {
    pid: pythonProcess.pid,
    killed: pythonProcess.killed,
    exitCode: pythonProcess.exitCode,
    signalCode: pythonProcess.signalCode
  } : 'Process is null');
  
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

// Add this with your existing IPC handlers
ipcMain.handle('frontend-log', async (event, level, args) => {
    const message = args.join(' ');
    console.log(`[FRONTEND-${level.toUpperCase()}] ${message}`);
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

// Add this new function to test backend health manually
function testBackendHealth() {
  console.log('=== TESTING BACKEND HEALTH ===');
  
  const testUrls = [
    'http://localhost:5000/health',
    'http://127.0.0.1:5000/health',
    'http://localhost:5000/api/debug-info'
  ];
  
  testUrls.forEach(async (url, index) => {
    try {
      console.log(`Testing URL ${index + 1}: ${url}`);
      const response = await axios.get(url, { timeout: 2000 });
      console.log(`✓ ${url} responded:`, response.status, response.data);
    } catch (error) {
      console.log(`✗ ${url} failed:`, error.message);
    }
  });
}