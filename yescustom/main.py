#!/usr/bin/python
#coding=utf8
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "custom.settings"

DEBUG = False
if os.getenv('CUSTOMDEV'):
    DEBUG = True

import sys
import socket
import urllib
import urlparse
from hashlib import md5

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.auth
import tornado.httpclient
from optparse import OptionParser
from pycomm.log import log, open_log, open_debug
from pyquery import PyQuery as pq
from custom.order.models import UserProfile, UserOrder
from pycomm.utils.cache import SimpleFileBasedCache


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        try:
            profile_id = self.get_secure_cookie('profile_id', max_age_days=31 * 1000)
            return UserProfile.objects.get(pk=int(profile_id))
        except:
            pass
        return None



file_cache = {} #SimpleFileBasedCache('cache')
target_doamin = 'www.customdropshipping.com'
if DEBUG:
    my_domain = 'custom.ttwait.com'
else:
    my_domain = 'www.customdiydropshipping.com'

class ProxyHandler(BaseHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT']
    cache = False

    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        log.trace("%s %s", self.request.method, self.request.uri)

        def handle_response(response):
            if response.error and not isinstance(response.error,
                                                 tornado.httpclient.HTTPError):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
                self.finish()
            else:
                code, headers, body = self._process_response(response)

                self.set_status(code)
                for header in ('Date', 'Cache-Control', 'Server',
                               'Content-Type', 'Location', 'Set-Cookie'):
                    v = headers.get(header)
                    if v:
                        self.set_header(header, v)
                if body:
                    self.write(body)
                self.finish()

        headers, uri, body = self.process_request(self.request)

        url = self.application.proxypass + uri
        req = tornado.httpclient.HTTPRequest(url=url,
                                             method=self.request.method, body=body,
                                             headers=headers, follow_redirects=False,
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
    def post(self, *args, **kwargs):
        self.cache = False
        return self.get()

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


    def encode(self, value):
        return value

    def decode(self, value):
        return value

    def process_request_body(self, body):
        return body

    def process_request(self, request):
        headers = {}
        for k, v in request.headers.items():
            if k.lower() not in ['host']:
                headers[k] = v
        uri = request.uri
        body = request.body
        if body:
            body = body.replace(my_domain, target_doamin)
            body = self.process_request_body(body)
        return headers, uri, body

    def _process_response(self, response):
        if self.cache and response.effective_url in file_cache:
            value = file_cache[response.effective_url]
            return self.decode(value)
        
        res = self.process_response(response)
        file_cache[response.effective_url] = self.encode(res)
        return res

    def process_response(self, response):
        code = response.code
        headers = response.headers
        if 'Location' in headers:
            headers['Location'] = headers['Location'].replace(target_doamin, my_domain)
        return code, headers, response.body


class ImageHandler(ProxyHandler):
    cache = True

class CodeHandler(ProxyHandler):
    cache = False


class StaticHandler(ProxyHandler):
    cache = True
    response_replaces = [(target_doamin, my_domain), ('Custom Drop', 'Custom DIY Drop'), ('Customdropshipping', ' Customdiydropshipping')]

    def process_body(self, response, body):
        return body

    def process_response(self, response):
        code, headers, body = super(StaticHandler, self).process_response(response)
        if body:
            for k, v in self.response_replaces:
                body = body.replace(k, v)
            if self.current_user:
                body = body.replace(self.current_user.hash_user_name, self.current_user.user_name)
                body = body.replace(self.current_user.hash_user_email, self.current_user.user_email)

            body = self.process_body(response, body)
        
        return code, headers, body


class HtmlHandler(StaticHandler):
    cache = False
    remove_elms = ['.headContact', '.footNewsletter', ('.footNav li', 'eq(2)')]

    def change_body_extra(self, response, body):
        pass

    def get_remove_elms(self):
        elms = []
        clss = [self.__class__]
        while clss:
            cls = clss.pop(0)
            if not issubclass(cls, StaticHandler):
                break
            if hasattr(cls, 'remove_elms'):
                elms.extend(cls.remove_elms)
            
            clss.extend(cls.__bases__)
        return set(elms)


    def process_body(self, response, body):
        pqbody = pq(body)

        for elm in self.get_remove_elms():

            if isinstance(elm, (tuple, list)):
                obj = pqbody(elm[0])
                for ex in elm[1:]:
                    obj = eval('obj.%s' % ex, {'obj' : obj})

            else:
                obj = pqbody.find(elm)
            obj.remove()

        self.change_body_extra(response, pqbody)

        body = pqbody.outerHtml()

        return body


class SignSignupAction(StaticHandler):
    def get_data_map(self):
        user_email = self.get_argument('user_email')
        user_verify_email = self.get_argument('user_verify_email', '')
        
        user_password = self.get_argument('user_password', '')
        user_verify_password = self.get_argument('user_verify_password')
        user_name = self.get_argument('user_name', '')

        hash_user_email = user_email and md5(user_email).hexdigest() + '@' + user_email.split('@')[-1] or user_email
        hash_user_verify_email = user_verify_email and md5(user_verify_email).hexdigest() + '@' + user_verify_email.split('@')[-1] or user_verify_email

        hash_user_name = user_name and md5(user_name).hexdigest() or user_name

        return locals()


    def process_request(self, request):
        headers, uri, body = super(SignSignupAction, self).process_request(request)
        names = self.get_data_map()

        data = {
            'return' : self.get_argument('return', ''),
            'user_email' : names['hash_user_email'],
            'user_verify_email' : names['hash_user_verify_email'], 
            'user_password' : names['user_password'],
            'user_verify_password' : names['user_verify_password'],
            'user_name' : names['hash_user_name'],
            'code': self.get_argument('code', '')
        }
        body = urllib.urlencode(data)
        return headers, uri, body

    def process_response(self, response):
        code, headers, body = super(SignSignupAction, self).process_response(response)
        if code == 200 and headers.get('Set-Cookie', '').find('user=') != -1:
            names = self.get_data_map()
            profile = UserProfile()
            profile.__dict__.update(names)
            profile.save()
            self.set_secure_cookie('profile_id', unicode(profile.pk), expires_days=31 * 1000)

            body = body.replace(profile.hash_user_name, profile.user_name)
        return code, headers, body



class SignSigninAction(StaticHandler):
    def prepare(self):
        if self.request.method == 'POST':
            user_email = self.get_argument('user_email', '')
            try:
                self.profile = UserProfile.objects.get(user_email=user_email)
            except:
                return self.redirect('/sign-signin/s/2/')



    def process_request_body(self, body):
        if self.request.method != 'POST':
            return body
        user_password = self.get_argument('user_password', '')
        
        data = dict(urlparse.parse_qsl(body))

        data['user_email'] = self.profile.hash_user_email
        return urllib.urlencode(data)

    def process_response(self, response):

        code, headers, body = super(SignSigninAction, self).process_response(response)
        
        if self.request.method == 'POST' and code == 200 and headers.get('Set-Cookie', '').find('user=') != -1:
            self.set_secure_cookie('profile_id', unicode(self.profile.pk), expires_days=31 * 1000)

            body = body.replace(self.profile.hash_user_name, self.profile.user_name)
        return code, headers, body


class SignSigoutAction(ProxyHandler):
    def process_response(self, response):
        self.clear_cookie('profile_id')


class MyHandler(HtmlHandler):
    remove_elms = ['.prompt1']


class MyAccountSetPassword(HtmlHandler):
    def process_response(self, response):
        code, headers, body = super(MyAccountSetPassword, self).process_response(response)
        if body.find('/myaccount-change_password/s/1/') != -1:
            self.current_user.user_password = self.get_argument('user_new_password')
            self.current_user.save()
        return code, headers, body



class MyAccountProfile(HtmlHandler):
    def get_data_map(self):        
        user_name = self.get_argument('user_name', '')
        hash_user_name = user_name and md5(user_name).hexdigest() or user_name

        return locals()


    def process_request(self, request):
        headers, uri, body = super(MyAccountProfile, self).process_request(request)
        names = self.get_data_map()

        data = {
            'user_name' : names['hash_user_name'],
        }
        body = urllib.urlencode(data)
        return headers, uri, body


class Cart(HtmlHandler):
    remove_elms = [('.table1', 'eq(1)'), ('.line2', 'eq(1)')]


class CartPayment(HtmlHandler):
    def get(self, order_sn, *args, **kwargs):
        if self.current_user:
            order, create = UserOrder.objects.get_or_create(user=self.current_user, order_sn=order_sn)

        return HtmlHandler.get(self)


handlers = [
    (r'.*\.(jpg|png|bmp|gif|jpeg|ico)', ImageHandler),
    (r'/edit-(i|img)/.*', ImageHandler),
    (r'.*\.(css|js)', StaticHandler),

    (r'/code', CodeHandler),
    (r'/service-ad/.*', StaticHandler),
    (r'/edit-(product|color|model)/.*', StaticHandler),
    (r'/sign-signup_action/.*', SignSignupAction),
    (r'/sign-signout_action/.*', SignSigoutAction),
    (r'/sign-signin_action/.*', SignSigninAction),
    (r'/cart', Cart),
    (r'/myaccount-set_password/.*', MyAccountSetPassword),
    (r'/myaccount-profile/.*', MyAccountProfile),
    (r'/my.*', MyHandler),
    (r'/cart-payment/cart/(.+)/.*', CartPayment),
    (r'.*', HtmlHandler),
]


class ProxyApplication(tornado.web.Application):
    def __init__(self, io_loop=None, **kwargs):
        kwargs.update(handlers=handlers)

        super(ProxyApplication, self).__init__(**kwargs)
        self.io_loop = io_loop or tornado.ioloop.IOLoop.instance()
        self.proxypass = 'http://www.customdropshipping.com'

    def start(self, port, address=''):
        self.listen(port, address=address)
        self.io_loop.start()

import base64
import uuid



def run_proxy(**kwargs):
    parser = OptionParser(conflict_handler='resolve')
    parser.add_option('-p', '--port', dest='port', action="store", help="the listen port", type='int')
    parser.add_option('--logname', dest='logname', action="store", help="the log name", type='string')
    parser.add_option('--loglevel', dest='loglevel', action="store", help="the log level", type='int')
    parser.add_option('-d', '--debug', dest='debug', action="store_true", help="run in debug mode")
    parser.add_option('--proxypass', dest='proxypass', action="store", help="the host to proxy", type="string")

    options, args = parser.parse_args(sys.argv[1:])

    if not options.logname:
        options.logname = 'webproxy'

    if not options.loglevel:
        options.loglevel = 40

    open_log(options.logname, options.loglevel)
    open_debug()
    log.trace("start server on %s proxypass %s", options.port, options.proxypass)
    app = ProxyApplication(debug = options.debug, cookie_secret='aaaa')
    app.start(options.port)


if __name__ == '__main__':
    run_proxy()
