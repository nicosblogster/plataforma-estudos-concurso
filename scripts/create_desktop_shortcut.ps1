$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runBat = Join-Path $projectRoot "scripts\run.bat"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Plataforma Estudos Concurso.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $runBat
$shortcut.WorkingDirectory = $projectRoot
$shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,21"
$shortcut.Description = "Abrir plataforma local de estudos para concurso"
$shortcut.Save()

Write-Host "Atalho criado em: $shortcutPath"
