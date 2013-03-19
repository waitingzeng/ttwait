#!/usr/bin/python
#coding=utf8
from .utils import UrlStatus
from pycomm.utils.escape import json_encode, json_decode
from pycomm.log import log
from pycomm.libs.rpc.magicclient import MagicClient


class BasePipe(object):

    def __init__(self, starturls=[]):
        for url in starturls:
            if isinstance(url, (list, tuple)):
                url, kwargs = url
            else:
                kwargs = {}
            print url, kwargs
            self.push_url(url, 'starturl', **kwargs)

    def init(self):
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


class LevelDBPipeline(BasePipe):
    def __init__(self, db_name, db_host, db_port, *args, **kwargs):
        self.client = MagicClient(db_host, db_port)
        self.db_name = db_name
        self.ct = 0
        BasePipe.__init__(self, *args, **kwargs)

    def push_url(self, href, *args, **kwargs):
        status = kwargs.pop('status', UrlStatus.new)
        data = {
            'kwargs': kwargs,
            'status': status,
        }
        data = json_encode(data)
        self.client.set_default(self.db_name, href, data)

    def pop_url(self):
        while True:
            try:
                url, data = self.client.next(self.db_name)
                data = json_decode(data)
                if data['status'] != UrlStatus.new:
                    continue
                self.ct += 1
                return url, data['kwargs']
            except Exception, info:
                if self.ct == 0:
                    raise info

    def exists(self, url):
        return self.client.exists(self.db_name, url)

    def set_status(self, url, status, msg=''):
        data = self.client.get(self.db_name, url)
        data = json_decode(data)
        data['status'] = status
        data = json_encode(data)
        self.client.set(self.db_name, url, data)

    def next(self):
        url, kwargs = self.pop_url()
        self.set_status(url, UrlStatus.pop)
        return url, kwargs

    def get_by_url(self, url):
        try:
            data = self.client.get(self.db_name, url)
            data = json_decode(data)
            return url, data['kwargs']
        except:
            return None, None

    def save_result(self, *args, **kwargs):
        pass
