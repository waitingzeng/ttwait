#!/usr/bin/python
#coding=utf8
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "custom.settings"
import sys
sys.path.insert(0, os.path.dirname('../../'))

from custom.spider.models import CustomGoodsPipeline
from pycomm.libs.spider import ResponseHandler, route, Spider, Url
from custom.goods.models import Category, GoodsInfo, GoodsAttr, GoodsInfoAttr, Tags, GoodsImg
from pyquery import PyQuery as pq
import re
import traceback
from urlparse import urljoin, urlparse


@route('/personalized')
class Index(ResponseHandler):
    def parse(self, **kwargs):
        body = self.response.body

        page = pq(body)
        for dl in page.find('.cateList4 dl'):
            dl = pq(dl)
            a = dl.find('dt a')
            cid, name = re.findall('\d+$', a.attr('href'))[0], a.text()
            cat, create = Category.objects.get_or_new(pk=cid)
            cat.name = name
            cat.save()
            for dd in dl.find('dd'):
                dd = pq(dd)
                for a in dd.find('li a'):
                    a = pq(a)
                    child_cid, child_name = re.findall('\d+$', a.attr('href'))[0], a.text()
                    child_cat, create = Category.objects.get_or_new(pk=child_cid)
                    child_cat.name = child_name
                    child_cat.parent = cat
                    child_cat.save()
                    href = urljoin(self.response.url, a.attr('href'))
                    yield Url(child_name, href, cid=child_cid)


@route('/personalized-category/personalized/.*')
class SubCategory(ResponseHandler):
    def parse(self, **kwargs):
        parent_id = kwargs.get('cid', None)

        body = self.response.body

        page = pq(body)
        for a in page.find('.cateList3 li .cateList3Pic a'):
            a = pq(a)
            img = a.find('img')
            try:
                cid, name = re.findall('\d+$', a.attr('href'))[0], img.attr('alt').strip()
            except IndexError:
                continue
            src = img.attr('src')
            url = Url(name, src, self.response)
            yield url
            src = src.replace('_t_200_200', '')
            url = Url(name, src, self.response)
            yield url            
            cat, create = Category.objects.get_or_new(pk=cid)
            cat.name = name
            cat.img = urlparse(src).path
            cat.parent_id = parent_id
            cat.save()

            href = urljoin(self.response.url, a.attr('href') + '/page/1')
            yield Url(name, href, cid=cid)


@route('/personalized-designs/personalized/(.*?)/page/(\d+)')
class Design(ResponseHandler):
    def parse(self, cname, cur_page, **kwargs):
        cid = kwargs.get('cid', None)

        body = self.response.body

        page = pq(body)
        for li in page.find('.designList2 li'):
            li = pq(li)
            a = li.find('.designList2Pic a')
            href = urljoin(self.response.url, a.attr('href'))
            name = a.find('img').attr('alt').strip()
            pid = re.findall('\d+$', a.attr('href'))[0]
            yield Url(name, href, cid=cid, pid=pid)
            goods, create = GoodsInfo.objects.get_or_create(pk=pid)
            goods.category_id = cid
            goods.name = name
            goods.price = li.find('.designList2Text .fb').eq(0).text().strip('$')
            goods.save()

        for a in page.find('.page1 a'):
            a = pq(a)
            if a.text().strip() == 'Next':
                self.log.trace("get next page for %s", self.response.url)
                yield Url('%s_%s' % (cid, cur_page), a.attr('href'), self.response)



@route('/personalized-design/personalized/.*')
class Detail(ResponseHandler):
    def parse(self, **kwargs):
        cid = kwargs.get('cid', None)
        pid = kwargs.get('pid', None)

        body = self.response.body
        page = pq(body)

        goods, create = GoodsInfo.objects.get_or_create(pk=pid)
        right = page.find('.designShow1Right')

        ##Material and Size
        for mt10 in right.find('.mt10'):
            mt10 = pq(mt10)
            txt = mt10.text()
            if txt.startswith('Material') or txt.startswith('Size'):
                name, values = txt.split(':', 1)
                attr, create = GoodsAttr.objects.get_or_create(name=name.strip())

                values = values.split(',')
                for value in values:
                    ga, cretae = GoodsInfoAttr.objects.get_or_create(goods_info=goods, attr=attr, value=value.strip())

            #tags
            if txt.startswith('Tags'):
                for a in mt10.find('a'):
                    tag = pq(a).text()
                    tag, create = Tags.objects.get_or_create(name=tag)
                    goods.tags.add(tag)

        ###color
        attr, create = GoodsAttr.objects.get_or_create(name='Color')
        for color in right.find('.designColorList1 li a'):
            color = pq(color)
            value = color.attr('title')
            value2 = color.find('b').css('background')
            ga, cretae = GoodsInfoAttr.objects.get_or_new(goods_info=goods, attr=attr, value=value.strip())
            ga.extra = value2
            ga.save()

        goods.can_addcart = right.find('a').text().find('to cartCustomize') != -1

        detail = page.find('.mt20').eq(1).html()
        detail = detail.replace('http://www.customdropshipping.com', '')
        goods.detail = detail

        goods.save()

        for img in page.find('.mt20').eq(1).find('img'):
            img = pq(img)
            src = img.attr('src')
            name = img.attr('alt')
            yield Url(name, src, self.response)
            src = src.replace('_t_500_500', '')
            yield Url(name, src, self.response)
            
        # pic list
        for img in page.find('#designPicList1 img'):
            img = pq(img)
            src, alt = img.attr('src'), img.attr('alt')
            yield Url(alt, src, self.response)
            src = src.replace('_t_75_75', '')
            yield Url(alt, src, self.response)

            path = src.replace('http://www.customdropshipping.com', '')
            GoodsImg.objects.get_or_create(goods_info=goods, path=path)

        yield Url(goods.name, '/create-design/personalized/%s' % goods.pk, self.response, cid=cid, pid=pid)



@route(['(/.*\.jpg)', '(/.*\.gif)', '(/.*\.png)'])
class LoadImage(ResponseHandler):
    def parse(self, path):
        path = urlparse(self.response.url).path
        os.makedirs(path)
        file(path, 'wb').write(self.response.body)
        return


class GoodsSpider(Spider):
    request_default = {
        'connect_timeout' : 100,
        'request_timeout' : 100,
    }

def main():
    start_urls = ['http://www.customdropshipping.com/personalized']
    pipeline = CustomGoodsPipeline(start_urls)
    spider = GoodsSpider(pipeline, max_running=1000000)

    spider.run()


if __name__ == '__main__':
    main()
