#!/usr/bin/python
#coding=utf8

from django.db import models
from custom.basic_models import TermsBase
from custom.design.models import Product, Category, ProductColor


class Tags(TermsBase):
    class Meta:
        verbose_name = "标签"
        verbose_name_plural = verbose_name


class DesignProduct(models.Model):
    product = models.ForeignKey(Product, null=True)
    color = models.ForeignKey(ProductColor, null=True)
    price = models.FloatField(default=0)
    name = models.CharField("设计名称", max_length=200, blank=True, default='')
    tags = models.ManyToManyField("Tags", verbose_name='Tags', blank=True)
    thumb = models.CharField("缩略图", max_length=200, null=True)
    design_data = models.TextField("设计数据", blank=True)
    category = models.ForeignKey(Category, null=True)
    

    class Meta:
        verbose_name = "产品"
        verbose_name_plural = verbose_name


