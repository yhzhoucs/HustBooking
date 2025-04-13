param(
    [Parameter(Mandatory=$false, HelpMessage='Just use this script to clean cache')]
    [switch]$Clean=$false,
    [Parameter(Mandatory=$false, HelpMessage='Prepare environment')]
    [switch]$Prepare=$false,
    [Parameter(Mandatory=$false, HelpMessage='Run python script')]
    [switch]$StartBooking=$false
)

function Print-Msg {
    param ( [Parameter(Mandatory=$true, HelpMessage='String to output')][string]$msg, [string]$color = "Green" )
    Write-Host ('{0}' -f $msg) -ForegroundColor $color
}

function Install-PythonEnv {
    param(
        [Parameter(Mandatory=$true,HelpMessage='Python embeddable package url')]
        [string]$PythonUrl,
        [Parameter(Mandatory=$true,HelpMessage='get-pip.py url')]
        [string]$PipUrl,
        [Parameter(Mandatory=$false,HelpMessage='Path to extract python')]
        [string]$PythonPath='python'
    )
    
    # download embeddable python
    Invoke-WebRequest -Uri $PythonUrl -OutFile './embeddable-python.zip'
    Expand-Archive -Path './embeddable-python.zip' -DestinationPath $PythonPath

    # patch python
    $pthPath = Get-ChildItem -Path $PythonPath -Filter *._pth
    $newContent = (Get-Content -Path $pthPath | Out-String) -replace '#import site','import site'
    $newContent | Set-Content -Path $pthPath

    # download get-pip script
    Invoke-WebRequest -Uri $PipUrl -OutFile "$PythonPath/get-pip.py"
    
    # install pip
    & "$PythonPath/python.exe" "$PythonPath/get-pip.py" --no-warn-script-location

    # install requirements
    & "$PythonPath/Scripts/pip.exe" install -r requirements-win.txt --no-warn-script-location

    Remove-Item -Path './embeddable-python.zip'
}

function Fetch-Dependency {
    param(
        [Parameter(Mandatory=$true, HelpMessage='Dependency url')]
        [string]$Url,
        [Parameter(Mandatory=$true, HelpMessage='Path to extract')]
        [string]$Path,
        [Parameter(Mandatory=$false, HelpMessage='Patch file path')][AllowEmptyString()]
        [string]$PatchPath
    )

    Invoke-WebRequest -Uri $Url -OutFile './dep.zip'
    Expand-Archive -Path './dep.zip' -Destination $Path
    $inner = Get-ChildItem -Path $Path
    Move-Item -Path "$inner/*" -Destination $Path
    Remove-Item $inner

    if ((Test-Path -Path $PatchPath)) {
        # fix from https://stackoverflow.com/questions/4770177/git-apply-fails-with-patch-does-not-apply-error
        git apply --ignore-space-change --ignore-whitespace --directory=$Path $PatchPath
    }

    Remove-Item -Path './dep.zip'
}

function Add-PythonSysPath {
    param(
        [Parameter(Mandatory=$true,HelpMessage='Path to embeddable python')]
        [string]$PythonPath,
        [Parameter(Mandatory=$true,HelpMessage='Path to add to python system path')]
        [string]$PathToAdd
    )

    $pthPath = Get-ChildItem -Path $PythonPath -Filter *._pth
    $fullPath = (Get-Item $PathToAdd).FullName
    Add-Content -Path $pthPath -Value $fullPath
}

function Run-PythonScript {
    [CmdletBinding()]
    param(
        [Parameter(Position = 0, Mandatory = 1)][string]$PythonExe,
        [Parameter()][string]$errorMessage,
        [parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Passthrough
    )
    & $PythonExe @Passthrough
    if ($lastexitcode -ne 0) {
        if (!($errorMessage)) {
          throw ('Exec: Error executing command {0} with arguments ''{1}''' -f $cmd, "$Passthrough")
        } else {
          throw ('Exec: ' + $errorMessage)
        }
    }
}

$pythonUrl = 'https://www.python.org/ftp/python/3.10.9/python-3.10.9-embed-amd64.zip'
$pipUrl = 'https://bootstrap.pypa.io/get-pip.py'
$pythonPath = 'python310'

$captchaIdentifierUrl = 'https://github.com/scwang98/Captcha_Identifier/archive/main.zip'
$captchaIdentifierPatchPath = './patches/Captcha_Identifier-001-fix-integration.patch'
$captchaIdentifierPath = 'Captcha_Identifier'

if ($Clean) {
    Print-Msg "Cleaning up..."
    Remove-Item -Path $pythonPath,$captchaIdentifierPath -Force -Recurse -ErrorAction SilentlyContinue
    Remove-Item -Path '__pycache__' -Force -Recurse -ErrorAction SilentlyContinue
    exit 0
}

if ($StartBooking) {
    $pythonExe = Join-Path -Path $pythonPath -ChildPath 'python.exe'
    Run-PythonScript $pythonExe (Join-Path $pwd.Path 'main.py')
    exit 0
}

if (-not $Prepare) {
    Print-Msg "Nothing to do, Use `Get-Help ./auto.ps1` to see help"
    Print-Msg "Exiting..."
    exit 0
}

$pythonAlreadyExists = (Test-Path -Path $pythonPath) `
    -and ((Get-ChildItem -Path $pythonPath -Filter '*.exe') | Measure-Object).Count -gt 0
if (-not $pythonAlreadyExists) {
    Remove-Item $pythonPath -Force -Recurse -ErrorAction SilentlyContinue
    Print-Msg "Preparing python environment..."
    Install-PythonEnv -pythonUrl $pythonUrl -pipUrl $pipUrl -pythonPath $pythonPath
    Add-PythonSysPath -PythonPath $pythonPath -PathToAdd $pwd.Path
}

$captchaIdentifierAlreadyExists = (Test-Path -Path $captchaIdentifierPath) `
    -and ((Get-ChildItem -Path $captchaIdentifierPath -Filter '*.py') | Measure-Object).Count -gt 0
if (-not $captchaIdentifierAlreadyExists) {
    Remove-Item $captchaIdentifierPath -Force -Recurse -ErrorAction SilentlyContinue
    Print-Msg "Fetching Captcha_Identifier from $captchaIdentifierUrl"
    Fetch-Dependency -Url $captchaIdentifierUrl -Path $captchaIdentifierPath -PatchPath $captchaIdentifierPatchPath
}