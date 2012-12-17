#! /usr/bin/env python
#coding=utf-8
import re, htmlentitydefs
import cgi
import time
import httplib

encoding = 'gbk'

def encode(s):
    "Encodes a string from local encoding to utf8"
    try:
        return s.decode(encoding).encode('utf-8')
    except:
        return s

def decode(s):
    "Decodes a string from utf8 to local encoding"
    try:
        return s.decode('utf-8').encode(encoding)
    except:
        return s
    

HEADERS = {
    'User-Agent' : 'MSN Explorer/9.0 (MSN 8.0; TmstmpExt)',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language' : 'zh-cn,zh;q=0.5',
    'Accept-Charset' : 'GB2312,utf-8;q=0.7,*;q=0.7',
    'Keep-Alive' : '300',
    'Connection' : 'keep-alive',
    'Cache-Control' : 'max-age=0',

}
import urllib2

class HTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        m = req.get_method()
        if (code in (301, 302, 303, 307) and m in ("GET", "HEAD")
            or code in (301, 302, 303) and m == "POST"):
            newurl = newurl.replace(' ', '%20')
            newheaders = dict((k,v) for k,v in req.headers.items()
                              if k.lower() not in ("content-length", "host")
                             )
            return urllib2.Request(newurl,
                           data=req.get_data(),
                           headers=newheaders,
                           origin_req_host=req.get_origin_req_host(),
                           unverifiable=True)
        else:
            raise urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)

        
opener = urllib2.build_opener(HTTPRedirectHandler)
urllib2.install_opener(opener)
def get_page(url, data=None, headers={}, times=3):
    for k,v in HEADERS.items():
        headers.setdefault(k, v)
    
    req = urllib2.Request(url, data, headers)
    for i in range(3):
        try:
            resp = urllib2.urlopen(req)
            return resp.code, resp.read()
        except urllib2.HTTPError, info:
            print url
            raise info
        except:
            continue
    return None, None

if __name__ == '__main__':
    fp = file('a.txt')
    fp.close()
    print bool(fp)