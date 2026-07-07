# Builds MAD1-Prep.exe. Run from the repo root:
#   powershell -ExecutionPolicy Bypass -File desktop/build_exe.ps1
# Needs: python, pip install pyinstaller pillow

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot   # repo root
Set-Location $root

# 1. stage the app content (flat files at repo root only)
$stage = Join-Path $env:TEMP "mad1prep-content"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force $stage | Out-Null
Get-ChildItem $root -File | Where-Object { $_.Extension -in ".html", ".css", ".js", ".png", ".ico", ".svg", ".gif" } |
    Copy-Item -Destination $stage

# 2. icon
if (-not (Test-Path "$root\desktop\icon.ico")) {
    Push-Location "$root\desktop"; python make_icon.py; Pop-Location
}

# 3. build
python -m PyInstaller --noconfirm --onefile --console `
    --name "MAD1-Prep" `
    --icon "$root\desktop\icon.ico" `
    --add-data "$stage;content" `
    --distpath "$root\desktop\dist" `
    --workpath "$root\desktop\build" `
    --specpath "$root\desktop" `
    "$root\desktop\launcher.py"

Write-Host ""
Write-Host "Done -> desktop\dist\MAD1-Prep.exe"
