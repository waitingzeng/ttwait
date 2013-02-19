#!/usr/bin/python
#coding=utf8

import os
import sys
from pycomm.log import log, open_log
from pycomm.proc import ProcPool
import tornado.ioloop
from optparse import OptionParser
from pycomm.log import open_log, open_debug
import tornado.ioloop
import tornado.autoreload
tornado.autoreload.start = lambda:True

from pycomm.utils import autoreload
from pprint import pprint, pformat
from pycomm.log import log, open_log, open_debug
from tornado.options import define, parse_command_line, options

define("logname", type=str, default='',
       help="the log name")
define("port", type=int, default=9000,
       help="the server port")
define("address", type=str, default='127.0.0.1',
       help="the server address")

define("open_debug", type=bool, default=False)
define("autoreload", type=bool, default=False)


def parse_options():
    parse_command_line()
    open_log(options.logname, options.logging)
    if options.open_debug:
        open_debug()
    return options


def run_server(app_server):
    app_server.listen(options.port, options.address)
    log.trace('start debug server %s', options.port)
    tornado.ioloop.IOLoop.instance().start()




def run_django_server():
    from pycomm.log import WSGILogApplication
    import django.core.handlers.wsgi
    handler = django.core.handlers.wsgi.WSGIHandler()
    log_handler = WSGILogApplication(handler)

    wsgi_app = tornado.wsgi.WSGIContainer(log_handler)
    tornado_app = tornado.web.Application(
        [('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
        ])
    app_server = tornado.httpserver.HTTPServer(tornado_app, xheaders=True)
    parse_options()
    
    run_server(app_server)

