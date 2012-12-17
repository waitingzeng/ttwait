#!/usr/bin/python
# coding: utf-8
try:
    import ujson as json
except ImportError:
    import json

import collections
from pycomm.utils.ioloop.ioloop import IOLoop
from pycomm.utils.ioloop.iostream import IOStream
import socket
import time


# exceptions for Client
class ClientError(Exception):
    pass


class TimeoutError(Exception):
    pass


class NetworkError(Exception):
    pass


class ProtocolError(Exception):
    pass


class STPRequest(object):
    def __init__(self, args=None, connect_timeout=None, request_timeout=None):
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        if args is None:
            self._argv = []
        elif isinstance(args, tuple):
            self._argv = list(args)
        elif isinstance(args, list):
            self._argv = args
        else:
            self._argv = [args]

    def __len__(self):
        return len(self._argv)

    def serialize(self):
        buf = json.dumps(self._argv)
        buf = '%d\r\n%s\r\n' % (len(buf), buf)
        buf += '\r\n'
        return buf


class STPResponse(object):
    def __init__(self, request_time=None, error=None):
        self.request_time = request_time
        self.error = error
        self._argv = []

    @property
    def argv(self):
        return self._argv

    def __len__(self):
        return len(self._argv)

    def rethrow(self):
        """If there was an error on the request, raise an `MagicError`."""
        if self.error:
            raise self.error


class LazySTPResponse(object):
    def __init__(self, io_loop):
        self._io_loop = io_loop
        self._response = None

    def __call__(self, resp):
        self._response = resp
        self._io_loop.stop()

    @property
    def response(self):
        while self._response is None:
            self._io_loop.start()
        self._response.rethrow()
        return self._response


class Connection(object):
    # Constants for connection state
    _CLOSED = 0x001
    _CONNECTING = 0x002
    _STREAMING = 0x004

    def __init__(self, io_loop, client, timeout=-1, connect_timeout=-1, max_buffer_size=104857600):
        self.io_loop = io_loop
        self.client = client
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.start_time = time.time()
        self.stream = None
        self._timeoutevent = None
        self._callback = None
        self._request_queue = collections.deque()
        self._request = None
        self._response = STPResponse()
        self._state = Connection._CLOSED

    @property
    def closed(self):
        return self._state == Connection._CLOSED

    def close(self):
        if self.stream is not None and not self.stream.closed():
            self.stream.close()
        self.stream = None

    def _connect(self):
        self._state = Connection._CONNECTING
        af = socket.AF_INET if self.client.unix_socket is None else socket.AF_UNIX
        self.stream = IOStream(socket.socket(af, socket.SOCK_STREAM),
                                io_loop=self.io_loop,
                                max_buffer_size=self.client.max_buffer_size)
        if self.connect_timeout is not None and self.connect_timeout > 0:
            self._timeoutevent = self.io_loop.add_timeout(time.time() + self.connect_timeout,
                                                            self._on_timeout)
        self.stream.set_close_callback(self._on_close)
        addr = self.client.unix_socket if self.client.unix_socket is not None else (self.client.host, self.client.port)
        self.stream.connect(addr, self._on_connect)

    def _on_connect(self):
        if self._timeoutevent is not None:
            self.io_loop.remove_timeout(self._timeoutevent)
            self._timeoutevent = None
        self._state = Connection._STREAMING
        self._send_request()

    def _on_timeout(self):
        self._timeoutevent = None
        self._run_callback(STPResponse(request_time=time.time() - self.start_time,
                                        error=TimeoutError('Timeout')))
        if self.stream is not None:
            self.stream.close()
        self.stream = None
        self._state = Connection._CLOSED
        self._request = None
        if len(self._request_queue) > 0:
            self._connect_and_send_request()

    def _on_close(self):
        self._run_callback(STPResponse(request_time=time.time() - self.start_time,
                                        error=NetworkError('Connection error')))
        self._state = Connection._CLOSED
        self._request = None
        if len(self._request_queue) > 0:
            self._connect_and_send_request()

    def send_request(self, request, callback):
        self._request_queue.append((request, callback))
        self._connect_and_send_request()

    def _connect_and_send_request(self):
        if len(self._request_queue) > 0 and self._request is None:
            self._request, self._callback = self._request_queue.popleft()
            if self.stream is None or self._state == Connection._CLOSED:
                self._connect()
            elif self._state == Connection._STREAMING:
                self._send_request()

    def _send_request(self):
        def write_callback():
            pass
        timeout = self.timeout
        if self._request.request_timeout is not None:
            timeout = self._request.request_timeout
        if timeout is not None and timeout > 0:
            self._timeoutevent = self.io_loop.add_timeout(time.time() + timeout, self._on_timeout)
        self.start_time = time.time()
        self.stream.write(self._request.serialize(), write_callback)
        self._read_arg()

    def _run_callback(self, response):
        if self._callback is not None:
            callback = self._callback
            self._callback = None
            callback(response)

    def _read_arg(self):
        self.stream.read_until(b'\r\n', self._on_arglen)

    def _on_arglen(self, data):
        if data == '\r\n':
            response = self._response
            self._response = STPResponse()
            response.request_time = time.time() - self.start_time
            if self._timeoutevent is not None:
                self.io_loop.remove_timeout(self._timeoutevent)
            self._run_callback(response)
            self._request = None
            self._connect_and_send_request()
        else:
            try:
                arglen = int(data[:-2])
                self.stream.read_bytes(arglen, self._on_arg)
            except Exception as e:
                self._run_callback(STPResponse(request_time=time.time() - self.start_time,
                                                error=ProtocolError(str(e))))

    def _on_arg(self, data):
        self._response._argv = json.loads(data)
        self.stream.read_until(b'\r\n', self._on_strip_arg_eol)

    def _on_strip_arg_eol(self, data):
        self._read_arg()


