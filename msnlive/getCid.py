#! /usr/bin/env python
#coding=utf-8
import urllib2
import urlparse
import sys
from text import getIn

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):     
    def http_error_301(self, *args, **kwargs):  
        return self.http_error_302(*args, **kwargs)

    def http_error_302(self, req, fp, code, msg, headers):   
        #result = urllib2.HTTPRedirectHandler.http_error_302(
        #    self, req, fp, code, msg, headers)              
        #result.status = code
        if 'location' in headers:
            newurl = headers.getheaders('location')[0]
        elif 'uri' in headers:
            newurl = headers.getheaders('uri')[0]
        else:
            return
        newurl = urlparse.urljoin(req.get_full_url(), newurl)
        return newurl                        

opener = urllib2.build_opener(SmartRedirectHandler())           


def getCid(id):
    url = 'http://spaces.live.com/Profile.aspx?partner=Messenger&mkt=zh-cn&cid=%s' % id
    req = opener.open(url)
    return getIn(req, 'cid-', '.')
    
    
def main():
    begin = len(sys.argv) == 2 and int(sys.argv[1]) or 0
    cidres = file('cid_finish.txt', 'a')
    for i, cid in enumerate(file('cid.txt')):
        if i < begin:
            continue
        cid = cid.strip()
        if cid == 0:
            continue
        elif not cid.startswith('-'):
            c = '%016X' % int(cid)
        else:
            c = getCid(cid)
        if c:
            cidres.write(c)
            cidres.write('\n')
            print i, cid, c
    cidres.close()
    
if __name__ == '__main__':
    main()