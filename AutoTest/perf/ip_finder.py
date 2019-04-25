import os
import fcntl
import struct
import socket
import re

SIOCGIFADDR = 0x8915

class IPFinder():
    def __init__(self, ifname=""):
        self.ifname = ifname


    def _get_ifaces(self):
        # Assuming Linux, not likely to run on anything else
        dev_file = '/proc/net/dev'
        dev_txt = ""
        fname_ptrn = "[a-z]+[0-9]+"
        ifaces = []

        with open(dev_file, 'r') as f:
            dev_txt = f.read()
            matches = re.findall(fname_ptrn, dev_txt)
            for iface in matches:
                if "eth" in iface :
                    ifaces.append(iface)

        return ifaces


    def _get_interface_ip(self, ifname):
        ip_str = ""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ip_str = socket.inet_ntoa(fcntl.ioctl(sock.fileno(), SIOCGIFADDR,
                                      struct.pack('256s', ifname[:15]))[20:24])
        except socket.error:
            pass

        return ip_str


    def get_ip(self):
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except socket.error:
            return []

        ips = []
        if ip.startswith("127."):
            # get IP for the requested interface
            if self.ifname != "":
                try:
                    ip = self._get_interface_ip(self.ifname)
                    ips.append(ip)
                except IOError:
                    pass
            else: # get all IPs for all interfaces
                ifaces = self._get_ifaces()
                for ifname in ifaces:
                    try:
                        ip = self._get_interface_ip(ifname)
                        ips.append(ip)
                    except IOError:
                        pass

        return ips

