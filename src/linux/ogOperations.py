#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import os
import json
import subprocess
from src.ogClient import ogClient

OG_SHELL = '/bin/bash'

class OgLinuxOperations:
    def __init__(self, config):
        self._url = config['opengnsys']['url']
        self._url_log = config['opengnsys']['url_log']

    def _restartBrowser(self, url):
        try:
            proc = subprocess.call(["pkill", "-9", "browser"])
            proc = subprocess.Popen(["browser", "-qws", url])
        except:
            raise ValueError('Error: cannot restart browser')

    def parseGetConf(self, out):
        parsed = {'serial_number': '',
              'disk_setup': list(),
              'partition_setup': list()}
        configs = out.split('\n')
        for line in configs[:-1]:
            if 'ser=' in line:
                parsed['serial_number'] = line.partition('ser=')[2]
            else:
                part_setup = {}
                params = dict(param.split('=') for param in line.split('\t'))
                # Parse partition configuration.
                part_setup['disk'] = params['disk']
                part_setup['partition'] = params['par']
                part_setup['code'] = params['cpt']
                part_setup['filesystem'] = params['fsi']
                part_setup['os'] = params['soi']
                part_setup['size'] = params['tam']
                part_setup['used_size'] = params['uso']
                if part_setup['partition'] == '0':
                    parsed['disk_setup'].append(part_setup)
                else:
                    parsed['partition_setup'].append(part_setup)
        return parsed

    def poweroff(self):
        if os.path.exists('/scripts/oginit'):
            cmd = f'source {ogClient.OG_PATH}etc/preinit/loadenviron.sh; ' \
                  f'{ogClient.OG_PATH}scripts/poweroff'
            subprocess.call([cmd], shell=True, executable=OG_SHELL)
        else:
            subprocess.call(['/sbin/poweroff'])

    def reboot(self):
        if os.path.exists('/scripts/oginit'):
            cmd = f'source {ogClient.OG_PATH}etc/preinit/loadenviron.sh; ' \
                  f'{ogClient.OG_PATH}scripts/reboot'
            subprocess.call([cmd], shell=True, executable=OG_SHELL)
        else:
            subprocess.call(['/sbin/reboot'])

    def shellrun(self, request, ogRest):
        cmd = request.getrun()
        cmds = cmd.split(";|\n\r")

        self._restartBrowser(self._url_log)

        try:
            ogRest.proc = subprocess.Popen(cmds,
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogClient.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser(self._url)

        return output.decode('utf-8')

    def session(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        cmd = f'{ogClient.OG_PATH}interfaceAdm/IniciarSesion {disk} {partition}'

        try:
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        return output.decode('utf-8')

    def software(self, request, path, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()

        self._restartBrowser(self._url_log)

        try:
            cmd = f'{ogClient.OG_PATH}interfaceAdm/InventarioSoftware {disk} ' \
                  f'{partition} {path}'

            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        self._restartBrowser(self._url)

        software = ''
        with open(path, 'r') as f:
            software = f.read()
        return software

    def hardware(self, path, ogRest):
        self._restartBrowser(self._url_log)

        try:
            cmd = f'{ogClient.OG_PATH}interfaceAdm/InventarioHardware {path}'
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        self._restartBrowser(self._url)

        return output.decode('utf-8')

    def setup(self, request, ogRest):
        disk = request.getDisk()
        cache = request.getCache()
        cache_size = request.getCacheSize()
        partlist = request.getPartitionSetup()
        cfg = f'dis={disk}*che={cache}*tch={cache_size}!'

        for part in partlist:
            cfg += f'par={part["partition"]}*cpt={part["code"]}*' \
                   f'sfi={part["filesystem"]}*tam={part["size"]}*' \
                   f'ope={part["format"]}%'

            if ogRest.terminated:
                break

        cmd = f'{ogClient.OG_PATH}interfaceAdm/Configurar {disk} {cfg}'
        try:
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogClient.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser(self._url)

        return self.parseGetConf(result.decode('utf-8'))

    def image_restore(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        ctype = request.getType()
        profile = request.getProfile()
        cid = request.getId()
        cmd = f'{ogClient.OG_PATH}interfaceAdm/RestaurarImagen {disk} {partition} ' \
              f'{name} {repo} {ctype}'

        self._restartBrowser(self._url_log)

        try:
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
            if (ogRest.proc.returncode):
                raise Exception
        except:
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogClient.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser(self._url)

        return output.decode('utf-8')

    def image_create(self, path, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        cmd_software = f'{ogClient.OG_PATH}interfaceAdm/InventarioSoftware {disk} ' \
                   f'{partition} {path}'
        cmd_create_image = f'{ogClient.OG_PATH}interfaceAdm/CrearImagen {disk} ' \
                   f'{partition} {name} {repo}'

        self._restartBrowser(self._url_log)

        try:
            ogRest.proc = subprocess.Popen([cmd_software],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        if ogRest.terminated:
            return

        try:
            ogRest.proc = subprocess.Popen([cmd_create_image],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        with open('/tmp/image.info') as file_info:
            line = file_info.readline().rstrip()

        image_info = {}

        (image_info['clonator'],
         image_info['compressor'],
         image_info['filesystem'],
         image_info['datasize'],
         image_info['clientname']) = line.split(':', 5)

        os.remove('/tmp/image.info')

        self._restartBrowser(self._url)

        return image_info

    def refresh(self, ogRest):
        self._restartBrowser(self._url_log)

        try:
            cmd = f'{ogClient.OG_PATH}interfaceAdm/getConfiguration'
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        self._restartBrowser(self._url)

        return self.parseGetConf(output.decode('utf-8'))
