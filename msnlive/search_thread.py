#! /usr/bin/env python
#coding=utf-8
from threadbase import ThreadBase
from store.filesystem import Store
import threading
from log import setup_date_log
import logging
from msn_search import AppSearch, NormalSearch
import mysignal
from dict4ini import DictIni
import time
import traceback


class SearchThread(ThreadBase):
    def __init__(self, config, dbcls=Store, searchcls = AppSearch):
        ThreadBase.__init__(self, config.threadcount, 1, 3)
        self.db = dbcls(config)
        self.search = searchcls()
        self.log_path = config.log_path
        self.log_level = config.log_level or 10

    def begin(self):
        setup_date_log('', self.log_path, self.log_level)
        self.total = 0
        self.search_num = 0
        self.news = []
        self.db.load()
        if len(self.db) == 0:
            cids = self.search.load_index('cids.txt')
            self.db.save(None, cids)
        
    def end(self):
        self.sync()
        del self.db

    def info(self):
        return 'sync thread:%d check_num:%d, exists:%d, total:%d, save:%d' % (threading.activeCount(), self.search_num, self.db.exists_ct, self.total,self.db.save_ct)

    def sync(self):
        self.db.sync()
        l = len(self.news)
        logging.info('had %d need sync', l)
        while l > 0:
            try:
                user, names = self.news.pop(0)
            except:
                logging.info('save finish')
                break
            self.db.save(user, names)
            l-=1
        self.db.sync()
        logging.info(self.info())

    def start_one(self, **kwargs):
        threadname = threading.currentThread().getName()
        print threadname, 'start'
        ct = 0
        while mysignal.ALIVE:
            try:
                user = self.db.get()
            except:
                traceback.print_exc()
                logging.info('can not get user')
                time.sleep(self.wait)
                continue
            try:
                
                names = self.search(user)
                self.search_num += 1
                self.total += len(names)
                self.news.append((user, names))
                ct += len(names)
                if ct % 30 == 0:
                    print threadname, user, self.search_num, self.total, ct
            except:
                traceback.print_exc()
                


def search():
    config = DictIni('config.ini')
    app = SearchThread(config.search)
    app.run()


if __name__ == '__main__':
    search()