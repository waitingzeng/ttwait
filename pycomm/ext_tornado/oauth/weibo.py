#!/usr/bin/python
#coding=utf8
import os
import urllib
import logging
import mimetools
import itertools
from tornado.auth import OAuth2Mixin
from tornado.httputil import url_concat
from tornado import httpclient
from tornado import escape

_CA_CERTS = os.path.dirname(__file__) + "/ca-certificates.crt"
class WeiboMixin(OAuth2Mixin):
    """
    The :class:`tornado.web.RequestHandler` mixin.
    """
    _OAUTH_ACCESS_TOKEN_URL = "https://api.weibo.com/oauth2/access_token?"
    _OAUTH_AUTHORIZE_URL = "https://api.weibo.com/oauth2/authorize?"
    _OAUTH_NO_CALLBACKS = False

    def authenticate_redirect(self, redirect_uri=None, extra_params=None):
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
            "redirect_uri": redirect_uri or self.request.full_url(),
            "client_id": self.settings["weibo_app_key"],
            }
        if extra_params:
            args.update(extra_params)
        self.redirect(
            url_concat(self._OAUTH_AUTHORIZE_URL, args)
        )

    def get_authenticated_user(self, code, callback, redirect_uri=None, extra_fields=None):
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
            "redirect_uri": redirect_uri or self.request.full_url(),
            "extra_params": {"grant_type": 'authorization_code'},
            "code": code,
            "client_id": self.settings["weibo_app_key"],
            "client_secret": self.settings["weibo_app_secret"],
            }

        fields = ['id', 'name', 'profile_image_url', 'location', 'url']
        if extra_fields:
            fields.extend(extra_fields)

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



"""
import tornado.ioloop
import tornado.web
import tornado.escape
import logging
import math
from tornado_weibo.auth import WeiboMixin


class AuthenticationHandler(tornado.web.RequestHandler, WeiboMixin):

    @tornado.web.asynchronous
    def get(self):
        code = self.get_argument("code", None)
        if code:
            self.get_authenticated_user(
                redirect_uri="http://example.com/back",
                code=code,
                callback=self.async_callback(self._on_authorize,
                    next=self.get_argument("next", "/"))
            )
            return
        self.authenticate_redirect(
            redirect_uri="http://example.com/back")

    def _on_authorize(self, user, next='/'):
        if user is None:
            self.send_error()
            return

        # session expires in user["session_expires"] sec
        self.set_secure_cookie("weibo_session",
            tornado.escape.json_encode(user),
            math.ceil(user["session_expires"] / 86400.0))
        self.redirect(next)


class HomeHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        session = self.get_secure_cookie("weibo_session")
        if session is None:
            return None
        user = tornado.escape.json_decode(session)
        return user

    def get_login_url(self):
        return "/login"

    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user()
        self.write("hello %s, you are from %s?, data : <br> %s" % (
            user.get("name"),
            user.get("location"),
            tornado.escape.json_encode(user),
        ))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # change the settings here
    settings = {
        "weibo_app_key": "",
        "weibo_app_secret": "",
        "cookie_secret": "",
    }

    application = tornado.web.Application([
        (r"/login", AuthenticationHandler),
        (r"/back", AuthenticationHandler),
        (r"/", HomeHandler)
    ], **settings)
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


"""

