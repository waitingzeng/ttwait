#!/usr/bin/python
#coding=utf8
from pycomm.django_apps.ext_django import admin

import models

class UserOrderAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_select_related = False
    list_display = [u'id', 'order_sn', 'status']
    search_fields = ['order_sn', 'content']
    list_filter = ['status', 'create_time']
    list_editable = ['status']
    date_hierarchy = None
    raw_id_fields = ['user']
    autocomplete_lookup_fields = {'m2m': [], 'fk': ['user']}

admin.site.register(models.UserOrder, UserOrderAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_select_related = False
    list_display = [u'id', 'user_email', 'hash_user_email', 'user_password', 'user_name', 'hash_user_name', 'status']
    search_fields = ['user_email', 'hash_user_email', 'user_password', 'user_name', 'hash_user_name']
    list_filter = ['create_time']
    list_editable = []
    date_hierarchy = None
    raw_id_fields = []
    autocomplete_lookup_fields = {'m2m': [], 'fk': []}

admin.site.register(models.UserProfile, UserProfileAdmin)
