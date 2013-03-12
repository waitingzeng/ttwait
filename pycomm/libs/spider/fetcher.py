#!/usr/bin/python
#coding=utf8
from tornado.httpclient import HTTPClient


def default_fetcher(spider, *args, **kwargs):
    client = HTTPClient()
    return client.fetch(*args, **kwargs)
