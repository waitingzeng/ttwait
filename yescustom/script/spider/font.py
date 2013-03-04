#!/usr/bin/python
#coding=utf8
from utils import get_img_url, get_img_path
from custom.spider.models import FontSpiderUrls
from pycomm.libs.spider import ResponseHandler, route, Spider, Url
from custom.design.models import BGCategory, BackGround
from pyquery import PyQuery as pq
import re
from urlparse import urljoin, urlparse
from pycomm.utils import text
from pycomm.utils.encoding import any_to_unicode

@route('/iframe-font')
class Index(ResponseHandler):
    def parse(self, **kwargs):
        body = self.response.body
        page = pq(body)
        for option in text.get_in_list(page.find('#cate_id').html(), '<option', '</option>'):
            name, value = text.get_in(option, '>'), text.get_in(option, 'value="', '"')
            if value == '0':
                continue

            obj, new = BGCategory.objects.get_or_new(id=value)
            obj.name = name
            obj.save()

            yield Url(name, '/iframe-font/c/%s/page/1' % value, self.response)


@route('/iframe-font/c/(\d+)/page/(\d+)')
class SubCategory(ResponseHandler):
    def parse(self, cid, cur_page, **kwargs):

        body = self.response.body

        page = pq(body)
        for li in text.get_in_list(page.find('.createFontList1').html(), '<li>', '</li>'):
            a = pq(li).find('a')
            img = pq(li).find('img')
            name = text.get_in(li, "updateText.font('", "')")
            src = img.attr('src')
            url = Url(name, src, self.response)
            yield url
            obj, new = BackGround.objects.get_or_new(name=name)
            obj.img = get_img_path(src)
            obj.category_id = cid
            obj.save()

        for a in text.get_in_list(page.find('.page1').html(), '<a', '</a>'):
            if a.find('Next') != -1:
                self.log.trace("get next page for %s", self.response.url)
                yield Url('%s_%s' % (cid, cur_page), '/iframe-font/c/%s/page/%s' % (cid, int(cur_page) + 1), self.response)




class AppSpider(Spider):
    request_default = {
        'connect_timeout': 100,
        'request_timeout': 100,
    }


def main():
    start_urls = ['http://www.yescustomall.com/iframe-font']
    pipeline = FontSpiderUrls.pipeline(start_urls)
    spider = AppSpider(pipeline, max_running=1000000)

    spider.run()


if __name__ == '__main__':
    main()
