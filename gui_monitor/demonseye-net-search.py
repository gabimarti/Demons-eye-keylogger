#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#-----------------------------------------------------------------------------------------------------------
# Name:         demonseye-net-search.py
# Purpose:      Search for possible active keyloggers in a network range.
#               Alternatively, it can be used as a normal network scanner, since it allows you to specify
#               which ports you want to check. It uses multithreading techniques so you can check
#               65535 computers in approximately 95 seconds.
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
import urllib.request

########################################################
# CONSTANTS
########################################################
APPNAME = "Demon's Eye Keylogger Network Search"                    # Just a name
VERSION = "1.0"                                                     # Version
NET_ADDRESS = "192.168.10.0/24"                                     # Network adress range to scan (CIDR)
KEYLOGGER_PORT = 6666                                               # Port of keylogger
SERVER_PORT = 7777                                                  # Port to receive response connection when search DemonsEye
PORT_LIST_SCAN = [ KEYLOGGER_PORT ]                                 # List of ports to Scan. For testing multiple ports
MAGIC_MESSAGE = '4ScauMiJcywpjAO/OfC2xLGsha45KoX5AhKR7O6T+Iw='      # Message to indentify to keylogger
BUFFER_SIZE = 4096                                                  # Buffer size
DEFAULT_TIMEOUT = 2                                                 # Default Timeout (seconds)
ENCODING = 'utf-8'                                                  # Encodinf for message sended
VERBOSE_LEVELS = [ "none", "error", "insane debug" ]                # Verbose levels


########################################################
# VARIABLES
########################################################
threadList = []                                                     # List of active threads
verbose = 0                                                         # Verbosity disabled, enabled
net_range = NET_ADDRESS                                             # Network Range for command line test
port_list = []                                                      # Port list for command line test
timeout = DEFAULT_TIMEOUT                                           # Timeout on port connection


########################################################
# CLASSES
########################################################

# Scan a host (ip), for open ports in port_list
# optionally, sends a message to host and wait response
# can activate more verbosity for errors and control messages
# can define a timeout for connection
class HostScan(threading.Thread):
    def __init__(self, ip, port_list, message = "", verbose = True, timeout = DEFAULT_TIMEOUT):
        threading.Thread.__init__(self)
        self.open_ports = []
        self.ports = port_list                              # All ports can be self.ports = range(1, 0xffff + 1)
        self.ip = ip                                        # ip to scan
        self.message = message                              # message to send
        self.threads = []                                   # Thread list
        self.timeout = timeout                              # Timeout - alternative: socket.setdefaulttimeout(timeout)
        self.verbose = verbose                              # Verbose

    def scan(self, host, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # ipv4 (AF_INET) tcp (SOCK_STREAM)
            s.settimeout(self.timeout)                                  # Sets timeout
            s.connect((host, port))
            if len(self.message)>0:
                if self.verbose >= 1:
                    print("Send message %s " % (self.message))
                s.send(self.message)
                response = s.recv(BUFFER_SIZE)
            else:
                response = ""
            self.open_ports.append("Host %s Port %s [Open] %s" % (host, port, response))
        except Exception as ex:
            if self.verbose >= 1:
                print("Host %s Port %d Exception %s " % (host, port, ex))
            pass
        finally:
            s.close()

    def write(self):
        for op in self.open_ports:
            print(op)

    def run(self):
        self.threads = []
        if self.verbose >= 2:
            print("Start scan " + str(self.ip))
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
    def __init__(self, net_range, port_list, message, verbose = True, timeout = DEFAULT_TIMEOUT):
        threading.Thread.__init__(self)
        self.active_hosts = []                                      # IP Host list with at least one open port
        self.ip_net = ipaddress.ip_network(net_range)               # Create the network
        self.all_hosts = list(self.ip_net.hosts())                  # Generate all hosts in network
        self.port_list = port_list                                  # List of ports to scan
        self.message = message                                      # Message to send
        self.threads = []                                           # Thread list
        self.verbose = verbose                                      # Verbose
        self.own_host = socket.gethostname()                        # Client Host name
        self.own_ip = socket.gethostbyname(self.own_host)           # Client Host ip
        self.timeout = timeout                                      # Timeout

    def scan(self):
        if self.verbose >= 2:
            print ("This host is %s %s " % (self.own_host, self.own_ip))

        hosts_scanned = 0
        for ip in self.all_hosts:                                   # Scan the network range
            # Thread host port scan
            hs = HostScan(str(ip), self.port_list, self.message, self.verbose, self.timeout)
            hs.start()
            self.threads.append(hs)
            hosts_scanned += 1

        # Wait to finish threads before main thread starts again
        for thread in self.threads:
            thread.join()

        return hosts_scanned


########################################################
# FUNCTIONS
########################################################

# Obtiene la ip externa - Get the external ip
def get_external_ip():
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    return external_ip


# Parse command line parameters
def parse_params():
    parser = argparse.ArgumentParser(description='Demon\'s Eye Keylogger Network Search',
                                     epilog='You can also use it to scan specific ports on a network.')
    parser.add_argument("-r", "--range", type=str, default=NET_ADDRESS, required=True,
                        help="Specify the network range in CIDR format. Example: 192.168.1.0/24")
    parser.add_argument("-p", "--ports", type=int, nargs='+', default=list(PORT_LIST_SCAN),
                        help="Specify a list of ports to scan. Default value: " + str(PORT_LIST_SCAN))
    parser.add_argument("-m", "--message", type=str, default=MAGIC_MESSAGE,
                        help="Message to send to host. If empty, -m '', then not message is sent. Default value: " + MAGIC_MESSAGE)
    parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Timeout in seconds on port connection. Default value: " + str(DEFAULT_TIMEOUT))
    parser.add_argument("-v", "--verbose", type=int, choices=[0,1,2], default=0,
                        help="Increase output verbosity. Default value: 0")
    args = parser.parse_args()
    return args


def main():
    # Check and parse parameters
    args = parse_params()
    verbose = args.verbose
    net_range = args.range
    port_list = args.ports
    message = args.message
    timeout = args.timeout

    # Host info
    hostname = socket.gethostname()
    localip = socket.gethostbyname(hostname)
    externalip = get_external_ip()

    print("Verbose level "+str(VERBOSE_LEVELS[verbose]))
    print("Network range "+args.range)
    print("Ports list "+str(args.ports))
    print("Message to send '"+args.message+"'")
    print("Timeout %d seconds" % (args.timeout))
    print("---")
    print("This Host %s : IP local %s : IP wan %s" % (hostname, localip, externalip))
    print("Scanning ...")
    start = time.perf_counter()
    scanner = RangeScan(net_range, port_list, message, verbose, timeout)
    total_hosts = scanner.scan()
    totaltime = time.perf_counter() - start
    print("Scanned %d hosts at %s in %6.2f seconds " % (total_hosts, args.range, totaltime))


if __name__ == '__main__':
    main()

