# Executable creation with PyInstaller

To create the executable in Windows, PyInstaller has been used.

Executable compression is disabled and the creation of a single file is forced.

### demonseyepy

This is the keylogger.

    pyinstaller -F --noupx --clean demonseye.py

### demonseye-net-search

This is the keylogger searcher in local network and monitor.

    pyinstaller -F --noupx --clean demonseye-net-search.py

