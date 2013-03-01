#!/usr/bin/python
#coding=utf8
from tornado.web import URLSpec, import_object, HTTPError
from tornado.escape import native_str, parse_qs_bytes
from tornado.httpclient import HTTPResponse
from tornado.escape import utf8, _unicode, url_unescape
import urlparse
import types
import re
from pycomm.log import log, PrefixLog
from .utils import Response, Url
from pyquery import PyQuery as pq
from pycomm.utils.encoding import any_to_unicode


class ResponseHandler(object):
    def __init__(self, parser, response, **kwargs):
        super(ResponseHandler, self).__init__()
        self.parser = parser
        self.spider = self.parser.spider
        self.pipeline = self.parser.pipeline
        self.response = response
        self._finished = False
        self.initialize(**kwargs)
        self.log = PrefixLog(response.url[:20])

    def initialize(self):
        pass

    @property
    def settings(self):
        return self.parser.settings

    _ARG_DEFAULT = []

    def get_argument(self, name, default=_ARG_DEFAULT, strip=True):
        args = self.get_arguments(name, strip=strip)
        if not args:
            if default is self._ARG_DEFAULT:
                raise HTTPError(400, "Missing argument %s" % name)
            return default
        return args[-1]

    def get_arguments(self, name, strip=True):
        values = []
        for v in self.response.arguments.get(name, []):
            v = self.decode_argument(v, name=name)
            if isinstance(v, unicode):
                # Get rid of any weird control chars (unless decoding gave
                # us bytes, in which case leave it alone)
                v = re.sub(r"[\x00-\x08\x0e-\x1f]", " ", v)
            if strip:
                v = v.strip()
            values.append(v)
        return values

    def decode_argument(self, value, name=None):
        return any_to_unicode(value)

    def prepare(self):
        pass

    def parse(self, *args, **kwargs):
        raise

    def find_handler(self, href):
        url = Url('', href, self.response)
        return self.parser.find_handler(url.full_url.lower())

    def get_url(self, tag_a):
        a = pq(tag_a)
        href = a.attr('href')
        if not href:
            href = a.attr('src')
            if not href:
                return None

        title = a.attr('title')
        if title:
            return Url(title, href, self.response)

        title = a.attr('alt')
        if title:
            return Url(title, href, self.response)

        title = a.text()
        if title:
            return Url(title, href, self.response)

        title = a.html()
        return Url(title, href, self.response)

    def find_all_href(self, *args, **kwargs):
        for a in pq(self.response.body).find('a'):
            a = pq(a)
            href = a.attr('href')
            if not href:
                continue
            if self.find_handler(href):
                yield self.get_url(a)

    def _execute(self, transforms, *args, **kwargs):
        self._transforms = transforms
        self.response.rethrow()
        try:
            self.prepare()
            if not self._finished:
                args = [self.decode_argument(arg) for arg in args]
                
                res = self.parse(*args, **kwargs)
                if isinstance(res, types.GeneratorType):
                    for item in res:
                        yield item
                else:
                    yield res

        except Exception, e:
            self.log.exception()
            self._handle_request_exception(e)

    def _handle_request_exception(self, e):
        pass


class NotFoundHandler(Exception):
    def __init__(self, response):
        self.response = response


class CollectUrlsHandler(ResponseHandler):
    def parse(self, *args, **kwargs):
        return self.find_all_href()


class Parser(object):
    """复用了tornado的application的实现"""
    def __init__(self, handlers=None, default_host="", transforms=None,
                 **settings):
        if transforms is None:
            self.transforms = []
        else:
            self.transforms = transforms
        self.handlers = []
        self.named_handlers = {}
        self.default_host = default_host
        self.settings = settings
        if handlers:
            self.add_handlers(".*$", handlers)
        self.pipeline = None
        self.spider = None

    def add_handlers(self, host_pattern, host_handlers):
        if not host_pattern.endswith("$"):
            host_pattern += "$"
        handlers = []
        # The handlers with the wildcard host_pattern are a special
        # case - they're added in the constructor but should have lower
        # precedence than the more-precise handlers added later.
        # If a wildcard handler group exists, it should always be last
        # in the list, so insert new groups just before it.
        if self.handlers and self.handlers[-1][0].pattern == '.*$':
            self.handlers.insert(-1, (re.compile(host_pattern), handlers))
        else:
            self.handlers.append((re.compile(host_pattern), handlers))

        for spec in host_handlers:
            if isinstance(spec, type(())):
                assert len(spec) in (2, 3)
                pattern = spec[0]
                handler = spec[1]

                if isinstance(handler, str):
                    # import the Module and instantiate the class
                    # Must be a fully qualified name (module.ClassName)
                    handler = import_object(handler)

                if len(spec) == 3:
                    kwargs = spec[2]
                else:
                    kwargs = {}
                spec = URLSpec(pattern, handler, kwargs)
            handlers.append(spec)
            if spec.name:
                if spec.name in self.named_handlers:
                    log.warning(
                        "Multiple handlers named %s; replacing previous value",
                        spec.name)
                self.named_handlers[spec.name] = spec

    def add_transform(self, transform_class):
        """Adds the given OutputTransform to our transform list."""
        self.transforms.append(transform_class)

    def _get_host_handlers(self, host):
        #host = response.netloc.lower().split(':')[0]
        for pattern, handlers in self.handlers:
            if pattern.match(host):
                return handlers
        return None

    def find_handler(self, url):
        result = urlparse.urlparse(url)
        host = result.netloc.lower().split(':')[0]

        handlers = self._get_host_handlers(host)
        if not handlers:
            handler = DefaultHandler(self, response)
        else:
            for spec in handlers:
                match = spec.regex.match(result.path.lower())
                if match:
                    return True
        return False

    def __call__(self, response, **kwargs):
        """Called by HTTPServer to execute the request."""
        if not isinstance(response, Response):
            response = Response(response)

        transforms = [t(response) for t in self.transforms]
        handler = None
        args = []
        handlers = self._get_host_handlers(response.netloc.lower().split(':')[0])
        if not handlers:
            handler = DefaultHandler(self, response, **kwargs)
        else:
            for spec in handlers:

                match = spec.regex.match(response.path.lower())
                if match:
                    handler = spec.handler_class(self, response, **spec.kwargs)
                    if spec.regex.groups:
                        # None-safe wrapper around url_unescape to handle
                        # unmatched optional groups correctly
                        def unquote(s):
                            if s is None:
                                return s
                            return url_unescape(s, encoding=None)
                        # Pass matched groups to the handler.  Since
                        # match.groups() includes both named and unnamed groups,
                        # we want to use either groups or groupdict but not both.
                        # Note that args are passed as bytes so the handler can
                        # decide what encoding to use.

                        args = [unquote(s) for s in match.groups()]
                    break
            if not handler:
                raise NotFoundHandler(response)

        # In debug mode, re-compile templates and reload static files on every
        # request so you don't need to restart to see changes
        return handler._execute(transforms, *args, **kwargs)

    def reverse_url(self, name, *args):
        if name in self.named_handlers:
            return self.named_handlers[name].reverse(*args)
        raise KeyError("%s not found in named urls" % name)

    def log_response(self, handler):
        request_time = 1000.0 * handler.request.request_time()
        log_method("%d %s %.2fms", handler.get_status(),
                   handler._request_summary(), request_time)
