#! /usr/bin/env python
#coding=utf-8
from tcpclient import TCPClient

cli = TCPClient(None)
cli.connect('127.0.0.1', 8888)
cli.send({'path' : '/index/'})
res = cli.recv()
print res

