from src.ogClient import *
from src.ogConfig import *

CONNECTING = 0
RECEIVING = 1

def main():
	ogconfig = ogConfig()
	if (not ogconfig.parserFile('cfg/ogagent.cfg')):
		print 'Error: Parsing configuration file'
		return 0

	ip = ogconfig.getValueSection('opengnsys', 'ip')
	port = ogconfig.getValueSection('opengnsys', 'port')

	client = ogClient(ip, int(port))
	client.connect()

	while 1:
		sock = client.get_socket()
		state = client.get_state()

		if state == CONNECTING:
			readset = [ sock ]
			writeset = [ sock ]
		else:
			readset = [ sock ]
			writeset = [ ]

		readable, writable, exception = select.select(readset, writeset, [ ])
		if state == CONNECTING and sock in writable:
			client.connect2()
		elif state == RECEIVING and sock in readable:
			client.receive()
		else:
			print "bad state" + str(state)

if __name__ == "__main__":
	main()
