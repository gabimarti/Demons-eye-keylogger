#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#-----------------------------------------------------------------------------------------------------------
# Name:         tinyserver.py
# Purpose:      Small Server using threads that listen to port
#               Small server using threads that listens on a default port and returns a response
#               with echo of the same message received and additional information.
#
# Author:       Gabriel Marti Fuentes
# email:        gabimarti at gmail dot com
# GitHub:       https://github.com/gabimarti
# Created:      03/08/2019
# License:      GPLv3
#-----------------------------------------------------------------------------------------------------------
#


import argparse
import atexit
import socket
import sys
import threading
import time
import traceback

########################################################
# CONSTANTS
########################################################
DESCRIPTION = 'Tiny Server'
EPILOG = 'Listen and respond. Simply.'
DEFAULT_MAXCLIENTS = 10                                     # Aka MAXTHREADS, every Client is a thread
DEFAULT_VERBOSE_LEVEL = 2                                   # Default verbose level
VERBOSE_LEVEL_DESCRIPTION = ['basic',
                             'a few',
                             'insane info']                 # Verbose levels description
DEFAULT_HOST_BIND = ''                                      # Bind to all ports
DEFAULT_PORT = 6666                                         # Default port
DEFAULT_KILL_MESSAGE = 'kill'                               # If this message is received, the server will end.
DEFAULT_MAX_BUFFER_SIZE = 4096                              # Default max buffer size
ENCODING = 'utf-8'                                          # EncodinG for message communication


########################################################
# VARIABLES
########################################################
host_bind = DEFAULT_HOST_BIND
max_clients = DEFAULT_MAXCLIENTS
server_port = DEFAULT_PORT
max_buffer_size = DEFAULT_MAX_BUFFER_SIZE
kill_message = DEFAULT_KILL_MESSAGE
verbose = DEFAULT_VERBOSE_LEVEL                             # Verbose level
thread_counter = 0                                          # Total executed threads / clients
thread_active_counter = 0                                   # active threads / clients
thread_list = []                                            # List of active threads
time_start = 0                                              # For Timer counter


########################################################
# FUNCTIONS
########################################################

# Print the message if the verbose level allows
def print_verbose(msg, verbose_level, established_verbose):
    if verbose_level <= established_verbose:
        print(msg)


# Wait for the indicated time in milliseconds
def delay_milliseconds(millisec):
    if millisec == 0:
        return None                                         # Avoid making unnecessary call
    time.sleep(millisec / 1000)


# Client input string processing
def do_client_input_string_processing(input_string, verbose):
    """
    This is where all the processing happens.
    Let's just read the string backwards
    """
    print_verbose('Processing '+str(input_string), 1, verbose)
    # Reverse message
    input_processed = input_string[::-1]
    return input_processed


# Client thread for each new connection
def client_thread(conn, ip, port, buffer_size, verbose, kill_message):
    # the input is in bytes, so decode it
    input_from_client_bytes = conn.recv(max_buffer_size)

    # max_buffer_size indicates how big the message can be
    # this is test if it's sufficiently big
    siz = sys.getsizeof(input_from_client_bytes)
    if siz >= buffer_size:
        print_verbose('The length of input is probably too long: {}'.format(siz), 0, verbose)

    # decode input and strip the end of line
    input_from_client = input_from_client_bytes.decode('utf8').rstrip()

    # check if message is received to kill server
    if input_from_client == kill_message:
        print("Kill message received. Shutdown server")
        sys.exit(1)

    res = do_client_input_string_processing(input_from_client, verbose)
    print_verbose('Result of processing {} is: {}'.format(input_from_client, res), 1, verbose)

    res_encoded = res.encode('utf8')            # encode the result string
    conn.sendall(res_encoded)                   # send it to client
    conn.close()                                # close connection
    print_verbose('Connection ' + ip + ':' + port + " ended", 1, verbose)


# Parse command line parameters
def parse_params():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG)
    parser.add_argument('-i', '--interfacebind', type=str, default=DEFAULT_HOST_BIND,
                        help='What interface is it linked to? Default (empty) to any of this host.')
    parser.add_argument('-c', '--maxclients', type=int, default=DEFAULT_MAXCLIENTS,
                        help='Indicates the maximum number of clients/threads. Default value: %s '
                             % str(DEFAULT_MAXCLIENTS))
    parser.add_argument('-p', '--serverport', type=int, default=DEFAULT_PORT,
                        help='Port to listen. Default value: %s '
                             % str(DEFAULT_PORT))
    parser.add_argument('-b', '--buffersize', type=int, default=DEFAULT_MAX_BUFFER_SIZE,
                        help='Buffer size. Default value: %s '
                             % str(DEFAULT_MAX_BUFFER_SIZE))
    parser.add_argument('-k', '--killmessage', type=str, default=DEFAULT_KILL_MESSAGE,
                        help='Message to kill server. Default value: \'%s\''
                             % str(DEFAULT_KILL_MESSAGE))
    parser.add_argument('-v', '--verbose', type=int, choices=[0, 1, 2], default=DEFAULT_VERBOSE_LEVEL,
                        help='Increase output verbosity. Default value: %s'
                            % DEFAULT_VERBOSE_LEVEL)
    args = parser.parse_args()
    return args


# Executes on program close
def on_close_program():
    global time_start

    pass
    '''
    totaltime = time.perf_counter() - time_start
    average_sleep = total_sleep_seconds / thread_counter
    print('Performed %d threads in %6.2f seconds ' % (thread_counter, totaltime))
    print('Current active threads %d' % (thread_active_counter))
    print('Total sleep %d (shared) seconds for all process' % (total_sleep_seconds))
    print('Average sleep %6.2f seconds' % (average_sleep))
    '''


# Main - Start Server
def start_server():
    global host_bind, max_clients, server_port, max_buffer_size, kill_message, verbose, time_start

    # Handler to do actions when application is closed
    atexit.register(on_close_program)

    # Check and parse parameters
    args = parse_params()
    host_bind = args.interfacebind
    max_clients = args.maxclients
    server_port = args.serverport
    max_buffer_size = args.buffersize
    kill_message = args.killmessage
    verbose = args.verbose

    if max_clients < 1:                     # avoid zero division
        max_clients = DEFAULT_MAXCLIENTS

    print('Verbose level %s ' % str(VERBOSE_LEVEL_DESCRIPTION[verbose]))
    print('Host bind %s' % host_bind)
    print('Max %d Clients / Threads ' % max_clients)
    print('Server Port %d' % server_port)
    print('Buffer size %d bytes' % max_buffer_size)
    print('Kill message \'%s\'' % kill_message)
    print('Starting Server ...')
    time_start = time.perf_counter()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print_verbose('Socket created', 1, verbose)

    # Bind socket to local host and port
    try:
        s.bind((host_bind, server_port))
        print_verbose('Socket bind completed', 2, verbose)
    except socket.error as msg:
        print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        print('Sys Error Info : ' + str(sys.exc_info()))
        sys.exit()

    # Start listening on socket
    s.listen(max_clients)
    print_verbose('Socket now listening', 2, verbose)

    # now keep talking with the client
    while True:
        # wait to accept a connection - blocking call
        conn, addr = s.accept()
        ip, port = str(addr[0]), str(addr[1])
        print('Accepting connection from ' + ip + ':' + port)
        try:
            client = threading.Thread(target=client_thread,
                                      args=(conn, ip, port, max_buffer_size, verbose, kill_message))
            client.start()
        except Exception as e:
            print('Terible error! '+str(e))
            traceback.print_exc()

    s.close()

if __name__ == '__main__':
    start_server()

