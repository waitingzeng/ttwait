#!/usr/bin/python
#coding=utf8

from phpserialize import serialize, unserialize
from mfhui_admin.mall.models import Payment
from pycomm.singleweb import SingleWeb
from pycomm.log import log
from xml.etree import ElementTree
import io
import time
import hashlib
import urllib

class AlipayService(object):
    err_msg                    = ''
    err_code                   = ''
    ###参数####
    partner                    = ""
    key                        = ""
    seller_email               = ""

    subject                     = "美肤汇订单"
    out_trade_no                = "123455"
    total_fee                   = "29.00"
    out_user                    = "chain0414"

    notify_url                  = "http://m.mfhui.com/orders/order_done"
    call_back_url               = "http://m.mfhui.com/orders/order_done"
    merchant_url                = "http://m.mfhui.com/orders/order_done"

    Service_Create              = "alipay.wap.trade.create.direct"
    Service_authAndExecute      = "alipay.wap.auth.authAndExecute"
    format                      = "xml"
    sec_id                      = "MD5"
    _input_charset              = "utf-8"
    v                           = "2.0"

    config_type                 = 'alipay'
    #淘宝网关 url
    gateway_order = "http://wappaygw.alipay.com/service/rest.htm?"

    def __init__(self):
        #try:
        alipay_data = Payment.objects.get(pay_code=self.config_type)
        config_str = alipay_data.pay_config 
        config = unserialize(config_str)
        key_arr = {'alipay_account': 'seller_email', 'alipay_key': 'key', 'alipay_partner': 'partner'}
        for k in config:
            i = config[k]
            name = i['name']
            value = i['value']
            if key_arr.has_key(name):
                setattr(self, key_arr[name], value)
        #self.seller_email = config['alipay_account']
        #self.key = config['alipay_key']
        #self.partner = config['alipay_partner']
        #except:
        #    return None
        self.params = {}
        self.web = SingleWeb()

    def alipy_get_token(self, data):
        req_data = self.make_token_req_data(data)
        params = {
            "req_data" : req_data,
            "service" : self.Service_Create,
            "sec_id" : self.sec_id,
            "partner" : self.partner,
            "req_id" : time.time(),
            "format" : self.format,
            "v" : self.v,
        }
        #linkstring = create_linkstring(params)
        #print "linkstring is %s " % linkstring
        build_mysign_str = build_mysign(params, self.key)
        #sign_str = urllib.urlencode({'sign': build_mysign})
        #linkstring += '&' + sign_str
        params['sign'] = build_mysign_str
        result = self.web.get_page(self.gateway_order, params)
        ret_data = urldecode(result)
        log.trace("alipay ret str is %s ", result)
        return self.check_return_data(ret_data)

    def make_token_req_data(self, params):
        pars = {
            'subject' : self.subject,
            'out_trade_no' : 0,
            'total_fee' : 0,
            'seller_account_name' : self.seller_email,
            'call_back_url' : self.call_back_url,
            'out_user' : '',
        }

        pars.update(params)
        ret = {}
        for k in pars:
            v = pars[k]
            if v != '':
                ret[k] = v
        tmp = []
        tmp.append(u'<direct_trade_create_req>')
        tmp.append(u'<subject>' + pars['subject'] + '</subject>')
        tmp.append(u'<out_trade_no>' + pars['out_trade_no'] + '</out_trade_no>')
        tmp.append(u'<total_fee>' + str(pars['total_fee']) + '</total_fee>')
        tmp.append(u'<seller_account_name>' + pars['seller_account_name'] + '</seller_account_name>')
        tmp.append(u'<out_user>' + str(pars['out_user']) + '</out_user>')
        tmp.append(u'<call_back_url>' + pars['call_back_url'] + '</call_back_url>')
        tmp.append(u'</direct_trade_create_req>')
        ret_str = ''.join(tmp)
        return ret_str

    def execute(self, token):
        req_data = self.make_execute_data(token)
        params = {
            "req_data" : req_data,
            "service" : self.Service_authAndExecute,
            "sec_id" : self.sec_id,
            "partner" : self.partner,
            "call_back_url" : self.call_back_url,
            "format" : self.format,
            "v" : self.v,
        }

        build_mysign_str = build_mysign(params, self.key)
        params['sign'] = build_mysign_str
        url_str = urllib.urlencode(params)
        ret_url = self.gateway_order + url_str
        return ret_url

    def make_execute_data(self, token):
        tmp = []
        tmp.append('<auth_and_execute_req><request_token>')
        tmp.append(token)
        tmp.append('</request_token></auth_and_execute_req>')

        ret_str = ''.join(tmp)
        return ret_str

    def check_return_data(self, result):

        if result.has_key('res_error'):
            log.error("get token failed the failed msg is %s " , result['res_error'])
            self.err_code = 93000
            self.err_msg = result['res_error']
            return None
        mysign = build_mysign(result, self.key)
        if not result.has_key('sign'):
            self.err_code = 93001
            return None
        ret_sign = result['sign']
        print "ret_sign and mysign is %s  %s " % (ret_sign, mysign)
        if ret_sign != mysign:
            self.err_code = 93001
            return None

        if result.has_key('res_data'):
            token = self.__getToken__(result['res_data'])
            return token

        self.err_code = 93000
        return None

    def __getToken__(self, xml_data):
        etree = ElementTree.fromstring(xml_data)
        node = etree.find('request_token')
        tag = ""
        if node is not None:
            tag = node.text
        return tag

    def check_mysign(self, params, sign):
        mysign = build_mysign(params, self.key)
        if mysign == sign:
            return True
        return False

def build_mysign(params, key):
    linkstring = create_linkstring(params)
    print "linkstring is %s  " % linkstring
    m = hashlib.md5(linkstring + key)
    m.digest()
    ret_str = m.hexdigest()

    return ret_str

def create_linkstring(params):
    if not params:
        return ""
    ret_str = ""
    params = data_sort(params)
    ks = params.keys()
    ks.sort()

    for k in ks:
        v = str(params[k])
        ret_str += k + '=' + v + '&'
    ret_str = ret_str[0: len(ret_str) - 1]
    return ret_str

def data_sort(params):
    ks = params.keys()
    ks.sort()

    print "the data_sort is %s " % ks
    ret = {}
    for k in ks:
        v = params[k]
        if k not in ('sign','sign_type') and v != '':
            ret[k] = params[k]

    return ret
def urldecode(str):
    d = {}
    arr = str.split("&")
    for s in arr:
        if s.find('='):
            k,v = map(urllib.unquote, s.split('='))
            v = urllib.unquote_plus(v)
            v = v.decode('utf8')
        try:
            d[k] = v
        except:
            d[k] = [v]
    return d