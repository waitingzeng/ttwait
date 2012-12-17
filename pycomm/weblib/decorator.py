#! /usr/bin/env python
#coding=utf-8
import time
import json

from py3rd import webpy
from pycomm.weblib.hooks.session import create_session
from pycomm.weblib.hooks.debug import _processor as debug_processor, check_debug
from pycomm.weblib.hooks.profile import _processor as profile_processor
from pycomm.utils.decorators import decorator
from pycomm.log import log

def session(method):
    def _wrap(self, *args, **kwargs):
        if webpy.ctx.get('session', None) is None:
            create_session()
            self.session = webpy.config._session
            self.session.setdefault('msgs', [])            
            return self.session._processor(lambda : method(self, *args, **kwargs))
        return method(self, *args, **kwargs)
    return _wrap


def debug(method):
    def _wrap(self, *args, **kwargs):
        self.uin, self.is_debug = check_debug()
        return debug_processor(lambda : method(self, *args, **kwargs))
    return _wrap


def profile(method):
    def _wrap(self, *args, **kwargs):
        return profile_processor(lambda : method(self, *args, **kwargs))
    return _wrap


def jsonresp(method):
    def _wrap(self, *args, **kwargs):
        webpy.header('content-type','text/json;charset=utf-8', unique=True)
        
        data = method(self, *args, **kwargs)
        if isinstance(data, int):
            data = {'ret' : data}
        if not data:
            data = {'ret' : 500}
        data.setdefault('ret', 0)
        data.setdefault('time', int(time.time()))
        if data['ret'] != 0:
            log.debug("jsonresp::%s ret %s", webpy.ctx.fullpath, data['ret'])
        return json.dumps(data)
    return _wrap

@decorator
def xmlheader(method, self, *args, **kwargs):
	webpy.header('content-type','text/xml;charset=utf-8')
	return method(self, *args, **kwargs)
