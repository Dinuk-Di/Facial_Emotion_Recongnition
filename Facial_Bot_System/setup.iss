; setup.iss
[Setup]
AppName=Emotion Assistant
AppVersion=1.0
DefaultDirName={pf}\Emotion Assistant
DefaultGroupName=Emotion Assistant
UninstallDisplayIcon={app}\EmotionAssistant.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=EmotionAssistant_Setup
SetupIconFile=icon.ico

[Files]
Source: "dist\EmotionAssistant.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "Models\*"; DestDir: "{app}\Models"; Flags: ignoreversion recursesubdirs
Source: "icon.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Emotion Assistant"; Filename: "{app}\EmotionAssistant.exe"
Name: "{userdesktop}\Emotion Assistant"; Filename: "{app}\EmotionAssistant.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\EmotionAssistant.exe"; Description: "Run Emotion Assistant"; Flags: postinstall nowait