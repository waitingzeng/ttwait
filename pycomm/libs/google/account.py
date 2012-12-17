#! /usr/bin/env python
#coding=utf-8
from singleWeb import singleWeb
from text import getIn, escape, RndStr, getHidden, getInList
import urllib
import re
import urllib2
from storage import Storage
import sys
from httplib import HTTPConnection
HTTPConnection.debuglevel = 0


class GoogleAccount(object):
    DEBUG = False
    domain = 'gmail.com'
    loginUrl = 'https://appengine.google.com'
    loginPostUrl = 'https://www.google.com/accounts/ServiceLoginAuth?service=ah&sig=d71ef8b8d6150b23958ad03b3bf546b7'
    loginSuccessKey = 'CheckCookie?continue='
    SendMuti = True
    URL_GMAIL = 'https://appengine.google.com/_ah/login/continue?https://appengine.google.com/&ltmpl=ae&sig=c24697718eec1be75b7ab8f8a0c02416'
    ACTION_TOKEN_COOKIE = "GMAIL_AT"
    def __init__(self, name, psw):
        self.web = singleWeb()
        self.name = name
        self.psw = psw
        self.params = Storage()
    
    def _buildURL(self, **kwargs):
        return "%s%s" % (self.URL_GMAIL, urllib.urlencode(kwargs))
    
    def getLoginData(self, data):
        all = getHidden(data)
        all.update({
            'Email' : self.name,
            'Passwd' : self.psw,
            'rmShown' : '0',
        })
        return all

    def _getActionToken(self):
        at = self.web.GetCookies(self.ACTION_TOKEN_COOKIE)
        if at is None:    
            params = {'search' : 'inbox',
                  'start': 0,
                  'view': 'tl',
                  }
            self.web.GetPage(self._buildURL(**params))

            at = self.web.GetCookies(self.ACTION_TOKEN_COOKIE)
        return at
    
    def checkLoginSuccess(self, respurl, result):
        if self.DEBUG:
            if result:
                file('logindebug.html', 'w').write(result)
        if self.loginSuccessKey and (result.find(self.loginSuccessKey) != -1 or respurl.find(self.loginSuccessKey) != -1):
            return True
        if self.loginBlockKey and (result.find(self.loginBlockKey) != -1 or respurl.find(self.loginBlockKey) != -1):
            return False
        return False
    
    
    def loginSuccess(self, data):
        RE_PAGE_REDIRECT = 'CheckCookie\?continue=([^"\']+)' 
        try:
            link = re.search(RE_PAGE_REDIRECT, data).group(1)
            redirectURL = urllib2.unquote(link)
            redirectURL = redirectURL.replace('\\x26', '&')
        
        except AttributeError:
            return False
        pageData = self.web.GetPage(redirectURL)
        g = getIn(pageData, 'var GLOBALS=[,,', ',,')
        if g is None:
            return False
        self.GLOBALS = eval('[%s]' % g)
        return True
    
    def login(self):
        res = self.web.GetPage(self.loginUrl)
        if res is None:
            print 'login:get %s fail' % self.loginUrl
            return False
        data = self.getLoginData(res)
        if data is None:
            return False
        res = self.web.GetPage(self.loginPostUrl, data)
        if res is None:
            print 'login:post %s fail' % self.loginPostUrl
            return False
        respurl = self.web.url
        print respurl
        if respurl.find("accounts/CheckCookie") != -1:
            url = getIn(res, 'location.replace("', '"')
            url = url.replace('\\x3d', '=').replace('\\x26', '&')
            res = self.web.GetPage(url)
        
        return self.checkLoginSuccess(respurl, res)
        
class AppengineAccount(GoogleAccount):
    domain = 'gmail.com'
    loginUrl = 'https://appengine.google.com'
    loginPostUrl = 'https://www.google.com/accounts/ServiceLoginAuth?service=ah&sig=d71ef8b8d6150b23958ad03b3bf546b7'
    loginSuccessKey = 'https://appengine.google.com'
    SendMuti = True
    URL_GMAIL = 'https://appengine.google.com/_ah/login/continue?https://appengine.google.com/&ltmpl=ae&sig=c24697718eec1be75b7ab8f8a0c02416'
    

class GroupsAccount(GoogleAccount):
    loginUrl = 'https://www.google.com/accounts/ServiceLogin?passive=true&hl=zh-CN&service=groups2&continue=https%3A%2F%2Fgroups.google.com%2F&cd=US&ssip=g3'
    loginPostUrl = 'https://www.google.com/accounts/ServiceLoginAuth'
    loginSuccessKey = 'https://groups.google.com/'
    

def test():
    app = GroupsAccount('jordandrbe@gmail.com', 'gelnds38')
    print app.login()

if __name__ == '__main__':
    test()