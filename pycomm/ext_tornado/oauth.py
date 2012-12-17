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




class WeiboMixin(OAuth2Mixin):
    """
    The :class:`tornado.web.RequestHandler` mixin.
    """
    _OAUTH_ACCESS_TOKEN_URL = "https://api.weibo.com/oauth2/access_token?"
    _OAUTH_AUTHORIZE_URL = "https://api.weibo.com/oauth2/authorize?"
    _OAUTH_NO_CALLBACKS = False

    def authorize_redirect(self, redirect_uri, extra_params=None):
        """
        Redirect user to the weibo authorization page.

        User will be redirected to ``redirect_uri`` after he/she accepts/rejects
        the authorization request. If the user accepts the request, ``redirect_uri``
        will be visited with ``code`` parameter in HTTP GET, usually
        ``code`` will be further filled to :func:`get_authenticated_user`
        to obtain the ``access_code`` for later use.
        """
        self.require_setting("weibo_app_key", "Weibo OAuth2")
        args = {
            "redirect_uri": redirect_uri,
            "client_id": self.settings["weibo_app_key"],
            }
        if extra_params:
            args.update(extra_params)
        self.redirect(
            url_concat(self._OAUTH_AUTHORIZE_URL, args)
        )

    def get_authenticated_user(self, redirect_uri,
                               code, callback, extra_fields=None):
        """
        Get the authenticated user by given ``authorization_code``

        The ``callback`` function will be called with response of
        ``/users/show`` which is a dict with some information
        of specific user. ``access_token`` and ``session_expires``
        are also set in this dict, you should store ``access_token``
        to database/session for later use.

        This function calls ``OAuth2/access_token``, ``/account/get_uid``
        and ``/users/show`` internally, see
        http://open.weibo.com/wiki/OAuth2/access_token
        """
        self.require_setting("weibo_app_key", "Weibo OAuth2")
        self.require_setting("weibo_app_secret", "Weibo OAuth2")
        http = httpclient.AsyncHTTPClient()
        args = {
            "redirect_uri": redirect_uri,
            "extra_params": {"grant_type": 'authorization_code'},
            "code": code,
            "client_id": self.settings["weibo_app_key"],
            "client_secret": self.settings["weibo_app_secret"],
            }

        fields = {'id', 'name', 'profile_image_url', 'location', 'url'}
        if extra_fields:
            fields.update(extra_fields)

        # Weibo's oauth2 access_token only accepts POST method
        http.fetch(self._OAUTH_ACCESS_TOKEN_URL, method="POST",
            body=urllib.urlencode(args),
            callback=self.async_callback(self._on_access_token,
                callback, fields),
            ca_certs=_CA_CERTS
        )

    def _on_access_token(self, callback, fields, response):
        if response.error:
            logging.warning('Weibo auth error: %s' % str(response))
            callback(None)
            return

        session = escape.json_decode(response.body)

        self.weibo_request(
            path="/account/get_uid",
            callback=self.async_callback(
                self._on_get_uid, callback, session, fields),
            access_token=session["access_token"]
        )

    def _on_get_uid(self, callback, session, fields, response):
        if response is None or not "uid" in response:
            callback(None)
            return

        self.weibo_request(
            path="/users/show",
            callback=self.async_callback(
                self._on_get_user_info, callback, session, fields),
            access_token=session["access_token"],
            uid=response["uid"]
        )

    def _on_get_user_info(self, callback, session, fields, user):
        if user is None:
            callback(None)
            return

        fieldmap = {}
        for field in fields:
            fieldmap[field] = user.get(field)

        fieldmap.update({"access_token": session["access_token"],
                         "session_expires": session.get("expires_in")})
        callback(fieldmap)

    def weibo_request(self, path, callback, access_token=None,
                      post_args=None, **args):
        """
        This is a helper function to send Weibo API requests.

        ``path`` should be set to the API path which the request is sent to,
        e.g. ``'statuses/public_timeline'``.

        A dict containing user information will be passed to ``callback``
        function.

        If ``post_args`` is given, the request will be sent using POST method
        with ``post_args``. Anything in the keyword arguments will sent
        as HTTP query string.

        .. note:: For ``/statuses/upload`` method, the ``pic`` parameter is
           required and it should be a dict with key ``filename``, ``content`` and
           ``mime_type``. ``/statuses/upload`` requires a ``multipart/form-data``
           post request, therefore it must be handled differently. tornado_weibo
           already knows how to construct a ``multipart/form-data`` request, so you
           don't have to do extra work besides providing the ``pic`` dict. See
           http://open.weibo.com/wiki/Statuses/upload
        """
        url = "https://api.weibo.com/2" + path + ".json"
        if path == "/statuses/upload": # this request should be handled differently
            return self._weibo_upload_request(url, callback,
                access_token, args.get("pic"), status=args.get("status"))
        all_args = {}
        if access_token:
            all_args["access_token"] = access_token
            all_args.update(args)
            all_args.update(post_args or {})
        if all_args:
            url += "?" + urllib.urlencode(all_args)
        callback = self.async_callback(self._on_weibo_request, callback)
        http = httpclient.AsyncHTTPClient()
        if post_args is not None:
            http.fetch(url, method="POST", body=urllib.urlencode(post_args),
                callback=callback, ca_certs=_CA_CERTS)
        else:
            http.fetch(url, callback=callback, ca_certs=_CA_CERTS)

    def _weibo_upload_request(self, url, callback,
                              access_token, pic, status=None):
        # /statuses/upload is special
        if pic is None:
            raise Exception("pic not filled!")
        form = MultiPartForm()
        form.add_file("pic", pic["filename"], pic["content"], pic["mime_type"])

        form.add_field("status", status)
        headers = {
            "Content-Type": form.get_content_type(),
            }
        args = {
            "access_token": access_token
        }
        url += "?" + urllib.urlencode(args)
        http = httpclient.AsyncHTTPClient()
        http.fetch(url, method="POST", body=str(form),
            callback=self.async_callback(self._on_weibo_request, callback),
            headers=headers,
            ca_certs=_CA_CERTS)

    def _on_weibo_request(self, callback, response):
        if response.error:
            logging.warning("Error response %s fetching %s, body %s",
                response.error,
                response.request.url,
                response.body
            )
            callback(None)
            return
        callback(escape.json_decode(response.body))


class MultiPartForm(object):
    """Helper class to build a multipart form

    This part was copied from http://www.doughellmann.com/PyMOTW/urllib2/
    """

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, body, mimetype):
        """Add a file to be uploaded."""
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        """Return a string representing the form data,
        including attached files.
        """
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [part_boundary,
             'Content-Disposition: form-data; name="%s"' % name,
             '',
             value,
             ]
            for name, value in self.form_fields
        )

        # Add the files to upload
        parts.extend(
            [part_boundary,
             'Content-Disposition: form-data; name="%s"; filename="%s"' %\
             (field_name, filename),
             'Content-Type: %s' % content_type,
             '',
             body,
             ]
            for field_name, filename, content_type, body in self.files
        )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)
