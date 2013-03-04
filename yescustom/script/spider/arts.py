#!/usr/bin/python
#coding=utf8
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "custom.settings"
import sys
sys.path.insert(0, os.path.dirname('../../'))

from custom.spider.models import ArtSpiderUrls
from pycomm.libs.spider import ResponseHandler, route, Spider, Url
from custom.design.models import ArtCategory, Art
from pyquery import PyQuery as pq
import re
from urlparse import urljoin, urlparse
from pycomm.utils import text
from pycomm.utils.encoding import any_to_unicode
from utils import get_img_url, get_img_path



@route('/iframe-img')
class Index(ResponseHandler):
    def parse(self, **kwargs):
        body = self.response.body
        page = pq(body)
        for option in text.get_in_list(page.find('#cate_id').html(), '<option', '</option>'):
            name, value = text.get_in(option, '>'), text.get_in(option, 'value="', '"')
            if value == '0':
                continue

            obj, new = ArtCategory.objects.get_or_new(id=value)
            obj.name = name
            obj.save()

            yield Url(name, '/iframe-img/c/%s/page/1' % value, self.response)


@route('/iframe-img/c/(\d+)/page/(\d+)')
class SubCategory(ResponseHandler):
    def parse(self, cid, cur_page, **kwargs):

        body = self.response.body

        page = pq(body)
        for li in text.get_in_list(page.find('.createProductList1').html(), '<li>', '</li>'):
            a = pq(li).find('a')
            img = pq(li).find('img')
            value = text.get_in(li, 'insertImg(', ')')
            name = text.get_in(li, 'title="', '"')
            src = img.attr('src')
            for img in get_img_url(src):
                url = Url(name, img, self.response)
                yield url
            obj, new = Art.objects.get_or_new(id=value)
            obj.name = name
            obj.img = get_img_path(src)
            obj.category_id = cid
            obj.save()

        for a in text.get_in_list(page.find('.page1').html(), '<a', '</a>'):
            if a.find('Next') != -1:
                self.log.trace("get next page for %s", self.response.url)
                yield Url('%s_%s' % (cid, cur_page), '/iframe-img/c/%s/page/%s' % (cid, int(cur_page) + 1), self.response)


@route(['(/.*\.jpg)', '(/.*\.gif)', '(/.*\.png)'])
class LoadImage(ResponseHandler):
    def parse(self, path):
        filename = urlparse(self.response.url).path
        filename = 'img' + filename
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)

        file(filename, 'wb').write(self.response.body)
        return


class ArtSpider(Spider):
    request_default = {
        'connect_timeout': 100,
        'request_timeout': 100,
    }


def main():
    start_urls = ['http://www.yescustomall.com/iframe-img']
    pipeline = ArtSpiderUrls.pipeline(start_urls)
    spider = ArtSpider(pipeline, max_running=1000000)

    spider.run()


if __name__ == '__main__':
    main()
