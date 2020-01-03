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

class ogThread():
	# Executing cmd thread
	def execcmd(msgqueue, cmd):
		msgqueue.queue.clear()
		msgqueue.put(ogOperations.execCMD(cmd))

	# Powering off thread
	def poweroff():
		time.sleep(2)
		ogOperations.poweroff()

	# Rebooting thread
	def reboot():
		ogOperations.reboot()

	# Process session
	def procsession(msgqueue, disk, partition):
		msgqueue.queue.clear()
		msgqueue.put(ogOperations.procsession(disk, partition))

	# Process software
	def procsoftware(msgqueue, disk, partition, path):
		msgqueue.queue.clear()
		msgqueue.put(ogOperations.procsoftware(disk, partition, path))

	# Process hardware
	def prochardware(msgqueue, path):
		msgqueue.queue.clear()
		msgqueue.put(ogOperations.prochardware(path))

	# Process setup
	def procsetup(msgqueue, disk, cache, cachesize, partlist):
		ogOperations.procsetup(disk, cache, cachesize, partlist)

	# Process image restore
	def procirestore(msgqueue, disk, partition, name, repo, ctype, profile, cid):
		msgqueue.queue.clear()
		msgqueue.put(ogOperations.procirestore(disk, partition, name, repo, ctype, profile, cid))

class ogResponses(Enum):
	BAD_REQUEST=0
	IN_PROGRESS=1
	OK=2

class ogRest():
	def __init__(self):
		self.msgqueue = queue.Queue(1000)

	def getResponse(self, response, jsonResp=None):
		msg = ''
		if response == ogResponses.BAD_REQUEST:
			msg = 'HTTP/1.0 400 Bad request'
		elif response == ogResponses.IN_PROGRESS:
			msg = 'HTTP/1.0 202 Accepted'
		elif response == ogResponses.OK:
			msg = 'HTTP/1.0 200 OK'
		else:
			return msg

		if not jsonResp == None:
			msg = msg + '\nContent-Type:application/json'
			msg = msg + '\nContent-Length:' + str(len(jsonResp.dumpMsg()))
			msg = msg + '\n' + jsonResp.dumpMsg()

		msg = msg + '\r\n\r\n'
		return msg

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
				client.send(self.getResponse(ogResponses.BAD_REQUEST))
		elif ("POST" in op):
			if ("poweroff" in URI):
				self.process_poweroff(client)
			elif ("reboot" in URI):
				self.process_reboot(client)
			elif ("shell/run" in URI):
				self.process_shellrun(client, httpparser.getCMD())
			elif ("session" in URI):
				self.process_session(client, httpparser.getDisk(), httpparser.getPartition())
			elif ("software" in URI):
				self.process_software(client, httpparser.getDisk(), httpparser.getPartition())
			elif ("setup" in URI):
				self.process_setup(client, httpparser.getDisk(), httpparser.getCache(), httpparser.getCacheSize(), httpparser.getPartitionSetup())
			elif ("image/restore" in URI):
				self.process_irestore(client, httpparser.getDisk(),
						      httpparser.getPartition(), httpparser.getName(),
						      httpparser.getRepo(), httpparser.getType(),
						      httpparser.getProfile(), httpparser.getId())
			else:
				client.send(self.getResponse(ogResponses.BAD_REQUEST))
		else:
			client.send(self.getResponse(ogResponses.BAD_REQUEST))

		return 0

	def process_reboot(self, client):
		client.send(self.getResponse(ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=ogThread.reboot).start()

	def process_poweroff(self, client):
		client.send(self.getResponse(ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=ogThread.poweroff).start()

	def process_probe(self, client):
		client.send(self.getResponse(ogResponses.OK))

	def process_shellrun(self, client, cmd):
		if cmd == None:
			client.send(self.getResponse(ogResponses.BAD_REQUEST))
			return

		try:
			ogThread.execcmd(self.msgqueue, cmd)
		except ValueError as err:
			print(err.args[0])
			client.send(self.getResponse(ogResponses.BAD_REQUEST))
			return

		client.send(self.getResponse(ogResponses.OK))

	def process_shellout(self, client):
		jsonResp = jsonResponse()
		if self.msgqueue.empty():
			jsonResp.addElement('out', '')
			client.send(self.getResponse(ogResponses.OK, jsonResp))
		else:
			jsonResp.addElement('out', self.msgqueue.get())
			client.send(self.getResponse(ogResponses.OK, jsonResp))

	def process_session(self, client, disk, partition):
		threading.Thread(target=ogThread.procsession, args=(self.msgqueue, disk, partition,)).start()
		client.send(self.getResponse(ogResponses.OK))

	def process_software(self, client, disk, partition):
		path = '/tmp/CSft-' + client.ip + '-' + partition
		threading.Thread(target=ogThread.procsoftware, args=(self.msgqueue, disk, partition, path,)).start()
		client.send(self.getResponse(ogResponses.OK))

	def process_hardware(self, client):
		path = '/tmp/Chrd-' + client.ip
		threading.Thread(target=ogThread.prochardware, args=(self.msgqueue, path,)).start()
		client.send(self.getResponse(ogResponses.OK))

	def process_schedule(self, client):
		client.send(self.getResponse(ogResponses.OK))

	def process_setup(self, client, disk, cache, cachesize, partlist):
		threading.Thread(target=ogThread.procsetup, args=(self.msgqueue, disk, cache, cachesize, partlist,)).start()
		client.send(self.getResponse(ogResponses.OK))

	def process_irestore(self, client, disk, partition, name, repo, ctype, profile, cid):
		threading.Thread(target=ogThread.procirestore, args=(self.msgqueue, disk, partition, name, repo, ctype, profile, cid,)).start()
		client.send(self.getResponse(ogResponses.OK))
