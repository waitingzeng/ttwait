# -*- Encoding: utf-8 -*-
import base64
import binascii
import cgi
import hashlib
import hmac
import logging
import time
import urllib
import urlparse
import uuid
from pycomm.utils.storage import Storage
from tornado.auth import OAuthMixin, _oauth10a_signature

from tornado import httpclient
from tornado import escape
from tornado.ioloop import IOLoop


class User(Storage):
    pass

class BaseOAuthMixin(OAuthMixin):
    
    _OAUTH_NO_CALLBACKS = False

    def authenticate_redirect(self):
        http = httpclient.AsyncHTTPClient()
        http.fetch(self._oauth_request_token_url(), self.async_callback(
            self._on_request_token, self._OAUTH_AUTHENTICATE_URL, None))

    def api_request(self, path, callback, access_token=None, post_args=None, **args):

        url = self._OAUTH_API_URL % path
        
        if access_token:
            
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            
            method = 'POST' if post_args is not None else 'GET'
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            args.update(oauth)
            
        if args:
            url += '?' + urllib.urlencode(args)
        
        callback = self.async_callback(self._on_api_request, callback)
        
        http = httpclient.AsyncHTTPClient()
        
        if post_args is not None:
            http.fetch(url, method='POST', body=urllib.urlencode(post_args), callback=callback)
        else:
            http.fetch(url, callback=callback)

    def _on_api_request(self, callback, response):
        
        if response.error:
            logging.warning('Error response %s fetching %s', response.error,
                            response.request.url)
            callback(None)
            return
        
        callback(escape.json_decode(response.body))

    def _oauth_consumer_token(self):
        return dict(key=self._OAUTH_CONSUMER_KEY, secret=self._OAUTH_CONSUMER_SECRET)

class SinaMixin(BaseOAuthMixin):
    
    _OAUTH_CONSUMER_KEY = 'XXXXXXXXXXX'
    _OAUTH_CONSUMER_SECRET = 'XXXXXXXXXXXXXXXXXXXXX'
    
    _OAUTH_REQUEST_TOKEN_URL = 'http://api.t.sina.com.cn/oauth/request_token'
    _OAUTH_ACCESS_TOKEN_URL = 'http://api.t.sina.com.cn/oauth/access_token'
    _OAUTH_AUTHORIZE_URL = 'http://api.t.sina.com.cn/oauth/authorize'
    
    _OAUTH_AUTHENTICATE_URL = 'http://api.t.sina.com.cn/account/verify_credentials.json'
    _OAUTH_API_URL = 'http://api.t.sina.com.cn/%s.json'
    
    def _oauth_get_user(self, access_token, callback):
        
        callback = self.async_callback(self._parse_user_response, callback)
        
        self.api_request('users/show/' + access_token['user_id'],
            access_token=access_token, callback=callback)

    def _parse_user_response(self, callback, user):
        parse_user = User()
        parse_user.id = user['id']
        parse_user.name = user['name']
        parse_user.portrait = user['profile_image_url']
        parse_user.email = ''
        callback(parse_user)
        
