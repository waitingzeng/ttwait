#! /usr/bin/env python
#coding=utf-8
from msn_live import MSNLive
from pyquery import PyQuery as pq
from pycomm.utils.text import get_in, rnd_str
from pycomm.log import log
import httplib
import socket
httplib.HTTPConnection.debuglevel = 0
from pycomm.libs.dnspod import DnsPod, RecordType
import time
import sys
import os
from datetime import datetime
import threading



class DomainLive(MSNLive):
    def __init__(self, *args, **kwargs):
        self.dnspod = kwargs.pop('dnspod', None)
        if not self.dnspod:
            log.error("Not Found DNSPod")
            sys.exit(-3)

        super(self.__class__, self).__init__(*args, **kwargs)
        self.accounts = {}
        self.domains = {}
        
        
    def process_cookies(self):
        return
    
    def load_all_domain(self):
        url = 'https://domains.live.com/'
        page = self.web.get_page(url)
        trs = pq(page).find('#domainsGrid tbody tr')
        domains = {}
        for tr in trs:
            tds = pq(tr).find('td')
            num = pq(tds[1]).text().strip()
            try:
                num = int(num)
            except:
                num = -1
            domains[pq(tds[0]).text().strip()] = num
        self.domains = domains
        return domains
    
    def add_domain(self, domain, sub_domain=None):
        if sub_domain is None:
            sub_domain = rnd_str(5)
        full_domain = '%s.%s' % (sub_domain, domain)
        if full_domain in self.domains:
            log.error("domain exists %s" % full_domain)
            return self.domains[domain] >= 0
        
        data = {
            '_ctl0:ContentPanel:signupDomainName:domainName' : full_domain,
            '_ctl0:ContentPanel:signupDomainName:emailType' : 'mailTypeNone',
            '__EVENTTARGET' : '_ctl0$ContentPanel$signupDomainName$next',
        }
        page = self.web.submit_url('https://domains.live.com/Signup/SignupDomain.aspx', data, name='aspnetForm')
        
        if not page or page.find('_ctl0$ContentPanel$signupAdmin$accept') == -1:
            log.error("can not found accept %s" % full_domain)
            file('post.html', 'w').write(str(page))
            return False
        
        data = {'__EVENTTARGET' : '_ctl0$ContentPanel$signupAdmin$accept'}
        page = self.web.submit(page, data, name='aspnetForm')
        
        domain_key = get_in(page, 'v&#61;msv1 t&#61;', '</span>')
        
        if not domain_key:
            log.error("can not find domain_key %s" % full_domain)
            file('post_domain_key.html', 'w').write(str(page))
            return False
        
        res = self.dnspod.record_create(domain, sub_domain, RecordType.TXT, 'v=msv1 t=%s' % domain_key)
        if res:
            log.error("begin refresh domain %s" % full_domain)
            self.refresh_domain(full_domain)
            self.domains[full_domain] = 0
            return sub_domain
        else:
            log.error("set dnspod error %s" % full_domain)
        return False
        
    
    def refresh_domain(self, full_domain):
        time.sleep(5)
        data = {
            '__CALLBACKID' : '_ctl0:ContentPanel:callbackControl',
            '__CALLBACKPARAM' : 'a_0',
        }
        url = 'https://domains.live.com/Manage/ManageDomains.aspx?DomainName=%s' % full_domain
        while True:
            page = self.web.get_page(url)
            if page and page.find('onclick="onNewUser();"') != -1:
                return True
            if page is None:
                continue
            page = self.web.submit(page, data, name='aspnetForm')
            if page is None or page.find('onclick="onNewUser();"') == -1:
                log.error("wait domain valid")
                time.sleep(3)
                continue
            return True
            
    
    def load_accounts(self, full_domain):
        url = 'https://domains.live.com/Manage/ManageDomains.aspx?DomainName=%s' % full_domain
        page = self.web.get_page(url)
        
        if not page:
            return False
        new_num = get_in(page, '（共', '个帐户）')
        if not new_num:
            return False
        
        new_num = int(new_num.strip())
        return new_num

    
    def add_account(self, full_domain, name, lastname='', firstname=''):
        num = self.domains.get(full_domain, -1)
        if num == -1 or num >= 500:
            return False
        
        if name in self.accounts.get(full_domain, {}):
            return False
        
        data = {
            'addUserName' : name,
            'lastName' : lastname,
            'firstname' : firstname,
            'addPassword' : '846266',
            'addRetypePassword' : '846266',
            'requestInProgress' : 'true',
            '__CALLBACKID' : '_ctl0:ContentPanel:callbackControl',
            '__CALLBACKPARAM' : 'a_4',
        }
        url = 'https://domains.live.com/Manage/ManageDomains.aspx?DomainName=%s' % full_domain
        
        page = self.web.submit_url(url, data, name='aspnetForm')

        #new_num = int(new_num.strip())
        if page and page.find(name) != -1:
            self.domains[full_domain] = self.domains[full_domain] + 1
            return True
        return False
            

