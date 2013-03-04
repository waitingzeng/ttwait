#!/usr/bin/python
#coding=utf8

from django.db import models

from pycomm.libs.spider.models import SpiderUrlsBase
from pycomm.libs.spider.pipeline import DjangoPipeline

# Create your models here.


class CustomGoodsSpiderUrls(SpiderUrlsBase):
    pass


class ArtSpiderUrls(SpiderUrlsBase):
    pass


class BGSpiderUrls(SpiderUrlsBase):
    pass


class FontSpiderUrls(SpiderUrlsBase):
    pass


class CustomProductSpiderUrls(SpiderUrlsBase):
    pass

