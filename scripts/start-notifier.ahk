#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

root := A_ScriptDir "\.."
script := root "\scripts\start-notifier.ps1"

RunHidden(args) {
    global root, script
    RunWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' script '" ' args, root, "Hide"
}

RunVisible(args) {
    global root, script
    Run 'powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File "' script '" ' args, root
}

A_TrayMenu.Delete()
A_TrayMenu.Add("Start", (*) => RunHidden("-Start"))
A_TrayMenu.Add("Stop", (*) => RunHidden("-Stop"))
A_TrayMenu.Add("Restart", (*) => RunHidden("-Restart"))
A_TrayMenu.Add()
A_TrayMenu.Add("Status", (*) => RunVisible("-Status"))
A_TrayMenu.Add("Today", (*) => RunVisible("-Today"))
A_TrayMenu.Add("Summary", (*) => RunVisible("-Summary"))
A_TrayMenu.Add("Test Telegram", (*) => RunHidden("-TestTelegram"))
A_TrayMenu.Add()
A_TrayMenu.Add("Exit AHK Control", (*) => ExitApp())

RunHidden("-Start")
