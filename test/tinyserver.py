#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------------------------------------
# Name:         tinyserver.py
# Purpose:      Small server using threads that listens on a default port and returns a response
#               with echo of the same message received and additional information.
#
# Author:       Gabriel Marti Fuentes
# email:        gabimarti at gmail dot com
# GitHub:       https://github.com/gabimarti
# Created:      03/08/2019
# License:      GPLv3
# Notes:        Inspired by Daniel Hnyk's tutorial
#               http://danielhnyk.cz/simple-server-client-aplication-python-3/
# -----------------------------------------------------------------------------------------------------------
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
DEFAULT_VERBOSE_LEVEL = 1                                   # Default verbose level
VERBOSE_LEVEL_DESCRIPTION = ['basic',
                             'a few',
                             'insane info']                 # Verbose levels description
DEFAULT_HOST_BIND = ''                                      # Bind to all ports
DEFAULT_PORT = 6666                                         # Default port
DEFAULT_KILL_MESSAGE = 'kill'                               # If this message is received, the server will end.
DEFAULT_MAX_BUFFER_SIZE = 4096                              # Default max buffer size
ENCODING = 'utf-8'                                          # EncodinG for message communication
SHUTDOWN_RESPONSE = 'Shutting down the server'              # Shutdown response to client


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
thread_client_list = []                                     # List of active threads
time_start = 0                                              # For Timer counter
shutdown = False                                            # It will be True when the server has to be closed.
server = None                                               # Global server socket


########################################################
# FUNCTIONS
########################################################

# Print the message if the verbose level allows
def print_verbose(msg, verbose_level, established_verbose):
    if verbose_level <= established_verbose:
        print(msg)


# Kill all client active sockets
def kill_client_sockets():
    global thread_client_list
    print_verbose('Killing clients ...', 1, verbose)
    for client in thread_client_list:
        try:
            client.shutdown(socket.SHUT_RDWR)
            client.close()
        except socket.error:
            pass                    # socket already closed. don't worry


# Client input string processing
def do_client_input_string_processing(input_string, verbose):
    print_verbose('Processing '+str(input_string), 1, verbose)
    # Reverse message
    input_processed = input_string[::-1]
    return input_processed


# Client thread for each new connection
def client_thread(conn, ip, port, buffer_size, verbose, kill_message):
    global shutdown, thread_active_counter, thread_client_list, server

    # Lock for shared counters operations
    lock = threading.Lock()
    lock.acquire()
    thread_active_counter += 1
    thread_client_list.append(conn)
    lock.release()

    print_verbose('Total clients {} | Current active clients {}'.format(thread_counter, thread_active_counter),
                  1, verbose)

    # the input is in bytes, so decode it
    input_from_client_bytes = conn.recv(max_buffer_size)
    if not input_from_client_bytes:
        print_verbose('No data. from {}:{}'.format(ip,port), 1, verbose)

    # max_buffer_size indicates how big the message can be
    # this is test if it's sufficiently big
    siz = sys.getsizeof(input_from_client_bytes)
    if siz >= buffer_size:
        print_verbose('The length of input is probably too long: {}'.format(siz), 1, verbose)

    # decode input and strip the end of line
    input_from_client = input_from_client_bytes.decode(ENCODING).rstrip()

    # check if message is received to kill server
    if input_from_client == kill_message:
        print_verbose('Killing message received \'{}\''.format(input_from_client), 1, verbose)
        # response shutdown to client
        res = SHUTDOWN_RESPONSE
        res_encoded = res.encode(ENCODING)
        conn.sendall(res_encoded)
        shutdown = True
        try:
            print_verbose('Shutdown server from Client thread', 1, verbose)
            server.close()
        except Exception as e:
            print_verbose('Can\'t close Server from client thread', 1, verbose)
            print_verbose('Exception {}'.format(e), 1, verbose)

        kill_client_sockets()
    else:
        res = do_client_input_string_processing(input_from_client, verbose)
        print_verbose('Result of processing {} is: {}'.format(input_from_client, res), 1, verbose)

        res_encoded = res.encode(ENCODING)              # encode the result string
        try:
            conn.sendall(res_encoded)                   # send it to client
            conn.close()                                # close connection
        except Exception as e:
            print_verbose('Socket Error: {:s} '.format(e), 1, verbose)

    # Lock for shared counters operations
    lock.acquire()
    thread_active_counter -= 1
    thread_client_list.remove(conn)
    lock.release()

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
                        help='Port to listen. Default value: %s ' % str(DEFAULT_PORT))
    parser.add_argument('-b', '--buffersize', type=int, default=DEFAULT_MAX_BUFFER_SIZE,
                        help='Buffer size. Default value: %s ' % str(DEFAULT_MAX_BUFFER_SIZE))
    parser.add_argument('-k', '--killmessage', type=str, default=DEFAULT_KILL_MESSAGE,
                        help='Message to kill server. Default value: \'%s\'' % str(DEFAULT_KILL_MESSAGE))
    parser.add_argument('-v', '--verbose', type=int, choices=[0, 1, 2], default=DEFAULT_VERBOSE_LEVEL,
                        help='Increase output verbosity. Default value: %s' % DEFAULT_VERBOSE_LEVEL)
    args = parser.parse_args()
    return args


# Executes on program close
def on_close_program():
    global time_start

    totaltime = time.perf_counter() - time_start
    print('The server has been running for {} seconds.'.format(totaltime))


# Main - Start Server
def start_server():
    global host_bind, max_clients, server_port, max_buffer_size, kill_message, verbose, time_start
    global shutdown, thread_counter, server

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

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print_verbose('Socket created', 1, verbose)

    # Bind socket to local host and port
    try:
        server.bind((host_bind, server_port))
        print_verbose('Socket bind completed', 2, verbose)
    except socket.error as msg:
        print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        print('Sys Error Info : ' + str(sys.exc_info()))
        sys.exit()

    # Start listening on socket
    server.listen(max_clients)
    print_verbose('Socket now listening', 2, verbose)

    # Now keep talking with the client while no shutdown message is received
    while not shutdown:
        # Wait to accept a connection - blocking call
        try:
            conn, addr = server.accept()
        except:
            break                                   # Possibly closed server

        ip, port = str(addr[0]), str(addr[1])
        print('Accepting connection from ' + ip + ':' + port)
        thread_counter += 1
        try:
            client = threading.Thread(target=client_thread,
                                      args=(conn, ip, port, max_buffer_size, verbose, kill_message))
            client.start()
        except Exception as e:
            print('WTF Error! '+str(e))
            traceback.print_exc()

    # Shutting down server
    try:
        print("Shutdown server")
        server.shutdown(socket.SHUT_RDWR)
        server.close()
    except Exception as e:
        print_verbose("Server already closed from client thread", 1, verbose)
        print_verbose("Exception {}".format(e), 2, verbose)

    print_verbose('At shutdown, total clients {} | Current active {}'.format(thread_counter,
                                                                             thread_active_counter),
                  1, verbose)
    sys.exit(1)


if __name__ == '__main__':
    start_server()

