param(
    [Parameter(Mandatory=$false, HelpMessage='Just use this script to clean cache')]
    [switch]$Clean=$false
)

function Write-Msg {
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

function Install-Dependency {
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

$pythonUrl = 'https://www.python.org/ftp/python/3.10.9/python-3.10.9-embed-amd64.zip'
$pipUrl = 'https://bootstrap.pypa.io/get-pip.py'
$pythonPath = 'python310'

$captchaIdentifierUrl = 'https://github.com/scwang98/Captcha_Identifier/archive/main.zip'
$captchaIdentifierPatchPath = './patches/Captcha_Identifier-001-fix-integration.patch'
$captchaIdentifierPath = 'Captcha_Identifier'

if ($Clean) {
    Write-Msg "Cleaning up..."
    Remove-Item -Path $pythonPath,$captchaIdentifierPath -Force -Recurse -ErrorAction SilentlyContinue
    Remove-Item -Path '__pycache__' -Force -Recurse -ErrorAction SilentlyContinue
    exit 0
}

Remove-Item $pythonPath -Force -Recurse -ErrorAction SilentlyContinue
Write-Msg "Preparing python environment..."
Install-PythonEnv -pythonUrl $pythonUrl -pipUrl $pipUrl -pythonPath $pythonPath
Add-PythonSysPath -PythonPath $pythonPath -PathToAdd $pwd.Path

Remove-Item $captchaIdentifierPath -Force -Recurse -ErrorAction SilentlyContinue
Write-Msg "Fetching Captcha_Identifier from $captchaIdentifierUrl"
Install-Dependency -Url $captchaIdentifierUrl -Path $captchaIdentifierPath -PatchPath $captchaIdentifierPatchPath