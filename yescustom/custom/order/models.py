#!/usr/bin/python
#coding=utf8

from django.db import models
import hashlib
import time
import random
from pycomm.utils import text

# Create your models here.

class UserProfile(models.Model):
    user_email = models.CharField('用户邮箱', max_length=50, unique=True)
    hash_user_email = models.CharField('加密邮箱', max_length=50)
    user_password = models.CharField("密码", max_length=50)
    user_name = models.CharField('用户妮称', max_length=50)
    hash_user_name = models.CharField('加密用户妮称', max_length=50)
    status = models.IntegerField("状态", default=0)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class UserOrder(models.Model):
    user = models.ForeignKey(UserProfile)
    order_sn = models.CharField('订单号', max_length=20, unique=True)
    status = models.PositiveSmallIntegerField('订单状态', default=0)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)


    class Meta:
        verbose_name = '订单'
        verbose_name_plural = verbose_name

