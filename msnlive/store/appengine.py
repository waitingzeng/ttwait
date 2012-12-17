#! /usr/bin/env python
#coding=utf-8
from dict4ini import DictIni
from itertools import cycle
import mysignal
import threading
from apps import apps
import urllib2
import logging
import traceback
import socket
socket.setdefaulttimeout(30)

class State(object):
    INIT = 0
    CHECK = 1
    NOTEXIST = 2
    EXPORT = 3

apps = apps.keys()

class Store(object):
    BATCH_SAVE_LIMIT = 20
    def __init__(self, config):
        self.config = config
        self.apps = cycle(apps)
        self.users = []
        self.lock = threading.RLock()
        self.app_len = len(apps)
        self._batchs = {}
        self.init()
        self.cache_ct = 0
        self.repeat_ct = 0
        self.save_ct = 0

    def init(self):
        for appid in apps:
            self._batchs[appid] = {}
                

    def get_appid(self, cid):
        try:
            return apps[int(cid[-2:], 16) % self.app_len]
        except:
            print cid, 'error'

    def get_page(self, url):
        print url
        try:
            res = urllib2.urlopen(url).read()
            code, body = res.split(';')
            if code != '0':
                logging.error(res)
                return None
            return body
        except:
            traceback.print_exc()
            return None

    def get_app_url(self, appid):
        #return 'http://localhost:9000/store.py'
        return 'http://%s.appspot.com/store.py' % appid

    def _save(self, cid, state=State.INIT):
        if not cid:
            return
        appid = self.get_appid(cid)
        url = '%s?action=update&obj_keys=%s&obj_value=%s' % (self.get_app_url(appid), cid, state)
        return self.get_page(url)
    
    def _batch_ready(self, cids):
        for cid in cids:
            if not cid:
                continue
            appid = self.get_appid(cid)
            if not appid:
                continue
            if cid not in self._batchs[appid]:
                self.cache_ct += 1
                self._batchs[appid][cid]= True
                #if len(self._batchs[appid]) > self.BATCH_SAVE_LIMIT:
                #    self.save_appid(appid)
            else:
                self.repeat_ct += 1
    
    def save_appid(self, appid):
        cids = self._batchs[appid]
        print 'save', appid, len(cids)
        url = '%s?action=update&obj_keys=%s&obj_value=%s' % (self.get_app_url(appid), ';'.join(cids.keys()), State.INIT)
        self.get_page(url)
        self._batchs[appid] = {}
        self.cache_ct -= len(cids)
        self.save_ct += len(cids)
        
    
    def batch_save(self, limit=BATCH_SAVE_LIMIT):
        ct = 0
        for appid, cids in self._batchs.items():
            ct += 1
            if not cids or len(cids) < limit:
                continue
            print ct, appid, self.save_appid(appid)
        return ''
    
    def _load(self, appid, state, to_state=None):
        url = '%s?action=load&obj_value=%s' % (self.get_app_url(appid), state)
        if to_state is not None:
            url = '%s&to_value=%s' % (url, to_state)
        
        res = self.get_page(url)
        if res is not None:
            return res.split('\n')
        return []

    def load(self, limit=10000, state=State.INIT, to_state=None):
        if len(self.users) > (limit / 2):
            return
        ct = 0
        while mysignal.ALIVE and ct < self.app_len:
            ct += 1
            appid = self.apps.next()
            print 'in load', ct, appid, len(self.users)
            data = self._load(appid, state, to_state)
            if len(data):
                self.users.extend(data)
                if len(self.users) >= limit:
                    return

    def export(self, filename):
        f = file(filename, 'a')
        total = 0
        for i, appid in enumerate(apps):
            while True:
                print i, appid, total
                data = self._load(appid, State.CHECK, State.EXPORT)
                if len(data):
                    total += len(data)
                    f.write('\n'.join(data))
                    f.write('\n')
                    f.flush()
                if len(data) < 1000:
                    break
        f.close()


    def get(self):
        with self.lock:
            return self.users.pop(0)

    def __len__(self):
        return len(self.users)

    def save(self, user, names=None):
        if names:
            self._batch_ready(names)
            
        if user is not None:
            if not names:
                state = State.NOTEXIST
            else:
                state = State.CHECK
            self._save(user, state)

    def __del__(self):
        self.batch_save(0)

if __name__ == '__main__':
    config = DictIni('../config.ini')
    app = Store(config)
    app.load()
    #print app.users
    #tos = file('tos_1.txt').read().split('\n')
    #for i in xrange(0, len(tos), 25):
    #    print i, app.save(None, tos[i:i+25])