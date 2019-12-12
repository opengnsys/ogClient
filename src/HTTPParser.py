from mimetools import Message
from StringIO import StringIO

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

	def parser(self,data):
		self.requestLine, self.headersAlone = data.split('\n', 1)
		self.headers = Message(StringIO(self.headersAlone))

		if 'host' in self.headers.keys():
			self.host = self.headers['host']

		if 'content-type' in self.headers.keys():
			self.contentType = self.headers['content-type']

		if 'content-length' in self.headers.keys():
			self.contentLen = int(self.headers['content-length'])

		if (not self.requestLine == None or not self.requestLine == ''):
			self.operation = self.requestLine.split('/', 1)[0]
			self.URI = self.requestLine.split('/', 1)[1]

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
