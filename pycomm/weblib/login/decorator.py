#! /usr/bin/env python
#coding=utf-8
from py3rd import webpy
from pycomm.log import log
from pycomm.login import ptlogin
from pycomm.utils.decorators import decorator
from pycomm.utils.pprint import pprint
from pycomm.weblib.base_request import client_ip
from base import BaseRequest

import urllib
import urlparse
import json

debug_uins = {}
only_debug_uin = 0

def load_debug_uins(filename):
    for uin in file(filename):
        try:
            uin = int(uin)
            debug_uins[uin] = 1
        except:
            pass

def set_only_debug_uin(val = True):
    global only_debug_uin
    only_debug_uin = bool(val)

def get_cookie_uin(cookies=None):
    if cookies is None:
        cookies = webpy.cookies()

    uin = cookies.get('uin', None)
    if not uin:
        return None
    try:
        uin = int(uin[1:])
    except:
        return None
    return uin

def ptlogin_check():
    cookies = webpy.cookies()
    remote_ip = client_ip()
    uin = get_cookie_uin(cookies)
    if not uin:
        log.info('not uin in cookies, ip:%s', remote_ip)
        return 2, None
    
    if only_debug_uin and uin not in debug_uins:
        return 4, None
    # check uin is legal or not

    skey = cookies.get('skey', None)
    if not skey:
        log.info('%s not skey in cookies', uin)
        skey = cookies.get('lskey', None)
        if not skey:
            log.info('%s has not lskey in cookies', uin)
            return 2, None

    pt_user_info = ptlogin.check("0.0.0.0", uin=uin, user_ip=remote_ip, szkey=skey, option=1, **BaseRequest.SETTINGS.ptlogin)
    if not pt_user_info:
        log.error("ptlogin check fail %s", BaseRequest.SETTINGS.ptlogin)
        return 3, None

    webpy.ctx.uin = uin
    return 0, pt_user_info

def is_debug():
    uin = webpy.ctx.get('uin', 0)
    return uin and uin in debug_uins

def login_required_url(login_url):
    @decorator
    def login_required(viewfunc, self, *args, **kwargs):
        """ login check decorator for views
        """
        ret, pt_user_info = ptlogin_check()
        if ret == 0:
            self.pt_user_info = pt_user_info
            return viewfunc(self, *args, **kwargs)
        uri = webpy.ctx.env.get('REQUEST_URI')
        referer = urllib.quote_plus(uri)
        raise webpy.seeother(login_url % {'referer' : referer})
    return login_required

login_required = login_required_url('/login/?referer=%(referer)s')
    

@decorator
def login_required_ajax(viewfunc, self, *args, **kwargs):
    """ login check decorator for views
    """
    ret = ptlogin_check_for_mobile()
    if ret == 0:
        return viewfunc(self, *args, **kwargs)
    return -1

