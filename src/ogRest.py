from enum import Enum

class ogResponses(Enum):
	BAD_REQUEST=0
	IN_PROGRESS=1
	OK=2

def getResponse(response):
	if response == ogResponses.BAD_REQUEST:
		return 'HTTP/1.0 400 Bad request\r\n\r\n'
	if response == ogResponses.IN_PROGRESS:
		return 'HTTP/1.0 202 Accepted\r\n\r\n'
	if response == ogResponses.OK:
		return 'HTTP/1.0 200 OK\r\n\r\n'
