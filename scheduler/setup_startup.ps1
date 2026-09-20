$wsh = New-Object -ComObject WScript.Shell
$startup = [System.Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'TaiwanStockQuantPilot.lnk'
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = 'wscript.exe'
$shortcut.Arguments = '.\scheduler\run_silent.vbs'
$shortcut.WorkingDirectory = '.'
$shortcut.WindowStyle = 7
$shortcut.Description = 'Taiwan Stock Quant Pilot On-Boot Checker'
$shortcut.Save()
Write-Output "ShortcutCreated: $(Test-Path $shortcutPath)"
