#! /usr/bin/env python
#coding=utf-8
from gevent import monkey
monkey.patch_all()
import threading
import time
import sys
import traceback
from datetime import datetime
import errno

from connection import Connection
import json
from pycomm.utils.storage import Storage
from pycomm.log import log

from gevent import socket
import gevent
from gevent.pool import Pool
from gevent.server import StreamServer
from gevent.hub import GreenletExit



__all__ = ['JsonHandler', 'JsonServer']


MAB_BUFFER_SIZE = 8196


_INTERNAL_ERROR_CODE = '500'
_INTERNAL_ERROR_BODY = '500 Internal Server Error'
_INTERNAL_ERROR = {'info' : _INTERNAL_ERROR_BODY, 'code' : _INTERNAL_ERROR_CODE, 'path' : ''}

_REQUEST_TOO_LONG_RESPONSE = {'path' : '', 'info' : '414 Request URI Too Long', 'code' : '414'}
_BAD_REQUEST_RESPONSE = {'path' : '', 'info' : 'Bad Request Response', 'code' : '400'}
_NOT_HANDLE_FOUND = {'path' : '', 'info' : 'Not Handle Found', 'code' : '404'}


class JsonRequest(object):
    def __init__(self, data, conn):
        self.conn = conn
        self.raw_data = data
        

class JsonHandler(object):
    protocol_version = '0.1'
    end_char = '\r\n\r\n'
    
    def __init__(self, conn, app):
        self.conn = conn
        self.app = app
        self.request = None
        self.read_buffer = ''

    def handle(self):
        try:
            while True:
                self.time_start = time.time()
                self.time_finish = 0
                result = self.handle_one_request()
                if result is None:
                    break
                if result is True:
                    continue
                self.response = result
                self.write()
                if self.time_finish == 0:
                    self.time_finish = time.time()
                self.log_request()
                break
        finally:
            self.__dict__.pop('socket', None)
            self.__dict__.pop('rfile', None)
            self.__dict__.pop('wfile', None)

    def log_error(self, msg, *args):
        try:
            message = msg % args
        except Exception:
            traceback.print_exc()
            message = '%r %r' % (msg, args)
            sys.exc_clear()
        try:
            message = '%s: %s' % (self.socket, message)
        except Exception:
            sys.exc_clear()
        try:
            log.write(message + '\n')
        except Exception:
            traceback.print_exc()
            sys.exc_clear()

    def read_request(self):
        request = []
        while True:
            line = self.conn.readline()
            if not line:
                log.trace('%s disconnect', self.conn.client_address)
                break
            if line == '\r\n':
                dec = self.read_buffer
                self.read_buffer = ''
                return dec[:-2]
            self.read_buffer += line
    

    def handle_one_request(self):
        raw_request = self.read_request()
        if not raw_request:
            return
        try:
            self.request = JsonRequest(raw_request, self.conn)
        except Exception, ex:
            traceback.print_exc()
            self.log_error('Invalid request: %s', str(ex) or ex.__class__.__name__)
            return _BAD_REQUEST_RESPONSE
        
        try:
            return self.handle_one_response()
        except socket.error, ex:
            # Broken pipe, connection reset by peer
            if ex[0] in (errno.EPIPE, errno.ECONNRESET):
                sys.exc_clear()
            else:
                raise

        return True # read more requests

    def write(self):
        towrite = [self.response]
        towrite.append('\r\n\r\n')
        self.conn.write(''.join(towrite))
    
    def log_request(self):
        log.trace(self.format_request())
    
    def format_request(self):
        now = datetime.now().replace(microsecond=0)
        return '%s - - [%s] "%s" %.6f' % (
            self.conn.client_address[0],
            now,
            self.request.raw_data,
            self.time_finish - self.time_start)

    def handle_one_response(self):
        self.time_start = time.time()
        try:
            result = self.app.handle(self.request)
            self.response = result
            self.write()
            if self.time_finish == 0:
                self.time_finish = time.time()
            self.log_request()
            return True
        except Exception, info:
            log.exception('handle fail')
            result = ''
        return result


class JsonApp(object):
    """A Json server based on :class:`StreamServer` ."""

    handler_class = JsonHandler
    
    def __init__(self, handler_class=None):
        if handler_class is not None:
            self.handler_class = handler_class
            
    
    def run(self, host, port):
        pool = Pool(10000) # do not accept more than 10000 connections
        server = StreamServer((host, port), self, spawn=pool)
        server.serve_forever()
        
        
    def __call__(self, socket, address):
        conn = Connection(socket, address)
        log.trace('get new conn %s', address)
        handler = self.handler_class(conn, self)
        handler.handle()

    def handle(self, request):
        return ''
    
