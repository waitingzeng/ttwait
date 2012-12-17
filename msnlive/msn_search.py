#! /usr/bin/env python
#coding=utf-8
from itertools import cycle
import threading
import urllib2
import mysignal
import re

class BaseSearch(object):
    def load_index(self, filename):
        return [x.strip() for x in file(filename) if x.strip()]
    
    def __call__(self, *args, **kwargs):
        return self.search(*args, **kwargs)
    

class AppSearch(BaseSearch):
    baseurl = 'http://%s.appspot.com/live.py?ids=%s'
    testurl = 'http://127.0.0.1:9000/live.py?ids=%s'
    def __init__(self):
        from apps import apps
        self.apps_cycle = apps.keys()
        self.index = cycle(range(len(self.apps_cycle)))
        self.lock = threading.RLock()
        
    def get_app_url(self, cid):
        if len(self.apps_cycle) == 0:
            raise Exception('Not Enough app')
        
        appid = self.apps_cycle[self.index.next() % len(self.apps_cycle)]
        url = self.baseurl % (appid, cid)
        #url = self.testurl % cid
        return appid, url
        
    def remove_appid(self, appid):
        with self.lock:
            try:
                self.apps_cycle.remove(appid)
            except:
                pass
        
    
    def search(self, cid):
        appid, url = self.get_app_url(cid)
        print url
        try:
            data = urllib2.urlopen(url).read()
            if data.find('required more quota') != -1:
                self.remove_appid(appid)
                return self.search(cid)
            
            code, mail = data.split(';')
            if code == '404':
                return []
            res = mail.split('\n')
            return [x.strip() for x in res if x.strip()]
        except urllib2.HTTPError, info:
            if info.code == 404:
                self.remove_appid()
                return self.search(cid)
        except:
            pass
        return []



class NormalSearch(BaseSearch):
    baseurl = 'http://profile.live.com/cid-%s/friends/all/'
    CID_RE = re.compile(r'cid\-([\d\w]{16})', re.I)
    
    def get_page(self, url):
        for i in range(3):
            try:
                return urllib2.urlopen(url).read()
            except:
                pass
        return None
    
    def get_name_list(self, content):
        names = {}
        if content:
            namelist = self.CID_RE.findall(content)
            for name in namelist:
                names[name] = 1
        return names.keys()
    
    
    def search(self, cid):
        names = {}
        url = self.baseurl % cid
        content = self.get_page(url)
        if content is None:
            return []
        return self.get_name_list(content)
    
        
        
if __name__ == '__main__':
    search = AppSearch()
    print '\n'.join(search('01c7fe8770732179'))