#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import os
import subprocess
from src.ogConfig import *

OG_SHELL = '/bin/bash'

class OgLinuxOperations:

    _ogconfig = ogConfig()
    _config_path = f'{ogConfig.OG_PATH}ogclient/cfg/ogclient.cfg'
    _ogconfig.parser_file(_config_path)
    _url = _ogconfig.get_value_section('opengnsys', 'url')

    def _restartBrowser(self):
        try:
            proc = subprocess.call(["pkill", "-9", "browser"])
            proc = subprocess.Popen(["browser", "-qws", OgLinuxOperations._url])
        except:
            raise ValueError('Error: cannot restart browser')

    def parseGetConf(self, out):
        parsed = {'serial_number': '',
              'disk_setup': '',
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
                    parsed['disk_setup'] = part_setup
                else:
                    parsed['partition_setup'].append(part_setup)
        return parsed

    def poweroff(self):
        if os.path.exists('/scripts/oginit'):
            cmd = f'source {ogConfig.OG_PATH}etc/preinit/loadenviron.sh; ' \
                  f'{ogConfig.OG_PATH}scripts/poweroff'
            subprocess.call([cmd], shell=True, executable=OG_SHELL)
        else:
            subprocess.call(['/sbin/poweroff'])

    def reboot(self):
        if os.path.exists('/scripts/oginit'):
            cmd = f'source {ogConfig.OG_PATH}etc/preinit/loadenviron.sh; ' \
                  f'{ogConfig.OG_PATH}scripts/reboot'
            subprocess.call([cmd], shell=True, executable=OG_SHELL)
        else:
            subprocess.call(['/sbin/reboot'])

    def execCMD(self, request, ogRest):
        cmd = request.getrun()
        cmds = cmd.split(";|\n\r")
        try:
            ogRest.proc = subprocess.Popen(cmds,
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogConfig.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser()

        return output.decode('utf-8')

    def session(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        cmd = f'{ogConfig.OG_PATH}interfaceAdm/IniciarSesion {disk} {partition}'

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

        try:
            cmd = f'{ogConfig.OG_PATH}interfaceAdm/InventarioSoftware {disk} ' \
                  f'{partition} {path}'

            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        return output.decode('utf-8')

    def hardware(self, path, ogRest):
        try:
            cmd = f'{ogConfig.OG_PATH}interfaceAdm/InventarioHardware {path}'
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

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

        cmd = f'{ogConfig.OG_PATH}interfaceAdm/Configurar {disk} {cfg}'
        try:
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogConfig.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser()

        return self.parseGetConf(result.decode('utf-8'))

    def image_restore(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        ctype = request.getType()
        profile = request.getProfile()
        cid = request.getId()
        cmd = f'{ogConfig.OG_PATH}interfaceAdm/RestaurarImagen {disk} {partition} ' \
              f'{name} {repo} {ctype}'

        try:
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogConfig.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser()

        return output.decode('utf-8')

    def image_create(self, path, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        cmd_software = f'{ogConfig.OG_PATH}interfaceAdm/InventarioSoftware {disk} ' \
                   f'{partition} {path}'
        cmd_create_image = f'{ogConfig.OG_PATH}interfaceAdm/CrearImagen {disk} ' \
                   f'{partition} {name} {repo}'

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

        return output.decode('utf-8')

    def refresh(self, ogRest):
        try:
            cmd = f'{ogConfig.OG_PATH}interfaceAdm/getConfiguration'
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            raise ValueError('Error: Incorrect command value')

        self._restartBrowser()

        return self.parseGetConf(output.decode('utf-8'))
