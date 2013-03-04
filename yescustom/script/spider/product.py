#!/usr/bin/python
#coding=utf8
from utils import get_img_url, get_img_path

from custom.spider.models import CustomProductSpiderUrls
from pycomm.libs.spider import ResponseHandler, route, Spider, Url
from custom.design.models import Category, Product, ProductImg, ProductColor, Color, ProductSize, ProductModel, ProductColorSize
from pyquery import PyQuery as pq
import re
from urlparse import urljoin, urlparse
from pycomm.utils.escape import json_decode


@route('/custom')
class Index(ResponseHandler):
    def parse(self, **kwargs):
        body = self.response.body

        page = pq(body)
        for cat in page.find('.cateList2'):
            cat = pq(cat)
            parent, create = Category.objects.get_or_create(name=cat.prev().text())
            for a in cat.find('.cateList2Pic a'):
                a = pq(a)
                img = a.find('img')
                cid, name = get_id(a.attr('href')), img.attr('alt')
                category, create = Category.objects.get_or_new(pk=cid)
                category.name = name
                category.parent = parent
                src = img.attr('src')
                for img in get_img_url(src):
                    url = Url(name, img, self.response)
                    yield url
                category.img = get_img_path(src)
                category.save()
                yield Url(name, a.attr('href'), self.response, cid=cid)


@route('/custom-categories/custom/.*')
class SubCategory(ResponseHandler):
    def parse(self, **kwargs):
        parent_id = kwargs.get('cid', None)

        body = self.response.body

        page = pq(body)
        for a in page.find('.cateList3 li .cateList3Pic a'):
            a = pq(a)
            img = a.find('img')
            try:
                cid, name = get_id(a.attr('href')), img.attr('alt').strip()
            except IndexError:
                continue
            src = img.attr('src')
            for img in get_img_url(src):
                url = Url(name, img, self.response)
                yield url
            cat, create = Category.objects.get_or_new(pk=cid)
            cat.name = name
            cat.img = get_img_path(src)
            cat.parent_id = parent_id
            cat.save()

            href = a.attr('href') + '/page/1'
            yield Url(name, href, self.response, cid=cid)


@route('/custom-products/custom/(.*)/page/(\d+)')
class Design(ResponseHandler):
    def parse(self, cname, cur_page, **kwargs):
        cid = kwargs.get('cid', None)

        body = self.response.body

        page = pq(body)
        for prod in page.find('.productList1 dl'):
            prod = pq(prod)

            pic = prod.find('.productList1Pic')
            a = pic.find('a')
            img = a.find('img')
            href = urljoin(self.response.url, a.attr('href'))
            name = img.attr('alt').strip()

            pid = get_id(a.attr('href'))

            yield Url(name, href, self.response, cid=cid, pid=pid)
            src = img.attr('src')
            for img in get_img_url(src):
                url = Url(img, img, self.response)
                yield url

            product, create = Product.objects.get_or_create(pk=pid)
            product.category_id = cid
            product.name = name

            product.price = pic.find('.mt5 .fb').text().strip('$')
            product.material = prod.find('.productList1Text .mt5').eq(2).text()
            product.thumb = get_img_path(src)
            product.save()

            yield Url(name, '/edit-product/pid/%s' % pid, self.response, cid=cid, pid=pid)

        for a in page.find('.page1 a'):
            a = pq(a)
            if a.text().strip() == 'Next':
                self.log.trace("get next page for %s", self.response.url)
                yield Url('%s_%s' % (cid, cur_page), a.attr('href'), self.response)


