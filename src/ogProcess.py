import threading
import platform
import time
from src import ogRest

if platform.system() == 'Linux':
	from src.linux import ogOperations

class ogProcess():
	def processOperation(self, op, URI, client):
		if ("poweroff" in URI):
			self.process_poweroff(client)
		elif ("reboot" in URI):
			self.process_reboot(client)
		elif ("probe" in URI):
			self.process_probe(client)
		else:
			client.send(ogRest.getResponse(ogRest.ogResponses.BAD_REQUEST))

		return 0

	def process_reboot(self, client):
		# Rebooting thread
		def rebt():
			ogOperations.reboot()

		client.send(ogRest.getResponse(ogRest.ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=rebt).start()

	def process_poweroff(self, client):
		# Powering off thread
		def pwoff():
			time.sleep(2)
			ogOperations.poweroff()

		client.send(ogRest.getResponse(ogRest.ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=pwoff).start()

	def process_probe(self, client):
		client.send(ogRest.getResponse(ogRest.ogResponses.OK))
