# build.py
import os
import subprocess
import sys
import shutil
from PyInstaller.__main__ import run

# Create build directory
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')
os.makedirs('dist', exist_ok=True)

# PyInstaller configuration
pyinstaller_args = [
    'main.py',
    '--name=EmotionAssistant',
    '--onefile',
    '--windowed',
    '--icon=icon.ico',
    '--add-data=Models;Models',
    '--add-data=icon.png;.',
]

# Build executable
run(pyinstaller_args)

# Create installer directory
if os.path.exists('installer'):
    shutil.rmtree('installer')
os.makedirs('installer', exist_ok=True)

# Build installer
subprocess.call(['iscc', 'setup.iss'])

print("Build completed! Installer is in 'installer' directory")