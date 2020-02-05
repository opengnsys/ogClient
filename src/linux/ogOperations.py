#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import os
import subprocess

OG_PATH = '/opt/opengnsys/'

def parseGetConf(out):
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

def poweroff():
	if os.path.exists('/scripts/oginit'):
		subprocess.call('source ' + OG_PATH + 'etc/preinit/loadenviron.sh; ' + OG_PATH + 'scripts/poweroff', shell=True)
	else:
		subprocess.call(['/sbin/poweroff'])

def reboot():
	if os.path.exists('/scripts/oginit'):
		subprocess.call('source ' + OG_PATH + 'etc/preinit/loadenviron.sh; ' + OG_PATH + 'scripts/reboot', shell=True)
	else:
		subprocess.call(['/sbin/reboot'])

def execCMD(request, ogRest):
	cmd = request.getrun()
	cmds = cmd.split(";|\n")
	try:
		ogRest.proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def session(request, ogRest):
	disk = request.getDisk()
	partition = request.getPartition()

	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/IniciarSesion', disk, partition], stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def software(request, path, ogRest):
	disk = request.getDisk()
	partition = request.getPartition()

	try:
		cmd = OG_PATH + 'interfaceAdm/InventarioSoftware '
		cmd += str(disk) + ' '
		cmd += str(partition) + ' '
		cmd += path
		ogRest.proc = subprocess.Popen([cmd],
					       stdout=subprocess.PIPE,
					       shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def hardware(path, ogRest):
	try:
		cmd = [OG_PATH + 'interfaceAdm/InventarioHardware ' + path]
		ogRest.proc = subprocess.Popen(cmd,
					       stdout=subprocess.PIPE,
					       shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def setup(request, ogRest):
	disk = request.getDisk()
	cache = request.getCache()
	cachesize = request.getCacheSize()
	partlist = request.getPartitionSetup()
	listConfigs = []
	cfg = 'dis=' + disk + '*che=' + cache + '*tch=' + cachesize + '!'

	for part in partlist:
		cfg += 'par=' + part["partition"] + '*cpt='+part["code"] + \
		       '*sfi=' + part['filesystem'] + '*tam=' + \
		       part['size'] + '*ope=' + part['format'] + '%'
		if ogRest.terminated:
			break

	cmd = OG_PATH + 'interfaceAdm/Configurar' + " " + disk + " " + cfg
	try:
		ogRest.proc = subprocess.Popen([cmd],
					       stdout=subprocess.PIPE,
					       shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	cmd_get_conf = OG_PATH + 'interfaceAdm/getConfiguration'
	result = subprocess.check_output([cmd_get_conf], shell=True)
	return parseGetConf(result.decode('utf-8'))

def image_restore(request, ogRest):
	disk = request.getDisk()
	partition = request.getPartition()
	name = request.getName()
	repo = request.getRepo()
	ctype = request.getType()
	profile = request.getProfile()
	cid = request.getId()

	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/RestaurarImagen', disk, partition, name, repo, ctype], stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def image_create(path, request, ogRest):
	disk = request.getDisk()
	partition = request.getPartition()
	name = request.getName()
	repo = request.getRepo()
	cmd_software = f'{OG_PATH}interfaceAdm/InventarioSoftware {disk} ' \
		       f'{partition} {path}'
	cmd_create_image = f'{OG_PATH}interfaceAdm/CrearImagen {disk} ' \
			   f'{partition} {name} {repo}'

	try:
		ogRest.proc = subprocess.Popen([cmd_software],
					       stdout=subprocess.PIPE,
					       shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	if ogRest.terminated:
		return

	try:
		ogRest.proc = subprocess.Popen([cmd_create_image],
					       stdout=subprocess.PIPE,
					       shell=True)
		ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def refresh(ogRest):
	try:
		cmd = OG_PATH + 'interfaceAdm/getConfiguration'
		ogRest.proc = subprocess.Popen([cmd],
					       stdout=subprocess.PIPE,
					       shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return parseGetConf(output.decode('utf-8'))
