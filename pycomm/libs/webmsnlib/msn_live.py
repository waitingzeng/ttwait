#! /usr/bin/env python
#coding=utf-8

import httplib
import urllib
import time
import sys
from pycomm.log import log, PrefixLog, open_log, open_debug
from pycomm.singleweb import SingleWeb
from pycomm.utils import text
from pycomm.utils import html
from pycomm.utils.pprint import pprint
class DisabledException(Exception):pass
class AuthFailException(Exception):pass
class ProofException(Exception):pass

class MSNLive(object):
    APP_URL = 'http://profile.live.com/'
    DEBUG = False
    def __init__(self, name, psw):
        self.web = SingleWeb(debug = self.DEBUG)
        self.name = name
        self.psw = psw
        self.log = PrefixLog(name)

    def login(self, *args, **kwargs):
        try:
            return self._login(*args, **kwargs)
        except ProofException:
            self.log.exception('ProofException')
            self.web = SingleWeb()
            return self.login(*args, **kwargs)
        except:
            self.log.exception('login had some error')
            return False

    def do_submit(self, page):
        form = text.get_in(page, '<form name="fmHF" id="fmHF"', '</form>')
        if form is None:
            return page
        action = text.get_in(form, 'action="', '"')
        data = html.get_hidden(form)

        page = self.web.get_page(action, data, {'referer' : self.web.url})
        return page

    def get_auto_refresh_url(self, page):
        page = page.lower()
        noscript = text.get_in(page, '<noscript>', '</noscript>')
        if not noscript:
            return None
        for meta in text.get_in_list(noscript, '<meta', '/>'):
            equiv = text.get_in(meta, 'http-equiv="', '"')
            if equiv and equiv == 'refresh':
                refresh = text.get_in(meta, 'content="', '"')
                ii = refresh.find(";")
                if ii != -1:
                    pause, newurl_spec = float(refresh[:ii]), refresh[ii+1:]
                    jj = newurl_spec.find("=")
                    if jj != -1:
                        key, url = newurl_spec[:jj], newurl_spec[jj+1:]
                    if key.strip().lower() != "url":
                        continue
                else:
                    continue
                
                if pause > 1E-3:
                    time.sleep(pause)
                url = html.iso_to_char(url)
                return url
        return None

    def process_cookies(self):
        auth = self.web.get_cookies('RPSTAuth')
        if auth:
            self.web.clear_cookies()
            self.web.set_cookie_obj(auth)
            return
        return
    
    def active(self, login_page):
        file('1.html', 'w').write(login_page)
        posturl = text.get_in(login_page, '<form method="post" action="', '"')
        posturl = 'https://account.live.com/' + posturl.replace('&amp;', '&')
        data = html.get_hidden(login_page)
        data.update({
            'ctl00$ctl00$MainContent$MainContent$AccountContent$LoginMain$iPwdEncrypted' : '8rr4KG0TQcPPmWkrULn3xJHS U2M5F021LPROFYQ6GHT61TytCbZHu/tKcY1mw9FNCvRltdSdJfh0qqDFHe8cRGzG68eFqhkzufURuH5xBe2UrBq0eYLPl4ojq VakkTAgImMAaPaImBeD0ME jLgi YVXYQvoxu7ijU/fWVspk=',
        'ctl00$ctl00$MainContent$MainContent$AccountContent$LoginMain$iPublicKey' : '1BEF90811CE78A99D0820E87F3BDF1F96622EB40',
       'ctl00$ctl00$MainContent$MainContent$AccountContent$LoginWrapper$LoginRepeater$ctl00$LoginOther$iEncryptedSecretAnswer' : 'rXKB3IJ3sc6ywuheD3AMMS9Ak3qcw/rUYwULHAtQsglbKiS6nHkayn9J0NgXjgjGVdfzN MKOR58JNmOL5srv/VqQmIHPSLzo5BEpBxfdeS3mUK pU/cZZxcoVGepVRx99UcyiuC0BoTs5ehLJcXADzVnFfS6xjCyzSPLRZP2io=',
        'ctl00$ctl00$MainContent$MainContent$AccountContent$LoginWrapper$LoginRepeater$ctl00$LoginOther$iQuestion' : '母亲的出生地点',
        'ctl00$ctl00$MainContent$MainContent$AccountContent$btSubmit' : '提交',
        })
        data.pop('ctl00$ctl00$MainContent$MainContent$AccountContent$iErrors')
        pprint(data)
        page = self.web.get_page(posturl, data, {'referer' : posturl})
        
        file('3.html', 'wb').write(page)
        return page
    
    def proofs(self, result):
        data = {
            'EmailAddress' : self.name.split('@')[0] + '@yeah.net',
            'action' : 'Save',
            'DisplayPhoneCountryISO' : 'US'
        }
        page = self.web.submit(result, data, name='AddProofForm')
        
        return page
        
    
    def _login(self, to = None, login_page=None):
            
        login_page = self.web.get_page(self.APP_URL)

        url = self.get_auto_refresh_url(login_page)
        if url and url.find('cid-') != -1:
            self.log.debug('found cid %s', url)
            return True
        
        if url:
            login_page = self.web.get_page(url)

        post_url = text.get_in(login_page, "urlPost:'", "'")
        log.debug('get post_url %s', post_url)
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
                
        
        url = self.get_auto_refresh_url(result)
        if url is None:
            log.debug('get_auto_refresh_url fail, cururl is %s', self.web.url)
            return False
        if url.find('profile.live.com/') != -1:
            self.process_cookies()
            return True
        if self.web.url.lower().find('jsDisabled.srf') != -1:
            if result.find('action="https://security.live.com') != -1:
                self.log.error('Disable')
                raise DisabledException
            else:
                self.log.error('Auth Fail')
                raise AuthFailException
        else:
            self.log.debug('can not find profile.live.com %s', url)
        return False
    
    
    def get_page(self, *args, **kwargs):
        res = self.web.get_page(*args, **kwargs)
        return self.auto_refresh(res)
        
    def auto_refresh(self, res):
        if res is None:
            return None
        lower_res = res.lower()
        if lower_res.find('onload="javascript:dosubmit();"') != -1:
            return self.web.submit(res)
        
        url = self.get_auto_refresh_url(lower_res)
        if url:
            res = self.get_page(url)
        return res
        

def test():
    import httplib
    httplib.HTTPConnection.debuglevel = 1
    from optparse import OptionParser, OptionGroup
    from pycomm.log import open_debug, open_log
    open_log('MSNLIVE')
    open_debug()
    parser = OptionParser(conflict_handler='resolve')
    parser.add_option("-e", "--email", dest="email", action="store", help="the microsoft email", type="string")
    parser.add_option("-p", "--passwd", dest="passwd", action="store", help="the passwd", type="string")
    
    options, args = parser.parse_args(sys.argv[1:])
    
    if not options.email:
        parser.print_help()
        return
    MSNLive.debug = True
    app = MSNLive(options.email, options.passwd or '846266')
    if app._login():
        print 'login success'
    else:
        print 'login fail'
    
if __name__ == '__main__':
    test()
