#!/bin/env python
#coding=utf-8

from pycomm.log import log, PrefixLog
from pycomm.proc import ThreadBase
from pycomm.libs.webmsnlib.domain import DomainLive
from pycomm import signal as mysignal
from pycomm.libs.dnspod import DnsPod, RecordType
from pycomm.utils.dict4ini import DictIni
from pycomm.utils import text
from pycomm.libs.rpc import MagicClient
from pyquery import PyQuery as pq

import httplib
import time
import sys
import os
import threading
from datetime import datetime



class Application(ThreadBase):
    
    def init(self):
        
        self.dnspod = DnsPod(self.conf.dnspod.user, self.conf.dnspod.psw)
        self.dnspod.domain_list()
        domain = DictIni(self.conf.domain_conf)
        domain = domain[self.name]
        if not domain:
            log.error("%s Domain Doest not Exists", self.name)
            sys.exit(-1)

        self.domain = domain.domain
        self.account = domain.account
        self.psw = domain.psw
        self.names = text.CacheFile('data/names.txt')
        self.domain_fail = 0
        self.app = DomainLive(self.account , self.psw, dnspod=self.dnspod)
        self.begin() 

    def begin(self):
        log.error('begin login %s', self.app.name)
        if not self.app.login():
            log.error("%s login fail", self.app.name)
            raise Exception('%s login fail' % self.app.name)
        log.error("login success")
        
        p = 'create'
        if not os.path.exists(p):
            os.makedirs(p)
        
        self.out = file('%s/%s_%s.txt' % (p, self.name, datetime.today().strftime('%y%m%d')), 'a')
        self.doamin_ct = {}
        if self.conf.account_server:
            self.client = MagicClient(self.conf.account_server[0], int(self.conf.account_server[1]))
        else:
            self.client = None
    
    def add_options(self, parser):
        parser.add_option("-n", '--name', dest='name', action="store", help="the domain alias name require", type="string")


    def process_options(self, options, args):
        self.name = options.name
        if not self.name:
            log.error("Must Give Name")
            return True
        
    def create_one(self, full_domain):
        firstname = self.names.get()
        lastname = self.names.get()
        name = text.rnd_str(3)
        ct = self.doamin_ct[full_domain]
        if self.app.add_account(full_domain, name, lastname, firstname):
            self.total += 1
            ct += 1
            acc = '%s@%s' % (name, full_domain)
            log.error("success %s %s total:%s" % (acc, ct, self.total))
            #with self.lock:
            self.out.write('%s\n' % acc)
            self.out.flush()
            if self.client:
                try:
                    self.client.add_account(acc)
                except:
                    log.exception("add_account fail")
                    time.sleep(3)

            self.doamin_ct[full_domain] += 1
            
            return True
        else:
            log.error("fail %s@%s %s total:%s" % (name, ct, full_domain, self.total))
            return False
            
        
    def create_domain_accounts(self, full_domain):
        num = self.app.domains.get(full_domain, 0)
        #if num == -1:
        #    return
        fail = 0
        while num < 500 and mysignal.ALIVE and fail < 10:
            if self.create_one(full_domain):
                num += 1
                fail = 0
            else:
                fail += 1
    
    def create_domain(self):
        while mysignal.ALIVE:
            res = self.app.add_domain(self.domain)
            if res:
                return res
            log.error("add domain error")
            self.domain_fail += 1
            if self.domain_fail > 10:
                with self.lock:
                    if self.domain_fail < 10:
                        return

                    self.app = DomainLive(self.account , self.psw, dnspod=self.dnspod)    
                    if not self.app.login():
                        log.error("login fail")
                        return
                    self.domain_fail = 0
                    log.error("login success")
                
        return None
    
    
    def sync(self):

        self.out.flush()
    
    def work(self, name, id):
        sub_domain = self.create_domain()
        if not sub_domain:
            return
        full_domain = '%s.%s' % (sub_domain, self.domain)
        log.error("begin create accounts for %s" % full_domain)
        self.doamin_ct[full_domain] = 0
        self.create_domain_accounts(full_domain)
        del self.doamin_ct[full_domain]


def main():
    app = Application()
    app.run()


if __name__ == '__main__':
    main()
