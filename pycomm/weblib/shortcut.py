#! /usr/bin/env python
#coding=utf-8
import os
import os.path as osp
from pycomm.log import log
from pycomm.utils.pprint import pprint
from pycomm.utils.dict4ini import DictIni
from pycomm.utils.decorators import decorator
from pycomm.tools.track_time import TrackTime
from pycomm.weblib.hooks import profile
from py3rd import webpy



def collect_app(prefix, app):
    newurls = []
    for pat, what in app.mapping:
        newurl = '%s%s' % (prefix, pat)
        if isinstance(what, webpy.application):
            newurls.extend(collect_app(newurl, what))
        else:
            newurls.extend([newurl, what])
    return newurls

def collect_urls(urls):
    urls = webpy.utils.group(urls, 2)
    newurls = []
    for pat, what in urls:
        if isinstance(what, webpy.application):
            newurls.extend(collect_app(pat, what))
        else:
            newurls.extend([pat, what])
    
    return tuple(newurls)


def install_hooks(app, settings=None):
    if not hasattr(app, 'hooks'):
        app.hooks = {}
    for hook in settings.hooks:
        func = __import__(hook, fromlist=True)
        if func.__name__ not in app.hooks:
            func.create_hook(app)



def debug_server(app):
    from pycomm.log import open_debug
    open_debug()
    from pycomm.utils.autoreload import main
    webpy.config.debug = True
    if isinstance(app, webpy.application):
        main(app.run)
    else:
        main(lambda:webpy.wsgi.runwsgi(app))


def open_conf(path):
    if not osp.exists(path):
        config = DictIni()
        config.DEBUG = 1
        config.hooks = ['web.lib.hooks.session', 'web.lib.hooks.profile', 'web.lib.hooks.debug']
        #raise Exception("Can Not Found Settings %s" % conf_path)
        return config
    
    return DictIni(path)

@decorator
def application(wsgi, *args, **kwargs):
    begin_bg_stat()
    TrackTime.clear()
    T = TrackTime('Do')
    for item in wsgi(*args, **kwargs):
        yield item
    T.stop()
    TrackTime.track()
