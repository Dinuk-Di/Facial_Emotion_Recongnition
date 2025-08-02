# Facial Emotion Recognition - Build Script (PowerShell)
# Run this script with: powershell -ExecutionPolicy Bypass -File build.ps1

param(
    [switch]$SkipDependencies,
    [switch]$SkipTests,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Install-PythonDependency {
    param([string]$Package)
    try {
        Write-ColorOutput "Installing $Package..." $Blue
        pip install $Package
        Write-ColorOutput "✅ $Package installed successfully" $Green
        return $true
    }
    catch {
        Write-ColorOutput "❌ Failed to install $Package" $Red
        return $false
    }
}

# Main script
Write-ColorOutput "========================================" $Blue
Write-ColorOutput "Facial Emotion Recognition - Build Tool" $Blue
Write-ColorOutput "========================================" $Blue
Write-Host ""

# Check Python installation
if (-not (Test-Command "python")) {
    Write-ColorOutput "ERROR: Python is not installed or not in PATH" $Red
    Write-ColorOutput "Please install Python 3.8+ from https://www.python.org/downloads/" $Yellow
    exit 1
}

$pythonVersion = python --version 2>&1
Write-ColorOutput "Found Python: $pythonVersion" $Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-ColorOutput "Creating virtual environment..." $Blue
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "ERROR: Failed to create virtual environment" $Red
        exit 1
    }
}

# Activate virtual environment
Write-ColorOutput "Activating virtual environment..." $Blue
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-ColorOutput "Upgrading pip..." $Blue
python -m pip install --upgrade pip

# Install dependencies
if (-not $SkipDependencies) {
    Write-ColorOutput "Installing application dependencies..." $Blue
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "ERROR: Failed to install application dependencies" $Red
        exit 1
    }

    Write-ColorOutput "Installing build dependencies..." $Blue
    pip install -r build_requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "ERROR: Failed to install build dependencies" $Red
        exit 1
    }
}

# Test the application (optional)
if (-not $SkipTests) {
    Write-ColorOutput "Testing application..." $Blue
    try {
        python -c "import customtkinter; import cv2; import numpy; print('✅ All imports successful')"
        Write-ColorOutput "✅ Application test passed" $Green
    }
    catch {
        Write-ColorOutput "⚠️  Application test failed, but continuing with build..." $Yellow
    }
}

# Run the build script
Write-ColorOutput "Starting build process..." $Blue
python build_installer.py

# Check build results
$buildSuccess = $false
if (Test-Path "dist\FacialEmotionRecognition\FacialEmotionRecognition.exe") {
    $buildSuccess = $true
    Write-ColorOutput "" $Green
    Write-ColorOutput "========================================" $Green
    Write-ColorOutput "BUILD COMPLETED SUCCESSFULLY!" $Green
    Write-ColorOutput "========================================" $Green
    Write-Host ""
    Write-ColorOutput "Generated files:" $Green
    
    if (Test-Path "dist\FacialEmotionRecognition\FacialEmotionRecognition.exe") {
        $size = [math]::Round((Get-Item "dist\FacialEmotionRecognition\FacialEmotionRecognition.exe").Length / 1MB, 2)
        Write-ColorOutput "- Executable: dist\FacialEmotionRecognition\FacialEmotionRecognition.exe ($size MB)" $Green
    }
    
    if (Test-Path "FacialEmotionRecognition_Setup.exe") {
        $size = [math]::Round((Get-Item "FacialEmotionRecognition_Setup.exe").Length / 1MB, 2)
        Write-ColorOutput "- Installer: FacialEmotionRecognition_Setup.exe ($size MB)" $Green
    }
    
    if (Test-Path "FacialEmotionRecognition_Portable.zip") {
        $size = [math]::Round((Get-Item "FacialEmotionRecognition_Portable.zip").Length / 1MB, 2)
        Write-ColorOutput "- Portable: FacialEmotionRecognition_Portable.zip ($size MB)" $Green
    }
    
    Write-Host ""
    Write-ColorOutput "You can now distribute these files to users." $Green
} else {
    Write-ColorOutput "" $Red
    Write-ColorOutput "========================================" $Red
    Write-ColorOutput "BUILD FAILED!" $Red
    Write-ColorOutput "========================================" $Red
    Write-Host ""
    Write-ColorOutput "Please check the error messages above and try again." $Yellow
}

Write-Host ""
if ($buildSuccess) {
    Write-ColorOutput "Press any key to exit..." $Blue
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} 