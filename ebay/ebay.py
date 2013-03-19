#!/usr/bin/python
#coding=utf8
import re
from pycomm.log import open_debug
from pycomm.libs.spider import ResponseHandler, route, Spider, Url
from pycomm.libs.spider.pipeline import LevelDBPipeline
from site_config import SiteUrl
from pyquery import PyQuery as pq
from pycomm.libs.rpc.magicclient import MagicClient

email_client = MagicClient('127.0.0.1', 11222)

open_debug()
MAILSEARCH = re.compile(r"(\w+([-+\.]\w+)*@\w+([-\.]\w+)*\.\w+([-\.]\w+)*)", re.I).findall


@route('.*?/allcategories/all-categories')
class Index(ResponseHandler):
    def parse(self, *args, **kwargs):
        body = self.response.body
        for a in pq(body).find('.gdlnk- a'):
            a = pq(a)
            yield Url(a.text(), a.attr('href'), self.response)


@route('/sch/(.*?)/(\d+)/i.html.*')
class Index1(ResponseHandler):
    def parse(self, name, cid, *args, **kwargs):
        body = self.response.body
        page = pq(body)

        page_url = kwargs.get('page_url', 0)

        for a in page.find('#ResultSetItems h4 a'):
            a = pq(a)
            yield Url(a.text(), a.attr('href'), self.response)

        if page_url == 0:
            try:
                num = int(page.find('.rcnt').text().replace(',', '').replace('.', ''))
                if num == 0:
                    return
            except:
                
                num = int(page.find('.countClass').text().replace(',', '').replace('.', ''))
                if num == 0:
                    return
            page = (num - 1) / 200 + 1
            for i in range(page):
                url = '/sch/%s/%s/i.html?_pgn=%s&_skc=200&rt=nc' % (name, cid, i + 1)
                yield Url(url, url, self.response, page_url=1)


@route('/itm/.*')
class Item(ResponseHandler):
    def parse(self, *args, **kargs):
        body = self.response.body
        maillist = MAILSEARCH(body)
        maillist = set(maillist)
        for m in maillist:
            email = m[0]
            if not email:
                continue
            email_client.set('ebay_email', m[0].lower().strip(), '1')
            print 'found email', email


def main():

    start_urls = []
    for k, v in SiteUrl.items():
        if k != 'US':
            continue
        url = 'http://%s/sch/allcategories/all-categories' % v
        start_urls.append((url, {'site': k}))

    pipeline = LevelDBPipeline('ebay.ldb', '127.0.0.1', 11222, start_urls)
    spider = Spider(pipeline, max_running=1000000)

    spider.run()

if __name__ == '__main__':
    main()
