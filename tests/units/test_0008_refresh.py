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
import json

class TestRefreshMethods(unittest.TestCase):

    def test_correct_get(self):
        req = 'GET /refresh HTTP/1.0\r\nContent-Length:0\r\n' + \
              'Content-Type:application/json\r\n\r\n'
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

        self.assertIn('partition_setup', response_json)
        self.assertIn('disk', response_json)

        # Check partition_setup parameters.
        for partition in response_json['partition_setup']:
            self.assertIn('filesystem', partition)
            self.assertIn('partition', partition)
            self.assertIn('format', partition)
            self.assertIn('code', partition)
            self.assertIn('size', partition)

if __name__ == '__main__':
    unittest.main()
