#! /usr/bin/env python
#coding=utf-8
import pycomm
import greenlet
from gevent import core
from gevent import select
from gevent import monkey
monkey.patch_all(ssl=False)
from gevent.pywsgi import WSGIServer, WSGIHandler
import gevent

import os
import os.path as osp
import sys
import json
import urllib
import urllib2
import urlparse
import signal
import socket
import time
from datetime import datetime
import traceback
import posixpath
try:
    # The mod_python version is more efficient, so try importing it first.
    from mod_python.util import parse_qsl
except ImportError:
    from urlparse import parse_qsl

from pycomm.utils.procpool import ProcPool
from pycomm.log import log
from pyso import pysk

import mimetypes
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class MMWSGIHandler(WSGIHandler):
    STATIC_FILES = []
    
    @classmethod
    def init_static_urls(cls, static):
        cls.STATIC_FILES = []
        for k, v in static.items():
            k = k.replace('__', '/')
            v = v.replace('$HOME', os.getenv('HOME'))
            cls.STATIC_FILES.append((k, v))

    def log_error(self, msg, *args):
        try:
            message = msg % args
        except Exception, info:
            traceback.print_exc()
            message = '%r %r exception %s' % (msg, args, traceback.format_exc())
        try:
            message = '%s: %s' % (self.socket, message)
        except Exception:
            pass
        try:
            log.error(message)
        except Exception:
            log.exception('')

    def log_request(self):
        log.trace(self.format_request())

    def format_request(self):
        now = datetime.now().replace(microsecond=0)
        if self.time_finish:
            delta = '%.6f' % (self.time_finish - self.time_start)
            length = self.response_length
        else:
            delta = '-'
            if not self.response_length:
                length = '-'
        return '[%s]%s "%s" %s %s %s' % (
            os.getpid(),
            self.client_address[0],
            self.requestline,
            (self.status or '000').split()[0],
            length,
            delta)
    
    def translate_path(self, path, target_path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = target_path
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path
    
    def server_static(self):
        for url, path in self.STATIC_FILES:
            if self.path.startswith(url):
                path = self.translate_path(self.path[len(url):], path)
                log.trace('handle static file %s', path)
                if os.path.exists(path):
                    if os.path.isdir(path):
                        if not self.path.endswith('/'):
                            # redirect browser - doing basically what apache does
                            self.start_response('301  Moved Permanently', (("Location" , self.path + "/")))
                            return True
                        for index in "index.html", "index.htm":
                            index = os.path.join(path, index)
                            if os.path.exists(index):
                                path = index
                                break
                        else:
                            return False
                    ctype = self.guess_type(path)
                    self.result = file(path, 'rb')
                    fs = os.fstat(self.result.fileno())
                    self.start_response('200 OK', (("Content-type", ctype), ("Last-Modified", self.date_time_string(fs.st_mtime))))
                    self.process_result()
                    return True
        return False

    def run_application(self):
        if not self.server_static():
            try:
                return WSGIHandler.run_application(self)
            except Exception, info:
                log.exception("%s had some error")
                raise info
    

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    
    def send_all(self, msg):
        try:
            self.socket.sendall(msg)
        except socket.error, ex:
            self.status = 'socket error: %s' % ex
            if self.code > 0:
                self.code = -self.code
            raise

    def send_headers(self):
        towrite = []
        self.finalize_headers()
        towrite.append('%s %s\r\n' % (self.request_version, self.status))
        for header in self.response_headers:
            towrite.append('%s: %s\r\n' % header)

        towrite.append('\r\n')
        self.headers_sent = True
        msg = ''.join(towrite)
        self.send_all(msg)

                        
    def write(self, data):
        towrite = []
        if not self.status:
            raise AssertionError("The application did not call start_response()")
        if not self.headers_sent:
            self.send_headers()

        if data:
            if self.response_use_chunked:
                ## Write the chunked encoding
                towrite.append("%x\r\n%s\r\n" % (len(data), data))
            else:
                towrite.append(data)

        msg = ''.join(towrite)
        try:
            self.socket.sendall(msg)
        except socket.error, ex:
            self.status = 'socket error: %s' % ex
            if self.code > 0:
                self.code = -self.code
            raise
        self.response_length += len(msg)
    
    def date_time_string(self, timestamp=None):
        """Return the current date and time formatted for a message header."""
        if timestamp is None:
            timestamp = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
        s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
                self.weekdayname[wd],
                day, self.monthname[month], year,
                hh, mm, ss)
        return s

    def process_result(self):
        bodySent = None
        fileWrapper = self.environ.get('wsgi.file_wrapper',None)
        if fileWrapper and isinstance(self.result, file):
            self.response_use_chunked = False
            if 'Content-Length' not in self.response_headers_list:
                self.response_headers_list.append('Content-Length')
                fs = os.fstat(self.result.fileno())
                self.response_headers.append(('Content-Length', fs[6]))
                self.response_headers.append(('Last-Modified', self.date_time_string(fs.st_mtime)))
            self.send_headers()
            bodySent = fileWrapper.sendfile(self.result, self.wfile)
            if bodySent is not None:
                self.response_length += bodySent

        if bodySent is None:
            for data in self.result:
                if data:
                    self.write(data)
            if self.status and not self.headers_sent:
                self.write('')
            if self.response_use_chunked:
                self.send_all('0\r\n\r\n')
                self.response_length += 5

    def get_environ(self):
        env = WSGIHandler.get_environ(self)
        env['REQUEST_URI'] = self.path
        env['SERVER_NAME'] = self.server.address[0]
        env['SERVER_PORT'] = str(self.server.address[1])
        
        for http_header, http_value in self.headers.items():
            env ['HTTP_%s' % http_header.replace('-', '_').upper()] = http_value
        return env
    

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })
    
    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    monthname = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']



