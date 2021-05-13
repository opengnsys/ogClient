#
# Copyright (C) 2020-2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from server import Server
from client import Client
import unittest
import json

class TestHardwareMethods(unittest.TestCase):

    def test_get(self):
        req = 'GET /hardware HTTP/1.0\r\nContent-Length: 0\r\n' + \
              'Content-Type: application/json\r\n\r\n '
        c = Client()
        s = Server()
        s.connect()
        s.send(req)
        client_response = s.recv()
        s.stop()
        c.stop()
        self.assertRegex(client_response, '^HTTP/1.0 200 OK\r\n*')
        client_response = client_response.split('\r\n\r\n')
        response_json = json.loads(client_response[1])
        self.assertIn('hardware', response_json)

if __name__ == '__main__':
    unittest.main()
