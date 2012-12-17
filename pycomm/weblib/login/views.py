#! /usr/bin/env python
#coding=utf-8
import os.path as osp
import os
import urlparse
import urllib
import sys
from base import BaseRequest
from py3rd import webpy
from pycomm.log import log
from decorator import login_required, ptlogin_check

def get_referer(referer):
    if not referer:
        return '/'
    referer = urllib.unquote_plus(referer)
    homedomain = webpy.ctx.homedomain
    normal_uri = urlparse.urljoin(homedomain, referer)
    print normal_uri, homedomain, normal_uri.startswith(homedomain)
    if not normal_uri.startswith(homedomain):
        raise webpy.BadRequest()
    return referer

class Login(BaseRequest):
    def GET(self):
        ret = self.input.get_int('ret')
        uri = get_referer(self.input.get('referer'))
        if ret == 0:
            ret, pt_user_info = ptlogin_check()
            if ret == 0:
                webpy.seeother(uri)

        redirect = '%s/login/check/?referer=%s' % (webpy.ctx['homedomain'], urllib.quote_plus(uri))
        log.info('login check ret:%s, referer:%s', ret, uri)
        return self.render('login.html', redirect = redirect, appid = self.settings.ptlogin.app_id, type=ret)

class LoginCheck(BaseRequest):
    def GET(self):
        uri = get_referer(self.input.get('referer'))
        ret, pt_user_info = ptlogin_check()

        log.error("ptlogin check ret, ret[%s]", ret)
        if ret == 0:
            log.error("login check %s", uri)
            raise webpy.seeother(uri)
        else:
            raise webpy.seeother('/login/')

class Logout(BaseRequest):
    #@login_required
    def GET(self):
        webpy.setcookie('skey', '', -1, 'qq.com')
        webpy.setcookie('lskey', '', -1, 'qq.com')
        uri = get_referer(self.input.get('referer'))
        raise webpy.seeother('/login/?referer=%s' % urllib.quote_plus(uri))

