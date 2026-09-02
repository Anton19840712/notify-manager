param(
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status,
    [switch]$Foreground,
    [switch]$Once,
    [switch]$Summary,
    [switch]$Today,
    [switch]$Processes,
    [switch]$TestTelegram,
    [switch]$SyncBotCommands,
    [switch]$TestDesktop,
    [switch]$DesktopOn,
    [switch]$DesktopOff,
    [switch]$DesktopStatus,
    [int]$RecalcFood = 0,
    [int]$RecalcMinInterval = 135,
    [string]$RecalcAnchor = "",
    [int]$LastMealNumber = 1,
    [string]$ShiftDay = ""
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:PYTHONPATH = Join-Path $Root "src"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$PidPath = Join-Path $Root "data\notifier.pid"
$LogDir = Join-Path $Root "logs"
$OutLog = Join-Path $LogDir "notifier.out.log"
$ErrLog = Join-Path $LogDir "notifier.err.log"

function Get-NotifierProcess {
    if (-not (Test-Path -LiteralPath $PidPath)) {
        return $null
    }

    $rawPid = (Get-Content -LiteralPath $PidPath -Raw).Trim()
    if (-not ($rawPid -match '^\d+$')) {
        Remove-Item -LiteralPath $PidPath -Force
        return $null
    }

    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $rawPid" -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Remove-Item -LiteralPath $PidPath -Force
        return $null
    }
    if (($process.CommandLine -notlike "*day_notifier*") -or ($process.CommandLine -notlike "*$($Root.Path)*")) {
        Remove-Item -LiteralPath $PidPath -Force
        return $null
    }

    return $process
}

function Invoke-NotifierForeground {
    param([string[]]$ExtraArgs)

    $ArgsList = @("-m", "day_notifier", "--root", $Root.Path) + $ExtraArgs
    python @ArgsList
}

function Start-Notifier {
    $existing = Get-NotifierProcess
    if ($null -ne $existing) {
        Write-Output "notify-manager already running, pid=$($existing.ProcessId)"
        return
    }

    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $PidPath) | Out-Null

    $python = (Get-Command python).Source
    $arguments = @("-m", "day_notifier", "--root", "`"$($Root.Path)`"")
    $process = Start-Process `
        -FilePath $python `
        -ArgumentList $arguments `
        -WorkingDirectory $Root.Path `
        -WindowStyle Hidden `
        -RedirectStandardOutput $OutLog `
        -RedirectStandardError $ErrLog `
        -PassThru

    Set-Content -LiteralPath $PidPath -Value $process.Id -Encoding ASCII
    Write-Output "notify-manager started, pid=$($process.Id)"
}

function Stop-Notifier {
    $existing = Get-NotifierProcess
    if ($null -eq $existing) {
        Write-Output "notify-manager is not running"
        return
    }

    Stop-Process -Id $existing.ProcessId -Force
    Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
    Write-Output "notify-manager stopped, pid=$($existing.ProcessId)"
}

if ($Once) {
    Invoke-NotifierForeground @("--once")
    exit $LASTEXITCODE
}
if ($Summary) {
    Invoke-NotifierForeground @("--summary")
    exit $LASTEXITCODE
}
if ($Today) {
    Invoke-NotifierForeground @("--today")
    exit $LASTEXITCODE
}
if ($Processes) {
    Invoke-NotifierForeground @("--processes")
    exit $LASTEXITCODE
}
if ($TestTelegram) {
    Invoke-NotifierForeground @("--test-telegram")
    exit $LASTEXITCODE
}
if ($SyncBotCommands) {
    Invoke-NotifierForeground @("--sync-bot-commands")
    exit $LASTEXITCODE
}
if ($TestDesktop) {
    Invoke-NotifierForeground @("--test-desktop")
    exit $LASTEXITCODE
}
if ($DesktopOn) {
    Invoke-NotifierForeground @("--desktop-on")
    exit $LASTEXITCODE
}
if ($DesktopOff) {
    Invoke-NotifierForeground @("--desktop-off")
    exit $LASTEXITCODE
}
if ($DesktopStatus) {
    Invoke-NotifierForeground @("--desktop-status")
    exit $LASTEXITCODE
}
if ($RecalcFood -gt 0) {
    $recalcArgs = @(
        "--recalc-food", [string]$RecalcFood,
        "--recalc-min-interval", [string]$RecalcMinInterval,
        "--last-meal-number", [string]$LastMealNumber
    )
    if ($RecalcAnchor) {
        $recalcArgs += @("--recalc-anchor", $RecalcAnchor)
    }
    Invoke-NotifierForeground $recalcArgs
    exit $LASTEXITCODE
}
if ($ShiftDay) {
    Invoke-NotifierForeground @("--shift-day", $ShiftDay)
    exit $LASTEXITCODE
}
if ($Status) {
    $existing = Get-NotifierProcess
    if ($null -eq $existing) {
        Write-Output "notify-manager is not running"
    } else {
        Write-Output "notify-manager running, pid=$($existing.ProcessId), started=$($existing.CreationDate)"
    }
    exit 0
}
if ($Stop) {
    Stop-Notifier
    exit 0
}
if ($Restart) {
    Stop-Notifier
    Start-Notifier
    exit 0
}
if ($Foreground) {
    Invoke-NotifierForeground @()
    exit $LASTEXITCODE
}

Start-Notifier
