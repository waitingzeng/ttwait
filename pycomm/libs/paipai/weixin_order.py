#!/usr/bin/python
#coding=utf8
from pycomm.singleweb import SingleWeb, get_page
from pycomm.utils import text
from pycomm.utils import html
from pyquery import PyQuery
import random
import time
import json
import urllib
import os
from pycomm.log import log, PrefixLog, open_log, open_debug
import hashlib
from pycomm.utils.pprint import pprint, pformat
from comm_def import PaiPaiRequestDealState

class NeedLoginException(Exception):
    pass

pjs='phantomjs --load-images=no --ignore-ssl-errors=yes --disk-cache=yes'
pwd = os.path.abspath('.')
cur_path = os.path.dirname(os.path.abspath(__file__))

class Application(object):
    m_paipai_domain = "http://wmai.m.paipai.com"
    def __init__(self, uin, psw):
        self.uin = uin
        self.psw = psw
        self.web = SingleWeb(debug=0)
        self.log = PrefixLog('paipai uin %s psw %s' % (self.uin, self.psw))
        self.gtk = ''
        self.load_cookies()

    def run_login(self):
        os.chdir(cur_path)
        os.system("%s login.js %s '%s'" % (pjs, self.uin, self.psw))
        os.chdir(pwd)

    def load_cookies(self, retry=False):
        name = "/tmp/%s_paipai_cookie" % self.uin
        cookies = os.path.exists(name) and file(name).read() or ''
        if cookies:
            self.web.set_cookies(cookies, {'domain' : '.paipai.com', 'path' : '/'}) 
        url = "http://wmai.m.paipai.com/DefaultPage.xhtml"
        self.web.get_page(url)
        if not self.web.url.startswith(url):
            if not retry:
                self.run_login()
                return self.load_cookies(True)
            raise NeedLoginException(self.web.url)
        self.gtk = self.get_gtk()
        return True

    

    def get_page(self, url, *args, **kwargs):
        retry = kwargs.pop('retry', False)
        newurl = html.add_querystr(url, 'g_tk=%s' % self.gtk)
        page = self.web.get_page(newurl, *args, **kwargs)
        if not self.web.url.startswith(self.m_paipai_domain) or self.web.url.find('LoginAction.xhtml') != -1 or self.web.url.find('40x') != -1:
            if retry:
                raise NeedLoginException(self.web.url)
            self.load_cookies()
            kwargs['retry'] = True
            return self.get_page(url, *args, **kwargs)
        if not page:
            self.log.error('load url %s fail')
        return page

    def time33(self, s):
        hash = 5381
        l = len(s)
        for x in s:
            hash += (hash << 5) + ord(x)
        return hash & 0x7fffffff

    def get_gtk(self):
        skey_cookie = self.web.get_cookies('skey')
        if not skey_cookie:
            raise NeedLoginException(self.web.url)
        return self.time33(skey_cookie.value)


    def load_order_info(self, deal_code):
        if not deal_code:
            return None

        try:
            uin, order_time, code_id = deal_code.split('-')
            if uin != self.uin:
                self.log.error('%s not %s deal', deal_code, self.uin)
                return None
        except:
            self.log.error('invalid deal code %s', deal_code)
            return None
        self.log.trace("begin process %s", deal_code)
        url = "http://wmai.m.paipai.com/DealDetail.xhtml?dealId=%s&substate=0" % code_id
        page = self.get_page(url)
        if not page:
            self.log.error("process %s get page fail", deal_code)
            return None
        if not isinstance(page, unicode):
            page = page.decode('gbk')

        if page.find(deal_code) == -1:
            self.log.error("load deal detal %s but not found deal_code", deal_code)
            return None
        pq = PyQuery(page)
        #"订单编号：1516715015-20121129-964458501买家昵称：(518800315)买家姓名：待确认买家电话：13888888888买家邮编：无"
        res = {}
        name_map = {
            u'订单编号' : 'dealCode',
            u'买家昵称' : 'buyerUin',
            u'买家姓名' : 'receiverName',
            u'买家电话' : 'receiverMobile',
            u'买家邮编' : 'receiverPostcode',

        }
        for li in pq.find('.info_order_form').find('li'):
            li = PyQuery(li)
            try:
                name, info = li.text().split('：')
            except:
                log.exception()
                continue

            info = info.strip(' \n\t()')
            if info == '无' or info == '待确认':
                info = ''
            if name not in name_map:
                continue
            res[name_map[name]] = info
        address = pq.find('#recvinfo').text()
        if address:
            address = address.strip()
            res['receiverAddress'] = address

        order_status_text = pq.find('.order_status .title').text().split('：')[1]
        
        status = PaiPaiRequestDealState.DS_SYSTEM_HALT
        if order_status_text.find('等待卖家确认货到付款订单的收货') != -1:
            status = PaiPaiRequestDealState.DS_WAIT_BUYER_RECEIVE
        if order_status_text.find('卖家已确认订单，等待卖家发货') != -1:
            status = PaiPaiRequestDealState.DS_WAIT_SELLER_DELIVERY
        if order_status_text.find('交易已关闭') != -1:
            status = PaiPaiRequestDealState.DS_DEAL_CANCELLED
        if order_status_text.find('等待买家确认货到付款订单') != -1:
            status = PaiPaiRequestDealState.DS_WAIT_BUYER_PAY
        res['dealState'] = status
        res['dealStateDesc'] = order_status_text

        self.log.trace('load weixin order %s', pformat(res))
        return res

    def ajax_call(self, url, deal_code, **kwargs):
        kwargs['dealId'] = deal_code.strip()
        kwargs.setdefault('type', 0)
        name = url.lower()[:-6]
        page = self.get_page(self.m_paipai_domain + '/%s' % url, data=kwargs)
        if not page:
            return False
        if page.find('errCode:0') != -1:
            self.log.error("%s %s success", name, deal_code)
            return True
    
        self.log.error("%s %s fail %s", name, deal_code, page)
        return False


    def confirm_deal(self, deal_code, type=0):
        return self.ajax_call('ConfirmDeal.xhtml', deal_code, type=type)

    def close_deal(self, deal_code, close_reason, type=0):
        return self.ajax_call('CloseDeal.xhtml', deal_code, type=type, closeReason=close_reason)

    def mark_send(self, deal_code, shipping_id, invoice_no, expect_time=3):
        return self.ajax_call('MarkSend.xhtml', deal_code, wuliuCode=invoice_no, companyId=shipping_id, expectTime=expect_time)

    def confirm_receive(self, deal_code):
        return self.ajax_call('ConfirmReceive.xhtml', deal_code, confirmType=1)

    def deny_receive(self, deal_code, deny_reason):
        return self.ajax_call('ConfirmReceive.xhtml', deal_code, confirmType=0, denyReason=deny_reason)


def main():
    open_log('paipai')
    open_debug()
    #app = Application('2680078771', 'TTwait846266')
    #app.load_cookes()
    #print app.gtk
    app = Application('1516715015', 'TTwait846266')
    deal_code = '1516715015-20121129-964149777'
    #print app.load_order_info(deal_code)
    print app.close_deal(deal_code, 2)

if __name__ == '__main__':
    main()
