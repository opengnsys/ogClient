from server import Server
from client import Client
import unittest

class TestShellRunMethods(unittest.TestCase):

    def test_post_with_echo(self):
        req_json = '{"run":"echo \\"croqueta\\"", "echo":true}'
        response_json = '{"out": "\\"croqueta\\"\\n"}'
        req = 'POST /shell/run HTTP/1.0\r\nContent-Length:'+ \
              str(len(req_json)) + \
              '\r\nContent-Type:application/json\r\n\r\n' + req_json
        resp = 'HTTP/1.0 200 OK\r\nContent-Length:' + \
               str(len(response_json)) + \
               '\r\nContent-Type:application/json\r\n\r\n' + response_json
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
        req = 'POST /shell/run HTTP/1.0\r\nContent-Length:'+ \
              str(len(req_json)) + \
              '\r\nContent-Type:application/json\r\n\r\n' + req_json
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
        s.connect(probe=False)
        s.send('POST /shell/run HTTP/1.0\r\nContent-Length:0\r\n\r\n')
        response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(response, 'HTTP/1.0 400 Bad Request\r\n\r\n')

    def test_malformed_json(self):
        json = '{"wrong_param": 0}'
        len_json = str(len(json))
        msg = 'POST /shell/run HTTP/1.0\r\nContent-Length:' + len_json + \
              '\r\nContent-Type:application/json\r\n\r\n' + json
        c = Client()
        s = Server()
        s.connect(probe=False)
        s.send(msg)
        response = s.recv()
        s.stop()
        c.stop()
        self.assertEqual(response, 'HTTP/1.0 400 Bad Request\r\n\r\n')

if __name__ == '__main__':
    unittest.main()
