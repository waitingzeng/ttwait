#!/usr/bin/python
# coding: utf-8
from .rpc import Application, RequestHandler
from pycomm.log import log
import inspect
import sys
import linecache
import re

class MagicApplication(Application):
    def __init__(self, server, request_callback):
        self.server = server
        Application.__init__(self, MagicHandler)


class MagicHandler(RequestHandler):
    def deal(self):
        if self.request.func == 'get_schema':
            fn = self.get_schema
        else:
            try:
                fn = getattr(self.request.connection.application.server, self.request.func)
            except AttributeError:
                fn = None
        if fn is not None:
            try:
                resp = fn(self, *self.request.args, **self.request.kwargs)
                
                self.appendarg('OK')
                self.appendarg(resp)
            except Exception, info:
                log.exception('%s call exception', self.request.func)
                self.appendarg('ERR')
                self.appendarg(str(info))
        else:
            self.appendarg('ERR')
            self.appendarg('No such method on server')

    def get_schema(self, handle):
        server = self.request.connection.application.server
        func = []
        for k in dir(server):
            v = getattr(server, k)
            if not callable(v):
                continue
            if str(v).find('bound method') == -1:
                continue
            if v.__name__.startswith('_'):
                continue
            code = inspect.getsourcelines(v)
            def_code = code[0][0]
            if def_code.find('handler') == -1:
                continue
            def_code = def_code.strip()[4:-1]
            def_code = re.sub('self\s*,\shandler\s*,\s*', '', def_code)
            code = '%s\n%s' % (def_code, v.im_func.func_doc and v.im_func.func_doc.strip() or '')
            func.append(code.strip())
        return func

class MagicServer(object):
    def __init__(self, port, address=''):
        self.app = MagicApplication(self, MagicHandler)
        self.app.listen(port)

    def start(self):
        self.app.start()
