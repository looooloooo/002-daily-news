# 002-daily-news setup script
# Run once to install dependencies and create Windows scheduled task
# Usage: Right-click → Run with PowerShell (or: powershell -ExecutionPolicy Bypass -File setup.ps1)

Write-Host "=== 002-daily-news Setup ===" -ForegroundColor Cyan

$projectDir = "C:\Users\AlyssaLin\cc projects\002-daily-news"

# Find Python
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) { $python = $found.Source; break }
}
if (-not $python) {
    Write-Host "ERROR: Python not found. Install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "Python: $python" -ForegroundColor Green

# Install dependencies
Write-Host "`nInstalling Python packages..." -ForegroundColor Yellow
& $python -m pip install -r "$projectDir\requirements.txt" --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed. Try manually: pip install -r requirements.txt" -ForegroundColor Red
} else {
    Write-Host "Dependencies OK." -ForegroundColor Green
}

# Check .env
$envFile = "$projectDir\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "`n.env not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item "$projectDir\.env.example" $envFile
    Write-Host "ACTION REQUIRED: Edit $envFile with your keys:" -ForegroundColor Red
    Write-Host "  1. DEEPSEEK_API_KEY   (from https://platform.deepseek.com)" -ForegroundColor Red
    Write-Host "  2. GMAIL_USERNAME      (your Gmail address)" -ForegroundColor Red
    Write-Host "  3. GMAIL_APP_PASSWORD  (from https://myaccount.google.com/apppasswords)" -ForegroundColor Red
    Write-Host ""
    $edit = Read-Host "Open .env now? (y/n)"
    if ($edit -eq "y") { notepad $envFile }
}

# Create scheduled task
$taskName = "002-daily-news"
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "`nRemoving old scheduled task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute $python `
    -Argument "`"$projectDir\01-main.py`"" `
    -WorkingDirectory $projectDir

$trigger = New-ScheduledTaskTrigger -Daily -At 7:50AM

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -WakeToRun:$false

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Daily news brief — fetch RSS, analyze with DeepSeek, send via Gmail" `
    -ErrorAction Stop

Write-Host "`nScheduled task '$taskName' created — runs daily at 7:50 AM" -ForegroundColor Green

# Offer test run
Write-Host ""
$test = Read-Host "Run a test now? (y/n)"
if ($test -eq "y") {
    Write-Host "Running 01-main.py..." -ForegroundColor Cyan
    & $python "$projectDir\01-main.py"
    Write-Host "`nCheck daily/ folder for today's brief." -ForegroundColor Green
}

Write-Host "`nSetup complete." -ForegroundColor Green
