#!/usr/bin/python
# coding: utf-8
try:
    import ujson as json
except ImportError:
    import json
from pycomm.log import log
from .server import STPServer
from tornado.ioloop import IOLoop
from pycomm.utils.ioloop import ioloop

class Application(object):
    RUN_TIMES = 0
    def __init__(self, request_handler=None):
        self.request_handler = request_handler

    def listen(self, port, address='', **kwargs):
        server = STPServer(self, application=self, **kwargs)
        self.address = (address, port)
        server.listen(port, address)

    def __call__(self, request):
        if self.request_handler is not None:
            log.info('begin handler %s runtimes %d', request, Application.RUN_TIMES)
            handler = self.request_handler(self, request)
            handler.deal()
            handler.finish()
            log.info('end handler %s resp %s size %s runtimes %d', request, handler.resp[0], len(handler.resp), Application.RUN_TIMES)
            Application.RUN_TIMES += 1

    def start(self):
        log.trace('start server %s', self.address)
        ioloop.IOLoop.instance().start()

class RequestHandler(object):
    def __init__(self, application, request, **kwargs):
        self.application = application
        self.request = request
        self.resp = []

    def appendarg(self, arg):
        self.resp.append(arg)

    addarg = appendarg

    def finish(self):
        data = json.dumps(self.resp)
        self.request.connection.stream.write('%d\r\n%s\r\n' % (len(data), data))

        self.request.connection.stream.write('\r\n')