class QQMixin(BaseOAuthMixin):
    
    _OAUTH_CONSUMER_KEY = 'YYYYYYYYYYYYYYYYYYY'
    _OAUTH_CONSUMER_SECRET = 'YYYYYYYYYYYYYYYYYYYYY'
    
    _OAUTH_REQUEST_TOKEN_URL = 'http://open.t.qq.com/cgi-bin/request_token'
    _OAUTH_ACCESS_TOKEN_URL = 'http://open.t.qq.com/cgi-bin/access_token'
    _OAUTH_AUTHORIZE_URL = 'http://open.t.qq.com/cgi-bin/authorize'
    
    _OAUTH_AUTHENTICATE_URL = 'http://open.t.qq.com/api/user/verify?format=json'
    _OAUTH_API_URL = 'http://open.t.qq.com/api/%s'
    
    _OAUTH_VERSION = '1.0'
    
    def authorize_redirect(self, callback_uri=None, extra_params=None):
        if callback_uri and getattr(self, "_OAUTH_NO_CALLBACKS", False):
            raise Exception("This service does not support oauth_callback")
        
        http = httpclient.AsyncHTTPClient()
        http.fetch(self._oauth_request_token_url(callback_uri=callback_uri,
            extra_params=extra_params),
            self.async_callback(
                self._on_request_token,
                self._OAUTH_AUTHORIZE_URL,
            callback_uri))
        
    def _oauth_request_token_url(self, callback_uri= None, extra_params=None):
        consumer_token = self._oauth_consumer_token()
        url = self._OAUTH_REQUEST_TOKEN_URL
        args = dict(
            oauth_consumer_key=consumer_token["key"],
            oauth_signature_method="HMAC-SHA1",
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=getattr(self, "_OAUTH_VERSION", "1.0"),
        )
        
        if callback_uri:
            args["oauth_callback"] = urlparse.urljoin(
                self.request.full_url(), callback_uri)
        if extra_params: args.update(extra_params)
        signature = _oauth10a_signature(consumer_token, "GET", url, args)

        args["oauth_signature"] = signature
        return url + "?" + urllib.urlencode(args)
    
    def _oauth_access_token_url(self, request_token):
        consumer_token = self._oauth_consumer_token()
        url = self._OAUTH_ACCESS_TOKEN_URL
        args = dict(
            oauth_consumer_key=consumer_token["key"],
            oauth_token=request_token["key"],
            oauth_signature_method="HMAC-SHA1",
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=getattr(self, "_OAUTH_VERSION", "1.0"),
        )
        if "verifier" in request_token:
            args["oauth_verifier"]=request_token["verifier"]

        signature = _oauth10a_signature(consumer_token, "GET", url, args,
                                            request_token)

        args["oauth_signature"] = signature
        return url + "?" + urllib.urlencode(args)
    
    def _oauth_request_parameters(self, url, access_token, parameters={}, method="GET"):
        consumer_token = self._oauth_consumer_token()
        base_args = dict(
            oauth_consumer_key=consumer_token["key"],
            oauth_token=access_token["key"],
            oauth_signature_method="HMAC-SHA1",
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=getattr(self, "_OAUTH_VERSION", "1.0"),
        )
        args = {}
        args.update(base_args)
        args.update(parameters)
        signature = _oauth10a_signature(consumer_token, method, url, args,
                                         access_token)
        base_args["oauth_signature"] = signature
        return base_args
    
    def _oauth_get_user(self, access_token, callback):
        
        callback = self.async_callback(self._parse_user_response, callback)
        
        self.api_request('user/info', access_token=access_token, callback=callback, format='json')

    def _parse_user_response(self, callback, user):
        parse_user = User()
        parse_user.id = self.get_argument('openid', None)
        parse_user.name = user['data']['name']
        parse_user.portrait = user['data']['head'] + '/100'
        parse_user.email = user['data']['email']
        callback(parse_user)
        
class NeteaseMixin(BaseOAuthMixin):
    
    _OAUTH_CONSUMER_KEY = 'ZZZZZZZZZZZZZZ'
    _OAUTH_CONSUMER_SECRET = 'ZZZZZZZZZZZZZZZZZZZZZZ'
    
    _OAUTH_REQUEST_TOKEN_URL = 'http://api.t.163.com/oauth/request_token'
    _OAUTH_ACCESS_TOKEN_URL = 'http://api.t.163.com/oauth/access_token'
    _OAUTH_AUTHORIZE_URL = 'http://api.t.163.com/oauth/authenticate'
    
    _OAUTH_AUTHENTICATE_URL = 'http://api.t.163.com/account/verify_credentials.json'
    _OAUTH_API_URL = 'http://api.t.163.com/%s.json'
    
    _OAUTH_VERSION = '1.0'
    
    def _oauth_get_user(self, access_token, callback):
        
        callback = self.async_callback(self._parse_user_response, callback)
        
        self.api_request('users/show', access_token=access_token, callback=callback)

    def _parse_user_response(self, callback, user):
        parse_user = User()
        parse_user.id = user['id']
        parse_user.name = user['name']
        parse_user.portrait = user['profile_image_url']
        parse_user.email = ''
        callback(parse_user)
        
