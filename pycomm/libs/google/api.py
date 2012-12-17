#! /usr/bin/env python
#coding=utf-8
import urllib2
import urllib
import json

class Api(object):
    def __init__(self, api_key=None):
        self.api_key = api_key

    
    def url_shortener(self, long_url, api_key=None):
        if not api_key:
            api_key = self.api_key
        post_url = 'https://www.googleapis.com/urlshortener/v1/url'
        if api_key:
            post_url += '?key=%s' % api_key
        headers = {'Content-Type' : 'application/json'}
        data = json.dumps({'longUrl' : long_url})

        req = urllib2.Request(post_url, data=data, headers=headers)
        res = urllib2.urlopen(req)

        res_data = res.read()
        res_data = json.loads(res_data)
        return res_data['id']



if __name__ == '__main__':
    api = Api()
    print api.url_shortener('http://www.google.com/')
       
