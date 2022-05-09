#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import os
import subprocess
import platform

from subprocess import PIPE

from src.utils.fs import find_mountpoint

def getlinuxversion(osrelease):
    """
    Parses a os-release file to fetch 'PRETTY_NAME' key.
    If file or key are not found, then returns generic
    'Linux' string.
    """
    mountpoint = find_mountpoint(osrelease)

    with open(osrelease, 'r') as f:
        for line in f:
            if line.find('=') == -1:
                continue
            key, value = line.split('=')
            if key == 'PRETTY_NAME':
                value = value.replace('\n', '')
                value = value.strip('"')
                bits = ' 64 bits' if linux_is64bit(mountpoint) else ''
                return f'{value}{bits}'
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
        bits = ' 64 bits' if windows_is64bit(winreghives) else ''

        if proc_prodname.returncode == 0 and proc_releaseid.returncode == 0:
            return f'{prodname} {releaseid}{bits}'
    except FileNotFoundError:  # hivexget command not found
        pass
    return 'Microsoft Windows'


def windows_is64bit(winreghives):
    """
    Check for 64 bit Windows by means of retrieving the value of
    ProgramW6432Dir. This key is set if Windows is running 64 bit.

    If set returns True.
    If not set or hivexget exits with non-zero, returns False.
    """
    try:
        proc_hivexget = subprocess.run(['hivexget',
            f'{winreghives}/SOFTWARE',
            'Microsoft\Windows\CurrentVersion',
            'ProgramW6432Dir'], stdout=PIPE)
        stdout = proc_hivexget.stdout.decode().replace('\n', '')

        if proc_hivexget.returncode == 0 and stdout:
            return True
    except FileNotFoundError:  # hivexget command not found
        pass
    return False


def linux_is64bit(mountpoint):
    """
    If /sbin/init is detected, check if compiled for 64-bit machine.

    If init executable is not found, check for /lib64.
    If /lib64 is found returns True, otherwise False.
    """
    init_path = f'{mountpoint}/sbin/init'
    lib64_path = f'{mountpoint}/lib64'
    if os.path.exists(init_path):
        bits, linkage = platform.architecture(executable=init_path)
        return True if bits == '64bit' else False
    return os.path.exists(lib64_path)


def cache_probe():
    """
    Runs 'blkid -L CACHE' and returns stripped stdout
    """
    proc_blkid = subprocess.run(['blkid', '-L', 'CACHE'],
                                stdout=subprocess.PIPE)
    stdout = proc_blkid.stdout.decode().strip()
    return stdout

def os_probe(mountpoint):
    """
    Probes mountpoint for typical OS dependant files.

    Windows: Tries finding and querying the software
    registry hive.
    Linux: Looks for /etc/os-release file.

    Returns a string depending on the OS it detects.
    """
    winreghives = f'{mountpoint}/Windows/System32/config'
    osrelease = f'{mountpoint}/etc/os-release'

    if os.path.exists(osrelease):
        return getlinuxversion(osrelease)
    elif os.path.exists(winreghives):
        return getwindowsversion(winreghives)
    else:
        return ''
