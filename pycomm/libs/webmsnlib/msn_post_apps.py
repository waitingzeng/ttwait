#! /usr/bin/env python
#coding=utf-8
from pycomm.libs.webmsnlib import msn_post
from apps import apps
from singleweb import SingleWeb
from threading import RLock
from itertools import cycle
import sys
import traceback

lock = RLock()
apps_cycle = apps.keys()
index = cycle(range(len(apps_cycle)))

def remove_appid(appid):
    with lock:
        try:
            apps_cycle.remove(appid)
        except:
            pass


class MSNPostApps(msn_post.MSNPost):
    baseurl = 'http://%s.appspot.com/msn.py?action=addfriend&sender=%s&psw=%s&to=%s'
    #baseurl = 'http://%slocalhost:9000/msn.py?action=addfriend&sender=%s&psw=%s&to=%s'
    
    
    def get_app_url(self, cid):
        if len(apps_cycle) == 0:
            raise Exception('Not Enough app')
        
        appid = apps_cycle[index.next() % len(apps_cycle)]
        return appid, self.baseurl % (appid, self.name, self.psw, cid)
    
    def add_friend(self, cid, body = '', retry=0):
        if retry > 5:
            return False
        web = SingleWeb()
        appid, url = self.get_app_url(cid)
        cookie = self.web.cookies_to_str()
        data = web.get_page(url, data={'cookie' : cookie}, muti=True)
        if not data:
            return msn_post.MSNPost.add_friend(self, cid, body)
        if data.find('required more quota') != -1:
            remove_appid(appid)
            self.error('appid:%s had limit quota, retry %d', appid, retry)
            return self.add_friend(cid, body, retry+1)
        else:
            code, s = data.split(';')
            if code == '200':
                if s == 'success':
                    return True
                elif s == 'fail':
                    return False
                elif s.endswith('Exception'):
                    cls = getattr(msn_post, s, Exception)
                    raise cls()
            self.error('unknow data appid:%s, %s retry with old', appid, data)
            return msn_post.MSNPost.add_friend(self, cid, body)
            
                
            
        
if __name__ == '__main__':
    app = MSNPostApps(sys.argv[1], '846266')
    if app.login():
        print 'login success'
    if app.add_friend(sys.argv[2]):
        print 'add success'