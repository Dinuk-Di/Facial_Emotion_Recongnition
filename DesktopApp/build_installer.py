#!/usr/bin/env python3
"""
Build script for Facial Emotion Recognition Desktop App
This script automates the process of creating an executable and installer.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("Stdout:", e.stdout)
        if e.stderr:
            print("Stderr:", e.stderr)
        return False

def check_dependencies():
    """Check if required tools are installed"""
    print("Checking dependencies...")
    
    # Check PyInstaller
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
        print("✅ PyInstaller found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found. Installing...")
        run_command("pip install pyinstaller", "Installing PyInstaller")
    
    # Check NSIS (optional - will be checked later)
    nsis_path = None
    possible_paths = [
        r"C:\Program Files\NSIS\makensis.exe",
        r"C:\Program Files (x86)\NSIS\makensis.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            nsis_path = path
            break
    
    if nsis_path:
        print("✅ NSIS found")
    else:
        print("⚠️  NSIS not found. Installer creation will be skipped.")
    
    return nsis_path

def clean_build():
    """Clean previous build artifacts"""
    print("\nCleaning previous build artifacts...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Removed {dir_name}")
    
    # Clean .spec files (except main.spec)
    for file in os.listdir('.'):
        if file.endswith('.spec') and file != 'main.spec':
            os.remove(file)
            print(f"✅ Removed {file}")

def build_executable():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable...")
    
    # Build with PyInstaller
    success = run_command(
        "pyinstaller main.spec --clean",
        "Building executable with PyInstaller"
    )
    
    if not success:
        print("❌ Build failed!")
        return False
    
    # Check if executable was created
    exe_path = "dist/FacialEmotionRecognition/FacialEmotionRecognition.exe"
    if os.path.exists(exe_path):
        print(f"✅ Executable created: {exe_path}")
        return True
    else:
        print("❌ Executable not found!")
        return False

def create_installer(nsis_path):
    """Create installer using NSIS"""
    if not nsis_path:
        print("⚠️  Skipping installer creation (NSIS not found)")
        return False
    
    print("\nCreating installer...")
    
    # Create installer
    success = run_command(
        f'"{nsis_path}" installer.nsi',
        "Creating installer with NSIS"
    )
    
    if success:
        installer_path = "FacialEmotionRecognition_Setup.exe"
        if os.path.exists(installer_path):
            size_mb = os.path.getsize(installer_path) / (1024 * 1024)
            print(f"✅ Installer created: {installer_path} ({size_mb:.1f} MB)")
            return True
    
    print("❌ Installer creation failed!")
    return False

def create_portable_zip():
    """Create a portable ZIP version"""
    print("\nCreating portable ZIP...")
    
    if not os.path.exists("dist/FacialEmotionRecognition"):
        print("❌ Executable not found. Build first!")
        return False
    
    zip_name = "FacialEmotionRecognition_Portable.zip"
    
    # Remove existing zip
    if os.path.exists(zip_name):
        os.remove(zip_name)
    
    # Create zip
    success = run_command(
        f'powershell Compress-Archive -Path "dist/FacialEmotionRecognition/*" -DestinationPath "{zip_name}"',
        "Creating portable ZIP"
    )
    
    if success:
        size_mb = os.path.getsize(zip_name) / (1024 * 1024)
        print(f"✅ Portable ZIP created: {zip_name} ({size_mb:.1f} MB)")
        return True
    
    print("❌ Portable ZIP creation failed!")
    return False

def main():
    """Main build process"""
    print("🚀 Facial Emotion Recognition - Build Script")
    print("=" * 50)
    
    # Check dependencies
    nsis_path = check_dependencies()
    
    # Clean previous builds
    clean_build()
    
    # Build executable
    if not build_executable():
        print("❌ Build process failed!")
        sys.exit(1)
    
    # Create installer
    installer_created = create_installer(nsis_path)
    
    # Create portable version
    portable_created = create_portable_zip()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 BUILD SUMMARY")
    print("=" * 50)
    
    if os.path.exists("dist/FacialEmotionRecognition/FacialEmotionRecognition.exe"):
        print("✅ Executable: dist/FacialEmotionRecognition/FacialEmotionRecognition.exe")
    
    if installer_created:
        print("✅ Installer: FacialEmotionRecognition_Setup.exe")
    
    if portable_created:
        print("✅ Portable: FacialEmotionRecognition_Portable.zip")
    
    print("\n🎉 Build process completed!")
    
    if not installer_created:
        print("\n💡 To create an installer, install NSIS from: https://nsis.sourceforge.io/Download")
        print("   Then run this script again.")

if __name__ == "__main__":
    main() 