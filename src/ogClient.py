import errno
import select
import socket
import time

from HTTPParser import *
from ogProcess import *
from enum import Enum

class State(Enum):
	CONNECTING = 0
	RECEIVING = 1

class ogClient:
	def __init__(self, ip, port):
		self.ip = ip
		self.port = port

	def get_socket(self):
		return self.sock

	def get_state(self):
		return self.state

	def connect(self):
		print "connecting"
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(0)
		self.state = State.CONNECTING
		self.data = ""
		self.trailer = False
		self.content_len = 0

		try:
			self.sock.connect((self.ip, self.port))
		except socket.error, err:
			if err.errno == errno.EINPROGRESS:
				return
			elif err.errno == errno.ECONNREFUSED:
				return

			print "Error connect " + str(err)

	def connect2(self):
		try:
			self.sock.connect((self.ip, self.port))
		except socket.error, err:
			if err.errno == errno.EISCONN:
				print "connected"
				self.state = State.RECEIVING
			else:
				print "connection refused, retrying..."
				self.state = State.CONNECTING
				self.sock.close()
				self.connect()

	def receive(self):
		print "receiving"
		try:
			data = self.sock.recv(1024)
		except socket.err, err:
			print "Error3 " + str(err)

		if len(data) == 0:
			self.state = State.CONNECTING
			self.sock.close()
			self.connect()

		self.data = self.data + data
		httpparser = HTTPParser()
		ogprocess = ogProcess()

		if not self.trailer:
			if self.data.find("\r\n") > 0:
				# https://stackoverflow.com/questions/4685217/parse-raw-http-headers
				request_line, headers_alone = self.data.split('\n', 1)
				headers = Message(StringIO(headers_alone))

				if 'content-length' in headers.keys():
					self.content_len = int(headers['content-length'])

				self.trailer = True

		if self.trailer and len(self.data) >= self.content_len:
			httpparser.parser(self.data)
			print httpparser.getRequestOP()
			print httpparser.getURI()
			ogprocess.processOperation(httpparser.getRequestOP(), httpparser.getURI())

			self.sock.send("HTTP/1.0 200 OK\r\n\r\n")

			# Cleanup state information from request
			self.data = ""
			self.content_len = 0
			self.trailer = False