class AsyncClient(object):
    def __init__(self, host, port, unix_socket=None, io_loop=None, timeout=-1, connect_timeout=-1, max_buffer_size=104857600):
        self.host = host
        self.port = port
        self.unix_socket = unix_socket
        self.io_loop = io_loop or IOLoop.instance()
        self.max_buffer_size = max_buffer_size
        self.connection = Connection(self.io_loop, self, timeout, connect_timeout, self.max_buffer_size)

    @property
    def closed(self):
        return self.connection.closed

    def close(self):
        self.connection.close()

    def _prepare_request(self, request):
        if not isinstance(request, STPRequest):
            if isinstance(request, list) or isinstance(request, tuple):
                request = STPRequest(list(request))
            else:
                request = STPRequest([request])
        return request

    def lazy_call(self, request):
        request = self._prepare_request(request)
        lresp = LazySTPResponse(self.io_loop)
        self.connection.send_request(request, lresp)
        return lresp

    def call(self, request, callback):
        request = self._prepare_request(request)
        self.connection.send_request(request, callback)

    def __str__(self):
        return '%s:%d' % (self.host, self.port) if self.unix_socket is None else self.unix_socket

    def start(self):
        return IOLoop.instance().start()


class Client(object):
    def __init__(self, host, port, timeout=None, connect_timeout=-1, unix_socket=None, max_buffer_size=104857600):
        self._io_loop = IOLoop()
        self._async_client = AsyncClient(host, port, unix_socket, self._io_loop, timeout, connect_timeout, max_buffer_size)
        self._response = None
        self._closed = False

    def __del__(self):
        self.close()

    @property
    def closed(self):
        return self._async_client.closed

    def close(self):
        if not self._closed:
            self._async_client.close()
            self._io_loop.close()
            self._closed = True

    def call(self, request):
        def callback(response):
            self._response = response
            self._io_loop.stop()
        self._async_client.call(request, callback)
        self._io_loop.start()
        response = self._response
        self._response = None
        response.rethrow()
        return response

    def __str__(self):
        return str(self._async_client)

    def start(self):
        return IOLoop.instance().start()
