$projRoot = (Get-Item -Path $PSScriptRoot).Parent.FullName
$pythonPath = Join-Path -Path $projRoot -ChildPath 'python310'
$pythonExe = Join-Path -Path $pythonPath -ChildPath 'python.exe'
$scriptPath = Join-Path -Path $projRoot -ChildPath 'main.py'

# replace it to your Tesseract path
$tesseractPath = "C:\Program Files\Tesseract-OCR"

Set-Location -Path "$projRoot"
$env:Path += ";$tesseractPath"
& $pythonExe $scriptPath
