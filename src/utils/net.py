#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import array
import fcntl
import socket
import struct

def ethtool(interface):
    try:
        ETHTOOL_GSET = 0x00000001
        SIOCETHTOOL = 0x8946
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd = sock.fileno()
        ecmd = array.array(
                "B", struct.pack("I39s", ETHTOOL_GSET, b"\x00" * 39)
               )
        interface = interface.encode("utf-8")
        ifreq = struct.pack("16sP", interface, ecmd.buffer_info()[0])
        fcntl.ioctl(sockfd, SIOCETHTOOL, ifreq)
        res = ecmd.tobytes()
        speed = struct.unpack("12xH29x", res)[0]
    except IOError:
        speed = 0
    finally:
        sock.close()
    return speed

def getifaddr(device):
    """
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(device[:15], 'utf-8'))
    )[20:24])

def getifhwaddr(device):
    """
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    hwaddr = fcntl.ioctl(
        s.fileno(),
        0x8927,  # SIOCGIFHWADDR
        struct.pack('256s', bytes(device[:15], 'utf-8'))
        )[18:24]
    return "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("BBBBBB", hwaddr)
