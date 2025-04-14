param(
    [Parameter(Mandatory=$true, HelpMessage="Schedule time, e.g. 2025-04-14 08:00:00")]
    [string]$ScheduleTime,
    [Parameter(Mandatory=$false, HelpMessage="Use highest privileges")]
    [switch]$Sudo=$false
)

############### Customize here ###################

$pwsh = "pwsh.exe"

$tesseractPath = "C:\Program Files\Tesseract-OCR"

############### Customize here ###################

function Test-Administrator {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

# Check if the script is running with administrator privileges
# If not, re-run the script with elevated privileges
if ($Sudo -and (-not (Test-Administrator))) {
    $scriptPath = $PSCommandPath
    if (-not $scriptPath) {
        $scriptPath = $MyInvocation.MyCommand.Path
    }
    
    $workingDirectory = Get-Location
    
    $arguments = "-NoProfile -ExecutionPolicy Bypass -NoExit -Command `"$scriptPath -ScheduleTime '$ScheduleTime' -Sudo`""
    Start-Process -FilePath $pwsh -Verb RunAs -ArgumentList $arguments -WorkingDirectory $workingDirectory
    
    exit
}

$projRoot = (Get-Item -Path $PSScriptRoot).Parent.FullName
$pythonPath = Join-Path -Path $projRoot -ChildPath 'python310'
$pythonExe = Join-Path -Path $pythonPath -ChildPath 'python.exe'
$scriptPath = Join-Path -Path $projRoot -ChildPath 'main.py'

$command = @"
Set-Location -Path '$projRoot'
`$env:Path += ';$tesseractPath'
& $pythonExe $scriptPath
"@

$action1 = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoExit -Command `"$command`""
$action2 = New-ScheduledTaskAction -Execute $pwsh -Argument @"
-Command `"Unregister-ScheduledTask -TaskName HustBooking -Confirm:`$false`"; 
Write-Host '定时器已删除';
Read-Host '按回车退出';
exit
"@
$triggerParams = @{
    Once = $true
    At = Get-Date $ScheduleTime -Format "yyyy-MM-dd HH:mm:ss"
}
$trigger = New-ScheduledTaskTrigger @triggerParams
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable

$task = $null
if ($Sudo) {
    $principal = New-ScheduledTaskPrincipal -GroupId "Administrators" -RunLevel Highest
    $task = New-ScheduledTask -Action $action1,$action2 -Principal $principal -Trigger $trigger -Settings $settings
} else {
    $task = New-ScheduledTask -Action $action1,$action2 -Trigger $trigger -Settings $settings
}

Register-ScheduledTask "HustBooking" -InputObject $task
if ($Sudo) {
    Write-Host "高优先级定时器已设定，触发时间为 $($triggerParams.At)"
    Write-Host "若定时器非正常关闭，您可在管理员权限下运行以下命令删除定时器："
} else {
    Write-Host "定时器已设定，触发时间为 $($triggerParams.At)"
    Write-Host "若定时器非正常关闭，您可在普通权限下运行以下命令删除定时器："
}

Write-Host "Unregister-ScheduledTask -TaskName HustBooking -Confirm:`$false"