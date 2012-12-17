#! /usr/bin/env python
#coding=utf-8
import re
from py3rd import webpy
from pycomm.log import log

def auto_ck():
    return 'OK'

slash_remove = re.compile('([/]+)')
def auto_slash():
    path = webpy.ctx.path
    path = slash_remove.sub('/', path)
    fn, args = webpyapp._match(webpyapp.mapping, path)
    if fn and fn.__name__ != 'auto_slash':
        raise webpy.SeeOther(path)

    if path.endswith('/'):
        path = path[:-1]
    else:
        path = path + '/'
    
    fn, args = webpyapp._match(webpyapp.mapping, path)
    if fn and fn.__name__ != 'auto_slash':
        raise webpy.SeeOther(path + webpy.ctx.query)
    log.error('not path found %s', webpy.ctx.path)
    raise webpy.NotFound()

def env():
    raise