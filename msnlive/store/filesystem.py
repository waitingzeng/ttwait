#! /usr/bin/env python
#coding=utf-8
import os
import sys
import os.path as osp
from dict4ini import DictIni
from itertools import cycle
import mysignal
import threading
import shutil
import traceback
from distinct import DistinctBase
from accounttext import AccountNotMemery, NotDataException
from datetime import datetime
import logging


class Store(object):
    DATA_NUM = 100
    DATA_NAME = 'data'
    CUR_NAME = 'cur'
    EXISTS_NAME = 'exists%s.txt'
    
    def __init__(self, data_path='.'):
        if data_path:
            self.path = data_path
        else:
            self.path = osp.dirname(osp.dirname(__file__))
            self.path = osp.join(self.path, 'filesytem')
        
        self.distinct_base = DistinctBase(osp.join(self.path, 'base'))
    
        self.save_ct = 0
        self.lock = threading.RLock()
        self.init()
        
    def init_path(self):
        self.data_path = osp.join(self.path, self.DATA_NAME)
        self.exists_path = osp.join(self.path, self.EXISTS_NAME % datetime.today().strftime('%y%m%d'))
        AccountNotMemery.BASEDIR = self.path
        self.cur_file = osp.join(self.path, '%s.txt' % self.CUR_NAME)
    
    def get_file_size(self, filename):
        with file(filename) as f:
            f.seek(0, 2)
            return f.tell()

    def init(self):
        self.init_path()
        self.data_fds = []
        if not osp.exists(self.data_path):
            os.makedirs(self.data_path)
        
        for i in range(self.DATA_NUM):
            p = osp.join(self.data_path, str(i))
            self.data_fds.append(file(p, 'a'))
        
        self.exists_fd = file(self.exists_path, 'a')
        self.exists_ct = 0
        
        self.create_cur()
        
        self.cur = AccountNotMemery(self.CUR_NAME)
        self.cur.trunk()
        
                
    def create_cur(self):
        logging.info("begin create cur")
        filenames = [f.name for f in self.data_fds]
        output = file(self.cur_file, 'a')
        num = self.distinct_base(filenames, lambda x:int(x[-2:], 16), output)
        output.close()
        for i, f in enumerate(filenames):
            self.data_fds[i] = file(f, 'w')

    def close(self):
        for f in self.data_fds:
            f.close()
        self.exists_fd.flush()
        self.sync()

    def load(self, limit=10000):
        pass

    def export(self, filename):
        pass

    def sync(self):
        self.cur.sync()
        self.exists_fd.flush()

    def get(self):
        while True:
            try:
                line = self.cur.get()
            except NotDataException:
                self.close()
                self.cur.unlink()
                self.create_cur()
                self.cur = AccountNotMemery(self.CUR_NAME)
                continue
            if not line:
                continue
            return line

    def __len__(self):
        return 99999

    def save(self, user, names=None):
        if names:
            for name in names:
                try:
                    index = int(name[-2:], 16) % self.DATA_NUM
                except:
                    traceback.print_exc()
                    continue
                self.data_fds[index].write(name)
                self.data_fds[index].write('\n')
                self.save_ct += 1

        if user is not None:
            if not names:
                return
            self.exists_fd.write(user)
            self.exists_fd.write('\n')
            self.exists_ct += 1

    def __del__(self):
        self.close()
    
if __name__ == '__main__':
    from log import setup_date_log
    setup_date_log('', None)
    config = DictIni('../config.ini')
    app = Store(config.search)
    while False:
        app.load()
        try:
            for i in app.get():
                print i
        except:
            continue
