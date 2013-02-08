#-*- coding: utf-8 -*-
"""
Empty file, mark package as valid django application
"""
from django.db import models
from pycomm.django_apps.ext_django.fields import CustomImageField, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User


class ModelStatusChange(models.Model):
    user = models.ZeroForeignKey(User, verbose_name='操作者')
    content_type = models.ZeroForeignKey(ContentType)
    object_id = models.IntegerField('object id')

    obj = GenericForeignKey('content_type', 'object_id')
    status_from = models.CharField('起始状态', max_length=100)
    status_to = models.CharField("结束状态", max_length=100)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '状态变更记录'
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return '%s change %s from %s to %s' % (self.user, self.obj, self.status_from, self.status_to)



