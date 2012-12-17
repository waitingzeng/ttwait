#! /usr/bin/env python
#coding=utf-8
from singleweb import get_page
from text import getIn
import bsddb
import urllib
from functools import partial
import re
import simplejson

Pattern = {}
def _parse_rest(url, title_l, title_r, content_l, content_r, title_func=None, content_func=None):
    page = getPage(url)
    if page is None:
        return None
    if title_func and callable(title_func):
        title = title_func(page)
    else:
        title = getIn(page, title_l, title_r)
    
    if content_func and callable(content_func):
        content = content_func(page)
    else:
        content = getIn(page, content_l, content_r)
    
    return title.strip(), content.strip()

def load(url):
    type, url1 = urllib.splittype(url)
    host, url1 = urllib.splithost(url1)
    if host in Pattern:
        return Pattern[host](url)
    raise NotImplementedError
        

def searchRest(keyword, num = 100, lang='en'):
    start = 0
    data= {
        'rsz' : '8',
        'q' : keyword,
        'hl' : lang,
        'v' : '1.0',
    }
    url = 'http://ajax.googleapis.com/ajax/services/search/web?'
    output = []
    while start <= num:
        print keyword, start
        data['start'] = str(start)
        page = getPage(url + urllib.urlencode(data))
        if page is None:
            continue
        res = simplejson.loads(page)
        if res['responseStatus'] != 200:
            if res['responseDetails'] == 'out of range start':
                break
            continue
        responseData = res['responseData']
        results, cursor = responseData['results'], responseData['cursor']
        output.extend(results)
        start += 8
            
    return output

seach_re = re.compile(r'<h3 class="r[^"]*"><a href="([^"]*)"[^>]*>([^<]*)</a></h3>', re.I|re.M)
def _parse_search(page):
    if page is None:
        return []
    for item in ['<em>', '</em>', '<b>', '</b>']:
        page = page.replace(item, '')
    all = seach_re.findall(page)
    return all
    

def search(keyword, total=1000, lang='en'):
    data = {
        'q' : keyword,
        'num' : '100',
        'hl' : lang,
    }
    ct = 0
    for i in range(10):
        data['start'] = i * 100
        url = 'http://www.google.com/search?%s' % (urllib.urlencode(data))
        page = getPage(url)
        res = _parse_search(page)
        ct += len(res)
        yield i, res
        if ct >= total:
            break
    


if __name__ == '__main__':
    res = list(search('abbie boudreau', 100))
    print len(res[0]), res