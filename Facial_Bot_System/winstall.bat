@echo off
echo Installing required dependencies...
pip install pyqt5 opencv-python ultralytics mss pillow langgraph ollama pywin32 pystray
echo Downloading AI models...
ollama pull qwen:4b
ollama pull llava
echo Installation complete!
pause