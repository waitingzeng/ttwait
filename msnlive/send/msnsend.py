#!/bin/env python
#coding=utf8

import sys
import time
from datetime import datetime
from random import shuffle
#from pycomm.proc.threadbase import ThreadBase
from pycomm.proc.threadbase import ThreadBase
from pycomm import signal as mysignal
from pycomm.log import PrefixLog, log
from pycomm.utils.dict4ini import DictIni
from pycomm.libs.msnclass import MSN, TimeoutException
from pycomm.libs.msnclass.message import get_message
from pycomm.utils.tracktime import DiffTime
from pycomm.libs.rpc import MagicClient
from messagecache import  MuchMessageCache
from pycomm.utils.accounttext import RandomAccountNotMembery, NotDataException
from pycomm.utils import textfile
import threading

class AccountClient(object):
    def __init__(self, *args):
        self.client = MagicClient(*args)
        self.lock = threading.RLock()
        self.data = []

    def load_accounts(self):
        while True:
            try:
                self.data = self.client.get_send_accounts()
                if not self.data:
                    log.trace('load send_accounts not data')
                    time.sleep(3)
                    continue
                break
            except:
                log.exception("get_send_accounts fail")
                time.sleep(3)
                continue
        shuffle(self.data)
        file('data/send_accounts%s.txt' % (datetime.now().strftime('%Y%M%d%H%m%S')), 'w').write('\n'.join(self.data))

        if not self.data:
            raise Exception('Not Data Left')
        

    def get_rnd(self):
        with self.lock:
            if not self.data:
                self.load_accounts()

            return '%s----%s' % (self.data.pop(), '846266')
    get = get_rnd

    def set_fail(self, acc):
        try:
            self.client.add_account(acc, -1)
        except:
            pass


class AccountCache(RandomAccountNotMembery):
    autorelead = True
    def get(self):
        acc = RandomAccountNotMembery.get(self)
        if acc.find('----') != -1:
            return acc.split('----')
        return acc, '846266'


class MSNSend(ThreadBase):
    def get_siteconfig(self):
        if hasattr(self, 'site_config'):
            return
        site_file = self.conf.site_config
        site_config = DictIni(site_file)
        site_config.all = set([x for x in site_config.keys() if x and not x.startswith('_')])
        self.site_config = site_config
        log.debug('load site_conf %s', self.site_config.all)
        return

    def parse_names(self):
        self.get_siteconfig()
        names = self.options.names
        if not names or names == ['all']:
            self.names = self.site_config.all
        else:
            not_valid = [x for x in names if x not in self.site_config.all]
            if not_valid:
                log.trace('%s not valid site')
                sys.exit(-1)
            self.names = names

            self.names = set(self.names)

    def init(self):
        self.parse_names() 
            
        self.msgs = MuchMessageCache(self.site_config, self.names, self.conf.shorturl==1)
        #self.msgs.load() 
        if self.options.test_msgs:
            print self.msgs.get()
            sys.exit()
        if self.options.account:
            self.accounts = textfile.CacheText(self.options.account, force_local=False)
        else:
            self.accounts = AccountClient(self.conf.account_server[0], self.conf.account_server[1])
        
        self.wait_one_msg = float(self.conf.wait_one_msg)
        self.total = 0
        self.msn_ct = 0
        self.fail_total = 0
        self.begin = DiffTime()
        self.cur = DiffTime()
        self.last_total = 0

    def add_options(self, parser):
        parser.add_option("-n", '--name', dest='names', action="append", help="the site name", type="string")
        parser.add_option("-a", '--account', dest='account', action="store", help="the account file", type="string")
        parser.add_option("-w", '--wait_chl', dest='wait_chl', action="store", help="", type="string")

        parser.add_option("-m", '--test_msgs', dest='test_msgs', action="store_true")

    def sync(self):
        diff = self.begin.get_diff()
        if diff == 0:
            return
        diff1 = self.cur.get_diff()
        cur_total = self.total - self.last_total
        self.last_total = self.total
        self.cur.reset()
        s = "msn_ct %s, msn_speed %0.2f total %s speed:%0.2f/%0.2f time %0.2f/%0.2f " % (self.msn_ct, self.msn_ct / diff, self.total, self.total / diff, cur_total/diff1, diff, diff1 )
        log.error(s)
        
    def get_allow_email(self, app, msn_ct):
        members = app.get_allow_email()
        
        return members or []
    
    def send_members_oim(self, app, account, psw, msn_ct, msgs=None, T=None):
        if not msgs:
            msgs = self.msgs
        #members = self.get_friend_list(account, psw)
        
        if not T:
            T = DiffTime()
        members = self.get_allow_email(app, msn_ct)
        shuffle(members)
        #members.insert(0, 'zqc160@163.com')
        ct = members and len(members) or 0
        self.log.error('%d %s load members success %d' % (msn_ct, account, ct))
        fail_ct = 0
        for member in members:
            if not mysignal.ALIVE:
                break
            
            if app.error_code == 800:
                time.sleep(10)
                app.error_code = 0
            
            ct -= 1
            try:
                send_msg = get_message(msgs.get())
                code = app.send_oim_message(send_msg, member)
                if code:
                    self.total += 1
                    if ct % 20 == 0:
                        self.log.trace('%d %s succ %d:%d, total %d %d msg is %s', msn_ct, account, len(members), ct, self.total, self.fail_total, send_msg.strip().split('\n')[-1])
                    
                else:
                    self.fail_total += 1
                    fail_ct += 1
                    self.log.error('%d %s fail %d, total %d %d' % (msn_ct, account, ct, self.total, self.fail_total))
                    if fail_ct > 5:
                        return False
                if self.wait_one_msg:
                    time.sleep(self.wait_one_msg)
            except:
                self.log.exception('send_member_oim %s', app.user)
                break
        self.log.trace('%d %s send finish %s usetime %s', msn_ct, account, len(members), T.get_diff())
    
    
    def work(self, name, id=0):
        try:
            line = self.accounts.get_rnd()
            if line.find('----') != -1:
                account, psw = line.split('----', 1)
            else:
                account = line.split('\t')[0]
                psw = '846266'
        except NotDataException:
            mysignal.ALIVE = False
            return
        
        self.msn_ct += 1
        msn_ct = self.msn_ct
        self.log.error('%d %s begin connect' % (msn_ct, account))
        app = MSN()
        T = DiffTime()
        try:
            res = app.connect(account, psw)
        except TimeoutException:
            self.log.error("$d %s login timeout usetime %s", msn_ct, account, T.get_diff())
            return 
        if not res:
            self.log.error('%d %s %s login fail, usetime %s' % (msn_ct, account, psw, T.get_diff()))
            self.accounts.set_fail(line)
            return
        else:
            self.log.error('%d %s login success usetime %s' % (msn_ct, account, T.get_diff()))
        try:
            self.send_members_oim(app, account, psw, msn_ct, self.msgs, T)
        except:
            self.log.exception('%s %s send fail', account, psw)
            pass
        app.disconnect()

            


def main():
    app = MSNSend()
    app.run()

if __name__ == '__main__':
    main()
