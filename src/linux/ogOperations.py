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

def execCMD(cmd):
	cmds = cmd.split(" ")
	try:
		result = subprocess.check_output(cmds)
	except:
		raise ValueError('Error: Incorrect command value')

	return result.decode('utf-8')

def procsession(disk, partition):
	result = subprocess.check_output([OG_PATH + 'interfaceAdm/IniciarSesion', disk, partition], shell=True)
	return result.decode('utf-8')

def procsoftware(disk, partition, path):
	result = subprocess.check_output([OG_PATH + 'interfaceAdm/InventarioSoftware', disk, partition, path], shell=True)
	return result.decode('utf-8')

def prochardware(path):
	result = subprocess.check_output([OG_PATH + 'interfaceAdm/InventarioHardware', path], shell=True)
	return result.decode('utf-8')

def procsetup(disk, cache, cachesize, partlist):
	for part in partlist:
		cfg = 'dis=' + disk + '*che=' + cache + '*tch=' + cachesize + '!par=' + part["partition"] + '*cpt='+part["code"] + '*sfi=' + part['filesystem'] + '*tam=' + part['size'] + '*ope=' + part['format'] + '%'
		subprocess.check_output([OG_PATH + 'interfaceAdm/Configurar', disk, cfg], shell=True)

def procirestore(disk, partition, name, repo, ctype, profile, cid):
	result = subprocess.check_output([OG_PATH + 'interfaceAdm/RestaurarImagen', disk, partition, name, repo, ctype], shell=True)
	return result.decode('utf-8')
