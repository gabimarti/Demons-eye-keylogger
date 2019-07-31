#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#-----------------------------------------------------------------------------------------------------------
# Name:         demonseye-net-search.py
# Purpose:      Search for possible active keyloggers in a network range.
#
# Author:       Gabriel Marti Fuentes
# email:        gabimarti at gmail dot com
# GitHub:       https://github.com/gabimarti
# Created:      29/07/2019
# License:      GPLv3
#-----------------------------------------------------------------------------------------------------------
#

import ipaddress
import argparse
import socket
import threading
import time

########################################################
# CONSTANTS
########################################################
NET_ADDRESS="192.168.10.0/24"                                       # Network adress range to scan (CIDR)
KEYLOGGER_PORT = 6666                                               # Port of keylogger
PORT_LIST_SCAN = [ KEYLOGGER_PORT ]                                 # List of ports to Scan. For testing multiple ports
MAGIC_MESSAGE = '4ScauMiJcywpjAO/OfC2xLGsha45KoX5AhKR7O6T+Iw='      # Message to indentify to keylogger
BUFFER_SIZE = 4096                                                  # Buffer size
DEFAULT_TIMEOUT = 2                                                 # Default Timeout (seconds)

########################################################
# VARIABLES
########################################################
threadList = []                                                     # List of active threads
verbose = False                                                     # Verbosity disabled, enabled
net_range = NET_ADDRESS                                             # Network Range for command line test
port_list = []                                                      # Port list for command line test
timeout = DEFAULT_TIMEOUT                                           # Timeout on port connection

# Scan a host (ip), for open ports in port_list
# optionally, sends a message to host and wait response
# can activate more verbosity for errors and control messages
# can define a timeout for connection
class HostScan(threading.Thread):
    def __init__(self, ip, port_list, message = "", verbose=True, timeout = DEFAULT_TIMEOUT):
        threading.Thread.__init__(self)
        socket.setdefaulttimeout(timeout)
        self.open_ports = []
        # Ports from 1-65535
        # self.ports = range(1, 0xffff + 1)
        self.ports = port_list
        # self.host = socket.gethostname()
        # self.ip = socket.gethostbyname(self.host)
        self.ip = ip                                        # ip to scan
        self.message = message                              # message to send
        self.threads = []                                   # Thread list

    def scan(self, host, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)           # ipv4 (AF_INET) tcp (SOCK_STREAM)
            s.connect((host, port))
            if len(self.message)>0:
                s.send(self.message)
                response = s.recv(BUFFER_SIZE)
            else:
                response = ""
            self.open_ports.append("Host %s Port %s [Open] %s" % (host, port, response))
        except Exception as ex:
            print("host %s port %d exception %s " % (host, port, ex))
            pass
        finally:
            s.close()

    def write(self):
        for op in self.open_ports:
            print(op)

    def run(self):
        self.threads = []

        # Enumerate ports list and scan and add to thread
        for i, port in enumerate(self.ports):
            s = threading.Thread(target=self.scan, args=(self.ip, port))
            s.start()
            self.threads.append(s)

        # Finish threads before main thread starts again
        for thread in self.threads:
            thread.join()

        # Write out the ports that are open
        self.write()

# Scan a range of IPs for open ports
# Get CIDR net_gange, List of port_list, message to send, verbosity
class RangeScan(threading.Thread):
    def __init__(self, net_range, port_list, message, verbose=True, timeout = DEFAULT_TIMEOUT):
        threading.Thread.__init__(self)
        self.active_hosts = []                                      # IP Host list with at least one open port
        self.ip_net = ipaddress.ip_network(net_range)               # Create the network
        self.all_hosts = list(self.ip_net.hosts())                  # Generate all hosts in network
        self.port_list = port_list                                  # List of ports to scan
        self.message = message                                      # Message to send
        self.threads = []                                           # Thread list
        self.verbose = verbose                                      # Verbose

    def run(self):
        for ip in self.all_hosts:                                   # Scan the network range
            # Thread host port scan
            hs = HostScan(str(ip), self.port_list, self.message, self.verbose)
            hs.start()
            self.threads.append(hs)

        # Finish threads before main thread starts again
        for thread in self.threads:
            thread.join()


# Parse command line parameters
def parse_params():
    parser = argparse.ArgumentParser(description='Demon\'s Eye Keylogger Network Search',
                                     epilog='You can also use it to scan specific ports on a network.')
    parser.add_argument("-s", "--scan", action="store_true",
                        help="Run Net Scan (mandatory). If it is not set, the network scan does not run.",
                        required=True)
    parser.add_argument("-r", "--range", type=str, default=NET_ADDRESS,
                        help="Specify the network range in CIDR format (x.x.x.x/m)\nDefault value: "+NET_ADDRESS)
    parser.add_argument("-p", "--ports", type=int, nargs='*', default=list(PORT_LIST_SCAN),
                        help="Specify a list of ports to scan\nDefault value: " + str(PORT_LIST_SCAN))
    parser.add_argument("-m", "--message", type=str, default=MAGIC_MESSAGE,
                        help="Message to send to host\nDefault value: " + MAGIC_MESSAGE)
    parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Timeout on port connection\nDefault value: " + str(DEFAULT_TIMEOUT))
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    args = parser.parse_args()

    if not args.scan:
        parser.print_help()

    return args


def main():
    # Check and parse parameters
    args = parse_params()
    if args.scan==False:                    # If the parameter --scan is not passed, the scan is not executed.
        exit(1)
    verbose = args.verbose

    if verbose:
        print("Verbose Enabled")
        print("Network range "+args.range)
        print("Ports list "+str(args.ports))
        print("Message to send '"+args.message+"'")
        print("Timeout %d seconds" % (args.timeout))

    net_range = args.range
    port_list = args.ports
    message = args.message
    timeout = args.timeout

    exit(0)
    # Classic system, without threads
    '''
    print("Scaning with no-thread")
    start = time.perf_counter()
    network_scan(NET_ADDRESS,KEYLOGGER_PORT,MAGIC_MESSAGE)
    end = time.perf_counter()
    print("Time ",end-start)
    '''

    # Threaded metode scan
    print("Scaning with threads")
    start = time.perf_counter()
    scanner = RangeScan(net_range,port_list,message,verbose,timeout)
    scanner.run()
    end = time.perf_counter()
    print("Time ",end-start)

if __name__ == '__main__':
    main()

