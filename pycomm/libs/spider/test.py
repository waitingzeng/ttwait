#!/usr/bin/python
#coding=utf8

from pycomm.libs.spider import ResponseHandler, BasePipe, route, Result, Spider
from pyquery import PyQuery as pq
from pycomm.log import open_debug

open_debug()

class MemeryPipe(BasePipe):
    def __init__(self, start_urls=[]):
        self._urls = start_urls

    def push_url(self, url):

        self._urls.append(url)

    def pop_url(self):
        if not self._urls:
            raise StopIteration
        return self._urls.pop(0)

    def save_result(self, response, result):
        print result

@route('/products/1316-1381-1392(.*).html')
class Index(ResponseHandler):
    def parse(self, suburl):
        for a in pq(self.response.body).find('a'):
            href = pq(a).attr('href')
            if not href:
                continue
            if href.startswith('1316-1381-1392'):
                yield href
        #yield Result(content=self.response.body)



pipeline = MemeryPipe(['http://www.360buy.com/products/1316-1381-1392.html'])
spider = Spider(pipeline)

spider.run()
