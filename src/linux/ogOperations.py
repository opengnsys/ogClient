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
