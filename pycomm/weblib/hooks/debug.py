#! /usr/bin/env python
#coding=utf-8
import os.path as osp
import sys
from py3rd import webpy
import time
from pycomm.shortcuts import get_conf
from pycomm.utils.pprint import pformat
from pycomm.log import log
from pycomm.utils.decorators import get_std_output

debug_auth_file = get_conf('debugauthuser.list')

debug_users = dict([(int(x.strip()), 1) for x in file(debug_auth_file) if x.strip()])

def check_debug():
    uin = int(webpy.cookies().get('uin', 'o0')[1:])
    is_debug = uin and uin in debug_users
    return uin, is_debug

def _processor(handler):
    begin_time = time.time()
    
    uin, is_debug = check_debug()
    if is_debug:
        res, output = get_std_output(handler)()
        runtime = time.time() - begin_time
        res += "<br/><b>Debug:</b><pre>uin:%s\nruntime:%s\n%s</pre>" % (uin, runtime, output)
        return res
    else:
        return handler()

def create_hook(app):
    app.add_processor(_processor)
