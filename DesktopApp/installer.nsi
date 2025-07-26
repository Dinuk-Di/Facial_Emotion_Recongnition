Outfile "DesktopAppSetup.exe"
InstallDir "$PROGRAMFILES\DesktopApp"
RequestExecutionLevel admin

Page directory
Page instfiles

Section ""
  SetOutPath $INSTDIR
  File "dist\DesktopApp\DesktopApp.exe"
  File /r "dist\DesktopApp\assets"
  File /r "dist\DesktopApp\Models"
  CreateShortCut "$DESKTOP\Desktop App.lnk" "$INSTDIR\DesktopApp.exe"
SectionEnd
