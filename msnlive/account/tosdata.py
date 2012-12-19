#!/usr/bin/python2.7
#coding=utf8
import glob
import os
import os.path as osp
import random
from pycomm.log import log
from pycomm.utils.accounttext import AccountNotMemery, NotDataException

class TosData(object):
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.cur_tos = 'tos'
        self.cur_dir = osp.abspath('.')
        self.ct = 0
        try:
            self.tos = AccountNotMemery(self.cur_tos)
        except:
            self.init_tos_data()

    def init_tos_data(self):
        
        os.chdir(self.data_dir)
        tos_files = glob.glob('tos_*.txt')
        if not tos_files:
            log.trace('not find tos files, need to un tgz')
            for tgzfile in glob.glob('tos_*.txt.tgz'):
                os.popen('tar xzvf %s' %  tgzfile).read()
                log.info("init_tos_data untgz tos %s", tgzfile)
        
        tos_files = glob.glob('tos_*.txt')
        if not tos_files:
            log.error("not found any tos file")
            raise NotDataException
        
        f = random.choice(tos_files)
        cmd = "mv %s %s.txt" % ( f, self.cur_tos)
        os.popen(cmd).read()
        log.trace(cmd)
        try:
            os.unlink('%s.info' % (self.cur_tos))
        except:
            pass
        os.chdir(self.cur_dir)
        self.tos = AccountNotMemery(self.cur_tos)


    def next(self):
        
        try:
            ret = self.tos.get()
            self.ct += 1
            if self.ct > 10000:
                self.sync()
                self.ct = 0
            return ret
        except:
            self.init_tos_data()
            return self.tos.get()
    get = next

    def sync(self):
        self.tos.sync()


def test():
    from pycomm.log import open_log, open_debug
    open_debug()
    app = TosData()
    print app.next()
    app.sync()

if __name__ == '__main__':
    test()
