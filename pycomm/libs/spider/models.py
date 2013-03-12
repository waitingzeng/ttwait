#!/usr/bin/python
#coding=utf8

import hashlib
import urlparse

from django.db import models

from .utils import UrlStatus
from .pipeline import DjangoPipeline
from pycomm.django_apps.ext_django.manager import ModelManager


class SpiderUrlsManager(ModelManager):
    def check_url_exists(self, url):
        md5key = hashlib.md5(url).hexdigest()
        return self.filter(key=md5key).count() > 0


class SpiderUrlsBase(models.Model):
    host = models.CharField('域名', max_length=32, editable=False, db_index=True)
    key = models.CharField('md5key', max_length=32, editable=False, unique=True)
    url = models.URLField('链接', max_length=200, db_index=True)
    title = models.CharField('锚文字', max_length=1000, blank=True, default='')
    status = models.IntegerField('状态', choices=UrlStatus.attrs.items(), default=UrlStatus.new, db_index=True)
    state = models.PositiveSmallIntegerField('外部状态', editable=False, null=True, default=0, db_index=True)
    priority = models.PositiveIntegerField("优先级", default=0, db_index=True)
    msg = models.TextField('备注', blank=True)
    kwargs = models.CharField("自定义数据", max_length=200)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    objects = SpiderUrlsManager()

    class Meta:
        abstract = True
        ordering = ('-priority', 'id')

    def __unicode__(self):
        return self.url

    def save(self, *args, **kwargs):
        if not self.host:
            self.host = urlparse.urlparse(self.url).netloc.lower().split(':')[0]
        self.key = hashlib.md5(self.url).hexdigest()
        return models.Model.save(self, *args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "url__icontains",)

    @classmethod
    def pipeline(cls, *args):
        pipe =  type(cls.__name__ + 'Pipeline', (DjangoPipeline,), {'model' : cls})
        if args:
            return pipe(*args)
        return pipe


