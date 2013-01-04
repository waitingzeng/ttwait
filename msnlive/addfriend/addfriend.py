#!/bin/env python
#coding=utf-8
from gevent import monkey
monkey.patch_all()
from pycomm.log import log
from pycomm.proc import ThreadBase
from pycomm.libs.msnclass import MSN, TimeoutException
from pycomm.libs.rpc import MagicClient
from pycomm import signal as mysignal
from pycomm.utils import textfile
from pycomm.utils.tracktime import DiffTime
from pycomm.utils.textfile import NotDataException
import threading
import random
import sys
import time
from datetime import datetime

class AccountClient(object):
    func_name = 'get_add_friends'
    limit = 10000
    
    def __init__(self, *args):
        self.client = MagicClient(*args)
        self.lock = threading.RLock()
        self.data = []

    def load_thread(self):
        log.debug("begin %s", self.func_name)
        if len(self.data) >= self.limit:
            log.debug("skip %s", self.func_name)
            time.sleep(3)
            return
        try:
            data = self.load_accounts()
            if data:
                log.trace("%s load %s", self.func_name, len(data))
                self.data.extend(data)

        except:
            log.exception()
            pass


    def load_accounts(self):
        while True:
            try:
                data = getattr(self.client, self.func_name)(self.limit)
                if not data:
                    log.trace('load %s not data', self.func_name)
                    time.sleep(3)
                    continue
                break
            except:
                log.exception("%s fail", self.func_name)
                time.sleep(3)
                continue
        #file('data/%s%s.txt' % (self.func_name, datetime.now().strftime('%Y%M%d%H%m%S')), 'w').write('\n'.join(data))
        random.shuffle(data)

        if not data:
            raise Exception('Not Data Left')
        return data

    def get_rnd(self):
        return self.data.pop()

    def set_fail(self, acc):
        try:
            self.client.add_account(acc, -1)
        except:
            pass

    def update_contact(self, acc, num):
        if num == 0:
            return
        try:
            if num == 1 or num % 10 == 0:
                self.client.add_account(acc, num + 1)
        except:     
            pass

    def __nonzero__(self):
        return bool(self.data)

class TosDataClient(AccountClient):
    func_name = 'get_tos_data'

    def sync(self):
        pass

    def get(self):
        return self.get_rnd()

class Application(ThreadBase):
    
    def init(self):
        self.accounts = AccountClient(self.conf.account_server[0], int(self.conf.account_server[1])) 
        self.tos = TosDataClient(self.conf.tos_server[0], int(self.conf.tos_server[1]))
        
        self.begin = DiffTime()
        self.cur = DiffTime()
        
        self.wait_chl = self.options.wait_chl or self.conf.wait_chl
        self.add_num = self.conf.add_num or 1
        self.hello = self.conf.hello
        self.account_success = 0
        self.account_fail = 0
        self.add_fail = 0
        self.total = 0
        self.last_total = 0
        
        if not self.sync():
            sys.exit()



    def add_options(self, parser):
        parser.add_option("-n", '--name', dest='name', action="store", help="the account file name(default get from account server)", type="string")
        parser.add_option("-t", '--tos_num', dest='tos_num', action="store", default=0, help="the tos file num", type="int")
        parser.add_option("-w", '--wait_chl', dest='wait_chl', action="store", help="", type="string")
        
        

    def process_options(self, options, args):
        self.name = options.name
    
    def sync(self):

        self.tos.load_thread()
        self.accounts.load_thread()
        diff = self.begin.get_diff()
        if diff == 0:
            return
        diff1 = self.cur.get_diff()
        cur_total = self.total - self.last_total
        self.last_total = self.total
        self.cur.reset()
        s = "account %s, account_speed %0.2f total %s speed:%0.2f/%0.2f time %0.2f/%0.2f " % (self.account_success, self.account_success / diff, self.total, self.total / diff, cur_total/diff1, diff, diff1 )
        log.error(s)

        return bool(self.tos) and bool(self.accounts)
    
    def end(self):
        pass

    def get_to(self):
        while mysignal.ALIVE:
            try:
                return self.tos.get()
            except NotDataException:
                mysignal.ALIVE = False
                log.trace("not any tos")
                time.sleep(2)
                continue

    def work(self, *args, **kwargs):
        try:
            return self._work(*args, **kwargs)
        except:
            log.exception("")

    def _work(self, name, id):
        line = self.accounts.get_rnd()
        if line.find('----') != -1:
            account, psw = line.split('----', 1)
        else:
            account = line.split('\t')[0]
            psw = '846266'
        account = account.strip()
        psw = psw.strip()
        msn = MSN(self.wait_chl)
        try:
            ret = msn.connect(account, psw)
        except TimeoutException:
            log.trace('%s login timeout', account)
            return
        if ret:
            #log.trace("%s login success", account)
             
            self.account_success += 1
            for i in range(self.conf.add_num):
                to_email = self.get_to()
                ret = msn.add_contact(to_email, 1, self.hello)
                if ret == 0:
                    members = msn.get_allow_email()
                    num = members and len(members) or 0
                    if not self.name and num:
                        self.accounts.update_contact(account, num)
                
                    self.total += 1
                    log.trace('%s add %s success friends %s', account, to_email, num)

                #else:
                #    log.trace('%s add %s fail ret %s friends %s', account, to_email, ret, num)
                #    break

        else:
            #log.trace('%s %s login fail', account, psw)
            self.accounts.set_fail(line)
            self.account_fail += 1

def main():
    app = Application()
    app.run()


if __name__ == '__main__':
    main()
