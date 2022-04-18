#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import os
import subprocess

from subprocess import DEVNULL

import psutil


def mount_mkdir(source, target):
    """
    Mounts and creates the mountpoint directory if it's not present.
    """
    if not os.path.exists(target):
        os.mkdir(target)
    if not os.path.ismount(target):
        return mount(source, target)
    return False


def mount(source, target):
    """
    Mounts source into target directoru using mount(8).

    Return true if exit code is 0. False otherwise.
    """
    cmd = f'mount {source} {target}'
    proc = subprocess.run(cmd.split(), stderr=DEVNULL)

    return not proc.returncode


def umount(target):
    """
    Umounts target using umount(8).

    Return true if exit code is 0. False otherwise.
    """
    cmd = f'umount {target}'
    proc = subprocess.run(cmd.split(), stderr=DEVNULL)

    return not proc.returncode


def get_usedperc(mountpoint):
    """
    Returns percetage of used filesystem as decimal number.
    """
    try:
        total, used, free, perc = psutil.disk_usage(mountpoint)
    except FileNotFoundError:
        return '0'
    return str(perc)
