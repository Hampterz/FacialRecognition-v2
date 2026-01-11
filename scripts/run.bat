@echo off
echo ========================================
echo Face Recognition System - Startup
echo ========================================
echo.

REM Check for conda Python first (has dlib pre-installed)
set PYTHON_CMD=python
set CONDA_FOUND=0

REM Try common conda locations first (faster)
if exist "%USERPROFILE%\miniconda3\python.exe" (
    set PYTHON_CMD=%USERPROFILE%\miniconda3\python.exe
    set CONDA_FOUND=1
    goto python_found
)
if exist "%USERPROFILE%\anaconda3\python.exe" (
    set PYTHON_CMD=%USERPROFILE%\anaconda3\python.exe
    set CONDA_FOUND=1
    goto python_found
)
if exist "C:\ProgramData\miniconda3\python.exe" (
    set PYTHON_CMD=C:\ProgramData\miniconda3\python.exe
    set CONDA_FOUND=1
    goto python_found
)

REM Try to get conda base path using conda command
where conda >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('conda info --base 2^>nul') do set CONDA_BASE=%%i
    if defined CONDA_BASE (
        if exist "%CONDA_BASE%\python.exe" (
            set PYTHON_CMD=%CONDA_BASE%\python.exe
            set CONDA_FOUND=1
            goto python_found
        )
    )
)

REM Check if Python is installed
:python_found
if %CONDA_FOUND% equ 1 (
    echo Using Conda Python (has dlib pre-installed)
) else if "%PYTHON_CMD%"=="python" (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH!
        echo Please install Python 3.9+ from https://www.python.org/downloads/
        echo OR install Anaconda/Miniconda which includes dlib
        pause
        exit /b 1
    )
)

echo [1/3] Checking Python installation...
%PYTHON_CMD% --version
if errorlevel 1 (
    echo ERROR: Python command failed!
    pause
    exit /b 1
)
echo.

echo [2/3] Checking dependencies...
%PYTHON_CMD% -c "import cv2" >nul 2>&1
if errorlevel 1 (
    echo Dependencies not found.
    echo.
    echo IMPORTANT: Installing dependencies may require Visual Studio C++ Build Tools.
    echo If installation fails, run install_dependencies.bat for detailed instructions.
    echo.
    echo Installing from requirements.txt...
    echo This may take several minutes...
    echo.
    %PYTHON_CMD% -m pip install --upgrade pip
    if errorlevel 1 (
        echo ERROR: Failed to upgrade pip!
        pause
        exit /b 1
    )
    %PYTHON_CMD% -m pip install -r requirements.txt
    REM Also install Smart Attendance dependencies
    %PYTHON_CMD% -m pip install gspread oauth2client
    if errorlevel 1 (
        echo.
        echo ========================================
        echo ERROR: Failed to install some dependencies!
        echo ========================================
        echo.
        echo This is likely because dlib requires Visual Studio C++ Build Tools.
        echo.
        echo To fix this:
        echo 1. Install Visual Studio Build Tools from:
        echo    https://visualstudio.microsoft.com/downloads/
        echo 2. Select "Desktop development with C++" workload
        echo 3. Run install_dependencies.bat or try again
        echo.
        echo OR if using conda, install dlib first:
        echo   conda install -c conda-forge dlib
        echo   %PYTHON_CMD% -m pip install face-recognition
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed successfully!
    echo.
) else (
    echo Dependencies are installed.
    echo.
)

echo [3/3] Starting application...
echo.
%PYTHON_CMD% app.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start!
    echo Check the error messages above.
    pause
    exit /b 1
)

pause
