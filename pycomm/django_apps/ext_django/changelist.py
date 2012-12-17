#!/usr/bin/python
#coding=utf8

from django.contrib.admin.views.main import ChangeList, EMPTY_CHANGELIST_VALUE
from django.contrib.admin.util import (lookup_field, display_for_field,
    display_for_value, label_for_field)
from django.utils.encoding import force_str, force_text, smart_text
from django.utils import six
from django.utils import timezone
import datetime
from django.utils import formats
from django.db import models

class ExportChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        ChangeList.__init__(self, *args, **kwargs)

        self.show_all = True
        self.formset = None


class QuerySetChangeList(object):
    def __init__(self, model, query_set, list_display, model_admin=None):
        self.result_list = query_set
        self.model = model
        self.opts = model._meta
        self.lookup_opts = self.opts
        self.list_display = list_display
        self.model_admin = model_admin

    def get_ordering_field_columns(self):
        return {}

    def get_query_string(self, *args, **kwargs):
        return ''

