#! /usr/bin/env python
#coding=utf-8
import json
from datetime import datetime
from django.contrib import admin

from pycomm.log import log

from django.contrib.contenttypes.models import ContentType

class ContentTypeAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ( 'name', 'app_label', 'model' )
    ordering = ('app_label', 'model')
    list_filter = ('app_label', 'model')
    search_fields = ('name', 'app_label', 'model' )

admin.site.register( ContentType, ContentTypeAdmin)

from django.contrib.sessions.models import Session
class SessionAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ( 'session_key', 'session_data', 'expire_date' )
    ordering = ('-expire_date',)
    search_fields = ('session_key',)

admin.site.register( Session, SessionAdmin)


from django.contrib.admin.models import LogEntry
class LogEntryAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message')
    ordering = ('-action_time',)
    list_filter = ('content_type', 'action_flag', 'user')
    date_hierarchy = 'action_time'
    search_fields = ('object_repr', 'change_message', 'user__username')

admin.site.register( LogEntry, LogEntryAdmin)

from django.contrib.auth.models import Permission
class PermissionAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('name', 'content_type', 'codename')
    list_filter = ('content_type',)
    search_fields = ('name', 'codename')
    raw_id_fields = ['content_type']

admin.site.register(Permission, PermissionAdmin)
