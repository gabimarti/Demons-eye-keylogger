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
threadList = []

class HostScan(threading.Thread):
    def __init__(self, ip, port_list, message = "", timeout = DEFAULT_TIMEOUT):
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


class RangeScan(threading.Thread):
    def __init__(self,net_range,port_list,message):
        threading.Thread.__init__(self)
        self.active_hosts = []                                      # IP Host list with at least one open port
        self.ip_net = ipaddress.ip_network(net_range)               # Create the network
        self.all_hosts = list(self.ip_net.hosts())                  # Generate all hosts in network
        self.port_list = port_list                                  # List of ports to scan
        self.message = message                                      # Message to send
        self.threads = []                                           # Thread list

    def scanhost(self,ip,port_list,message):
        hs = HostScan(ip,port_list,message)
        pass

    def run(self):
        for ip in self.all_hosts:                                   # Scan the network range
            # Thread host port scan
            # sh = threading.Thread(target=self.scanhost, args=(ip,self.port_list,self.message))
            hs = HostScan(str(ip), self.port_list, self.message)
            hs.start()
            self.threads.append(hs)

        # Finish threads before main thread starts again
        for thread in self.threads:
            thread.join()



# Connects to IP, port, send message and returns response
def client_connect(ip, port, message):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)      # ipv4 (AF_INET) tcp (SOCK_STREAM)
    client.settimeout(DEFAULT_TIMEOUT)

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
        print("Scan IP %s at port %d with message %s = %s" % (ip, port, message, client_connect(str(ip),port,message)))


def main():
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
    scanner = RangeScan(NET_ADDRESS,PORT_LIST_SCAN,MAGIC_MESSAGE)
    scanner.run()
    end = time.perf_counter()
    print("Time ",end-start)

if __name__ == '__main__':
    main()

