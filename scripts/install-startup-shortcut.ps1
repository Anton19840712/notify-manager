param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "Notify Manager.lnk"

if ($Remove) {
    Remove-Item -LiteralPath $ShortcutPath -Force -ErrorAction SilentlyContinue
    Write-Output "Startup shortcut removed: $ShortcutPath"
    exit 0
}

$Target = Join-Path $Root "scripts\start-notifier.ahk"
if (-not (Test-Path -LiteralPath $Target)) {
    throw "AutoHotkey launcher not found: $Target"
}

$AutoHotkeyCandidates = @(
    "C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
    "C:\Program Files\AutoHotkey\v2\AutoHotkey.exe",
    "C:\Program Files\AutoHotkey\AutoHotkey.exe",
    "C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe"
)
$AutoHotkey = $AutoHotkeyCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
if ($AutoHotkey) {
    $Shortcut.TargetPath = $AutoHotkey
    $Shortcut.Arguments = "`"$Target`""
} else {
    $Shortcut.TargetPath = $Target
    $Shortcut.Arguments = ""
}
$Shortcut.WorkingDirectory = $Root.Path
$Shortcut.Description = "Start notify-manager Telegram day reminders"
$Shortcut.Save()

Write-Output "Startup shortcut installed: $ShortcutPath"
