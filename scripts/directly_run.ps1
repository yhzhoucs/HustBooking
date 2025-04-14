$pythonPath = (Get-Item -Path 'python310').FullName
$pythonExe = Join-Path -Path $pythonPath -ChildPath 'python.exe'
$scriptPath = Join-Path -Path $pwd.Path -ChildPath 'main.py'

# replace it to your Tesseract path
$tesseractPath = "C:\Program Files\Tesseract-OCR"

Set-Location -Path "$($pwd.Path)"
$env:Path += ";$tesseractPath"
& $pythonExe $scriptPath
