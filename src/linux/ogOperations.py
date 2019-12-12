import os
import subprocess

def poweroff():
	if os.path.exists('/scripts/oginit'):
		subprocess.call('source /opt/opengnsys/etc/preinit/loadenviron.sh; /opt/opengnsys/scripts/poweroff', shell=True)
	else:
		subprocess.call(['/sbin/poweroff'])

def reboot():
	if os.path.exists('/scripts/oginit'):
		subprocess.call('source /opt/opengnsys/etc/preinit/loadenviron.sh; /opt/opengnsys/scripts/reboot', shell=True)
	else:
		subprocess.call(['/sbin/reboot'])
