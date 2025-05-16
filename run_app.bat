@echo off
SETLOCAL

echo Starting ECT Technis...

REM Try to find Python in standard locations
SET PYTHON_CMD=python
WHERE %PYTHON_CMD% >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    SET PYTHON_CMD=python3
    WHERE %PYTHON_CMD% >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo ERROR: Python is not found in your PATH.
        echo Please make sure Python is installed and added to your PATH.
        pause
        exit /b 1
    )
)

REM Define the Streamlit command explicitly
SET ST_CMD=%PYTHON_CMD% -m streamlit

REM Run the application
echo Launching application with: %ST_CMD% run main.py
%ST_CMD% run main.py

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to run Streamlit. Attempting to install or repair...
    echo.
    %PYTHON_CMD% -m pip install --upgrade streamlit
    
    echo.
    echo Retrying to launch application...
    %ST_CMD% run main.py
    
    IF %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Could not start the application.
        echo Please make sure Streamlit is installed correctly with:
        echo     pip install streamlit
        echo.
        echo If you're using a virtual environment, make sure it's activated.
    )
)

pause
ENDLOCAL
