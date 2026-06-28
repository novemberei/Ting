Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
desktopPath = WshShell.SpecialFolders("Desktop")

Set shortcut = WshShell.CreateShortcut(desktopPath & "\Ting 语音输入.lnk")
shortcut.TargetPath = projectDir & "\start.bat"
shortcut.WorkingDirectory = projectDir
shortcut.WindowStyle = 7
shortcut.Description = "Ting 语音输入工具"
shortcut.Save

WScript.Echo "桌面快捷方式已创建！"
