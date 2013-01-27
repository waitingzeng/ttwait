#!/usr/bin/python
#coding=utf8
import base64
from tornado.web import *
from hashlib import md5

class BasicAuthMixin(object):
    def _request_auth(self, realm):
        if self._headers_written: raise Exception('headers have already been written')
        
        self.set_status(401)
        self.set_header('WWW-Authenticate', 'Basic realm="%s"' % realm)
        self.finish()
        
        return False
        
    def get_authenticated_user(self, auth_func, realm):
        """Requests HTTP basic authentication credentials from the client, or
        authenticates the user if credentials are provided."""
        try:
            auth = self.request.headers.get('Authorization')
            
            if auth == None: return self._request_auth(realm)
            if not auth.startswith('Basic '): return self._request_auth(realm)
            
            auth_decoded = base64.decodestring(auth[6:])
            username, password = auth_decoded.split(':', 1)
            
            if auth_func(self, realm, username, password):
                self._current_user = username
                return True
            else:
                return self._request_auth(realm)
        except Exception, e:
            import traceback
            traceback.print_exc()
            return self._request_auth(realm)
            
def basic_auth(realm, auth_func):
    """A decorator that can be used on methods that you wish to protect with
    HTTP basic"""
    def basic_auth_decorator(func):
        def func_replacement(self, *args, **kwargs):
            if self.get_authenticated_user(auth_func, realm):
                return func(self, *args, **kwargs)
        
        return func_replacement
    return basic_auth_decorator



class DigestAuthMixin(object):
    def apply_checksum(self, data):
        return md5(data).hexdigest()

    def apply_digest(self, secret, data):
        return self.apply_checksum(secret + ":" + data)

    def A1(self, algorithm, auth_pass):
        """
         If 'algorithm' is "MD5" or unset, A1 is:
         A1 = unq(username-value) ":" unq(realm-value) ":" passwd

         if 'algorithm' is 'MD5-Sess', A1 is:
         A1 = H( unq(username-value) ":" unq(realm-value) ":" passwd )
          ":" unq(nonce-value) ":" unq(cnonce-value)

        """

        username = self.params["username"]
        if algorithm == 'MD5' or not algorithm:
            return "%s:%s:%s" % (username, self.realm, auth_pass)
        elif algorithm == 'MD5-Sess':
            return self.apply_checksum('%s:%s:%s:%s:%s' % \
                                       (username,
                                       self.realm,
                                       auth_pass,
                                       self.params['nonce'],
                                       self.params['cnonce']))


    def A2(self):
        """
        If the "qop" directive's value is "auth" or is unspecified, then A2 is:
            A2 = Method ":" digest-uri-value
        Else,
            A2 = Method ":" digest-uri-value ":" H(entity-body)

        """
        if self.params['qop'] == 'auth' or not self.params['qop']:
            return self.request.method + ":" + self.request.uri
        elif self.params['qop'] == 'auth-int':
            #print "UNSUPPORTED 'qop' METHOD\n"
            return ":".join([self.request.method,
                             self.request.uri,
                             self.apply_checksum(self.request.body)])
        else:
            print "A2 GOT BAD VALUE FOR 'qop': %s\n" % self.params['qop']

    def response(self, auth_pass):
        if 'qop' in self.params:
            auth_comps = [self.params['nonce'],
                               self.params['nc'],
                               self.params['cnonce'],
                               self.params['qop'],
                               self.apply_checksum(self.A2())]
            return self.apply_digest(self.apply_checksum( \
                                    self.A1(self.params.get('algorithm'),
                                            auth_pass)),
                                     ':'.join(auth_comps))
        else:
            return self.apply_digest(self.apply_checksum( \
                                    self.A1(self.params.get('algorithm'),
                                            auth_pass)),
                                    ':'.join([self.params["nonce"],
                                              self.apply_checksum(self.A2())]))

    def _parse_header(self, authheader):
        try:
            n = len("Digest ")
            authheader = authheader[n:].strip()
            items = authheader.split(", ")
            keyvalues = [i.split("=", 1) for i in items]
            keyvalues = [(k.strip(), v.strip().replace('"', '')) for k, v in keyvalues]
            self.params = dict(keyvalues)
        except:
            self.params = []

    def _create_nonce(self):
        return md5("%d:%s" % (time.time(), self.realm)).hexdigest()

    def create_auth_header(self):
        self.set_status(401)
        nonce = self._create_nonce()
        self.set_header("WWW-Authenticate", "Digest algorithm=MD5 realm=%s qop=auth nonce=%s" % (self.realm, nonce))
        self.finish()

        return False

    def get_authenticated_user(self, get_creds_callback, realm):
        creds = None
        expected_response = None
        actual_response = None
        auth = None
        if not hasattr(self,'realm'):
            self.realm = realm
        
        try:
            auth = self.request.headers.get('Authorization')
            if not auth or not auth.startswith('Digest '):
                return self.create_auth_header()
            else:
                self._parse_header(auth)
                required_params = ['username', 'realm', 'nonce', 'uri', 'response', 'qop', 'nc', 'cnonce']
                for k in required_params:
                    if k not in self.params:
                        print "REQUIRED PARAM %s MISSING\n" % k
                        return self.create_auth_header()
                    elif not self.params[k]:
                        print "REQUIRED PARAM %s IS NONE OR EMPTY\n" % k
                        return self.create_auth_header()
                    else:
                        continue
            print '>>>>>bbb'
            creds = get_creds_callback(self.params['username'])
            if not creds:
                # the username passed to get_creds_callback didn't
                # match any valid users.
                self.create_auth_header()
            else:
                expected_response = self.response(creds['auth_password'])
                actual_response = self.params['response']
                print "Expected: %s" % expected_response
                print "Actual: %s" % actual_response

            if expected_response and actual_response:
                if expected_response == actual_response:
                    self._current_user = self.params['username']
                    print "Digest Auth user '%s' successful for realm '%s'. URI: '%s', IP: '%s'" % (self.params['username'], self.realm, self.request.uri, self.request.remote_ip)
                    return True
                else:
                    self.create_auth_header()

        except Exception as out:
            print "FELL THROUGH: %s\n" % out
            print "AUTH HEADERS: %s" % auth
            print "SELF.PARAMS: ",self.params,"\n"
            print "CREDS: ", creds
            print "EXPECTED RESPONSE: %s" % expected_response
            print "ACTUAL RESPONSE: %s" % actual_response
            return self.create_auth_header()


def digest_auth(realm, auth_func):
    """A decorator used to protect methods with HTTP Digest authentication.

    """
    def digest_auth_decorator(func):
        def func_replacement(self, *args, **kwargs):
            # 'self' here is the RequestHandler object, which is inheriting
            # from DigestAuthMixin to get 'get_authenticated_user'
            if self.get_authenticated_user(auth_func, realm):
                return func(self, *args, **kwargs)
        return func_replacement
    return digest_auth_decorator
