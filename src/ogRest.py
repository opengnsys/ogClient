#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import threading
import platform
import time
from enum import Enum
import json
import queue
import sys
import os
import signal

from src.restRequest import *

from src.linux.ogOperations import OgLinuxOperations

class ThreadState(Enum):
	IDLE = 0
	BUSY = 1

class jsonBody():
	def __init__(self, dictionary=None):
		if dictionary:
			self.jsontree = dictionary
		else:
			self.jsontree = {}

	def add_element(self, key, value):
		self.jsontree[key] = value

	def dump(self):
		return json.dumps(self.jsontree)

class restResponse():
	def __init__(self, response, json_body=None):
		self.msg = ''
		if response == ogResponses.BAD_REQUEST:
			self.msg = 'HTTP/1.0 400 Bad Request'
		elif response == ogResponses.IN_PROGRESS:
			self.msg = 'HTTP/1.0 202 Accepted'
		elif response == ogResponses.OK:
			self.msg = 'HTTP/1.0 200 OK'
		elif response == ogResponses.INTERNAL_ERR:
			self.msg = 'HTTP/1.0 500 Internal Server Error'
		elif response == ogResponses.UNAUTHORIZED:
			self.msg = 'HTTP/1.0 401 Unauthorized'
		elif response == ogResponses.SERVICE_UNAVAILABLE:
			self.msg = 'HTTP/1.0 503 Service Unavailable'
		else:
			return self.msg

		self.msg += '\r\n'

		if json_body:
			self.msg += 'Content-Length: ' + str(len(json_body.dump()))
			self.msg += '\r\nContent-Type: application/json'
			self.msg += '\r\n\r\n' + json_body.dump()
		else:
			self.msg += 'Content-Length: 0\r\n' \
				    'Content-Type: application/json\r\n\r\n'


	def get(self):
		return self.msg

