import subprocess
import os

class Client():

    def __init__(self):
        self.null = open(os.devnull, 'wb')
        self.proc = subprocess.Popen(['python3', 'main.py'],
                                     cwd='../',
                                     stdout=self.null,
                                     stderr=self.null)

    def stop(self):
        self.proc.terminate()
        self.proc.kill()
        self.proc.wait()
        self.null.close()
