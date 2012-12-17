#! /usr/bin/env python
#coding=utf-8
import traceback
import urllib2
import json

def get_allsite():
    try:
        allsite = urllib2.urlopen('http://ttwait.sinaapp.com/allsite').read()
        allsite = json.loads(allsite)
        return [v['tosite'] for v in allsite.values()]
    except:
        traceback.print_exc()
        return []

def clear_cache(url):
    try:
        url = 'http://%s/flushcache' % url
        res = urllib2.urlopen(url).read()
        if len(res) > 100:
            print url, 'fail1'
            return False
        print url, res
        url = 'http://%s/update_config' % url
        res = urllib2.urlopen(url).read()
        return True
    except:
        print url, 'fail'
        return False
    
    
def main():
    for url in get_allsite():
        for i in range(2):
            print i, clear_cache(url)
            
            
if __name__ == '__main__':
    main()
    
    
    
