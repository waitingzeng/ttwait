#!/usr/bin/python
#coding=utf8
import models

from pycomm.django_apps.ext_django.admin import auto_admin_for_models

auto_admin_for_models(models)
