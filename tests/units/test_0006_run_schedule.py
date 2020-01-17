#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

from server import Server
from client import Client
import unittest

class TestRunScheduleMethods(unittest.TestCase):

    def test_get(self):
        req = 'GET /run/schedule HTTP/1.0\r\nContent-Length:0'+ \
              '\r\nContent-Type:application/json\r\n\r\n'
        c = Client()
        s = Server()
        s.connect()
        s.send(req)
        client_response = s.recv()
        s.stop()
        c.stop()
        self.assertRegex(client_response, '^HTTP/1.0 200 OK\r\n*')

if __name__ == '__main__':
    unittest.main()
