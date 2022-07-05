#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import logging
import os
import subprocess

from subprocess import DEVNULL, PIPE

import psutil


def find_mountpoint(path):
    """
    Returns mountpoint of a given path
    """
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path


def mount_mkdir(source, target):
    """
    Mounts and creates the mountpoint directory if it's not present.

    Return True if mount is sucessful or if target is already a mountpoint.
    """
    if not os.path.exists(target):
        os.mkdir(target)

    if not os.path.ismount(target):
        return mount(source, target)
    else:
        return True

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


def ogReduceFs(disk, part):
    """
    Bash function 'ogReduceFs' wrapper
    """
    proc = subprocess.run(f'ogReduceFs {disk} {part}',
                          shell=True, stdout=PIPE)

    if proc.returncode == 0:
        subprocess.run(f'ogUnmount {disk} {part}',
                       shell=True, stdout=PIPE)
        return proc.stdout.decode().replace('\n', '')

    logging.warn(f'ogReduceFS exited with code {proc.returncode}')
    return None


def ogExtendFs(disk, part):
    """
    Bash function 'ogExtendFs' wrapper
    """
    proc = subprocess.run(f'ogExtendFs {disk} {part}',
                          shell=True)
    return proc.returncode
