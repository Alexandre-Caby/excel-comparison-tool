@echo off
echo Building Excel Comparison Tool...
echo.

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

echo Python detected! Using: 
%PYTHON_CMD% --version

rem Ensure we have the required directories
if not exist "dist" mkdir dist

echo Checking for running application...
tasklist /FI "IMAGENAME eq ECT_Technis.exe" 2>NUL | find /I /N "ECT_Technis.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo.
    echo WARNING: ECT_Technis.exe is currently running.
    echo Please close the application before building a new version.
    echo.
    choice /C YN /M "Do you want to terminate the running application and continue?"
    if errorlevel 2 (
        echo Build cancelled.
        pause
        exit /b 1
    ) else (
        echo Attempting to terminate ECT_Technis.exe...
        taskkill /F /IM ECT_Technis.exe >nul 2>&1
        ping -n 2 127.0.0.1 >nul
    )
)

REM Delete the old executable if it exists to prevent permission errors
if exist "dist\ECT_Technis.exe" (
    echo Removing old executable...
    del /F /Q "dist\ECT_Technis.exe" >nul 2>&1
    if exist "dist\ECT_Technis.exe" (
        echo Warning: Could not delete existing executable. It may be in use.
        echo Using a temporary file name...
        set "OUTPUT_NAME=ECT_Technis_%RANDOM%.exe"
    ) else (
        set "OUTPUT_NAME=ECT_Technis.exe"
    )
) else (
    set "OUTPUT_NAME=ECT_Technis.exe"
)

echo Installing dependencies...
if %errorlevel% NEQ 0 (
    call %PYTHON_CMD% -m pip install -r requirements.txt
    call %PYTHON_CMD% -m pip install pyinstaller
    echo Dependencies installation status: %ERRORLEVEL%
    if %errorlevel% NEQ 0 (
        echo Dependencies installed successfully.
    ) else (
        echo Dependencies installation failed.
    )
) else (
    echo Dependencies already installed.
)

echo Verifying run.py exists...
if not exist "run.py" (
    echo ERROR: run.py file not found!
    echo Please make sure run.py exists in the current directory.
    pause
    exit /b 1
)

echo Building executable with PyInstaller...
call %PYTHON_CMD% -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name "%OUTPUT_NAME:~0,-4%" ^
    --clean ^
    --add-data "src;src" ^
    --icon="src/static/images/icon_excel_comparison.ico" ^
    --hidden-import streamlit ^
    --hidden-import streamlit.web.bootstrap ^
    --hidden-import numpy ^
    --hidden-import pandas ^
    --hidden-import openpyxl ^
    --hidden-import xlsxwriter ^
    run.py

echo.
if exist "dist\%OUTPUT_NAME%" (
    echo Build successful! Executable is in the "dist" folder.
    dir /b "dist\%OUTPUT_NAME%"
    
    rem If we used a temporary name, try to rename it back now
    if not "%OUTPUT_NAME%"=="ECT_Technis.exe" (
        echo Attempting to rename to ECT_Technis.exe...
        if exist "dist\ECT_Technis.exe" del /F /Q "dist\ECT_Technis.exe" >nul 2>&1
        ren "dist\%OUTPUT_NAME%" "ECT_Technis.exe" >nul 2>&1
        if exist "dist\ECT_Technis.exe" (
            echo Successfully renamed to ECT_Technis.exe
        ) else (
            echo Could not rename file. Please rename "%OUTPUT_NAME%" to "ECT_Technis.exe" manually.
        )
    )
) else (
    echo Build failed. Check the errors above.
)

echo Script ending.