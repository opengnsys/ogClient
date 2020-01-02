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
