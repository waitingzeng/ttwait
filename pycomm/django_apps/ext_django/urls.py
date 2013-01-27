# coding: utf-8

# DJANGO IMPORTS
from django.conf.urls.defaults import *
from django.views.generic.base import TemplateView
from django.conf import settings


urlpatterns = patterns('',
    
    # FOREIGNKEY & GENERIC LOOKUP
    url(r'^model_lookup/$', 'pycomm.django_apps.ext_django.views.model_lookup', name="ext_django_model_lookup"),

)
