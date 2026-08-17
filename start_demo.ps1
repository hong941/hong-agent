$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$root\backend\.venv\Scripts\python.exe" "$root\start_demo.py"
