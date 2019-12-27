import email
from io import StringIO
import json

class HTTPParser:
	def __init__(self):
		self.requestLine = None
		self.headersAlone = None
		self.headers = None
		self.host = None
		self.contentType = None
		self.contentLen = None
		self.operation = None
		self.URI = None
		self.cmd = None

	def parser(self,data):
		self.requestLine, self.headersAlone = data.split('\n', 1)
		self.headers = email.message_from_file(StringIO(self.headersAlone))

		if 'Host' in self.headers.keys():
			self.host = self.headers['Host']

		if 'Content-Type' in self.headers.keys():
			self.contentType = self.headers['Content-Type']

		if 'Content-Length' in self.headers.keys():
			self.contentLen = int(self.headers['Content-Length'])

		if (not self.requestLine == None or not self.requestLine == ''):
			self.operation = self.requestLine.split('/', 1)[0]
			self.URI = self.requestLine.split('/', 1)[1]

		if not self.contentLen == 0:
			msgs = self.headersAlone.rstrip().split('\n')
			cmd = msgs[len(msgs) - 1]
			try:
				jsoncmd = json.loads(cmd)
			except ValueError as e:
				print ("Error: Json message incomplete")
				return

			if "run" in cmd:
				self.cmd = jsoncmd["run"]

	def getHeaderLine(self):
		return self.headersAlone

	def getRequestLine(self):
		return self.requestLine

	def getHeaderParsed(self):
		return self.headers

	def getHost(self):
		return self.host

	def getContentType(self):
		return self.contentType

	def getContentLen(self):
		return self.contentLen

	def getRequestOP(self):
		return self.operation

	def getURI(self):
		return self.URI

	def getCMD(self):
		return self.cmd
