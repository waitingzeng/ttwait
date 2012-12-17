#! /usr/bin/env python
#coding=gbk
from __future__ import with_statement
import urllib2
import threading
import mysignal
import time
from dict4ini import DictIni
from db.mysql import DB
import Queue
import socket
socket.setdefaulttimeout(20)
import traceback
from msnlive import MSNLive


config = DictIni('config.ini')
DEFAULT = {
    'charset': 'gbk',
    'use_unicode': False,
    'host' : config.mysql.host,
    'user' : config.mysql.user,
    'passwd' : config.mysql.passwd,
}

class NotDataException(Exception):pass

class MSNSearch(MSNLive):
    def __init__(self):
        MSNLive.__init__(self, config.search.name, config.search.psw)
        self.lock = threading.RLock()
        self.news = {}
        self.users = Queue.Queue()
        self.maxid = {}
        #self.load()
        self.tablelist = cycle('0123456789abcdef')
        self.current = self.tablelist.next()
        self.db = self.getDB()
        self.total = 0
        self.total2 = 0
    
    def getDB(self):
        try:
            return DB(config.mysql.dbname, **DEFAULT)
        except:
            return None
    
    
    def load(self, limit=10000, tryLoad=1):
        ct = 0
        while mysignal.ALIVE and ct < 16:
            ct += 1
            maxid = self.maxid.setdefault(self.current, 0)
            sql = "select id, name from user_%s where state=0 and id>%s order by id limit %s" % (self.current, maxid, limit)
            data = self.db.ExecuteAll(sql)
            if len(data):
                for user in data:
                    self.users.put(user[1])
                self.maxid[self.current] = data[-1][0]
                return
            else:
                self.current = self.tablelist.next()
            
    def getNum(self):
        #return 0
        sql = "select count(*) from user"
        return self.db.ExecuteInt(sql)
        
    
    def save(self, names, user=None, state=1):
        try:
            for name in names:
                name = name.lower().strip()
                sql = "insert ignore user_%s (name) values ('%s')" % (name[-1], name)
                self.db.Execute(sql)
                
            if user is not None:
                sql = "update user_%s set state=%s where name='%s'" % (user[-1], state, user)
                self.db.Execute(sql)
                self.total2 += 1
        except Exception, info:
            if str(info).lower().find('lost connection') != -1:
                self.db = self.getDB()
                self.save(names, user)
        
    
    def startOne(self, **kwargs):
        threadname = threading.currentThread().getName()
        print threadname, 'start'
        ct = 0
        news = self.news.setdefault(threadname, [])
        while mysignal.ALIVE:
            try:
                name = self.users.get(timeout=10)
            except Queue.Empty:
                continue
            
            appid, mail = search(name)
            if appid is None:
                print appid, 'is None'
                break
            if mail is None:
                continue
            self.total += 1
            ct += 1
            
            code, mail = mail.split(';')
            if code == '404':
                news.append((name, 4, []))
                print threadname, name, 'not found', self.total, self.total2
            elif code == '200':
                if mail:
                    mails = mail.split('\n')
                    state = 1
                else:
                    mails = []
                    state = 2
                    
                news.append((name, state, mails))
                print threadname, name, len(mails), self.total, self.total2
            elif code == '000':
                print threadname, appid, mail, name, self.total, self.total2
                if mail.find("required more quota") != -1 or mail.find('disable') != -1:
                    mylock.acquire()
                    try:
                        apps_cycle.remove(appid)
                    except:
                        pass
                    if len(apps_cycle) == 0:
                        mysignal.ALIVE = False
                    mylock.release()

            else:
                news.append((name, 3, []))
                print '%s, %s, %s' % (appid, code, name)
        
        
    def run(self):
        self.load()
        threadcount = config.search.threadcount
        for i in range(threadcount):
            h = threading.Thread(target = self.startOne, name='thread%d' % i)
            h.setDaemon(True)
            h.start()

        t = 0
        while mysignal.ALIVE and threading.activeCount() > 1:
            try:
                time.sleep(1)
            except IOError:
                mysignal.ALIVE = False
                break
            self.saveNews()
            if self.users.qsize() < 100:
                self.load()
                
                
        while True:
            a = threading.activeCount()
            print '活动线程', a
            if a <= 1:
                break
            try:
                time.sleep(1)
            except:
                pass
        self.saveNews()
        print 'all complete', self.total, self.total2


def main():
    try:
        app = MSNSearch()
        app.run()
    except:
        traceback.print_exc()
    raw_input('press any key to exit')


if __name__ == '__main__':
    print __file__
    #app = MSNSearch()
    #print app.save(['zjcy0001@taobao', 'cawha', 'xiao180180', 'diannao4444', 'nhdxl', 'zhaojjia', 'jhqjhq666@taobao', 'rayfeng007', 'jianlan123', 'gengsai', 'namito16@taobao', 'pure_kiss', 'fpf110', 'nmq123', 'quanxiuyin', 'luobote44'])
    #app.run()
    #print app.loadIndex()