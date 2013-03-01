#!/usr/bin/python
#coding=utf8

from django.db import models

from pycomm.libs.spider.models import SpiderUrlsBase
from pycomm.libs.spider.pipeline import DjangoPipeline

# Create your models here.


class CustomGoodsSpiderUrls(SpiderUrlsBase):
    class Meta:
        verbose_name = 'customdropshipping'
        verbose_name_plural = verbose_name


class CustomGoodsPipeline(DjangoPipeline):
    model = CustomGoodsSpiderUrls
