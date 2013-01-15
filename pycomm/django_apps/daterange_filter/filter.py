# -*- coding: utf-8 -*-


'''
Has the filter that allows to filter by a date range.

'''
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.db import models
from django.utils.translation import ugettext as _
from datetime import datetime
import time
from urlparse import parse_qsl



class DateRangeForm(forms.Form):

    def __init__(self, *args, **kwargs):
        use_timestamp = kwargs.pop('use_timestamp', False)

        field_name = kwargs.pop('field_name')
        
        super(DateRangeForm, self).__init__(*args, **kwargs)

        self.use_timestamp = use_timestamp
        self.field_name = field_name
        
        gte_value = self.data.get('%s__gte' % field_name, '')
        lte_value = self.data.get('%s__lte' % field_name, '')

        if use_timestamp and gte_value and gte_value.isdigit():
            gte_value = datetime.fromtimestamp(int(gte_value)).strftime('%Y-%m-%d')
            self.data['%s__gte' % field_name] = gte_value

        if use_timestamp and lte_value and lte_value.isdigit():
            lte_value = datetime.fromtimestamp(int(lte_value)).strftime('%Y-%m-%d')
            self.data['%s__lte' % field_name] = gte_value

        self.fields['%s__gte' % field_name] = forms.DateField(
            label='', widget=AdminDateWidget(
                attrs={'placeholder': _('From date')}), localize=True,
            required=False)

        self.fields['%s__lte' % field_name] = forms.DateField(
            label='', widget=AdminDateWidget(
                attrs={'placeholder': _('To date')}), localize=True,
            required=False)

    def clean(self):
        if self.use_timestamp:
            gte_value = self.cleaned_data.get('%s__gte' % self.field_name, '')
            lte_value = self.cleaned_data.get('%s__lte' % self.field_name, '')

            if gte_value:
                gte_value = time.mktime(gte_value.timetuple())
                self.cleaned_data['%s__gte' % self.field_name] = int(gte_value)

            if lte_value:
                lte_value = time.mktime(lte_value.timetuple())
                self.cleaned_data['%s__lte' % self.field_name] = int(lte_value)
        return self.cleaned_data



class DateRangeFilter(admin.filters.FieldListFilter):
    template = 'daterange_filter/filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_upto = '%s__lte' % field_path
        super(DateRangeFilter, self).__init__(
            field, request, params, model, model_admin, field_path)
        self.form = self.get_form(request)

    def choices(self, cl):
        querystring = cl.get_query_string({}, [self.lookup_kwarg_since, self.lookup_kwarg_upto])
        for k, v in parse_qsl(querystring.strip('?')):
            yield k, v

    def expected_parameters(self):
        return [self.lookup_kwarg_since, self.lookup_kwarg_upto]

    def get_form(self, request):

        return DateRangeForm(data=self.used_parameters,
                             field_name=self.field_path)

    def queryset(self, request, queryset):
        if self.form.is_valid():
            # get no null params
            filter_params = dict(filter(lambda x: bool(x[1]),
                                        self.form.cleaned_data.items()))
            return queryset.filter(**filter_params)
        else:
            return queryset

class TimeStampRangeFilter(DateRangeFilter):
    def get_form(self, request):
        return DateRangeForm(data=self.used_parameters,
                             field_name=self.field_path, use_timestamp=True)

# register the filter
admin.filters.FieldListFilter.register(
    lambda f: isinstance(f, models.DateField), DateRangeFilter)
