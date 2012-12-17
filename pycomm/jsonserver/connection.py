#! /usr/bin/env python
#coding=utf-8
MAX_REQUEST_LINE = 8192

class Connection(object):
    def __init__(self, socket, address):
        self.socket = socket
        self.client_address = address
        self.file = self.socket.makefile()
        
    
    def read(self):
        return self.file.read(MAX_REQUEST_LINE)
    
    def readline(self):
        return self.file.readline(MAX_REQUEST_LINE)
    
    def write(self, data):
        self.file.write(data)
        self.file.flush()
        

    def writelines(self, datas):
        self.file.writelines(datas)