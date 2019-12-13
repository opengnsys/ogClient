import threading
import platform
import time
from src import ogRest

if platform.system() == 'Linux':
	from src.linux import ogOperations

class ogProcess():
	def processOperation(self, op, URI, sock):
		if ("poweroff" in URI):
			sock.send(bytes(ogRest.getResponse(ogRest.ogResponses.IN_PROGRESS), 'utf-8'))
			sock.close()
			self.process_poweroff()
			return 0
		elif ("reboot" in URI):
			sock.send(bytes(ogRest.getResponse(ogRest.ogResponses.IN_PROGRESS), 'utf-8'))
			sock.close()
			self.process_reboot()
			return 0
		elif ("probe" in URI):
			sock.send(bytes(ogRest.getResponse(ogRest.ogResponses.OK), 'utf-8'))
		else:
			sock.send(bytes(ogRest.getResponse(ogRest.ogResponses.BAD_REQUEST), 'utf-8'))

		return 1

	def process_reboot(self):
		# Rebooting thread
		def rebt():
			ogOperations.reboot()
		threading.Thread(target=rebt).start()

	def process_poweroff(self):
		# Powering off thread
		def pwoff():
			time.sleep(2)
			ogOperations.poweroff()
		threading.Thread(target=pwoff).start()
