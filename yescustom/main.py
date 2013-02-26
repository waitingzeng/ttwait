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
from pycomm.utils import text
from custom.order.comm_def import OrderStatus


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


INSANDBOX = True
if INSANDBOX:
    PAYPAL_RECEIVER_EMAIL = 'ttsell_1361842354_biz@gmail.com'
else:
    PAYPAL_RECEIVER_EMAIL = 'chobotracy@gmail.com'


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
                try:
                    self.set_status(code)
                except AssertionError, info:
                    self.log.error('not valid code %s', code)
                    raise info
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
        return self.get(*args, **kwargs )

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

    def get_request_header(self, request):
        headers = {}
        for k, v in request.headers.items():
            if k.lower() not in ['host']:
                headers[k] = v
        return headers

    def process_request(self, request):
        headers = self.get_request_header(request)
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
    response_replaces = [(target_doamin, my_domain),
         ('Custom Drop', 'Custom DIY Drop'), ('Customdropshipping', ' Customdiydropshipping'),
         ('UA-28350827-1', ''), ('february.cst@hotmail.com', PAYPAL_RECEIVER_EMAIL), ('kathy.yescustom@gmail.com', ''),
         ('order.yescustom@yahoo.com', 'yesdiycustom@live.com'),('yescustom', 'yesdiycustom'), ('23.53', '0.01')
         ]

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
    remove_elms = []#['.headContact', '.footNewsletter', ('.footNav li', 'eq(2)')]
    remove_ins = [('<div class="headContact cf">', '</div>', """<div class="headContact cf"><span style="cursor:pointer; " id="365webcall_IMME_Icon_2d955ad6" ></span>
<script type='text/javascript' src='http://www3.365webcall.com/IMMe1.aspx?settings=mw7m6XNNNN6wX6Pz3AN6760Xz3ANmN0bIz3Am6mmbI&IMME_Icon=365webcall_IMME_Icon_2d955ad6&LL=1'></script></div>"""), ('<div class="footNewsletter fr">', '<div class="line3"></div>', ''), ('<dt>FOLLOW  Customdiydropshipping</dt>', '</dd>', '')]

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

        for begin, end, replace in self.remove_ins:
            content = text.get_in(body, begin, end)
            body = body.replace('%s%s%s' % (begin, content, end), replace)

        if self.remove_elms:
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


class MyOrderOrders(MyHandler):
    remove_elms = ['.table5', ('.table1 th', 'eq(5)'), ('.table1 td', 'eq(5)')]


class MyOrderDetail(MyHandler):
    def get(self, order_sn, *args, **kwargs):
        self.order_sn = order_sn
        return MyHandler.get(self, order_sn, *args, **kwargs)

    def process_body(self, response, body):
        body = MyHandler.process_body(self, response, body)

        page = pq(body)

        b = page.find('.memberBottomRight1 .mt10')

        order, create = UserOrder.objects.get_or_create(user=self.current_user, order_sn=self.order_sn)
        if not order.content:
            content = pq(body).find('.memberBottomRight1')
            content.find('.mt10').eq(0).remove()
            order.content = content.html()
            order.save()



        b.eq(0).find('.mt5 .fb').eq(1).text(OrderStatus.attrs[order.status])

        if order.status != OrderStatus.unpaid:
            page.find('.button1').remove()

        return page.outerHtml()




class CartPayment(HtmlHandler):
    if INSANDBOX:
        response_replaces = HtmlHandler.response_replaces + [('paypal.com', 'sandbox.paypal.com')]
    @tornado.web.asynchronous
    def get(self, order_sn, *args, **kwargs):
        if self.current_user:
            order, create = UserOrder.objects.get_or_create(user=self.current_user, order_sn=order_sn)

            if not order.content:
                url = self.application.proxypass + '/myorder-order/code/%s' % order_sn
                headers = self.get_request_header(self.request)

                req = tornado.httpclient.HTTPRequest(url=url,
                                                 headers=headers, follow_redirects=False,
                                                 allow_nonstandard_methods=True)

                def handle_response(response):
                    if response.error and not isinstance(response.error,
                                                         tornado.httpclient.HTTPError):
                        self.set_status(500)
                        self.write('Internal server error:\n' + str(response.error))
                        self.finish()
                    else:
                        code, headers, body = self._process_response(response)
                        page = pq(body)
                        content = page.find('.memberBottomRight1')
                        content.find('.mt10').eq(0).remove()
                        order.content = content.html()
                        order.save()
                        return HtmlHandler.get(self)
                        
                client = tornado.httpclient.AsyncHTTPClient()

                try:
                    client.fetch(req, handle_response)
                except tornado.httpclient.HTTPError, e:
                    return HtmlHandler.get(self)
            else:
                return HtmlHandler.get(self)    
            

class CartDone(HtmlHandler):
    def get(self, order_sn, *args, **kwargs):
        if self.request.headers['Origin'] != 'https://www.paypal.com':
            return HtmlHandler.get(self, order_sn, *args, **kwargs)

        self.redirect('/myorder-order/code/%s' % order_sn)

        #return HtmlHandler.get(self, order_sn, *args, **kwargs)


