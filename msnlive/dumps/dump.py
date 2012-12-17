#!/usr/bin/python
#coding=utf8
from outlook import OutLook

import sys
import os.path as osp
import os
import time
from datetime import datetime
from random import shuffle
#from pycomm.proc.threadbase import ThreadBase
from pycomm.proc import ThreadBase, WorkerFinishException
from pycomm import signal as mysignal
from pycomm.log import PrefixLog, log
from pycomm.utils.tracktime import DiffTime
from pycomm.utils import textfile
import threading

class Application(ThreadBase):

    def init(self):
        if self.options.account:
            self.accounts = textfile.CacheText(self.options.account, once=True)
        else:
            raise Exception("need accounts")

        self.msn_ct = 0
        self.total = 0
        self.fail_total = 0
        self.begin = DiffTime()
        self.cur = DiffTime()
        self.files = {}
        target = self.options.target or 'result'

        if not osp.exists(target):
            os.makedirs(target)

        for i in range(1, self.worker_num + 1):
            f = file('%s/emails_%s.txt' % (target, i), 'a')
            self.files[i] = f

        
    def add_options(self, parser):
        parser.add_option("-a", '--account', dest='account', action="store", help="the account file", type="string")
        parser.add_option("-t", '--target', dest='target', action="store", help="the target dir", type="string")

    def sync(self):
        diff = self.begin.get_diff()
        if diff == 0:
            return
        s = "msn_ct %s, total %s " % (self.msn_ct, self.total )
        log.error(s)
        self.accounts.sync()
        
    def work(self, name, id=0):
        try:
            account, psw = self.accounts.get(), '846266'
        except textfile.NotDataException:
            mysignal.ALIVE = False
            raise WorkerFinishException
            return
        
        self.msn_ct += 1
        msn_ct = self.msn_ct
        log.error('%d %s begin connect' % (msn_ct, account))
        app = OutLook(account, psw)
        app.login()
        for i in range(3):
            emails = app.get_contacts()
            if emails is not None:
                self.total += len(emails)
                log.trace('%s %s found emails %s total %s', msn_ct, account, len(emails), self.total)
                log.trace('%s %s found emails %s', msn_ct, account, ','.join(emails))
                
                f = self.files[id]
                f.write('\n'.join(emails))
                f.write('\n')
                f.flush()
                break



def main():
    app = Application()
    app.run()


if __name__ == '__main__':
    main()
