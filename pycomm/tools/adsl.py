#!/usr/bin/env python
#coding=gbk
import os,re, time
import urllib2
import platform
from pycomm.log import log
from pycomm.utils import text

viewip = "http://www.7y8.com/V/ip.asp"
ip4_re = re.compile(r'((25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3})', re.I|re.M)
if platform.system() == 'Windows':
    class ADSL(object):
        def __init__(self, name, username, password, unique=False):
            self.name = name
            self.username = username
            self.password = password
            self.unique = unique
            self.ip_list = {}


        def disconnect(self):
            cmd = 'rasdial %s /DISCONNECT' % self.name
            #print cmd
            s = os.popen(cmd).read()
            log.debug('cmd %s result %s', cmd, s)
            #print s
            if s == '没有连接\n命令已完成。\n' or s == '命令已完成。\n':
                return True
            else:
                return False

        def connect(self):
            cmd = 'rasdial %s %s %s' % (self.name, self.username, self.password)
            #print cmd
            s = os.popen(cmd).read()
            log.debug('cmd %s result %s', cmd, s)
            
            ip = self.get_ip_local()
            if ip:
                return ip
            else:
                log.debug('connect fail')
                return None

        def renew(self):
            c = 0
            while c < 20:
                self.disconnect()
                ip = self.connect()
                if ip and (self.unique and ip not in self.ip_list):
                    self.ip_list[ip] = 1
                    return ip
                else:
                    c+=1
                    log.debug('try renew ip %s hadip %s', c, len(self.ip_list))
                    

        def get_ip_local(self):
            s = os.popen('ipconfig /all').read()
            r_str = 'PPP adapter'
            r = s.find(r_str)
            if r == -1:
                return None
            begin_str = 'IP Address. . . . . . . . . . . . : '
            end_str = '\n'
            begin = s.find(begin_str, r)
            if begin == -1:
                return None
            begin += len(begin_str)
            end = s.find(end_str, begin)
            r = s[begin:end].strip()
            if ip4_re.search(r):
                return r
            else:
                return None

        def get_ip_remote(self):
            try:
                page = urllib2.urlopen(viewip).read()
                a = ip4_re.findall(page)
                return a[0][0]
            except Exception, info:
                log.exception('get remote ip fail')
                return None
        
if __name__ == '__main__':
    adsl = ADSL('home', 'gzDSL05638840@163.gd', 'little_fox846266', True)
    print adsl.renew()

