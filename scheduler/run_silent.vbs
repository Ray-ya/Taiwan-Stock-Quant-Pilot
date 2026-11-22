Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """C:\Python314\pythonw.exe"" "".\scheduler\daily_runner.py"" ON_BOOT", 0, False
