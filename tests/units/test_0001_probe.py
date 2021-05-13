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

class TestProbeMethods(unittest.TestCase):

    def setUp(self):
        self.ok_response = 'HTTP/1.0 200 OK\r\nContent-Length: 17\r\n' \
                           'Content-Type: application/json\r\n\r\n' + \
                           '{"status": "OPG"}'

    def test_post(self):
        c = Client()
        s = Server()
        server_response = s.connect()
        s.stop()
        c.stop()
        self.assertEqual(server_response, self.ok_response)

    def test_no_json(self):
        c = Client()
        s = Server()
        s.connect(probe=False)
        s.send('POST /probe HTTP/1.0\r\nContent-Length: 0\r\n\r\n')
        response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(response, 'HTTP/1.0 400 Bad Request\r\n\r\n')

    def test_malformed_json(self):
        json = '{"id": 0, "name": "test_local", "center": 0}'
        len_json = str(len(json))
        msg = 'POST /probe HTTP/1.0\r\nContent-Length: ' + len_json + \
              '\r\nContent-Type: application/json\r\n\r\n' + json
        c = Client()
        s = Server()
        s.connect(probe=False)
        s.send(msg)
        response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(response, 'HTTP/1.0 400 Bad Request\r\n\r\n')

    def test_multiple_probes(self):
        c = Client()
        s = Server()
        s.connect(probe=False)
        s.send(s._probe_msg)
        s.send(s._probe_msg)
        server_response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(server_response, self.ok_response)

    def test_extra_parameter_json(self):
        json = '{"id": 0, "name": "test_local", "center": 0, "room": 0, ' + \
               '"extra_param": true}'
        len_json = str(len(json))
        msg = 'POST /probe HTTP/1.0\r\nContent-Length: ' + len_json + \
              '\r\nContent-Type: application/json\r\n\r\n' + json
        c = Client()
        s = Server()
        s.connect(probe=False)
        s.send(msg)
        response = s.recv()
        s.stop()
        c.stop()
        self.assertRegex(response, '^HTTP/1.0 200 OK\r\n*')

if __name__ == '__main__':
    unittest.main()
