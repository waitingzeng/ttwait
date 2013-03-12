#!/usr/bin/python
#coding=utf8
from .utils import UrlStatus, Result
from pycomm.utils.escape import json_encode, json_decode
from pycomm.log import log


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

    def push_url(self, href, title, priority=0, **kwargs):
        pass

    def pop_url(self):
        raise StopIteration

    def exists(self, url):
        return False

    def set_status(self, url, status, msg=''):
        pass

    def next(self):
        url, kwargs = self.pop_url()
        self.set_status(url, UrlStatus.pop)
        return url, kwargs

    def get_by_url(self, url):
        return None, None

    get_url = pop_url
    get = next


class DjangoPipeline(BasePipe):
    model = None
    result_model = None

    def get_spider_url(self, url):
        return self.model.objects.get_or_none(url=url)

    def save_result(self, response, result):
        url = self.get_spider_url(response.url)
        if not url:
            return
        result.url_id = url.pk
        result.save()

    def push_url(self, url, title='', priority=0, **kwargs):
        if not self.model.objects.check_url_exists(url):
            self.model(url=url, title=title, priority=priority, kwargs=json_encode(kwargs)).save()
        else:
            log.debug("url %s exists", url)
        return True

    def pop_url(self):

        obj = self.model.objects.filter(status=UrlStatus.new).get_first()
        if not obj:
            raise StopIteration

        return obj.url, json_decode(obj.kwargs)

    def exists(self, url):
        return self.model.objects.filter(url=url).count()

    def set_status(self, url, status, msg=''):
        return self.model.objects.filter(url=url).update(status=status, msg=msg)

    def get_result_obj(self, response):
        url = self.get_spider_url(response.url)
        if not url:
            return None
        result, create = self.result_model.objects.get_or_create(url_id=url.pk)
        return result

    def get_by_url(self, url):
        try:
            obj = self.model.objects.get(url=url)
        except:
            return None, None
        return obj.url, json_decode(obj.kwargs)
