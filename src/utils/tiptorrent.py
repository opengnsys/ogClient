import hashlib
import logging
import os
import shlex
import shutil
import subprocess
import urllib.request

def _compute_md5(path, bs=2**20):
    m = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            buf = f.read(bs)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def tip_fetch_csum(tip_addr, image_name):
    """
    """
    url = f'http://{tip_addr}:9999/{image_name}.img.full.sum'
    with urllib.request.urlopen(f'{url}') as resp:
        r = resp.readline().rstrip().decode('utf-8')
    return r


def tip_write_csum(image_name):
    """
    TODO: Check for CACHE partition
    """
    image_path = f'/opt/opengnsys/cache/opt/opengnsys/images/{image_name}.img'

    if not os.path.exists(image_path):
        logging.error('Invalid image path')
        raise ValueError('Invalid image path for tiptorrent checksum writing')

    filename = image_path + ".full.sum"
    csum = _compute_md5(image_path)
    with open(filename, 'w') as f:
        f.write(csum)

    return csum


def tip_check_csum(tip_addr, image_name):
    """
    """
    image_path = f'/opt/opengnsys/cache/opt/opengnsys/images/{image_name}.img'
    if not os.path.exists(image_path):
        logging.error('Invalid image path')
        raise ValueError('Invalid image path for tiptorrent image csum comparison')

    cache_csum = _compute_md5(image_path)
    remote_csum = tip_fetch_csum(tip_addr, image_name)
    logging.debug(f'cache_csum: {cache_csum}')
    logging.debug(f'remote_csum: {remote_csum}')
    return cache_csum == remote_csum


def tip_client_get(tip_addr, image_name):
    """
    """
    logging.info(f'Fetching image {image_name} from tiptorrent server at {tip_addr}')
    cmd = f'tiptorrent-client {tip_addr} {image_name}.img'
    logfile = open('/tmp/command.log', 'wb', 0)

    try:
        proc = subprocess.Popen(shlex.split(cmd),
                                stdout=logfile,
                                cwd='/opt/opengnsys/cache/opt/opengnsys/images/')
        proc.communicate()
    except:
        logging.error('Exception when running tiptorrent client GET subprocess')
        raise ValueError('Unexpected error running tiptorrent subprocess')
    finally:
        logfile.close()

    if proc.returncode != 0:
        logging.error(f'Error fetching image {image_name} via tiptorrent')
        raise ValueError('Tiptorrent download failed')
    else:
        logging.info('tiptorrent transfer completed, writing checksum')
        tip_write_csum(image_name)