class IPNHandler(BaseHandler):
    def verify_ipn(self, data):
        # prepares provided data set to inform PayPal we wish to validate the response
        data["cmd"] = "_notify-validate"
        params = urllib.urlencode(data)

        if INSANDBOX:
            # sends the data and request to the PayPal Sandbox
            paypal_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
        else:
            paypal_url = 'https://www.paypal.com/cgi-bin/webscr'

        req = urllib2.Request(paypal_url, params)
        req.add_header("Content-type", "application/x-www-form-urlencoded")
        # reads the response back from PayPal
        response = urllib2.urlopen(req)
        status = response.read()

        # If not verified
        if not status == "VERIFIED":
            return False

        # if not the correct receiver email
        if not INSANDBOX and data['txn_type'] != 'subscr_payment' \
        and not data["receiver_email"] == PAYPAL_RECEIVER_EMAIL:
            self.log.info('Incorrect receiver_email')
            self.log.info(data['receiver_email'])
            return False

        # if not the correct currency
        if not INSANDBOX and not data.get("mc_currency") == "USD":
            self.log.info('Incorrect mc_currency')
            return False

        # otherwise...
        return True

    def subscr_signup(self, data):
        # handle a 'Signup' IPN message
        # you can create a User object, for example,
        # or set a user's plan
        pass

    def subscr_payment(self, data):
        # handle a 'Payment' IPN message
        # this message gets sent when you receive a recurring payment
        # you can re-set your user's plan here
        if data['payment_status'] == 'Completed':
            order_sn = data['invoice']
            order = UserOrder.objects.get(order_sn=order_sn)
            order.payid = data['txn_id']
            order.status = OrderStatus.paid
            order.save()
        pass

    def subscr_modify(self, data):
        # handle a 'Modify' IPN message
        # the Subscribe button has an option to allow users to modify
        # their subscription plan
        # you can upgrade your user's plan here
        pass

    def subscr_eot(self, data):
        # handle a 'End of Transaction' IPN message
        # at the end of the subscription period, this message gets sent
        # you can disable a user here
        pass

    def subscr_cancel(self, data):
        # handle a 'Cancel' IPN message
        # when a user cancels his subscription (either in his PayPal page or
        # in your website), this message gets sent
        # you can disable a user here
        pass

    def subscr_failed(self, data):
        # handle a 'Failed' IPN message
        # sometimes something goes wrong while the IPN is being sent
        # you can log the error here
        pass

    def post(self, sandbox=''):
        data = {}

        # the values in request.arguments are stored as single value lists
        # we need to extract their string values
        for arg in self.request.arguments:
            data[arg] = self.request.arguments[arg][0]

        print '>>>>', data
        # If there is no txn_id in the received arguments don't proceed
        if data['txn_type'] == 'subscr_payment' \
        and not 'txn_id' in data:
            self.log.info('IPN: No Parameters')
            return

        self.log.info('IPN: Verified!')

        # Now do something with the IPN data
        if data['txn_type'] == 'subscr_signup':
            # initial subscription
            self.subscr_signup(data)
        elif data['txn_type'] == 'subscr_payment':
            # subscription renewed
            self.subscr_payment(data)
        elif data['txn_type'] == 'subscr_modify':
            # subscription plan modified
            self.subscr_modify(data)
        elif data['txn_type'] == 'subscr_eot':
            # subscription expired
            self.subscr_eot(data)
        elif data['txn_type'] == 'subscr_cancel':
            # subscription canceled
            self.subscr_cancel(data)
        elif data['txn_type'] == 'subscr_failed':
            # subscription failed
            self.subscr_failed(data)

        return



class AboutUs(HtmlHandler):
    response_replaces = HtmlHandler.response_replaces + [
        ('/data/article/201112/2011121317134384677.gif', '/data/logo/logo-363-105.jpg'), 
        ('/data/article/201112/2011121317163360585.gif', '/data/logo/logo-80-58.jpg'), 
        ('/data/article/201112/2011121317161537891.gif', '/data/logo/logo-80-58.jpg'),
        ('/data/article/201112/2011121317165065072.gif', '/data/logo/logo-80-58.jpg'),
        ]


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
    (r'/myorder-order/code/(.*)', MyOrderDetail),
    (r'/myorder-orders/.*', MyOrderOrders),
    (r'/my.*', MyHandler),
    (r'/cart-respond_action/', IPNHandler),
    (r'/cart-done/cart/(.*)/', CartDone),
    (r'/cart-payment/cart/(.+)/.*', CartPayment),
    (r'/article-about/n/about_us', AboutUs),
    (r'.*', HtmlHandler),
]


class ProxyApplication(tornado.web.Application):
    def __init__(self, io_loop=None, **kwargs):
        self.proxypass = 'http://www.customdropshipping.com'
        kwargs.update(handlers=handlers)

        super(ProxyApplication, self).__init__(**kwargs)
        self.io_loop = io_loop or tornado.ioloop.IOLoop.instance()

    def start(self, port, address=''):
        self.listen(port, address=address)
        self.io_loop.start()


from pycomm.ext_tornado.daemon_server import run_server, parse_options

options = parse_options()
app = ProxyApplication(debug = options.open_debug, cookie_secret='Q8hZd669bNYG85b9')
run_server(app)

