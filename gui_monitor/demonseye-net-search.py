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
import threading
import socket

########################################################
# CONSTANTS
########################################################
NET_ADDRESS="192.168.10.0/24"                                               # Network adress range to scan (CIDR)
KEYLOGGER_PORT = 6666                                                       # Port of keylogger
MAGIC_MESSAGE = '4ScauMiJcywpjAO/OfC2xLGsha45KoX5AhKR7O6T+Iw='              # Message to indentify to keylogger
BUFFER_SIZE = 4096                                                          # Buffer size
DEFAULT_TIMEOUT = 1                                                         # Default Timeout

########################################################
# VARIABLES
########################################################

class HostScan(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        socket.setdefaulttimeout(DEFAULT_TIMEOUT)
        self.open_ports = []
        # Ports from 1-65535
        self.ports = range(1, 0xffff + 1)
        self.host = socket.gethostname()
        self.ip = socket.gethostbyname(self.host)
        self.message = ""

    def scan(self,host,port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)           # ipv4 (AF_INET) tcp (SOCK_STREAM)
            s.connect((host, port))
            self.open_ports.append("Port %s is [Open] on host %s" % (port, host))
            if len(self.message)>0:
                s.send(message)
                response = s.recv(BUFFER_SIZE)
        except:
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


class RangeScan(threading.Thread):
    def __init__(self, net_range, port_list, message):
        threading.Thread.__init__(self)
        self.active_hosts = []                                      # IP Host list with at least one open port
        self.ip_net = ipaddress.ip_network(net_range)               # Create the network
        self.all_hosts = list(self.ip_net.hosts())                  # Generate all hosts in network
        self.port_list = port_list                                  # List of ports to scan
        self.message = message                                      # Message to send

    def scanhost(self,ip,port_list,message):
        pass

    def run(self):
        self.threads = []

        for ip in self.all_hosts:                                   # Scan the network range
            # Thread host port scan
            sh = threading.Thread(target=self.scanhost, args=(ip,self.port_list,self.message))

        # Finish threads before main thread starts again
        for thread in self.threads:
            thread.join()


# Scanner object which initializes our vars and then we run our scanner
scanner = Scanner()
scanner.run()

# Connects to IP, port, send message and returns response
def client_connect(ip, port, message):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)      # ipv4 (AF_INET) tcp (SOCK_STREAM)
    client.settimeout(1)

    try:
        client.connect((ip, port))
        client.send(message)
        response = client.recv(BUFFER_SIZE)
    except socket.error:
        response = "CLOSED PORT"
    finally:
        client.close()

    return response

# Scan a network range and returns the first IP that has this port open
def network_scan(net_range, port, message):
    ip_net = ipaddress.ip_network(net_range)        # Create the network
    all_hosts = list(ip_net.hosts())                # Generate all hosts in network

    for ip in all_hosts:                            # Scan the network range
        print("Scan IP %s at port %d with message %s" % (ip, port, message))
        print(client_connect(str(ip),port,message))


def main():
    network_scan(NET_ADDRESS,KEYLOGGER_PORT,MAGIC_MESSAGE)

if __name__ == '__main__':
    main()

