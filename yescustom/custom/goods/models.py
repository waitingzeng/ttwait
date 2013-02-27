#!/usr/bin/python
#coding=utf8

from django.db import models

# Create your models here.
class TermsBase(models.Model):
    name = models.CharField("名称", max_length=32, unique=True)
    parent = models.ForeignKey('self', verbose_name='父分类', null=True, blank=True)
    parent_path = models.CharField('分类路径', max_length=120, default='', blank=True, editable=False)
    display_order = models.PositiveIntegerField('排序', default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)    
   
    class Meta:
        abstract = True
        ordering = ['display_order', 'id']

    @property
    def path(self):
        return self.parent_path + ',%s' % self.pk

    def save(self, *args, **kwargs):
        if not self.parent:
            self.parent_path = ''
        else:
            self.parent_path = self.parent.path

        return models.Model.save(self, *args, **kwargs)

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "name__icontains",)


class GoodsAttr(TermsBase):
    pass

    class Meta:
        verbose_name = "商品属性"
        verbose_name_plural = verbose_name


class Tags(TermsBase):

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = verbose_name


class GoodsInfo(models.Model):
    name = models.CharField("商品名称", max_length=200)
    price = models.FloatField("价格")
    tags = models.ManyToManyField("Tags", verbose_name='Tags')    

    attrs = models.ManyToManyField(GoodsAttr, verbose_name='attrs', through="GoodsInfoAttr")

    class Meta:
        verbose_name = "产品"
        verbose_name_plural = verbose_name

class GoodsInfoAttr(models.Model):
    attr = models.ForeignKey(GoodsAttr)
    goods_info = models.ForeignKey(GoodsInfo)

