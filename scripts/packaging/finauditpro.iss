; Inno Setup 6 Script for FinAuditPro (Windows x64)
; Builds single-file standalone offline installer

#define MyAppName "FinAuditPro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "FinAuditPro Team"
#define MyAppURL "https://github.com/Coderaryanyadav/FinAuditPro"
#define MyAppExeName "FinAuditPro.exe"

[Setup]
AppId={{D68F23A1-74B0-4A63-952B-849E9EFA7F11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\..\dist
OutputBaseFilename=FinAuditPro-Setup-{#MyAppVersion}-x64
SetupIconFile=..\..\src\finauditpro\assets\icons\FinAuditPro.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\FinAuditPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\src\finauditpro\assets\icons\FinAuditPro.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\src\finauditpro\assets\icons\FinAuditPro.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
