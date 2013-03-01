#!/usr/bin/python
#coding=utf8
import urlparse
from tornado import httpclient
from pycomm.log import log, PrefixLog
from pycomm.utils.decorator import decorator
import re
from tornado.util import b, bytes_type, import_object, ObjectDict, raise_exc_info
from tornado.web import URLSpec
from .parser import Parser, ResponseHandler, NotFoundHandler
from .utils import Result, route, UrlStatus, Url, Response
from .pipeline import BasePipe
import traceback
from pycomm.proc import ThreadBase, WorkerFinishException


class Spider(ThreadBase):
    request_default = {
        'connect_timeout' : 20,
        'request_timeout' : 20,
    }
    

    default_fetcher = httpclient.HTTPClient().fetch

    def __init__(self, pipeline, parser=None, fetcher=None, max_running=1000, name='spider', **kwargs):
        if parser is None:
            parser = Parser(route.get_routes())
        self._parser = parser
        self._parser.spider = self
        self._parser.pipeline = pipeline
        self.pipeline = pipeline
        self.max_running = max_running
        self.fetcher = fetcher or self.default_fetcher
        self.running = False
        self.runnings = 0
        self.name = name
        self.log = PrefixLog(name)

    def init(self):
        self.pipeline.init()

    def parse(self, url, **kwargs):
        try:
            response = self.fetcher(url, **self.request_default)
        except Exception, info:
            status = UrlStatus.error
            self.pipeline.set_status(url, status, info)
            self.log.trace("url %s set_status %s[%s]", url, status, UrlStatus.attrs[status])
            self.log.exception()
            return

        if response.error:
            self.log.error("req %s fetch error %s", response.error)

        response = Response(response)
        info = ''
        try:
            for r in self._parser(response, **kwargs):
                if isinstance(r, Result):
                    self.log.trace("url %s start result %s", url, r)
                    self.pipeline.save_result(response, r)
                elif isinstance(r, Url):
                    if r.skip:
                        self.log.debug("url %s skip %s", url, r.href)
                        continue

                    self.log.debug("url %s push url %s", url, r.full_url)
                    self.pipeline.push_url(r.full_url, r.title, r.priority, **r.kwargs)

            status = UrlStatus.success
        except NotFoundHandler:
            status = UrlStatus.nothandler
        except Exception, info:
            status = UrlStatus.error
            info = traceback.format_exc()
            self.log.exception()
            raw_input('error')

        self.pipeline.set_status(url, status, info)
        self.log.trace("url %s set_status %s[%s]", url, status, UrlStatus.attrs[status])

    def run_one(self, url, **kwargs):
        if not self._parser.find_handler(url):
            status = UrlStatus.nothandler
            self.pipeline.set_status(url, status)
            self.log.trace("url %s set_status %s[%s]", url, status, UrlStatus.attrs[status])
            return

        self.runnings += 1

        self.log.trace("begin parse url %s", url)

        self.parse(url, **kwargs)

    def run_test(self, options, args):
        for arg in args:
            self.pipeline.push_url(arg, arg)
            self.run_one(args[0])

    def work(self, name, id):
        with self.lock:
            try:
                url, kwargs = self.pipeline.next()
            except StopIteration:
                self.log.trace("run spider finish")
                raise WorkerFinishException
        self.run_one(str(url), **(kwargs or {}))