class MMWSGIServer(WSGIServer):
    base_env = {'GATEWAY_INTERFACE': 'CGI/1.1',
                'SERVER_SOFTWARE': 'gevent/%d.%d Python/%d.%d MMWSGIServer' % (gevent.version_info[:2] + sys.version_info[:2]),
                'SCRIPT_NAME': '',
                'wsgi.version': (1, 0),
                'wsgi.multithread': False,
                'wsgi.multiprocess': True,
                'wsgi.run_once': False,
                'wsgi.errors' : log,
                }

    def __init__(self, *args, **kwargs):
        self.loop_number = kwargs.pop('loop_number', 0)
        WSGIServer.__init__(self, *args, **kwargs)

        self.runtimes = 0

    def handle(self, socket, address):
        handler = self.handler_class(socket, address, self)
        try:
            handler.handle()
        except Exception, info:
            log.exception("pid %s exception %s", os.getpid(), info)

        if self.loop_number:
            self.runtimes += 1
            if self.runtimes >= self.loop_number:
                log.trace( 'loop %d times, exit, pid: %d' % ( self.loop_number, os.getpid() ) ); 
                os._exit(0)

    def pre_start(self):
        self.init_socket()
        self._stop_event.clear()

class WSGIProcPool(ProcPool):
    def __init__(self, application, conf_file=None):
        ProcPool.__init__(self, conf_file)
        self.application = application
    
    def init(self):
        self.as_daemon = self.conf.General.Daemon == 'true'
        self.gevent_conf = self.conf.gevent
        if self.gevent_conf.pythonpath:
            for path in self.gevent_conf.pythonpath:
                sys.path.insert(0, path)
        
        self.ip = self.gevent_conf.server_ip
        self.port = self.gevent_conf.port

        MMWSGIHandler.init_static_urls(self.conf.static)
    
    def get_server(self):
        if hasattr(self, 'server'):
            return self.server
        self.server = MMWSGIServer((self.ip, self.port), self.application, spawn=self.gevent_conf.spawn, handler_class=MMWSGIHandler, loop_number=self.loop_number)
        self.server.pre_start()
        return self.server

    def _start( self ):
        self.get_server()
        
        ProcPool._start(self)
        
    def test_init(self, options):
        if options.reload:
            self._worker = self.worker
            self.worker = self.reload_worker
        if options.port:
            self.port = options.port
        self.get_server()

    def reload_worker(self):
        from pycomm.utils.autoreload import main
        main(self._worker)
    
    def worker( self ): 
        #self.get_server()
        
        log.trace('worker No.%d(%d) begin running' % ( self.id, os.getpid() ) )
        signal.signal( signal.SIGTERM, self.worker_terminate )

        self.begin_run_worker()
        log.trace('bind ip %s port %s', self.ip, self.port)
        self.server.start_accepting()
        self.server._stop_event.wait()

        self.after_run_worker()
        log.trace( 'loop %d times, exit, pid: %d' % ( self.loop_number, os.getpid() ) ); 

    def add_options(self, parser):
        parser.add_option("-l", '--reload', dest='reload', action="store_true", help="auto reload")
        parser.add_option("-p", '--port', dest='port', type="int", help="the port to listen")
    


    

class FileWrapper(object):
    """
    File Wrapper to perform platform specific file transmission
    """

    def sendfile(self, inputFile, outputSocket):
        """Platform-specific file transmission

        Override this method in subclasses to support platform-specific
        file transmission.  It is only called if the application's
        return iterable ('self.result') is an instance of 'file'.

        This method should return the number of sent bytes or None on failure
        """
        return None   # No platform-specific transmission by default

from errno import EAGAIN
from gevent.socket import wait_write
import os
disable_sendfile = False
try:
    from sendfile import sendfile as original_sendfile
except ImportError:
    disable_sendfile = True

class SendFileWrapper(FileWrapper):
    
    def sendfile(self, inputFile, outputSocket):
        if disable_sendfile:
            # we cannot use sendfile on this platform
            return False

        output = outputSocket.fileno()
        input = inputFile.fileno()
        count = os.fstat(input)[6]
        offset = 0
        total_sent = 0
        while total_sent < count:
            try:
                _offset, sent = original_sendfile(output, input, offset + total_sent, count - total_sent)
                total_sent += sent
            except OSError, ex:
                if ex[0] == EAGAIN:
                    wait_write(output)
                else:
                    raise
        return total_sent


