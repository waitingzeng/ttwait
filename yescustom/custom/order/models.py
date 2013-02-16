#!/usr/bin/python
#coding=utf8

from django.db import models
import hashlib
import time
import random
from pycomm.utils import text

# Create your models here.

class UserProfile(models.Model):
    user_email = models.CharField('user_email', max_length=50, unique=True)
    hash_user_email = models.CharField('hash_user_email', max_length=50)
    user_password = models.CharField("user_password", max_length=50)
    user_name = models.CharField('user_name', max_length=50)
    hash_user_name = models.CharField('hash_user_name', max_length=50)
    status = models.IntegerField("status", default=0)


class UserOrder(models.Model):
    user = models.ForeignKey(UserProfile)
    order_sn = models.CharField('order_sn', max_length=20, unique=True)
    status = models.PositiveSmallIntegerField('订单状态', default=0)




