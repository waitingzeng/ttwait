#!/usr/bin/python
#coding=utf8
from .utils import UrlStatus, Result

class BasePipe(object):

    def __init__(self, starturls):
        for url in starturls:
            self.push_url(url, 'starturl')

    def init(self):
        pass

    def get_result_obj(self, response):
        return Result()

    def save_result(self, response, result):
        pass

    def push_url(self, href, title, priority=0):
        pass

    def pop_url(self):
        raise StopIteration

    def exists(self, url):
        return False

    def set_status(self, url, status, msg=''):
        pass

    def next(self):
        url = self.pop_url()
        self.set_status(url, UrlStatus.pop)
        return url

    get_url = pop_url
    get = next


