param(
    [switch]$Once,
    [switch]$Summary
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:PYTHONPATH = Join-Path $Root "src"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$ArgsList = @("-m", "day_notifier", "--root", $Root.Path)
if ($Once) {
    $ArgsList += "--once"
}
if ($Summary) {
    $ArgsList += "--summary"
}

python @ArgsList
