#
# Copyright (C) 2020-2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import socket
import sys

class Server():

    _probe_json = '{"id": 0, "name": "test_local", "center": 0, "room": 0}'
    _probe_msg = 'POST /probe HTTP/1.0\r\nContent-Length: '+ \
                 str(len(_probe_json)) + \
                 '\r\nContent-Type: application/json\r\n\r\n' + _probe_json
    _recv_buffer_size = 16384

    def __init__(self, host='127.0.0.1', port=1234):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self, probe=True):
        try:
            self.sock.bind((self.host, self.port))
        except socket.error as msg:
            print('Bind failed. Error Code : ' + str(msg[0]) + ' Message '
                  + msg[1])
            sys.exit()

        self.sock.listen(10)
        self.conn, self.addr = self.sock.accept()
        if probe:
            self.send(self._probe_msg)
            return self.recv()

    def send(self, msg):
        self.conn.send(msg.encode())

    def recv(self):
        return self.conn.recv(self._recv_buffer_size).decode('utf-8')

    def stop(self):
        self.conn.close()
        self.sock.close()
