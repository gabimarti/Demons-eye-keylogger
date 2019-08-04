#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------------------------------------
# Name:         tinyclient.py
# Purpose:      Small client program to use with tiny server.
#               Send a standard or predefined message and receive the respect from the server.
#
# Author:       Gabriel Marti Fuentes
# email:        gabimarti at gmail dot com
# GitHub:       https://github.com/gabimarti
# Created:      04/08/2019
# License:      GPLv3
# Notes:        Inspired by Daniel Hnyk's tutorial
#               http://danielhnyk.cz/simple-server-client-aplication-python-3/
# -----------------------------------------------------------------------------------------------------------
#


import argparse
import socket
import sys
import threading
import time
import traceback

########################################################
# CONSTANTS
########################################################
DESCRIPTION = 'Tiny Client'
EPILOG = 'Connect, send and receive. Simply.'
DEFAULT_VERBOSE_LEVEL = 1                                   # Default verbose level.
VERBOSE_LEVEL_DESCRIPTION = ['basic',                       # Arbitrary values to adjust
                             'a few',
                             'insane info']                 # Verbose levels description
DEFAULT_HOST_CONNECT = '127.0.0.1'                          # Host to connect
DEFAULT_PORT = 6666                                         # Default port
DEFAULT_KILL_MESSAGE = 'kill'                               # Message to kill server, if no message is indicate
DEFAULT_MESSAGE_IF_EMPTY = DESCRIPTION                      # If empty message is established, replace it with this one.
DEFAULT_MAX_BUFFER_SIZE = 4096                              # Default max buffer size
ENCODING = 'utf-8'                                          # Encoding for message communication
SOCKET_TIMEOUT = 3                                          # 3 seconds are more than enough


########################################################
# VARIABLES
########################################################
host_connect = DEFAULT_HOST_CONNECT
server_port = DEFAULT_PORT
buffer_size = DEFAULT_MAX_BUFFER_SIZE
message = DEFAULT_KILL_MESSAGE
verbose = DEFAULT_VERBOSE_LEVEL                             # Verbose level
time_start = 0                                              # Simply to measure times


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


# Parse command line parameters
def parse_params():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG)
    parser.add_argument('-s', '--hostserver', type=str, default=DEFAULT_HOST_CONNECT,
                        help='Host to connect. Default %s ' % DEFAULT_HOST_CONNECT)
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                        help='Port to connect. Default value: %s ' % str(DEFAULT_PORT))
    parser.add_argument('-b', '--buffersize', type=int, default=DEFAULT_MAX_BUFFER_SIZE,
                        help='Buffer size. Default value: %s ' % str(DEFAULT_MAX_BUFFER_SIZE))
    parser.add_argument('-m', '--message', type=str, default=DEFAULT_KILL_MESSAGE,
                        help='Message to send to the server. Default value: \'%s\'' % str(DEFAULT_KILL_MESSAGE))
    parser.add_argument('-v', '--verbose', type=int, choices=[0, 1, 2], default=DEFAULT_VERBOSE_LEVEL,
                        help='Increase output verbosity. Default value: %s' % DEFAULT_VERBOSE_LEVEL)
    args = parser.parse_args()
    return args


# Main - Start Client
def start_client():
    global host_connect, server_port, buffer_size, message, verbose, time_start

    # Check and parse parameters
    args = parse_params()
    host_connect = args.hostserver
    server_port = args.port
    buffer_size = args.buffersize
    message = args.message
    verbose = args.verbose

    if buffer_size < 64:                                    # avoid too small buffer size
        buffer_size = DEFAULT_MAX_BUFFER_SIZE
        print_verbose('Buffer size too small. Setting to {:d} bytes'.format(buffer_size) , 1, verbose)

    if message == '':                                       # avoid empty message
        message = DEFAULT_MESSAGE_IF_EMPTY
        print_verbose('Message is empty. Setting to \'{}\''.format(message), 1, verbose)

    print('Verbose level %s ' % str(VERBOSE_LEVEL_DESCRIPTION[verbose]))
    print('Connect to Host %s' % host_connect)
    print('Server Port %d' % server_port)
    print('Buffer size %d bytes' % buffer_size)
    print('Message to send \'%s\'' % message)
    print('Starting Client ...')

    time_start = time.perf_counter()

    try:
        print_verbose('Connecting ...', 1, verbose)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SOCKET_TIMEOUT)
        s.connect((host_connect, server_port))
        # Send message
        print_verbose('Sending \'{}\' ...'.format(message), 1, verbose)
        s.send(message.encode(ENCODING))                    # Encoding string to bytes
        # Wait for server response
        print_verbose('Waiting response ...', 2, verbose)
        response_bytes = s.recv(buffer_size)
        response_string = response_bytes.decode(ENCODING)   # Decode response in bytes
        print("Response from server is \'{}\'".format(response_string))
    except Exception as e:
        print('An error has occurred.')
        print('Exception : ' + str(e))
    finally:
        s.close()

    # Time measurement
    total_time = time.perf_counter() - time_start
    print('The process has happened in {:3.2f} seconds'.format(total_time))
    sys.exit()


if __name__ == '__main__':
    start_client()

