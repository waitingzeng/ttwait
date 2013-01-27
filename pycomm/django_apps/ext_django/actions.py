#!/usr/bin/python
#coding=utf8
# coding: utf-8

# PYTHON IMPORTS
from datetime import datetime
import csv
import re
from types import *

# DJANGO IMPORTS
from django.contrib.admin import helpers
from django.utils.encoding import force_unicode
from django.shortcuts import render_to_response
from django import template
from django.contrib.admin.util import unquote
from django.http import HttpResponse
from django.utils.translation import ugettext as _


def get_csv_export_fields(modeladmin, included, request):
    fields = []
    return [name for name, verbose_name in modeladmin.get_export_fields(request) if name in included]

def csv_get_export_filename(modeladmin):
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return '%s_%s_%s_export.xls' % (ts, modeladmin.model._meta.app_label, modeladmin.model._meta.module_name)


def _csv_resolve_field(modeladmin, row, fieldname):

    if isinstance(fieldname, basestring):
        if getattr(modeladmin, fieldname, None):
            return getattr(modeladmin, fieldname)(row)

        if isinstance(getattr(row, fieldname), MethodType):
            return getattr(row, fieldname)()
        else:
            return getattr(row, fieldname)
    elif isinstance(fieldname, FunctionType):
        return fieldname(row)
    else:
        obj = row
        for bit in fieldname:
            obj = getattr(obj, bit)
        return obj

def csv_resolve_field(modeladmin, row, fieldname):
    f = _csv_resolve_field(modeladmin, row, fieldname)
    if isinstance(f, unicode):
        if f.isdigit():
            f = '"%s"' % f
        return f.encode('utf8')
    elif isinstance(f, int):
        if f > 2 ** 10:
            return '"%s"' % f
    return f

def csv_get_fieldname(field):
    if isinstance(field, basestring):
        return field
    elif isinstance(field, FunctionType):
        return field.short_description
    return '.'.join(field)


def csv_export_selected(modeladmin, request, queryset):
    if request.POST.get('post'):
        fields = get_csv_export_fields(modeladmin, request.POST.getlist('_fields'), request)
        
        res = modeladmin.export_model(modeladmin.model, queryset, fields, modeladmin)
        
        response = HttpResponse(res, mimetype='application/octet-stream; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename=%s' % csv_get_export_filename(modeladmin)
        return response

    fields = modeladmin.get_export_fields(request)
    
    opts = modeladmin.model._meta
    app_label = opts.app_label
    context = {
        "title": _("导出为CSV"),
        "object_name": force_unicode(opts.verbose_name),
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'fields': fields,
    }
    
    # Display the confirmation page
    return render_to_response([
        "admin/%s/%s/csv_export_confirmation.html" % (app_label, opts.object_name.lower()),
        "admin/%s/csv_export_confirmation.html" % app_label,
        "admin/csv_export_confirmation.html"
    ], context, context_instance=template.RequestContext(request))
csv_export_selected.short_description = "导出所选为Excel"
