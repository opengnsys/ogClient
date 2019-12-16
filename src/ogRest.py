import threading
import platform
import time
from enum import Enum

if platform.system() == 'Linux':
	from src.linux import ogOperations

class ogResponses(Enum):
	BAD_REQUEST=0
	IN_PROGRESS=1
	OK=2

class ogRest():
	def getResponse(self, response):
		if response == ogResponses.BAD_REQUEST:
			return 'HTTP/1.0 400 Bad request\r\n\r\n'
		if response == ogResponses.IN_PROGRESS:
			return 'HTTP/1.0 202 Accepted\r\n\r\n'
		if response == ogResponses.OK:
			return 'HTTP/1.0 200 OK\r\n\r\n'

	def processOperation(self, op, URI, client):
		if ("poweroff" in URI):
			self.process_poweroff(client)
		elif ("reboot" in URI):
			self.process_reboot(client)
		elif ("probe" in URI):
			self.process_probe(client)
		else:
			client.send(self.getResponse(ogResponses.BAD_REQUEST))

		return 0

	def process_reboot(self, client):
		# Rebooting thread
		def rebt():
			ogOperations.reboot()

		client.send(self.getResponse(ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=rebt).start()

	def process_poweroff(self, client):
		# Powering off thread
		def pwoff():
			time.sleep(2)
			ogOperations.poweroff()

		client.send(self.getResponse(ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=pwoff).start()

	def process_probe(self, client):
		client.send(self.getResponse(ogResponses.OK))
