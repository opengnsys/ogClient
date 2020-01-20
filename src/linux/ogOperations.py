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
	listConfigs = []
	disk = -1;

	configs = out.split('\n')
	configs = filter(None, configs)
	for item in configs:
		i = 0
		json = {}
		val = item.rstrip().split('\t')
		while i < len(val):
			val[i] = val[i].split('=')[1]
			i += 1

		json['partition'] = val[1]
		json['code'] = val[4]
		json['filesystem'] = val[2]
		json['size'] = val[5]
		json['format'] = val[6]
		disk = val[0]
		listConfigs.append(json)

	return [disk, listConfigs]

def poweroff():
	if os.path.exists('/scripts/oginit'):
		subprocess.call('source ' + OG_SCRIPT_PATH + 'etc/preinit/loadenviron.sh; ' + OG_SCRIPT_PATH + 'scripts/poweroff', shell=True)
	else:
		subprocess.call(['/sbin/poweroff'])

def reboot():
	if os.path.exists('/scripts/oginit'):
		subprocess.call('source ' + OG_SCRIPT_PATH + 'etc/preinit/loadenviron.sh; ' + OG_SCRIPT_PATH + 'scripts/reboot', shell=True)
	else:
		subprocess.call(['/sbin/reboot'])

def execCMD(request, ogRest):
	cmd = request.getrun()
	cmds = cmd.split(" ")
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
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/InventarioSoftware', disk, partition, path], stdout=subprocess.PIPE, shell=True)
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

	for part in partlist:
		cfg = 'dis=' + disk + '*che=' + cache + '*tch=' + cachesize + '!par=' + part["partition"] + '*cpt='+part["code"] + '*sfi=' + part['filesystem'] + '*tam=' + part['size'] + '*ope=' + part['format'] + '%'
		if ogRest.terminated:
			break

		try:
			ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/Configurar', disk, cfg], stdout=subprocess.PIPE, shell=True)
			(output, error) = ogRest.proc.communicate()
		except:
			continue

	result = subprocess.check_output([OG_PATH + 'interfaceAdm/getConfiguration'], shell=True)
	return parseGetConf(result.decode('utf-8'))[1]

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

	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/InventarioSoftware', disk, partition, path], stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	if ogRest.terminated:
		return

	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/CrearImagen', disk, partition, name, repo], stdout=subprocess.PIPE, shell=True)
		ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def refresh(ogRest):
	listConfigs = []
	disk = -1;

	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/getConfiguration'], stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return parseGetConf(output.decode('utf-8'))
