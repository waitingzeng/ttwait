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


class Application(ProcPool):
    def __init__(self, app_server):
        self.server = app_server

    def init(self):
        self.port = self.conf.port or 8000
        self.server_num = self.worker_num
        self.worker_num = 1

    def work(self, name, id):
        log.trace('start server port %s', self.port)
        self.server.bind(self.port)
        self.server.start(num_processes=self.server_num)
        self.append_pids_file()
        tornado.ioloop.IOLoop.instance().start()




def run_server(app_server):
    parser = OptionParser(conflict_handler='resolve')
    parser.add_option('-p', '--port', dest='port', action="store", help="the listen port", type='int')
    parser.add_option('--address', dest='address', action="store", help="the listen address", type='string')
    parser.add_option('--worker_num', dest='worker_num', action="store", help="the thread num", type='int')
    parser.add_option('--logname', dest='logname', action="store", help="the log name", type='string')
    parser.add_option('--loglevel', dest='loglevel', action="store", help="the log level", type='int')
    options, args = parser.parse_args(sys.argv[1:])
    if not options.worker_num:
        options.worker_num = 1

    if not options.logname:
        options.logname = 'web'

    if not options.address:
        options.address = '127.0.0.1'

    if not options.loglevel:
        options.loglevel = 10

    open_log(options.logname, options.loglevel)
    open_debug()

    log.trace('start server port %s', options.port)
    app_server.bind('%s' % options.port, options.address)
    app_server.start(num_processes=options.worker_num)
    tornado.ioloop.IOLoop.instance().start()

