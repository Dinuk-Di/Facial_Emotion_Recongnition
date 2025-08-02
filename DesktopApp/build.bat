@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Facial Emotion Recognition - Build Tool
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install app dependencies
echo Installing application dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install application dependencies
    pause
    exit /b 1
)

REM Install build dependencies (e.g., pyinstaller)
echo Installing build dependencies...
pip install -r build_requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install build dependencies
    pause
    exit /b 1
)

REM Run build script (should use PyInstaller inside)
echo.
echo Starting build process...
python build_installer.py
if errorlevel 1 (
    echo ERROR: Build script failed
    pause
    exit /b 1
)

REM Check for built executable
set "EXE_PATH=dist\FacialEmotionRecognition.exe"
set "SETUP_PATH=FacialEmotionRecognition_Setup.exe"
set "ZIP_PATH=FacialEmotionRecognition_Portable.zip"

echo.
if exist "%EXE_PATH%" (
    echo ========================================
    echo BUILD COMPLETED SUCCESSFULLY!
    echo ========================================
    echo.
    echo Generated files:
    echo - Executable: %EXE_PATH%
    if exist "%SETUP_PATH%" (
        echo - Installer: %SETUP_PATH%
    )
    if exist "%ZIP_PATH%" (
        echo - Portable: %ZIP_PATH%
    )
    echo.
    echo You can now distribute these files to users.
) else (
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo Please check the error messages above and try again.
)

echo.
pause
