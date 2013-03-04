#!/usr/bin/python
#coding=utf8
import re
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "custom.settings"
import sys
sys.path.insert(0, os.path.dirname('../../'))
from pycomm.libs.spider import ResponseHandler, route
from urlparse import urlparse


def get_raw_img(path):
    return re.sub('_t_\d+_\d+', '', path)


def get_img_path(path):
    raw_img = get_raw_img(path)
    return urlparse(raw_img).path


def get_id(path):
    return re.findall('\d+$', path)[0]


def get_img_url(path):
    raw_img = get_raw_img(path)

    yield raw_img
    ext = raw_img.rsplit('.', 1)[-1]
    for s in ['75', '150', '500']:
        yield raw_img.replace('.%s' % ext, '_t_%s_%s.%s' % (s, s, ext))


@route(['(/.*\.jpg)', '(/.*\.gif)', '(/.*\.png)'])
class LoadImage(ResponseHandler):
    def parse(self, path):
        if self.response.body.find('Controller file error') != -1:
            return
        filename = urlparse(self.response.url).path
        filename = 'img' + filename
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)

        file(filename, 'wb').write(self.response.body)
        return
