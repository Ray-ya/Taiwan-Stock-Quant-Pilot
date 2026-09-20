Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python .\scheduler\daily_runner.py ON_BOOT", 0, False
