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

class TestShellRunMethods(unittest.TestCase):

    def test_post_with_echo(self):
        req_json = '{"run":"echo \\"croqueta\\"", "echo":true}'
        response_json = '{"out": \"croqueta\\n\"}'
        req = 'POST /shell/run HTTP/1.0\r\nContent-Length: '+ \
              str(len(req_json)) + \
              '\r\nContent-Type: application/json\r\n\r\n' + req_json
        resp = 'HTTP/1.0 200 OK\r\nContent-Length: ' + \
               str(len(response_json)) + \
               '\r\nContent-Type: application/json\r\n\r\n' + response_json
        c = Client()
        s = Server()
        s.connect()
        s.send(req)
        server_response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(server_response, resp)

    def test_post_without_echo(self):
        req_json = '{"run":"echo 1", "echo":false}'
        req = 'POST /shell/run HTTP/1.0\r\nContent-Length: '+ \
              str(len(req_json)) + \
              '\r\nContent-Type: application/json\r\n\r\n' + req_json
        resp = 'HTTP/1.0 200 OK\r\n\r\n'
        c = Client()
        s = Server()
        s.connect()
        s.send(req)
        server_response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(server_response, resp)

    def test_no_json(self):
        c = Client()
        s = Server()
        s.connect()
        s.send('POST /shell/run HTTP/1.0\r\nContent-Length: 0\r\n\r\n')
        response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(response, 'HTTP/1.0 400 Bad Request\r\n\r\n')

    def test_malformed_json(self):
        json = '{"wrong_param": 0}'
        len_json = str(len(json))
        msg = 'POST /shell/run HTTP/1.0\r\nContent-Length: ' + len_json + \
              '\r\nContent-Type: application/json\r\n\r\n' + json
        c = Client()
        s = Server()
        s.connect()
        s.send(msg)
        response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(response, 'HTTP/1.0 400 Bad Request\r\n\r\n')

    def test_serial_requests(self):
        req1_json = '{"run":"echo 1", "echo":true}'
        req1 = 'POST /shell/run HTTP/1.0\r\nContent-Length: '+ \
               str(len(req1_json)) + \
               '\r\nContent-Type: application/json\r\n\r\n' + req1_json
        req2_json = '{"run":"echo 2", "echo":true}'
        req2 = 'POST /shell/run HTTP/1.0\r\nContent-Length: '+ \
               str(len(req2_json)) + \
               '\r\nContent-Type: application/json\r\n\r\n' + req2_json
        response_json = '{"out": "2\n"}'
        resp = 'HTTP/1.0 200 OK\r\nContent-Length: ' + \
               str(len(response_json)) + \
               '\r\nContent-Type: application/json\r\n\r\n' + response_json
        c = Client()
        s = Server()
        s.connect()
        s.send(req1)
        s.send(req2)
        client_response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(client_response, client_response)

if __name__ == '__main__':
    unittest.main()
