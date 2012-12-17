#! /usr/bin/env python
#coding=utf-8
from py3rd import webpy
from pycomm.log import log
from pycomm.utils.decorators import decorator

import os
import http
import urllib
from tencent_oa import oa

VERIFY_METHOD_URL_TICKET = 1
VERIFY_METHOD_COOKIE     = 2
class OALogin():
    def __init__(self):
        self.access_list = []
        self.username = ''
    
    def set_access_list(self,access_list):
        self.access_list =  access_list

    def get_access_list(self):
        return self.access_list

    def get_username(self):
        return self.username

    def _verify(self,ticket,username,verify_method,request):
        o=oa()
        ret=o.getuser(ticket)
        if ret!=0:
            log.error('oa auth fail %d' % ret)
            return -100
        log.trace('oa auth success firsttime, username %s' % username)
        if username and username!=o.username:
            log.error("oa auth fail. username %s not equal oa.username %s",username,o.username)
            return -200

        if self.access_list and o.username not in self.access_list:
            log.error('oa auth fail. %s not in access_list', o.username)
            return -300

        if verify_method == VERIFY_METHOD_URL_TICKET:
            if request:
                request.session['tof_ticket'] = ticket
                request.session['user_name'] = self.username
                #request.set_cookie('tof_ticket',ticket)
                #request.set_cookie('user_name',self.username)
            else:
                webpy.setcookie('tof_ticket',ticket)
                webpy.setcookie('user_name',self.username)

        self.userid=o.userid
        self.username=o.username
        return 0

    def _auth(self, request=None):
#        '''
#        get username and tof_ticket from cookie or from http get param.
#        If return -100, means oa verify ticket error
#        If return -200, means oa username not equals the cookie username.
#        If return -300, means the user is not valid
#        '''
#        ticket=cgi.FieldStorage().getvalue('ticket','')            
        log.trace("in request auth")
        if request:
            ticket = request.REQUEST.get('ticket', '')
            cookies = request.session
        else:
            ticket = webpy.input(ticket='').ticket
            cookies=webpy.cookies()

        if ticket:
            log.trace('in url auth ticket')
            if self._verify(ticket,None,VERIFY_METHOD_URL_TICKET,request) < 0: return -1
            else: return 0

        if cookies.get('tof_ticket'):
            log.trace('in cookies auth')
            username=cookies.get('user_name')
            ticket=cookies.get('tof_ticket')
            return self._verify(ticket,self.username,VERIFY_METHOD_COOKIE,request) 

    def auth(self, request=None):
        ret=self._auth(request)
        if ret==0:return ret
        elif ret==-1: 
            log.error("Login fail due to url ticket auth fail")
            return -1
        elif ret==-300:
            log.error('%s trying to login' % self.username)
            return -1
        
        else:
            oa_url="http://passport.oa.com/modules/passport/signin.ashx"
            title='weixin'
            if request:
                myurl = 'http://' + request.META.get('HTTP_HOST')  + request.META.get('PATH_INFO')
            else:
                myurl='http://'+http.get_host()+http.get_uri()

            url='%s?%s' % (oa_url,urllib.urlencode({'url':myurl,'title':title}))
            if request:
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(url)
            else:
                raise webpy.seeother(url)

login=OALogin()
set_access_list=login.set_access_list
get_access_list=login.get_access_list
get_username   =login.get_username

@decorator
def oa_login_required(f,*args,**kw):
    if login.auth()==0:
        log.trace("%s Auth end. " % (login.username))
        return f(*args,**kw)
    else:
        return "Sorry, You have no right to open this web. "

   
