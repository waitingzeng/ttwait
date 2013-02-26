#!/usr/bin/python
#coding=utf8

from django.db import models

# Create your models here.

class GoodsAttr(models.Model):
    name = models.CharField("商品属性", max_length=50)



class GoodsInfo(models.Model):
    name = models.CharField("商品名称", max_length=200)
    price = models.FloatField("价格")
    

    attrs = models.ManyToManyField(GoodsAttr)

    class Meta:
        verbose_name = "产品"
        verbose_name_plural = verbose_name


