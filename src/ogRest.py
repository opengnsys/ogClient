import threading
import platform
import time
from enum import Enum
import json
import queue

from src.HTTPParser import *

if platform.system() == 'Linux':
	from src.linux import ogOperations

class jsonResponse():
	def __init__(self):
		self.jsontree = {}

	def addElement(self, key, value):
		self.jsontree[key] = value

	def dumpMsg(self):
		return json.dumps(self.jsontree)

class restResponse():
	def getResponse(response, jsonResp=None):
		msg = ''
		if response == ogResponses.BAD_REQUEST:
			msg = 'HTTP/1.0 400 Bad request'
		elif response == ogResponses.IN_PROGRESS:
			msg = 'HTTP/1.0 202 Accepted'
		elif response == ogResponses.OK:
			msg = 'HTTP/1.0 200 OK'
		elif response == ogResponses.INTERNAL_ERR:
			msg = 'HTTP/1.0 500 Internal Server Error'
		else:
			return msg

		if not jsonResp == None:
			msg = msg + '\nContent-Type:application/json'
			msg = msg + '\nContent-Length:' + str(len(jsonResp.dumpMsg()))
			msg = msg + '\n' + jsonResp.dumpMsg()

		msg = msg + '\r\n\r\n'
		return msg

class ogThread():
	# Executing cmd thread
	def execcmd(msgqueue, httpparser):
		msgqueue.queue.clear()
		msgqueue.put(ogOperations.execCMD(httpparser))

	# Powering off thread
	def poweroff():
		time.sleep(2)
		ogOperations.poweroff()

	# Rebooting thread
	def reboot():
		ogOperations.reboot()

	# Process session
	def procsession(client, httpparser):
		try:
			ogOperations.procsession(httpparser)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		client.send(restResponse.getResponse(ogResponses.OK))

	# Process software
	def procsoftware(client, httpparser, path):
		try:
			ogOperations.procsoftware(httpparser, path)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		jsonResp = jsonResponse()
		jsonResp.addElement('disk', httpparser.getDisk())
		jsonResp.addElement('partition', httpparser.getPartition())

		f = open(path, "r")
		lines = f.readlines()
		f.close()
		jsonResp.addElement('software', lines[0])

		client.send(restResponse.getResponse(ogResponses.OK, jsonResp))

	# Process hardware
	def prochardware(client, path):
		try:
			ogOperations.prochardware(path)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		jsonResp = jsonResponse()
		f = open(path, "r")
		lines = f.readlines()
		f.close()
		jsonResp.addElement('hardware', lines[0])
		client.send(restResponse.getResponse(ogResponses.OK, jsonResp))

	# Process setup
	def procsetup(msgqueue, httpparser):
		ogOperations.procsetup(httpparser)

	# Process image restore
	def procirestore(httpparser):
		try:
			ogOperations.procirestore(httpparser)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		client.send(restResponse.getResponse(ogResponses.OK))

class ogResponses(Enum):
	BAD_REQUEST=0
	IN_PROGRESS=1
	OK=2
	INTERNAL_ERR=3

class ogRest():
	def __init__(self):
		self.msgqueue = queue.Queue(1000)

	def processOperation(self, httpparser, client):
		op = httpparser.getRequestOP()
		URI = httpparser.getURI()
		if ("GET" in op):
			if ("probe" in URI):
				self.process_probe(client)
			elif ("shell/output" in URI):
				self.process_shellout(client)
			elif ("hardware" in URI):
				self.process_hardware(client)
			elif ("run/schedule" in URI):
				self.process_schedule(client)
			else:
				client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))
		elif ("POST" in op):
			if ("poweroff" in URI):
				self.process_poweroff(client)
			elif ("reboot" in URI):
				self.process_reboot(client)
			elif ("shell/run" in URI):
				self.process_shellrun(client, httpparser)
			elif ("session" in URI):
				self.process_session(client, httpparser)
			elif ("software" in URI):
				self.process_software(client, httpparser)
			elif ("setup" in URI):
				self.process_setup(client, httpparser)
			elif ("image/restore" in URI):
				self.process_irestore(client, httpparser)
			else:
				client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))
		else:
			client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))

		return 0

	def process_reboot(self, client):
		client.send(restResponse.getResponse(ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=ogThread.reboot).start()

	def process_poweroff(self, client):
		client.send(restResponse.getResponse(ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=ogThread.poweroff).start()

	def process_probe(self, client):
		client.send(restResponse.getResponse(ogResponses.OK))

	def process_shellrun(self, client, httpparser):
		if httpparser.getCMD() == None:
			client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))
			return

		try:
			ogThread.execcmd(self.msgqueue, httpparser)
		except ValueError as err:
			print(err.args[0])
			client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))
			return

		client.send(restResponse.getResponse(ogResponses.OK))

	def process_shellout(self, client):
		jsonResp = jsonResponse()
		if self.msgqueue.empty():
			jsonResp.addElement('out', '')
			client.send(restResponse.getResponse(ogResponses.OK, jsonResp))
		else:
			jsonResp.addElement('out', self.msgqueue.get())
			client.send(restResponse.getResponse(ogResponses.OK, jsonResp))

	def process_session(self, client, httpparser):
		threading.Thread(target=ogThread.procsession, args=(client, httpparser,)).start()

	def process_software(self, client, httpparser):
		path = '/tmp/CSft-' + client.ip + '-' + httpparser.getPartition()
		threading.Thread(target=ogThread.procsoftware, args=(client, httpparser, path,)).start()

	def process_hardware(self, client):
		path = '/tmp/Chrd-' + client.ip
		threading.Thread(target=ogThread.prochardware, args=(client, path,)).start()

	def process_schedule(self, client):
		client.send(restResponse.getResponse(ogResponses.OK))

	def process_setup(self, client, httpparser):
		threading.Thread(target=ogThread.procsetup, args=(self.msgqueue, httpparser,)).start()
		client.send(restResponse.getResponse(ogResponses.OK))

	def process_irestore(self, client, httpparser):
		threading.Thread(target=ogThread.procirestore, args=(client, httpparser,)).start()