class SohuMixin(BaseOAuthMixin):
    
    _OAUTH_CONSUMER_KEY = '1111111111111111'
    _OAUTH_CONSUMER_SECRET = '111111111111111111111111111111'
    
    _OAUTH_REQUEST_TOKEN_URL = 'http://api.t.sohu.com/oauth/request_token'
    _OAUTH_ACCESS_TOKEN_URL = 'http://api.t.sohu.com/oauth/access_token'
    _OAUTH_AUTHORIZE_URL = 'http://api.t.sohu.com/oauth/authorize'
    
    _OAUTH_AUTHENTICATE_URL = 'http://api.t.sohu.com/account/verify_credentials.json'
    _OAUTH_API_URL = 'http://api.t.sohu.com/%s.json'
    
    _OAUTH_VERSION = '1.0'
    
    def authorize_redirect(self, callback_uri=None, extra_params=None):
        if callback_uri and getattr(self, "_OAUTH_NO_CALLBACKS", False):
            raise Exception("This service does not support oauth_callback")
        
        http = httpclient.AsyncHTTPClient()
        http.fetch(self._oauth_request_token_url(callback_uri=callback_uri,
            extra_params=extra_params),
            self.async_callback(
                self._on_request_token,
                self._OAUTH_AUTHORIZE_URL,
            callback_uri))
        
    def _oauth_request_token_url(self, callback_uri= None, extra_params=None):
        consumer_token = self._oauth_consumer_token()
        url = self._OAUTH_REQUEST_TOKEN_URL
        args = dict(
            oauth_consumer_key=consumer_token["key"],
            oauth_signature_method="HMAC-SHA1",
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=getattr(self, "_OAUTH_VERSION", "1.0"),
        )
        
        if callback_uri:
            args["oauth_callback"] = urlparse.urljoin(
                self.request.full_url(), callback_uri)
        if extra_params: args.update(extra_params)
        signature = _oauth10a_signature(consumer_token, "GET", url, args)

        args["oauth_signature"] = signature
        return url + "?" + urllib.urlencode(args)
    
    def _oauth_access_token_url(self, request_token):
        consumer_token = self._oauth_consumer_token()
        url = self._OAUTH_ACCESS_TOKEN_URL
        args = dict(
            oauth_consumer_key=consumer_token["key"],
            oauth_token=request_token["key"],
            oauth_signature_method="HMAC-SHA1",
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=getattr(self, "_OAUTH_VERSION", "1.0"),
        )
        if "verifier" in request_token:
            args["oauth_verifier"]=request_token["verifier"]

        signature = _oauth10a_signature(consumer_token, "GET", url, args,
                                            request_token)

        args["oauth_signature"] = signature
        return url + "?" + urllib.urlencode(args)
    
    def _oauth_request_parameters(self, url, access_token, parameters={}, method="GET"):
        
        consumer_token = self._oauth_consumer_token()
        base_args = dict(
            oauth_consumer_key=consumer_token["key"],
            oauth_token=access_token["key"],
            oauth_signature_method="HMAC-SHA1",
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=getattr(self, "_OAUTH_VERSION", "1.0"),
        )
        args = {}
        args.update(base_args)
        args.update(parameters)
        signature = _oauth10a_signature(consumer_token, method, url, args,
                                         access_token)
        base_args["oauth_signature"] = signature
        return base_args
    
    def _oauth_get_user(self, access_token, callback):
        
        callback = self.async_callback(self._parse_user_response, callback)
        
        self.api_request('users/show',
            access_token=access_token, callback=callback)

    def _parse_user_response(self, callback, user):
        parse_user = User()
        parse_user.id = user['id']
        parse_user.name = user['screen_name']
        parse_user.portrait = user['profile_image_url']
        parse_user.email = ''
        callback(parse_user)



