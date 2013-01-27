#!/usr/bin/python
#coding=utf8
from django.conf import settings

def extra(request):
    return {'ADMIN_URL' : settings.ADMIN_URL}
