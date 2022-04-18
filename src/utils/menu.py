#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""
Utility module for ogBrowser menu generation
"""

import os
import socket

from src.utils.net import getifaddr, getifhwaddr, ethtool

MENU_TEMPLATE = """
<div align="center" style="font-family: Arial, Helvetica, sans-serif;">
<p style="color:#999999; font-size: 16px; margin: 2em;">
<table border="1" width="100%">
<tr>
<td rowspan="2"><p align="left"><img border="0" src="../images/iconos/logoopengnsys.png"><p> </td>
<td> Hostname </td> <td> IP </td> <td> MAC </td> <td> SPEED </td> </tr>
<tr> <td>{hostname} </td> <td> {ip} </td> <td> {mac} </td> <td> {speed} </td> </tr>
</table>
</p>

{boot_list}

<p><a href="command:poweroff">Power Off</a></p>
</div>
"""

MENU_OS_TEMPLATE = "<p><a href=\"command:bootOs {diskno} {partno}\">Boot {os} ({diskno}, {partno})</a></p>"

def generate_menu(part_setup):
    """
    Writes html menu to /opt/opengnsys/log/{ip}.info.html based on a partition
    setup
    """
    device = os.getenv('DEVICE')
    if not device:
        return False

    ip = getifaddr(device)
    mac = getifhwaddr(device)
    speed = ethtool(device)
    hostname = socket.gethostname()
    menufile = f'/opt/opengnsys/log/{ip}.info.html'

    l = [MENU_OS_TEMPLATE.format(diskno=part['disk'], partno=part['partition'], os=part['os'])
         for part in part_setup if part['os']]
    boot_list = '\n'.join(l)

    with open(menufile, 'w') as f:
        f.write(MENU_TEMPLATE.format(hostname=hostname, ip=ip, mac=mac, speed=speed, boot_list=boot_list))
    return True
