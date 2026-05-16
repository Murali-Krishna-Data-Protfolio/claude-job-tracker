# setup_scheduler.ps1
# Run this ONCE (as Administrator) to register the daily Task Scheduler job.
# Usage:  powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1

$TaskName   = "JobApplyTracker_Daily"
$ScriptPath = Join-Path $PSScriptRoot "run_daily.bat"
$LogDir     = Join-Path $PSScriptRoot "outputs"

# Remove old task if it exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task: $TaskName"
}

# Action: run the batch file
$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$ScriptPath`"" `
    -WorkingDirectory $PSScriptRoot

# Trigger: every day at 08:00
$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00"

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -WakeToRun:$false

# Register
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Daily English-speaking job search in France (Indeed via Claude Code)" `
    -RunLevel Limited

Write-Host ""
Write-Host "Task '$TaskName' registered successfully." -ForegroundColor Green
Write-Host "It will run every day at 08:00."
Write-Host ""
Write-Host "To run it immediately:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "To view it in Task Scheduler:"
Write-Host "  taskschd.msc"