@route('/edit-product/pid/(\d+)')
class Detail1(ResponseHandler):
    def parse(self, product_id, **kargs):
        data = json_decode(self.response.body)

        product = Product.objects.get(pk=product_id)

        for item in data:
            product_color = ProductColor()
            product_color.id = item['color_id']
            product_color.color_min_buy = item['color_min_buy']
            product_color.color_max_buy = item['color_max_buy']
            product_color.product = product
            product_color.save()

            if item['color_num'] == 1:
                color, new = Color.objects.get_or_new(name=item['color_name'])
                color.value = item['color_value']

                color.save()
                product_color.colors.add(color)
            else:
                for i in range(item['color_num']):
                    color, new = Color.objects.get_or_new(name=item['color_name'][i])
                    color.value = item['color_value'][i]
                    color.save()
                    product_color.colors.add(color)

            for color_size in item['color_size']:
                size, new = ProductSize.objects.get_or_new(id=color_size['size_id'])
                size.name = color_size['size_name']
                size.save()

                pcs = ProductColorSize()
                pcs.color = product_color
                pcs.size = size
                pcs.price = color_size['size_price']
                pcs.save()

            yield Url('pid_%s_color_%s' % (product_id, product_color.id), '/edit-color/cid/%s' % product_color.pk, self.response)


@route('/edit-color/cid/(\d+)')
class EditColor(ResponseHandler):
    def parse(self, color_id, **kwargs):
        product_color = ProductColor.objects.get(pk=color_id)

        data = json_decode(self.response.body)

        for item in data:
            model, new = ProductModel.objects.get_or_new(id=item['model_id'])
            model.name = item['model_name']
            model.price = item['model_price']

            for img in get_img_url(item['model_bg']):
                url = Url(img, img, self.response)
                yield url

            model.bg = get_img_path(item['model_bg'])
            model.color = product_color
            model.save()

            yield Url('color_%s_model_%s' % (color_id, model.id), '/edit-model/mid/%s' % model.id, self.response)


@route('/edit-model/mid/(\d+)')
class EditModel(ResponseHandler):
    def parse(self, mid, **kwargs):
        model, new = ProductModel.objects.get_or_new(pk=mid)

        data = json_decode(self.response.body)
        for k, v in [('name', 'name'), ('sort', 'sort'), ('trueWidth', 'true_width'), ('trueHeight', 'true_height'), ('trueAreaWidth', 'true_area_width'), ('trueAreaHeight', 'true_area_height'), ('areaWidth', 'area_width'), ('areaHeight', 'area_height'), ('areaX', 'area_x'), ('areaY', 'area_Y')]:
            setattr(model, v, data[k])

        for img in get_img_url(data['bg']):
            url = Url(img, img, self.response)
            yield url

        for img in get_img_url(data['front']):
            url = Url(img, img, self.response)
            yield url

        model.bg = get_img_path(data['bg'])
        model.front = get_img_path(data['front'])


@route('/custom-product/custom/.*')
class Detail(ResponseHandler):
    def parse(self, **kwargs):
        pid = kwargs.get('pid', None)

        body = self.response.body
        page = pq(body)

        product, create = Product.objects.get_or_create(pk=pid)

        detail = page.find('.line1').eq(1).nextAll()
        detail.find('.commentList1, .comment1').remove()

        keywords = []
        for a in detail.find('.mt10').eq(1).find('a'):
            keywords.append(a.text())

        product.keywords = ','.join(keywords)

        detail.find('.mt10').eq(1).remove()

        for img in detail.find('#gallery img'):
            src = img.attr(src)
            for item in get_img_url(src):
                yield Url(item, item, self.response)

            a = ProductImg()
            a.product = product
            a.img = get_img_path(src)
            try:
                a.save()
            except:
                pass

        detail.find('#gallery').remove()

        detail = str(detail)
        detail = detail.replace('http://www.customdropshipping.com', '')
        product.detail = detail

        product.save()
        # pic list
        for img in pq(detail).find('img'):
            img = pq(img)
            src, alt = img.attr('src'), img.attr('alt')
            if not src:
                continue
            for img in get_img_url(src):
                url = Url(img, img, self.response)
                yield url


class ProductSpider(Spider):
    request_default = {
        'connect_timeout': 100,
        'request_timeout': 100,
    }


def main():
    start_urls = ['http://www.yescustomall.com/custom']
    pipeline = CustomProductSpiderUrls.pipeline(start_urls)
    spider = ProductSpider(pipeline, max_running=1000000)

    spider.run()


if __name__ == '__main__':
    main()
