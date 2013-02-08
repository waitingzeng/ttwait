#!/usr/bin/env python
#
# Simple asynchronous HTTP proxy with tunnelling (CONNECT).
#
# GET/POST proxying based on
# http://groups.google.com/group/python-tornado/msg/7bea08e7a049cf26
#
# Copyright (C) 2012 Senko Rasic <senko.rasic@dobarkod.hr>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import socket

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.auth
import tornado.httpclient
from optparse import OptionParser
from pycomm.log import log, open_log, open_debug


__all__ = ['ProxyHandler', 'run_proxy']


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        if not self.application.auth:
            return True
        user = self.get_secure_cookie('user')
        if user and user in self.application.auth:
            return user
        else:
            return None


class LoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, 'Google auth failed')
        if user['email'] not in self.application.auth:
            raise tornado.web.HTTPError(404, "Access denied to '{email}'. "
                                        "Please use another account or ask your admin to "
                                        "add your email to proxy handler --auth".format(**user))

        self.set_secure_cookie("user", str(user['email']))
        self.redirect(self.get_argument('next', '/'))


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        return 'Successfully logged out!'


class ProxyHandler(BaseHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT']

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        log.trace("%s %s", self.request.method, self.request.uri)

        def handle_response(response):
            if response.error and not isinstance(response.error,
                                                 tornado.httpclient.HTTPError):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
                self.finish()
            else:
                self.set_status(response.code)
                for header in ('Date', 'Cache-Control', 'Server',
                               'Content-Type', 'Location', 'Set-Cookie'):
                    v = response.headers.get(header)
                    if v:
                        self.set_header(header, v)
                if response.body:
                    self.write(response.body)
                self.finish()

        req = tornado.httpclient.HTTPRequest(url=self.application.proxypass + self.request.uri,
                                             method=self.request.method, body=self.request.body,
                                             headers=self.request.headers, follow_redirects=False,
                                             allow_nonstandard_methods=True)

        client = tornado.httpclient.AsyncHTTPClient()
        try:
            client.fetch(req, handle_response)
        except tornado.httpclient.HTTPError, e:
            if hasattr(e, 'response') and e.response:
                self.handle_response(e.response)
            else:
                self.set_status(500)
                self.write('Internal server error:\n' + str(e))
                self.finish()

    @tornado.web.asynchronous
    def post(self):
        return self.get()

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def connect(self):
        host, port = self.request.uri.split(':')
        client = self.request.connection.stream

        def read_from_client(data):
            upstream.write(data)

        def read_from_upstream(data):
            client.write(data)

        def client_close(_dummy):
            upstream.close()

        def upstream_close(_dummy):
            client.close()

        def start_tunnel():
            client.read_until_close(client_close, read_from_client)
            upstream.read_until_close(upstream_close, read_from_upstream)
            client.write('HTTP/1.0 200 Connection established\r\n\r\n')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)
        upstream.connect((host, int(port)), start_tunnel)


handlers = [
    (r"/login", LoginHandler),
    (r"/logout", LogoutHandler),
    (r'.*', ProxyHandler),
]


class ProxyApplication(tornado.web.Application):
    def __init__(self, auth=None, proxypass=None, io_loop=None, **kwargs):
        kwargs.update(handlers=handlers)

        super(ProxyApplication, self).__init__(**kwargs)
        self.io_loop = io_loop or tornado.ioloop.IOLoop.instance()
        self.auth = auth or []
        self.proxypass = proxypass

    def start(self, port, address=''):
        self.listen(port, address=address)
        self.io_loop.start()

import base64
import uuid


def gen_cookie_secret():
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)

APP_SETTINGS = dict(
    cookie_secret=gen_cookie_secret(),
    login_url='/login',
)


def run_proxy(**kwargs):
    parser = OptionParser(conflict_handler='resolve')
    parser.add_option('-p', '--port', dest='port', action="store", help="the listen port", type='int')
    parser.add_option('--logname', dest='logname', action="store", help="the log name", type='string')
    parser.add_option('--loglevel', dest='loglevel', action="store", help="the log level", type='int')
    parser.add_option('-d', '--debug', dest='debug', action="store_true", help="run in debug mode")
    parser.add_option('--auth', dest='auth', action="store", help="the email to google openid auth", type="string")
    parser.add_option('--proxypass', dest='proxypass', action="store", help="the host to proxy", type="string")

    options, args = parser.parse_args(sys.argv[1:])

    if not options.logname:
        options.logname = 'webproxy'

    if not options.loglevel:
        options.loglevel = 40

    if not options.auth:
        print 'need auth '
        parser.print_help()
        return

    if not options.proxypass:
        print 'need host to proxypass'
        parser.print_help()
        return

    auth = options.auth.split(',')

    open_log(options.logname, options.loglevel)
    open_debug()
    if options.debug:
        APP_SETTINGS['debug'] = True
    APP_SETTINGS.update(kwargs)
    log.trace("start server on %s proxypass %s", options.port, options.proxypass)
    app = ProxyApplication(auth, options.proxypass, **APP_SETTINGS)
    app.start(options.port)


if __name__ == '__main__':
    run_proxy()
