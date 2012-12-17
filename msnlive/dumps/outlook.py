#!/usr/bin/python
#coding=utf8
import time
import sys
from pycomm.utils import text, html
from pycomm.log import log, open_debug, PrefixLog
from pycomm.singleweb import SingleWeb
from random import randint
import re
import socket
import urlparse
socket.setdefaulttimeout(30)

class OutLook(object):
    APP_URL = 'https://outlook.com/'
    def __init__(self, name, psw, debug=0):
        self.web = SingleWeb(debug = debug)
        self.name = name
        self.psw = psw
        self.log = PrefixLog('name %s psw %s' % (name, psw))

    def login(self):
        login_page = self.web.get_page(self.APP_URL)

        post_url = text.get_in(login_page, "urlPost:'", "'")
        log.debug('get post_url %s, url %s', post_url, self.web.url)
        if not post_url:
            return False
        data = html.get_hidden(login_page)
        data.update({'login' : self.name,
                'passwd' : self.psw,
                'NewUser' : '1',
                
        })
        self.log.debug('get post data %s', data)
        #req = urllib2.Request(url, data=data, headers=headers)
        result = self.web.get_page(post_url, data=data, headers={'referer' : self.web.url})
        if result is None:
            self.log.debug('post %s is_name', post_url)
            return False
        
        if result.find('onload="javascript:DoSubmit();"') != -1:
            result = self.web.submit(result)
        
        
        if self.web.url.find('Logincredprof.aspx') != -1:
            self.log.debug('into active account')
            result = self.active(result)
            if result is None:
                self.log.debug('active account fail')
            
        if self.web.url.find('/Proofs/Manage') != -1:
            proofs_page = self.web.submit(result)
            result = self.proofs(proofs_page)
            if result is None:
                raise ProofException()
        
        if result.find('javascript:rd();') != -1:
            return True
        return False

    def get_contacts(self):
        if not hasattr(self, 'hostname'):
            self.hostname = 'mail.live.com'

        self.web.get_page('https://%s/mail/contacts.mvc?n=%s' % (self.hostname, randint(0, 1000000)))
        schema = urlparse.urlparse(self.web.url)
        if self.web.url.find('HipLight.aspx') != -1:
            log.error("now can not load contact")
            return None

        if schema.hostname is None:
            return None
        if schema.hostname.find('mail.live.com') == -1 and schema.hostname.find('profile.live.com') == -1:
            return None

        self.hostname = schema.hostname.find('mail.live.com') == -1 and self.hostname or schema.hostname
        
        t = int(time.time())
        url = 'https://%s/mail/GetContacts.aspx?n=%s' % (self.hostname, t)
        cvs =  self.web.get_page(url)
        if self.web.url.find('GetContacts') == -1:
            log.error("now can not load contact")
            return None
        emails = set()
        if cvs:
            for item in text.get_in_list(cvs, '"', '"'):
                if item.find('@') != -1:
                    emails.add(item.strip())
        return list(emails)


def test():
    open_debug()
    app = OutLook(sys.argv[1], '846266', 1)
    app.login()
    #    print 'login success'
    for i in range(3):
        res = app.get_contacts()
        if res is not None:
            break
        print res
    #else:
    #    print 'login fail'

if __name__ == '__main__':
    test()
