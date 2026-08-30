#Requires AutoHotkey v2.0

root := A_ScriptDir "\.."
script := root "\scripts\start-notifier.ps1"
Run 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' script '"', root

