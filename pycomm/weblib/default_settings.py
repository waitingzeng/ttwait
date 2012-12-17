from copy import deepcopy

from pycomm.core.hostconfig import HostConfig, deep_merge
from pycomm.utils.datastructures import Storage
from pycomm.log import open_log

#from pycomm.weblib.template import render_mako
from pycomm import template
from pycomm.utils.decorators import decorator
from pycomm.utils.pprint import pprint
from pycomm.shortcuts.init_path import get_conf, get_template
from py3rd import webpy



def get_app_settings(settings, appname):
    d = deepcopy(settings)
    if appname in d:
        deep_merge(d, d[appname])
    d['APPNAME'] = appname
    return Storage(d)

def get_default_settings(default_conf='web.conf'):
    conf_path = get_conf(default_conf)

    settings = HostConfig(conf_path)
    settings = Storage(settings.dict())
    
    open_log(settings.logname, settings.loglevel)
    return settings

