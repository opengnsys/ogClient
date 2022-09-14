import ipaddress
import logging
import os
import subprocess
import shlex

from subprocess import PIPE

def ogGetImageInfo(path):
    """
    Bash function 'ogGetImageInfo' wrapper (client/engine/Image.lib)
    """
    proc = subprocess.run(f'ogGetImageInfo {path}',
                          stdout=PIPE, shell=True,
                          encoding='utf-8')

    if proc.stdout.count(':') != 3:
        return ''

    image_info = {}
    (image_info['clonator'],
     image_info['compressor'],
     image_info['filesystem'],
     image_info['datasize']) = proc.stdout.rstrip().split(':', 4)
    image_info['clientname'] = os.getenv('HOSTNAME')
    return image_info


def cambiar_acceso(mode='rw', user='opengnsys', pwd='og'):
    """
    'CambiarAcceso' wrapper (admin/Interface/CambiarAcceso)
    """
    if mode not in ['rw', 'ro']:
        raise ValueError('Invalid remount mode option')

    cmd = shlex.split(f'mount -o remount,{mode},username={user},password={pwd} /opt/opengnsys/images')
    ret = True
    try:
        subprocess.run(cmd, check=True)
    except CalledProcessError:
        ret = False
    finally:
        return ret


def ogChangeRepo(ip):
    """
    Bash function 'ogGetImageInfo' wrapper (client/engine/Net.lib)
    """
    try:
        ipaddr = ipaddress.ip_address(ip)
    except ValueError as e:
        raise

    return subprocess.run(f'ogChangeRepo {ipaddr}',
                          shell=True)


def ogCopyEfiBootLoader(disk, partition):
    cmd = f'ogCopyEfiBootLoader {disk} {partition}'
    try:
        proc = subprocess.run(cmd,
                              shell=True)
    except:
        logging.error('Exception when running ogCopyEfiBootLoader subprocess')
        raise ValueError('Subprocess error: ogCopyEfiBootloader')
