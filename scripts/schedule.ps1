param(
    [Parameter(Mandatory=$true, HelpMessage="Schedule time, e.g. 2025-04-14 08:00:00")]
    [string]$ScheduleTime
)

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
    At = Get-Date $ScheduleTime -Format "yyyy-MM-dd HH:mm:ss"
}
$trigger = New-ScheduledTaskTrigger @triggerParams
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable
$task = New-ScheduledTask -Action $action1,$action2 -Trigger $trigger -Settings $settings
## or you can use the following code to run the task with highest privileges
## remember to run PowerShell as Administrator
#
# $principal = New-ScheduledTaskPrincipal -GroupId "Administrators" -RunLevel Highest
# $task = New-ScheduledTask -Action $action1,$action2 -Principal $principal -Trigger $trigger -Settings $settings

Register-ScheduledTask "HustBooking" -InputObject $task
Write-Host "Task 'HustBooking' has been registered to run at $($triggerParams.At)"
