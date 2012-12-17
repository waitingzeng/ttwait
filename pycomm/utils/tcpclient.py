#!/usr/bin/env python
# -*- coding:utf-8 -*-

#from gevent import socket
import socket
import logging
import time
import json

class TCPClient(object):
    def __init__(self, recv_callback=None, end_char="\r\n", max_buffer_size=8196, timeout=3):
        self._recv_callback = recv_callback
        self._end_char = end_char
        self._timeout = timeout
        self._max_buffer_size = max_buffer_size
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self._socket.settimeout(self._timeout)
        self._fileno = self._socket.fileno()
        #self._buffer = ""
        self._connected = False
        self.read_buffer = ""
        
    def set_callback(self, callback):
        self._recv_callback = callback

    def connect(self, host, port):
        assert self._connected == False
        self.host, self.port = host, port
        self._socket.connect((self.host, self.port))
        self._connected = True

    def send(self, send_data, add_endchar=True, callback=None):
        if isinstance(send_data, dict):
            send_data = json.dumps(send_data)          
        if add_endchar:
            send_data += self._end_char
        send_data = _utf8(send_data)
        #print "TCPClient sending data:", send_data
        self._socket.send(send_data)
        

    def close(self):
        assert self._connected
        self._socket.close()
        self._connected = False
        
    def recv(self):
        response = []
        while True:
            self.read_buffer += self._socket.recv(self._max_buffer_size)   
            while True:
                loc =  self.read_buffer.find(self._end_char)
                if loc != -1:
                    dec = self._consume(loc+len(self._end_char), len(self._end_char))
                    response.append(dec)
                else:
                    break
            if len(response) != 0:
                return response
    
    def _consume(self, loc, delimiter_len=None):
        result = self.read_buffer[:loc]
        self.read_buffer = self.read_buffer[loc:]
        if delimiter_len:
            return result[:loc-delimiter_len]
        else:
            return result      

def _utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    assert isinstance(s, str)
    return s        
