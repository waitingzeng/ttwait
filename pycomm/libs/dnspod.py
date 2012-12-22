#! /usr/bin/env python
#coding=utf-8
import json
from pycomm.singleweb import SingleWeb
import sys
import traceback

class LoginFailException(Exception):pass
class RecordType:
    A = 'A'
    CNAME = 'CNAME'
    MX = 'MX'
    URL = 'URL'
    NS = 'NS'
    TXT = 'TXT'
    AAAA = 'AAAA'

class RecordLine:
    default = '\u9ed8\u8ba4'     #默认
    tel = '电信'             #电信
    cnc = '网通'             #网通
    edu = '教育网'             #教育网
    cmd = '移动'             #移动(VIP)
    foreign = '国外'     #国外(VIP)
    

DEBUG = False
class DnsPod:
    App = 'pyDnsPod/1.5(%s)'
    def __init__(self, email, psw):
        self.email = email
        self.psw = psw
        self.web = SingleWeb()
        self._domains = None
        self._records = {}
    
    def domains(self):
        if self._domains is None:
            self.domain_list()
        return self._domains or {}
    
    
    def records(self, domain):
        if self._records.get(domain) is None:
            self.record_list(domain)
        return self._records[domain] or []
    
    def get_domain_id(self, domain):
        return self.domains().get(domain, {}).get('id', 0)
    
    def get_record_id(self, domain, sub_domain = None, type = None, value = None):
        records = self.records(domain)
        ids = []
        for r in records:
            if (sub_domain is None or r['name'] == sub_domain) and (type is None or r['type'] == type) and (value is None or r['value'] == value):
                ids.append(r['id'])
        return ids
    
    def urlquote(self, data):
        return u'&'.join([u'%s=%s' % (k, v) for k, v in data.items()])
    
    def _post(self, data = {},**kwargs):
        name = traceback.extract_stack()[-2][2].lower()
        api = '.'.join([x.capitalize() for x in name.split('_')])
        
        url = 'https://dnsapi.cn/%s' % api
        headers = {'User-Agent' : self.App % self.email}
        if 'format' not in data:
            data['format'] = 'json'
        
        data['login_email'] = self.email
        data['login_password'] = self.psw
        res = self.web.get_page(url, data, headers)
        if DEBUG:
            print url, data
            print res
        try:
            func = getattr(self, '%s_%s' % (name, data['format']))
        except AttributeError:
            func = getattr(self, 'default_%s' % data['format'])
        
        if not callable(func):
            return False
        try:
            if data['format'] == 'json':
                res = json.loads(res)
                if res['status']['code'] == '-1':
                    raise LoginFailException
                return func(res, **kwargs)
            else:
                return None
        except:
            traceback.print_exc()
            return False
    
    def default_json(self, data):
        if data['status']['code'] == '1':
            return True
        print data['status']['message']
        return False
        
    
    def info_version(self):
        if hasattr(self, 'Version'):
            return self.Version
        return self._post()
    
    def info_version_json(self, data):
        if data['status']['code'] == '1':
            self.Version = data['status']['message']
            return self.Version
        return 0
            
    
    def domain_create(self, domain):
        if self.Domain_Exists(domain):
            return True
        data = {'domain' : domain}
        return self._post(data)
    
    def domain_create_json(self, data):
        if data['status']['code'] in ['1', '5']:
            return True
        return False

    def domain_list(self):
        data = {'type' : 'mine', 'offset' : '0', 'length' : '9999'}
        return self._post(data)

    def domain_list_json(self, data):
        if data['status']['code'] == '1':
            self._domains = {}
            for x in data['domains']:
                self._domains[x['name']] = x
        return self._domains
    
    def domain_remove_by_name(self, domain):
        domain_id = self.get_domain_id(domain)
        if not domain_id:
            return True
        return self.domain_remove(domain_id)
    
    def domain_remove(self, domain_id):
        data = {'domain_id' : domain_id}
        return self._post(data)
    
    def domain_status_by_name(self, domain, *args, **kwargs):
        id = self.get_domain_id(domain)
        if not id:
            return False
        return self.domain_status(id, *args, **kwargs)
        
    
    def domain_status(self, domain_id, status = True):
        data = {
            'domain_id' : domain_id,
            'status' : status
        }
        return self._post(data)
    
    
    def record_create(self, domain, sub_domain, record_type,  value , record_line = RecordLine.default, mx=10, ttl=604800):
        domain_id = self.get_domain_id(domain)
        if not domain_id:
            return False
        record_id = self.get_record_id(domain, sub_domain, record_type, value)
        if record_id:
            return True
        data = {
            'domain_id' : domain_id,
            'sub_domain' : sub_domain,
            'record_type' : record_type,
            'value' : value,
            'record_line' : "默认",
            'mx' : mx,
            'ttl' : ttl
        }
        return self._post(data)
    
    def record_list(self, domain):
        domain_id = self.get_domain_id(domain)
        if not domain_id:
            return False
        data = {'domain_id' : domain_id}
        return self._post(data, domain=domain)
    
    def record_list_json(self, data, domain):
        if data['status']['code'] == '1':
            self._records[domain] = data['records']
        else:
            self._records[domain] = None
        return self._records[domain]
    
    def record_modify_by_name(self, domain, sub_domain, record_type,  value, *args, **kwargs):
        record_id = self.get_record_id(domain, sub_domain, record_type, value)
        domain_id = self.get_domain_id(domain)
        if not record_id or not domain_id:
            return False
        return self.record_modify(domain_id, record_id[0], sub_domain,  record_type, value, *args, **kwargs)
    
    def record_modify(self, domain_id, record_id, sub_domain, record_type,  value , record_line = RecordLine.default, mx=10, ttl=604800):
        data = {
            'domain_id' : domain_id,
            'record_id' : record_id,
            'sub_domain' : sub_domain,
            'record_type' : record_type,
            'value' : value,
            'record_line' : record_line,
            'mx' : mx,
            'ttl' : ttl
        }
        return self._post(data)
    
    def record_remove_by_name(self, domain, sub_domain, record_type, value):
        record_id = self.get_record_id(domain, sub_domain, record_type, value)
        domain_id = self.get_domain_id(domain)
        if not record_id or not domain_id:
            return False
        return self.record_remove(domain_id, record_id[0])
        
    
    def record_remove(self, domain_id, record_id):
        data = {
            'domain_id' : domain_id,
            'record_id' : record_id,
        }
        return self._post(data)
    
    def record_status_by_name(self, domain, sub_domain, record_type, value, *args, **kwargs):
        record_id = self.get_record_id(domain, sub_domain, record_type, value)
        domain_id = self.get_domain_id(domain)
        if not record_id or not domain_id:
            return False
        return self.record_status(domain_id, record_id[0], *args, **kwargs)
        
    
    def record_status(self, domain_id, record_id, status = True):
        data = {
            'domain_id' : domain_id,
            'record_id' : record_id,
            'status' : status
        }
        return self._post(data)
        
        
    
if __name__ == '__main__':
    app = DnsPod('zqc160@163.com', 'TTwait846266')
    #app.info_version()
    print app.record_create('tb8.cn.com', '1', RecordType.TXT, 'v=msv1 t=a6c60f8d3a16e746a2c38a279bbe72')