class ogThread():
	def shellrun(client, request, ogRest):
		if not request.getrun():
			response = restResponse(ogResponses.BAD_REQUEST)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		try:
			shellout = ogRest.operations.shellrun(request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		if request.getEcho():
			json_body = jsonBody()
			json_body.add_element('out', shellout)
			response = restResponse(ogResponses.OK, json_body)
			client.send(response.get())
		else:
			response = restResponse(ogResponses.OK)
			client.send(response.get())

		ogRest.state = ThreadState.IDLE

	def check_vm_state_loop(ogRest):
		POLLING_WAIT_TIME = 12
		while True:
			time.sleep(POLLING_WAIT_TIME)
			state = ogRest.operations.check_vm_state()
			installed_os = ogRest.operations.get_installed_os()
			if state == OgVM.State.STOPPED and \
			   ogRest.state == ThreadState.IDLE and \
			   len(installed_os) > 0:
				ogRest.operations.poweroff_host()

	def poweroff(ogRest):
		time.sleep(2)
		ogRest.operations.poweroff()

	def reboot(ogRest):
		ogRest.operations.reboot()

	def session(client, request, ogRest):
		try:
			ogRest.operations.session(request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		response = restResponse(ogResponses.OK)
		client.send(response.get())
		ogRest.state = ThreadState.IDLE

	def software(client, request, path, ogRest):
		try:
			software = ogRest.operations.software(request, path, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		json_body = jsonBody()
		json_body.add_element('partition', request.getPartition())
		json_body.add_element('software', software)

		response = restResponse(ogResponses.OK, json_body)
		client.send(response.get())
		ogRest.state = ThreadState.IDLE

	def hardware(client, path, ogRest):
		try:
			ogRest.operations.hardware(path, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		json_body = jsonBody()
		with open(path, 'r') as f:
			json_body.add_element('hardware', f.read())

		response = restResponse(ogResponses.OK, json_body)
		client.send(response.get())
		ogRest.state = ThreadState.IDLE

	def setup(client, request, ogRest):
		try:
			out = ogRest.operations.setup(request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		json_body = jsonBody(out)

		response = restResponse(ogResponses.OK, json_body)
		client.send(response.get())
		ogRest.state = ThreadState.IDLE

	def image_restore(client, request, ogRest):
		try:
			ogRest.operations.image_restore(request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		json_body = jsonBody()
		json_body.add_element('disk', request.getDisk())
		json_body.add_element('partition', request.getPartition())
		json_body.add_element('image_id', request.getId())

		response = restResponse(ogResponses.OK, json_body)
		client.send(response.get())
		ogRest.state = ThreadState.IDLE

	def image_create(client, path, request, ogRest):
		try:
			ogRest.operations.image_create(path, request, ogRest)
			software = ogRest.operations.software(request, path, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		json_body = jsonBody()
		json_body.add_element('disk', request.getDisk())
		json_body.add_element('partition', request.getPartition())
		json_body.add_element('code', request.getCode())
		json_body.add_element('id', request.getId())
		json_body.add_element('name', request.getName())
		json_body.add_element('repository', request.getRepo())
		json_body.add_element('software', software)

		response = restResponse(ogResponses.OK, json_body)
		client.send(response.get())
		ogRest.state = ThreadState.IDLE

	def refresh(client, ogRest):
		try:
			out = ogRest.operations.refresh(ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			ogRest.state = ThreadState.IDLE
			return

		json_body = jsonBody(out)

		response = restResponse(ogResponses.OK, json_body)
		client.send(response.get())
		ogRest.state = ThreadState.IDLE

class ogResponses(Enum):
	BAD_REQUEST=0
	IN_PROGRESS=1
	OK=2
	INTERNAL_ERR=3
	UNAUTHORIZED=4
	SERVICE_UNAVAILABLE=5

class ogRest():
	def __init__(self, config):
		self.proc = None
		self.terminated = False
		self.state = ThreadState.IDLE
		self.CONFIG = config
		self.mode = self.CONFIG['opengnsys']['mode']
		self.samba_config = self.CONFIG['samba']

		if self.mode == 'linux':
			self.operations = OgLinuxOperations(self.CONFIG)
		elif self.mode == 'virtual':
			from src.virtual.ogOperations import (OgVM,
				OgVirtualOperations)
			self.operations = OgVirtualOperations()
			threading.Thread(target=ogThread.check_vm_state_loop,
					 args=(self,)).start()
		else:
			raise ValueError('Mode not supported.')

	def process_request(self, request, client):
		method = request.get_method()
		URI = request.get_uri()

		if (not "stop" in URI and
		    not "reboot" in URI and
		    not "poweroff" in URI and
		    not "probe" in URI):
			if self.state == ThreadState.BUSY:
				response = restResponse(ogResponses.SERVICE_UNAVAILABLE)
				client.send(response.get())
				return
			else:
				self.state = ThreadState.BUSY

		if ("GET" in method):
			if "hardware" in URI:
				self.process_hardware(client)
			elif ("run/schedule" in URI):
				self.process_schedule(client)
			elif "refresh" in URI:
				self.process_refresh(client)
			else:
				response = restResponse(ogResponses.BAD_REQUEST)
				client.send(response.get())
		elif ("POST" in method):
			if ("poweroff" in URI):
				self.process_poweroff(client)
			elif "probe" in URI:
				self.process_probe(client)
			elif ("reboot" in URI):
				self.process_reboot(client)
			elif ("shell/run" in URI):
				self.process_shellrun(client, request)
			elif ("session" in URI):
				self.process_session(client, request)
			elif ("software" in URI):
				self.process_software(client, request)
			elif ("setup" in URI):
				self.process_setup(client, request)
			elif ("image/restore" in URI):
				self.process_imagerestore(client, request)
			elif ("stop" in URI):
				self.process_stop(client)
			elif ("image/create" in URI):
				self.process_imagecreate(client, request)
			else:
				response = restResponse(ogResponses.BAD_REQUEST)
				client.send(response.get())
		else:
			response = restResponse(ogResponses.BAD_REQUEST)
			client.send(response.get())

		return 0

	def kill_process(self):
		try:
			os.kill(self.proc.pid, signal.SIGTERM)
		except:
			pass

		time.sleep(2)
		try:
			os.kill(self.proc.pid, signal.SIGKILL)
		except:
			pass

		self.state = ThreadState.IDLE

	def process_reboot(self, client):
		response = restResponse(ogResponses.IN_PROGRESS)
		client.send(response.get())

		if self.mode != 'virtual':
			client.disconnect()
			if self.state == ThreadState.BUSY:
				self.kill_process()

		threading.Thread(target=ogThread.reboot, args=(self,)).start()

	def process_poweroff(self, client):
		response = restResponse(ogResponses.IN_PROGRESS)
		client.send(response.get())

		if self.mode != 'virtual':
			client.disconnect()
			if self.state == ThreadState.BUSY:
				self.kill_process()

		threading.Thread(target=ogThread.poweroff, args=(self,)).start()

	def process_probe(self, client):
		json_body = jsonBody()

		if self.state != ThreadState.BUSY:
			json_body.add_element('status', 'OPG')
			response = restResponse(ogResponses.OK, json_body)
		else:
			json_body.add_element('status', 'BSY')
			response = restResponse(ogResponses.IN_PROGRESS, json_body)

		client.send(response.get())

	def process_shellrun(self, client, request):
		threading.Thread(target=ogThread.shellrun, args=(client, request, self,)).start()

	def process_session(self, client, request):
		threading.Thread(target=ogThread.session, args=(client, request, self,)).start()

	def process_software(self, client, request):
		path = '/tmp/CSft-' + client.ip + '-' + str(request.getPartition())
		threading.Thread(target=ogThread.software, args=(client, request, path, self,)).start()

	def process_hardware(self, client):
		path = '/tmp/Chrd-' + client.ip
		threading.Thread(target=ogThread.hardware, args=(client, path, self,)).start()

	def process_schedule(self, client):
		response = restResponse(ogResponses.OK)
		client.send(response.get())
		self.state = ThreadState.IDLE

	def process_setup(self, client, request):
		threading.Thread(target=ogThread.setup, args=(client, request, self,)).start()

	def process_imagerestore(self, client, request):
		threading.Thread(target=ogThread.image_restore, args=(client, request, self,)).start()

	def process_stop(self, client):
		client.disconnect()
		if self.state == ThreadState.BUSY:
			self.kill_process()
			self.terminated = True

		sys.exit(0)

	def process_imagecreate(self, client, request):
		path = '/tmp/CSft-' + client.ip + '-' + request.getPartition()
		threading.Thread(target=ogThread.image_create, args=(client, path, request, self,)).start()

	def process_refresh(self, client):
		threading.Thread(target=ogThread.refresh, args=(client, self,)).start()
