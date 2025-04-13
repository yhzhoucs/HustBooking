$pythonPath = (Get-Item -Path 'python310').FullName
$pythonExe = Join-Path -Path $pythonPath -ChildPath 'python.exe'
$scriptPath = Join-Path -Path $pwd.Path -ChildPath 'main.py'

# replace it to your Tesseract path
$tesseractPath = "C:\Program Files\Tesseract-OCR"
$command = @"
Set-Location -Path '$($pwd.Path)'
`$env:Path += ';$tesseractPath'
& $pythonExe $scriptPath
"@

$action1 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoExit -Command `"$command`""
$action2 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command `"Unregister-ScheduledTask -TaskName HustBooking -Confirm:`$false`""
$triggerParams = @{
    Once = $true
    At = Get-Date "2025-04-14 08:00:00"
}
$trigger = New-ScheduledTaskTrigger @triggerParams
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable
$task = New-ScheduledTask -Action $action1,$action2 -Trigger $trigger -Settings $settings
Register-ScheduledTask "HustBooking" -InputObject $task
Write-Host "Task 'HustBooking' has been registered to run at $($triggerParams.At)"