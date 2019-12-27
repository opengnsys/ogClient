from src.ogClient import *
from src.ogConfig import *
from signal import signal, SIGPIPE, SIG_DFL

def main():
	signal(SIGPIPE, SIG_DFL)
	ogconfig = ogConfig()
	if (not ogconfig.parserFile('cfg/ogagent.cfg')):
		print ('Error: Parsing configuration file')
		return 0

	ip = ogconfig.getValueSection('opengnsys', 'ip')
	port = ogconfig.getValueSection('opengnsys', 'port')

	client = ogClient(ip, int(port))
	client.connect()
	client.run()

if __name__ == "__main__":
	main()
