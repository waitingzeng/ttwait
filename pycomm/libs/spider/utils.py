#!/usr/bin/python
#coding=utf8
import tornado.web
from tornado.escape import native_str, parse_qs_bytes
from tornado.httpclient import HTTPResponse
from pycomm.utils.storage import Storage
import urlparse
from pycomm.utils.storage import Const


class Result(Storage):
    def strip(self):
        for k, v in self.items():
            if not v:
                continue
            self[k] = v.strip()
        return self

    def save(self):
        pass

class Url(object):
    def __init__(self, title, href, response=None, priority=0, **kwargs):
        self.title = title
        self.href = href
        self.priority = priority or 0
        self.response = response
        self.kwargs = kwargs
        if response:
            self.full_url = urlparse.urljoin(response.url, href)
        else:
            self.full_url = href

        parser_result = urlparse.urlparse(self.full_url)
        for field in parser_result._fields:
            setattr(self, field, getattr(parser_result, field))
        self.host = self.netloc.lower().split(':')[0]

    @property
    def skip(self):
        if not self.href:
            return True
        if self.href.startswith('#'):
            return True

        if self.response and self.full_url == self.response.url:
            return True
        return False

    def __str__(self):
        return self.href

    def __unicode__(self):
        return self.href

class Response(HTTPResponse):
    def __init__(self, response):
        self._response = response
        self.url = response.effective_url

        parser_result = urlparse.urlparse(self._response.effective_url)
        for field in parser_result._fields:
            setattr(self, field, getattr(parser_result, field))

        self.host = self.netloc.lower().split(':')[0]

        arguments = parse_qs_bytes(self.query)
        self.arguments = {}
        for name, values in arguments.iteritems():
            values = [v for v in values if v]
            if values:
                self.arguments[name] = values


    def __getattr__(self, name):
        return getattr(self._response, name)




class route(object):
    _routes = []
    _urls = []

    def __init__(self, uris, name=None):
        if not isinstance(uris, (list, tuple)):
            uris = [uris]
        self._uris = uris
        self._name = name

    def __call__(self, handler):
        """gets called when we class decorate"""
        name = self._name or handler.__name__
        for uri in self._uris:
            self._urls.append(uri)
            self._routes.append(tornado.web.url(uri, handler, name=name))
        return handler

    @classmethod
    def get_routes(cls):
        return cls._routes

    @classmethod
    def get_urls(cls):
        return cls._urls



class UrlStatus(Const):
    new = (0, '新链接')
    pop = (1, '出管道  处理')
    nothandler = (2, '没有处理函数')
    error = (3, '处理出错')
    success = (4, '处理成功')
    
