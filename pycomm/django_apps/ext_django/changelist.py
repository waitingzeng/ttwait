#!/usr/bin/python
#coding=utf8
from django.contrib.admin.views import main
from django.contrib.admin.views.main import ChangeList, EMPTY_CHANGELIST_VALUE, ALL_VAR
from django.contrib.admin.util import (lookup_field, display_for_field,
    display_for_value, label_for_field)
from django.utils.encoding import force_str, force_text, smart_text
from django.utils import six
from django.utils import timezone
import datetime
from django.utils import formats
from django.db import models


main.IGNORED_PARAMS = list(main.IGNORED_PARAMS) + ['extra_info']

class ExportChangeList(ChangeList):
    def __init__(self, model_admin, request, model=None, list_display=None, list_filter=None, search_fields=None):
        list_display_links = None
        date_hierarchy = None
        list_select_related = False
        list_per_page = 100
        list_max_show_all = 100000000
        list_editable = []
        request.GET = dict(request.GET.items())
        request.GET[ALL_VAR] = 1
        if model is None:
            model = model_admin.model

        if list_display is None:
            list_display = model_admin.list_display

        if list_filter is None:
            list_filter = model_admin.list_filter

        if search_fields is None:
            search_fields = model_admin.search_fields

        ChangeList.__init__(self, request, model, list_display, list_display_links,
            list_filter, date_hierarchy, search_fields, list_select_related,
            list_per_page, list_max_show_all, list_editable, model_admin)


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

