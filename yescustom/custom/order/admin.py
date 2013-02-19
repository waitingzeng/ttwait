#!/usr/bin/python
#coding=utf8
import models

from pycomm.django_apps.ext_django.admin import auto_admin_for_models

auto_admin_for_models(models)



"""
class UserProfileAdmin(object):
    list_display = ('user_email', 'hash_user_email', 'user_password', 'user_name', 'create_time')
    list_display_links = ('user_email',)

    list_filter = ['create_time']
    search_fields = ['user_email', 'user_name']


class UserOrderAdmin(object):
    list_display = ('user', 'order_sn', 'status', 'create_time')
"""
