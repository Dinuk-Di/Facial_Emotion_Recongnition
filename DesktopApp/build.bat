@echo off
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

REM Check if virtual environment exists
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

REM Install/upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing application dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install application dependencies
    pause
    exit /b 1
)

echo Installing build dependencies...
pip install -r build_requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install build dependencies
    pause
    exit /b 1
)

REM Run the build script
echo.
echo Starting build process...
python build_installer.py

REM Check if build was successful
if exist "dist\FacialEmotionRecognition\FacialEmotionRecognition.exe" (
    echo.
    echo ========================================
    echo BUILD COMPLETED SUCCESSFULLY!
    echo ========================================
    echo.
    echo Generated files:
    if exist "dist\FacialEmotionRecognition\FacialEmotionRecognition.exe" (
        echo - Executable: dist\FacialEmotionRecognition\FacialEmotionRecognition.exe
    )
    if exist "FacialEmotionRecognition_Setup.exe" (
        echo - Installer: FacialEmotionRecognition_Setup.exe
    )
    if exist "FacialEmotionRecognition_Portable.zip" (
        echo - Portable: FacialEmotionRecognition_Portable.zip
    )
    echo.
    echo You can now distribute these files to users.
) else (
    echo.
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above and try again.
)

echo.
pause 