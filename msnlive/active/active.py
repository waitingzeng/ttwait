#!/bin/env python
#coding=utf-8
from pycomm.proc import ThreadBase, WorkerFinishException
from pycomm.log import log, PrefixLog, open_debug
from pycomm.utils import text, html
from pycomm.libs.rpc import MagicClient
from pycomm.libs.webmsnlib import msn_live
from pprint import pprint
import time
import sys
import os
import urllib
from pycomm.singleweb import SingleWeb

class ProofException(Exception):
    pass

class OutLook(msn_live.MSNLive):
    APP_URL = 'https://profile.live.com/'

    def login(self):
        login_page = self.web.get_page(self.APP_URL)

        url = self.get_auto_refresh_url(login_page)
        if url and url.find('cid-') != -1:
            self.log.debug('found cid %s', url)
            return True
        
        if url:
            login_page = self.web.get_page(url)

        post_url = text.get_in(login_page, "urlPost:'", "'")
        #log.debug('get post_url %s, url %s', post_url, self.web.url)
        if not post_url:
            return False
        data = html.get_hidden(login_page)
        data.update({'login' : self.name,
                'passwd' : self.psw,
                'NewUser' : '1',
                
        })
        #self.log.debug('get post data %s', data)
        #req = urllib2.Request(url, data=data, headers=headers)
        result = self.web.get_page(post_url, data=data, headers={'referer' : self.web.url})
        if result is None:
            self.log.debug('post %s is_name', post_url)
            return False
        
        if result.find('onload="javascript:DoSubmit();"') != -1:
            result = self.web.submit(result)
        
        #ret = self.proof(result)
        #if ret:
        #    raise ProofException()
        if self.web.url.find('Logincredprof.aspx') != -1:
            #self.log.debug('into active account')
            result = self.active(result)
            if result is None:
                self.log.debug('active account fail')
                return False
            if self.web.url.find('Logincredprof.aspx') == -1:
                self.log.trace("active success")
                return True
            self.log.trace("active fail got url %s", self.web.url)
        return True

    def active(self, login_page):
        posturl = text.get_in(login_page, '<form method="post" action="', '"')
        posturl = 'https://account.live.com/' + posturl.replace('&amp;', '&')
        data = html.get_hidden(login_page)


        data.update({
            '__EVENTTARGET' : '',
            'ctl00$ctl00$MainContent$MainContent$AccountContent$LoginMain$iPwdEncrypted' : 'afvTFRcnT7hEK2A1CQg9lYHtxmOSKF9o7cbm1pVUmL0vGiWz7FPKuZTTOHyf6hLFdG8y7sflCefQiCgU5IefiI6unwC+B6502BweGR8+7HE+Zu3Mm8UAECa4ZJ5ij/Mr0zzetzuq1E4sKqzy4IXbZLnAaomAI4J4ti3yvq1hlJA=',
            'ctl00$ctl00$MainContent$MainContent$AccountContent$LoginMain$iPublicKey' : '1BEF90811CE78A99D0820E87F3BDF1F96622EB40',
            'ctl00$ctl00$MainContent$MainContent$AccountContent$LoginWrapper$LoginRepeater$ctl00$LoginOther$iEncryptedSecretAnswer' : 'ZWmr8HXra02k0yizc09c5BES6p8RgW7evH3LmtZE9GJRibebShlE2ABH95b8/zva0dXY0v32XhvnsWolTZqfXPKwcoC1ONTadeBTWlLnqlzgU78P4OT2jjWx2rHhwrbVlvkYPP3J9QomBbf8uigVI/739HTw+Fvx8TbkoNWZGFA=',
            'ctl00$ctl00$MainContent$MainContent$AccountContent$LoginWrapper$LoginRepeater$ctl00$LoginOther$iQuestion' : '母亲的出生地点',
            'ctl00$ctl00$MainContent$MainContent$AccountContent$btSubmit' : '接受',
        })
        data.pop('ctl00$ctl00$MainContent$MainContent$AccountContent$iErrors')
        page = self.web.get_page(posturl, data, {'Origin': 'https://account.live.com'})

        return page

    def into_profile(self):
        self.web.get_page(self.APP_URL)
        if self.web.url.startswith(self.APP_URL):
            cid = text.get_in(self.web.url, 'cid-', '/')
            if cid:
                self.web.get_page('%sP.mvc#!/cid-%s/' % (self.APP_URL, cid))



    def proof(self, result=None):
        if not result:
            result = self.web.get_page(self.APP_URL)
        print self.web.url
        if self.web.url.startswith(self.APP_URL):
            return True
        if self.web.url.startswith('https://account.live.com/Proofs/Manage'):
            data = {
                'EmailAddress' : '',
                'action' : 'save',
                'DisplayPhoneCountryISO' : 'US'
            }
            page = self.web.submit(result, data, name='AddProofForm')
            #file('before.html', 'w').write(page)
            if self.web.url.startswith(self.APP_URL):
                return True
            return page
        return False
        

class Application(ThreadBase):
    def init(self):
        self.pjs = self.conf.pjs
        #open_debug() 
        self.client = MagicClient(self.conf.account_server[0], int(self.conf.account_server[1]))
        self.next = self._next()
    

    def _next(self):
        while True:
            try:
                ret = self.client.get_new_account()
            except:
                log.exception("get_new_account fail")
                time.sleep(5)
                continue
            if not ret:
                time.sleep(5)
                continue
                break
            yield ret

    def work_py(self, name, id=0):
        with self.lock:
            try:
                email = self.next.next()
            except StopIteration:
                raise WorkerFinishException

        app = OutLook(email, '846266')
        
        try:
            res = app.login()
            if res:
                app.into_profile()
                #app = OutLook(email, '846266')
                #app.login()
                #if app.proof():
                log.trace('%s active success', email)
                self.client.add_account(email, 1)
        except ProofException:
            log.trace('%s active success', email)
            self.client.add_account(email, 1)
        except:
            time.sleep(2)


    def work_js(self, name, id=0):
        with self.lock:
            try:
                email = self.next.next()
            except StopIteration:
                raise WorkerFinishException
        cmd = '%s active.js %s' % (self.pjs, email) 
        res = os.system(cmd)
        res = res / 256
        log.trace('%s active %s %s', name, email, res)
        res = int(res)
        try:
            if res == 0:
                self.client.add_account(email, 1)
            elif res == 2:
                self.client.add_account(email, -1)
        except:
            time.sleep(2)

        #time.sleep(2)
    work = work_js

def main():
    app = Application()
    app.run()

def test():
    open_debug()
    app = OutLook(sys.argv[1], '846266', 1)
    print app.login()
    print app.login()
    
if __name__ == '__main__':
    main()
