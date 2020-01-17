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

class TestOtherRequests(unittest.TestCase):

    def test_non_existent_function(self):
        post_req = 'POST /this_function_does_not_exist HTTP/1.0\r\n' + \
                   'Content-Length:0\r\nContent-Type:application/json\r\n\r\n'
        get_req = 'GET /this_function_does_not_exist HTTP/1.0\r\n' + \
                  'Content-Length:0\r\nContent-Type:application/json\r\n\r\n'
        c = Client()
        s = Server()
        s.connect()
        s.send(post_req)
        post_response = s.recv()
        s.send(get_req)
        get_response = s.recv()
        s.stop()
        c.stop()
        self.assertRegex(post_response, '^HTTP/1.0 400 Bad Request\r\n*')
        self.assertRegex(get_response, '^HTTP/1.0 400 Bad Request\r\n*')

if __name__ == '__main__':
    unittest.main()
