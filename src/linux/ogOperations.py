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

def execCMD(httpparser, ogRest):
	cmd = httpparser.getCMD()
	cmds = cmd.split(" ")
	try:
		ogRest.proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def procsession(httpparser, ogRest):
	disk = httpparser.getDisk()
	partition = httpparser.getPartition()

	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/IniciarSesion', disk, partition], stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def procsoftware(httpparser, path, ogRest):
	disk = httpparser.getDisk()
	partition = httpparser.getPartition()

	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/InventarioSoftware', disk, partition, path], stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def prochardware(path, ogRest):
	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/InventarioHardware', path], stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def procsetup(httpparser, ogRest):
	disk = httpparser.getDisk()
	cache = httpparser.getCache()
	cachesize = httpparser.getCacheSize()
	partlist = httpparser.getPartitionSetup()
	listConfigs = []

	for part in partlist:
		i = 0
		json = {}
		cfg = 'dis=' + disk + '*che=' + cache + '*tch=' + cachesize + '!par=' + part["partition"] + '*cpt='+part["code"] + '*sfi=' + part['filesystem'] + '*tam=' + part['size'] + '*ope=' + part['format'] + '%'
		if ogRest.terminated:
			break

		try:
			ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/Configurar', disk, cfg], stdout=subprocess.PIPE, shell=True)
			(output, error) = ogRest.proc.communicate()
		except:
			continue

		result = subprocess.check_output([OG_PATH + 'interfaceAdm/getConfiguration'], shell=True)
		val = result.decode('utf-8').rstrip().split('\t')
		while i < len(val):
			val[i] = val[i].split('=')[1]
			i += 1

		json['partition'] = val[1]
		json['code'] = val[4]
		json['filesystem'] = val[2]
		json['size'] = val[5]
		json['format'] = val[6]
		listConfigs.append(json)

	return listConfigs

def procirestore(httpparser, ogRest):
	disk = httpparser.getDisk()
	partition = httpparser.getPartition()
	name = httpparser.getName()
	repo = httpparser.getRepo()
	ctype = httpparser.getType()
	profile = httpparser.getProfile()
	cid = httpparser.getId()

	try:
		ogRest.proc = subprocess.Popen([OG_PATH + 'interfaceAdm/RestaurarImagen', disk, partition, name, repo, ctype], stdout=subprocess.PIPE, shell=True)
		(output, error) = ogRest.proc.communicate()
	except:
		raise ValueError('Error: Incorrect command value')

	return output.decode('utf-8')

def procicreate(path, httpparser, ogRest):
	disk = httpparser.getDisk()
	partition = httpparser.getPartition()
	name = httpparser.getName()
	repo = httpparser.getRepo()

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
