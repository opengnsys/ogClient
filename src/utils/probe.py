#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import os
import subprocess

from subprocess import PIPE

def getlinuxversion(osrelease):
    """
    Parses a os-release file to fetch 'PRETTY_NAME' key.
    If file or key are not found, then returns generic
    'Linux' string.
    """
    with open(osrelease, 'r') as f:
        for line in f:
            if line.find('=') == -1:
                continue
            key, value = line.split('=')
            if key == 'PRETTY_NAME':
                value = value.replace('\n', '')
                value = value.strip('"')
                return value
        return 'Linux'


def getwindowsversion(winreghives):
    """
    Tries to obtain windows version information by
    querying the SOFTWARE registry hive. Registry
    hives path is a required parameter.

    Runs hivexget(1) to fetch ProductName and
    ReleaseId. If something fails (hivexget is
    not installed, or registry is not found) it
    returns a generic "Microsoft Windows" string.
    """

    # XXX: 3.6 friendly
    try:
        proc_prodname = subprocess.run(['hivexget',
            f'{winreghives}/SOFTWARE',
            'microsoft\windows nt\currentversion',
            'ProductName'], stdout=PIPE)
        proc_releaseid = subprocess.run(['hivexget',
            f'{winreghives}/SOFTWARE',
            'microsoft\windows nt\currentversion',
            'ReleaseId'], stdout=PIPE)

        prodname = proc_prodname.stdout.decode().replace('\n', '')
        releaseid = proc_releaseid.stdout.decode().replace('\n', '')

        if proc_prodname.returncode == 0 and proc_releaseid.returncode == 0:
            return f'{prodname} {releaseid}'
    except FileNotFoundError:  # hivexget command not found
        pass
    return 'Microsoft Windows'


def os_probe(mountpoint):
    """
    Probes mountpoint for typical OS dependant files.

    Windows: Tries finding and querying the software
    registry hive.
    Linux: Looks for /etc/os-release file.

    Returns a string depending on the OS it detects.
    """
    winreghives = f'{mountpoint}Windows/System32/config'
    osrelease = f'{mountpoint}/etc/os-release'

    if os.path.exists(osrelease):
        return getlinuxversion(osrelease)
    elif os.path.exists(winreghives):
        return getwindowsversion(winreghives)
    else:
        return ''
